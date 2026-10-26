import sqlite3
from pathlib import Path

import pandas as pd

# The database stays in the project folder, alongside this Python file.
DB_NAME = str(Path(__file__).resolve().with_name("expenses.db"))


def create_table():
    """Create the expense/settings tables and initialise the default budget."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                name TEXT PRIMARY KEY,
                value REAL NOT NULL
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO settings (name, value)
            VALUES ('monthly_budget', 10000)
        """)


def add_expense(amount, category, expense_date, description):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO expenses (amount, category, date, description)
            VALUES (?, ?, ?, ?)
            """,
            (float(amount), str(category), str(expense_date), str(description)),
        )


def get_expenses():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC",
            conn,
        )


def delete_expense(expense_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (int(expense_id),),
        )


def get_budget():
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute(
            "SELECT value FROM settings WHERE name = 'monthly_budget'"
        ).fetchone()
    return float(result[0]) if result else 10000.0


def set_budget(amount):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO settings (name, value)
            VALUES ('monthly_budget', ?)
            ON CONFLICT(name) DO UPDATE SET value = excluded.value
            """,
            (float(amount),),
        )
