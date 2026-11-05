from typing import Literal
from .ExpenseModels import Category
from pydantic import BaseModel, Field


BudgetCategory=Category|Literal["total"]

class Budget(BaseModel):
    category: BudgetCategory=Field(description="A category, or 'total' for the overall monthly limit across all categories")
    amount:float = Field(gt=0,description="Monthly budget limit in ILS (shekels), e.g. 2000")