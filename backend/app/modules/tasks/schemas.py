from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.tasks.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    note: str = ""
    priority: TaskPriority = TaskPriority.medium
    due_date: datetime | None = None
    category_id: int | None = None


class TaskUpdate(BaseModel):
    """Partial update — ส่งเฉพาะ field ที่จะแก้"""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    note: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    category_id: int | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    note: str
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    category_id: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
