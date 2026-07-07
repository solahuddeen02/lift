from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.modules.dashboard.schemas import (
    DashboardOut,
    DayStat,
    RoutineSummary,
    TaskSummary,
)
from app.modules.journal.models import JournalEntry
from app.modules.routines import service
from app.modules.routines.models import Routine, RoutineType
from app.modules.routines.routes import to_out as routine_to_out
from app.modules.tasks.models import Task, TaskStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

PRIO_ORDER = {"high": 0, "medium": 1, "low": 2}


def task_group_order(task: Task, ref) -> int:
    """เลยกำหนด(0) → วันนี้(1) → พรุ่งนี้(2) → ถัดไป(3) → ไม่มีกำหนด(4)"""
    if task.due_date is None:
        return 4
    diff = (task.due_date.date() - ref).days
    if diff < 0:
        return 0
    if diff == 0:
        return 1
    if diff == 1:
        return 2
    return 3


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ref = service.today()

    # ---- routines: "ต้องทำวันนี้" = รายวัน + ที่ถึงรอบ + ที่ทำไปแล้ววันนี้ ----
    routines = db.scalars(
        select(Routine)
        .where(Routine.user_id == user.id)
        .options(selectinload(Routine.logs))
        .order_by(Routine.created_at)
    ).all()
    today_routines = [
        r
        for r in routines
        if r.type == RoutineType.daily or service.is_due(r, ref) or service.done_on(r, ref)
    ]
    done_today = sum(1 for r in today_routines if service.done_on(r, ref))
    best_streak = max(
        (service.streak(r, ref) for r in routines if r.type == RoutineType.daily),
        default=0,
    )

    # ---- กราฟ 7 วัน: วันเก่า total = จำนวนรายวัน + งานเป็นรอบที่ทำจริงวันนั้น ----
    # (ย้อนอดีตรู้ไม่ได้ว่างานเป็นรอบ "ถึงรอบ" วันไหน เลยนับเฉพาะที่ทำจริง)
    entries = db.scalars(
        select(JournalEntry).where(
            JournalEntry.user_id == user.id,
            JournalEntry.entry_date >= ref - timedelta(days=6),
        )
    ).all()
    mood_by_day = {e.entry_date: e.mood for e in entries}

    daily_count = sum(1 for r in routines if r.type == RoutineType.daily)
    week: list[DayStat] = []
    for offset in range(6, 0, -1):
        day = ref - timedelta(days=offset)
        done_daily = sum(
            1 for r in routines if r.type == RoutineType.daily and service.done_on(r, day)
        )
        done_cycle = sum(
            1 for r in routines if r.type != RoutineType.daily and service.done_on(r, day)
        )
        week.append(
            DayStat(
                date=day,
                done=done_daily + done_cycle,
                total=daily_count + done_cycle,
                mood=mood_by_day.get(day),
            )
        )
    # วันนี้ใช้ตัวเลขเดียวกับวงแหวน (รู้ due จริง)
    week.append(
        DayStat(date=ref, done=done_today, total=len(today_routines), mood=mood_by_day.get(ref))
    )

    # ---- tasks: done/total + top 3 ของที่ค้าง เรียงกลุ่มเวลา + priority ----
    tasks = db.scalars(select(Task).where(Task.user_id == user.id)).all()
    done_tasks = sum(1 for t in tasks if t.status == TaskStatus.done)
    pending = sorted(
        (t for t in tasks if t.status != TaskStatus.done),
        key=lambda t: (task_group_order(t, ref), PRIO_ORDER[t.priority.value]),
    )

    latest_journal = db.scalar(
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id)
        .order_by(JournalEntry.entry_date.desc())
        .limit(1)
    )

    return DashboardOut(
        routines_today=RoutineSummary(
            done=done_today,
            total=len(today_routines),
            items=[routine_to_out(r) for r in today_routines],
        ),
        tasks=TaskSummary(done=done_tasks, total=len(tasks), top=pending[:3]),
        week=week,
        best_streak=best_streak,
        latest_journal=latest_journal,
    )
