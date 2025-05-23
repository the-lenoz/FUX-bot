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


async def find_most_recent_active_run(thread_id: str) -> str | None:
    """
    Finds the ID of the most recent run that is not in a terminal state.

    Args:
        thread_id: The ID of the thread.

    Returns:
        The ID of the most recent active run, or None if no active run is found.
    """
    try:
        # List runs for the thread. Default order is descending creation time.
        # Use limit=10 or similar if you might have many runs, adjust if needed.
        runs_page: AsyncPage[Run] = await openAI_client.beta.threads.runs.list(
            thread_id=thread_id,
            order="desc", # Ensure most recent is first
            limit=10      # Check a few recent runs
        )

        # Check the most recent runs for one that is active
        for run in runs_page.data:
            if run.status in ['queued', 'in_progress', 'requires_action']:
                print(f"Found active run: {run.id} with status {run.status}")
                return run.id # Found an active run, return its ID
            # If the most recent are not active, it's likely okay to proceed
            # Unless there was a failed/expired run you also care about
            # For the purpose of waiting for a *currently blocking* run,
            # we focus on the active states.
        return None # No active run found in the checked list

    except Exception as e:
        print(f"Error listing runs for thread {thread_id}: {e}")
        return None

# Re-use the polling function from the previous answer
async def wait_for_run_completion(thread_id: str, polling_interval_seconds: float = 1.0, timeout_seconds: float = 60.0):
    """
    Asynchronously waits for a SPECIFIC OpenAI Assistant run to complete.
    (Same function as before)
    ... implementation omitted for brevity ...
    """

    run_id = await find_most_recent_active_run(thread_id)
    if not run_id:
        return None

    # You'd paste the body of the previous wait_for_run_completion function here
    start_time = asyncio.get_event_loop().time()
    while True:
        run = await openAI_client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status in ['completed', 'failed', 'cancelled', 'expired']:
            if run.status in ['failed', 'cancelled', 'expired']:
                raise Exception(f"Run {run.id} ended with status: {run.status}. Last error: {run.last_error}")
            return run
        if asyncio.get_event_loop().time() - start_time > timeout_seconds:
             raise TimeoutError(f"Run {run_id} did not complete within {timeout_seconds} seconds.")
        await asyncio.sleep(polling_interval_seconds)
