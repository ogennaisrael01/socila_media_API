from datetime import datetime
from pydantic import BaseModel, Field


class PostBase(BaseModel):
    title: str | None = Field(max_length=200)
    content: str | None = Field(max_length=1000)
    image_url: str | None = None
    user_id: str | None = Field(description="Lookup for who made that post", default=None)
    is_deleted: bool = Field(default=False)
    created_at: datetime | None = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)


class PostCreate(PostBase):
    pass


class PostCreateResponse(BaseModel):
    success: bool
    id: str
    message: str

class PostUpdate(PostBase):
    pass