import os
import uuid
import datetime as dt
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import cast

from models import User, RefreshToken, get_sess

# ---------------- Config ----------------
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")          # set in env for real deployments
JWT_ALG = "HS256"
ACCESS_TTL_MIN = int(os.getenv("ACCESS_TTL_MIN", "15"))    # spec: 15 min
REFRESH_TTL_DAYS = int(os.getenv("REFRESH_TTL_DAYS", "7")) # spec: 7 days

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------- Schemas ----------------
class LoginIn(BaseModel):
    user_name: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None  # only on /login

class RefreshIn(BaseModel):
    refresh_token: str

class LogoutIn(BaseModel):
    refresh_token: str

# ---------------- Helpers ----------------

def make_access_token(user: User) -> str:
    assert user.id is not None, "User must have an id to build JWT"
    now = dt.datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "username": user.user_name,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=ACCESS_TTL_MIN)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token if isinstance(token, str) else token.decode("utf-8")

def store_refresh_token(sess: Session, user_id: int) -> str:
    token = uuid.uuid4().hex
    sess.add(RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=dt.datetime.utcnow() + dt.timedelta(days=REFRESH_TTL_DAYS),
        revoked=False
    ))
    sess.commit()
    return token

def invalid_user():
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Invalid user"})

# ---------------- Routes ----------------
@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, sess: Session = Depends(get_sess)):
    from models import pwd
    user = sess.exec(select(User).where(User.user_name == data.user_name)).first()
    if not user or not pwd.verify(data.password, user.password_hash):
        return invalid_user()

    assert user.id is not None, "User missing id"   
    user_id = cast(int, user.id)                         

    return TokenOut(
        access_token=make_access_token(user),
        refresh_token=store_refresh_token(sess, user_id),
    )

@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, sess: Session = Depends(get_sess)):
    rt = sess.exec(select(RefreshToken).where(RefreshToken.token == data.refresh_token)).first()
    if not rt or rt.revoked or rt.expires_at < dt.datetime.utcnow():
        return invalid_user()
    user = sess.get(User, rt.user_id)
    if not user:
        return invalid_user()
    return TokenOut(access_token=make_access_token(user))

@router.post("/logout")
def logout(data: LogoutIn, sess: Session = Depends(get_sess)):
    rt = sess.exec(select(RefreshToken).where(RefreshToken.token == data.refresh_token)).first()
    if rt and not rt.revoked:
        rt.revoked = True
        sess.add(rt)
        sess.commit()
    return {"message": "successfully logout"}
