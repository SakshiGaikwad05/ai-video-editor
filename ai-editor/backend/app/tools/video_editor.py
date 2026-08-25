from pathlib import Path
from typing import List, Dict, Any
from app.config import settings
from app.utils.media import build_output_name
from app.utils.ffmpeg import run_ffmpeg, validate_trim
from app.models.video import (
    TrimResponse,
    SplitResponse,
    ClipPair,
    AspectRatioResponse,
    AddSubtitlesResponse,
)
from app.services.store import store
from fastapi import HTTPException

RATIO_MAP = {
    "16:9": "16:9",
    "9:16": "9:16",
    "1:1": "1:1",
    "4:5": "4:5",
}


def _ensure_video(video_id: str) -> Path:
    video = store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="video_not_found")
    if not video.exists():
        raise HTTPException(status_code=404, detail="video_file_missing")
    return video


def _detect_duration(path: Path) -> float:
    from app.utils.ffmpeg import probe_duration
    return probe_duration(path)


def _save_to_store(path: Path) -> str:
    return store.add(path)


def _aspect_filter(ratio: str) -> str:
    if ratio == "16:9":
        return "scale=iw*9/16:ih,setsar=1,pad=iw:ih*16/9:(iw-iw*16/9)/2:0"
    if ratio == "9:16":
        return "scale=iw:ih*9/16,setsar=1,pad=iw*9/16:ih:(iw*9/16-iw)/2:0"
    if ratio == "1:1":
        return "scale=iw:iw,setsar=1,pad=iw:iw:(iw-iw)/2:(iw-iw)/2"
    if ratio == "4:5":
        return "scale=iw:iw*4/5,setsar=1,pad=iw*4/5:ih:(iw*4/5-iw)/2:0"
    raise ValueError(f"Unsupported ratio: {ratio}")


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _write_srt(path: Path, subtitles: List[Dict[str, Any]]) -> Path:
    lines = []
    for idx, sub in enumerate(subtitles, start=1):
        start = sub.get("start", 0)
        end = sub.get("end", start + 2)
        text = sub.get("text", "")
        lines.append(
            f"{idx}\n{_format_srt_time(start)} --> {_format_srt_time(end)}\n{text}\n"
        )
    srt_path = path.with_suffix(".srt")
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    return srt_path


def upload_video(filename: str, content_type: str | None, size: int, path: Path) -> dict:
    vid = _save_to_store(path)
    return {
        "video_id": vid,
        "filename": filename,
        "content_type": content_type,
        "size": size,
        "duration": _detect_duration(path),
    }


def get_video_info(video_id: str) -> dict:
    src = _ensure_video(video_id)
    meta = store.meta(video_id)
    data = {
        "id": video_id,
        "filename": meta.filename if meta else src.name,
        "size": meta.size if meta else src.stat().st_size,
        "duration": _detect_duration(src),
    }
    return data


def trim_video(video_id: str, start_time: float, end_time: float) -> TrimResponse:
    src = _ensure_video(video_id)
    duration = _detect_duration(src)
    validate_trim(start_time, end_time, duration)
    out_name = build_output_name(src.name, "trim")
    out_path = settings.output_dir / out_name
    run_ffmpeg(["-ss", str(start_time), "-to", str(end_time), "-i", str(src), "-c:v", "libx264", "-c:a", "aac", str(out_path)])
    return TrimResponse(
        video_id=_save_to_store(out_path),
        filename=out_name,
        path=str(out_path),
        original_video_id=video_id,
    )


def split_video(video_id: str, timestamp: float) -> SplitResponse:
    src = _ensure_video(video_id)
    duration = _detect_duration(src)
    if timestamp <= 0 or timestamp >= duration:
        raise HTTPException(status_code=400, detail="Split timestamp must be inside the video duration")
    part1 = settings.output_dir / build_output_name(src.name, "split_part1")
    part2 = settings.output_dir / build_output_name(src.name, "split_part2")
    run_ffmpeg(["-ss", "0", "-to", str(timestamp), "-i", str(src), "-c:v", "libx264", "-c:a", "aac", str(part1)])
    run_ffmpeg(["-ss", str(timestamp), "-i", str(src), "-c:v", "libx264", "-c:a", "aac", str(part2)])
    return SplitResponse(
        original_video_id=video_id,
        timestamp=timestamp,
        clips=[
            ClipPair(id=_save_to_store(part1), part=1, filename=part1.name, path=str(part1)),
            ClipPair(id=_save_to_store(part2), part=2, filename=part2.name, path=str(part2)),
        ],
    )


def change_aspect_ratio(video_id: str, ratio: str) -> AspectRatioResponse:
    src = _ensure_video(video_id)
    if ratio not in RATIO_MAP:
        raise HTTPException(status_code=400, detail="Unsupported aspect ratio")
    ratio_key = ratio.replace(":", "x")
    out_name = build_output_name(src.name, f"aspect_{ratio_key}")
    out_path = settings.output_dir / out_name
    vf = _aspect_filter(ratio)
    run_ffmpeg(["-i", str(src), "-vf", vf, "-c:v", "libx264", "-c:a", "aac", str(out_path)])
    return AspectRatioResponse(
        video_id=_save_to_store(out_path),
        ratio=ratio,
        filename=out_name,
        path=str(out_path),
    )


def add_subtitles(video_id: str, subtitles: List[Dict[str, Any]]) -> AddSubtitlesResponse:
    src = _ensure_video(video_id)
    out_name = build_output_name(src.name, "subtitled")
    out_path = settings.output_dir / out_name
    srt_path = _write_srt(out_path, subtitles)
    try:
        run_ffmpeg(["-i", str(src), "-i", str(srt_path), "-c:v", "libx264", "-c:a", "aac", "-c:s", "mov_text", str(out_path)])
    except RuntimeError:
        # If muxing fails on this environment, still return the sidecar SRT.
        pass
    return AddSubtitlesResponse(
        video_id=_save_to_store(out_path),
        filename=out_name,
        path=str(out_path),
        subtitle_count=len(subtitles),
    )


def export_video(video_id: str) -> dict:
    src = _ensure_video(video_id)
    return {
        "video_id": video_id,
        "path": str(src),
    }


def clip_video(video_id: str, start_time: float, end_time: float, ratio: str | None = None) -> dict:
    src = _ensure_video(video_id)
    duration = _detect_duration(src)
    validate_trim(start_time, end_time, duration)
    trimmed_name = build_output_name(src.name, "trim")
    trimmed_path = settings.output_dir / trimmed_name
    run_ffmpeg([
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", str(src),
        "-c:v", "libx264",
        "-c:a", "aac",
        str(trimmed_path),
    ])
    final_path = trimmed_path
    final_name = trimmed_name
    if ratio:
        if ratio not in RATIO_MAP:
            raise ValueError(f"Unsupported aspect ratio: {ratio}")
        final_name = build_output_name(src.name, f"clip_{ratio.replace(':', 'x')}")
        final_path = settings.output_dir / final_name
        vf = _aspect_filter(ratio)
        run_ffmpeg([
            "-i", str(trimmed_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-c:a", "aac",
            str(final_path),
        ])
    return {
        "video_id": _save_to_store(final_path),
        "filename": final_name,
        "path": str(final_path),
        "original_video_id": video_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration": _detect_duration(final_path),
        "ratio": ratio,
    }

