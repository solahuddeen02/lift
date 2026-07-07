from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.database import Base
from app.core.models import utcnow


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(7))  # hex เช่น #818cf8

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# preset 4 หมวดตาม design — seed ให้ user ใหม่ตอน register แล้วแก้/ลบเองได้
DEFAULT_CATEGORIES = [
    ("งาน", "#818cf8"),
    ("ส่วนตัว", "#34d399"),
    ("เรียน", "#fbbf24"),
    ("บ้าน", "#f472b6"),
]


def seed_default_categories(db: Session, user_id: int) -> None:
    for name, color in DEFAULT_CATEGORIES:
        db.add(Category(user_id=user_id, name=name, color=color))
