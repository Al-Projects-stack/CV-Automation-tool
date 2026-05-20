import json
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import CV, User

router = APIRouter(prefix="/cv")


# ── Validation helpers ──────────────────────────────────────────────────────

def _clamp(v: str, limit: int) -> str:
    return v.strip()[:limit]

def _url(v: str) -> str:
    v = v.strip()
    if v and not re.match(r'^https?://', v):
        raise ValueError("URL must start with https://")
    return v[:400]


# ── CV payload models ────────────────────────────────────────────────────────

class PersonalInfo(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

    @field_validator("name")
    @classmethod
    def name_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name is required")
        if len(v) > 120:
            raise ValueError("Name must be under 120 characters")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Invalid email address")
        return v[:200]

    @field_validator("phone", "location")
    @classmethod
    def short_text(cls, v: str) -> str:
        return _clamp(v, 100)

    @field_validator("linkedin", "github", "portfolio")
    @classmethod
    def valid_url(cls, v: str) -> str:
        return _url(v)


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    type: str = ""
    start: str = ""
    end: str = ""
    bullets: List[str] = []

    @field_validator("title", "company", "type", "start", "end")
    @classmethod
    def cap_fields(cls, v: str) -> str:
        return _clamp(v, 200)

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, v: list) -> list:
        if len(v) > 20:
            raise ValueError("Max 20 bullets per role")
        return [b.strip()[:400] for b in v if isinstance(b, str)]


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""
    status: str = ""

    @field_validator("institution", "degree", "field", "year", "status")
    @classmethod
    def cap_fields(cls, v: str) -> str:
        return _clamp(v, 200)


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    tech: List[str] = []
    link: str = ""

    @field_validator("name", "description")
    @classmethod
    def cap_fields(cls, v: str) -> str:
        return _clamp(v, 500)

    @field_validator("tech")
    @classmethod
    def cap_tech(cls, v: list) -> list:
        return [t.strip()[:80] for t in v if isinstance(t, str)][:20]

    @field_validator("link")
    @classmethod
    def valid_url(cls, v: str) -> str:
        return _url(v)


class SkillsData(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    tools: List[str] = []
    concepts: List[str] = []

    @field_validator("languages", "frameworks", "databases", "tools", "concepts")
    @classmethod
    def cap_skills(cls, v: list) -> list:
        return [s.strip()[:80] for s in v if isinstance(s, str)][:50]


class CVPayload(BaseModel):
    personal: PersonalInfo
    summary: dict = {}
    skills: SkillsData = SkillsData()
    experience: List[ExperienceEntry] = []
    education: List[EducationEntry] = []
    projects: List[ProjectEntry] = []

    @field_validator("experience")
    @classmethod
    def max_exp(cls, v: list) -> list:
        if len(v) > 20:
            raise ValueError("Max 20 experience entries")
        return v

    @field_validator("education")
    @classmethod
    def max_edu(cls, v: list) -> list:
        if len(v) > 10:
            raise ValueError("Max 10 education entries")
        return v

    @field_validator("projects")
    @classmethod
    def max_proj(cls, v: list) -> list:
        if len(v) > 20:
            raise ValueError("Max 20 projects")
        return v


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
def get_cv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.user_id == user.id).first()
    if not cv:
        return None
    return json.loads(cv.cv_data)


@router.put("")
def save_cv(
    payload: CVPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cv = db.query(CV).filter(CV.user_id == user.id).first()
    serialized = payload.model_dump_json()
    if cv:
        cv.cv_data = serialized
    else:
        cv = CV(user_id=user.id, cv_data=serialized)
        db.add(cv)
    db.commit()
    return {"ok": True}
