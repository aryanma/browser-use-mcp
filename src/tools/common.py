# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Shared helpers for Browser Use Cloud tool modules."""

from __future__ import annotations

from browser.types import CloudApiResult


def message_for_error(exc: Exception) -> str:
    """Normalize exception to concise message."""
    return str(exc) if str(exc) else exc.__class__.__name__


def api_error(exc: Exception) -> CloudApiResult:
    """Build CloudApiResult for failure."""
    return CloudApiResult(success=False, error=message_for_error(exc))
