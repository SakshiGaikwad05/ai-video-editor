import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  Play,
  Pause,
  Scissors,
  SplitSquareVertical,
  Crop,
  Type,
  Captions,
  Sparkles,
  Download,
  Undo2,
  Redo2,
  Film,
  Trash2,
  Replace,
  Wand2,
  MessageSquareText,
  X,
  Check,
  Loader2,
} from "lucide-react";
import {
  uploadVideo,
  trimVideo,
  splitVideo,
  changeAspectRatio,
  addSubtitles,
  exportVideo,
  downloadVideo,
  listAgentTools,
  clipVideo,
  getVideo,
  startAgentTask,
  getAgentTask,
  stopAgentTask,
  resolveAgentApproval,
} from "../services/api";

type TabId = "media" | "edit" | "text" | "captions" | "ai";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "media", label: "Media", icon: <Film size={16} /> },
  { id: "edit", label: "Edit", icon: <Scissors size={16} /> },
  { id: "text", label: "Text", icon: <Type size={16} /> },
  { id: "captions", label: "Captions", icon: <Captions size={16} /> },
  { id: "ai", label: "AI", icon: <Sparkles size={16} /> },
];

export default function Editor() {
  const [video, setVideo] = useState<any>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [status, setStatus] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("media");

  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(0);
  const [splitTime, setSplitTime] = useState(0);
  const [ratio, setRatio] = useState("16:9");

  const [subtitles, setSubtitles] = useState(
    () => [{ start: 0, end: 2.5, text: "Hello everyone" }]
  );

  const [aiCommand, setAiCommand] = useState("");
  const [aiRunning, setAiRunning] = useState(false);
  const [task, setTask] = useState<any>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const stopPollingRef = useRef(false);

  const [exporting, setExporting] = useState(false);
  const [exportDone, setExportDone] = useState(false);
  const [clipCmd, setClipCmd] = useState("");

  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listAgentTools().catch(() => {});
  }, []);

  const notify = (message: string) => setStatus(message);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    notify("Uploading...");
    try {
      const data = await uploadVideo(file);
      setVideo(data);
      setStartTime(0);
      setEndTime(0);
      setCurrentTime(0);
      setExportDone(false);
      notify("Video uploaded");
    } catch (err: any) {
      notify(err.message || "Upload failed");
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      const d = videoRef.current.duration;
      setDuration(d);
      setEndTime(d);
      setSplitTime(d / 2);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  };

  const togglePlay = () => {
    if (!videoRef.current || !video) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const seek = (t: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = t;
    setCurrentTime(t);
  };

  const handleTrim = async () => {
    if (!video) return;
    notify("Trimming...");
    try {
      const data = await trimVideo(video.video_id, startTime, endTime);
      setVideo(data);
      notify("Trim applied");
    } catch (err: any) {
      notify(err.message || "Trim failed");
    }
  };

  const handleClip = async (cmd?: string) => {
    if (!video) return;
    const raw = (cmd ?? "").trim();
    if (!raw) {
      notify("Enter a clip command like: clip this video from 1 min to 3 min in 16:9");
      return;
    }
    let match = raw.match(/(?:from\s+)?([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m)?\s*(?:to|-)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:min|minutes|m)?/i);
    if (!match) {
      notify("Could not parse start/end. Example: clip from 1 min to 3 min");
      return;
    }
    const start = parseFloat(match[1]);
    const end = parseFloat(match[2]);
    const ratioMatch = raw.match(/(?:in\s+)?(16:9|9:16|1:1|4:5)/);
    const ratio = ratioMatch ? ratioMatch[1] : undefined;
    notify("Clipping...");
    try {
      const data = await clipVideo(video.video_id, start, end, ratio);
      setVideo(data);
      notify("Clip created");
    } catch (err: any) {
      notify(err.message || "Clip failed");
    }
  };

  const handleSplit = async () => {
    if (!video) return;
    notify("Splitting...");
    try {
      const data = await splitVideo(video.video_id, splitTime);
      setVideo(data.clips[0]);
      notify("Split complete");
    } catch (err: any) {
      notify(err.message || "Split failed");
    }
  };

  const handleAspect = async () => {
    if (!video) return;
    notify("Changing aspect ratio...");
    try {
      const data = await changeAspectRatio(video.video_id, ratio);
      setVideo(data);
      notify("Aspect ratio updated");
    } catch (err: any) {
      notify(err.message || "Aspect ratio failed");
    }
  };

  const handleTrimAndAspect = async () => {
    if (!video) return;
    if (!ratio || ratio === "16:9") {
      await handleTrim();
      return;
    }
    notify("Clipping...");
    try {
      const data = await clipVideo(video.video_id, startTime, endTime, ratio);
      setVideo(data);
      notify("Clip created");
    } catch (err: any) {
      notify(err.message || "Clip failed");
    }
  };

  const handleSubtitles = async () => {
    if (!video) return;
    notify("Adding subtitles...");
    try {
      const data = await addSubtitles(video.video_id, subtitles);
      setVideo(data);
      notify("Subtitles added");
    } catch (err: any) {
      notify(err.message || "Subtitles failed");
    }
  };

  const handleExport = async () => {
    if (!video) return;
    setExporting(true);
    setExportDone(false);
    notify("Exporting...");
    try {
      await exportVideo(video.video_id);
      const url = await downloadVideo(video.video_id);
      notify("Export complete");
      setExportDone(true);
      const a = document.createElement("a");
      a.href = url;
      a.download = video.filename || "video.mp4";
      a.click();
    } catch (err: any) {
      notify(err.message || "Export failed");
      setExporting(false);
    }
  };

  const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

  const finishTask = async (t: any) => {
    setTask(t);
    if (t?.status === "completed") {
      for (const step of t.steps || []) {
        if (step?.kind === "tool" && step.result?.video_id) {
          const fresh = await getVideo(step.result.video_id).catch(() => null);
          if (fresh) {
            setVideo(fresh);
            break;
          }
        }
      }
      notify("Task complete");
    } else if (t?.status === "failed") {
      setAiError(t.error || "Task failed");
      notify(t.error || "Task failed");
    } else if (t?.status === "stopped") {
      notify("Task stopped");
    }
    setAiRunning(false);
  };

  const pollTask = async (taskId: string) => {
    try {
      while (!stopPollingRef.current) {
        const t = await getAgentTask(taskId);
        setTask(t);
        const terminal = t?.status === "completed" || t?.status === "failed" || t?.status === "stopped";
        if (terminal) {
          await finishTask(t);
          return;
        }
        await sleep(t?.status === "pending_approval" ? 1200 : 2000);
      }
      const t = await getAgentTask(taskId).catch(() => null);
      if (t) await finishTask(t);
    } catch (err: any) {
      setAiError(err.message || "Failed to fetch task status");
      setAiRunning(false);
    }
  };

  const runAi = async () => {
    const cmd = aiCommand.trim();
    if (!cmd || aiRunning) return;
    setAiRunning(true);
    setTask(null);
    setAiError(null);
    stopPollingRef.current = false;
    notify("Starting task...");
    try {
      const started = await startAgentTask({ command: cmd, video_id: video?.video_id });
      await pollTask(started.task_id);
    } catch (err: any) {
      setAiError(err.message || "Failed to start task");
      setAiRunning(false);
      notify(err.message || "Failed to start task");
    }
  };

  const stopTask = async () => {
    stopPollingRef.current = true;
    if (task?.id) await stopAgentTask(task.id).catch(() => {});
    notify("Stopping task...");
  };

  const approveTask = async (approved: boolean) => {
    if (!task?.id) return;
    try {
      await resolveAgentApproval(task.id, approved);
    } catch (err: any) {
      setAiError(err.message || "Failed to resolve approval");
    }
  };

  const formatTime = (t: number) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    const ms = Math.floor((t % 1) * 100);
    return `${m}:${s.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex h-screen w-full flex-col bg-gray-950 text-gray-100">
      <header className="flex items-center justify-between border-b border-gray-800 bg-gray-900/80 px-4 py-2 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-blue-400" />
            <span className="text-sm font-semibold tracking-wide">AI Video Editor</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Film size={14} />
          <span className="max-w-[200px] truncate">
            {video ? video.filename : "Untitled Project"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button className="btn-secondary rounded-md px-2 py-1.5 text-xs" title="Undo">
            <Undo2 size={16} />
          </button>
          <button className="btn-secondary rounded-md px-2 py-1.5 text-xs" title="Redo">
            <Redo2 size={16} />
          </button>
          <button
            onClick={handleExport}
            disabled={!video || exporting}
            className="btn-primary rounded-md px-3 py-1.5 text-xs"
          >
            {exporting ? "Exporting..." : exportDone ? "Export Again" : "Export"}
          </button>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden">
        <aside className="flex w-56 flex-col border-r border-gray-800 bg-gray-900/40">
          <nav className="flex flex-col gap-1 p-2">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  activeTab === tab.id
                    ? "bg-gray-800 text-white"
                    : "text-gray-400 hover:bg-gray-800/60 hover:text-gray-200"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>

          <div className="flex-1 overflow-y-auto p-3">
            {activeTab === "media" && (
              <div className="space-y-3">
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Media</h3>
                  <input ref={fileInputRef} type="file" accept="video/*" onChange={handleUpload} className="hidden" />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-primary w-full rounded-md py-2 text-xs"
                  >
                    <Upload size={14} className="mr-2" />
                    Upload Video
                  </button>
                  {video && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="btn-secondary mt-2 w-full rounded-md py-2 text-xs"
                    >
                      <Replace size={14} className="mr-2" />
                      Replace Video
                    </button>
                  )}
                </div>

                {video && (
                  <div className="panel p-3">
                    <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Current Media</h3>
                    <div className="flex items-center gap-2 text-xs text-gray-300">
                      <Film size={14} className="text-gray-500" />
                      <span className="truncate">{video.filename}</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {(video.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "edit" && (
              <div className="space-y-3">
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Trim</h3>
                  <label className="mb-1 block text-xs text-gray-500">Start (s)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={startTime}
                    onChange={(e) => setStartTime(parseFloat(e.target.value))}
                    className="input mb-2"
                  />
                  <label className="mb-1 block text-xs text-gray-500">End (s)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={endTime}
                    onChange={(e) => setEndTime(parseFloat(e.target.value))}
                    className="input mb-2"
                  />
                  <button onClick={handleTrimAndAspect} disabled={!video} className="btn-secondary w-full rounded-md py-2 text-xs">
                    <Scissors size={14} className="mr-2" />
                    {ratio && ratio !== "16:9" ? `Clip ${ratio}` : "Apply Trim"}
                  </button>
                </div>

                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Split</h3>
                  <label className="mb-1 block text-xs text-gray-500">Timestamp (s)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={splitTime}
                    onChange={(e) => setSplitTime(parseFloat(e.target.value))}
                    className="input mb-2"
                  />
                  <button onClick={handleSplit} disabled={!video} className="btn-secondary w-full rounded-md py-2 text-xs">
                    <SplitSquareVertical size={14} className="mr-2" />
                    Split at Timestamp
                  </button>
                </div>

                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Aspect Ratio</h3>
                  <select value={ratio} onChange={(e) => setRatio(e.target.value)} className="select mb-2">
                    <option value="16:9">16:9</option>
                    <option value="9:16">9:16</option>
                    <option value="1:1">1:1</option>
                    <option value="4:5">4:5</option>
                  </select>
                  <button onClick={handleAspect} disabled={!video} className="btn-secondary w-full rounded-md py-2 text-xs">
                    <Crop size={14} className="mr-2" />
                    Apply Aspect Ratio
                  </button>
                </div>

                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">AI Clip</h3>
                  <p className="mb-2 text-xs text-gray-500">
                    Try: "clip this video from 1 min to 3 min in 16:9"
                  </p>
                  <input
                    value={clipCmd}
                    onChange={(e) => setClipCmd(e.target.value)}
                    className="input mb-2"
                    placeholder="clip from 1 min to 3 min in 9:16"
                  />
                  <button onClick={() => handleClip(clipCmd)} disabled={!video} className="btn-primary w-full rounded-md py-2 text-xs">
                    Clip
                  </button>
                </div>

                <div className="panel p-3">
                  <button onClick={() => notify("Delete not implemented yet")} disabled={!video} className="btn-secondary w-full rounded-md py-2 text-xs text-red-300">
                    <Trash2 size={14} className="mr-2" />
                    Delete Selection
                  </button>
                </div>
              </div>
            )}

            {activeTab === "text" && (
              <div className="space-y-3">
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Add Text</h3>
                  <input className="input mb-2" placeholder="Enter text..." />
                  <button onClick={() => notify("Text overlay not implemented yet")} className="btn-secondary w-full rounded-md py-2 text-xs">
                    <Type size={14} className="mr-2" />
                    Add to Preview
                  </button>
                </div>
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Style</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                    <div className="rounded-md border border-dashed border-gray-700 p-2 text-center">Font</div>
                    <div className="rounded-md border border-dashed border-gray-700 p-2 text-center">Color</div>
                    <div className="rounded-md border border-dashed border-gray-700 p-2 text-center">Size</div>
                    <div className="rounded-md border border-dashed border-gray-700 p-2 text-center">Position</div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "captions" && (
              <div className="space-y-3">
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Subtitles</h3>
                  {subtitles.map((s, idx) => (
                    <div key={idx} className="mb-2 space-y-1">
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>#{idx + 1}</span>
                        <button
                          onClick={() => setSubtitles(subtitles.filter((_, i) => i !== idx))}
                          className="text-gray-500 hover:text-red-400"
                        >
                          <X size={12} />
                        </button>
                      </div>
                      <input
                        type="number"
                        step="0.1"
                        value={s.start}
                        onChange={(e) => {
                          const next = [...subtitles];
                          next[idx] = { ...s, start: parseFloat(e.target.value) };
                          setSubtitles(next);
                        }}
                        className="input"
                        placeholder="Start"
                      />
                      <input
                        type="number"
                        step="0.1"
                        value={s.end}
                        onChange={(e) => {
                          const next = [...subtitles];
                          next[idx] = { ...s, end: parseFloat(e.target.value) };
                          setSubtitles(next);
                        }}
                        className="input"
                        placeholder="End"
                      />
                      <input
                        value={s.text}
                        onChange={(e) => {
                          const next = [...subtitles];
                          next[idx] = { ...s, text: e.target.value };
                          setSubtitles(next);
                        }}
                        className="input"
                        placeholder="Subtitle text"
                      />
                    </div>
                  ))}
                  <button
                    onClick={() => setSubtitles([...subtitles, { start: 0, end: 2, text: "" }])}
                    className="btn-secondary w-full rounded-md py-2 text-xs"
                  >
                    + Add Caption
                  </button>
                  <button onClick={handleSubtitles} disabled={!video} className="btn-primary mt-2 w-full rounded-md py-2 text-xs">
                    Burn Subtitles
                  </button>
                </div>
              </div>
            )}

            {activeTab === "ai" && (
              <div className="space-y-3">
                <div className="panel p-3">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">AI Assistant</h3>
                  <p className="mb-2 text-xs text-gray-500">
                    Ask the assistant to analyze the project, edit a video, or browse the web. Example: "Analyze this project and describe what it does."
                  </p>
                  <textarea
                    value={aiCommand}
                    onChange={(e) => setAiCommand(e.target.value)}
                    className="input mb-2 h-24 resize-none"
                    placeholder="Describe what you want..."
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={runAi}
                      disabled={aiRunning || !aiCommand.trim()}
                      className="btn-primary flex-1 rounded-md py-2 text-xs"
                    >
                      {aiRunning ? (
                        <>
                          <Loader2 size={14} className="mr-2 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Wand2 size={14} className="mr-2" />
                          Run AI
                        </>
                      )}
                    </button>
                    {(aiRunning || task?.status === "running" || task?.status === "pending_approval") && (
                      <button
                        onClick={stopTask}
                        className="btn-secondary rounded-md px-3 py-2 text-xs text-red-300"
                      >
                        <X size={14} className="mr-1" />
                        Stop
                      </button>
                    )}
                  </div>

                  {aiError && (
                    <div className="mt-2 rounded-md border border-red-800 bg-red-950/40 p-2 text-xs text-red-300">
                      <div className="mb-1 font-semibold">Error</div>
                      <pre className="whitespace-pre-wrap">{aiError}</pre>
                    </div>
                  )}

                  {task && (
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center gap-2 text-xs">
                        <span
                          className={`rounded-full px-2 py-0.5 font-medium ${
                            task.status === "completed"
                              ? "bg-green-900/60 text-green-300"
                              : task.status === "failed"
                              ? "bg-red-900/60 text-red-300"
                              : task.status === "pending_approval"
                              ? "bg-amber-900/60 text-amber-300"
                              : task.status === "stopped"
                              ? "bg-gray-700 text-gray-300"
                              : "bg-blue-900/60 text-blue-300"
                          }`}
                        >
                          {task.status}
                        </span>
                        {task.current_tool && (
                          <span className="text-blue-300">
                            <Loader2 size={12} className="mr-1 inline animate-spin" />
                            tool: {task.current_tool}
                          </span>
                        )}
                        {task.iteration ? <span className="text-gray-500">iter {task.iteration}</span> : null}
                      </div>

                      {task.status === "pending_approval" && task.pending_action && (
                        <div className="rounded-md border border-amber-700 bg-amber-950/30 p-2">
                          <div className="mb-1 text-xs font-medium text-amber-300">Approval required</div>
                          <pre className="mb-2 overflow-x-auto whitespace-pre-wrap text-[11px] text-amber-200">
                            {JSON.stringify(task.pending_action, null, 2)}
                          </pre>
                          <div className="flex gap-2">
                            <button
                              onClick={() => approveTask(true)}
                              className="btn-primary flex-1 rounded-md py-1.5 text-xs"
                            >
                              <Check size={14} className="mr-1 inline" />
                              Approve
                            </button>
                            <button
                              onClick={() => approveTask(false)}
                              className="btn-secondary flex-1 rounded-md py-1.5 text-xs"
                            >
                              <X size={14} className="mr-1 inline" />
                              Deny
                            </button>
                          </div>
                        </div>
                      )}

                      {task.plan?.length > 0 && (
                        <div className="rounded-md bg-gray-800/60 p-2">
                          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Plan</div>
                          <ol className="list-inside list-decimal space-y-0.5 text-[11px] text-gray-300">
                            {task.plan.map((s: string, i: number) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ol>
                        </div>
                      )}

                      {(task.steps?.length ?? 0) > 0 && (
                        <div className="rounded-md bg-gray-800/60 p-2">
                          <div className="mb-1 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                            <span>Execution</span>
                            <span className="text-gray-500">{task.steps.length} steps</span>
                          </div>
                          <div className="space-y-1.5">
                            {task.steps.map((s: any, i: number) => (
                              <div key={i} className="rounded bg-gray-900/70 p-1.5">
                                <div className="flex items-center justify-between gap-1">
                                  <span className="text-[11px] font-medium text-gray-300">
                                    {s.kind === "plan"
                                      ? `Plan (${s.steps?.length ?? 0} steps)`
                                      : s.kind === "tool"
                                      ? `${s.tool}`
                                      : s.kind === "error"
                                      ? `Error in ${s.tool || "step"}`
                                      : s.kind === "approval"
                                      ? `${s.tool} (denied)`
                                      : s.kind}
                                  </span>
                                  <span className="text-[10px] text-gray-600">#{i + 1}</span>
                                </div>
                                {s.kind === "tool" && (
                                  <pre className="mt-1 max-h-28 overflow-auto whitespace-pre-wrap text-[10px] text-gray-400">
                                    {JSON.stringify(s.result ?? s.arguments, null, 2)}
                                  </pre>
                                )}
                                {s.error && (
                                  <pre className="mt-1 max-h-20 overflow-auto whitespace-pre-wrap text-[10px] text-red-400">
                                    {s.error}
                                  </pre>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {task.final_answer && (
                        <div className="rounded-md border border-green-800 bg-green-950/20 p-2">
                          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-green-400">Final answer</div>
                          <p className="whitespace-pre-wrap text-xs text-green-100">{task.final_answer}</p>
                        </div>
                      )}

                      {task.error && (
                        <div className="rounded-md border border-red-800 bg-red-950/20 p-2 text-xs text-red-300">
                          {task.error}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>

        <section className="flex flex-1 flex-col">
          <div className="flex flex-1 items-center justify-center bg-black/40 p-4">
            {video ? (
              <div className="relative w-full max-w-4xl">
                <video
                  ref={videoRef}
                  className="max-h-[60vh] w-full rounded-lg border border-gray-800 bg-black"
                  controls={false}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  src={`/api/videos/${video.video_id}/download`}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <button
                    onClick={togglePlay}
                    className="rounded-full bg-white/10 p-3 backdrop-blur hover:bg-white/20"
                  >
                    {isPlaying ? <Pause size={24} className="text-white" /> : <Play size={24} className="text-white" />}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-3 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-800">
                  <Upload size={28} className="text-gray-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-300">Drop your video here</p>
                  <p className="text-xs text-gray-500">or</p>
                </div>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-primary rounded-md px-4 py-2 text-xs"
                >
                  Upload Video
                </button>
                <p className="text-xs text-gray-600">MP4, MOV, WebM</p>
              </div>
            )}
          </div>

          <div className="border-t border-gray-800 bg-gray-900/60 p-3">
            <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
            <div className="relative h-12 rounded-md border border-gray-800 bg-gray-900">
              <div className="absolute inset-x-0 top-1/2 -translate-y-1/2">
                <div className="mx-auto h-2 w-full max-w-5xl rounded-full bg-gray-800" />
                <div
                  className="mx-auto h-2 rounded-full bg-blue-500/80"
                  style={{
                    width: duration ? `${Math.max(((endTime - startTime) / duration) * 100, 2)}%` : "0%",
                    marginLeft: duration ? `${(startTime / duration) * 100}%` : "0%",
                  }}
                />
              </div>
              <input
                type="range"
                min={0}
                max={duration || 0}
                step="0.01"
                value={currentTime}
                onChange={(e) => seek(parseFloat(e.target.value))}
                className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
              />
              <div
                className="absolute top-0 h-full w-0.5 bg-blue-400"
                style={{ left: duration ? `${(currentTime / duration) * 100}%` : "0%" }}
              />
            </div>
          </div>
        </section>

        <aside className="w-64 border-l border-gray-800 bg-gray-900/40 p-3">
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-gray-400">Properties</h3>

          <div className="panel mb-3 p-3">
            <div className="flex items-center gap-2 text-xs text-gray-300">
              <Film size={14} className="text-gray-500" />
              <span className="truncate">{video ? video.filename : "No clip selected"}</span>
            </div>
          </div>

          {video && (
            <div className="panel mb-3 p-3 space-y-3">
              <div>
                <label className="mb-1 block text-xs text-gray-500">Start</label>
                <input
                  type="number"
                  step="0.1"
                  value={startTime}
                  onChange={(e) => setStartTime(parseFloat(e.target.value))}
                  className="input"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">End</label>
                <input
                  type="number"
                  step="0.1"
                  value={endTime}
                  onChange={(e) => setEndTime(parseFloat(e.target.value))}
                  className="input"
                />
              </div>
              <div className="text-xs text-gray-400">
                Duration: <span className="text-gray-200">{(endTime - startTime).toFixed(2)} sec</span>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">Aspect Ratio</label>
                <select value={ratio} onChange={(e) => setRatio(e.target.value)} className="select">
                  <option value="16:9">16:9</option>
                  <option value="9:16">9:16</option>
                  <option value="1:1">1:1</option>
                  <option value="4:5">4:5</option>
                </select>
                <button onClick={handleAspect} className="btn-secondary mt-2 w-full rounded-md py-2 text-xs">
                  <Crop size={14} className="mr-2" />
                  Apply Aspect Ratio
                </button>
              </div>
            </div>
          )}

          <div className="panel p-3">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Quick Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => setActiveTab("captions")}
                disabled={!video}
                className="btn-secondary w-full rounded-md py-2 text-xs"
              >
                <MessageSquareText size={14} className="mr-2" />
                Add Captions
              </button>
              <button
                onClick={() => setActiveTab("ai")}
                disabled={!video}
                className="btn-secondary w-full rounded-md py-2 text-xs"
              >
                <Sparkles size={14} className="mr-2" />
                Open AI Assistant
              </button>
              <button
                onClick={handleExport}
                disabled={!video}
                className="btn-primary w-full rounded-md py-2 text-xs"
              >
                <Download size={14} className="mr-2" />
                Export Video
              </button>
            </div>
          </div>
        </aside>
      </main>

      <footer className="border-t border-gray-800 bg-gray-900/80 p-3">
        <div className="mx-auto flex max-w-5xl items-center gap-3">
          <div className="flex flex-1 items-center gap-2 rounded-md border border-gray-800 bg-gray-900 px-3 py-2">
            <Sparkles size={16} className="text-blue-400" />
            <input
              value={aiCommand}
              onChange={(e) => setAiCommand(e.target.value)}
              className="flex-1 bg-transparent text-sm text-gray-100 placeholder:text-gray-600 focus:outline-none"
              placeholder='Try: "Make this a YouTube Short with subtitles."'
            />
            <button
              onClick={runAi}
              disabled={aiRunning || !aiCommand.trim()}
              className="btn-primary rounded-md px-3 py-1.5 text-xs"
            >
              {aiRunning ? "Running..." : "Run AI"}
            </button>
          </div>
        </div>
        <div className="mx-auto mt-1 flex max-w-5xl items-center justify-between text-xs text-gray-500">
          <span>{status || "Ready"}</span>
          <span>Hermes-ready tool layer active</span>
        </div>
      </footer>

      {exportDone && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur">
          <div className="panel w-full max-w-md p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-green-400">
              <Check size={18} />
              Export complete
            </div>
            <p className="mb-4 text-xs text-gray-400">
              Your video is ready. You can preview it or download the file.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => video && downloadVideo(video.video_id)}
                className="btn-primary flex-1 rounded-md py-2 text-xs"
              >
                <Download size={14} className="mr-2" />
                Download
              </button>
              <button
                onClick={() => setExportDone(false)}
                className="btn-secondary flex-1 rounded-md py-2 text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
