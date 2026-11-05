from mcp_server.expenses_tracker.models.BudgetModels import Budget


def rows(db):
    with db.transaction() as con:
        return {
            r["category"]: r["amount_agorot"]
            for r in con.execute("SELECT * FROM budgets")
        }


def test_add_budget_stores_agorot(db, budget_repo):
    budget_repo.add_budget(Budget(category="food", amount=1500.5))
    assert rows(db) == {"food": 150050}


def test_add_budget_twice_updates_instead_of_failing(db, budget_repo):
    budget_repo.add_budget(Budget(category="food", amount=500))
    budget_repo.add_budget(Budget(category="food", amount=700))
    assert rows(db) == {"food": 70000}


def test_total_and_category_budgets_coexist(db, budget_repo):
    budget_repo.add_budget(Budget(category="total", amount=3000))
    budget_repo.add_budget(Budget(category="food", amount=1000))
    assert rows(db) == {"total": 300000, "food": 100000}
