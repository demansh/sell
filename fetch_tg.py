import os
import re
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService, User
from dotenv import load_dotenv

from llm_utils import analyze_post
from config import config
from image_optimizer import optimize_image, create_thumbnail

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH')
SESSION_STRING = os.getenv('TG_SESSION_STRING')
CHANNEL_USERNAME = os.getenv('TG_CHANNEL')
POSTS_DIR = '_posts'
IMAGES_DIR = 'assets/img/posts'
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

def get_post_content(text, author_name, author_handle, author_id, msg_id, ai_data, date, images, preview=None):
    """Генерация контента Markdown файла."""
    img_list = "\n  - ".join([f'"{img}"' for img in images])
    preview_line = ('\npreview: "' + preview + '"') if preview else ""
    safe_author = author_name.replace('"', '\\"')
    
    product_name = ai_data['title'].replace('"', '\\"')
    price = ai_data.get('price')
    currency = ai_data.get('currency') or "AMD"
    
    if price and price != "null":
        seo_title = f"{product_name} за {price} {currency} — Купить в Ереване"
    else:
        seo_title = f"{product_name} — Купить в Ереване"
    
    safe_header = ai_data['title'].replace('"', '\\"')

    front_matter = f"""---
layout: post
date: {date.strftime('%Y-%m-%d %H:%M:%S')}
author_name: "{safe_author}"
author_handle: "{author_handle}"
author_id: "{author_id}"
t_post_id: "{msg_id}"
title: "{seo_title}"
header: "{safe_header}"
price: {ai_data['price'] if ai_data['price'] else "null"}
currency: {ai_data['currency'] if ai_data['currency'] else "AMD"}
keywords: {ai_data['keywords']}
images:
  - {img_list}{preview_line}
---
{text}"""
    return front_matter

async def cleanup_old_posts():
    now = datetime.now()
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        date_match = re.search(r'date: (\d{4}-\d{2}-\d{2})', content)
        if not date_match:
            continue

        post_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        if now - post_date <= timedelta(days=config.expiry_days):
            continue

        images_block = re.search(
            r'^images:\s*\n((?:[ \t]*-[ \t]*"[^\n"]*"\n?)*)',
            content,
            re.MULTILINE,
        )
        image_paths = re.findall(r'"([^"]+)"', images_block.group(1)) if images_block else []

        preview_match = re.search(r'^preview:\s*"([^"]+)"', content, re.MULTILINE)
        if preview_match:
            image_paths.append(preview_match.group(1))

        for img in image_paths:
            local_path = img.lstrip('/')
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("Deleted image: %s", local_path)
            else:
                logger.warning("Image not found during cleanup: %s", local_path)

        os.remove(filepath)
        logger.info("Deleted old post: %s", filename)

async def get_author_data(message):
    """
    Извлекает имя, никнейм и уникальный ID автора.
    """
    name = "Пользователь"
    handle = ""
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

    if not full_text:
        logger.info("Skipping message %s: no text.", messages[0].id)
        return
    
    author_name, author_handle, author_id = await get_author_data(main_msg)
    date = main_msg.date
    msg_id = main_msg.id

    # Deduplication
    existing_file = None
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"): continue
        f_path = os.path.join(POSTS_DIR, filename)
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if full_text[:100] in content and f'author_id: "{author_id}"' in content:
                existing_file = f_path
                break

    if existing_file:
        # Bump
        with open(existing_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(existing_file, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('date:'):
                    f.write(f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                else:
                    f.write(line)
        logger.info("Post bumped: %s", existing_file)
        return
    
    logger.info("Requesting LLM for post %s...", main_msg.id)
    ai_data = await analyze_post(full_text)

    if ai_data is None:
        logger.warning("Skipping message %s: prohibited content detected by AI.", main_msg.id)
        return

    # Скачивание медиа
    image_paths = []
    preview_path = None
    for i, msg in enumerate(messages):
        if msg.photo:
            filename = f"{date.strftime('%Y%m%d')}_{msg_id}_{i}.jpg"
            path = os.path.join(IMAGES_DIR, filename)
            await client.download_media(msg.photo, path)
            final_path = optimize_image(path)
            image_paths.append(final_path)
            if i == 0:
                preview_path = create_thumbnail(final_path)

    if not image_paths:
        logger.info("Skipping message %s: no images.", messages[0].id)
        return

    # Создание Markdown
    post_filename = f"{date.strftime('%Y-%m-%d')}-{msg_id}.md"
    post_path = os.path.join(POSTS_DIR, post_filename)

    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(get_post_content(full_text, author_name, author_handle, author_id, msg_id, ai_data, date, image_paths, preview_path))
    logger.info("Created new post: %s", post_filename)

async def main():
    await client.start()
    logger.info("Script started...")

    # Чистим старье перед началом
    await cleanup_old_posts()

    last_processed_id = await get_last_id()
    new_messages = []
    
    if last_processed_id is None:
        # ЛОГИКА 1: Первый запуск — берем посты за последний час
        logger.info("First run. Looking for posts from the last hour...")
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        async for message in client.iter_messages(CHANNEL_USERNAME):
            if message.date < hour_ago:
                break
            new_messages.append(message)
    else:
        # ЛОГИКА 2: Инкрементальный запуск — только новые посты
        logger.info("Looking for posts newer than ID: %s", last_processed_id)
        async for message in client.iter_messages(CHANNEL_USERNAME, min_id=last_processed_id):
            new_messages.append(message)

    if not new_messages:
        logger.info("No new posts.")
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

    logger.info("Processing complete. Messages found: %d", len(new_messages))

if __name__ == '__main__':
    asyncio.run(main())