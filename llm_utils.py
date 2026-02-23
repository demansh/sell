import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Настройка API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

async def analyze_post(text):
    """
    Анализирует текст объявления через Gemini LLM.
    Возвращает словарь с title, price и categories.
    """
    if not model:
        print("⚠️ Gemini API Key не найден. Используются значения по умолчанию.")
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
        # Gemini поддерживает асинхронность через generate_content_async
        response = await model.generate_content_async(prompt)
        
        # Очистка от markdown-тегов
        raw_text = response.text
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        
        data = json.loads(clean_json)
        
        # Валидация типов (гарантируем наличие полей)
        return {
            "title": str(data.get("title", text[:30])),
            "price": data.get("price") if isinstance(data.get("price"), (int, float)) else None,
            "categories": data.get("categories") if isinstance(data.get("categories"), list) else ["Другое"]
        }
    except Exception as e:
        print(f"🤖 Ошибка Gemini: {e}")
        return fallback_data(text)

def fallback_data(text):
    """Резервные данные при сбое LLM."""
    return {
        "title": text[:30].strip() + "...",
        "price": None,
        "categories": ["другое"]
    }