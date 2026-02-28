# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Task tools for Browser Use Cloud API v2."""

from __future__ import annotations

import asyncio
from typing import cast

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from browser.cloud import request
from browser.guards import ensure_non_empty, ensure_positive_int, maybe_url
from browser.types import (
    CloudApiResult,
    TaskAction,
    TaskRefResult,
    TaskRunResult,
    TaskStatus,
    TaskWaitResult,
    VisionMode,
)
from tools.common import api_error, message_for_error


PayloadDict = dict[str, object]


def _normalize_vision(vision: bool | VisionMode | str | None) -> bool | str | None:
    """Normalize vision argument to API-compatible value."""
    if vision is None or isinstance(vision, bool):
        return vision
    if isinstance(vision, VisionMode):
        return vision.value
    try:
        return VisionMode(vision).value
    except ValueError as exc:
        message = "vision must be boolean or one of: auto"
        raise ValueError(message) from exc


def _normalize_task_action(action: TaskAction | str) -> str:
    """Normalize task action argument to API-compatible value."""
    if isinstance(action, TaskAction):
        return action.value
    try:
        return TaskAction(action).value
    except ValueError as exc:
        message = "action must be one of: stop, pause, resume, stop_task_and_session"
        raise ValueError(message) from exc


def _normalize_task_status(status: TaskStatus | str, *, field_name: str) -> str:
    """Normalize task status enum or string to canonical value."""
    if isinstance(status, TaskStatus):
        return status.value
    try:
        return TaskStatus(status).value
    except ValueError as exc:
        message = f"{field_name} must be one of: created, started, finished, stopped"
        raise ValueError(message) from exc


def _normalize_session_settings(session_settings: PayloadDict | None) -> PayloadDict | None:
    """Normalize session settings keys to API format."""
    if session_settings is None:
        return None
    if not isinstance(session_settings, dict):
        message = "session_settings must be an object"
        raise TypeError(message)

    key_map = {
        "profile_id": "profileId",
        "proxy_country_code": "proxyCountryCode",
        "browser_screen_width": "browserScreenWidth",
        "browser_screen_height": "browserScreenHeight",
    }
    normalized = {
        key_map.get(key, key): value for key, value in session_settings.items() if value is not None
    }

    raw_width = normalized.get("browserScreenWidth")
    if raw_width is not None:
        if not isinstance(raw_width, int):
            message = "session_settings.browserScreenWidth must be an integer"
            raise TypeError(message)
        width = ensure_positive_int(
            "session_settings.browserScreenWidth",
            raw_width,
            minimum=320,
            maximum=6144,
        )
        normalized["browserScreenWidth"] = width
    raw_height = normalized.get("browserScreenHeight")
    if raw_height is not None:
        if not isinstance(raw_height, int):
            message = "session_settings.browserScreenHeight must be an integer"
            raise TypeError(message)
        height = ensure_positive_int(
            "session_settings.browserScreenHeight",
            raw_height,
            minimum=320,
            maximum=3456,
        )
        normalized["browserScreenHeight"] = height

    return normalized or None


def _task_payload(
    *,
    task: str,
    llm: str | None,
    start_url: str | None,
    max_steps: int,
    structured_output: str | None,
    session_id: str | None,
    session_settings: PayloadDict | None,
    metadata: dict[str, str] | None,
    secrets: dict[str, str] | None,
    allowed_domains: list[str] | None,
    op_vault_id: str | None,
    highlight_elements: bool,
    flash_mode: bool,
    thinking: bool,
    vision: bool | VisionMode | str | None,
    system_prompt_extension: str | None,
    judge: bool,
    judge_ground_truth: str | None,
    judge_llm: str | None,
    skill_ids: list[str] | None,
) -> PayloadDict:
    """Build task creation payload, dropping None values."""
    payload: PayloadDict = {
        "task": task,
        "llm": llm,
        "startUrl": maybe_url(start_url),
        "maxSteps": max_steps,
        "structuredOutput": structured_output,
        "sessionId": session_id,
        "sessionSettings": _normalize_session_settings(session_settings),
        "metadata": metadata,
        "secrets": secrets,
        "allowedDomains": allowed_domains,
        "opVaultId": op_vault_id,
        "highlightElements": highlight_elements,
        "flashMode": flash_mode,
        "thinking": thinking,
        "vision": _normalize_vision(vision),
        "systemPromptExtension": system_prompt_extension,
        "judge": judge,
        "judgeGroundTruth": judge_ground_truth,
        "judgeLlm": judge_llm,
        "skillIds": skill_ids,
    }
    return {key: value for key, value in payload.items() if value is not None}


def _extract_task_ref(payload: object | None) -> tuple[str | None, str | None]:
    """Extract task/session IDs from API payload."""
    if not isinstance(payload, dict):
        return None, None

    payload_dict = cast("PayloadDict", payload)
    task = payload_dict.get("task")
    if isinstance(task, dict):
        task_dict = cast("PayloadDict", task)
        task_id = task_dict.get("id")
        session_id = task_dict.get("sessionId")
        return (str(task_id) if task_id is not None else None, str(session_id) if session_id is not None else None)

    task_id = payload_dict.get("id")
    session_id = payload_dict.get("sessionId")
    return (str(task_id) if task_id is not None else None, str(session_id) if session_id is not None else None)


def _task_status(payload: object | None) -> str | None:
    """Extract task status from API payload."""
    if not isinstance(payload, dict):
        return None
    payload_dict = cast("PayloadDict", payload)
    if "status" in payload_dict:
        status = payload_dict.get("status")
        return str(status) if status is not None else None
    nested = payload_dict.get("task")
    if isinstance(nested, dict) and "status" in nested:
        nested_dict = cast("PayloadDict", nested)
        status = nested_dict.get("status")
        return str(status) if status is not None else None
    return None


@tool(
    description="Create Browser Use Cloud task and return task_id + resolved session_id",
    tags=["browser-use", "task", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_task_create(
    task: str,
    llm: str | None = None,
    start_url: str | None = None,
    max_steps: int = 100,
    structured_output: str | None = None,
    session_id: str | None = None,
    session_settings: PayloadDict | None = None,
    metadata: dict[str, str] | None = None,
    secrets: dict[str, str] | None = None,
    allowed_domains: list[str] | None = None,
    op_vault_id: str | None = None,
    highlight_elements: bool = False,
    flash_mode: bool = False,
    thinking: bool = False,
    vision: bool | VisionMode | str | None = None,
    system_prompt_extension: str | None = None,
    judge: bool = False,
    judge_ground_truth: str | None = None,
    judge_llm: str | None = None,
    skill_ids: list[str] | None = None,
) -> TaskRefResult:
    """Create task in Browser Use Cloud and return correlation IDs.

    Stateless-correlation contract for LMs/agents:
    - First call may omit `session_id`; Browser Use can create/resolve one.
    - Persist returned `task_id` and `session_id` for all follow-up calls.
    - Do not rely on MCP server memory between calls.
    """
    try:
        payload = _task_payload(
            task=ensure_non_empty("task", task),
            llm=llm,
            start_url=start_url,
            max_steps=ensure_positive_int("max_steps", max_steps, minimum=1, maximum=10_000),
            structured_output=structured_output,
            session_id=session_id,
            session_settings=session_settings,
            metadata=metadata,
            secrets=secrets,
            allowed_domains=allowed_domains,
            op_vault_id=op_vault_id,
            highlight_elements=highlight_elements,
            flash_mode=flash_mode,
            thinking=thinking,
            vision=vision,
            system_prompt_extension=system_prompt_extension,
            judge=judge,
            judge_ground_truth=judge_ground_truth,
            judge_llm=judge_llm,
            skill_ids=skill_ids,
        )
        resp = await request(HttpMethod.POST, "/api/v2/tasks", body=payload)
        if not resp.success:
            return TaskRefResult(success=False, status_code=resp.status_code, error=resp.error)
        task_id, resolved_session_id = _extract_task_ref(resp.data)
        return TaskRefResult(
            success=True,
            task_id=task_id,
            session_id=resolved_session_id,
            status_code=resp.status_code,
        )
    except Exception as exc:  # noqa: BLE001
        return TaskRefResult(success=False, error=message_for_error(exc))


@tool(
    description="Get Browser Use Cloud task details",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_get(task_id: str) -> CloudApiResult:
    """Fetch task by ID."""
    try:
        return await request(HttpMethod.GET, f"/api/v2/tasks/{ensure_non_empty('task_id', task_id)}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="List Browser Use Cloud tasks",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_list(
    page_size: int = 10,
    page_number: int = 1,
    session_id: str | None = None,
    filter_by: TaskStatus | str | None = None,
    after: str | None = None,
    before: str | None = None,
) -> CloudApiResult:
    """List tasks with pagination and optional filters."""
    try:
        query = {
            "pageSize": ensure_positive_int("page_size", page_size, minimum=1, maximum=100),
            "pageNumber": ensure_positive_int("page_number", page_number, minimum=1, maximum=10_000),
            "sessionId": session_id,
            "filterBy": _normalize_task_status(filter_by, field_name="filter_by") if filter_by else None,
            "after": after,
            "before": before,
        }
        return await request(HttpMethod.GET, "/api/v2/tasks", query=query)
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get lightweight Browser Use Cloud task status for polling",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_get_status(task_id: str) -> CloudApiResult:
    """Fetch task status only (recommended for polling)."""
    try:
        cleaned_task = ensure_non_empty("task_id", task_id)
        return await request(HttpMethod.GET, f"/api/v2/tasks/{cleaned_task}/status")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Update a Browser Use Cloud task action",
    tags=["browser-use", "task", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_task_update(
    task_id: str,
    action: TaskAction | str = TaskAction.stop,
) -> CloudApiResult:
    """Patch task action (stop, pause, resume, or stop task + session)."""
    try:
        return await request(
            HttpMethod.PATCH,
            f"/api/v2/tasks/{ensure_non_empty('task_id', task_id)}",
            body={"action": _normalize_task_action(action)},
        )
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Wait for Browser Use Cloud task to reach a terminal state",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_wait(
    task_id: str,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 2,
    terminal_statuses: list[TaskStatus | str] | None = None,
) -> TaskWaitResult:
    """Poll task until terminal status or timeout."""
    try:
        cleaned_task_id = ensure_non_empty("task_id", task_id)
        timeout = ensure_positive_int("timeout_seconds", timeout_seconds, minimum=1, maximum=86_400)
        interval = ensure_positive_int("poll_interval_seconds", poll_interval_seconds, minimum=1, maximum=60)
        terminals = (
            {TaskStatus.finished.value, TaskStatus.stopped.value}
            if terminal_statuses is None
            else {
                _normalize_task_status(status, field_name="terminal_statuses")
                for status in terminal_statuses
            }
        )

        attempts = 0
        elapsed = 0
        while elapsed <= timeout:
            attempts += 1
            resp = await bu_task_get_status(cleaned_task_id)
            if not resp.success:
                return TaskWaitResult(
                    success=False,
                    task_id=cleaned_task_id,
                    attempts=attempts,
                    error=resp.error,
                )

            payload = resp.data if isinstance(resp.data, dict) else {}
            status = _task_status(payload)
            task_ref, session_ref = _extract_task_ref(payload)

            if status is not None and status.lower() in terminals:
                final_payload = payload
                final_task = await bu_task_get(cleaned_task_id)
                if final_task.success and isinstance(final_task.data, dict):
                    final_payload = final_task.data
                    task_ref, session_ref = _extract_task_ref(final_payload)
                return TaskWaitResult(
                    success=True,
                    task_id=task_ref or cleaned_task_id,
                    session_id=session_ref,
                    status=status,
                    attempts=attempts,
                    task=final_payload,
                )

            await asyncio.sleep(interval)
            elapsed += interval

        return TaskWaitResult(
            success=False,
            task_id=cleaned_task_id,
            timed_out=True,
            attempts=attempts,
            error=f"Timed out after {timeout} seconds",
        )
    except Exception as exc:  # noqa: BLE001
        return TaskWaitResult(
            success=False,
            task_id=task_id,
            error=message_for_error(exc),
        )


@tool(
    description="Create task, wait for completion, and return task_id + session_id",
    tags=["browser-use", "task", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def bu_task_run(
    task: str,
    llm: str | None = None,
    start_url: str | None = None,
    max_steps: int = 100,
    structured_output: str | None = None,
    session_id: str | None = None,
    session_settings: PayloadDict | None = None,
    metadata: dict[str, str] | None = None,
    secrets: dict[str, str] | None = None,
    allowed_domains: list[str] | None = None,
    op_vault_id: str | None = None,
    highlight_elements: bool = False,
    flash_mode: bool = False,
    thinking: bool = False,
    vision: bool | VisionMode | str | None = None,
    system_prompt_extension: str | None = None,
    judge: bool = False,
    judge_ground_truth: str | None = None,
    judge_llm: str | None = None,
    skill_ids: list[str] | None = None,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 2,
    terminal_statuses: list[TaskStatus | str] | None = None,
) -> TaskRunResult:
    """Create task, poll to terminal status, and return durable IDs.

    This helper is preferred for stateless clients because one response contains
    both `task_id` and `session_id`, which can be reused in subsequent calls.
    """
    created = await bu_task_create(
        task=task,
        llm=llm,
        start_url=start_url,
        max_steps=max_steps,
        structured_output=structured_output,
        session_id=session_id,
        session_settings=session_settings,
        metadata=metadata,
        secrets=secrets,
        allowed_domains=allowed_domains,
        op_vault_id=op_vault_id,
        highlight_elements=highlight_elements,
        flash_mode=flash_mode,
        thinking=thinking,
        vision=vision,
        system_prompt_extension=system_prompt_extension,
        judge=judge,
        judge_ground_truth=judge_ground_truth,
        judge_llm=judge_llm,
        skill_ids=skill_ids,
    )
    if not created.success or created.task_id is None:
        return TaskRunResult(
            success=False,
            task_id=created.task_id,
            session_id=created.session_id,
            error=created.error or "Task creation failed",
        )

    waited = await bu_task_wait(
        task_id=created.task_id,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        terminal_statuses=terminal_statuses,
    )

    return TaskRunResult(
        success=waited.success,
        task_id=waited.task_id,
        session_id=waited.session_id or created.session_id,
        status=waited.status,
        timed_out=waited.timed_out,
        attempts=waited.attempts,
        task=waited.task,
        error=waited.error,
    )


@tool(
    description="Get task logs download URL",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_get_logs_url(task_id: str) -> CloudApiResult:
    """Get logs URL for task."""
    try:
        return await request(HttpMethod.GET, f"/api/v2/tasks/{ensure_non_empty('task_id', task_id)}/logs")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


@tool(
    description="Get task output file download URL",
    tags=["browser-use", "task", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def bu_task_get_output_file_url(task_id: str, file_id: str) -> CloudApiResult:
    """Get output file URL for task/file IDs."""
    try:
        cleaned_task = ensure_non_empty("task_id", task_id)
        cleaned_file = ensure_non_empty("file_id", file_id)
        return await request(HttpMethod.GET, f"/api/v2/files/tasks/{cleaned_task}/output-files/{cleaned_file}")
    except Exception as exc:  # noqa: BLE001
        return api_error(exc)


task_tools = [
    bu_task_create,
    bu_task_get,
    bu_task_list,
    bu_task_get_status,
    bu_task_update,
    bu_task_wait,
    bu_task_run,
    bu_task_get_logs_url,
    bu_task_get_output_file_url,
]
