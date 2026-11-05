"""End-to-end tests: call the MCP tools the same way Claude does, through
FastMCP's in-memory client, against a fresh database per test."""

import asyncio
from datetime import date

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_server.expenses_tracker import server


@pytest.fixture
def call(monkeypatch, expense_service):
    # Tools look up server.expense_service at call time, so swapping it
    # gives each test its own empty database.
    monkeypatch.setattr(server, "expense_service", expense_service)

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
