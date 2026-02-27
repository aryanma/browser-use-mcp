"""Server bootstrap for browser-use-mcp."""

import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from browser_use_mcp.browser_use import browser_use, browser_use_tools
from browser_use_mcp.smoke import smoke_tools


DEFAULT_PORT = 8080


def create_server() -> MCPServer:
    """Create configured Browser Use MCP server."""
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    return MCPServer(
        name="browser-use-mcp",
        connections=[browser_use],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )


async def main() -> None:
    """Run the MCP server."""
    server = create_server()
    server.collect(*smoke_tools, *browser_use_tools)
    await server.serve(port=DEFAULT_PORT)
