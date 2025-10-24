from fastapi import APIRouter, status,  Path, Depends, HTTPException
from typing import Annotated
from app.utils.helper_functions import get_users
from app.utils.security import get_current_user
from app.config.db_config import db
from fastapi.encoders import jsonable_encoder
from app.models.user_models import FollowerModel, UserResponse
from bson import ObjectId
from datetime import datetime
from .user_route import get_user_byId, get_user_byEmail
from pymongo.errors import PyMongoError
from ..config.db_config import (
    user_collection,
    follower_collection
)


router = APIRouter(
    tags=["Users/Following Managements"]
)

@router.post("/follow/{user}", status_code=status.HTTP_200_OK)
def follow_user(
    user: Annotated[dict, ...] = Depends(get_user_byId),
    current_user: Annotated[str, ...] = Depends(get_current_user)):

    if user["email"] == current_user:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "You can't follow yourself"})

    if not user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "Can't follow unverified user"})
    
    # get the current user object.
    curr_user = user_collection.find_one( { "email": current_user} )

    already_followed = follower_collection.find_one({
        "followed": ObjectId(user["_id"]),
        "follower": curr_user["_id"]
    })
    if already_followed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": True, "message": "ALready followed this user."})

    model = FollowerModel()
    form_data = model.model_dump()
    form_data["followed"] = user["_id"]
    form_data["follower"] = curr_user["_id"]
    form_data["followed_on"] = datetime.now()
    
    save = follower_collection.insert_one(form_data)

    return {
        "success": True,
        "result": str(save.inserted_id)
    }

@router.delete("/unfollow/{user}", status_code=status.HTTP_200_OK)
def unfollow_user(
    user: Annotated[dict, ...] = Depends(get_user_byId),
    current_user: Annotated[str, ...] = Depends(get_current_user)
):
    try:
        curr_user_id = user_collection.find_one({"email": current_user})
        if not curr_user_id:
            raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": True, "message": "can't get current user id"})
        unfollow = follower_collection.find_one_and_delete({
            "follower": ObjectId(curr_user_id["_id"]),
            "followed": ObjectId(user["_id"])
        })
        if unfollow:
            return {
                "success": True,
                "message": f"{curr_user_id["username"]} unfollowed {user["username"]}"
            }
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "user dosn't exists."})
   
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"an error occured: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"Error: {e}"})

@router.get("/verified-followers", status_code=status.HTTP_200_OK)
def list_followers(current_user: Annotated[str, ...] = Depends(get_current_user)):
    try:
        user = get_user_byEmail(email=current_user)
        followers = list(follower_collection.find({'followed': user["_id"]}))
        if not followers:
            return [] or "No active follower"
        all_follower = list(get_user_byId(follower["follower"]) for follower in followers)
        encoded_followers = jsonable_encoder(all_follower, custom_encoder={ObjectId: str, datetime:str})
        for follower in encoded_followers:
            if not follower["is_verified"]:
                encoded_followers.remove(follower)
        return {
            "success": True,
            "followers": get_users(encoded_followers)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"can't collect active folowers: {e}"})


@router.get("/following", status_code=status.HTTP_200_OK)
def list_following(current_user:  Annotated[str, ...] = Depends(get_current_user)):
    try:
        user = get_user_byEmail(email=current_user)
        following = list(follower_collection.find({'follower': user["_id"]}))
        if not following:
            return []
        all_following = list(get_user_byId(follower["followed"]) for follower in following)
        encoded_following = jsonable_encoder(all_following, custom_encoder={ObjectId: str, datetime:str})
        for following in encoded_following:
            if not following["is_verified"]:
                encoded_following.remove(following)
        return {
            "success": True,
            "following": get_users(encoded_following)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"can't collect active following: {e}"})

