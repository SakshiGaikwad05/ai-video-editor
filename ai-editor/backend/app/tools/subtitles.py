import json
from pathlib import Path
from typing import List
from app.models.video import SubtitleItem

def build_ass_from_subtitles(path: Path, subtitles: List[SubtitleItem], video_path: Path):
    srt_content = []
    for idx, item in enumerate(subtitles, start=1):
        srt_content.append(
            f"{idx}\n{_format_time(item.start)} --> {_format_time(item.end)}\n{item.text}\n"
        )
    srt_path = path.with_suffix(".srt")
    srt_path.write_text("\n".join(srt_content), encoding="utf-8")

    ass_path = path.with_suffix(".ass")
    escaped = [str(video_path), str(srt_path)]
    cmd = [
        "ffmpeg",
        "-y",
        *escaped,
        str(ass_path),
    ]
    return ass_path

def _format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"
