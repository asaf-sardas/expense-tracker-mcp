from sqlalchemy import text

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
                text("""
                    INSERT INTO users (id, email) VALUES (:id, :email)
                    ON CONFLICT (id) DO NOTHING
                """),
                {"id": user_id, "email": email},
            )
        return user_id
