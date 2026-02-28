# browser-use-mcp

Browser Use MCP built with the Dedalus MCP framework.

This server does not run local browsers. Every tool forwards to Browser Use Cloud
API v2 (`https://api.browser-use.com`), enabled by Dedalus Auth (DAuth).

## Features

- Browser Use task orchestration with polling helpers
- Cloud browser session lifecycle and share links
- Remote browser (CDP) session management
- Profile management
- Logs/output URL retrieval for artifacts

## Setup

```bash
cd browser-use-mcp
cp .env.example .env
# set BROWSER_USE_API_KEY
uv sync
```

## Run server

```bash
uv run src/main.py
```

Server endpoint: `http://127.0.0.1:8080/mcp`

## Local test client

```bash
uv run src/client.py
```

## Interactive REPL client (DAuth)

```bash
uv run src/repl.py
```

This follows the same DAuth interactive pattern used by the Gmail/Linear/Tinker
sample clients and streams responses from the Dedalus runner.
It requires the `dedalus_labs` SDK package in your environment.

## Live connection test (no deploy)

```bash
uv run pytest tests/test_connection_live.py -q
```

This uses a shared pytest fixture based on
`ConnectionTester.from_env(browser_use_mcp)` and probes Browser Use API with
`BROWSER_USE_API_KEY` from `.env`. If the key is missing, the test is skipped.

## Stateless correlation strategy

This server is intentionally stateless (`streamable_http_stateless=True`), so
multi-step flows must be correlated by IDs returned from Browser Use.

Recommended pattern:

1. Call a create endpoint (`bu_session_create`, `bu_browser_session_create`, or
   `bu_task_create`).
2. Persist returned IDs (`session_id`, `task_id`, optional `cdp_url`).
3. Pass those IDs explicitly into follow-up calls.

Create endpoints return typed ID fields at top-level to make this reliable for
LMs and MCP clients.

## Environment

- `DEDALUS_AS_URL` default `https://as.dedaluslabs.ai`
- `BROWSER_USE_API_URL` default `https://api.browser-use.com`
- `BROWSER_USE_API_KEY` required

## Tool groups

### Billing

- `bu_billing_account_get`

### Tasks

- `bu_task_create`
- `bu_task_get`
- `bu_task_list`
- `bu_task_get_status`
- `bu_task_update`
- `bu_task_wait`
- `bu_task_run`
- `bu_task_get_logs_url`
- `bu_task_get_output_file_url`

### Sessions

- `bu_session_create`
- `bu_session_list`
- `bu_session_get`
- `bu_session_update`
- `bu_session_delete`
- `bu_session_public_share_create`
- `bu_session_public_share_get`
- `bu_session_public_share_delete`

### Remote Browser Sessions (CDP)

- `bu_browser_session_create`
- `bu_browser_session_list`
- `bu_browser_session_get`
- `bu_browser_session_update`

### Files

- `bu_session_file_presigned_url_create`
- `bu_browser_file_presigned_url_create`

### Profiles

- `bu_profile_create`
- `bu_profile_list`
- `bu_profile_get`
- `bu_profile_update`
- `bu_profile_delete`

## Recommended usage patterns

1. One-shot execution: `bu_task_run`
2. Follow-up workflows:
   - create/reuse session (`bu_session_create`)
   - run tasks with `session_id` or `session_settings`
   - poll with `bu_task_wait` (uses lightweight status endpoint internally)
3. Debugging/ops:
   - `bu_task_get_logs_url`
   - `bu_task_get_output_file_url`
   - `bu_task_list`
4. Human review/share:
   - `bu_session_public_share_create`

## Notes

- Authentication is header-based (`X-Browser-Use-API-Key`) and handled via
  DAuth.
- This server intentionally avoids local Browser Use runtime APIs.
- Create endpoints return typed ID references for stateless correlation.

## License

MIT
