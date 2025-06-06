import asyncio
from model.ai_assistant import (
    get_chat_response as _sync_get_chat_response,
    verify_access_password,
    save_chat_history,
    load_chat_history,
)

async def get_chat_response(message: str, chat_history=None):
    """Asynchronously fetch chat response from the LLM."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_get_chat_response, message, chat_history)
