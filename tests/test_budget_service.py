import pytest

from mcp_server.expenses_tracker.models.BudgetModels import Budget


def setup(service, **budgets):
    for category, amount in budgets.items():
        service.add_budget(Budget(category=category, amount=amount))


def saved(budget_repo):
    return {b.category: b.amount for b in budget_repo.get_all_budgets()}


# ---- allowed changes ----

def test_add_budget_saves_it(budget_service, budget_repo):
    result = budget_service.add_budget(Budget(category="food", amount=500))
    assert result == Budget(category="food", amount=500)
    assert saved(budget_repo) == {"food": 500}


def test_categories_without_total_have_no_limit(budget_service, budget_repo):
    setup(budget_service, food=700, transport=5000)
    assert saved(budget_repo) == {"food": 700, "transport": 5000}


def test_categories_equal_to_total_are_allowed(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700, transport=300)
    assert saved(budget_repo) == {"total": 1000, "food": 700, "transport": 300}


def test_total_equal_to_categories_is_allowed(budget_service, budget_repo):
    setup(budget_service, food=700, transport=300, total=1000)
    assert saved(budget_repo)["total"] == 1000


def test_lowering_a_category_is_allowed(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700, transport=300)
    budget_service.add_budget(Budget(category="food", amount=500))
    assert saved(budget_repo)["food"] == 500


def test_updating_a_category_replaces_its_old_amount(budget_service, budget_repo):
    # 700 -> 1000 makes the sum 1000, not 1700, so it fits
    setup(budget_service, total=1000, food=700)
    budget_service.add_budget(Budget(category="food", amount=1000))
    assert saved(budget_repo)["food"] == 1000


def test_raising_total_is_allowed(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700)
    budget_service.add_budget(Budget(category="total", amount=2000))
    assert saved(budget_repo)["total"] == 2000


def test_agorot_precision_at_the_limit(budget_service, budget_repo):
    # 0.1 + 0.2 must count as exactly 0.3, not 0.30000000000000004
    setup(budget_service, total=0.3, food=0.1, transport=0.2)
    assert saved(budget_repo)["transport"] == 0.2


# ---- rejected changes save nothing ----

def test_new_category_over_total_is_rejected(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(Budget(category="transport", amount=400))
    assert saved(budget_repo) == {"total": 1000, "food": 700}


def test_new_total_below_categories_is_rejected(budget_service, budget_repo):
    setup(budget_service, food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(Budget(category="total", amount=900))
    assert "total" not in saved(budget_repo)


def test_raising_category_over_total_keeps_old_value(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(Budget(category="food", amount=800))
    assert saved(budget_repo)["food"] == 700


def test_lowering_total_below_categories_keeps_old_value(budget_service, budget_repo):
    setup(budget_service, total=1000, food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(Budget(category="total", amount=999.99))
    assert saved(budget_repo)["total"] == 1000


def test_error_message_explains_the_numbers(budget_service):
    setup(budget_service, total=1000, food=700)
    with pytest.raises(ValueError) as error:
        budget_service.add_budget(Budget(category="transport", amount=400))
    assert "₪1,100.00" in str(error.value)
    assert "₪1,000.00" in str(error.value)
