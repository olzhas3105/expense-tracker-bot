"""
stats.py — подсчёт статистики и формирование отчётов.
"""

from collections import defaultdict
from datetime import datetime, timedelta

import database


CATEGORIES = {
    "еда": "🍔",
    "транспорт": "🚌",
    "здоровье": "💊",
    "развлечения": "🎮",
    "одежда": "👕",
    "жильё": "🏠",
    "другое": "📦",
}


def get_category_emoji(category: str) -> str:
    """Возвращает эмодзи для категории, или 📦 если не найдено."""
    return CATEGORIES.get(category.lower(), "📦")


def build_summary(user_id: int, days: int = 30) -> str:
    """
    Формирует текстовый отчёт за последние N дней.

    Args:
        user_id: Telegram ID пользователя.
        days:    Количество дней для анализа.

    Returns:
        Готовый текст для отправки в Telegram.
    """
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    rows = database.get_expenses_by_period(user_id, start, end)

    if not rows:
        return f"За последние {days} дней расходов не найдено."

    total = 0.0
    by_category: dict[str, float] = defaultdict(float)

    for row in rows:
        total += row["amount"]
        by_category[row["category"]] += row["amount"]

    lines = [f"📊 *Отчёт за {days} дней*\n"]

    sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    for cat, amount in sorted_cats:
        emoji = get_category_emoji(cat)
        pct = amount / total * 100
        lines.append(f"{emoji} {cat.capitalize()}: *{amount:,.0f} ₸* ({pct:.0f}%)")

    lines.append(f"\n💰 *Итого: {total:,.0f} ₸*")
    lines.append(f"📅 {start} — {end}")

    return "\n".join(lines)


def build_last_expenses(user_id: int, limit: int = 5) -> str:
    """Формирует список последних N расходов пользователя."""
    rows = database.get_expenses(user_id, limit=limit)

    if not rows:
        return "У вас пока нет записанных расходов."

    lines = ["🧾 *Последние расходы:*\n"]
    for row in rows:
        emoji = get_category_emoji(row["category"])
        date = row["created_at"][:10]
        note = f" — {row['note']}" if row["note"] else ""
        lines.append(
            f"`#{row['id']}` {emoji} {row['amount']:,.0f} ₸  "
            f"[{row['category']}]{note}  _{date}_"
        )

    return "\n".join(lines)


def validate_amount(text: str) -> float | None:
    """
    Проверяет и парсит сумму из текста.

    Returns:
        Число > 0 или None если неверный формат.
    """
    try:
        amount = float(text.replace(",", ".").replace(" ", ""))
        return amount if amount > 0 else None
    except ValueError:
        return None


def validate_category(text: str) -> str:
    """
    Нормализует категорию. Если не из списка — ставит 'другое'.
    """
    cleaned = text.lower().strip()
    return cleaned if cleaned in CATEGORIES else "другое"

