"""
handlers.py — обработчики команд и сообщений Telegram-бота.
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

import database
import stats


MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("➕ Добавить расход"), KeyboardButton("📋 Последние расходы")],
        [KeyboardButton("📊 Статистика 30 дней"), KeyboardButton("📊 Статистика 7 дней")],
        [KeyboardButton("🗑 Удалить расход"), KeyboardButton("❓ Помощь")],
    ],
    resize_keyboard=True,
)

CATEGORY_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🍔 Еда"), KeyboardButton("🚌 Транспорт"), KeyboardButton("💊 Здоровье")],
        [KeyboardButton("🎮 Развлечения"), KeyboardButton("👕 Одежда"), KeyboardButton("🏠 Жильё")],
        [KeyboardButton("📦 Другое"), KeyboardButton("❌ Отмена")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

HELP_TEXT = """
*Expense Tracker Bot* 💰

Используйте кнопки меню внизу 👇

Или команды:
/add `<сумма> <категория> [заметка]`
/list — последние расходы
/stats — отчёт за 30 дней
/stats7 — отчёт за 7 дней
/delete `<id>` — удалить по номеру
"""

user_state: dict[int, dict] = {}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\nЯ помогу отслеживать твои расходы.\nВыбери действие 👇",
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Пример: `/add 1500 еда обед в кафе`",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    amount = stats.validate_amount(context.args[0])
    if amount is None:
        await update.message.reply_text("❌ Неверная сумма.", reply_markup=MAIN_KEYBOARD)
        return

    category = stats.validate_category(context.args[1])
    note = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    user_id = update.effective_user.id
    expense_id = database.add_expense(user_id, amount, category, note)
    emoji = stats.get_category_emoji(category)
    await update.message.reply_text(
        f"✅ Записано! {emoji}\n*{amount:,.0f} ₸* — {category}{f' ({note})' if note else ''}\nID: `#{expense_id}`",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    rows = database.get_expenses(user_id, limit=5)

    if not rows:
        await update.message.reply_text("У вас пока нет расходов.", reply_markup=MAIN_KEYBOARD)
        return

    await update.message.reply_text("🧾 *Последние расходы:*", parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)

    for row in rows:
        emoji = stats.get_category_emoji(row["category"])
        date = row["created_at"][:10]
        note = f" — {row['note']}" if row["note"] else ""
        text = f"{emoji} *{row['amount']:,.0f} ₸* [{row['category']}]{note}\n_{date}_"

        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🗑 Удалить #{row['id']}", callback_data=f"delete_{row['id']}")]
        ])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=inline_kb)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int = 30) -> None:
    user_id = update.effective_user.id
    text = stats.build_summary(user_id, days=days)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def cmd_stats7(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_stats(update, context, days=7)


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "Пример: `/delete 5`",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    expense_id = int(context.args[0])
    user_id = update.effective_user.id
    deleted = database.delete_expense(user_id, expense_id)
    if deleted:
        await update.message.reply_text(f"🗑 Запись `#{expense_id}` удалена.", parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)
    else:
        await update.message.reply_text(f"❌ Запись `#{expense_id}` не найдена.", parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на inline-кнопку удаления."""
    query = update.callback_query
    await query.answer()

    expense_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    deleted = database.delete_expense(user_id, expense_id)

    if deleted:
        await query.edit_message_text(f"🗑 Запись `#{expense_id}` удалена.", parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ Запись `#{expense_id}` не найдена.", parse_mode="Markdown")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.effective_user.id

    if text == "➕ Добавить расход":
        user_state[user_id] = {"step": "waiting_amount"}
        await update.message.reply_text("Введите сумму расхода (например: `1500`):", parse_mode="Markdown")

    elif text == "📋 Последние расходы":
        await cmd_list(update, context)

    elif text == "🗑 Удалить расход":
        await cmd_list(update, context)

    elif text == "📊 Статистика 30 дней":
        await cmd_stats(update, context, days=30)

    elif text == "📊 Статистика 7 дней":
        await cmd_stats(update, context, days=7)

    elif text == "❓ Помощь":
        await cmd_help(update, context)

    elif text == "❌ Отмена":
        user_state.pop(user_id, None)
        await update.message.reply_text("Отменено.", reply_markup=MAIN_KEYBOARD)

    elif text in ["🍔 Еда", "🚌 Транспорт", "💊 Здоровье", "🎮 Развлечения", "👕 Одежда", "🏠 Жильё", "📦 Другое"]:
        category_map = {
            "🍔 Еда": "еда", "🚌 Транспорт": "транспорт",
            "💊 Здоровье": "здоровье", "🎮 Развлечения": "развлечения",
            "👕 Одежда": "одежда", "🏠 Жильё": "жильё", "📦 Другое": "другое",
        }
        state = user_state.get(user_id, {})
        if state.get("step") == "waiting_category":
            category = category_map[text]
            amount = state["amount"]
            expense_id = database.add_expense(user_id, amount, category)
            emoji = stats.get_category_emoji(category)
            user_state.pop(user_id, None)
            await update.message.reply_text(
                f"✅ Записано! {emoji}\n*{amount:,.0f} ₸* — {category}\nID: `#{expense_id}`",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD,
            )

    elif user_state.get(user_id, {}).get("step") == "waiting_amount":
        amount = stats.validate_amount(text)
        if amount is None:
            await update.message.reply_text("❌ Неверная сумма. Введите число, например `1500`:", parse_mode="Markdown")
            return
        user_state[user_id] = {"step": "waiting_category", "amount": amount}
        await update.message.reply_text(
            f"Сумма: *{amount:,.0f} ₸*\nВыберите категорию 👇",
            parse_mode="Markdown",
            reply_markup=CATEGORY_KEYBOARD,
        )

    else:
        await update.message.reply_text("Используйте кнопки меню или /help.", reply_markup=MAIN_KEYBOARD)


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Неизвестная команда. Напишите /help.", reply_markup=MAIN_KEYBOARD)
