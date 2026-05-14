from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str = "completed"


class Learning(BaseModel):
    id: str
    content: str
    category: str = "tech"
    keywords: List[str] = []
    source: Optional[str] = None


class DailyLogCreate(BaseModel):
    date: Optional[str] = None  # 日期，格式 YYYY-MM-DD
    tasks: List[Task] = []
    learnings: List[Learning] = []
    attachments: List[str] = []
    tags: List[str] = []


class DailyLogResponse(BaseModel):
    id: str
    date: datetime
    tasks: List[Task] = []
    learnings: List[Learning] = []
    attachments: List[str] = []
    tags: List[str] = []
    ai_summary: Optional[str] = None


class LogUpdate(BaseModel):
    tasks: Optional[List[Task]] = None
    learnings: Optional[List[Learning]] = None
    attachments: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    ai_summary: Optional[str] = None