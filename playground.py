import asyncio
import tempfile
from pathlib import Path

from fastmcp import Client

from mcp_server.expenses_tracker.config import load_settings
from mcp_server.expenses_tracker.server import create_app

# Use a throwaway database so the smoke test never touches real data.
mcp = create_app(load_settings({"EXPENSES_DB": str(Path(tempfile.mkdtemp()) / "smoke.db")}))


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
