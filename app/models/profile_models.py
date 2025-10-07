from pydantic import BaseModel, HttpUrl
from app.models.user_models import UserProfile

class ProfileUpdate(UserProfile):
    pass