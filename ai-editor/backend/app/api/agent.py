from fastapi import APIRouter, HTTPException
from app.tools.registry import AGENT_TOOLS, TOOL_DISPATCH
from app.tools.video_editor import _ensure_video
from app.services.agent_loop import manager

router = APIRouter()


def _video_ctx(video_id: str):
    src = _ensure_video(video_id)
    try:
        from app.tools.video_editor import _detect_duration
        return video_id, _detect_duration(src)
    except Exception:
        return video_id, None


@router.get("/tools")
def list_tools():
    return {"tools": [t.model_dump() for t in AGENT_TOOLS]}


@router.post("/run")
def run(payload: dict):
    command = (payload.get("command") or "").strip()
    if not command:
        raise HTTPException(status_code=400, detail="command is required")

    video_id = (payload.get("video_id") or "").strip() or None
    duration = None
    if video_id:
        try:
            video_id, duration = _video_ctx(video_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid video_id: {e}")

    snap = manager.start(command, video_id, duration)
    return {**snap, "task_id": snap["id"]}


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    return task.snapshot()


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: str):
    task = manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    manager.stop(task_id)
    return {"status": "stopping"}


@router.post("/tasks/{task_id}/approval")
def resolve_approval(task_id: str, payload: dict):
    task = manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    approved = bool(payload.get("approved"))
    if task.status != "pending_approval":
        raise HTTPException(status_code=400, detail="task is not awaiting approval")
    manager.approve(task_id, approved)
    return {"status": "approved" if approved else "denied"}


@router.post("/call")
def call_tool(payload: dict):
    name = payload.get("tool")
    arguments = payload.get("arguments", {})
    if name not in TOOL_DISPATCH:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {name}")
    try:
        return {"tool": name, "result": TOOL_DISPATCH[name](arguments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool failed: {type(e).__name__}: {e}")