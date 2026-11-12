"""Tests run against a real PostgreSQL: the expenses_test database of the
docker-compose Postgres (`docker compose up -d`), or EXPENSES_TEST_DATABASE_URL.

Once per run the schema is dropped and rebuilt with the Alembic migrations, so
the migrations themselves are tested too. Before every test all tables are
emptied and ids restart at 1, so each test starts from a clean database."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, make_url, text

from mcp_server.expenses_tracker.config import load_settings
from mcp_server.expenses_tracker.db import SCHEMA, Database
from mcp_server.expenses_tracker.repository.BudgetRepository import BudgetRepository
from mcp_server.expenses_tracker.repository.ExpenseRepository import ExpenseRepository
from mcp_server.expenses_tracker.repository.UserRepository import UserRepository
from mcp_server.expenses_tracker.services.BudgetService import BudgetService
from mcp_server.expenses_tracker.services.ExpenseService import ExpenseService

ROOT = Path(__file__).resolve().parent.parent

TEST_DATABASE_URL = load_settings(
    {
        "EXPENSES_DATABASE_URL": os.environ.get(
            "EXPENSES_TEST_DATABASE_URL",
            "postgresql://expenses:expenses@localhost:5432/expenses_test",
        )
    }
).database_url

# The suite deletes everything in the database it runs on. Refuse to run
# against anything that isn't clearly a test database (like Supabase).
if not make_url(TEST_DATABASE_URL).database.endswith("_test"):
    raise RuntimeError(
        "Tests empty the database they run on, so its name must end in '_test'."
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    """The test database, with a schema freshly built by the migrations."""
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as con:
        con.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
    engine.dispose()

    alembic_config = Config(str(ROOT / "alembic.ini"))
    alembic_config.attributes["database_url"] = TEST_DATABASE_URL
    alembic_config.attributes["configure_logger"] = False
    command.upgrade(alembic_config, "head")
    return TEST_DATABASE_URL


@pytest.fixture
def db(database_url):
    """The test database, emptied before the test."""
    database = Database(database_url)
    with database.transaction() as con:
        con.execute(text("TRUNCATE users, expenses, budgets RESTART IDENTITY CASCADE"))
    yield database
    database.close()


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
