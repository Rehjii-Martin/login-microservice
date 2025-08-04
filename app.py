import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db, seed_demo_user
from auth import router as auth_router

app = FastAPI(title="Login Management Service", version="1.0.0")

# ---- OPTIONAL ----
CORS_ORIGINS = os.getenv("CORS_ORIGINS")
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def startup():
    init_db()
    if os.getenv("SEED_DEMO_USER", "true").lower() == "true":
        seed_demo_user()  # user: M.Koike / pass0000

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)

# `python app.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
