"""Logic คำนวณสถานะ routine จาก log — pure functions ทดสอบง่าย"""

from datetime import date, timedelta

from app.core.models import utcnow
from app.modules.routines.models import Routine, RoutineType


def today() -> date:
    return utcnow().date()


def last_done(routine: Routine) -> date | None:
    if not routine.logs:
        return None
    return max(log.done_at for log in routine.logs)


def done_on(routine: Routine, day: date) -> bool:
    return any(log.done_at == day for log in routine.logs)


def streak(routine: Routine, ref: date) -> int:
    """นับวันติดต่อกันย้อนหลัง — ถ้าวันนี้ยังไม่ทำแต่เมื่อวานทำ streak ยังไม่ขาด"""
    days = {log.done_at for log in routine.logs}
    start = ref if ref in days else ref - timedelta(days=1)
    count = 0
    while start in days:
        count += 1
        start -= timedelta(days=1)
    return count


def last_7_days(routine: Routine, ref: date) -> list[bool]:
    """จุด 7 วัน: index 0 = 6 วันก่อน, index 6 = วันนี้"""
    days = {log.done_at for log in routine.logs}
    return [(ref - timedelta(days=offset)) in days for offset in range(6, -1, -1)]


def days_until_due(routine: Routine, ref: date) -> int | None:
    """interval: เหลืออีกกี่วันถึงรอบ (ติดลบ = เลยกำหนด), None = ไม่เคยทำ (ถึงรอบทันที)"""
    done = last_done(routine)
    if done is None or routine.freq_days is None:
        return None
    return (done + timedelta(days=routine.freq_days) - ref).days


def is_due(routine: Routine, ref: date) -> bool:
    if routine.type == RoutineType.daily:
        return not done_on(routine, ref)
    if routine.type == RoutineType.interval:
        remaining = days_until_due(routine, ref)
        return remaining is None or remaining <= 0
    # as_needed
    return routine.threshold is not None and routine.uses_count >= routine.threshold
