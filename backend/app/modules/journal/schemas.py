from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Mood = Literal["😄", "😌", "😐", "😔", "😤"]


class JournalUpsert(BaseModel):
    mood: Mood
    text: str = Field(min_length=1)
    # client ส่งวันที่ท้องถิ่นของตัวเองมาได้ — ไม่ส่ง = วันนี้ตามเวลา server (UTC)
    entry_date: date | None = None


class JournalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_date: date
    mood: str
    text: str
    created_at: datetime
    updated_at: datetime
