from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class NotificationType(str, Enum):
    LIKE = "like"
    COMMENT = "Comment"
    FOLLOW= "Follow"
    UNFOLLOW = "Unfollow"
    REPLY ="Reply"

    
class Notification(BaseModel):
    sender: str 
    reciever: str
    notification_type: str 
    created_at: datetime = datetime.now()