# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Shared pytest fixtures for browser-use-mcp tests."""

from __future__ import annotations

import os

from dedalus_mcp.testing import ConnectionTester
from dotenv import load_dotenv
import pytest

from browser.cloud import browser_use_mcp


@pytest.fixture(scope="session")
def browser_use_connection_tester() -> ConnectionTester:
    """Return a locally configured ConnectionTester for Browser Use Cloud."""
    load_dotenv()
    if not os.getenv("BROWSER_USE_API_KEY"):
        pytest.skip("BROWSER_USE_API_KEY not set; skipping live Browser Use connection tests")
    return ConnectionTester.from_env(browser_use_mcp)
