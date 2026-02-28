# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Billing tools for Browser Use Cloud API v2."""

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.types import CloudApiResult
from tools.common import api_error


@tool(
    description="Get Browser Use Cloud account billing and credit balances",
    tags=["browser-use", "billing", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_billing_account_get() -> CloudApiResult:
    """Fetch account billing details."""
    try:
        return await request(HttpMethod.GET, "/api/v2/billing/account")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


billing_tools = [bu_billing_account_get]
