from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

# Each Pydantic model corresponds to a Mongo collection named as class name lowercased

class User(BaseModel):
    name: str = Field(..., description="Display name or nickname")
    email: EmailStr = Field(..., description="Unique email")
    vibe: Optional[str] = Field(None, description="Current emotional vibe or state")
    interests: List[str] = Field(default_factory=list, description="Interest tags")
    streak: int = Field(0, ge=0, description="Consecutive daily activity streak")
    xp: int = Field(0, ge=0, description="Experience points")
    companion: Optional[str] = Field(None, description="Selected companion name")
    companion_visible: bool = Field(True, description="Whether companion is shown")
    last_active: Optional[datetime] = None

class Mood(BaseModel):
    user_id: str
    mood: str
    note: Optional[str] = None
    timestamp: Optional[datetime] = None

class Journal(BaseModel):
    user_id: str
    text: str
    mood_tag: Optional[str] = None
    sentiment: Optional[Literal['positive', 'neutral', 'negative']] = None
    created_at: Optional[datetime] = None

class MindfulnessSession(BaseModel):
    user_id: str
    activity_type: Literal['breathing', 'meditation', 'sleep', 'relaxation', 'mini']
    duration_seconds: Optional[int] = Field(default=0, ge=0)
    completed_at: Optional[datetime] = None

class PeerWallPost(BaseModel):
    post_text: str
    mood_tag: Optional[str] = None
    likes: int = 0
    timestamp: Optional[datetime] = None

class Badge(BaseModel):
    user_id: str
    badge_name: str
    earned_at: Optional[datetime] = None

class MentraBotLog(BaseModel):
    user_id: Optional[str] = None
    message: str
    response: str
    timestamp: Optional[datetime] = None

class Appointment(BaseModel):
    user_id: str
    doctor_name: str
    date: datetime
    status: Literal['requested', 'confirmed', 'completed', 'cancelled'] = 'requested'

class GameRecord(BaseModel):
    user_id: str
    game_name: Literal['tic-tac-toe', 'sudoku', 'daily-puzzle']
    score: int = 0
    date: Optional[datetime] = None
