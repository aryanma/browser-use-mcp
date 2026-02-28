# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Live Browser Use Cloud connection probes."""

from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus

from dedalus_mcp.testing import ConnectionTester, HttpMethod
from dedalus_mcp.testing import TestRequest as ConnectionTestRequest
import pytest


class LiveProbe(StrEnum):
    """Live upstream endpoints used for smoke verification."""

    billing = "/api/v2/billing/account"
    tasks = "/api/v2/tasks?limit=1"


@pytest.mark.asyncio
@pytest.mark.parametrize("probe", [LiveProbe.billing, LiveProbe.tasks], ids=lambda value: value.name)
async def test_browser_use_connection_live(
    browser_use_connection_tester: ConnectionTester,
    probe: LiveProbe,
) -> None:
    """Browser Use API should be reachable with configured credentials."""
    response = await browser_use_connection_tester.request(
        ConnectionTestRequest(method=HttpMethod.GET, path=probe.value),
    )

    assert response.success, f"{probe.name} probe failed with status={response.status} body={response.body!r}"
    assert response.status == HTTPStatus.OK
    assert response.body is not None
