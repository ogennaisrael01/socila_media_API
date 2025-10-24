from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from typing import Annotated
from app.models import profile_models
from app.utils.security import get_current_user
from fastapi.encoders import jsonable_encoder
from pymongo.collection import ReturnDocument
from bson import ObjectId
from pymongo.errors import PyMongoError
from datetime import datetime
from app.utils.helper_functions import get_profile_data
from .following_route import list_followers, list_following
import logging
from ..config.db_config import (
    user_collection,
    profile_collection 
)
router = APIRouter(
    tags=["Profile Management"]
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.put("/profile/update", status_code=status.HTTP_200_OK)
def profile_update(
        update_form: Annotated[profile_models.ProfileUpdate, Body(...)] = None,
        email: str = Depends(get_current_user)
    ):
    if not update_form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Please provide the data to update"})
    encoded_form = update_form.model_dump(exclude_unset=True)
    encoded_form["updated_at"] = datetime.now()
    user = user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"success": False, "message": "You don't have access to perform this action"})
    try:
        update_user_profile = profile_collection.find_one_and_update({"user_id": str(user["_id"])}, {"$set": encoded_form}, return_document=ReturnDocument.AFTER)
        if update_user_profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "No profile is attached to this user"})
    except PyMongoError as e:
        logging.error(f"Error occured while updating user profile, check your internet connectivity: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error occured while updating user info, check your internet connectivity: {e}"})
    except Exception as e:
        logging.error(f"Updating user profile raised an Exception: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message":f"Updating user profile raised an exception: {e}"})
    
    data_to_return = jsonable_encoder(update_user_profile, custom_encoder={ObjectId:str, datetime: str})
    return data_to_return


@router.get("/profile/{user_id}", status_code=status.HTTP_200_OK)
def view_profile(
    user_id: str |None = None,
    q: Annotated[str | None, Query(title="retrieve user by their username")] = None,
    current_user : str = Depends(get_current_user)
):

    user = user_collection.find_one({
        "$or": [
            {"username": {"$regex": f"^{q}$", "$options": "i"}},
            {"_id": ObjectId(user_id)}
        ]
    })

    if not user:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    
    profile = profile_collection.find_one({
        "user_id": str(user["_id"])

    })

    if not profile:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    profile_data = get_profile_data(user=user, profile=profile)
    encoded_data = jsonable_encoder(profile_data, custom_encoder={ObjectId: str})

    followers = list_followers(current_user=current_user)
    following = list_following(current_user=current_user)
    try:
        encoded_data["followers"] = len(followers) if followers else []
        encoded_data["following"] = len(following) if following else []
    except Exception:
        pass
    return {
        "success": True,
        "profile": encoded_data
    }


@router.delete("/delete/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: str = Depends(get_current_user)):
    try:
        user = user_collection.find_one_and_delete({
            "email": current_user
        })
        if user:
            profile_collection.find_one_and_delete({
                "user_id": str(user["_id"])
            })
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "User not found"})
    except PyMongoError as e:
        logging.error(f"Error occured while deleting user account, check your internet connectivity: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error occured while deleting user account, check your internet connectivity: {e}"})
    except Exception as e:
        logging.error(f"Deleting user account raised an Exception: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message":f"Deleting user account raised an exception: {e}"})
    return {"success": True, "message": f"{current_user} account and associated profile deleted successfully"}
