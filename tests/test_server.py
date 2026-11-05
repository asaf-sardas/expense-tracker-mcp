"""End-to-end tests: call the MCP tools the same way Claude does, through
FastMCP's in-memory client, against a fresh database per test."""

import asyncio
from datetime import date

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_server.expenses_tracker import server


@pytest.fixture
def call(monkeypatch, expense_service, budget_service):
    # Tools look up the services on the server module at call time, so
    # swapping them gives each test its own empty database.
    monkeypatch.setattr(server, "expense_service", expense_service)
    monkeypatch.setattr(server, "budget_service", budget_service)

    def _call(tool, args):
        async def run():
            async with Client(server.mcp) as client:
                return await client.call_tool(tool, args)

        return asyncio.run(run()).structured_content

    return _call


def test_all_tools_are_registered():
    async def run():
        async with Client(server.mcp) as client:
            return {t.name for t in await client.list_tools()}

    assert asyncio.run(run()) == {
        "new_expense",
        "list_expenses",
        "summary_by_category",
        "delete_expense",
        "set_budget",
        "budget_status",
        "delete_budget",
    }


def test_full_flow_add_list_summarize_delete(call):
    today = date.today()

    falafel = call(
        "new_expense",
        {"expense": {"amount": 45, "category": "food", "description": "falafel"}},
    )
    call(
        "new_expense",
        {"expense": {"amount": 12.9, "category": "food", "description": "coffee"}},
    )
    assert falafel["id"] == 1
    assert falafel["expense_date"] == today.isoformat()

    listed = call(
        "list_expenses",
        {"first_date": today.isoformat(), "last_date": today.isoformat()},
    )["result"]
    assert [e["description"] for e in listed] == ["falafel", "coffee"]

    summary = call("summary_by_category", {"year": today.year, "month": today.month})
    assert summary["total"] == 57.9
    assert summary["expenses_by_category"] == {"food": 57.9}

    call("delete_expense", {"expense_id": falafel["id"]})
    summary = call("summary_by_category", {"year": today.year, "month": today.month})
    assert summary["total"] == 12.9


def test_invalid_expense_is_rejected(call):
    with pytest.raises(ToolError):
        call(
            "new_expense",
            {"expense": {"amount": -5, "category": "food", "description": "bad"}},
        )


def test_invalid_month_is_rejected(call):
    with pytest.raises(ToolError):
        call("summary_by_category", {"year": 2026, "month": 13})


def test_deleting_missing_expense_reports_error(call):
    with pytest.raises(ToolError, match="No expense with id 42"):
        call("delete_expense", {"expense_id": 42})


def test_budget_flow_warns_then_reports_exceeded(call):
    today = date.today()
    expense = {"category": "food", "description": "groceries"}

    call("set_budget", {"budget": {"category": "food", "amount": 100}})

    under = call("new_expense", {"expense": {**expense, "amount": 50}})
    assert under["budget_alerts"] == []

    warned = call("new_expense", {"expense": {**expense, "amount": 35}})
    assert [(a["category"], a["level"]) for a in warned["budget_alerts"]] == [
        ("food", "warning")
    ]

    over = call("new_expense", {"expense": {**expense, "amount": 20}})
    assert [(a["category"], a["level"]) for a in over["budget_alerts"]] == [
        ("food", "exceeded")
    ]

    [status] = call("budget_status", {"year": today.year, "month": today.month})[
        "result"
    ]
    assert status["spent"] == 105
    assert status["remaining"] == -5
    assert status["exceeded"] is True


def test_set_budget_over_total_is_rejected(call):
    call("set_budget", {"budget": {"category": "total", "amount": 1000}})
    with pytest.raises(ToolError, match="total budget"):
        call("set_budget", {"budget": {"category": "food", "amount": 1500}})


def test_delete_budget(call):
    call("set_budget", {"budget": {"category": "food", "amount": 100}})
    call("delete_budget", {"category": "food"})
    today = date.today()
    assert call("budget_status", {"year": today.year, "month": today.month})[
        "result"
    ] == []
    with pytest.raises(ToolError, match="No budget for food"):
        call("delete_budget", {"category": "food"})
