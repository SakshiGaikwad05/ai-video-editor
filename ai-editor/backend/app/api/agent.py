from fastapi import APIRouter, HTTPException
from app.tools.registry import AGENT_TOOLS
from app.tools.video_editor import (
    upload_video,
    get_video_info,
    trim_video,
    split_video,
    change_aspect_ratio,
    add_subtitles,
    export_video,
)
from app.models.video import TrimResponse, SplitResponse, AspectRatioResponse, AddSubtitlesResponse

router = APIRouter()

@router.get("/tools")
def list_tools():
    return {"tools": [t.model_dump() for t in AGENT_TOOLS]}

@router.post("/call")
def call_tool(payload: dict):
    name = payload.get("tool")
    arguments = payload.get("arguments", {})

    tool_map = {
        "upload_video": lambda args: upload_video(
            args.get("filename"), args.get("content_type"), args.get("size"), args.get("path")
        ),
        "get_video_info": lambda args: get_video_info(args["video_id"]),
        "trim_video": lambda args: trim_video(args["video_id"], args["start_time"], args["end_time"]),
        "split_video": lambda args: split_video(args["video_id"], args["timestamp"]),
        "change_aspect_ratio": lambda args: change_aspect_ratio(args["video_id"], args["ratio"]),
        "add_subtitles": lambda args: add_subtitles(args["video_id"], args["subtitles"]),
        "export_video": lambda args: export_video(args["video_id"]),
        "clip_video": lambda args: clip_video(args["video_id"], args["start_time"], args["end_time"], args.get("ratio")),
    }

    if name not in tool_map:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {name}")
    return {"tool": name, "result": tool_map[name](arguments)}
