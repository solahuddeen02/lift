from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.modules.journal.models import JournalEntry
from app.modules.journal.schemas import JournalOut, JournalUpsert
from app.modules.routines.service import today

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("", response_model=list[JournalOut])
def list_entries(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id)
        .order_by(JournalEntry.entry_date.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(q).all()


@router.post("", response_model=JournalOut)
def upsert_entry(
    data: JournalUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """1 entry ต่อวัน — มีของวันนั้นแล้ว = แก้ทับ (mood + text)"""
    ref = data.entry_date or today()
    # เผื่อ timezone ล้ำหน้า UTC (ไทย = UTC+7 วันที่ local ขึ้นก่อน) — เกิน +1 วันถือว่าผิด
    if ref > today() + timedelta(days=1):
        raise HTTPException(422, "บันทึกล่วงหน้าไม่ได้")

    entry = db.scalar(
        select(JournalEntry).where(
            JournalEntry.user_id == user.id, JournalEntry.entry_date == ref
        )
    )
    if entry is None:
        entry = JournalEntry(user_id=user.id, entry_date=ref)
        db.add(entry)
    entry.mood = data.mood
    entry.text = data.text

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = db.get(JournalEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    db.delete(entry)
    db.commit()
