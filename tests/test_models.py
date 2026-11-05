from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from mcp_server.expenses_tracker.models.BudgetModels import Budget
from mcp_server.expenses_tracker.models.ExpenseModels import ExpenseIn


def test_valid_expense_defaults_to_today():
    expense = ExpenseIn(amount=45, category="food", description="falafel")
    assert expense.expense_date == date.today()


@pytest.mark.parametrize(
    "fields",
    [
        {"amount": 0, "category": "food", "description": "x"},
        {"amount": -5, "category": "food", "description": "x"},
        {"amount": 10, "category": "groceries", "description": "x"},
        {"amount": 10, "category": "food", "description": ""},
        {
            "amount": 10,
            "category": "food",
            "description": "x",
            "expense_date": date.today() + timedelta(days=1),
        },
    ],
    ids=["zero", "negative", "unknown-category", "empty-description", "future-date"],
)
def test_invalid_expense_is_rejected(fields):
    with pytest.raises(ValidationError):
        ExpenseIn(**fields)


def test_budget_accepts_category_or_total():
    assert Budget(category="food", amount=500).category == "food"
    assert Budget(category="total", amount=3000).category == "total"


@pytest.mark.parametrize(
    "fields",
    [{"category": "food", "amount": 0}, {"category": "pets", "amount": 100}],
    ids=["zero-amount", "unknown-category"],
)
def test_invalid_budget_is_rejected(fields):
    with pytest.raises(ValidationError):
        Budget(**fields)
