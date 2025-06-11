import os
from typing import Literal, Dict, List

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
    role: Literal["user", "assistant", "developer", "system"]
    content: str | List

    def __init__(self, content: str | List, role: str = "user"):
        super().__init__(
            content=content,
            role=role
        )


class ModelChatThread:
    _messages: Dict[int, ModelChatMessage | None] = {}
    __current_id = 0

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