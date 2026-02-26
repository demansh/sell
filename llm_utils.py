import os
import re
import json
import asyncio
import logging
from google import genai
from dotenv import load_dotenv
from config import config

logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT_TEMPLATE = os.getenv("GEMINI_PROMPT", "Extract JSON from: {text}")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "models/gemini-2.5-flash-lite"
else:
    client = None
    logger.warning("GEMINI_API_KEY is not set")


async def analyze_post(text: str) -> dict:
    """Analyze a listing post via Google GenAI and return structured data.

    Args:
        text: Raw post text to analyze.

    Returns:
        Dict with keys: title, price, currency, keywords.
    """
    if not client:
        return fallback_data(text)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(text=text)

    for _ in range(config.llm_retry_count):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=MODEL_NAME,
                contents=prompt,
            )

            if not response or not response.text:
                continue

            raw_content = re.sub(r"```[a-z]*\n?|```", "", response.text.strip()).strip()
            data = json.loads(raw_content)
            if isinstance(data, list):
                data = data[0] if data else {}

            price_data = data.get("price")
            amount = None
            currency = "AMD"

            if isinstance(price_data, dict):
                amount = price_data.get("amount")
                detected_curr = str(price_data.get("currency", "AMD")).upper()
                currency = detected_curr if detected_curr in config.currencies else "AMD"
            elif isinstance(price_data, (int, float)):
                amount = price_data

            return {
                "title": str(data.get("title", text[:30])).strip(),
                "price": amount,
                "currency": currency,
                "keywords": [k.lower() for k in data.get("keywords", [])],
            }

        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            if status == 429:
                logger.warning("Quota exceeded, waiting %ds...", config.llm_quota_backoff_sec)
                await asyncio.sleep(config.llm_quota_backoff_sec)
                continue
            logger.error("LLM error: %s", e)
            break

    return fallback_data(text)


def fallback_data(text: str) -> dict:
    return {"title": text[:30], "price": None, "currency": "AMD", "keywords": ["другое"]}
