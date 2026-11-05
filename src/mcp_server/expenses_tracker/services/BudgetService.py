from ..models.BudgetModels import Budget, BudgetAlert, BudgetCategory, BudgetStatus
from ..models.ExpenseModels import Expense, Month, Year
from ..config import settings
from ..parser import format_money, to_agorot, to_shekels
from ..repository.BudgetRepository import BudgetRepository
from .ExpenseService import ExpenseService


class BudgetService:
    def __init__(
        self,
        repository: BudgetRepository,
        expense_service: ExpenseService,
        warning_percent: int = settings.warning_percent,
        exceeded_percent: int = settings.exceeded_percent,
    ):
        self.repository = repository
        self.expense_service = expense_service
        self.warning_percent = warning_percent
        self.exceeded_percent = exceeded_percent

    def add_budget(self, budget: Budget) -> Budget:
        """Create or update a budget. Rejects the change, saving nothing, if the
        category budgets would add up to more than the 'total' budget."""
        self._check_fits_total(budget)
        return self.repository.save_budget(budget)

    def get_all_budgets(self) -> list[Budget]:
        return self.repository.get_all_budgets()

    def delete_budget(self, category: BudgetCategory) -> BudgetCategory:
        # Always safe: removing a budget can't break the total limit.
        return self.repository.delete_budget(category)

    def budget_status(self, year: Year, month: Month) -> list[BudgetStatus]:
        """Limit, spent, remaining and percent used for every budget in the month.
        'total' is compared with all spending, a category with its own spending."""
        summary = self.expense_service.monthly_summary(year, month)
        statuses = []
        for budget in self.repository.get_all_budgets():
            spent = (
                summary.total
                if budget.category == "total"
                else summary.expenses_by_category.get(budget.category, 0)
            )
            statuses.append(_status(budget, to_agorot(spent)))
        return statuses

    def alerts_for(self, expense: Expense) -> list[BudgetAlert]:
        """Alerts for the expense's own category and 'total', in the expense's month:
        'warning' at warning_percent or more, 'exceeded' at exceeded_percent or
        more (80% and 100% by default, see config.py). Repeats on every
        expense while a budget stays above the threshold."""
        day = expense.expense_date
        statuses = {
            s.category: s for s in self.budget_status(day.year, day.month)
        }
        alerts = []
        for category in (expense.category, "total"):
            status = statuses.get(category)
            if status is None:
                continue
            level = self._alert_level(status)
            if level is not None:
                alerts.append(
                    BudgetAlert(
                        category=category,
                        level=level,
                        percent_used=status.percent_used,
                        message=_alert_message(status, level),
                    )
                )
        return alerts

    def _check_fits_total(self, new: Budget) -> None:
        # Budgets as they would be after this change: an update replaces the
        # category's old amount instead of adding to it. Compared in agorot.
        after = {
            b.category: to_agorot(b.amount) for b in self.repository.get_all_budgets()
        }
        after[new.category] = to_agorot(new.amount)

        total = after.pop("total", None)
        if total is None:
            return  # no overall limit, nothing to check

        categories_sum = sum(after.values())
        if categories_sum > total:
            raise ValueError(
                f"Category budgets would add up to {format_money(to_shekels(categories_sum))}, "
                f"more than the total budget of {format_money(to_shekels(total))}. "
                "Raise the total budget first, or lower another category."
            )

    def _alert_level(self, status: BudgetStatus) -> str | None:
        # Compare whole agorot, not the rounded percent, so 79.96% never counts as 80%.
        spent, limit = to_agorot(status.spent), to_agorot(status.limit)
        if spent * 100 >= limit * self.exceeded_percent:
            return "exceeded"
        if spent * 100 >= limit * self.warning_percent:
            return "warning"
        return None


def _status(budget: Budget, spent_agorot: int) -> BudgetStatus:
    limit_agorot = to_agorot(budget.amount)
    return BudgetStatus(
        category=budget.category,
        limit=budget.amount,
        spent=to_shekels(spent_agorot),
        remaining=to_shekels(limit_agorot - spent_agorot),
        percent_used=round(spent_agorot * 100 / limit_agorot, 1),
        exceeded=spent_agorot >= limit_agorot,
    )


def _alert_message(status: BudgetStatus, level: str) -> str:
    name = "Total" if status.category == "total" else status.category.capitalize()
    amounts = f"{format_money(status.spent)} of {format_money(status.limit)}"
    if level == "exceeded":
        return f"{name} budget exceeded: {amounts} ({status.percent_used:g}%)."
    return (
        f"{name} budget at {status.percent_used:g}%: {amounts}, "
        f"{format_money(status.remaining)} left."
    )
