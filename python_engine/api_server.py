
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from main import analyze_video
from reframe import generate_reframe

ROOT = Path(__file__).resolve().parent.parent
COMMUNICATION = ROOT / "communication"
COMMUNICATION.mkdir(exist_ok=True)

app = FastAPI(title="SafeFrame AI Local Engine")
job_lock = Lock()

FORMATS = {"9:16", "1:1", "4:5", "16:9"}


class AnalyzeRequest(BaseModel):
    video_path: str
    format: str = "9:16"
    smoothness: int = Field(default=65, ge=0, le=100)


@app.get("/health")
def health():
    return {"status": "online", "engine": "SafeFrame AI"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    video = Path(request.video_path).expanduser().resolve()

    if not video.is_file():
        raise HTTPException(400, "Video file not found")

    if video.suffix.lower() not in {
        ".mp4", ".mov", ".avi", ".mkv"
    }:
        raise HTTPException(400, "Unsupported video format")

    if request.format not in FORMATS:
        raise HTTPException(400, "Unsupported output format")

    if not job_lock.acquire(blocking=False):
        raise HTTPException(409, "Another analysis is running")

    try:
        output_json = COMMUNICATION / "output.json"
        reframe_json = COMMUNICATION / "reframe.json"

        alpha = 0.95 - (request.smoothness / 100) * 0.90

        analyze_video(
            str(video),
            str(output_json),
            sample_every=15,
            alpha=alpha
        )

        generate_reframe(
            str(output_json),
            str(reframe_json),
            request.format
        )

        return {
            "status": "success",
            "message": "Analysis completed",
            "analysis_file": str(output_json),
            "reframe_file": str(reframe_json),
            "video_path": str(video),
            "format": request.format
        }

    except Exception as exc:
        raise HTTPException(500, str(exc))

    finally:
        job_lock.release()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765
    )
