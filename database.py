import sqlite3
from datetime import datetime

DB_PATH = "expenses.db"

def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    # Позволяет обращаться к полям по именам: row['amount']
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Инициализирует таблицу расходов при первом запуске."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def add_expense(user_id: int, amount: float, category: str, note: str = "") -> int:
    """Добавляет новый расход и возвращает его ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
            (user_id, amount, category, note)
        )
        conn.commit()
        return cursor.lastrowid

def get_expenses(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    """Возвращает последние N расходов конкретного пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return rows

def delete_expense(user_id: int, expense_id: int) -> bool:
    """
    Удаляет расход по ID (только если он принадлежит пользователю).
    Returns: True если запись удалена, False если не найдена.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0