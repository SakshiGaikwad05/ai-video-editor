import subprocess
from pathlib import Path
from app.config import settings

def run_ffmpeg(cmd: list[str | Path]) -> subprocess.CompletedProcess:
    full_cmd = [settings.ffmpeg_bin, "-y", *map(str, cmd)]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")
    return result

def probe_duration(path: Path) -> float:
    cmd = [
        settings.ffmpeg_bin,
        "-i",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    for line in proc.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration"):
            time = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    raise RuntimeError("Could not detect video duration")

def validate_trim(start: float, end: float, duration: float) -> tuple[float, float]:
    if start < 0 or end < 0:
        raise ValueError("Trim times must be non-negative")
    if start >= end:
        raise ValueError("Start time must be less than end time")
    if end > duration:
        raise ValueError(f"End time {end} exceeds video duration {duration}")
    return start, end
