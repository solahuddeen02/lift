from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import utcnow

# mood picker 5 อันตาม design
MOODS = ["😄", "😌", "😐", "😔", "😤"]


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    # 1 entry ต่อวันต่อ user — เขียนซ้ำ = แก้ของวันนั้น (upsert ใน route)
    __table_args__ = (UniqueConstraint("user_id", "entry_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    entry_date: Mapped[date] = mapped_column(Date, index=True)
    mood: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
