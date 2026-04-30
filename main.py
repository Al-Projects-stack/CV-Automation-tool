import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.claude_service import tailor_cv
from services.document_service import generate_documents

BASE_DIR = Path(__file__).resolve().parent
MASTER_CV_PATH = BASE_DIR / "master_cv.json"

app = FastAPI(title="CV Automation API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the frontend index.html at root"""
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            status_code=404,
            content=f"❌ index.html not found at {index_path}"
        )
    return FileResponse(str(index_path))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this when you have a deployed frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_master_cv() -> dict:
    if not MASTER_CV_PATH.exists():
        raise FileNotFoundError("master_cv.json not found")
    with open(MASTER_CV_PATH, "r") as f:
        return json.load(f)


class GenerateRequest(BaseModel):
    job_description: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(request: GenerateRequest):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    try:
        master_cv = load_master_cv()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        tailored = tailor_cv(request.job_description, master_cv)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")

    try:
        zip_path = generate_documents(tailored, master_cv)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation error: {str(e)}")

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_path.name
    )
