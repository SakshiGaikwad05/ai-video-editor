from pydantic import BaseModel, Field, model_validator
from typing import Optional, List


class VideoMeta(BaseModel):
    id: str
    filename: str
    content_type: Optional[str] = None
    size: int
    duration: Optional[float] = None


class TrimRequest(BaseModel):
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")

    @model_validator(mode="after")
    def validate_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class TrimResponse(BaseModel):
    video_id: str
    filename: str
    path: str
    original_video_id: str


class SplitRequest(BaseModel):
    timestamp: float = Field(..., ge=0, description="Split timestamp in seconds")


class ClipPair(BaseModel):
    id: str
    part: int
    filename: str
    path: str


class SplitResponse(BaseModel):
    original_video_id: str
    timestamp: float
    clips: List[ClipPair]


class AspectRatioRequest(BaseModel):
    ratio: str = Field(..., pattern=r"^(16:9|9:16|1:1|4:5)$", description="Target aspect ratio")


class AspectRatioResponse(BaseModel):
    video_id: str
    ratio: str
    filename: str
    path: str


class SubtitleItem(BaseModel):
    start: float = Field(..., ge=0, description="Subtitle start time in seconds")
    end: float = Field(..., gt=0, description="Subtitle end time in seconds")
    text: str = Field(..., min_length=1, description="Subtitle text")

    @model_validator(mode="after")
    def validate_times(self):
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class AddSubtitlesRequest(BaseModel):
    subtitles: List[SubtitleItem] = Field(..., min_length=1)


class AddSubtitlesResponse(BaseModel):
    video_id: str
    filename: str
    path: str
    subtitle_count: int


class AgentTool(BaseModel):
    name: str
    description: str
    parameters: dict
    output_schema: dict
