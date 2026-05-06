import sqlite3
from datetime import datetime
DB_PATH = "expenses.db"


def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Инициализирует таблицу расходов при первом запуске."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                amount    REAL    NOT NULL,
                category  TEXT    NOT NULL,
                note      TEXT,
                created_at TEXT   NOT NULL
            )
        """)
        conn.commit()


def add_expense(user_id: int, amount: float, category: str, note: str = "") -> int:
    """
    Добавляет новый расход в базу.

    Args:
        user_id:  Telegram ID пользователя.
        amount:   Сумма расхода (> 0).
        category: Категория (еда, транспорт и т.д.).
        note:     Необязательная заметка.

    Returns:
        ID новой записи.
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category.lower().strip(), note.strip(), created_at),
        )
        conn.commit()
        return cursor.lastrowid


def get_expenses(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    """Возвращает последние расходы пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return rows


def delete_expense(user_id: int, expense_id: int) -> bool:
    """
    Удаляет расход по ID (только свой).

    Returns:
        True если запись удалена, False если не найдена.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_expenses_by_period(user_id: int, start: str, end: str) -> list[sqlite3.Row]:
    """Возвращает расходы пользователя за указанный период (YYYY-MM-DD)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM expenses
               WHERE user_id = ?
                 AND DATE(created_at) BETWEEN ? AND ?
               ORDER BY created_at DESC""",
            (user_id, start, end),
        ).fetchall()
    return rows