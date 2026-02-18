#!/bin/bash
python3 -m venv venv          # Создаем виртуальное окружение
source venv/bin/activate     # Активируем его
pip install --upgrade pip    # Обновляем сам установщик
pip install -r requirements.txt # Устанавливаем зависимости
echo "✅ Окружение готово. Используй 'source venv/bin/activate' перед запуском."
