from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User, utcnow
from app.modules.categories.models import Category
from app.modules.tasks.models import Task, TaskPriority, TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_owned_task(task_id: int, db: Session, user: User) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


def check_owned_category(category_id: int | None, db: Session, user: User) -> None:
    if category_id is None:
        return
    category = db.get(Category, category_id)
    if category is None or category.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Task).where(Task.user_id == user.id)
    if status_filter is not None:
        q = q.where(Task.status == status_filter)
    if priority is not None:
        q = q.where(Task.priority == priority)
    if category_id is not None:
        q = q.where(Task.category_id == category_id)
    q = q.order_by(Task.due_date.is_(None), Task.due_date, Task.created_at.desc())
    return db.scalars(q).all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_owned_category(data.category_id, db, user)
    task = Task(user_id=user.id, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_owned_task(task_id, db, user)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = get_owned_task(task_id, db, user)
    changes = data.model_dump(exclude_unset=True)

    if "category_id" in changes:
        check_owned_category(changes["category_id"], db, user)

    for field, value in changes.items():
        setattr(task, field, value)

    # sync completed_at กับ status
    if "status" in changes:
        task.completed_at = utcnow() if task.status == TaskStatus.done else None

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = get_owned_task(task_id, db, user)
    db.delete(task)
    db.commit()
