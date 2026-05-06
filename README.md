# Expense Tracker Bot 💰

Telegram-бот для отслеживания личных расходов.

## Установка

1. Установите зависимости:
pip install -r requirements.txt

2. Получите токен через @BotFather в Telegram

3. Запустите:
export BOT_TOKEN="ваш_токен"
python main.py

## Команды

- /add <сумма> <категория> [заметка] — добавить расход
- /list — последние расходы
- /stats — отчёт за 30 дней
- /stats7 — отчёт за 7 дней
- /delete <id> — удалить запись

## Категории

еда, транспорт, здоровье, развлечения, одежда, жильё, другое

## Стек

- Python 3.11+
- python-telegram-bot 21.5
- SQLite
