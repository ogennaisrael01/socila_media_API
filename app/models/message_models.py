from pydantic import BaseModel
from datetime import datetime
class Messaging(BaseModel):
    sender: str | None = None
    reciever: str | None = None
    message: str
    created_at: datetime | None = datetime.now()
    updated_at: datetime | None = datetime.now()

class MessageUpdate(BaseModel):
    message: str