from ..db import Database
from ..models.ExpenseModels import Expense, ExpenseIn
from datetime import date
from ..parser import to_agorot, to_shekels


def _to_expense(row) -> Expense:
    return Expense(
        id=row["id"],
        amount=to_shekels(row["amount_agorot"]),
        category=row["category"],
        description=row["description"],
        expense_date=date.fromisoformat(row["expense_date"]),
    )


class ExpenseRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, user_id:str, expense: ExpenseIn) -> Expense:
        with self.db.transaction() as con:
            new_id = con.execute(
                """
                INSERT INTO expenses (amount_agorot, user_id, description, category, expense_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    to_agorot(expense.amount),
                    user_id,
                    expense.description,
                    expense.category,
                    expense.expense_date.isoformat(),
                ),
            ).lastrowid
        return Expense(id=new_id, **expense.model_dump())

    def between_dates(self,user_id:str, beginning: date, last: date) -> list[Expense]:
        """Return expenses from beginning to last, both dates included."""
        with self.db.transaction() as con:
            rows = con.execute(
                """
                SELECT *
                FROM expenses as e
                WHERE e.expense_date BETWEEN ? AND ? AND e.user_id=?
                ORDER BY expense_date, id              
                """,
                (
                    beginning.isoformat(),
                    last.isoformat(),
                    user_id,
                ),
            ).fetchall()
        return [_to_expense(row) for row in rows]

    def delete_expense(self,user_id:str, expense_id: int) -> int:
        with self.db.transaction() as con:
            cur = con.execute(
                """
                            DELETE FROM expenses
                            WHERE expenses.id=? AND expenses.user_id=? """,
                (   
                    expense_id,
                    user_id,
                 ),
            )
            if cur.rowcount == 0:
                raise ValueError(f"No expense with id {expense_id}")
            else:
                return expense_id
