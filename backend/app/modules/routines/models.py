import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.models import utcnow


class RoutineType(str, enum.Enum):
    daily = "daily"          # ทุกวัน — streak + จุด 7 วัน
    interval = "interval"    # ทุก N วัน (freq_days)
    as_needed = "as_needed"  # นับจากการใช้งาน (uses_count/threshold)


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[RoutineType] = mapped_column(Enum(RoutineType), index=True)

    # interval เท่านั้น: ทำทุกกี่วัน
    freq_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # as_needed เท่านั้น: ใช้ครบกี่ครั้งถึงรอบ
    threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    logs: Mapped[list["RoutineLog"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan"
    )


class RoutineLog(Base):
    __tablename__ = "routine_logs"
    __table_args__ = (UniqueConstraint("routine_id", "done_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("routines.id"), index=True)
    done_at: Mapped[date] = mapped_column(Date, index=True)
    # as_needed: ค่า uses_count ก่อนเช็คอิน — ใช้คืนค่าตอนยกเลิกเช็คอิน
    uses_before: Mapped[int | None] = mapped_column(Integer, nullable=True)

    routine: Mapped[Routine] = relationship(back_populates="logs")
