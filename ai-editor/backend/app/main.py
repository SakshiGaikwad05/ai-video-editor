from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import video, agent
from app.config import settings

app = FastAPI(title="AI Video Editor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router, prefix="/api/videos", tags=["videos"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ai/demo")
def ai_demo():
    return {
        "status": "ok",
        "mode": "demo",
        "message": "AI tool layer is connected. Use /api/agent/call from the UI.",
    }
