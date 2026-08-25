from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from app.config import settings

def save_upload(upload: UploadFile, prefix: str = "video") -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}_{ts}_{upload.filename}"
    dest = settings.upload_dir / filename
    with dest.open("wb") as f:
        f.write(upload.file.read())
    return dest

def build_output_name(source_name: str, suffix: str, ext: str = "mp4") -> str:
    base = Path(source_name).stem
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{base}_{suffix}_{ts}.{ext}"

def get_media_relative(path: Path) -> str:
    return str(path.relative_to(settings.media_root)).replace("\\", "/")
