from datetime import date

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from sqlalchemy.exc import ProgrammingError

from .config import Settings, load_settings
from .db import Database
from .models.BudgetModels import Budget, BudgetCategory, BudgetStatus, SavedExpense
from .models.ExpenseModels import Expense, ExpenseIn, Month, MonthlySummary, Year
from .repository.BudgetRepository import BudgetRepository
from .repository.ExpenseRepository import ExpenseRepository
from .repository.UserRepository import UserRepository
from .services.BudgetService import BudgetService
from .services.ExpenseService import ExpenseService

INSTRUCTIONS = (
    "Track the user's personal expenses and monthly budgets. All amounts are in "
    "ILS (shekels). When new_expense returns budget_alerts, tell the user about "
    "each one. To delete an expense, first find its id with list_expenses. "
    "Always confirm with the user before deleting an expense or a budget."
)


def create_app(settings: Settings) -> FastMCP:
    """Build the MCP server and everything under it from the given settings.
    Nothing is opened at import time, so tests and other transports can build
    their own instance (for example against a throwaway database)."""
    # Wiring: each layer gets the one below it. BudgetService reads spending
    # through ExpenseService; ExpenseService knows nothing about budgets.
    db = Database(settings.database_url)
    users = UserRepository(db)
    expense_service = ExpenseService(ExpenseRepository(db))
    budget_service = BudgetService(
        BudgetRepository(db),
        expense_service,
        warning_percent=settings.warning_percent,
        exceeded_percent=settings.exceeded_percent,
        currency_symbol=settings.currency_symbol,
    )

    # Local runs have no login, so everything belongs to the dev user.
    # This is also the first query, so it reports a database without tables.
    try:
        users.ensure_user(settings.dev_user_id)
    except ProgrammingError as e:
        raise RuntimeError(
            "The database has no expense tables yet. Create them with: "
            "uv run alembic upgrade head"
        ) from e

    def current_user_id() -> str:
        """Who is calling. With a login (HTTP + OAuth) it is the token's subject;
        local stdio runs have no token and act as the dev user.
        Every tool calls this once and passes the id down to the services."""
        token = get_access_token()
        if token is None:
            return settings.dev_user_id
        # TODO(Phase 3): ensure_user on every call is one extra write per request;
        # cache known ids or create the user once at login instead.
        return users.ensure_user(token.claims["sub"], token.claims.get("email"))

    mcp = FastMCP("Expenses", instructions=INSTRUCTIONS)

    @mcp.tool
    def new_expense(expense: ExpenseIn) -> SavedExpense:
        """Save a new expense. Use when the user tells you about something they paid for.
        The result includes budget_alerts for any budget now at 80% or more."""
        user_id = current_user_id()
        saved = expense_service.add_expense(user_id, expense)
        alerts = budget_service.alerts_for(user_id, saved)
        return SavedExpense(**saved.model_dump(), budget_alerts=alerts)

    @mcp.tool
    def summary_by_category(year: Year, month: Month) -> MonthlySummary:
        """Total spending for a full calendar month, broken down by category, in ILS.
        Use when the user asks how much they spent in a month, or on what they spent the most."""
        return expense_service.monthly_summary(current_user_id(), year, month)

    @mcp.tool
    def list_expenses(first_date: date, last_date: date) -> list[Expense]:
        """List all expenses between two dates, both included, each with its id."""
        return expense_service.expenses_between_dates(
            current_user_id(), first_date, last_date
        )

    @mcp.tool
    def delete_expense(expense_id: int) -> int:
        """Permanently delete one expense by its id and return the deleted id.
        Find the id with list_expenses first, and confirm with the user before deleting."""
        return expense_service.delete_expense(current_user_id(), expense_id)

    @mcp.tool
    def set_budget(budget: Budget) -> Budget:
        """Create or update the monthly budget for a category, or 'total' for all spending.
        A budget applies to every month. Category budgets together may not exceed the
        'total' budget; if they would, the change is rejected and the error says why."""
        return budget_service.add_budget(current_user_id(), budget)

    @mcp.tool
    def budget_status(year: Year, month: Month) -> list[BudgetStatus]:
        """For every budget: limit, amount spent, remaining and percent used in the month.
        Use when the user asks how they are doing against their budgets."""
        return budget_service.budget_status(current_user_id(), year, month)

    @mcp.tool
    def delete_budget(category: BudgetCategory) -> BudgetCategory:
        """Remove the budget for a category (or 'total'). Confirm with the user first."""
        return budget_service.delete_budget(current_user_id(), category)

    return mcp


def main() -> None:
    # Settings may come from a .env file in the working directory (for example
    # EXPENSES_DATABASE_URL); variables already set in the environment win.
    load_dotenv(override=False)
    create_app(load_settings()).run()


if __name__ == "__main__":
    main()
