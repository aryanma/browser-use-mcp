# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Typed result models for Browser Use Cloud tools."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypeAlias

from pydantic import Field
from pydantic.dataclasses import dataclass


JSONValue: TypeAlias = str | int | float | bool | dict[str, Any] | list[Any] | None


class TaskAction(StrEnum):
    """Supported task update actions."""

    stop = "stop"
    pause = "pause"
    resume = "resume"
    stop_task_and_session = "stop_task_and_session"


class TaskStatus(StrEnum):
    """Task lifecycle status."""

    created = "created"
    started = "started"
    finished = "finished"
    stopped = "stopped"


class SessionAction(StrEnum):
    """Supported session update actions."""

    stop = "stop"


class SessionStatus(StrEnum):
    """Session lifecycle status."""

    active = "active"
    stopped = "stopped"


class BrowserSessionAction(StrEnum):
    """Supported browser session update actions."""

    stop = "stop"


class BrowserSessionStatus(StrEnum):
    """Browser session lifecycle status."""

    active = "active"
    stopped = "stopped"


class VisionMode(StrEnum):
    """Special string mode for task vision behavior."""

    auto = "auto"


class UploadFileContentType(StrEnum):
    """Allowed content types for file upload endpoints."""

    image_jpg = "image/jpg"
    image_jpeg = "image/jpeg"
    image_png = "image/png"
    image_gif = "image/gif"
    image_webp = "image/webp"
    image_svg_xml = "image/svg+xml"
    application_pdf = "application/pdf"
    application_msword = "application/msword"
    application_vnd_openxmlformats_officedocument_wordprocessingml_document = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    application_vnd_ms_excel = "application/vnd.ms-excel"
    application_vnd_openxmlformats_officedocument_spreadsheetml_sheet = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    text_plain = "text/plain"
    text_csv = "text/csv"
    text_markdown = "text/markdown"


@dataclass(frozen=True)
class CloudApiResult:
    """Generic Browser Use Cloud API result."""

    success: bool
    status_code: int | None = None
    data: JSONValue = None
    error: str | None = None


@dataclass(frozen=True)
class TaskRefResult:
    """Task creation result reference."""

    success: bool
    task_id: str | None = None
    session_id: str | None = None
    status_code: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class TaskWaitResult:
    """Task polling result."""

    success: bool
    task_id: str
    session_id: str | None = None
    status: str | None = None
    timed_out: bool = False
    attempts: int = 0
    task: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class TaskRunResult:
    """Combined create + wait result."""

    success: bool
    task_id: str | None = None
    session_id: str | None = None
    status: str | None = None
    timed_out: bool = False
    attempts: int = 0
    task: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class SessionRefResult:
    """Session creation result with correlation ID for follow-up calls."""

    success: bool
    session_id: str | None = None
    status_code: int | None = None
    data: JSONValue = None
    error: str | None = None


@dataclass(frozen=True)
class BrowserSessionRefResult:
    """Remote browser session creation result with correlation identifiers."""

    success: bool
    session_id: str | None = None
    cdp_url: str | None = None
    status_code: int | None = None
    data: JSONValue = None
    error: str | None = None
