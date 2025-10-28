from ..config.db_config import notification_collection
from ..models.notification_models import Notification
from fastapi import status, HTTPException


def notification_create(sender, reciever, notification_type):
    notif_model = Notification(sender=sender, reciever=reciever, notification_type=notification_type)
    convert_to_dict = notif_model.model_dump()
    try:
        save_notif = notification_collection.insert_one(convert_to_dict)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'success': False, "message": f"unable to send notif: {e}"})
    
    return {
        "success": True
    }
