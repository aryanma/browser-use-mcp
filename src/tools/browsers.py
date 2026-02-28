# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Remote browser session tools for Browser Use Cloud API v2."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.guards import ensure_non_empty, ensure_positive_int
from browser.types import BrowserSessionAction, BrowserSessionRefResult, BrowserSessionStatus
from tools.common import api_error, message_for_error


if TYPE_CHECKING:
    from browser.types import CloudApiResult


def _normalize_browser_session_action(action: BrowserSessionAction | str) -> str:
    """Normalize browser session action enum or string."""
    if isinstance(action, BrowserSessionAction):
        return action.value
    try:
        return BrowserSessionAction(action).value
    except ValueError as exc:
        message = "action must be one of: stop"
        raise ValueError(message) from exc


def _normalize_browser_session_status(status: BrowserSessionStatus | str, *, field_name: str) -> str:
    """Normalize browser session status enum or string."""
    if isinstance(status, BrowserSessionStatus):
        return status.value
    try:
        return BrowserSessionStatus(status).value
    except ValueError as exc:
        message = f"{field_name} must be one of: active, stopped"
        raise ValueError(message) from exc


def _extract_browser_session_refs(payload: object | None) -> tuple[str | None, str | None]:
    """Extract browser session correlation fields from known response shapes."""
    if not isinstance(payload, dict):
        return None, None

    payload_dict = cast("dict[str, object]", payload)
    nested = payload_dict.get("session")
    if isinstance(nested, dict):
        nested_dict = cast("dict[str, object]", nested)
        nested_id = nested_dict.get("id") or nested_dict.get("sessionId")
        nested_cdp = nested_dict.get("cdpUrl")
        return (
            str(nested_id) if nested_id is not None else None,
            str(nested_cdp) if nested_cdp is not None else None,
        )

    session_id = payload_dict.get("id") or payload_dict.get("sessionId")
    cdp_url = payload_dict.get("cdpUrl")
    return (
        str(session_id) if session_id is not None else None,
        str(cdp_url) if cdp_url is not None else None,
    )


@tool(
    description="Create Browser Use Cloud remote browser session and return session_id (plus cdp_url when available)",
    tags=["browser-use", "browser-session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_browser_session_create(
    profile_id: str | None = None,
    proxy_country_code: str | None = None,
    timeout: int = 60,
    browser_screen_width: int | None = None,
    browser_screen_height: int | None = None,
    allow_resizing: bool = False,
    custom_proxy: dict[str, Any] | None = None,
) -> BrowserSessionRefResult:
    """Create remote browser session and return correlation identifiers.

    Stateless-correlation contract for LMs/agents:
    - Create first if no prior browser session exists.
    - Persist returned `session_id` for later get/update/file operations.
    - Reuse returned `cdp_url` immediately when connecting a CDP client.
    """
    try:
        payload: dict[str, object] = {
            "profileId": profile_id,
            "proxyCountryCode": proxy_country_code,
            "timeout": ensure_positive_int("timeout", timeout, minimum=1, maximum=240),
            "browserScreenWidth": (
                ensure_positive_int("browser_screen_width", browser_screen_width, minimum=320, maximum=6144)
                if browser_screen_width is not None
                else None
            ),
            "browserScreenHeight": (
                ensure_positive_int(
                    "browser_screen_height",
                    browser_screen_height,
                    minimum=320,
                    maximum=3456,
                )
                if browser_screen_height is not None
                else None
            ),
            "allowResizing": allow_resizing,
            "customProxy": custom_proxy,
        }
        clean_payload = {key: value for key, value in payload.items() if value is not None}
        resp = await request(HttpMethod.POST, "/api/v2/browsers", body=clean_payload)
        if not resp.success:
            return BrowserSessionRefResult(
                success=False,
                status_code=resp.status_code,
                data=resp.data,
                error=resp.error,
            )

        session_id, cdp_url = _extract_browser_session_refs(resp.data)
        if session_id is None:
            message = "Browser session created but response did not include session_id"
            return BrowserSessionRefResult(
                success=False,
                status_code=resp.status_code,
                data=resp.data,
                error=message,
            )

        return BrowserSessionRefResult(
            success=True,
            session_id=session_id,
            cdp_url=cdp_url,
            status_code=resp.status_code,
            data=resp.data,
        )
    except Exception as exc:  # noqa: BLE001
        return BrowserSessionRefResult(success=False, error=message_for_error(exc))


@tool(
    description="List Browser Use Cloud remote browser sessions",
    tags=["browser-use", "browser-session", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_browser_session_list(
    page_size: int = 10,
    page_number: int = 1,
    filter_by: BrowserSessionStatus | str | None = None,
) -> CloudApiResult:
    """List remote browser sessions."""
    try:
        return await request(
            HttpMethod.GET,
            "/api/v2/browsers",
            query={
                "pageSize": ensure_positive_int("page_size", page_size, minimum=1, maximum=100),
                "pageNumber": ensure_positive_int("page_number", page_number, minimum=1, maximum=10_000),
                "filterBy": (
                    _normalize_browser_session_status(filter_by, field_name="filter_by")
                    if filter_by
                    else None
                ),
            },
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get Browser Use Cloud remote browser session",
    tags=["browser-use", "browser-session", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_browser_session_get(session_id: str) -> CloudApiResult:
    """Get remote browser session."""
    try:
        return await request(HttpMethod.GET, f"/api/v2/browsers/{ensure_non_empty('session_id', session_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Stop Browser Use Cloud remote browser session",
    tags=["browser-use", "browser-session", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_browser_session_update(
    session_id: str,
    action: BrowserSessionAction | str = BrowserSessionAction.stop,
) -> CloudApiResult:
    """Patch remote browser session action."""
    try:
        return await request(
            HttpMethod.PATCH,
            f"/api/v2/browsers/{ensure_non_empty('session_id', session_id)}",
            body={"action": _normalize_browser_session_action(action)},
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


browser_session_tools = [
    bu_browser_session_create,
    bu_browser_session_list,
    bu_browser_session_get,
    bu_browser_session_update,
]
