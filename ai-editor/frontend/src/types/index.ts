export type VideoMeta = {
  id: string;
  filename: string;
  size: number;
  duration: number | null;
  url?: string;
};

export type ToolDefinition = {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  output_schema: Record<string, unknown>;
};

export type TrimResponse = {
  video_id: string;
  filename: string;
  path: string;
  original_video_id: string;
};

export type SplitResponse = {
  original_video_id: string;
  timestamp: number;
  clips: Array<{
    id: string;
    part: number;
    filename: string;
    path: string;
  }>;
};

export type AspectRatioResponse = {
  video_id: string;
  ratio: string;
  filename: string;
  path: string;
};

export type AddSubtitlesResponse = {
  video_id: string;
  filename: string;
  path: string;
  subtitle_count: number;
};
