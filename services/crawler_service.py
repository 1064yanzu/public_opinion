import asyncio
from model.nlp import main_nlp

async def run_spider(keyword: str, platforms, start_date: str, end_date: str, precision: str):
    """Asynchronously run crawler and NLP pipeline."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, main_nlp, keyword, precision, platforms)
