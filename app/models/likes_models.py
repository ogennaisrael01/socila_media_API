from pydantic import BaseModel
from datetime import   datetime
from bson import ObjectId

class Like(BaseModel):
    post_id: str
    user_id: str
    created_at: datetime | None = datetime.now()

    class config:
        arbitrary_types_allowed=True
