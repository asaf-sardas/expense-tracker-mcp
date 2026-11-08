from datetime import date

import pytest

from mcp_server.expenses_tracker.models.ExpenseModels import ExpenseIn


def make(amount=10.0, category="food", description="x", day=date(2026, 10, 15)):
    return ExpenseIn(
        amount=amount, category=category, description=description, expense_date=day
    )


def test_add_returns_expense_with_id(expense_repo, user_id):
    saved = expense_repo.add(user_id, make(amount=19.99, description="falafel"))
    assert saved.id == 1
    assert saved.amount == 19.99
    assert saved.description == "falafel"


def test_amount_survives_round_trip_exactly(expense_repo, user_id):
    expense_repo.add(user_id, make(amount=12.9))
    [loaded] = expense_repo.between_dates(user_id, date(2026, 10, 1), date(2026, 10, 31))
    assert loaded.amount == 12.9


def test_between_dates_is_inclusive_and_sorted(expense_repo, user_id):
    expense_repo.add(user_id, make(description="after", day=date(2026, 11, 1)))
    expense_repo.add(user_id, make(description="last", day=date(2026, 10, 31)))
    expense_repo.add(user_id, make(description="first", day=date(2026, 10, 1)))
    expense_repo.add(user_id, make(description="before", day=date(2026, 9, 30)))

    result = expense_repo.between_dates(user_id, date(2026, 10, 1), date(2026, 10, 31))

    assert [e.description for e in result] == ["first", "last"]


def test_delete_removes_expense(expense_repo, user_id):
    saved = expense_repo.add(user_id, make())
    assert expense_repo.delete_expense(user_id, saved.id) == saved.id
    assert expense_repo.between_dates(user_id, date(2000, 1, 1), date.today()) == []


def test_delete_unknown_id_raises(expense_repo, user_id):
    with pytest.raises(ValueError, match="No expense with id 999"):
        expense_repo.delete_expense(user_id, 999)
