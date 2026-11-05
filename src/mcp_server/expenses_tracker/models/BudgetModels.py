from typing import Literal

from pydantic import BaseModel, Field

from .ExpenseModels import Category, Expense

BudgetCategory = Category | Literal["total"]


class Budget(BaseModel):
    category: BudgetCategory = Field(
        description="A category, or 'total' for the overall monthly limit across all categories"
    )
    amount: float = Field(
        gt=0, description="Monthly budget limit in ILS (shekels), e.g. 2000"
    )


class BudgetStatus(BaseModel):
    category: BudgetCategory = Field(description="The budget's category, or 'total'")
    limit: float = Field(description="Monthly budget limit in ILS")
    spent: float = Field(description="Amount spent in the month in ILS")
    remaining: float = Field(
        description="limit - spent in ILS; negative when the budget is exceeded"
    )
    percent_used: float = Field(description="spent / limit * 100, rounded to 1 decimal")
    exceeded: bool = Field(description="True when spent is at or above the limit")


class BudgetAlert(BaseModel):
    category: BudgetCategory = Field(description="The budget that triggered the alert")
    level: Literal["warning", "exceeded"] = Field(
        description="'warning' at 80% or more of the limit, 'exceeded' at 100% or more"
    )
    percent_used: float = Field(description="spent / limit * 100 after this expense")
    message: str = Field(description="A short message to show the user")


# Defined here rather than in ExpenseModels to avoid a circular import
# (this module already imports from ExpenseModels).
class SavedExpense(Expense):
    budget_alerts: list[BudgetAlert] = Field(
        default_factory=list,
        description="Budgets this expense brought to 80% or more. Tell the user about each one.",
    )
