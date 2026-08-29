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
    clip_video,
    _detect_duration,
    _ensure_video,
)
from app.services.store import store
from app.services.hermes import run_agent

router = APIRouter()


@router.get("/tools")
def list_tools():
    return {"tools": [t.model_dump() for t in AGENT_TOOLS]}


@router.post("/run")
def run(payload: dict):
    command = (payload.get("command") or "").strip()
    video_id = (payload.get("video_id") or "").strip()

    if not command:
        raise HTTPException(status_code=400, detail="command is required")
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")

    src = _ensure_video(video_id)
    duration = _detect_duration(src)

    try:
        parsed = run_agent(command, video_id, duration)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Hermes agent failed: {e}")

    name = parsed["tool"]
    arguments = parsed["arguments"]

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
        "clip_video": lambda args: clip_video(
            args["video_id"], args["start_time"], args["end_time"], args.get("ratio")
        ),
    }

    if name not in tool_map:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {name}")

    return {"tool": name, "result": tool_map[name](arguments)}

