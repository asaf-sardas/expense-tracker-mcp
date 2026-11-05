from fastmcp import FastMCP
from .services.ExpenseService import ExpenseService
from .repository.ExpenseRepository import ExpenseRepository
from .models.ExpenseModels import ExpenseIn, Expense, Month, MonthlySummary, Year
from .db import Database
from datetime import date
import os

from pathlib import Path

mcp = FastMCP(
    "Expenses",
    instructions=(
        "Track the user's personal expenses. All amounts are in ILS (shekels). "
        "To delete an expense, first find its id with list_expenses, "
        "and always confirm with the user before deleting."
    ),
)
db = Database(Path(os.environ.get("EXPENSES_DB", Path.home() /"expenses.db")))
repo = ExpenseRepository(db)
expense_service = ExpenseService(repo)


@mcp.tool
def new_expense(expense: ExpenseIn) -> Expense:
    """Saves a new expense to the data base, Use when user tell about a new expense he had and want to record it"""
    return expense_service.add_expense(expense)


@mcp.tool
def summary_by_category(year: Year, month: Month) -> MonthlySummary:
    """Total spending for a full calendar month, broken down by category, in ILS.
    Use when the user asks how much they spent in a month, or on what they spent the most."""
    return expense_service.monthly_summary(year, month)


@mcp.tool
def list_expenses(first_date: date, last_date: date) -> list[Expense]:
    """return list of all the expenses that reported between the two following dates"""
    return expense_service.expenses_between_dates(first_date, last_date)


@mcp.tool
def delete_expense(expense_id: int) -> int:
    """Permanently delete one expense by its id and return the deleted id.
    Find the id with list_expenses first, and confirm with the user before deleting."""
    return expense_service.delete_expense(expense_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
