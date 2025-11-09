import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import (
    User, Mood, Journal, MindfulnessSession, PeerWallPost,
    Badge, MentraBotLog, Appointment, GameRecord
)

app = FastAPI(title="MentraCare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "MentraCare API", "status": "ok"}


# Simple health and schema endpoints
@app.get("/test")
def test_database():
    status = {
        "backend": "running",
        "database": "disconnected",
        "collections": []
    }
    try:
        if db is not None:
            status["database"] = "connected"
            status["collections"] = db.list_collection_names()
    except Exception as e:
        status["database"] = f"error: {str(e)[:120]}"
    return status


# Request models for simple interactions
class MoodRequest(BaseModel):
    user_id: str
    mood: str
    note: Optional[str] = None


class JournalRequest(BaseModel):
    user_id: str
    text: str
    mood_tag: Optional[str] = None


# Core endpoints
@app.post("/moods")
async def create_mood(req: MoodRequest):
    mood_doc = Mood(user_id=req.user_id, mood=req.mood, note=req.note, timestamp=datetime.now(timezone.utc))
    mood_id = create_document("mood", mood_doc)

    # Award XP (simple rule)
    try:
        db["user"].update_one({"_id": req.user_id}, {"$inc": {"xp": 10}, "$set": {"last_active": datetime.now(timezone.utc)}}, upsert=False)
    except Exception:
        pass

    return {"id": mood_id, "xp_awarded": 10}


@app.get("/moods/{user_id}")
async def list_moods(user_id: str, limit: int = 30):
    docs = get_documents("mood", {"user_id": user_id}, limit=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


@app.post("/journals")
async def create_journal(req: JournalRequest):
    # naive sentiment rule
    text = req.text.lower()
    sentiment = "neutral"
    if any(w in text for w in ["great", "good", "grateful", "happy", "calm"]):
        sentiment = "positive"
    if any(w in text for w in ["sad", "bad", "anxious", "angry", "stressed", "worried"]):
        sentiment = "negative"
    journal_doc = Journal(user_id=req.user_id, text=req.text, mood_tag=req.mood_tag, sentiment=sentiment, created_at=datetime.now(timezone.utc))
    journal_id = create_document("journal", journal_doc)
    try:
        db["user"].update_one({"_id": req.user_id}, {"$inc": {"xp": 15}}, upsert=False)
    except Exception:
        pass
    return {"id": journal_id, "sentiment": sentiment}


@app.get("/journals/{user_id}")
async def list_journals(user_id: str, limit: int = 20):
    docs = get_documents("journal", {"user_id": user_id}, limit=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


@app.post("/mindfulness/sessions")
async def log_session(session: MindfulnessSession):
    session.completed_at = session.completed_at or datetime.now(timezone.utc)
    sid = create_document("mindfulnesssession", session)
    try:
        db["user"].update_one({"_id": session.user_id}, {"$inc": {"xp": 10}}, upsert=False)
    except Exception:
        pass
    return {"id": sid}


@app.post("/peer-wall")
async def create_post(post: PeerWallPost):
    post.timestamp = post.timestamp or datetime.now(timezone.utc)
    pid = create_document("peerwallpost", post)
    return {"id": pid}


@app.get("/peer-wall")
async def list_posts(limit: int = 50):
    docs = get_documents("peerwallpost", {}, limit=limit)
    docs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


@app.post("/games")
async def save_game(record: GameRecord):
    record.date = record.date or datetime.now(timezone.utc)
    gid = create_document("gamerecord", record)
    try:
        db["user"].update_one({"_id": record.user_id}, {"$inc": {"xp": 5}}, upsert=False)
    except Exception:
        pass
    return {"id": gid}


@app.post("/badges")
async def add_badge(badge: Badge):
    badge.earned_at = badge.earned_at or datetime.now(timezone.utc)
    bid = create_document("badge", badge)
    return {"id": bid}


@app.post("/appointments")
async def create_appointment(appt: Appointment):
    appt_id = create_document("appointment", appt)
    return {"id": appt_id}


@app.post("/mentrabot")
async def mentrabot(msg: MentraBotLog):
    # very compact supportive response
    message = (msg.message or "").lower()
    response = "I'm here for you. Let's take a slow breath together. You're not alone."
    if any(k in message for k in ["stressed", "overwhelmed", "anxious", "panic"]):
        response = "It sounds heavy. Try a 4-7-8 breath with me now. If it persists, I can show emergency help."
    if any(k in message for k in ["sad", "down", "tired", "low"]):
        response = "I hear you. Be gentle with yourself today—one small step is enough. Want a short mindfulness break?"
    if any(k in message for k in ["hurt", "harm", "sos", "suicide", "kill"]):
        response = "Your safety matters. Please reach out to someone you trust. Tap SOS—help is available right now."

    log = MentraBotLog(user_id=msg.user_id, message=msg.message, response=response, timestamp=datetime.now(timezone.utc))
    _ = create_document("mentrabotlog", log)
    return {"response": response}
