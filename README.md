# Expense Tracker MCP Server

An [MCP](https://modelcontextprotocol.io) server that lets Claude record and analyze personal expenses through natural conversation. Tell Claude "I spent 45 shekels on falafel" or "how much did I spend on food in October?", and it calls the right tool, validates the input, and stores everything locally in SQLite.

## Features

- **Record expenses in natural language** — Hebrew or English, with optional dates ("yesterday I paid 120 for a taxi")
- **List expenses by date range** — every expense is returned with its id
- **Monthly summary by category** — total spent and a per-category breakdown, in ILS
- **Input validation** — positive amounts only, a fixed set of categories, no future dates; invalid input is rejected with a message Claude can act on
- **Receipt photos** — in clients that support images, Claude reads the receipt and records the expense with no extra code
- **Exact money handling** — amounts are stored as integer agorot, so `0.10 + 0.20` is exactly `0.30`

## Example

> **You:** I spent 45 shekels on falafel and 12.90 on coffee
>
> **Claude:** *(calls `new_expense` twice)* Saved both: falafel (food, ₪45.00) and coffee (food, ₪12.90).
>
> **You:** How much did I spend this month?
>
> **Claude:** *(calls `summary_by_category`)* ₪57.90 so far, all in food.

## Tools

| Tool | Description |
| --- | --- |
| `new_expense` | Save a new expense (amount, category, description, optional date) |
| `list_expenses` | List expenses between two dates, inclusive, each with its id (dates may be given in either order) |
| `summary_by_category` | Total spending for a calendar month, broken down by category |
| `delete_expense` | Delete an expense by id (Claude confirms with you first) |

Categories: `food`, `transport`, `travel`, `housing`, `subscriptions`, `other`.

## Architecture

The code is split into layers. Each layer only knows the one below it, and all wiring happens in one place (`server.py`).

```
server.py      MCP tools: thin wrappers, no logic
   ↓
services/      business logic (month ranges, summaries, rules)
   ↓
repository/    SQL only, converts rows to models
   ↓
db.py          Database: knows the file path and how to open a transaction
```

```
src/mcp_server/expenses_tracker/
├── server.py          # MCP tools and dependency wiring
├── db.py              # Database class with a transaction() context manager
├── parser.py          # shekels <-> agorot conversion
├── models/
│   ├── ExpenseModels.py   # ExpenseIn, Expense, MonthlySummary, Category/Month/Year types
│   └── BudgetModels.py    # Budget (per category or "total")
├── repository/
│   ├── ExpenseRepository.py   # add, between_dates, delete_expense
│   └── BudgetRepository.py    # add_budget (in progress)
└── services/
    └── ExpenseService.py      # add, monthly summary, date-range listing
```

### Design decisions

- **Money as integer agorot.** Floats can't represent most decimal amounts exactly (`0.1 + 0.2 == 0.30000000000000004`). Amounts are converted to agorot on the way into the database and back to shekels only for output, through a single pair of helper functions.
- **Validation at the boundaries.** Pydantic models validate everything Claude sends before any code runs, and repository helpers convert database rows back into models. Inside the system, everything is a validated model.
- **Layers with injected dependencies.** Repositories receive the `Database`, services receive repositories, and `server.py` builds the chain once at startup. This keeps SQL, logic, and the MCP interface separate and makes each layer testable on its own (for example, testing a service against a fake in-memory repository).
- **One transaction per operation.** `Database.transaction()` opens a connection, commits on success, rolls back on error, and always closes the connection.
- **Tool descriptions written for the model.** Docstrings and field descriptions tell Claude when to use each tool, what units to use, and rules it can't see in the schema (such as "no future dates").

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd expense-tracker-mcp
uv sync
```

Run the server directly (it will start and wait for a client):

```bash
uv run python -m mcp_server.expenses_tracker.server
```

### Connect to Claude Code

```bash
claude mcp add expenses -- uv --directory /path/to/expense-tracker-mcp run python -m mcp_server.expenses_tracker.server
```

Then open Claude Code, run `/mcp` to confirm the server is connected, and start talking about your expenses.

### Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `EXPENSES_DB` | `~/expenses.db` | Path to the SQLite database file |

## Testing

The pytest suite in `tests/` gives every test its own empty database, so it never touches your real data:

```bash
uv run pytest
```

| File | What it checks |
| --- | --- |
| `test_parser.py` | Shekel ↔ agorot conversion is exact (`0.1 + 0.2 == 0.3`) |
| `test_models.py` | Validation rejects zero/negative amounts, unknown categories, empty descriptions, future dates |
| `test_expense_repository.py` | Insert, inclusive and sorted date ranges, delete, delete of a missing id |
| `test_expense_service.py` | Monthly totals per category, month boundaries, leap years, empty months, reversed date ranges |
| `test_budget_repository.py` | Budgets stored in agorot, setting a budget twice updates it, `total` alongside categories |
| `test_server.py` | End to end through FastMCP's in-memory client: add → list → summarize → delete, plus rejected inputs |

For a quick manual check there is also `playground.py`, a short smoke script:

```bash
uv run playground.py
```

## Roadmap

- [x] Record expenses
- [x] List expenses by date range
- [x] Monthly summary by category
- [x] Delete an expense
- [ ] Update an expense
- [ ] Monthly budgets, overall and per category *(in progress: `budgets` table, `Budget` model and `BudgetRepository.add_budget` (insert or update) done; service and tools pending)*
- [ ] Budget warnings when adding an expense
- [ ] Export a month as CSV
- [x] pytest suite for models, repositories, services and tools
- [ ] Evaluation set measuring how reliably Claude picks the right tool

## Limitations

Single user, local only. Each person runs their own server with their own database file. Supporting multiple users on a shared server would require authentication, a `user_id` on every row, and a database such as PostgreSQL.

## Tech stack

Python · [uv](https://docs.astral.sh/uv/) · [FastMCP](https://gofastmcp.com) · [Pydantic](https://docs.pydantic.dev) · SQLite