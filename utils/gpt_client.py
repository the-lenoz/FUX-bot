import asyncio
import os

import httpx
from openai import AsyncOpenAI
from openai.pagination import AsyncPage
from openai.types.beta.threads import Run

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
