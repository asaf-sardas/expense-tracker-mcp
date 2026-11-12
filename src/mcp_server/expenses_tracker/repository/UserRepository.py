from ..db import Database


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def ensure_user(self, user_id: str, email: str | None = None) -> str:
        """Create the user's row if it doesn't exist yet; an existing user is left
        as is. Expenses and budgets reference users, so this must run before a
        user's first save."""
        with self.db.transaction() as con:
            con.execute(
                "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
                (user_id, email),
            )
        return user_id
