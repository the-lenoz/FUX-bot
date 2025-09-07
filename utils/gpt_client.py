import asyncio
import logging
import mimetypes
import os
import secrets
import wave
from asyncio import sleep
from io import BytesIO
from typing import Literal, Dict, List

import numpy as np
import pydub
from aiogram.types import BufferedInputFile
from google.cloud import texttospeech
from gcloud.aio import storage
from google.cloud.texttospeech import SynthesisInput, VoiceSelectionParams, AudioConfig, \
    AudioEncoding
from google.genai import types, Client, errors
from google.genai.types import HttpOptions, LiveConnectConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig
from pydantic import BaseModel

from utils.prompts import SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT
from utils.user_request_types import UserFile

BASIC_MODEL = "gemini-2.5-flash-lite"
ADVANCED_MODEL = "gemini-2.5-flash"

TTS_MODEL = "gemini-live-2.5-flash-preview-native-audio"

MAX_RETRIES = 10


logger = logging.getLogger(__name__)

google_genai_client = Client(http_options=HttpOptions(api_version="v1"), location='us-central1')

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
    def __init__(self, model_name: str = BASIC_MODEL):
        self.model_name = model_name

    @staticmethod
    async def create_document_content_item(document: UserFile):
        storage_client = storage.storage.Storage()

        bucket = storage_client.get_bucket("fuxfiles")
        name = secrets.token_hex(16) + document.filename
        blob = bucket.new_blob(name)

        await blob.upload(
            data=document.file_bytes,
            content_type="application/pdf"
        )

        return types.Part.from_uri(file_uri=f"gs://fuxfiles/{name}", mime_type="application/pdf")

    @staticmethod
    async def create_image_content_item(image: UserFile) -> types.Part:
        storage_client = storage.storage.Storage()
        
        bucket = storage_client.get_bucket("fuxfiles")
        name = secrets.token_hex(16) + image.filename
        blob = bucket.new_blob(name)

        await blob.upload(
            data=image.file_bytes,
            content_type=mimetypes.guess_type(image.filename)[0]
        )

        return types.Part.from_uri(file_uri=f"gs://fuxfiles/{name}", mime_type=mimetypes.guess_type(image.filename)[0])

    @staticmethod
    async def create_voice_content_item(voice: UserFile) -> types.Part:
        storage_client = storage.storage.Storage()

        bucket = storage_client.get_bucket("fuxfiles")
        name = secrets.token_hex(16) + voice.filename
        blob = bucket.new_blob(name)

        await blob.upload(
            data=voice.file_bytes,
            content_type=mimetypes.guess_type(voice.filename)[0]
        )

        return types.Part.from_uri(file_uri=f"gs://fuxfiles/{name}", mime_type=mimetypes.guess_type(voice.filename)[0])

    @staticmethod
    async def create_text_content_item(text: str) -> types.Part:
        return types.Part.from_text(
            text=text
        )

    # noinspection PyTypeChecker
    @staticmethod
    async def generate_speech(text: str, user_ai_temperature: float = 1) -> BufferedInputFile:
        config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name="Puck",
                    )
                ),
            )
        )
        success = False
        tries = 0
        while not success and tries < MAX_RETRIES:
            try:
                async with google_genai_client.aio.live.connect(
                        model=TTS_MODEL,
                        config=config,
                ) as session:
                    text_input = f'Ты - просто text-to-speech модель. Ты не придумываешь свой ответ, а просто читаешь текст. Прочти его выразительно, в заданном стиле. Стиль: говори {"очень жёстко, злобно, строго, быстро и восклицательно. Ты как будто приказываешь" if user_ai_temperature == 0.6 else "спокойно"}. Текст:\n\n{text}'
                    await session.send_client_content(
                        turns=types.Content(role="user", parts=[types.Part(text=text_input)]))

                    audio_data = []
                    async for message in session.receive():
                        if (
                                message.server_content.model_turn
                                and message.server_content.model_turn.parts
                        ):
                            for part in message.server_content.model_turn.parts:
                                if part.inline_data:
                                    audio_data.append(
                                        np.frombuffer(part.inline_data.data, dtype=np.int16)
                                    )
                success = True
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(5)
            tries += 1

        if success:
            buffer = BytesIO()
            with wave.open(buffer, "w") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(24000)
                f.writeframes(np.concatenate(audio_data))
            buffer.seek(0)

            audio_segment = pydub.AudioSegment.from_wav(buffer)

            opus_buffer = BytesIO()
            audio_segment.export(opus_buffer, format="opus", codec="libopus", bitrate="64k")

            # Seek to the beginning of the BytesIO object so it can be read from
            opus_buffer.seek(0)

            return BufferedInputFile(
                opus_buffer.getvalue(),
                "voice.ogg"
            )
        else:
            logger.error("Ошибка - голос не сохранён")
            return None

    @staticmethod
    async def is_text_smalltalk(text: str):
        
        try:
            response = await google_genai_client.aio.models.generate_content(
                model=BASIC_MODEL,
                contents=SMALL_TALK_TEXT_CHECK_PROMPT_FORMAT.format(text=text)
            )
            logger.info(f"Smalltalk - {'true'in response.text}")
            return 'true' in response.text
        except errors.ClientError:
            return False

    @staticmethod
    def create_message(content: List, role: str = "user"):
        return types.Content(
            parts=content,
            role=role
        )

    async def process_request(self, input: List | str):
        contents = []
        system_prompt = "You are a helpful assistant"
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
        retry_time = 1
        response = None
        retries = 0
        while not response and retries < MAX_RETRIES:
            try:
                response = await google_genai_client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=[system_prompt],
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                            ),
                        ]
                    ),
                )
            except errors.ClientError as e:
                logger.error(e)
                logger.info(f"Retrying ({retries + 1})")
                await sleep(retry_time)
                retry_time *= 2
                retries += 1

        return response.text if response else 'Произошла ошибка, пожалуйста, повтори запрос чуть позже или сообщи в тех. поддержку!'