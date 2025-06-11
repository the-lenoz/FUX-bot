import os
from typing import Literal

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

from settings import openai_api_key

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
    role: Literal["user", "assistant", "developer"]
    content: str | list

    def __init__(self, content: str | list, role: str = "user"):
        super().__init__(
            content=content,
            role=role
        )


class ModelChatThread:
    _messages = []

    def __init__(self):
        pass

    def add_message(self, message: ModelChatMessage) -> int:
        self._messages.append(message)
        return len(self._messages) - 1

    def get_messages(self):
        return self._messages