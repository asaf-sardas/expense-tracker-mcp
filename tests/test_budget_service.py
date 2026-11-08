import pytest

from mcp_server.expenses_tracker.models.BudgetModels import Budget


@pytest.fixture
def setup(budget_service, user_id):
    def _setup(**budgets):
        for category, amount in budgets.items():
            budget_service.add_budget(user_id, Budget(category=category, amount=amount))

    return _setup


@pytest.fixture
def saved(budget_repo, user_id):
    def _saved():
        return {b.category: b.amount for b in budget_repo.get_all_budgets(user_id)}

    return _saved


# ---- allowed changes ----

def test_add_budget_saves_it(budget_service, saved, user_id):
    result = budget_service.add_budget(user_id, Budget(category="food", amount=500))
    assert result == Budget(category="food", amount=500)
    assert saved() == {"food": 500}


def test_categories_without_total_have_no_limit(setup, saved):
    setup(food=700, transport=5000)
    assert saved() == {"food": 700, "transport": 5000}


def test_categories_equal_to_total_are_allowed(setup, saved):
    setup(total=1000, food=700, transport=300)
    assert saved() == {"total": 1000, "food": 700, "transport": 300}


def test_total_equal_to_categories_is_allowed(setup, saved):
    setup(food=700, transport=300, total=1000)
    assert saved()["total"] == 1000


def test_lowering_a_category_is_allowed(budget_service, setup, saved, user_id):
    setup(total=1000, food=700, transport=300)
    budget_service.add_budget(user_id, Budget(category="food", amount=500))
    assert saved()["food"] == 500


def test_updating_a_category_replaces_its_old_amount(budget_service, setup, saved, user_id):
    # 700 -> 1000 makes the sum 1000, not 1700, so it fits
    setup(total=1000, food=700)
    budget_service.add_budget(user_id, Budget(category="food", amount=1000))
    assert saved()["food"] == 1000


def test_raising_total_is_allowed(budget_service, setup, saved, user_id):
    setup(total=1000, food=700)
    budget_service.add_budget(user_id, Budget(category="total", amount=2000))
    assert saved()["total"] == 2000


def test_agorot_precision_at_the_limit(setup, saved):
    # 0.1 + 0.2 must count as exactly 0.3, not 0.30000000000000004
    setup(total=0.3, food=0.1, transport=0.2)
    assert saved()["transport"] == 0.2


# ---- rejected changes save nothing ----

def test_new_category_over_total_is_rejected(budget_service, setup, saved, user_id):
    setup(total=1000, food=700)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(user_id, Budget(category="transport", amount=400))
    assert saved() == {"total": 1000, "food": 700}


def test_new_total_below_categories_is_rejected(budget_service, setup, saved, user_id):
    setup(food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(user_id, Budget(category="total", amount=900))
    assert "total" not in saved()


def test_raising_category_over_total_keeps_old_value(budget_service, setup, saved, user_id):
    setup(total=1000, food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(user_id, Budget(category="food", amount=800))
    assert saved()["food"] == 700


def test_lowering_total_below_categories_keeps_old_value(budget_service, setup, saved, user_id):
    setup(total=1000, food=700, transport=300)
    with pytest.raises(ValueError, match="total budget"):
        budget_service.add_budget(user_id, Budget(category="total", amount=999.99))
    assert saved()["total"] == 1000


def test_error_message_explains_the_numbers(budget_service, setup, user_id):
    setup(total=1000, food=700)
    with pytest.raises(ValueError) as error:
        budget_service.add_budget(user_id, Budget(category="transport", amount=400))
    assert "₪1,100.00" in str(error.value)
    assert "₪1,000.00" in str(error.value)
