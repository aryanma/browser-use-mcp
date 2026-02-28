# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Profile tools for Browser Use Cloud API v2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.guards import ensure_non_empty, ensure_positive_int, maybe_stripped
from tools.common import api_error


if TYPE_CHECKING:
    from browser.types import CloudApiResult


@tool(
    description="Create Browser Use Cloud profile",
    tags=["browser-use", "profile", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_profile_create(name: str | None = None) -> CloudApiResult:
    """Create profile with optional name."""
    try:
        clean_name = maybe_stripped(name)
        payload = {"name": clean_name} if clean_name is not None else {}
        return await request(HttpMethod.POST, "/api/v2/profiles", body=payload)
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="List Browser Use Cloud profiles",
    tags=["browser-use", "profile", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_profile_list(page_size: int = 10, page_number: int = 1) -> CloudApiResult:
    """List profiles with pagination."""
    try:
        return await request(
            HttpMethod.GET,
            "/api/v2/profiles",
            query={
                "pageSize": ensure_positive_int("page_size", page_size, minimum=1, maximum=100),
                "pageNumber": ensure_positive_int("page_number", page_number, minimum=1, maximum=10_000),
            },
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get Browser Use Cloud profile",
    tags=["browser-use", "profile", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_profile_get(profile_id: str) -> CloudApiResult:
    """Get profile by ID."""
    try:
        return await request(HttpMethod.GET, f"/api/v2/profiles/{ensure_non_empty('profile_id', profile_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Update Browser Use Cloud profile",
    tags=["browser-use", "profile", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_profile_update(profile_id: str, name: str | None = None) -> CloudApiResult:
    """Update profile fields."""
    try:
        cleaned_name = maybe_stripped(name)
        return await request(
            HttpMethod.PATCH,
            f"/api/v2/profiles/{ensure_non_empty('profile_id', profile_id)}",
            body={"name": cleaned_name},
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Delete Browser Use Cloud profile",
    tags=["browser-use", "profile", "write"],
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
async def bu_profile_delete(profile_id: str) -> CloudApiResult:
    """Delete profile by ID."""
    try:
        return await request(HttpMethod.DELETE, f"/api/v2/profiles/{ensure_non_empty('profile_id', profile_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


profile_tools = [
    bu_profile_create,
    bu_profile_list,
    bu_profile_get,
    bu_profile_update,
    bu_profile_delete,
]
