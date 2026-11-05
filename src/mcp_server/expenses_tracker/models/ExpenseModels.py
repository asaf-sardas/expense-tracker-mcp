from datetime import date
from typing import Literal, Annotated

from pydantic import BaseModel, Field, field_validator

Category = Literal["food", "transport", "travel", "housing", "subscriptions", "other"]

Month = Annotated[int, Field(ge=1, le=12, description="Month number, 1-12")]

Year = Annotated[
    int, Field(ge=2000, le=9999, description="Four-digit year, e.g. 2026")
]



class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, description="Amount in ILS (shekels), e.g. 45.5")
    category: Category = Field(
        description=(
            "transport = daily commuting, taxis, fuel, parking; "
            "travel = trips and vacations, including flights and hotels"
        )
    )
    description: str = Field(
        min_length=1, description="Short description, e.g. 'falafel'"
    )
    expense_date: date = Field(
        default_factory=date.today,
        description="Date of the expense. Cannot be in the future. Omit for today.",
    )

    @field_validator("expense_date")
    @classmethod
    def validate_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("expense_date cannot be in the future")
        return v


class Expense(ExpenseIn):
    id: int = Field(description="Unique expense id. Use it with delete_expense.")


class MonthlySummary(BaseModel):
    year: Year
    month: Month
    total: float = Field(
        description="The total amount of expenses in the mentioned month in ILS"
    )
    expenses_by_category: dict[Category, float] = Field(
        description="The expenses in the month by category in ILS"
    )
