"""Гостевая книга на FastAPI."""
import json
import logging
import os
import time
import uuid
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import Base, Message, SessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("guestbook")

APP_VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(title="Guestbook", version=APP_VERSION)


class MessageIn(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=1000)


class MessageOut(BaseModel):
    id: int
    author: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
            ensure_ascii=False,
        )
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "up"}
    except SQLAlchemyError as exc:
        logger.error(json.dumps({"event": "db_check_failed", "error": str(exc)}))
        return JSONResponse(status_code=503, content={"status": "error", "database": "down"})


@app.get("/version")
def version():
    return {"version": APP_VERSION}


@app.post("/messages", response_model=MessageOut, status_code=201)
def create_message(payload: MessageIn):
    db = SessionLocal()
    try:
        message = Message(author=payload.author, text=payload.text)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    finally:
        db.close()


@app.get("/messages", response_model=list[MessageOut])
def list_messages():
    db = SessionLocal()
    try:
        return db.query(Message).order_by(Message.id.desc()).all()
    finally:
        db.close()
