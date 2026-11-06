"""Budget status and the 80% / 100% alerts returned when adding an expense.
Fixed dates in 2025 keep the tests independent of today's date."""

from datetime import date

import pytest

from mcp_server.expenses_tracker.models.BudgetModels import Budget
from mcp_server.expenses_tracker.models.ExpenseModels import ExpenseIn

OCT = date(2025, 10, 15)
SEP = date(2025, 9, 15)


@pytest.fixture
def budgets(budget_service):
    def _set(**amounts):
        for category, amount in amounts.items():
            budget_service.add_budget(Budget(category=category, amount=amount))

    return _set


@pytest.fixture
def spend(expense_service, budget_service):
    """Add an expense and return the alerts it triggers, as the tool does."""

    def _spend(amount, category="food", day=OCT):
        saved = expense_service.add_expense(
            ExpenseIn(amount=amount, category=category, description="x", expense_date=day)
        )
        return budget_service.alerts_for(saved)

    return _spend


def levels(alerts):
    return [(a.category, a.level) for a in alerts]


# ---- budget_status ----

def test_status_with_no_budgets_is_empty(budget_service, spend):
    spend(50)
    assert budget_service.budget_status(2025, 10) == []


def test_status_under_budget(budget_service, budgets, spend):
    budgets(food=100)
    spend(25)
    [status] = budget_service.budget_status(2025, 10)
    assert status.category == "food"
    assert (status.limit, status.spent, status.remaining) == (100, 25, 75)
    assert status.percent_used == 25
    assert status.exceeded is False


def test_status_over_budget_has_negative_remaining(budget_service, budgets, spend):
    budgets(food=100)
    spend(120)
    [status] = budget_service.budget_status(2025, 10)
    assert status.remaining == -20
    assert status.percent_used == 120
    assert status.exceeded is True


def test_status_budget_with_no_spending(budget_service, budgets):
    budgets(travel=500)
    [status] = budget_service.budget_status(2025, 10)
    assert (status.spent, status.remaining, status.exceeded) == (0, 500, False)


def test_total_status_counts_all_categories(budget_service, budgets, spend):
    budgets(total=1000)
    spend(100, "food")
    spend(250, "transport")
    [status] = budget_service.budget_status(2025, 10)
    assert status.spent == 350


def test_status_ignores_other_months(budget_service, budgets, spend):
    budgets(food=100)
    spend(90, day=SEP)
    spend(10, day=OCT)
    [status] = budget_service.budget_status(2025, 10)
    assert status.spent == 10


def test_status_has_no_float_drift(budget_service, budgets, spend):
    budgets(food=0.3)
    spend(0.1)
    spend(0.2)
    [status] = budget_service.budget_status(2025, 10)
    assert status.remaining == 0
    assert status.exceeded is True


# ---- alerts ----

def test_no_alert_under_80_percent(budgets, spend):
    budgets(food=100)
    assert spend(79.99) == []


def test_warning_at_exactly_80_percent(budgets, spend):
    budgets(food=100)
    assert levels(spend(80)) == [("food", "warning")]


def test_warning_between_80_and_100(budgets, spend):
    budgets(food=100)
    assert levels(spend(85)) == [("food", "warning")]


def test_exceeded_at_exactly_100_percent(budgets, spend):
    budgets(food=100)
    assert levels(spend(100)) == [("food", "exceeded")]


def test_over_100_gives_only_exceeded(budgets, spend):
    budgets(food=100)
    assert levels(spend(150)) == [("food", "exceeded")]


def test_alert_counts_earlier_expenses_in_month(budgets, spend):
    budgets(food=100)
    assert spend(50) == []
    assert levels(spend(35)) == [("food", "warning")]


def test_warning_repeats_on_every_expense(budgets, spend):
    budgets(food=100)
    spend(85)
    assert levels(spend(1)) == [("food", "warning")]


def test_no_alert_for_category_without_budget(budgets, spend):
    budgets(food=100)
    assert spend(500, "transport") == []


def test_other_categories_over_budget_are_not_reported(budgets, spend):
    budgets(food=100, transport=50)
    spend(60, "transport")  # transport is over budget
    assert spend(10, "food") == []


def test_total_alert_for_category_without_budget(budgets, spend):
    budgets(total=1000)
    assert levels(spend(900, "travel")) == [("total", "warning")]


def test_category_and_total_can_both_alert(budgets, spend):
    budgets(total=1000, food=500)
    assert levels(spend(900)) == [("food", "exceeded"), ("total", "warning")]


def test_backdated_expense_is_checked_against_its_own_month(budgets, spend):
    budgets(food=100)
    spend(50, day=SEP)
    spend(70, day=OCT)
    assert levels(spend(35, day=SEP)) == [("food", "warning")]


def test_alert_messages_show_the_amounts(budgets, spend):
    budgets(food=100)
    [warning] = spend(85)
    assert warning.message == "Food budget at 85%: ₪85.00 of ₪100.00, ₪15.00 left."
    assert warning.percent_used == 85

    [exceeded] = spend(30)
    assert exceeded.message == "Food budget exceeded: ₪115.00 of ₪100.00 (115%)."


def test_total_alert_message(budgets, spend):
    budgets(total=1000)
    [alert] = spend(1200, "travel")
    assert alert.message == "Total budget exceeded: ₪1,200.00 of ₪1,000.00 (120%)."


def test_custom_thresholds(budget_repo, expense_service):
    from mcp_server.expenses_tracker.services.BudgetService import BudgetService

    service = BudgetService(
        budget_repo, expense_service, warning_percent=50, exceeded_percent=90
    )
    service.add_budget(Budget(category="food", amount=100))

    def spend(amount):
        saved = expense_service.add_expense(
            ExpenseIn(amount=amount, category="food", description="x", expense_date=OCT)
        )
        return levels(service.alerts_for(saved))

    assert spend(49) == []
    assert spend(1) == [("food", "warning")]  # 50%
    assert spend(40) == [("food", "exceeded")]  # 90%
