import json
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import CV, User

router = APIRouter(prefix="/cv")


@router.get("")
def get_cv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.user_id == user.id).first()
    if not cv:
        return None
    return json.loads(cv.cv_data)


@router.put("")
def save_cv(
    cv_data: Any = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(cv_data, dict):
        raise HTTPException(status_code=422, detail="CV data must be a JSON object")
    cv = db.query(CV).filter(CV.user_id == user.id).first()
    serialized = json.dumps(cv_data)
    if cv:
        cv.cv_data = serialized
    else:
        cv = CV(user_id=user.id, cv_data=serialized)
        db.add(cv)
    db.commit()
    return {"ok": True}
