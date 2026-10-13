import json
import re
import threading
import time
import uuid
from typing import Any

from app.config import settings
from app.services import hermes
from app.tools.registry import AGENT_TOOLS, TOOL_DISPATCH

MAX_STEPS = 8
LLM_TIMEOUT = 300
RESULT_TRUNCATE = 4000
HISTORY_MAX_LINES = 160
JSON_RETRY_LIMIT = 2


def _truncate(value: Any) -> str:
    text = str(value)
    if len(text) > RESULT_TRUNCATE:
        text = text[:RESULT_TRUNCATE] + "\n...[truncated]"
    return text


def _build_system_prompt(video_ctx: str | None) -> str:
    tool_lines = []
    for t in AGENT_TOOLS:
        d = t.model_dump()
        tool_lines.append(
            "- %s\n  description: %s\n  parameters: %s\n  requires_approval: %s"
            % (
                d["name"],
                d["description"],
                json.dumps(d["parameters"]),
                d.get("requires_approval", False),
            )
        )
    tools_text = "\n".join(tool_lines)

    ctx = f"You are running as an agent inside the project at: {settings.project_root} (the web app serves this project)."
    if video_ctx:
        ctx += f"\nCurrent video context: {video_ctx}"

    return f"""You are the reasoner component of an autonomous agent that completes user tasks inside the AI Video Editor project.

{ctx}

CRITICAL ROLE:
- You have NO tools on your side. You CANNOT inspect files, run commands, or fetch websites yourself.
- The ONLY way for you to act is to reply with a single JSON action object; a separate executor will run the chosen tool and return its result to you.
- You must NOT announce, describe, or claim to have used a tool. You must NOT answer questions about code, files, or websites from memory or guesses.

How to work:
1. Think step by step. For multi-step tasks, first emit a plan action.
2. Then emit ONE tool action at a time. Wait for the tool result (it will be appended to your context) before deciding the next action.
3. Use the available tools to gather real information. To inspect the project use list_files then read_file. To read a web page use browse_url and base your answer ONLY on its returned title/headings/preview.
4. Ignore vendor/build directories while exploring: node_modules, .venv, __pycache__, .git, dist, build, media.
5. run_shell requires human approval. If denied, adjust and continue without it.
6. Only after the necessary information has been gathered, emit a single "final" action containing the complete answer for the user.

Every reply you send MUST be exactly one JSON object matching one of these three shapes, with no markup, no code fences, and no other text:
{{"action":"plan","steps":["step1","step2"]}}
{{"action":"tool","tool":"<exact_tool_name>","arguments":{{...}}}}
{{"action":"final","answer":"<complete answer>"}}

AVAILABLE TOOLS (use only these names):
{tools_text}
"""

REPLY_RULE = "\n\nReply NOW with exactly one JSON object and zero other text, matching one of these three exactly:\n{\"action\": \"plan\", \"steps\": [\"step1\", \"step2\", ...]}\n{\"action\": \"tool\", \"tool\": \"<name>\", \"arguments\": {...}}\n{\"action\": \"final\", \"answer\": \"your complete final answer\"}"


class AgentTask:
    def __init__(self, task_id: str, command: str, video_id: str | None = None, duration: float | None = None):
        self.id = task_id
        self.command = command
        self.video_id = video_id
        self.duration = duration
        self.status = "running"
        self.current_tool: str | None = None
        self.pending_action: dict | None = None
        self.plan: list[str] = []
        self.steps: list[dict] = []
        self.final_answer: str | None = None
        self.error: str | None = None
        self.iteration = 0
        self._stop = threading.Event()
        self._approval = threading.Event()
        self._approved = False
        self._lock = threading.Lock()

    def stop(self) -> None:
        self._stop.set()
        self._approval.set()

    def approve(self, approved: bool) -> None:
        self._approved = approved
        self._approval.set()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "command": self.command,
                "video_id": self.video_id,
                "status": self.status,
                "current_tool": self.current_tool,
                "pending_action": self.pending_action,
                "plan": list(self.plan),
                "steps": [dict(s) for s in self.steps],
                "final_answer": self.final_answer,
                "error": self.error,
                "iteration": self.iteration,
            }

    def _wait_approval_or_stop(self) -> bool:
        while not self._approval.wait(timeout=1.0):
            if self._stop.is_set():
                return False
        return not self._stop.is_set()

    def run(self) -> None:
        conversation: list[str] = [f"User task: {self.command}"]
        if self.video_id:
            video_note = f"video_id={self.video_id}"
            if self.duration is not None:
                video_note += f", duration_seconds={self.duration}"
            conversation.append(f"Context: current video is {video_note}.")
        video_ctx = None
        if self.video_id:
            video_ctx = f"video_id={self.video_id}"
            if self.duration is not None:
                video_ctx += f", duration_seconds={self.duration}"

        try:
            bad_replies = 0
            for step_index in range(1, MAX_STEPS + 1):
                if self._stop.is_set():
                    self.status = "stopped"
                    return
                self.iteration = step_index
                history = _trim_history(conversation)
                prompt = _build_system_prompt(video_ctx)
                prompt += "\n\n" + history + REPLY_RULE

                raw = hermes.complete(prompt, timeout=LLM_TIMEOUT) or ""
                action = parse_action(raw)

                if action is None:
                    bad_replies += 1
                    if bad_replies <= JSON_RETRY_LIMIT:
                        self.steps.append(
                            {
                                "kind": "error",
                                "tool": None,
                                "error": "Model reply was not a valid JSON action; requesting retry.",
                            }
                        )
                        conversation.append(
                            f"Reply parse failed: your previous reply was not one of the three allowed JSON objects. "
                            f"Your reply was: {raw[:500]}. Reply NOW again with exactly one JSON object."
                        )
                        continue
                    self.status = "completed"
                    self.final_answer = raw.strip() or "Task finished (model gave no structured answer)."
                    return

                act = action.get("action")
                if act == "plan":
                    steps = action.get("steps") or []
                    self.plan = [str(s) for s in steps]
                    self.steps.append({"kind": "plan", "steps": self.plan})
                    conversation.append(
                        "Assistant plan: " + json.dumps(self.plan, ensure_ascii=False)
                    )
                    continue

                if act == "final":
                    self.status = "completed"
                    self.final_answer = str(action.get("answer") or raw).strip()
                    return

                if act == "tool":
                    tool = action.get("tool")
                    arguments = action.get("arguments") or {}
                    if tool not in TOOL_DISPATCH:
                        msg = f"Unknown tool '{tool}'. Choose one of: {sorted(TOOL_DISPATCH.keys())}."
                        self.steps.append({"kind": "error", "tool": tool, "error": msg})
                        conversation.append(f"Tool error: {msg}")
                        continue

                    self.current_tool = tool
                    approved = True
                    if AGENT_TOOL_BY_NAME(tool).requires_approval:
                        self.status = "pending_approval"
                        self.pending_action = {"tool": tool, "arguments": arguments}
                        if not self._wait_approval_or_stop():
                            self.pending_action = None
                            self.status = "stopped"
                            return
                        approved = self._approved
                        self.pending_action = None
                        self.status = "running"
                        if not approved:
                            self.steps.append(
                                {"kind": "approval", "tool": tool, "arguments": arguments, "approved": False}
                            )
                            conversation.append(
                                f"User DENIED the request to run tool '{tool}' with {json.dumps(arguments)}. Adapt."
                            )
                            continue

                    try:
                        result = TOOL_DISPATCH[tool](arguments)
                        self.steps.append(
                            {
                                "kind": "tool",
                                "tool": tool,
                                "arguments": arguments,
                                "result": result,
                            }
                        )
                        conversation.append(
                            f"Tool call: {tool}({json.dumps(arguments)})\nTool result:\n{_truncate(result)}"
                        )
                    except Exception as e:
                        err = f"{type(e).__name__}: {e}"
                        self.steps.append({"kind": "error", "tool": tool, "error": err})
                        conversation.append(f"Tool call {tool} FAILED: {err}")
                    finally:
                        self.current_tool = None
                    continue

                self.status = "completed"
                self.final_answer = raw.strip()
                return

            self.status = "failed"
            self.error = f"Reached step limit ({MAX_STEPS}) without a final answer."
        except Exception as e:
            self.status = "failed"
            self.error = f"{type(e).__name__}: {e}"
        finally:
            self.current_tool = None


def AGENT_TOOL_BY_NAME(name: str):
    for t in AGENT_TOOLS:
        if t.name == name:
            return t
    return None


def _trim_history(conversation: list[str]) -> str:
    joined = "\n\n".join(conversation)
    lines = joined.splitlines()
    if len(lines) > HISTORY_MAX_LINES:
        lines = lines[-HISTORY_MAX_LINES:]
        return "...(earlier messages truncated)...\n" + "\n".join(lines)
    return joined


def parse_action(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.S)
    if m:
        raw = m.group(1).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group())
        except json.JSONDecodeError:
            return None
    if not isinstance(obj, dict):
        return None
    action = obj.get("action")
    if action not in ("plan", "tool", "final"):
        if obj.get("tool"):
            return {"action": "tool", "tool": obj["tool"], "arguments": obj.get("arguments", {})}
        return None
    return obj


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, AgentTask] = {}
        self._lock = threading.Lock()

    def start(self, command: str, video_id: str | None = None, duration: float | None = None) -> dict:
        task = AgentTask(f"task_{uuid.uuid4().hex[:8]}", command, video_id, duration)
        with self._lock:
            self._tasks[task.id] = task
        threading.Thread(target=task.run, daemon=True).start()
        return task.snapshot()

    def get(self, task_id: str) -> AgentTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def stop(self, task_id: str) -> None:
        task = self.get(task_id)
        if task:
            task.stop()

    def approve(self, task_id: str, approved: bool) -> None:
        task = self.get(task_id)
        if task:
            task.approve(approved)


manager = TaskManager()