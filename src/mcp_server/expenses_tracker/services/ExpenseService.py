from ..models.ExpenseModels import Expense, ExpenseIn, MonthlySummary, Month, Category, Year
from ..repository.ExpenseRepository import ExpenseRepository
from calendar import monthrange
from datetime import date
from ..parser import to_agorot, to_shekels
from collections import defaultdict


class ExpenseService:
    def __init__(self, repository: ExpenseRepository):
        self.repo = repository

    def add_expense(self, user_id: str, expense: ExpenseIn) -> Expense:
        return self.repo.add(user_id, expense)

    def monthly_summary(self, user_id: str, year: Year, month: Month) -> MonthlySummary:
        first_date = date(year, month, 1)
        last_date = date(year, month, monthrange(year, month)[1])
        expenses = self.repo.between_dates(user_id, beginning=first_date, last=last_date)

        by_category_agorot: dict[Category, int] = defaultdict(int)
        for expense in expenses:
            by_category_agorot[expense.category] += to_agorot(expense.amount)

        total_agorot = sum(by_category_agorot.values())

        return MonthlySummary(
            year=year,
            month=month,
            total=to_shekels(total_agorot),
            expenses_by_category={
                category: to_shekels(agorot)
                for category, agorot in by_category_agorot.items()
            },
        )

    def expenses_between_dates(
        self, user_id: str, first_date: date, last_date: date
    ) -> list[Expense]:
        if last_date < first_date:
            first_date, last_date = last_date, first_date
        return self.repo.between_dates(user_id, first_date, last_date)

    def delete_expense(self, user_id: str, expense_id: int) -> int:
        return self.repo.delete_expense(user_id, expense_id)
