"""
main.py — точка входа. Инициализация и запуск бота.
"""

import logging
import os

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import database
import handlers


logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

    database.init_db()
    logger.info("База данных инициализирована.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("help", handlers.cmd_help))
    app.add_handler(CommandHandler("add", handlers.cmd_add))
    app.add_handler(CommandHandler("list", handlers.cmd_list))
    app.add_handler(CommandHandler("stats", handlers.cmd_stats))
    app.add_handler(CommandHandler("stats7", handlers.cmd_stats7))
    app.add_handler(CommandHandler("delete", handlers.cmd_delete))
    app.add_handler(CallbackQueryHandler(handlers.handle_delete_callback, pattern="^delete_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_buttons))
    app.add_handler(MessageHandler(filters.COMMAND, handlers.handle_unknown))

    logger.info("Бот запущен. Ожидание сообщений...")
    app.run_polling()


if __name__ == "__main__":
    main()
