import logging
import os

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User

logger = logging.getLogger("uvicorn.error")

ALGORITHM = "HS256"
_DEV_SECRET = "dev-secret-change-in-production"

# A Secure-cookie deployment signals production. Shared by main.py (CORS,
# session key) and auth.py (cookie flags) so the signal lives in one place.
IS_PRODUCTION = os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes")

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set in production "
            "(COOKIE_SECURE is enabled). Refusing to sign tokens with a public default."
        )
    logger.warning("SECRET_KEY not set — using an insecure development default.")
    SECRET_KEY = _DEV_SECRET


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
