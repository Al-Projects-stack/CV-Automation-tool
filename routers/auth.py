import os
from datetime import datetime, timedelta, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import jwt
from sqlalchemy.orm import Session

from database import get_db
from dependencies import ALGORITHM, SECRET_KEY, get_current_user
from models import User

router = APIRouter(prefix="/auth")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


@router.get("/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    user = db.query(User).filter(User.google_id == user_info["sub"]).first()
    if not user:
        user = User(
            google_id=user_info["sub"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    session_token = create_token(user.id)
    # Use an HTML page instead of RedirectResponse — some browsers drop
    # Set-Cookie headers on 307 redirects, breaking the auth flow.
    response = HTMLResponse(
        '<!DOCTYPE html><html><head>'
        '<script>window.location.replace("/")</script>'
        '</head><body></body></html>'
    )
    response.set_cookie(
        "auth_token",
        session_token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 3600,
        path="/",
    )
    return response


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.post("/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("auth_token")
    return response
