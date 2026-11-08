import pytest

from mcp_server.expenses_tracker.db import Database
from mcp_server.expenses_tracker.repository.BudgetRepository import BudgetRepository
from mcp_server.expenses_tracker.repository.ExpenseRepository import ExpenseRepository
from mcp_server.expenses_tracker.repository.UserRepository import UserRepository
from mcp_server.expenses_tracker.services.BudgetService import BudgetService
from mcp_server.expenses_tracker.services.ExpenseService import ExpenseService


@pytest.fixture
def db(tmp_path) -> Database:
    """A fresh, empty database for every test."""
    return Database(tmp_path / "test.db")


@pytest.fixture
def user_id(db) -> str:
    """The user most tests act as. Its row must exist: expenses and budgets
    reference users."""
    return UserRepository(db).ensure_user("alice")


@pytest.fixture
def other_user_id(db) -> str:
    """A second user, for checking that users never see each other's data."""
    return UserRepository(db).ensure_user("bob")


@pytest.fixture
def expense_repo(db) -> ExpenseRepository:
    return ExpenseRepository(db)


@pytest.fixture
def budget_repo(db) -> BudgetRepository:
    return BudgetRepository(db)


@pytest.fixture
def expense_service(expense_repo) -> ExpenseService:
    return ExpenseService(expense_repo)


@pytest.fixture
def budget_service(budget_repo, expense_service) -> BudgetService:
    return BudgetService(budget_repo, expense_service)
