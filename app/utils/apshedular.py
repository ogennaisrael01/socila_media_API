from datetime import datetime
import logging
from ..routes.user_route import get_user_byId
from ..config.db_config import notification_collection
from ..models.notification_models import NotificationType


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def starter():
    logging.info(f"{[str(datetime.now())]}: Shedular job running......")


def send_notif():
    notifications = list(notification_collection.find())
    message = ""
    for notification in notifications:
        match notification:
            case {"notification_type": NotificationType.LIKE}:
                reciever = get_user_byId(user=notification["reciever"])
                sender = get_user_byId(user= notification["sender"])
                message = f"{sender["username"]} liked one of your post"
                logging.info(message)
                save_message = notification_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"message": message, "sent_at": datetime.now()}}
                )
            case {"notification_type": NotificationType.FOLLOW}:
                reciever = get_user_byId(user=notification["reciever"])
                sender = get_user_byId(user= notification["sender"])
                message = f"{sender["username"]} started following you"
                logging.info(message)
                save_message = notification_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"message": message, "sent_at": datetime.now()}}
                )
            case {"notification_type": NotificationType.COMMENT}:
                reciever = get_user_byId(user=notification["reciever"])
                sender = get_user_byId(user= notification["sender"])
                message = f"{sender["username"]} commented on your post"
                logging.info(message)
                save_message = notification_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"message": message, "sent_at": datetime.now()}}
                )

            case {"notification_type": NotificationType.UNFOLLOW}:
                reciever = get_user_byId(user=notification["reciever"])
                sender = get_user_byId(user= notification["sender"])
                message = f"{sender["username"]} unfollowed you"
                logging.info(message)
                save_message = notification_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"message": message, "sent_at": datetime.now()}}
                )

            case {"notification_type": NotificationType.REPLY}:
                reciever = get_user_byId(user=notification["reciever"])
                sender = get_user_byId(user= notification["sender"])
                message = f"{sender["username"]} replied to your comment"
                logging.info(message)
                save_message = notification_collection.update_one(
                    {"_id": notification["_id"]},
                    {"$set": {"message": message, "sent_at": datetime.now()}}
                )
            case _:
                logging.warning(f"Unknown notification type: {notification['notification_type']}")
    logging.info(f"{[str(datetime.now())]}: Notification Shedular job completed......")


            