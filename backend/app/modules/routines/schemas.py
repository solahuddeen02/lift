import datetime as dt
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.modules.routines.models import RoutineType


def validate_type_fields(type_: RoutineType, freq_days: int | None, threshold: int | None):
    if type_ == RoutineType.interval and freq_days is None:
        raise ValueError("interval routine ต้องระบุ freq_days")
    if type_ == RoutineType.as_needed and threshold is None:
        raise ValueError("as_needed routine ต้องระบุ threshold")


class RoutineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: RoutineType
    freq_days: int | None = Field(default=None, ge=1)
    threshold: int | None = Field(default=None, ge=1)
    # interval/as_needed: วันที่ทำล่าสุด — ไม่เลือก = เริ่มแบบถึงรอบ
    last_done: date | None = None

    @model_validator(mode="after")
    def check_type_fields(self):
        validate_type_fields(self.type, self.freq_days, self.threshold)
        # เคลียร์ field ที่ไม่เกี่ยวกับประเภทตัวเอง กัน data ค้าง
        if self.type != RoutineType.interval:
            self.freq_days = None
        if self.type != RoutineType.as_needed:
            self.threshold = None
        return self


class RoutineUpdate(BaseModel):
    """Partial update — เปลี่ยนความถี่ข้ามประเภทได้ (validate หลัง merge ใน route)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: RoutineType | None = None
    freq_days: int | None = Field(default=None, ge=1)
    threshold: int | None = Field(default=None, ge=1)


class CheckinIn(BaseModel):
    # ชื่อ field ต้องเป็น "date" ตาม API — ใช้ dt.date กัน field ชื่อเดียวกัน shadow type
    date: dt.date | None = None  # ไม่ส่ง = วันนี้


class RoutineOut(BaseModel):
    id: int
    name: str
    type: RoutineType
    freq_days: int | None
    threshold: int | None
    uses_count: int
    created_at: datetime

    # computed จาก log
    done_today: bool
    due: bool
    last_done: date | None
    streak: int | None            # daily เท่านั้น
    days_until_due: int | None    # interval เท่านั้น (ติดลบ = เลยกำหนด)
    last_7_days: list[bool] | None  # daily เท่านั้น
