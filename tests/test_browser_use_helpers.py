"""Helper-level tests for Browser Use tools."""

from __future__ import annotations

import pytest

from browser_use_mcp.browser_use import _build_query, _clamp, _expect_enum


def test_build_query_omits_none_and_encodes_lists() -> None:
    query = _build_query(
        {
            "pageSize": 10,
            "pageNumber": None,
            "allowedDomains": ["a.com", "b.com"],
            "filterBy": "started",
        }
    )

    assert query.startswith("?")
    assert "pageSize=10" in query
    assert "filterBy=started" in query
    assert "allowedDomains=a.com" in query
    assert "allowedDomains=b.com" in query
    assert "pageNumber" not in query


def test_build_query_empty() -> None:
    assert _build_query({"a": None, "b": None}) == ""


def test_expect_enum_raises_for_invalid_value() -> None:
    with pytest.raises(ValueError, match="must be one of"):
        _expect_enum("action", "invalid", ["stop", "pause"])


def test_clamp_bounds() -> None:
    assert _clamp(-1, 1, 5) == 1
    assert _clamp(9, 1, 5) == 5
    assert _clamp(3, 1, 5) == 3
