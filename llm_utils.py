import os
import json
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT_TEMPLATE = os.getenv("GEMINI_PROMPT", "Extract JSON from: {text}")
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
        "other"
    ]

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = 'models/gemini-2.5-flash-lite'
else:
    client = None
    print("⚠️ GEMINI_API_KEY не установлен")

async def analyze_post(text):
    """
    Анализирует текст объявления через новый Google GenAI SDK.
    """
    if not client:
        return fallback_data(text)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        text=text, 
        categories=", ".join(ALLOWED_CATEGORIES)
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            
            if not response or not response.text:
                continue

            # Очистка JSON
            raw_content = response.text.strip()
            if "```" in raw_content:
                # Извлекаем содержимое между ```json и ```
                parts = raw_content.split("```")
                raw_content = parts[1].replace("json", "").strip() if len(parts) > 2 else parts[1]

            data = json.loads(raw_content)
            
            # Валидация категорий
            input_cats = data.get("categories", [])
            valid_cats = [c for c in input_cats if c in ALLOWED_CATEGORIES]
            if not valid_cats:
                valid_cats = ["other"]

            return {
                "title": str(data.get("title", text[:30])).strip(),
                "price": data.get("price") if isinstance(data.get("price"), (int, float)) else None,
                "categories": valid_cats
            }

        except Exception as e:
            if "429" in str(e):
                print(f"⏳ Quota exceeded, waiting 25s...")
                await asyncio.sleep(25)
                continue
            print(f"🤖 LLM Error: {e}")
            break
            
    return fallback_data(text)

def fallback_data(text):
    return {"title": text[:30].strip() + "...", "price": None, "categories": ["other"]}