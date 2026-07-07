from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(pattern=HEX_COLOR)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    created_at: datetime
