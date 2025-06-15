import os
import tempfile
from typing import Literal, Dict, List

import httpx
import openai
from aiogram.types import BufferedInputFile
from openai import AsyncOpenAI
from pydantic import BaseModel

from settings import openai_api_key
from utils.prompts import SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT
from utils.user_request_types import UserFile

BASIC_MODEL = "gpt-4o-mini"
ADVANCED_MODEL = "gpt-4.1"

TRANSCRIPT_MODEL = "whisper-1"

TTS_MODEL = "tts-1-hd"

mental_assistant_id = os.getenv("MENTAL_ASSISTANT_ID")
standard_assistant_id = os.getenv("STANDARD_ASSISTANT_ID")



proxy_url = os.environ.get("OPENAI_PROXY_URL")
openAI_client = AsyncOpenAI(api_key=openai_api_key) if proxy_url is None or proxy_url == "" else \
    AsyncOpenAI(http_client=httpx.AsyncClient(proxy=proxy_url), api_key=openai_api_key)


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
        document_file = await openAI_client.files.create(
            file=(document.filename, document.file_bytes),
            purpose="user_data"
        )
        return {
            "type": "input_file",
            "file_id": document_file.id,
        }

    @staticmethod
    async def create_image_content_item(image: UserFile):
        image_file = await openAI_client.files.create(
            file=(image.filename, image.file_bytes),
            purpose="vision"
        )
        return {
            "type": "input_image",
            "file_id": image_file.id,
        }

    @staticmethod
    async def create_voice_content_item(voice: UserFile):
        text = await LLMProvider.get_transcription(voice)
        return {
            "type": "input_text",
            "text": text
        }

    @staticmethod
    def create_text_content_item(text: str):
        return {
            "type": "input_text",
            "text": text
        }

    @staticmethod
    async def get_transcription(voice: UserFile) -> str:
        try:
            transcript = await openAI_client.audio.transcriptions.create(
                model=TRANSCRIPT_MODEL,
                file=(voice.filename, voice.file_bytes),
                language="ru"
            )
            return transcript.text

        except openai.BadRequestError:
            return ""

    @staticmethod
    async def generate_speech(text: str) -> BufferedInputFile:
        response = await openAI_client.audio.speech.create(
            model=TTS_MODEL,
            voice="alloy",  # Выберите один из голосов: alloy, echo, fable, onyx, nova, shimmer
            input=text,
            response_format="opus"  # mp3, opus, aac, flac, wav, pcm
        )

        return BufferedInputFile(
            response.content,
            "voice.ogg"
        )

    @staticmethod
    async def is_text_smalltalk(text: str):
        try:
            response = await openAI_client.responses.create(
                model=BASIC_MODEL,
                input=SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT.format(text=text),
                max_output_tokens=32
            )
            return response.output_text == 'true'
        except openai.BadRequestError:
            return False

    @staticmethod
    def create_message(content: str | List, role: str = "user"):
        return ModelChatMessage(
            content=content,
            role=role
        )

    async def process_request(self, input: List | str):
        response = await openAI_client.responses.create(
            model=self.model_name,
            input=input
        )

        return response.output_text