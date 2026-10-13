from app.models.video import AgentTool

VIDEO_AGENT_TOOLS: list[AgentTool] = [
    AgentTool(
        name="upload_video",
        description="Register a video file that already exists on disk into the media store. Returns a video_id usable by the other video tools.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or project-relative path to a video file (.mp4/.mov etc.)",
                },
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "size": {"type": "integer"},
                "duration": {"type": ["number", "null"]},
            },
        },
    ),
    AgentTool(
        name="get_video_info",
        description="Get metadata for an uploaded video.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
            },
            "required": ["video_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "filename": {"type": "string"},
                "size": {"type": "integer"},
                "duration": {"type": ["number", "null"]},
            },
        },
    ),
    AgentTool(
        name="trim_video",
        description="Trim a video between start_time and end_time.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "original_video_id": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="split_video",
        description="Split a video at a timestamp into two clips.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "timestamp": {"type": "number", "minimum": 0},
            },
            "required": ["video_id", "timestamp"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "original_video_id": {"type": "string"},
                "timestamp": {"type": "number"},
                "clips": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "part": {"type": "integer"},
                            "filename": {"type": "string"},
                            "path": {"type": "string"},
                        },
                    },
                },
            },
        },
    ),
    AgentTool(
        name="change_aspect_ratio",
        description="Change a video's aspect ratio. Supported: 16:9, 9:16, 1:1, 4:5.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "ratio"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "ratio": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="add_subtitles",
        description="Burn subtitles into a video.",
        parameters={
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
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "subtitle_count": {"type": "integer"},
            },
        },
    ),
    AgentTool(
        name="export_video",
        description="Return a downloadable path for the final rendered video.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
            },
            "required": ["video_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "path": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="clip_video",
        description="Clip a video from start_time to end_time and optionally change aspect ratio. Supported ratios: 16:9, 9:16, 1:1, 4:5.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "original_video_id": {"type": "string"},
                "start_time": {"type": "number"},
                "end_time": {"type": "number"},
                "duration": {"type": "number"},
                "ratio": {"type": ["string", "null"]},
            },
        },
    ),
]

from pathlib import Path
import mimetypes

from app.tools.general import GENERAL_AGENT_TOOLS, GENERAL_DISPATCH
from app.tools.video_editor import (
    upload_video,
    get_video_info,
    trim_video,
    split_video,
    change_aspect_ratio,
    add_subtitles,
    export_video,
    clip_video,
)
from app.tools.general import _resolve

AGENT_TOOLS: list[AgentTool] = VIDEO_AGENT_TOOLS + GENERAL_AGENT_TOOLS


def _upload_from_path(path: str) -> dict:
    p = _resolve(path)
    if not p.is_file():
        raise ValueError(f"not a file or missing: {path}")
    ctype = mimetypes.guess_type(p.name)[0] or "video/mp4"
    return upload_video(p.name, ctype, p.stat().st_size, p)


VIDEO_DISPATCH = {
    "upload_video": lambda args: _upload_from_path(args["path"]),
    "get_video_info": lambda args: get_video_info(args["video_id"]),
    "trim_video": lambda args: trim_video(args["video_id"], args["start_time"], args["end_time"]),
    "split_video": lambda args: split_video(args["video_id"], args["timestamp"]),
    "change_aspect_ratio": lambda args: change_aspect_ratio(args["video_id"], args["ratio"]),
    "add_subtitles": lambda args: add_subtitles(args["video_id"], args["subtitles"]),
    "export_video": lambda args: export_video(args["video_id"]),
    "clip_video": lambda args: clip_video(
        args["video_id"], args["start_time"], args["end_time"], args.get("ratio")
    ),
}

TOOL_DISPATCH = {**VIDEO_DISPATCH, **GENERAL_DISPATCH}

APPROVAL_REQUIRED_TOOLS = {
    t.name: t.requires_approval for t in AGENT_TOOLS
}
