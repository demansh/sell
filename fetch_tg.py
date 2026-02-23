import os
import re
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService, User
from dotenv import load_dotenv

from llm_utils import analyze_post

# Загружаем переменные из .env файла, если он существует
load_dotenv() 

# Теперь os.getenv сначала ищет в системе, а если не находит — берет из .env
API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH')
SESSION_STRING = os.getenv('TG_SESSION_STRING')
CHANNEL_USERNAME = os.getenv('TG_CHANNEL')
POSTS_DIR = '_posts'
IMAGES_DIR = 'assets/img/posts'
BASE_URL = '/sell'
EXPIRY_DAYS = 7
LAST_ID_FILE = 'last_id.txt'

# Проверка на дурака
if not API_ID or not API_HASH:
    raise ValueError("API_ID или API_HASH не найдены в переменных окружения!")

# Создаем папки, если их нет
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def get_last_id():
    """Читает ID последнего обработанного сообщения из файла."""
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return None

async def save_last_id(last_id):
    """Сохраняет ID последнего сообщения."""
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(last_id))

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\.]', '_', name)

def get_smart_title(text, limit=30):
    if not text:
        return "Объявление"
    
    # Очищаем от лишних пробелов и переносов в начале
    text = text.strip().split('\n')[0] 
    
    if len(text) <= limit:
        return text.replace('"', '\\"')
    
    # Режем до лимита и ищем последний пробел
    truncated = text[:limit]
    last_space = truncated.rfind(' ')
    
    if last_space != -1:
        truncated = truncated[:last_space]
    
    return (truncated.strip() + "...").replace('"', '\\"')

def get_post_content(text, author_name, author_handle, author_id, msg_id, ai_data, date, images):
    """Генерация контента Markdown файла."""
    title = get_smart_title(text)
    img_list = "\n  - ".join([f'"{img}"' for img in images])
    
    front_matter = f"""---
layout: post
date: {date.strftime('%Y-%m-%d %H:%M:%S')}
author_name: "{author_name}"
author_handle: "{author_handle}"
author_id: "{author_id}"
t_post_id: "{msg_id}"
title: "{ai_data['title']}"
price: {ai_data['price'] if ai_data['price'] else "null"}
categories: {ai_data['categories']}
images: 
  - {img_list}
title: "{title}"
---
{text}"""
    return front_matter

async def cleanup_old_posts():
    """Удаление постов старше 7 дней и их изображений."""
    now = datetime.now()
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"):
            continue
            
        filepath = os.path.join(POSTS_DIR, filename)
        # Читаем дату из front matter (упрощенно по дате файла или парсинг)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Простой поиск даты в Markdown
            match = re.search(r'date: (\d{4}-\d{2}-\d{2})', content)
            if match:
                post_date = datetime.strptime(match.group(1), '%Y-%m-%d')
                if now - post_date > timedelta(days=EXPIRY_DAYS):
                    # Находим картинки и удаляем
                    images = re.findall(r'\"(/assets/img/posts/.*?)\"', content)
                    for img in images:
                        img_path = img.lstrip('/')
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    os.remove(filepath)
                    print(f"🗑 Удален старый пост: {filename}")

async def get_author_data(message):
    """
    Извлекает имя, никнейм и уникальный ID автора.
    """
    name = "Пользователь"
    handle = ""  # Будет пустым, если юзернейма нет
    user_id = ""

    sender = await message.get_sender()

    if isinstance(sender, User):
        first = sender.first_name or ""
        last = sender.last_name or ""
        name = f"{first} {last}".strip() or "Участник"
        handle = sender.username if sender.username else ""
        user_id = str(sender.id)
    
    return name, handle, user_id

async def process_messages(messages):
    texts = [m.text for m in messages if m.text]
    full_text = "\n".join(texts).strip()
    main_msg = next((m for m in messages if m.text), messages[0])

    if not full_text and not any(m.photo for m in messages):
        return
    
    print(f"🤖 Запрос к LLM для поста {main_msg.id}...")
    ai_data = await analyze_post(full_text)
    
    # ПОЛУЧАЕМ ДАННЫЕ (теперь 3 параметра)
    author_name, author_handle, author_id = await get_author_data(main_msg)
    
    text = main_msg.text or ""
    date = main_msg.date
    msg_id = main_msg.id

    # Логика дедупликации стала точнее: текст + конкретный ID
    existing_file = None
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"): continue
        f_path = os.path.join(POSTS_DIR, filename)
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Проверяем уникальное поле author_id
            if text[:100] in content and f'author_id: "{author_id}"' in content:
                existing_file = f_path
                break

    if existing_file:
        # Bump: обновляем только дату
        with open(existing_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(existing_file, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('date:'):
                    f.write(f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                else:
                    f.write(line)
        print(f"🔝 Пост обновлен (Bump): {existing_file}")
        return

    # Скачивание медиа
    image_paths = []
    for i, msg in enumerate(messages):
        if msg.photo:
            filename = f"{date.strftime('%Y%m%d')}_{msg_id}_{i}.jpg"
            path = os.path.join(IMAGES_DIR, filename)
            await client.download_media(msg.photo, path)
            image_paths.append(f"/{IMAGES_DIR}/{filename}")
    
    if not image_paths:
        print(f"⏩ Пропуск сообщения {messages[0].id}: нет изображений.")
        return

    # Создание Markdown
    post_filename = f"{date.strftime('%Y-%m-%d')}-{msg_id}.md"
    post_path = os.path.join(POSTS_DIR, post_filename)
    
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(get_post_content(text, author_name, author_handle, author_id, msg_id, ai_data, date, image_paths))
    print(f"✅ Создан новый пост: {post_filename}")

async def main():
    await client.start()
    print("🚀 Скрипт запущен...")

    # Чистим старье перед началом
    await cleanup_old_posts()

    last_processed_id = await get_last_id()
    new_messages = []
    
    if last_processed_id is None:
        # ЛОГИКА 1: Первый запуск — берем посты за последний час
        print("🕯 Первый запуск. Ищем посты за последний час...")
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        async for message in client.iter_messages(CHANNEL_USERNAME):
            if message.date < hour_ago:
                break
            new_messages.append(message)
    else:
        # ЛОГИКА 2: Инкрементальный запуск — только новые посты
        print(f"🔄 Ищем посты новее ID: {last_processed_id}")
        async for message in client.iter_messages(CHANNEL_USERNAME, min_id=last_processed_id):
            new_messages.append(message)

    if not new_messages:
        print("☕️ Новых постов нет.")
        return

    # Сохраняем ID самого последнего сообщения (они приходят от новых к старым, так что это первый в списке)
    # Важно: берем ID до фильтрации картинок, чтобы не застревать на текстовых постах
    await save_last_id(max(m.id for m in new_messages))

    # Группируем сообщения в альбомы
    album_groups = {}
    for message in reversed(new_messages): # Обрабатываем от старых к новым
        if message.grouped_id:
            album_groups.setdefault(message.grouped_id, []).append(message)
        else:
            await process_messages([message])

    for group in album_groups.values():
        await process_messages(sorted(group, key=lambda x: x.id))

    print(f"🚀 Обработка завершена. Найдено сообщений: {len(new_messages)}")

if __name__ == '__main__':
    asyncio.run(main())