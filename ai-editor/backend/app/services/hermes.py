"""
Hermes Agent CLI gateway.

Executes Hermes as the AI orchestrator for video commands.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings

HERMES_CLI = Path(settings.hermes_cli)

TOOL_DEFINITIONS = [
    {
        "name": "trim_video",
        "description": "Trim a video between start_time and end_time.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
    },
    {
        "name": "split_video",
        "description": "Split a video at a timestamp into two clips.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "timestamp": {"type": "number", "minimum": 0},
            },
            "required": ["video_id", "timestamp"],
        },
    },
    {
        "name": "change_aspect_ratio",
        "description": "Change a video's aspect ratio. Supported: 16:9, 9:16, 1:1, 4:5.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "ratio"],
        },
    },
    {
        "name": "add_subtitles",
        "description": "Burn subtitles into a video.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "subtitles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number", "minimum": 0},
                            "end": {"type": "number", "exclusiveMinimum": 0},
                            "text": {"type": "string", "minLength": 1},
                        },
                        "required": ["start", "end", "text"],
                    },
                    "minItems": 1,
                },
            },
            "required": ["video_id", "subtitles"],
        },
    },
    {
        "name": "export_video",
        "description": "Return a downloadable path for the final rendered video.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
            },
            "required": ["video_id"],
        },
    },
    {
        "name": "clip_video",
        "description": "Clip a video from start_time to end_time and optionally change aspect ratio. Supported ratios: 16:9, 9:16, 1:1, 4:5.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
    },
]


def _build_prompt(command: str, video_id: str, duration: float) -> str:
    tools_json = json.dumps(TOOL_DEFINITIONS, ensure_ascii=False, indent=2)
    return (
        "You are an AI video-editor assistant. Given a user command and a list of "
        "available tools, decide which single tool to call and with what arguments.\n\n"
        "Available tools:\n"
        f"{tools_json}\n\n"
        "Rules:\n"
        "- start_time and end_time are in seconds.\n"
        "- If the user says 'minutes', multiply by 60.\n"
        "- If the user does not specify exact times, use reasonable defaults "
        "(start=0, end=video duration, or infer from context).\n"
        "- Always include video_id in arguments.\n"
        "- Return ONLY a valid JSON object matching {\"tool\": \"...\", \"arguments\": {...}}.\n"
        f"video_id: {video_id}\n"
        f"video_duration_seconds: {duration}\n\n"
        f"User command: {command}"
    )


def _parse_tool_call(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"Could not parse Hermes response: {text}")
        parsed = json.loads(m.group())

    tool = parsed.get("tool")
    args = parsed.get("arguments", {})

    if not tool:
        raise ValueError(f"Hermes response missing 'tool': {parsed}")

    return {"tool": tool, "arguments": args}


def run_agent(command: str, video_id: str, duration: float) -> dict[str, Any]:
    prompt = _build_prompt(command, video_id, duration)

    proc = subprocess.run(
        [str(HERMES_CLI), "-z", prompt, "--cli"],
        capture_output=True,
        text=True,
        timeout=180,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Hermes CLI failed with code {proc.returncode}: {proc.stderr[-500:]}"
        )

    raw = proc.stdout.strip()
    if not raw:
        raise RuntimeError(f"Hermes CLI returned empty output. stderr: {proc.stderr[-500:]}")

    parsed = _parse_tool_call(raw)

    if "video_id" not in parsed["arguments"]:
        parsed["arguments"]["video_id"] = video_id

    return parsed
