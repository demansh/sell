import os
import re
import json
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT_TEMPLATE = os.getenv("GEMINI_PROMPT", "Extract JSON from: {text}")
QUOTA_BACKOFF_SECONDS = 25
ALLOWED_CATEGORIES = [
    "electronics",
    "computers",
    "mobile",
    "furniture",
    "toys",
    "music",
    "arts",
    "jewelry",
    "clothing",
    "sport",
    "home",
    "transport",
    "hobbies",
    "watches",
    "other"
]
ALLOWED_CURRENCIES = ["AMD", "USD", "EUR", "RUB"]

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "models/gemini-2.5-flash-lite"
else:
    client = None
    print("⚠️ GEMINI_API_KEY не установлен")


async def analyze_post(text: str) -> dict:
    """Analyze a listing post via Google GenAI and return structured data.

    Args:
        text: Raw post text to analyze.

    Returns:
        Dict with keys: title, price, currency, categories.
    """
    if not client:
        return fallback_data(text)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        text=text,
        categories=", ".join(ALLOWED_CATEGORIES)
    )

    for _ in range(3):
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

            price_data = data.get("price")
            amount = None
            currency = "AMD"

            if isinstance(price_data, dict):
                amount = price_data.get("amount")
                detected_curr = str(price_data.get("currency", "AMD")).upper()
                currency = detected_curr if detected_curr in ALLOWED_CURRENCIES else "AMD"
            elif isinstance(price_data, (int, float)):
                amount = price_data

            input_cats = data.get("categories", [])
            valid_cats = [c for c in input_cats if c in ALLOWED_CATEGORIES] or ["other"]

            return {
                "title": str(data.get("title", text[:30])).strip(),
                "price": amount,
                "currency": currency,
                "categories": valid_cats,
            }

        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            if status == 429:
                print(f"⏳ Quota exceeded, waiting {QUOTA_BACKOFF_SECONDS}s...")
                await asyncio.sleep(QUOTA_BACKOFF_SECONDS)
                continue
            print(f"🤖 LLM Error: {e}")
            break

    return fallback_data(text)


def fallback_data(text: str) -> dict:
    return {"title": text[:30], "price": None, "currency": "AMD", "categories": ["other"]}
