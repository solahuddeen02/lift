from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryOut, CategoryUpdate
from app.modules.tasks.models import Task

router = APIRouter(prefix="/categories", tags=["categories"])


def get_owned_category(category_id: int, db: Session, user: User) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Category).where(Category.user_id == user.id).order_by(Category.created_at)
    return db.scalars(q).all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    category = Category(user_id=user.id, **data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    category = get_owned_category(category_id, db, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    category = get_owned_category(category_id, db, user)
    # ปลด task ที่ใช้หมวดนี้ให้เป็น "ไม่ระบุ" ก่อนลบ (ไม่พึ่ง ON DELETE ของ DB)
    db.execute(
        update(Task)
        .where(Task.category_id == category.id)
        .values(category_id=None)
    )
    db.delete(category)
    db.commit()
