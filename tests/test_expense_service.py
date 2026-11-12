from datetime import date

import pytest

from mcp_server.expenses_tracker.models.ExpenseModels import ExpenseIn


@pytest.fixture
def add(expense_service, user_id):
    def _add(amount, category, day):
        expense_service.add_expense(
            user_id,
            ExpenseIn(amount=amount, category=category, description="x", expense_date=day),
        )

    return _add


def test_monthly_summary_totals_by_category(add, expense_service, user_id):
    add(45, "food", date(2026, 10, 1))
    add(12.9, "food", date(2026, 10, 31))
    add(120, "transport", date(2026, 10, 15))
    add(999, "travel", date(2026, 11, 1))  # other month

    summary = expense_service.monthly_summary(user_id, 2026, 10)

    assert summary.total == 177.9
    assert summary.expenses_by_category == {"food": 57.9, "transport": 120.0}


def test_monthly_summary_has_no_float_drift(add, expense_service, user_id):
    add(0.1, "food", date(2026, 10, 1))
    add(0.2, "food", date(2026, 10, 2))
    assert expense_service.monthly_summary(user_id, 2026, 10).total == 0.3


def test_monthly_summary_handles_february_in_leap_year(add, expense_service, user_id):
    add(10, "food", date(2024, 2, 29))
    assert expense_service.monthly_summary(user_id, 2024, 2).total == 10


def test_monthly_summary_of_empty_month(expense_service, user_id):
    summary = expense_service.monthly_summary(user_id, 2026, 1)
    assert summary.total == 0
    assert summary.expenses_by_category == {}


def test_expenses_between_dates_accepts_reversed_range(add, expense_service, user_id):
    add(10, "food", date(2026, 10, 10))
    result = expense_service.expenses_between_dates(
        user_id, date(2026, 10, 31), date(2026, 10, 1)
    )
    assert len(result) == 1


def test_delete_expense(expense_service, user_id):
    saved = expense_service.add_expense(
        user_id, ExpenseIn(amount=5, category="other", description="x")
    )
    assert expense_service.delete_expense(user_id, saved.id) == saved.id
