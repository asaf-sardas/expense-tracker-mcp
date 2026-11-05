from datetime import date

from fastmcp import FastMCP

from .config import settings
from .db import Database
from .models.BudgetModels import Budget, BudgetCategory, BudgetStatus, SavedExpense
from .models.ExpenseModels import Expense, ExpenseIn, Month, MonthlySummary, Year
from .repository.BudgetRepository import BudgetRepository
from .repository.ExpenseRepository import ExpenseRepository
from .services.BudgetService import BudgetService
from .services.ExpenseService import ExpenseService

mcp = FastMCP(
    "Expenses",
    instructions=(
        "Track the user's personal expenses and monthly budgets. All amounts are in "
        "ILS (shekels). When new_expense returns budget_alerts, tell the user about "
        "each one. To delete an expense, first find its id with list_expenses. "
        "Always confirm with the user before deleting an expense or a budget."
    ),
)

# Wiring: each layer gets the one below it. BudgetService reads spending
# through ExpenseService; ExpenseService knows nothing about budgets.
db = Database(settings.db_path)
expense_service = ExpenseService(ExpenseRepository(db))
budget_service = BudgetService(BudgetRepository(db), expense_service)


@mcp.tool
def new_expense(expense: ExpenseIn) -> SavedExpense:
    """Save a new expense. Use when the user tells you about something they paid for.
    The result includes budget_alerts for any budget now at 80% or more."""
    saved = expense_service.add_expense(expense)
    alerts = budget_service.alerts_for(saved)
    return SavedExpense(**saved.model_dump(), budget_alerts=alerts)


@mcp.tool
def summary_by_category(year: Year, month: Month) -> MonthlySummary:
    """Total spending for a full calendar month, broken down by category, in ILS.
    Use when the user asks how much they spent in a month, or on what they spent the most."""
    return expense_service.monthly_summary(year, month)


@mcp.tool
def list_expenses(first_date: date, last_date: date) -> list[Expense]:
    """List all expenses between two dates, both included, each with its id."""
    return expense_service.expenses_between_dates(first_date, last_date)


@mcp.tool
def delete_expense(expense_id: int) -> int:
    """Permanently delete one expense by its id and return the deleted id.
    Find the id with list_expenses first, and confirm with the user before deleting."""
    return expense_service.delete_expense(expense_id)


@mcp.tool
def set_budget(budget: Budget) -> Budget:
    """Create or update the monthly budget for a category, or 'total' for all spending.
    A budget applies to every month. Category budgets together may not exceed the
    'total' budget; if they would, the change is rejected and the error says why."""
    return budget_service.add_budget(budget)


@mcp.tool
def budget_status(year: Year, month: Month) -> list[BudgetStatus]:
    """For every budget: limit, amount spent, remaining and percent used in the month.
    Use when the user asks how they are doing against their budgets."""
    return budget_service.budget_status(year, month)


@mcp.tool
def delete_budget(category: BudgetCategory) -> BudgetCategory:
    """Remove the budget for a category (or 'total'). Confirm with the user first."""
    return budget_service.delete_budget(category)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
