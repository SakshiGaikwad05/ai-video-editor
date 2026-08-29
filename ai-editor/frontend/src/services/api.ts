const base = "/api";

export async function uploadVideo(file: File) {
  const form = new FormData();
  form.append("up", file, file.name);
  const res = await fetch(`${base}/videos/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getVideo(videoId: string) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function downloadVideo(videoId: string) {
  return `${base}/videos/${encodeURIComponent(videoId)}/download`;
}

export async function trimVideo(videoId: string, startTime: number, endTime: number) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/trim?start_time=${startTime}&end_time=${endTime}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function splitVideo(videoId: string, timestamp: number) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/split?timestamp=${timestamp}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function changeAspectRatio(videoId: string, ratio: string) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/aspect-ratio?ratio=${encodeURIComponent(ratio)}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addSubtitles(videoId: string, subtitles: Array<{start: number; end: number; text: string}>) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/subtitles`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(subtitles),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportVideo(videoId: string) {
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/export`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function clipVideo(videoId: string, startTime: number, endTime: number, ratio?: string) {
  const body: Record<string, unknown> = { start_time: startTime, end_time: endTime };
  if (ratio) body.ratio = ratio;
  const res = await fetch(`${base}/videos/${encodeURIComponent(videoId)}/clip`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listAgentTools() {
  const res = await fetch(`${base}/agent/tools`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function callAgentTool(payload: { tool: string; arguments: Record<string, unknown> }) {
  const res = await fetch(`${base}/agent/call`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAgentCommand(payload: { command: string; video_id: string }) {
  const res = await fetch(`${base}/agent/run`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
