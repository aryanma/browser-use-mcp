"""Browser Use Cloud API v2 tools."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from dedalus_mcp.types import ToolAnnotations
from pydantic import Field
from pydantic.dataclasses import dataclass


if TYPE_CHECKING:
    from collections.abc import Collection


BASE_URL = "https://api.browser-use.com/api/v2"

browser_use = Connection(
    name="browser_use",
    base_url=BASE_URL,
    secrets=SecretKeys(api_key="BROWSER_USE_API_KEY"),
    auth_header_name="X-Browser-Use-API-Key",
    auth_header_format="{api_key}",
)

TASK_STATUSES = {"started", "paused", "finished", "stopped"}
SESSION_STATUSES = {"active", "stopped"}
BROWSER_SESSION_STATUSES = {"active", "stopped"}

TASK_UPDATE_ACTIONS = {"stop", "pause", "resume", "stop_task_and_session"}
SESSION_UPDATE_ACTIONS = {"stop"}
BROWSER_UPDATE_ACTIONS = {"stop"}

PROXY_COUNTRY_CODES = {"us", "uk", "fr", "it", "jp", "au", "de", "fi", "ca", "in"}
UPLOAD_FILE_CONTENT_TYPES = {
    "image/jpg",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
    "text/markdown",
}


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


def _without_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _build_query(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            parts.extend(f"{key}={item}" for item in value)
            continue
        parts.append(f"{key}={value}")

    if not parts:
        return ""
    return "?" + "&".join(parts)


def _expect_enum(name: str, value: str, allowed: Collection[str]) -> None:
    allowed_values = set(allowed)
    if value not in allowed_values:
        msg = f"{name} must be one of {sorted(allowed_values)}, got: {value}"
        raise ValueError(msg)


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


async def _req(method: HttpMethod, path: str, body: object | None = None) -> BrowserUseResult:
    ctx = get_context()
    resp = await ctx.dispatch("browser_use", HttpRequest(method=method, path=path, body=body))
    payload = resp.response.body if resp.response is not None else None

    if resp.success:
        return BrowserUseResult(
            ok=True,
            status_code=_to_status_code(resp.response),
            data=payload,
        )

    error_message = "Request failed"
    if resp.error is not None and getattr(resp.error, "message", None):
        error_message = str(resp.error.message)

    meta: dict[str, Any] = {}
    if payload is not None:
        meta["upstreamResponse"] = payload

    return BrowserUseResult(
        ok=False,
        status_code=_to_status_code(resp.response),
        error=error_message,
        meta=meta,
    )


# --- Billing ------------------------------------------------------------------


@tool(
    description="Get Browser Use account billing and credit balances",
    tags=["billing", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_account_billing() -> BrowserUseResult:
    return await _req(HttpMethod.GET, "/billing/account")


# --- Tasks --------------------------------------------------------------------


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
    if isinstance(vision, str):
        _expect_enum("vision", vision, {"auto"})

    body = _without_none(
        {
            "task": task,
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
    )

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


# --- Sessions -----------------------------------------------------------------


@tool(
    description="List Browser Use sessions with optional filters",
    tags=["sessions", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_list_sessions(
    page_size: int | None = None,
    page_number: int | None = None,
    filter_by: str | None = None,
) -> BrowserUseResult:
    if filter_by is not None:
        _expect_enum("filter_by", filter_by, SESSION_STATUSES)

    query = _build_query(
        {
            "pageSize": page_size,
            "pageNumber": page_number,
            "filterBy": filter_by,
        }
    )
    return await _req(HttpMethod.GET, "/sessions" + query)


@tool(
    description="Create a Browser Use session",
    tags=["sessions", "write"],
)
async def browser_use_create_session(
    profile_id: str | None = None,
    proxy_country_code: str | None = None,
    start_url: str | None = None,
) -> BrowserUseResult:
    if proxy_country_code is not None:
        _expect_enum("proxy_country_code", proxy_country_code, PROXY_COUNTRY_CODES)

    body = _without_none(
        {
            "profileId": profile_id,
            "proxyCountryCode": proxy_country_code,
            "startUrl": start_url,
        }
    )
    return await _req(HttpMethod.POST, "/sessions", body=body)


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
    description="Get public share info for a session",
    tags=["sessions", "read", "sharing"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_session_public_share(session_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/sessions/{session_id}/public-share")


@tool(
    description="Create or return public share for a session",
    tags=["sessions", "write", "sharing"],
)
async def browser_use_create_session_public_share(session_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.POST, f"/sessions/{session_id}/public-share")


@tool(
    description="Delete public share for a session",
    tags=["sessions", "write", "sharing"],
)
async def browser_use_delete_session_public_share(session_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.DELETE, f"/sessions/{session_id}/public-share")


# --- Files --------------------------------------------------------------------


@tool(
    description="Create presigned URL to upload a task input file for a session",
    tags=["files", "write", "uploads"],
)
async def browser_use_create_session_file_presigned_url(
    session_id: str,
    file_name: str,
    content_type: str,
    size_bytes: int,
) -> BrowserUseResult:
    _expect_enum("content_type", content_type, UPLOAD_FILE_CONTENT_TYPES)

    body = {
        "fileName": file_name,
        "contentType": content_type,
        "sizeBytes": size_bytes,
    }
    return await _req(
        HttpMethod.POST,
        f"/files/sessions/{session_id}/presigned-url",
        body=body,
    )


@tool(
    description="Create presigned URL to upload a file for a browser session",
    tags=["files", "write", "uploads"],
)
async def browser_use_create_browser_file_presigned_url(
    session_id: str,
    file_name: str,
    content_type: str,
    size_bytes: int,
) -> BrowserUseResult:
    _expect_enum("content_type", content_type, UPLOAD_FILE_CONTENT_TYPES)

    body = {
        "fileName": file_name,
        "contentType": content_type,
        "sizeBytes": size_bytes,
    }
    return await _req(
        HttpMethod.POST,
        f"/files/browsers/{session_id}/presigned-url",
        body=body,
    )


@tool(
    description="Get secure download URL for a task output file",
    tags=["files", "read", "downloads"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_task_output_file(
    task_id: str,
    file_id: str,
) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/files/tasks/{task_id}/output-files/{file_id}")


# --- Profiles -----------------------------------------------------------------


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
    body = _without_none({"name": name})
    return await _req(HttpMethod.POST, "/profiles", body=body)


@tool(
    description="Get Browser Use profile details by profile ID",
    tags=["profiles", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_profile(profile_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/profiles/{profile_id}")


@tool(
    description="Update Browser Use profile details",
    tags=["profiles", "write"],
)
async def browser_use_update_profile(profile_id: str, name: str | None) -> BrowserUseResult:
    return await _req(HttpMethod.PATCH, f"/profiles/{profile_id}", body={"name": name})


@tool(
    description="Delete Browser Use profile",
    tags=["profiles", "write"],
)
async def browser_use_delete_profile(profile_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.DELETE, f"/profiles/{profile_id}")


# --- Browsers -----------------------------------------------------------------


@tool(
    description="List Browser Use browser sessions",
    tags=["browsers", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_list_browsers(
    page_size: int | None = None,
    page_number: int | None = None,
    filter_by: str | None = None,
) -> BrowserUseResult:
    if filter_by is not None:
        _expect_enum("filter_by", filter_by, BROWSER_SESSION_STATUSES)

    query = _build_query(
        {
            "pageSize": page_size,
            "pageNumber": page_number,
            "filterBy": filter_by,
        }
    )
    return await _req(HttpMethod.GET, "/browsers" + query)


@tool(
    description="Create a Browser Use browser session",
    tags=["browsers", "write"],
)
async def browser_use_create_browser(
    profile_id: str | None = None,
    proxy_country_code: str | None = None,
    timeout: int | None = None,
) -> BrowserUseResult:
    if proxy_country_code is not None:
        _expect_enum("proxy_country_code", proxy_country_code, PROXY_COUNTRY_CODES)

    body = _without_none(
        {
            "profileId": profile_id,
            "proxyCountryCode": proxy_country_code,
            "timeout": timeout,
        }
    )
    return await _req(HttpMethod.POST, "/browsers", body=body)


@tool(
    description="Get Browser Use browser session details",
    tags=["browsers", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def browser_use_get_browser(session_id: str) -> BrowserUseResult:
    return await _req(HttpMethod.GET, f"/browsers/{session_id}")


@tool(
    description="Stop a Browser Use browser session",
    tags=["browsers", "write"],
)
async def browser_use_update_browser(session_id: str, action: str = "stop") -> BrowserUseResult:
    _expect_enum("action", action, BROWSER_UPDATE_ACTIONS)
    return await _req(HttpMethod.PATCH, f"/browsers/{session_id}", body={"action": action})


browser_use_tools = [
    browser_use_get_account_billing,
    browser_use_create_task,
    browser_use_get_task,
    browser_use_list_tasks,
    browser_use_update_task,
    browser_use_get_task_logs,
    browser_use_wait_for_task,
    browser_use_list_sessions,
    browser_use_create_session,
    browser_use_get_session,
    browser_use_update_session,
    browser_use_get_session_public_share,
    browser_use_create_session_public_share,
    browser_use_delete_session_public_share,
    browser_use_create_session_file_presigned_url,
    browser_use_create_browser_file_presigned_url,
    browser_use_get_task_output_file,
    browser_use_list_profiles,
    browser_use_create_profile,
    browser_use_get_profile,
    browser_use_update_profile,
    browser_use_delete_profile,
    browser_use_list_browsers,
    browser_use_create_browser,
    browser_use_get_browser,
    browser_use_update_browser,
]
