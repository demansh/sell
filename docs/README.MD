# Local run

```bash
gem install jekyll bundler
bundle exec jekyll serve
```

# Model

## Post

title: "Продам iPhone 15 Pro"
date: 2026-02-12 08:00:00 +0300
author_name: "Алексей"
author_handle: "@alex_seller"
images: 
  - "/assets/img/posts/iphone_1.png"
  - "/assets/img/posts/iphone_2.jpeg"
description_short: "Состояние идеальное, полный комплект. Срочно!"
text //full text in the body

---

# Контекст проекта: Telegram Showcase (Jekyll + Python)

**Роль:** Senior Python Developer.
**Задача:** Написать скрипт автоматизации для сбора данных из Telegram-канала и генерации статического контента для Jekyll.

## Текущая архитектура
1. **Frontend:** Статический сайт на Jekyll (GitHub Pages).
   - Главная: Сетка 3x3 (Instagram-style) с заголовками под превью.
   - Поиск: Живой поиск (JS) по `data-content` атрибутам.
   - Страница поста: Кастомная карусель (один жест = один слайд) и кнопка связи в Telegram.
2. **Хостинг:** Сайт живет по адресу `username.github.io/sell/` (baseurl: "/sell").

## Модель данных поста (Markdown Front Matter)
Каждый файл в `_posts/` должен иметь структуру:
---
layout: post
date: YYYY-MM-DD HH:MM:SS
author_name: "Имя"
author_handle: "username" (без @)
images: 
  - "/assets/img/posts/image1.jpg"
  - "/assets/img/posts/image2.jpg"
title: "Первые 20 символов текста"
---
Полный текст сообщения из Telegram.

## Требования к Python-скрипту (Telethon/Pyrogram)
1. **Источник:** Telegram-канал.
2. **Медиа:** - Скачивать все фото из поста в `assets/img/posts/`.
   - Именовать файлы: `{date}_{message_id}_{index}.jpg`.
   - Поддерживать альбомы (Grouped Messages) — все фото альбома должны попадать в список `images` одного поста.
3. **Логика дедупликации и Bump:**
   - Если текст и автор сообщения совпадают с существующим постом в `_posts/`, новый файл не создавать.
   - Вместо этого обновить поле `date` в существующем файле на текущее (чтобы пост поднялся в топ).
4. **Очистка:** Удалять файлы постов (Markdown и связанные картинки) старше 7 дней.
5. **Форматирование:** Текст сообщения должен сохранять переносы строк (использовать `white-space: pre-wrap` в CSS мы уже настроили).

## Твоя текущая задача:
Напиши полный код скрипта `fetch_tg.py`, учитывая асинхронность Telegram библиотек и необходимость корректной обработки альбомов (сообщения с одинаковым grouped_id приходят раздельно).
