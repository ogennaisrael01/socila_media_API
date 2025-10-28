from fastapi import APIRouter, status, HTTPException, Depends
from ..utils.security import get_current_user
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from ..config.db_config import notification_collection
from ..routes.user_route import get_user_byEmail
from datetime import datetime
router = APIRouter(tags=["Notifications"])


@router.get("/notifications", status_code=status.HTTP_200_OK)
def get_notifications(current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    print(str(user["_id"]))
    try:
        notif = list(notification_collection.find({"reciever": str(user['_id'])}))

        if  not  notif:
            return [] or "No notificatiosn"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": f"Error: {e}"})
    encode_response = jsonable_encoder(notif, custom_encoder={ObjectId: str, datetime: str})
    return {
        "success": True,
        "Notifications": encode_response
    }