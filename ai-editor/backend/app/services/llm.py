"""
Hermes-compatible AI agent service.

Supports:
- Ollama local models
- OpenAI-compatible backends, including Hermes-style servers

The active provider/model are chosen via backend settings, with local
`.env` values overriding defaults.
"""

import json
import re
import httpx
from typing import Any
from app.config import settings

SYSTEM_PROMPT = """\
You are an AI video-editor assistant.  Given a user command and a list of
available tools, decide which single tool to call and with what arguments.

Return ONLY valid JSON matching one of these shapes — nothing else:

{"tool": "<tool_name>", "arguments": { ... }}

Available tools:
- trim_video(video_id, start_time: float, end_time: float)
- split_video(video_id, timestamp: float)
- change_aspect_ratio(video_id, ratio: "16:9"|"9:16"|"1:1"|"4:5")
- add_subtitles(video_id, subtitles: [{start: float, end: float, text: string}])
- clip_video(video_id, start_time: float, end_time: float, ratio?: "16:9"|"9:16"|"1:1"|"4:5")
- export_video(video_id)

Rules:
- start_time and end_time are in seconds.
- If the user says "minutes", multiply by 60.
- If the user does not specify exact times, use reasonable defaults
  (start=0, end=video duration, or infer from context).
- Always include video_id in arguments.
- Return ONLY the JSON object, no explanation.
"""


def _build_user_message(command: str, video_id: str, duration: float) -> str:
    return (
        f"video_id: {video_id}\n"
        f"video_duration_seconds: {duration}\n\n"
        f"User command: {command}"
    )


def _chat_completion(base_url: str, api_key: str | None, model: str, payload: dict) -> dict:
    base = base_url.rstrip("/")
    if "/chat/completions" in base:
        url = base
    elif base.endswith("/v1"):
        url = f"{base}/chat/completions"
    else:
        url = f"{base}/chat/completions"

    headers: dict[str, str] = {
        "content-type": "application/json",
    }
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"

    resp = httpx.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _parse_tool_call(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError(f"Could not parse LLM response: {text}")
        parsed = json.loads(m.group())

    tool = parsed.get("tool")
    args = parsed.get("arguments", {})

    if not tool:
        raise ValueError(f"LLM response missing 'tool': {parsed}")

    return {"tool": tool, "arguments": args}


def parse_command(command: str, video_id: str, duration: float) -> dict[str, Any]:
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(command, video_id, duration)},
        ],
        "stream": False,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        body = _chat_completion(settings.llm_base_url, settings.llm_api_key, settings.llm_model, payload)
        raw_text = (body.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        if raw_text:
            parsed = _parse_tool_call(raw_text)
            if "video_id" not in parsed["arguments"]:
                parsed["arguments"]["video_id"] = video_id
            return parsed
    except Exception:
        pass

    return _local_fallback(command, video_id, duration)


def _local_fallback(command: str, video_id: str, duration: float) -> dict[str, Any]:
    text = command.lower()

    if text.startswith("export") or "export" in text:
        return {"tool": "export_video", "arguments": {"video_id": video_id}}

    if "subtitle" in text or "captions" in text:
        return {
            "tool": "add_subtitles",
            "arguments": {
                "video_id": video_id,
                "subtitles": [
                    {"start": 0.0, "end": max(2.0, duration / 4), "text": "AI generated subtitle"},
                    {"start": max(2.0, duration / 4), "end": duration, "text": "AI generated subtitle"},
                ],
            },
        }

    aspect = None
    for ratio in ["16:9", "9:16", "1:1", "4:5"]:
        if ratio in text:
            aspect = ratio
            break

    times = _parse_time_range(text, duration)
    if times is not None:
        start, end = times
        if aspect:
            return {
                "tool": "clip_video",
                "arguments": {"video_id": video_id, "start_time": start, "end_time": end, "ratio": aspect},
            }
        return {
            "tool": "trim_video",
            "arguments": {"video_id": video_id, "start_time": start, "end_time": end},
        }

    if "split" in text or "cut at" in text:
        ts = _parse_timestamp(text, duration)
        if ts is not None:
            return {"tool": "split_video", "arguments": {"video_id": video_id, "timestamp": ts}}

    if "first" in text:
        value = _parse_simple_number(text, "first")
        if value is not None:
            end = min(value, duration)
            if aspect:
                return {"tool": "clip_video", "arguments": {"video_id": video_id, "start_time": 0.0, "end_time": end, "ratio": aspect}}
            return {"tool": "trim_video", "arguments": {"video_id": video_id, "start_time": 0.0, "end_time": end}}

    if "last" in text:
        value = _parse_simple_number(text, "last")
        if value is not None:
            start = max(0.0, duration - value)
            if aspect:
                return {"tool": "clip_video", "arguments": {"video_id": video_id, "start_time": start, "end_time": duration, "ratio": aspect}}
            return {"tool": "trim_video", "arguments": {"video_id": video_id, "start_time": start, "end_time": duration}}

    return {"tool": "trim_video", "arguments": {"video_id": video_id, "start_time": 0.0, "end_time": duration}}


def _parse_simple_number(text: str, keyword: str) -> float | None:
    pattern = rf"{keyword}\s+([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m|s|sec|seconds)?"
    match = re.search(pattern, text)
    if not match:
        return None
    value = float(match.group(1))
    if "min" in text or "minutes" in text or " m " in f" {text} ":
        return value * 60
    return value


def _parse_timestamp(text: str, duration: float) -> float | None:
    match = re.search(r"at\s+([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m|s|sec)?", text)
    if not match:
        return None
    value = float(match.group(1))
    if "min" in text or "minutes" in text or " m " in f" {text} ":
        return value * 60
    return value


def _parse_time_range(text: str, duration: float) -> tuple[float, float] | None:
    match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m|s|sec)?\s*(?:to|-)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m|s|sec)?",
        text,
    )
    if not match:
        return None

    def _coerce(raw: str) -> float:
        value = float(raw)
        if text.lower().count("min") or text.lower().count("minutes") or bool(re.search(r'\bm\b', text)):
            return value * 60
        return value

    start = _coerce(match.group(1))
    end = _coerce(match.group(2))
    if end <= start:
        end = start + min(10.0, max(1.0, duration - start))
    return start, min(end, duration)
