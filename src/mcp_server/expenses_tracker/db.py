import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path
        with self.transaction() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount_agorot INTEGER NOT NULL CHECK (amount_agorot > 0),
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    expense_date DATE NOT NULL
                );
            """)
            # Every expense query filters by user and then by date.
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses (user_id, expense_date);
            """)
            # user_id first in the key, so "all budgets of a user" uses the index.
            con.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category TEXT NOT NULL,
                    amount_agorot INTEGER NOT NULL CHECK (amount_agorot > 0),
                    PRIMARY KEY (user_id, category)
                );
            """)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        # SQLite ignores REFERENCES unless this is turned on for each connection.
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
