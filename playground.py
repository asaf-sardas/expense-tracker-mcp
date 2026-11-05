import asyncio
import os
import tempfile
from pathlib import Path

# Use a throwaway database so the smoke test never touches real data.
os.environ["EXPENSES_DB"] = str(Path(tempfile.mkdtemp()) / "smoke.db")

from fastmcp import Client  # noqa: E402
from mcp_server.expenses_tracker.server import mcp  # noqa: E402


async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("tools:", [t.name for t in tools])

        result = await client.call_tool(
            "new_expense",
            {
                "expense": {
                    "amount": 19.99,
                    "category": "food",
                    "description": "falafel",
                }
            },
        )
        print("saved:", result.structured_content)

        try:
            await client.call_tool(
                "new_expense",
                {"expense": {"amount": -5, "category": "food", "description": "bad"}},
            )
        except Exception as e:
            print("rejected as expected:", e)


asyncio.run(main())
