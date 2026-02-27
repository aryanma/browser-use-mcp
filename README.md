# browser-use-mcp

A Dedalus MCP server for Browser Use Cloud API v2.

## Features

- Full Browser Use Cloud API v2 parity for billing, tasks, sessions, files, profiles, and browsers.
- Uses Dedalus credential isolation via `dispatch()`.
- Expects Browser Use API key credentials at runtime (no plaintext key on server).

## Auth Model

This server defines one MCP connection (single-connection auto-dispatch):

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
- `browser_use_wait_for_task`
- `browser_use_list_sessions`
- `browser_use_create_session`
- `browser_use_get_session`
- `browser_use_update_session`
- `browser_use_get_session_public_share`
- `browser_use_create_session_public_share`
- `browser_use_delete_session_public_share`
- `browser_use_create_session_file_presigned_url`
- `browser_use_create_browser_file_presigned_url`
- `browser_use_get_task_output_file`
- `browser_use_list_profiles`
- `browser_use_create_profile`
- `browser_use_get_profile`
- `browser_use_update_profile`
- `browser_use_delete_profile`
- `browser_use_list_browsers`
- `browser_use_create_browser`
- `browser_use_get_browser`
- `browser_use_update_browser`

## Run

```bash
cd browser-use-mcp
uv run python -m browser_use_mcp.main
```

Server runs on port `8080` by default.

## Per-user auth (dedalus bearer + required credential)

This server is designed for per-user Browser Use credentials:

- If no Browser Use credential is provided by the caller, tool calls fail with `oauth_required`.
- If a per-user `BROWSER_USE_API_KEY` credential is provided, the tools execute against that user's Browser Use project.
- No Browser Use key is hardcoded in server code.
