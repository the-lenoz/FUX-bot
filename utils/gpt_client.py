import logging
import mimetypes
import os
from io import BytesIO
from pprint import pprint
from typing import Literal, Dict, List

import httpx
import openai
import pydub
from aiogram.types import BufferedInputFile
from google.genai import types, Client
from openai import AsyncOpenAI
from pydantic import BaseModel

from settings import openai_api_key, gemini_api_key
from utils.prompts import SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT
from utils.user_request_types import UserFile

BASIC_MODEL = "gemini-2.0-flash-lite"
ADVANCED_MODEL = "gemini-2.5-flash-preview-05-20"

TTS_MODEL = "gemini-2.5-flash-preview-tts"

mental_assistant_id = os.getenv("MENTAL_ASSISTANT_ID")
standard_assistant_id = os.getenv("STANDARD_ASSISTANT_ID")


logger = logging.getLogger(__name__)


proxy_url = os.environ.get("OPENAI_PROXY_URL")
openAI_client = AsyncOpenAI(api_key=openai_api_key) if proxy_url is None or proxy_url == "" else \
    AsyncOpenAI(http_client=httpx.AsyncClient(proxy=proxy_url), api_key=openai_api_key)

google_genai_client = Client(api_key=gemini_api_key)

class ModelChatMessage(BaseModel):
    role: Literal["user", "assistant", "developer", "system"]
    content: str | List

    def __init__(self, content: str | List, role: str = "user"):
        super().__init__(
            content=content,
            role=role
        )

    def __str__(self):
        return f"{{\n  role: {self.role},\n  content: {self.content[:32]}...\n}}"

    def __repr__(self):
        return self.__str__()


class ModelChatThread:
    def __init__(self):
        self._messages: Dict[int, ModelChatMessage | None] = {}
        self.__current_id = 0

    def add_message(self, message: ModelChatMessage) -> int:
        self._messages[self.__current_id] = message
        self.__current_id += 1
        return self.__current_id - 1

    def delete_message(self, message_id: int) -> bool:
        if self._messages.get(message_id) is not None:
            self._messages[message_id] = None
            return True
        else:
            return False

    def get_messages(self) -> List[ModelChatMessage]:
        return [message for _, message in sorted(list(self._messages.items()), key=lambda x: x[0]) if message is not None]

    def __str__(self):
        return '[\n  ' + '\n  '.join((str(message) for message in self.get_messages())) + '\n]'

    def __repr__(self):
        return self.__str__()


class LLMProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name

    @staticmethod
    async def create_document_content_item(document: UserFile):
        document_file = await google_genai_client.aio.files.upload(
            file=BytesIO(document.file_bytes),
            config=types.UploadFileConfig(mime_type="application/pdf")
        )
        return types.Part.from_uri(file_uri=document_file.uri, mime_type=document_file.mime_type)

    @staticmethod
    async def create_image_content_item(image: UserFile) -> types.Part:
        image_file = await google_genai_client.aio.files.upload(
            file=BytesIO(image.file_bytes),
            config=types.UploadFileConfig(mime_type=mimetypes.guess_type(image.filename)[0])
        )
        return types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)

    async def create_voice_content_item(self, voice: UserFile) -> types.Part:
        voice_file = await google_genai_client.aio.files.upload(
            file=BytesIO(voice.file_bytes),
            config=types.UploadFileConfig(mime_type=mimetypes.guess_type(voice.filename)[0])
        )

        transcript = await self.process_request(
            [
                self.create_message(
                    [
                        await self.create_text_content_item("Provide a transcript of the speech"),
                        types.Part.from_uri(
                            file_uri=voice_file.uri,
                            mime_type=voice_file.mime_type
                        )
                    ]
                )
            ]
        )

        return await self.create_text_content_item(
            text=transcript
        )

    @staticmethod
    async def create_text_content_item(text: str) -> types.Part:
        return types.Part.from_text(
            text=text
        )

    @staticmethod
    async def generate_speech(text: str) -> BufferedInputFile:
        response = await google_genai_client.aio.models.generate_content(
            model=TTS_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore',
                        )
                    )
                ),
            )
        )
        audio_segment = pydub.AudioSegment(
            data=response.candidates[0].content.parts[0].inline_data.data,
            sample_width=2,  # 16-bit PCM
            frame_rate=24000,
            channels=1
        )

        opus_buffer = BytesIO()
        audio_segment.export(opus_buffer, format="opus", codec="libopus", bitrate="64k")

        # Seek to the beginning of the BytesIO object so it can be read from
        opus_buffer.seek(0)

        return BufferedInputFile(
            opus_buffer.read(),
            "voice.ogg"
        )

    @staticmethod
    async def is_text_smalltalk(text: str):

        try:
            response = await google_genai_client.aio.models.generate_content(
                model=BASIC_MODEL,
                contents=SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT.format(text=text)
            )
            logger.info(f"Smalltalk - {'true'in response.text}")
            return 'true' in response.text
        except openai.BadRequestError:
            return False

    @staticmethod
    def create_message(content: List, role: str = "user"):
        return types.Content(
            parts=content,
            role=role
        )

    async def process_request(self, input: List | str):
        contents = []
        system_prompt = "You are an helpful assistant"
        for message in input:
            if message.role == "system":
                system_prompt = message.parts[0].text
            elif message.role in ("model", "user", "assistant"):
                contents.append(message)

        for content in input:
            for part in content.parts:
                if part.text:
                    logger.info(part.text[:32] + '...')
        logger.info("=" * 40)
        for content in contents:
            for part in content.parts:
                if part.text:
                    logger.info(part.text[:32] + '...')

        response = await google_genai_client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )


        return response.text