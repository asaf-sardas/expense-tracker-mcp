import os
import tempfile
from pathlib import Path

# server.py opens the database at import time, so point it at a throwaway
# file before anything imports it. Tests never touch ~/expenses.db.
os.environ["EXPENSES_DB"] = str(Path(tempfile.mkdtemp()) / "import.db")

import pytest  # noqa: E402

from mcp_server.expenses_tracker.db import Database  # noqa: E402
from mcp_server.expenses_tracker.repository.BudgetRepository import (  # noqa: E402
    BudgetRepository,
)
from mcp_server.expenses_tracker.repository.ExpenseRepository import (  # noqa: E402
    ExpenseRepository,
)
from mcp_server.expenses_tracker.services.ExpenseService import (  # noqa: E402
    ExpenseService,
)


@pytest.fixture
def db(tmp_path) -> Database:
    """A fresh, empty database for every test."""
    return Database(tmp_path / "test.db")


@pytest.fixture
def expense_repo(db) -> ExpenseRepository:
    return ExpenseRepository(db)


@pytest.fixture
def budget_repo(db) -> BudgetRepository:
    return BudgetRepository(db)


@pytest.fixture
def expense_service(expense_repo) -> ExpenseService:
    return ExpenseService(expense_repo)
