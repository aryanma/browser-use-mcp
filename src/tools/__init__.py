# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Tool registry for browser-use-mcp cloud wrapper."""

from tools.billing import billing_tools
from tools.browsers import browser_session_tools
from tools.files import file_tools
from tools.profiles import profile_tools
from tools.sessions import session_tools
from tools.tasks import task_tools


browser_tools = [
    *billing_tools,
    *task_tools,
    *session_tools,
    *browser_session_tools,
    *file_tools,
    *profile_tools,
]
