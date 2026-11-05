from ..db import Database
from ..models.BudgetModels import Budget
from..parser import to_agorot


class BudgetRepository:
    def __init__(self,db:Database):
        self.db=db
    def add_budget(self,budget:Budget):
        with self.db.transaction() as con:
            con.execute(
                """
                INSERT INTO budgets (category, amount_agorot)
                VALUES (?, ?)
                ON CONFLICT(category) DO UPDATE SET amount_agorot = excluded.amount_agorot
                """,
                (
                    budget.category,
                    to_agorot(budget.amount)
                    )
            )