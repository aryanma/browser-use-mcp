# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Browser Use Cloud connection and request helpers."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

from dedalus_mcp import HttpMethod, HttpRequest, get_context
from dedalus_mcp.auth import Connection, SecretKeys

from browser.types import CloudApiResult


browser_use_mcp = Connection(
    name="browser-use-mcp",
    secrets=SecretKeys(api_key="BROWSER_USE_API_KEY"),
    base_url=os.getenv("BROWSER_USE_API_URL", "https://api.browser-use.com"),
    auth_header_name="X-Browser-Use-API-Key",
    auth_header_format="{api_key}",
)


def _query(params: dict[str, Any] | None = None) -> str:
    """Encode query params, dropping None values."""
    if not params:
        return ""
    clean: dict[str, Any] = {key: value for key, value in params.items() if value is not None}
    if not clean:
        return ""
    return f"?{urlencode(clean, doseq=True)}"


async def request(
    method: HttpMethod,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> CloudApiResult:
    """Dispatch Browser Use Cloud API request through Dedalus connection."""
    ctx = get_context()
    final_path = f"{path}{_query(query)}"
    resp = await ctx.dispatch(browser_use_mcp, HttpRequest(method=method, path=final_path, body=body))

    if resp.success and resp.response is not None:
        status = getattr(resp.response, "status", None)
        return CloudApiResult(success=True, status_code=status, data=resp.response.body)

    status = getattr(resp.response, "status", None) if resp.response is not None else None
    message = "Browser Use Cloud request failed"
    if resp.error is not None:
        raw_message = getattr(resp.error, "message", None)
        if isinstance(raw_message, str) and raw_message:
            message = raw_message
        else:
            message = str(resp.error) or message
    return CloudApiResult(success=False, status_code=status, error=message)
