"""Test fixtures for browser-use-mcp."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class FakeHttpResponse:
    """Fake HTTP response for dispatch mocks."""

    status: int
    body: Any = None


@dataclass
class FakeDispatchError:
    """Fake dispatch error model."""

    message: str


@dataclass
class FakeDispatchResult:
    """Fake dispatch result model."""

    success: bool
    response: FakeHttpResponse | None = None
    error: FakeDispatchError | None = None


class FakeDispatchContext:
    """Capture dispatch requests and serve queued responses."""

    def __init__(self, responses: list[FakeDispatchResult]) -> None:
        self._responses = deque(responses)
        self.calls: list[tuple[str, object]] = []

    async def dispatch(self, connection: str, request: object) -> FakeDispatchResult:
        self.calls.append((connection, request))
        if not self._responses:
            msg = "No fake responses queued"
            raise RuntimeError(msg)
        return self._responses.popleft()


@pytest.fixture
def ok_response() -> FakeDispatchResult:
    """Factory-like base success response."""
    return FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={}))
