import os
import datetime as dt
from pathlib import Path
from typing import Optional, Generator

from sqlmodel import SQLModel, Field, Session, create_engine, select
from passlib.context import CryptContext

# ---------------- Config ----------------
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
DB_URL = os.getenv("DB_URL", f"sqlite:///{(DATA_DIR / 'auth.db').as_posix()}")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- DB Engine ----------------
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})

def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_sess() -> Generator[Session, None, None]:
    with Session(engine) as s:
        yield s

# ---------------- Tables ----------------
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str = Field(index=True, unique=True)
    password_hash: str

class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    token: str = Field(index=True, unique=True)
    expires_at: dt.datetime
    revoked: bool = Field(default=False)

# ---------------- Utilities ----------------
def seed_demo_user(user_name: str = "M.Koike", password: str = "pass0000") -> None:
    """Create a demo user if not exists (dev/demo only)."""
    with Session(engine) as s:
        exists = s.exec(select(User).where(User.user_name == user_name)).first()
        if not exists:
            s.add(User(user_name=user_name, password_hash=pwd.hash(password)))
            s.commit()
