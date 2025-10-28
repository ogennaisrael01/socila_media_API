from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import List
from bson import ObjectId

class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_verified: bool | None = False
    created_at: datetime = datetime.utcnow()
    

class UserCreate(UserBase):
    password: str

class FollowerModel(BaseModel):
    followed: str | None  = None
    follower: str | None = None
    followed_on: datetime | None = datetime.utcnow()


class UserResponse(BaseModel):
    success: bool
    result: UserBase

class UserLogin(UserCreate):
    email: EmailStr

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class PasswordResetForm(BaseModel):
    email: str

class PasswordConfirm(BaseModel):
    new_password: str
    confirm_password: str


class ToeknData(BaseModel):
    email: EmailStr

class UserProfile(BaseModel):
    bio: str | None = None
    profile_picture: HttpUrl | None = None
    location: str | None = None
    updated_at: datetime | None = datetime.now()
    user_id: str | None = None
    

class UserProfileResponse(BaseModel):
    id: str
    user: UserBase
    bio: str | None = None   
    profile_picture: str | None = None
    location: str | None = None
    updated_at: datetime = datetime.now()


class UploadImage(BaseModel):
    image_url: str 