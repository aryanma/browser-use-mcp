# browser-use-mcp

A Dedalus MCP server for Browser Use Cloud API v2.

## Features

- Read and write tools for Browser Use Cloud tasks, sessions, and profiles.
- Uses Dedalus credential isolation via `dispatch()`.
- Expects Browser Use API key credentials at runtime (no plaintext key on server).

## Auth Model

This server defines one MCP connection named `browser_use`:

- Secret key field: `BROWSER_USE_API_KEY`
- Header: `X-Browser-Use-API-Key: <key>`
- Base URL: `https://api.browser-use.com/api/v2`

Use Dedalus SDK credentials (`SecretValues`) or per-server encrypted credentials
(`MCPServerSpec.credentials`) to provide the key.

## Tools

- `browser_use_get_account_billing`
- `browser_use_create_task`
- `browser_use_get_task`
- `browser_use_list_tasks`
- `browser_use_update_task`
- `browser_use_get_task_logs`
- `browser_use_get_session`
- `browser_use_update_session`
- `browser_use_list_profiles`
- `browser_use_create_profile`
- `browser_use_get_profile`
- `browser_use_wait_for_task`

## Run

```bash
cd browser-use-mcp
uv run python -m browser_use_mcp.main
```

Server runs on port `8080` by default.
