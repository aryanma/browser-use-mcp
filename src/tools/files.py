# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""File tools for Browser Use Cloud API v2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.guards import ensure_non_empty, ensure_positive_int
from browser.types import UploadFileContentType
from tools.common import api_error


if TYPE_CHECKING:
    from browser.types import CloudApiResult


def _normalize_content_type(content_type: UploadFileContentType | str) -> str:
    """Normalize upload content type enum or string."""
    if isinstance(content_type, UploadFileContentType):
        return content_type.value
    cleaned = ensure_non_empty("content_type", content_type)
    try:
        return UploadFileContentType(cleaned).value
    except ValueError as exc:
        allowed = ", ".join(item.value for item in UploadFileContentType)
        message = f"content_type must be one of: {allowed}"
        raise ValueError(message) from exc


def _upload_payload(
    file_name: str,
    content_type: UploadFileContentType | str,
    size_bytes: int,
) -> dict[str, object]:
    return {
        "fileName": ensure_non_empty("file_name", file_name),
        "contentType": _normalize_content_type(content_type),
        "sizeBytes": ensure_positive_int("size_bytes", size_bytes, minimum=1, maximum=10_485_760),
    }


@tool(
    description="Create presigned upload URL for a Browser Use agent session file",
    tags=["browser-use", "files", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_session_file_presigned_url_create(
    session_id: str,
    file_name: str,
    content_type: UploadFileContentType | str,
    size_bytes: int,
) -> CloudApiResult:
    """Create upload URL for a session-scoped file."""
    try:
        payload = _upload_payload(file_name=file_name, content_type=content_type, size_bytes=size_bytes)
        return await request(
            HttpMethod.POST,
            f"/api/v2/files/sessions/{ensure_non_empty('session_id', session_id)}/presigned-url",
            body=payload,
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Create presigned upload URL for a Browser Use browser session file",
    tags=["browser-use", "files", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_browser_file_presigned_url_create(
    session_id: str,
    file_name: str,
    content_type: UploadFileContentType | str,
    size_bytes: int,
) -> CloudApiResult:
    """Create upload URL for a browser-session-scoped file."""
    try:
        payload = _upload_payload(file_name=file_name, content_type=content_type, size_bytes=size_bytes)
        return await request(
            HttpMethod.POST,
            f"/api/v2/files/browsers/{ensure_non_empty('session_id', session_id)}/presigned-url",
            body=payload,
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


file_tools = [
    bu_session_file_presigned_url_create,
    bu_browser_file_presigned_url_create,
]
