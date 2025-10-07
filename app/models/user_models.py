from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import List

class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    created_at: datetime = datetime.utcnow()
    

class UserCreate(UserBase):
    password: str

class FollowerModel(BaseModel):
    followed: str | None  = None
    follower: str | None = None
    followed_on: datetime | None = datetime.utcnow()


class UserResponse(BaseModel):
    id: str
    status_code: str
    email: str


class UserLogin(UserCreate):
    email: EmailStr

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class ToeknData(BaseModel):
    email: EmailStr


class ResendOTP(BaseModel):
    email: EmailStr

class OTPCode(BaseModel):
    code: int

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
