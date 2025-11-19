from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import create_document, db
import os

app = FastAPI(title="Mykonos Made in Italy API", version="1.0.0")

# CORS - allow frontend preview and general use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WaitlistIn(BaseModel):
    email: EmailStr
    source: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/test")
async def test_db():
    has_db = db is not None
    name = os.getenv("DATABASE_NAME") if has_db else None
    return {"database_connected": has_db, "database_name": name}


@app.post("/waitlist")
async def join_waitlist(payload: WaitlistIn, request: Request):
    try:
        # Basic dedupe check: do not insert duplicates (best-effort)
        # Using find_one requires a direct call; keep this lightweight
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")

        existing = db["waitlist"].find_one({"email": payload.email.lower()})
        if existing:
            return {"ok": True, "message": "You are already on the waitlist."}

        meta = {
            "email": payload.email.lower(),
            "source": payload.source,
            "ip": request.client.host if request and request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        _id = create_document("waitlist", meta)
        return {"ok": True, "id": _id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
