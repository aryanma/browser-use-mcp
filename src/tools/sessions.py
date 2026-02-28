# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Session tools for Browser Use Cloud API v2."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.guards import ensure_non_empty, ensure_positive_int, maybe_url
from browser.types import SessionAction, SessionRefResult, SessionStatus
from tools.common import api_error, message_for_error


if TYPE_CHECKING:
    from browser.types import CloudApiResult


def _normalize_session_action(action: SessionAction | str) -> str:
    """Normalize session action enum or string."""
    if isinstance(action, SessionAction):
        return action.value
    try:
        return SessionAction(action).value
    except ValueError as exc:
        message = "action must be one of: stop"
        raise ValueError(message) from exc


def _normalize_session_status(status: SessionStatus | str, *, field_name: str) -> str:
    """Normalize session status enum or string."""
    if isinstance(status, SessionStatus):
        return status.value
    try:
        return SessionStatus(status).value
    except ValueError as exc:
        message = f"{field_name} must be one of: active, stopped"
        raise ValueError(message) from exc


def _extract_session_id(payload: object | None) -> str | None:
    """Extract session ID from known Browser Use response shapes."""
    if not isinstance(payload, dict):
        return None

    payload_dict = cast("dict[str, object]", payload)
    nested = payload_dict.get("session")
    if isinstance(nested, dict):
        nested_dict = cast("dict[str, object]", nested)
        nested_id = nested_dict.get("id") or nested_dict.get("sessionId")
        if nested_id is not None:
            return str(nested_id)

    direct_id = payload_dict.get("id") or payload_dict.get("sessionId")
    return str(direct_id) if direct_id is not None else None


@tool(
    description="Create Browser Use Cloud session and return session_id for follow-up calls",
    tags=["browser-use", "session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_session_create(
    profile_id: str | None = None,
    proxy_country_code: str | None = None,
    start_url: str | None = None,
    browser_screen_width: int | None = None,
    browser_screen_height: int | None = None,
    persist_memory: bool = True,
    keep_alive: bool = True,
    custom_proxy: dict[str, Any] | None = None,
) -> SessionRefResult:
    """Create a cloud browser session and return a durable correlation ID.

    Stateless-correlation contract for LMs/agents:
    - If this is the first call, create a session without a prior `session_id`.
    - Persist returned `session_id` and pass it to all session-scoped tools.
    - Do not rely on MCP server memory between calls.
    """
    try:
        width = (
            ensure_positive_int("browser_screen_width", browser_screen_width, minimum=320, maximum=6144)
            if browser_screen_width is not None
            else None
        )
        height = (
            ensure_positive_int("browser_screen_height", browser_screen_height, minimum=320, maximum=3456)
            if browser_screen_height is not None
            else None
        )
        payload: dict[str, object] = {
            "profileId": profile_id,
            "proxyCountryCode": proxy_country_code,
            "startUrl": maybe_url(start_url),
            "browserScreenWidth": width,
            "browserScreenHeight": height,
            "persistMemory": persist_memory,
            "keepAlive": keep_alive,
            "customProxy": custom_proxy,
        }
        clean_payload = {key: value for key, value in payload.items() if value is not None}
        resp = await request(HttpMethod.POST, "/api/v2/sessions", body=clean_payload)
        if not resp.success:
            return SessionRefResult(
                success=False,
                status_code=resp.status_code,
                data=resp.data,
                error=resp.error,
            )

        session_id = _extract_session_id(resp.data)
        if session_id is None:
            message = "Session created but response did not include session_id"
            return SessionRefResult(
                success=False,
                status_code=resp.status_code,
                data=resp.data,
                error=message,
            )

        return SessionRefResult(
            success=True,
            session_id=session_id,
            status_code=resp.status_code,
            data=resp.data,
        )
    except Exception as exc:  # noqa: BLE001
        return SessionRefResult(success=False, error=message_for_error(exc))


@tool(
    description="List Browser Use Cloud sessions",
    tags=["browser-use", "session", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_session_list(
    page_size: int = 10,
    page_number: int = 1,
    filter_by: SessionStatus | str | None = None,
) -> CloudApiResult:
    """List sessions with pagination."""
    try:
        return await request(
            HttpMethod.GET,
            "/api/v2/sessions",
            query={
                "pageSize": ensure_positive_int("page_size", page_size, minimum=1, maximum=100),
                "pageNumber": ensure_positive_int("page_number", page_number, minimum=1, maximum=10_000),
                "filterBy": _normalize_session_status(filter_by, field_name="filter_by") if filter_by else None,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get Browser Use Cloud session",
    tags=["browser-use", "session", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_session_get(session_id: str) -> CloudApiResult:
    """Get session by ID."""
    try:
        return await request(HttpMethod.GET, f"/api/v2/sessions/{ensure_non_empty('session_id', session_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Update Browser Use Cloud session action",
    tags=["browser-use", "session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_session_update(
    session_id: str,
    action: SessionAction | str = SessionAction.stop,
) -> CloudApiResult:
    """Patch session action."""
    try:
        return await request(
            HttpMethod.PATCH,
            f"/api/v2/sessions/{ensure_non_empty('session_id', session_id)}",
            body={"action": _normalize_session_action(action)},
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Delete Browser Use Cloud session",
    tags=["browser-use", "session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
async def bu_session_delete(session_id: str) -> CloudApiResult:
    """Delete session by ID."""
    try:
        return await request(HttpMethod.DELETE, f"/api/v2/sessions/{ensure_non_empty('session_id', session_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Create a public share link for Browser Use session",
    tags=["browser-use", "session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_session_public_share_create(session_id: str) -> CloudApiResult:
    """Create session public share URL."""
    try:
        cleaned = ensure_non_empty("session_id", session_id)
        return await request(HttpMethod.POST, f"/api/v2/sessions/{cleaned}/public-share")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get public share URL for Browser Use session",
    tags=["browser-use", "session", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_session_public_share_get(session_id: str) -> CloudApiResult:
    """Get session public share URL."""
    try:
        cleaned = ensure_non_empty("session_id", session_id)
        return await request(HttpMethod.GET, f"/api/v2/sessions/{cleaned}/public-share")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Delete public share URL for Browser Use session",
    tags=["browser-use", "session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
async def bu_session_public_share_delete(session_id: str) -> CloudApiResult:
    """Delete session public share URL."""
    try:
        return await request(
            HttpMethod.DELETE,
            f"/api/v2/sessions/{ensure_non_empty('session_id', session_id)}/public-share",
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


session_tools = [
    bu_session_create,
    bu_session_list,
    bu_session_get,
    bu_session_update,
    bu_session_delete,
    bu_session_public_share_create,
    bu_session_public_share_get,
    bu_session_public_share_delete,
]
