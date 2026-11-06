from ..db import Database
from ..models.BudgetModels import Budget, BudgetCategory
from ..parser import to_agorot, to_shekels


def _to_budget(row) -> Budget:
    return Budget(category=row["category"], amount=to_shekels(row["amount_agorot"]))


class BudgetRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_budget(self, budget: Budget) -> Budget:
        """Create the budget, or update its amount if the category already has one."""
        with self.db.transaction() as con:
            con.execute(
                """
                INSERT INTO budgets (category, amount_agorot)
                VALUES (?, ?)
                ON CONFLICT(category) DO UPDATE SET amount_agorot = excluded.amount_agorot
                """,
                (budget.category, to_agorot(budget.amount)),
            )
        return budget

    def get_budget(self, category: BudgetCategory) -> Budget | None:
        with self.db.transaction() as con:
            row = con.execute(
                "SELECT * FROM budgets WHERE category = ?", (category,)
            ).fetchone()
        return _to_budget(row) if row else None

    def get_all_budgets(self) -> list[Budget]:
        with self.db.transaction() as con:
            rows = con.execute("SELECT * FROM budgets ORDER BY category").fetchall()
        return [_to_budget(row) for row in rows]

    def delete_budget(self, category: BudgetCategory) -> BudgetCategory:
        with self.db.transaction() as con:
            cur = con.execute("DELETE FROM budgets WHERE category = ?", (category,))
            if cur.rowcount == 0:
                raise ValueError(f"No budget for {category}")
        return category
