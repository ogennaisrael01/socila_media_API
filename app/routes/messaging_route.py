from fastapi import APIRouter, status, HTTPException, Depends
from ..utils.security import get_current_user
from ..routes.user_route import get_user_byId, get_user_byEmail
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from ..models.message_models import Messaging, MessageUpdate
from ..config.db_config import message_collection, user_collection
from pymongo.errors  import PyMongoError
import logging
from datetime import datetime
from pymongo import ReturnDocument
from ..utils.helper_functions import get_users

logging.basicConfig(level=logging.basicConfig)
logger = logging.getLogger(__name__)
router = APIRouter(tags=["Messaging Managements"])


@router.post("/message", status_code=status.HTTP_201_CREATED)
def send_message(user_id: str, message_form: Messaging, current_user:str = Depends(get_current_user)):
    reciever = get_user_byId(user=user_id, current_user=current_user)
    sender = get_user_byEmail(email=current_user)
    to_dict = message_form.model_dump()
    if reciever and reciever["is_verified"]:
        to_dict["sender"] = sender["_id"]
        to_dict["reciever"] = reciever["_id"]
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"success": False, "message": "cant message unverified users"})

    try:
        save_message = message_collection.insert_one(to_dict)
    except PyMongoError as e :
        logging.error(f"{e}")
        raise HTTPException (status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "success":False,
            "message": f"Error: {e}"
        })
    except Exception as e:
        logging.error(f"{e}")
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail={
            "success": False,
            "message": f"Error: {e}"
        })
    
    return{
        "success": True,
        "message": "message sent",
        "message_id": str(save_message.inserted_id)
    }
    
@router.get("/chats", status_code=status.HTTP_200_OK)
def chat_between_users(user_id: str, current_user: str = Depends(get_current_user)):
    sender = get_user_byEmail(email=current_user)
    reciever = get_user_byId(user=user_id, current_user=current_user)
    # get chats between two users by their ids

    chats = list(message_collection.find({
                                "$or": [
                                    {
                                        "$and": [
                                            {"sender": sender["_id"]},
                                            {"reciever": reciever["_id"]}
                                        ]
                                    },
                                    {
                                        "$and": [
                                            {"sender": reciever["_id"]},
                                            {"reciever": sender["_id"]}
                                        ]
                                    }
                                ]
    }))
    if not chats:
        return [] or "Empty chats"

    encode_chats = jsonable_encoder(chats, custom_encoder={ObjectId: str, datetime:str})
    return {
        "success": True,
        "chats": encode_chats
    }

@router.get("/chats/{chat_id}")
def retrieve_chat(chat_id: str, current_user: str = Depends(get_current_user)):
    try:
        chat = message_collection.find_one({"_id": ObjectId(chat_id)})
        if chat:
            return chat
        else:
            return "No chat with this  given ID"
    except PyMongoError as  e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detial={
            "success": False,
            "message": f"Error occured: {e}"
        })

@router.put("/user/{user_id}/chat/{chat_id}/update", status_code=status.HTTP_200_OK)
def update_chat(user_id: str, chat_id: str, update_form: MessageUpdate,  current_user: str = Depends(get_current_user)):
    sender = get_user_byEmail(email=current_user)
    reciever = get_user_byId(user=user_id)
    to_dict = update_form.model_dump(exclude_unset=True)
    chats = message_collection.find_one({
                    "_id": ObjectId(chat_id),
                    "sender": sender["_id"],
                    "$or": [
                         {
                            "$and": [
                                {"sender": sender["_id"]},
                                {"reciever": reciever["_id"]}
                            ]
                        },
                        {
                            "$and": [
                                {"sender": reciever["_id"]},
                                {"reciever": sender["_id"]}
                            ]
                        }
                    ]
    })
    if not chats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
            "success": False,
            "message": "Not Found"
        })
    
    merge_data = to_dict | chats 
    merge_data["message"] = to_dict["message"]
    merge_data["is_updated"] = True
    merge_data['updated-at'] = datetime.now()
    try: 
        update_chat = message_collection.find_one_and_update({
            "_id": merge_data["_id"]},
            {"$set": merge_data},
            return_document=ReturnDocument.AFTER)
        
        encode_chats = jsonable_encoder(update_chat, custom_encoder={ObjectId: str, datetime: str})

    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "success": True,
            "message": "Check your internet connection: Error occured: {e}"
        })
    return  {
        "success": True,
        "updated_chats": encode_chats
    }

@router.delete("/user/{user_id}/chat/{chat_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(user_id: str, chat_id: str, current_user: str = Depends(get_current_user)):
    sender = get_user_byEmail(email=current_user)
    reciever = get_user_byId(user=user_id)
    chats = message_collection.find_one({
                    "_id": ObjectId(chat_id),
                    "sender": sender["_id"],
                    "$or": [
                         {
                            "$and": [
                                {"sender": sender["_id"]},
                                {"reciever": reciever["_id"]}
                            ]
                        },
                        {
                            "$and": [
                                {"sender": reciever["_id"]},
                                {"reciever": sender["_id"]}
                            ]
                        }
                    ]
    })
    if not chats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
            "success": False,
            "message": "Not Found"
        })
    try: 
        message_collection.find_one_and_delete({
            "_id": chats["_id"]
        })
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "success": False,
            "message": "unable to delete message"
        })

@router.get("/users/chats", status_code=status.HTTP_200_OK)
def get_users(current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    chats = message_collection.find({
        "$or": [
            {"sender": user["_id"]},
            {"reciever": user["_id"]}
        ]
    })
    for chat in chats:
        list_chats = list(user_collection.find({
                    "$or": [
                        {"_id": chat["sender"]},
                       { "_id": chat["reciever"]}
                    ]
                 
        }))
        if not list_chats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
                "success": False, 
                "message": "Chats not listed"
            })

        for user in list_chats:
            encode_data = jsonable_encoder(user, custom_encoder={ObjectId: str, datetime:str})
            print (encode_data)
            # users = get_users(encode_data)
            # print(users)