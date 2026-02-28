# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Interactive Browser Use REPL via Dedalus Auth (DAuth).

DAuth (Dedalus Auth):
    Multi-tenant MCP authentication requires the Dedalus SDK. Generic MCP clients
    are spec-compliant but don't support credential injection.

    This file demonstrates DAuth credential handoff: the Browser Use API key is
    bound client-side and provided to the MCP server as encrypted credential
    material. The server does not receive raw credentials in source code.

    For custom runners or lower-level SDK usage, see https://docs.dedaluslabs.ai

Environment variables:
    DEDALUS_API_KEY:  Your Dedalus API key (dsk_*)
    DEDALUS_API_URL:  API base URL
    DEDALUS_AS_URL:   Authorization server URL
    BROWSER_USE_API_KEY: Browser Use API key (required)
    BROWSER_USE_API_URL: Browser Use API URL (optional, defaults to public API)
"""

import asyncio
import os
import webbrowser

from dotenv import load_dotenv


load_dotenv()

from dedalus_labs import AsyncDedalus, AuthenticationError, DedalusRunner
from dedalus_labs.utils.stream import stream_async
from dedalus_mcp.auth import Connection, SecretKeys, SecretValues


class MissingEnvError(ValueError):
    """Required environment variable not set."""


def get_env(key: str) -> str:
    """Get required env var or raise."""
    val = os.getenv(key)
    if not val:
        raise MissingEnvError(key)
    return val


API_URL = get_env("DEDALUS_API_URL")
AS_URL = get_env("DEDALUS_AS_URL")
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")
BROWSER_USE_API_KEY = get_env("BROWSER_USE_API_KEY")
BROWSER_USE_API_URL = os.getenv("BROWSER_USE_API_URL", "https://api.browser-use.com")

# Debug: print env vars
print("=== Environment ===")
print(f"  DEDALUS_API_URL: {API_URL}")
print(f"  DEDALUS_AS_URL: {AS_URL}")
print(
    f"  DEDALUS_API_KEY: {DEDALUS_API_KEY[:20]}..."
    if DEDALUS_API_KEY
    else "  DEDALUS_API_KEY: None"
)
print(f"  BROWSER_USE_API_URL: {BROWSER_USE_API_URL}")
print(f"  BROWSER_USE_API_KEY: {BROWSER_USE_API_KEY[:8]}...")


# Connection schema for Browser Use API v2.
# The identifier `browser-use-mcp` must match the MCP server's Connection name.
browser_use_mcp = Connection(
    name="browser-use-mcp",
    secrets=SecretKeys(api_key="BROWSER_USE_API_KEY"),
    base_url=BROWSER_USE_API_URL,
    auth_header_name="X-Browser-Use-API-Key",
    auth_header_format="{api_key}",
)

# SecretValues bind real credential values to the connection schema.
browser_use_credentials = SecretValues(browser_use_mcp, api_key=BROWSER_USE_API_KEY)


def _extract_connect_url(err: AuthenticationError) -> str | None:
    """Pull the OAuth connect URL from an AuthenticationError, if present."""
    body = err.body if isinstance(err.body, dict) else {}
    return body.get("connect_url") or body.get("detail", {}).get("connect_url")


def _prompt_oauth(url: str) -> None:
    """Open OAuth URL in browser and block until user confirms."""
    print("\nAttempting to open your default browser.")
    print("If the browser does not open, open the following URL:\n")
    print(url)
    webbrowser.open(url)
    input("\nPress Enter after completing OAuth...")


async def run_agent_loop() -> None:
    """Interactive chat loop that streams through the Browser Use MCP server."""
    client = AsyncDedalus(api_key=DEDALUS_API_KEY, base_url=API_URL, as_base_url=AS_URL)
    runner = DedalusRunner(client)
    messages: list[dict] = []

    async def run_turn() -> None:
        stream = runner.run(
            input=messages,
            model="anthropic/claude-opus-4-5",
            mcp_servers=["windsor/browser-use-mcp"],
            credentials=[browser_use_credentials],
            stream=True,
        )
        print("\nAssistant: ", end="", flush=True)
        await stream_async(stream)

    print("\n=== Browser Use MCP Agent ===")
    print("Type 'quit' or 'exit' to end the session.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            await run_turn()
        except AuthenticationError as err:
            url = _extract_connect_url(err)
            if not url:
                raise
            _prompt_oauth(url)
            await run_turn()

        print()


async def main() -> None:
    """Run interactive agent loop."""
    await run_agent_loop()


if __name__ == "__main__":
    asyncio.run(main())
