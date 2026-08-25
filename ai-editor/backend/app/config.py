from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_ROOT = BASE_DIR / "media"
UPLOAD_DIR = MEDIA_ROOT / "uploads"
OUTPUT_DIR = MEDIA_ROOT / "outputs"

class Settings(BaseSettings):
    app_name: str = "AI Video Editor"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    ffmpeg_bin: str = "ffmpeg"
    media_root: Path = MEDIA_ROOT
    upload_dir: Path = UPLOAD_DIR
    output_dir: Path = OUTPUT_DIR

settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
