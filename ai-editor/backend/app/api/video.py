from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
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
from app.services.store import store
from app.models.video import TrimResponse, SplitResponse, AspectRatioResponse, AddSubtitlesResponse
from app.utils.media import save_upload

router = APIRouter()

@router.post("/upload")
def upload(up: UploadFile = File(...)):
    if not up.content_type or not up.content_type.startswith("video"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video")
    dest = save_upload(up)
    result = upload_video(up.filename, up.content_type, dest.stat().st_size, dest)
    return result

@router.get("/{video_id}")
def get_video(video_id: str):
    video = store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="video_not_found")
    return {
        "id": video_id,
        "filename": video.name,
        "size": video.stat().st_size,
        "duration": get_video_info(video_id).get("duration"),
    }

@router.get("/{video_id}/download")
def download_video(video_id: str):
    video = store.get(video_id)
    if not video or not video.exists():
        raise HTTPException(status_code=404, detail="video_not_found")
    return FileResponse(video, filename=video.name, media_type="video/mp4")

@router.post("/{video_id}/trim", response_model=TrimResponse)
def trim(video_id: str, start_time: float, end_time: float):
    return trim_video(video_id, start_time, end_time)

@router.post("/{video_id}/split", response_model=SplitResponse)
def split(video_id: str, timestamp: float):
    return split_video(video_id, timestamp)

@router.post("/{video_id}/aspect-ratio", response_model=AspectRatioResponse)
def aspect_ratio(video_id: str, ratio: str):
    return change_aspect_ratio(video_id, ratio)

@router.post("/{video_id}/subtitles", response_model=AddSubtitlesResponse)
def subtitles(video_id: str, subtitles: list[dict]):
    return add_subtitles(video_id, subtitles)

@router.post("/{video_id}/export")
def export(video_id: str):
    return export_video(video_id)

@router.post("/{video_id}/clip")
def clip(video_id: str, start_time: float, end_time: float, ratio: str | None = None):
    return clip_video(video_id, start_time, end_time, ratio)
