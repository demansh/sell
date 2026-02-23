import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = 'gemini-1.5-flash'
else:
    client = None
    print("⚠️ GEMINI_API_KEY не установлен")

async def analyze_post(text):
    """
    Анализирует текст объявления через новый Google GenAI SDK.
    """
    if not client:
        return fallback_data(text)

    prompt = f"""
    Проанализируй объявление о продаже и верни JSON.
    Текст объявления:
    "{text}"

    Верни ТОЛЬКО JSON с полями:
    - "title": короткое название товара (3-5 слов, без цены). Если описание содержит модель или название, используй их для заголовка. Если в посте несколько товаров, пиши "Распродажа".
    - "price": число и валюту через побел (например, 5000 ֏). Для драм (dram, amd, драмов и т.п.) используй ֏. Для долларов $, для евро €, для рубля ₽. Если в посте несколько цен пиши самую низкую цену.
    - "categories": массив строк (выбери подходящие: электроника, одежда, дом, транспорт, хобби, другое) с маленькой буквы.

    Пример вывода:
    {{"title": "iPhone 13 Pro Max", "price": 250000 ֏, "categories": ["электроника", "телефоны"]}}
    """

    try:
        # В новом SDK вызов выглядит так:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        if not response or not response.text:
            return fallback_data(text)

        # Очистка от markdown-тегов
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
        
        return {
            "title": str(data.get("title", text[:30])),
            "price": data.get("price") if isinstance(data.get("price"), (int, float)) else None,
            "categories": data.get("categories") if isinstance(data.get("categories"), list) else ["Другое"]
        }
    except Exception as e:
        print(f"🤖 Ошибка нового Gemini SDK: {e}")
        return fallback_data(text)

def fallback_data(text):
    """Резервные данные при сбое LLM."""
    return {
        "title": text[:30].strip() + "...",
        "price": None,
        "categories": ["другое"]
    }