"""Multi-user isolation: one user never sees, changes or is limited by another
user's expenses and budgets. Alice is `user_id`, Bob is `other_user_id`."""

import asyncio
from datetime import date

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from sqlalchemy.exc import IntegrityError

from mcp_server.expenses_tracker.config import load_settings
from mcp_server.expenses_tracker.models.BudgetModels import Budget
from mcp_server.expenses_tracker.models.ExpenseModels import ExpenseIn
from mcp_server.expenses_tracker.server import create_app

OCT = date(2025, 10, 15)


def expense(amount, category="food", day=OCT):
    return ExpenseIn(amount=amount, category=category, description="x", expense_date=day)


# ---- repositories ----

def test_users_only_list_their_own_expenses(expense_repo, user_id, other_user_id):
    expense_repo.add(user_id, expense(10))
    expense_repo.add(other_user_id, expense(20))
    assert [e.amount for e in expense_repo.between_dates(user_id, OCT, OCT)] == [10]
    assert [e.amount for e in expense_repo.between_dates(other_user_id, OCT, OCT)] == [20]


def test_cannot_delete_another_users_expense(expense_repo, user_id, other_user_id):
    alices = expense_repo.add(user_id, expense(10))
    # Same message as a missing id, so Bob can't tell the id exists.
    with pytest.raises(ValueError, match=f"No expense with id {alices.id}"):
        expense_repo.delete_expense(other_user_id, alices.id)
    assert len(expense_repo.between_dates(user_id, OCT, OCT)) == 1


def test_same_category_budget_is_separate_per_user(budget_repo, user_id, other_user_id):
    budget_repo.save_budget(user_id, Budget(category="food", amount=100))
    budget_repo.save_budget(other_user_id, Budget(category="food", amount=500))
    assert budget_repo.get_budget(user_id, "food").amount == 100
    assert budget_repo.get_budget(other_user_id, "food").amount == 500


def test_cannot_delete_another_users_budget(budget_repo, user_id, other_user_id):
    budget_repo.save_budget(user_id, Budget(category="food", amount=100))
    with pytest.raises(ValueError, match="No budget for food"):
        budget_repo.delete_budget(other_user_id, "food")
    assert budget_repo.get_budget(user_id, "food") is not None


def test_unknown_user_cannot_save(expense_repo):
    # Foreign key: a user must exist (ensure_user) before saving anything.
    with pytest.raises(IntegrityError):
        expense_repo.add("nobody", expense(10))


# ---- services ----

def test_monthly_summary_counts_only_own_spending(expense_service, user_id, other_user_id):
    expense_service.add_expense(user_id, expense(10))
    expense_service.add_expense(other_user_id, expense(1000))
    assert expense_service.monthly_summary(user_id, 2025, 10).total == 10


def test_another_users_total_does_not_limit_my_budgets(budget_service, user_id, other_user_id):
    budget_service.add_budget(user_id, Budget(category="total", amount=100))
    # Would break Alice's total, but it's Bob's budget, so it's allowed.
    budget_service.add_budget(other_user_id, Budget(category="food", amount=500))
    assert [b.category for b in budget_service.get_all_budgets(other_user_id)] == ["food"]


def test_alerts_ignore_another_users_spending(
    expense_service, budget_service, user_id, other_user_id
):
    budget_service.add_budget(user_id, Budget(category="food", amount=100))
    budget_service.add_budget(other_user_id, Budget(category="food", amount=100))
    expense_service.add_expense(other_user_id, expense(95))  # Bob near his limit

    saved = expense_service.add_expense(user_id, expense(10))
    assert budget_service.alerts_for(user_id, saved) == []
    assert budget_service.budget_status(user_id, 2025, 10)[0].spent == 10


# ---- end to end through the tools ----

def test_tools_keep_users_apart(db, database_url):
    """Two servers on the same database, each acting as a different user, the
    way two logged-in users will share one database in the cloud."""
    def server_for(user):
        return create_app(
            load_settings({"EXPENSES_DATABASE_URL": database_url, "EXPENSES_DEV_USER_ID": user})
        )

    alice, bob = server_for("alice"), server_for("bob")
    today = date.today()

    async def run():
        async with Client(alice) as a, Client(bob) as b:
            saved = await a.call_tool(
                "new_expense",
                {"expense": {"amount": 45, "category": "food", "description": "falafel"}},
            )
            listed = await b.call_tool(
                "list_expenses",
                {"first_date": today.isoformat(), "last_date": today.isoformat()},
            )
            summary = await b.call_tool(
                "summary_by_category", {"year": today.year, "month": today.month}
            )
            with pytest.raises(ToolError, match="No expense with id"):
                await b.call_tool(
                    "delete_expense", {"expense_id": saved.structured_content["id"]}
                )
            return listed.structured_content["result"], summary.structured_content["total"]

    bob_list, bob_total = asyncio.run(run())
    assert bob_list == []
    assert bob_total == 0
