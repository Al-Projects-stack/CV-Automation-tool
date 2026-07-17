import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.datastructures import MutableHeaders
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from database import Base, engine, get_db
from dependencies import get_current_user
from models import CV, User
from routers.auth import router as auth_router
from routers.cv import router as cv_router
from services.claude_service import tailor_cv
from services.document_service import generate_documents

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent


class SecurityHeadersMiddleware:
    """Pure ASGI middleware — intercepts response.start so it never wraps or
    buffers the response body, which avoids the BaseHTTPMiddleware bug that
    drops Set-Cookie headers on redirect responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            await send(message)

        await self.app(scope, receive, send_with_security_headers)


app = FastAPI(title="CV Automation API", version="2.0.0")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-in-production"),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your domain when deployed
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(cv_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    index_path = BASE_DIR / "static" / "index.html"
    if not index_path.exists():
        return HTMLResponse(status_code=404, content="index.html not found")
    return FileResponse(str(index_path))


@app.get("/health")
def health():
    return {"status": "ok"}


class GenerateRequest(BaseModel):
    job_description: str = Field(min_length=50, max_length=15000)


@app.post("/generate")
def generate(
    request: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty")

    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    cv_record = db.query(CV).filter(CV.user_id == user.id).first()
    if not cv_record:
        raise HTTPException(
            status_code=400,
            detail="No CV found for your account. Please build your CV first.",
        )

    master_cv = json.loads(cv_record.cv_data)

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
        filename=zip_path.name,
    )
