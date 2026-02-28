# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client for testing browser-use-mcp server locally."""

from __future__ import annotations

import asyncio

from dedalus_mcp.client import MCPClient


SERVER_URL = "http://localhost:8080/mcp"


async def main() -> None:
    """List tools and run a basic Browser Use API call."""
    client = await MCPClient.connect(SERVER_URL)

    tools = await client.list_tools()
    print(f"\nAvailable tools ({len(tools.tools)}):\n")
    for item in tools.tools:
        print(f"  {item.name}")

    print("\n--- bu_billing_account_get ---")
    billing = await client.call_tool("bu_billing_account_get", {})
    print(billing)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
