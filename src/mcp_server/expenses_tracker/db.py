import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path



class Database:
    def __init__(self, path: Path):
        self.path = path
        with self.transaction() as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS expenses 
            (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount_agorot INTEGER NOT NULL CHECK(amount_agorot>0),
            description TEXT NOT NULL, 
            category TEXT NOT NULL,
            expense_date DATE  NOT NULL 
            );
            """)
            con.execute("""
                        CREATE TABLE IF NOT EXISTS budgets (
                        category TEXT PRIMARY KEY,
                        amount_agorot INTEGER NOT NULL CHECK (amount_agorot > 0)
                        );
                        """)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
