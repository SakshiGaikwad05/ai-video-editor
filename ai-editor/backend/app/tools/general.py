import re
import subprocess
from pathlib import Path

import httpx

from app.config import settings
from app.models.video import AgentTool


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = settings.project_root / p
    return p.resolve()


def _safe_text(content: str, limit: int = 6000) -> str:
    content = (content or "").strip()
    if len(content) > limit:
        content = content[:limit] + "\n...[truncated]"
    return content


def list_files(path: str = ".") -> dict:
    p = _resolve(path)
    if not p.exists():
        raise ValueError(f"path not found: {path}")
    if p.is_file():
        return {
            "target": str(p),
            "entry": {"name": p.name, "is_dir": False, "size": p.stat().st_size},
        }
    entries = []
    for child in sorted(p.iterdir()):
        try:
            entries.append(
                {
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "size": child.stat().st_size if child.is_file() else None,
                }
            )
        except OSError:
            continue
    return {"path": str(p), "count": len(entries), "entries": entries}


def read_file(path: str) -> dict:
    p = _resolve(path)
    if not p.is_file():
        raise ValueError(f"not a file or missing: {path}")
    size = p.stat().st_size
    if size > 512_000:
        raise ValueError(f"file too large to read ({size} bytes); use list_files instead")
    text = p.read_text(encoding="utf-8", errors="replace")
    return {"path": str(p), "size": size, "content": _safe_text(text)}


def run_shell(command: str) -> dict:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(settings.project_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": _safe_text(proc.stdout, 4000),
        "stderr": _safe_text(proc.stderr, 4000),
    }


_TAG_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.I | re.S)


def browse_url(url: str) -> dict:
    try:
        r = httpx.get(
            url,
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
    except Exception as e:
        raise ValueError(f"request failed: {e}")

    html = r.text
    title = None
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()

    headings = []
    for tag in ("h1", "h2", "h3"):
        for hm in re.finditer(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.I | re.S):
            txt = re.sub(r"<[^>]+>", "", hm.group(1))
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                headings.append({"tag": tag, "text": txt})

    body = _TAG_RE.sub(" ", html)
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "url": str(r.url),
        "status_code": r.status_code,
        "title": title,
        "headings": headings[:20],
        "text_preview": text[:1500],
    }


GENERAL_AGENT_TOOLS = [
    AgentTool(
        name="list_files",
        description="List the contents of a directory (or metadata of a single file). Used to explore the project.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or project-relative path (default: project root)",
                }
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "count": {"type": "integer"},
                "entries": {"type": "array"},
            },
        },
    ),
    AgentTool(
        name="read_file",
        description="Read the text contents of a file (limit 512 KB). Use for source/config/readme files.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Absolute or project-relative file path"}},
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        },
    ),
    AgentTool(
        name="run_shell",
        description="Run a shell command inside the project directory. Returns stdout/stderr/returncode.",
        parameters={
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Shell command to execute"}},
            "required": ["command"],
        },
        output_schema={
            "type": "object",
            "properties": {"returncode": {"type": "integer"}, "stdout": {"type": "string"}, "stderr": {"type": "string"}},
        },
        requires_approval=True,
    ),
    AgentTool(
        name="browse_url",
        description="Fetch a web page and return its URL, title, headings (h1-h3) and a text preview.",
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Full http(s) URL to fetch"}},
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "title": {"type": ["string", "null"]},
                "headings": {"type": "array"},
            },
        },
    ),
]

GENERAL_DISPATCH = {
    "list_files": lambda args: list_files(args.get("path", ".")),
    "read_file": lambda args: read_file(args["path"]),
    "run_shell": lambda args: run_shell(args["command"]),
    "browse_url": lambda args: browse_url(args["url"]),
}