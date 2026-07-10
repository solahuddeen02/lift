from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.categories.models import seed_default_categories

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if not settings.REGISTRATION_ENABLED:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ปิดรับสมัครสมาชิกอยู่")

    exists = db.scalar(select(User).where(User.email == data.email))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    db.flush()  # ให้ได้ user.id ก่อน seed
    seed_default_categories(db, user.id)  # preset 4 หมวดตาม design แก้/ลบเองได้
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
