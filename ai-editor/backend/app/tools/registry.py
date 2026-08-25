from app.models.video import AgentTool

AGENT_TOOLS: list[AgentTool] = [
    AgentTool(
        name="upload_video",
        description="Upload a video file for editing.",
        parameters={
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "multipart video file"},
            },
            "required": ["file"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "size": {"type": "integer"},
                "duration": {"type": ["number", "null"]},
            },
        },
    ),
    AgentTool(
        name="get_video_info",
        description="Get metadata for an uploaded video.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
            },
            "required": ["video_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "filename": {"type": "string"},
                "size": {"type": "integer"},
                "duration": {"type": ["number", "null"]},
            },
        },
    ),
    AgentTool(
        name="trim_video",
        description="Trim a video between start_time and end_time.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "original_video_id": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="split_video",
        description="Split a video at a timestamp into two clips.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "timestamp": {"type": "number", "minimum": 0},
            },
            "required": ["video_id", "timestamp"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "original_video_id": {"type": "string"},
                "timestamp": {"type": "number"},
                "clips": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "part": {"type": "integer"},
                            "filename": {"type": "string"},
                            "path": {"type": "string"},
                        },
                    },
                },
            },
        },
    ),
    AgentTool(
        name="change_aspect_ratio",
        description="Change a video's aspect ratio. Supported: 16:9, 9:16, 1:1, 4:5.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "ratio"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "ratio": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="add_subtitles",
        description="Burn subtitles into a video.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "subtitles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number", "minimum": 0},
                            "end": {"type": "number", "exclusiveMinimum": 0},
                            "text": {"type": "string", "minLength": 1},
                        },
                        "required": ["start", "end", "text"],
                    },
                    "minItems": 1,
                },
            },
            "required": ["video_id", "subtitles"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "subtitle_count": {"type": "integer"},
            },
        },
    ),
    AgentTool(
        name="export_video",
        description="Return a downloadable path for the final rendered video.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
            },
            "required": ["video_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "path": {"type": "string"},
            },
        },
    ),
    AgentTool(
        name="clip_video",
        description="Clip a video from start_time to end_time and optionally change aspect ratio. Supported ratios: 16:9, 9:16, 1:1, 4:5.",
        parameters={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "start_time": {"type": "number", "minimum": 0},
                "end_time": {"type": "number", "exclusiveMinimum": 0},
                "ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "4:5"]},
            },
            "required": ["video_id", "start_time", "end_time"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "video_id": {"type": "string"},
                "filename": {"type": "string"},
                "path": {"type": "string"},
                "original_video_id": {"type": "string"},
                "start_time": {"type": "number"},
                "end_time": {"type": "number"},
                "duration": {"type": "number"},
                "ratio": {"type": ["string", "null"]},
            },
        },
    ),
]
