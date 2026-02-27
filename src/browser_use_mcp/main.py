"""Entrypoint for browser-use-mcp."""

import asyncio

from dotenv import load_dotenv

from browser_use_mcp.server import main


load_dotenv()


if __name__ == "__main__":
    asyncio.run(main())
