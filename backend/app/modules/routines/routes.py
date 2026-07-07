from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.modules.routines import service
from app.modules.routines.models import Routine, RoutineLog, RoutineType
from app.modules.routines.schemas import (
    CheckinIn,
    RoutineCreate,
    RoutineOut,
    RoutineUpdate,
    validate_type_fields,
)

router = APIRouter(prefix="/routines", tags=["routines"])


def to_out(routine: Routine) -> RoutineOut:
    ref = service.today()
    is_daily = routine.type == RoutineType.daily
    return RoutineOut(
        id=routine.id,
        name=routine.name,
        type=routine.type,
        freq_days=routine.freq_days,
        threshold=routine.threshold,
        uses_count=routine.uses_count,
        created_at=routine.created_at,
        done_today=service.done_on(routine, ref),
        due=service.is_due(routine, ref),
        last_done=service.last_done(routine),
        streak=service.streak(routine, ref) if is_daily else None,
        days_until_due=(
            service.days_until_due(routine, ref)
            if routine.type == RoutineType.interval
            else None
        ),
        last_7_days=service.last_7_days(routine, ref) if is_daily else None,
    )


def get_owned_routine(routine_id: int, db: Session, user: User) -> Routine:
    routine = db.get(Routine, routine_id)
    if routine is None or routine.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Routine not found")
    return routine


def resolve_checkin_date(value: date | None) -> date:
    ref = value or service.today()
    if ref > service.today():
        raise HTTPException(422, "เช็คอินล่วงหน้าไม่ได้")
    return ref


@router.get("", response_model=list[RoutineOut])
def list_routines(
    type_filter: RoutineType | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        select(Routine)
        .where(Routine.user_id == user.id)
        .options(selectinload(Routine.logs))
        .order_by(Routine.created_at)
    )
    if type_filter is not None:
        q = q.where(Routine.type == type_filter)
    return [to_out(r) for r in db.scalars(q).all()]


@router.post("", response_model=RoutineOut, status_code=status.HTTP_201_CREATED)
def create_routine(
    data: RoutineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = Routine(
        user_id=user.id,
        name=data.name,
        type=data.type,
        freq_days=data.freq_days,
        threshold=data.threshold,
    )
    # interval/as_needed: เลือกวันที่ทำล่าสุดตอนสร้างได้ — ไม่เลือก = เริ่มแบบถึงรอบ
    if data.last_done is not None and data.type != RoutineType.daily:
        routine.logs.append(RoutineLog(done_at=resolve_checkin_date(data.last_done)))
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return to_out(routine)


@router.get("/{routine_id}", response_model=RoutineOut)
def get_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return to_out(get_owned_routine(routine_id, db, user))


@router.patch("/{routine_id}", response_model=RoutineOut)
def update_routine(
    routine_id: int,
    data: RoutineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    changes = data.model_dump(exclude_unset=True)

    new_type = changes.get("type", routine.type)
    new_freq = changes.get("freq_days", routine.freq_days)
    new_threshold = changes.get("threshold", routine.threshold)
    try:
        validate_type_fields(new_type, new_freq, new_threshold)
    except ValueError as e:
        raise HTTPException(422, str(e))

    for field, value in changes.items():
        setattr(routine, field, value)

    # เปลี่ยนประเภทแล้วเคลียร์ field ที่ไม่เกี่ยว กัน data ค้าง
    if routine.type != RoutineType.interval:
        routine.freq_days = None
    if routine.type != RoutineType.as_needed:
        routine.threshold = None
        routine.uses_count = 0

    db.commit()
    db.refresh(routine)
    return to_out(routine)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    db.delete(routine)
    db.commit()


@router.post("/{routine_id}/checkin", response_model=RoutineOut)
def checkin(
    routine_id: int,
    data: CheckinIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    ref = resolve_checkin_date(data.date if data else None)

    if service.done_on(routine, ref):
        raise HTTPException(status.HTTP_409_CONFLICT, "เช็คอินวันนี้ไปแล้ว")

    log = RoutineLog(routine_id=routine.id, done_at=ref)
    if routine.type == RoutineType.as_needed:
        # เก็บตัวนับก่อนรีเซ็ต ไว้คืนค่าตอนยกเลิก
        log.uses_before = routine.uses_count
        routine.uses_count = 0
    db.add(log)
    db.commit()
    db.refresh(routine)
    return to_out(routine)


@router.delete("/{routine_id}/checkin", response_model=RoutineOut)
def cancel_checkin(
    routine_id: int,
    on_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    ref = on_date or service.today()

    log = db.scalar(
        select(RoutineLog).where(
            RoutineLog.routine_id == routine.id, RoutineLog.done_at == ref
        )
    )
    if log is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ยังไม่ได้เช็คอินวันนี้")

    if routine.type == RoutineType.as_needed and log.uses_before is not None:
        routine.uses_count = log.uses_before
    db.delete(log)
    db.commit()
    db.refresh(routine)
    return to_out(routine)


@router.post("/{routine_id}/uses", response_model=RoutineOut)
def add_use(
    routine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    if routine.type != RoutineType.as_needed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "นับการใช้งานได้เฉพาะ routine แบบ as_needed"
        )
    routine.uses_count += 1
    db.commit()
    db.refresh(routine)
    return to_out(routine)


@router.delete("/{routine_id}/uses", response_model=RoutineOut)
def remove_use(
    routine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routine = get_owned_routine(routine_id, db, user)
    if routine.type != RoutineType.as_needed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "นับการใช้งานได้เฉพาะ routine แบบ as_needed"
        )
    routine.uses_count = max(0, routine.uses_count - 1)
    db.commit()
    db.refresh(routine)
    return to_out(routine)
