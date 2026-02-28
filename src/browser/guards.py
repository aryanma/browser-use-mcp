# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Validation helpers for Browser Use Cloud tools."""

from __future__ import annotations

from urllib.parse import urlparse


def ensure_non_empty(name: str, value: str) -> str:
    """Ensure string input is non-empty after strip."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} must be a non-empty string")
    return cleaned


def ensure_positive_int(name: str, value: int, *, minimum: int, maximum: int) -> int:
    """Ensure integer is within bounds."""
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def ensure_url(url: str) -> str:
    """Ensure URL uses http or https."""
    cleaned = ensure_non_empty("url", url)
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("url must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("url must include a host")
    return cleaned


def maybe_url(value: str | None) -> str | None:
    """Validate optional URL."""
    if value is None:
        return None
    return ensure_url(value)


def maybe_stripped(value: str | None) -> str | None:
    """Normalize optional string, dropping empty values."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
