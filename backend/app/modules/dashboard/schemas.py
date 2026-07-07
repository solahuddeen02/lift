from datetime import date

from pydantic import BaseModel

from app.modules.journal.schemas import JournalOut
from app.modules.routines.schemas import RoutineOut
from app.modules.tasks.schemas import TaskOut


class DayStat(BaseModel):
    date: date
    done: int
    total: int
    mood: str | None  # จาก journal ของวันนั้น


class RoutineSummary(BaseModel):
    done: int
    total: int
    items: list[RoutineOut]  # routine ที่ "ต้องทำวันนี้" — ใช้ render ลิสต์เช็คอินหน้าหลัก


class TaskSummary(BaseModel):
    done: int
    total: int
    top: list[TaskOut]  # 3 อันแรกของที่ค้าง เรียงกลุ่มเวลา + priority


class DashboardOut(BaseModel):
    routines_today: RoutineSummary
    tasks: TaskSummary
    week: list[DayStat]  # 7 ช่อง index 6 = วันนี้
    best_streak: int
    latest_journal: JournalOut | None
