"""Browser Use Cloud API v2 tools."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from dedalus_mcp.types import ToolAnnotations
from pydantic import Field
from pydantic.dataclasses import dataclass


BASE_URL = "https://api.browser-use.com/api/v2"

browser_use = Connection(
    name="browser_use",
    base_url=BASE_URL,
    secrets=SecretKeys(api_key="BROWSER_USE_API_KEY"),
    auth_header_name="X-Browser-Use-API-Key",
    auth_header_format="{api_key}",
)

TASK_STATUSES = {"started", "paused", "finished", "stopped"}
TASK_UPDATE_ACTIONS = {"stop", "pause", "resume", "stop_task_and_session"}
SESSION_UPDATE_ACTIONS = {"stop"}


@dataclass(frozen=True)
class BrowserUseResult:
    """Normalized Browser Use API result."""

    ok: bool
    status_code: int | None = None
    data: Any = None
    meta: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


def _to_status_code(response: object) -> int | None:
    if response is None:
        return None
    status = getattr(response, "status", None)
    if status is not None:
        return int(status)
    status_code = getattr(response, "status_code", None)
    if status_code is not None:
        return int(status_code)
    return None


def _build_query(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, list):
            parts.extend(f"{key}={item}" for item in value)
        else:
            parts.append(f"{key}={value}")
    if not parts:
        return ""
    return "?" + "&".join(parts)


def _expect_enum(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        msg = f"{name} must be one of {sorted(allowed)}, got: {value}"
        raise ValueError(msg)


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


async def _req(method: HttpMethod, path: str, body: object | None = None) -> BrowserUseResult:
    ctx = get_context()
    resp = await ctx.dispatch("browser_use", HttpRequest(method=method, path=path, body=body))

    if resp.success:
        payload = resp.response.body if resp.response is not None else None
        return BrowserUseResult(
            ok=True,
            status_code=_to_status_code(resp.response),
            data=payload,
        )

    error_message = "Request failed"
    if resp.error is not None and getattr(resp.error, "message", None):
        error_message = str(resp.error.message)

    return BrowserUseResult(
        ok=False,
        status_code=_to_status_code(resp.response),
        error=error_message,
    )


@tool(
    description="Get Browser Use account billing and credit balances",
    tags=["billing", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_account_billing() -> BrowserUseResult:
    return await _req(HttpMethod.GET, "/billing/account")


@tool(
    description="Create a Browser Use task in a new or existing session",
    tags=["tasks", "write"],
)
async def browser_use_create_task(  # noqa: PLR0913
    task: str,
    llm: str | None = None,
    session_id: str | None = None,
    start_url: str | None = None,
    max_steps: int | None = None,
    structured_output: str | None = None,
    metadata: dict[str, str] | None = None,
    secrets: dict[str, str] | None = None,
    allowed_domains: list[str] | None = None,
    op_vault_id: str | None = None,
    highlight_elements: bool | None = None,
    flash_mode: bool | None = None,
    thinking: bool | None = None,
    vision: bool | str | None = None,
    system_prompt_extension: str | None = None,
) -> BrowserUseResult:
    body: dict[str, Any] = {"task": task}
    optional_fields = {
        "llm": llm,
        "sessionId": session_id,
        "startUrl": start_url,
        "maxSteps": max_steps,
        "structuredOutput": structured_output,
        "metadata": metadata,
        "secrets": secrets,
        "allowedDomains": allowed_domains,
        "opVaultId": op_vault_id,
        "highlightElements": highlight_elements,
        "flashMode": flash_mode,
        "thinking": thinking,
        "vision": vision,
        "systemPromptExtension": system_prompt_extension,
    }
    body.update({key: value for key, value in optional_fields.items() if value is not None})

    return await _req(HttpMethod.POST, "/tasks", body=body)


@tool(
    description="Get a Browser Use task by task ID",
    tags=["tasks", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_task(task_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/tasks/{task_id}")


@tool(
    description="List Browser Use tasks with optional filters",
    tags=["tasks", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_list_tasks(
    page_size: int | None = None,
    page_number: int | None = None,
    session_id: str | None = None,
    filter_by: str | None = None,
    after: str | None = None,
    before: str | None = None,
) -> BrowserUseResult:
    if filter_by is not None:
        _expect_enum("filter_by", filter_by, TASK_STATUSES)

    query = _build_query(
        {
            "pageSize": page_size,
            "pageNumber": page_number,
            "sessionId": session_id,
            "filterBy": filter_by,
            "after": after,
            "before": before,
        }
    )
    return await _req(HttpMethod.GET, "/tasks" + query)


@tool(
    description="Update task state: stop, pause, resume, or stop task and session",
    tags=["tasks", "write"],
)
async def browser_use_update_task(task_id: str, action: str) -> BrowserUseResult:
    _expect_enum("action", action, TASK_UPDATE_ACTIONS)
    return await _req(HttpMethod.PATCH, f"/tasks/{task_id}", body={"action": action})


@tool(
    description="Get a secure download URL for task logs",
    tags=["tasks", "read", "logs"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_task_logs(task_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/tasks/{task_id}/logs")


@tool(
    description="Get session details by session ID",
    tags=["sessions", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_session(session_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/sessions/{session_id}")


@tool(
    description="Stop a session and all its running tasks",
    tags=["sessions", "write"],
)
async def browser_use_update_session(session_id: str, action: str = "stop") -> BrowserUseResult:
    _expect_enum("action", action, SESSION_UPDATE_ACTIONS)
    return await _req(HttpMethod.PATCH, f"/sessions/{session_id}", body={"action": action})


@tool(
    description="List Browser Use profiles",
    tags=["profiles", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_list_profiles(
    page_size: int | None = None,
    page_number: int | None = None,
) -> BrowserUseResult:
    query = _build_query({"pageSize": page_size, "pageNumber": page_number})
    return await _req(HttpMethod.GET, "/profiles" + query)


@tool(
    description="Create a Browser Use profile",
    tags=["profiles", "write"],
)
async def browser_use_create_profile(name: str | None = None) -> BrowserUseResult:
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    return await _req(HttpMethod.POST, "/profiles", body=body)


@tool(
    description="Get Browser Use profile details by profile ID",
    tags=["profiles", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_profile(profile_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/profiles/{profile_id}")


@tool(
    description="Poll a task until it reaches finished or stopped",
    tags=["tasks", "control", "read"],
)
async def browser_use_wait_for_task(
    task_id: str,
    timeout_seconds: int = 120,
    poll_interval_seconds: float = 2.0,
) -> BrowserUseResult:
    timeout_seconds = _clamp(timeout_seconds, 1, 900)
    poll_interval_seconds = max(0.1, min(10.0, poll_interval_seconds))

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds
    polls = 0
    last: BrowserUseResult | None = None

    while loop.time() < deadline:
        polls += 1
        current = await browser_use_get_task(task_id)
        last = current

        if not current.ok:
            return BrowserUseResult(
                ok=False,
                status_code=current.status_code,
                error=current.error,
                meta={"polls": polls},
            )

        data = current.data if isinstance(current.data, dict) else {}
        status = data.get("status")
        if status in {"finished", "stopped"}:
            return BrowserUseResult(
                ok=True,
                status_code=current.status_code,
                data=current.data,
                meta={"polls": polls, "finalStatus": status},
            )

        await asyncio.sleep(poll_interval_seconds)

    return BrowserUseResult(
        ok=False,
        status_code=last.status_code if last else None,
        error=f"Timeout waiting for task {task_id}",
        meta={
            "polls": polls,
            "lastResult": asdict(last) if last is not None else None,
            "timeoutSeconds": timeout_seconds,
        },
    )


browser_use_tools = [
    browser_use_get_account_billing,
    browser_use_create_task,
    browser_use_get_task,
    browser_use_list_tasks,
    browser_use_update_task,
    browser_use_get_task_logs,
    browser_use_get_session,
    browser_use_update_session,
    browser_use_list_profiles,
    browser_use_create_profile,
    browser_use_get_profile,
    browser_use_wait_for_task,
]
