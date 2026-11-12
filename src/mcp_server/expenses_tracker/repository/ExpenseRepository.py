from datetime import date

from sqlalchemy import text

from ..db import Database
from ..models.ExpenseModels import Expense, ExpenseIn
from ..parser import to_agorot, to_shekels


def _to_expense(row) -> Expense:
    return Expense(
        id=row["id"],
        amount=to_shekels(row["amount_agorot"]),
        category=row["category"],
        description=row["description"],
        expense_date=row["expense_date"],  # Postgres DATE comes back as a date
    )


class ExpenseRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, user_id: str, expense: ExpenseIn) -> Expense:
        with self.db.transaction() as con:
            new_id = con.execute(
                text("""
                    INSERT INTO expenses (user_id, amount_agorot, description, category, expense_date)
                    VALUES (:user_id, :amount_agorot, :description, :category, :expense_date)
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "amount_agorot": to_agorot(expense.amount),
                    "description": expense.description,
                    "category": expense.category,
                    "expense_date": expense.expense_date,
                },
            ).scalar_one()
        return Expense(id=new_id, **expense.model_dump())

    def between_dates(self, user_id: str, beginning: date, last: date) -> list[Expense]:
        """Return the user's expenses from beginning to last, both dates included."""
        with self.db.transaction() as con:
            rows = con.execute(
                text("""
                    SELECT *
                    FROM expenses
                    WHERE user_id = :user_id
                      AND expense_date BETWEEN :beginning AND :last
                    ORDER BY expense_date, id
                """),
                {"user_id": user_id, "beginning": beginning, "last": last},
            ).mappings().all()
        return [_to_expense(row) for row in rows]

    def delete_expense(self, user_id: str, expense_id: int) -> int:
        with self.db.transaction() as con:
            result = con.execute(
                text("DELETE FROM expenses WHERE id = :id AND user_id = :user_id"),
                {"id": expense_id, "user_id": user_id},
            )
            # Same error whether the id doesn't exist or belongs to someone else.
            if result.rowcount == 0:
                raise ValueError(f"No expense with id {expense_id}")
        return expense_id
