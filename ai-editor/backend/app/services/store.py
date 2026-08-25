from pathlib import Path
from app.config import settings
from app.models.video import VideoMeta


class Store:
    def __init__(self) -> None:
        self._next = 1
        self._videos: dict[str, Path] = {}
        self._meta: dict[str, VideoMeta] = {}

    def add(self, path: Path) -> str:
        vid = f"vid_{self._next}"
        self._next += 1
        self._videos[vid] = path
        self._meta[vid] = VideoMeta(
            id=vid,
            filename=path.name,
            size=path.stat().st_size,
        )
        return vid

    def get(self, vid: str) -> Path | None:
        return self._videos.get(vid)

    def meta(self, vid: str) -> VideoMeta | None:
        return self._meta.get(vid)


store = Store()
