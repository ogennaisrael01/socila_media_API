from pydantic import BaseModel
from datetime import datetime

class Comment(BaseModel):
    post_id: str | None = None
    user_id: str | None = None
    message: str
    date_created: datetime = datetime.now()
    date_updated: datetime = datetime.now()


class UpdateForm(Comment):
    pass