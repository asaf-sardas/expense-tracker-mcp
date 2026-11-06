import pytest

from mcp_server.expenses_tracker.models.BudgetModels import Budget


def rows(db):
    with db.transaction() as con:
        return {
            r["category"]: r["amount_agorot"]
            for r in con.execute("SELECT * FROM budgets")
        }


def test_save_budget_stores_agorot(db, budget_repo):
    saved = budget_repo.save_budget(Budget(category="food", amount=1500.5))
    assert saved == Budget(category="food", amount=1500.5)
    assert rows(db) == {"food": 150050}


def test_save_budget_twice_updates_instead_of_failing(db, budget_repo):
    budget_repo.save_budget(Budget(category="food", amount=500))
    budget_repo.save_budget(Budget(category="food", amount=700))
    assert rows(db) == {"food": 70000}


def test_total_and_category_budgets_coexist(db, budget_repo):
    budget_repo.save_budget(Budget(category="total", amount=3000))
    budget_repo.save_budget(Budget(category="food", amount=1000))
    assert rows(db) == {"total": 300000, "food": 100000}


def test_get_budget_returns_shekels(budget_repo):
    budget_repo.save_budget(Budget(category="food", amount=12.9))
    assert budget_repo.get_budget("food") == Budget(category="food", amount=12.9)


def test_get_missing_budget_returns_none(budget_repo):
    assert budget_repo.get_budget("travel") is None


def test_get_all_budgets_sorted_by_category(budget_repo):
    budget_repo.save_budget(Budget(category="transport", amount=300))
    budget_repo.save_budget(Budget(category="total", amount=3000))
    budget_repo.save_budget(Budget(category="food", amount=1000))
    assert [b.category for b in budget_repo.get_all_budgets()] == [
        "food",
        "total",
        "transport",
    ]


def test_get_all_budgets_empty(budget_repo):
    assert budget_repo.get_all_budgets() == []


def test_delete_budget(db, budget_repo):
    budget_repo.save_budget(Budget(category="food", amount=500))
    assert budget_repo.delete_budget("food") == "food"
    assert rows(db) == {}


def test_delete_missing_budget_raises(budget_repo):
    with pytest.raises(ValueError, match="No budget for food"):
        budget_repo.delete_budget("food")
