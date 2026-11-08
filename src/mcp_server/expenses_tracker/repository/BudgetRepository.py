from ..db import Database
from ..models.BudgetModels import Budget, BudgetCategory
from ..parser import to_agorot, to_shekels


def _to_budget(row) -> Budget:
    return Budget(category=row["category"], amount=to_shekels(row["amount_agorot"]))


class BudgetRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_budget(self, user_id: str, budget: Budget) -> Budget:
        """Create the user's budget, or update its amount if this user already
        has one for the category. Other users' budgets are never touched."""
        with self.db.transaction() as con:
            con.execute(
                """
                INSERT INTO budgets (user_id, category, amount_agorot)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, category) DO UPDATE SET amount_agorot = excluded.amount_agorot
                """,
                (user_id, budget.category, to_agorot(budget.amount)),
            )
        return budget

    def get_budget(self,user_id:str, category: BudgetCategory) -> Budget | None:
        with self.db.transaction() as con:
            row = con.execute(
                "SELECT * FROM budgets WHERE category = ? and user_id = ?", (category,user_id,)
            ).fetchone()
        return _to_budget(row) if row else None

    def get_all_budgets(self, user_id:str) -> list[Budget]:
        with self.db.transaction() as con:
            rows = con.execute("SELECT * FROM budgets WHERE user_id = ?ORDER BY category",(user_id,)).fetchall()
        return [_to_budget(row) for row in rows]

    def delete_budget(self, user_id:str,category: BudgetCategory) -> BudgetCategory:
        with self.db.transaction() as con:
            cur = con.execute("DELETE FROM budgets WHERE category = ? AND user_id = ?", (category,user_id,))
            if cur.rowcount == 0:
                raise ValueError(f"No budget for {category}")
        return category
