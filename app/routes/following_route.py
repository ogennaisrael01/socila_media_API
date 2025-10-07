from fastapi import APIRouter, status,  Path, Depends, HTTPException
from typing import Annotated
from app.utils.security import get_current_user
from app.config.db_config import db
from fastapi.encoders import jsonable_encoder
from app.models.user_models import FollowerModel
from bson import ObjectId
from datetime import datetime


user_collection = db.get_collection("social_media_users")
follower_collection = db.get_collection("social_media_followers")

router = APIRouter(
    tags=["Users/Following Managements"]
)

@router.post("/follow/{user_id}", status_code=status.HTTP_200_OK)
def follow_user(
    user_id: Annotated[str | None, Path(title="An id to get the user to follow")],
    current_user: Annotated[str, ...] = Depends(get_current_user)):

    user = user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(detail="Invalid", status_code=status.HTTP_404_NOT_FOUND)
    if user["email"] == current_user:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="You are not permitted to follow your self")

    if not user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can't follow unverified user")
    
    # get the current user object.
    curr_user = user_collection.find_one( { "email": current_user} )

    already_followed = follower_collection.find_one({
        "follower": curr_user["_id"]
    })
    if already_followed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="already followed this user.")
    # Follow the user if the provided the data are valid

    model = FollowerModel()
    encoded_data = jsonable_encoder(model)
    encoded_data["followed"] = user["_id"]
    encoded_data["follower"] = curr_user["_id"]
    
    follow = follower_collection.insert_one(encoded_data)

    return {
        "success": True,
        "id": str(follow.inserted_id),
        "message": f"{curr_user["username"]} followed {user["username"]}"
    }

@router.delete("/unfollow/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: Annotated[str | None, Path()],
    current_user: Annotated[str, ...] = Depends(get_current_user)
):

    curr_user_obj = user_collection.find_one({"email": current_user})
    user = follower_collection.find_one_and_delete(
        {
            "followed": ObjectId(user_id),
            "follower": curr_user_obj["_id"]
        }
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You don't have access to perform ths action")


@router.get("/verified-followers", status_code=status.HTTP_200_OK)
def list_followers(current_user: Annotated[str, ...] = Depends(get_current_user)):

    curr_user_obj = user_collection.find_one( {"email": current_user})
    followers = list(follower_collection.find( {"followed": curr_user_obj["_id"]} ))

    encode_data = jsonable_encoder(followers, custom_encoder={ObjectId: str, datetime: str})

    return encode_data


@router.get("/following", status_code=status.HTTP_200_OK)
def list_following(current_user:  Annotated[str, ...] = Depends(get_current_user)):
    curr_user_obj = user_collection.find_one( {"email": current_user})
    following = list(follower_collection.find( { "follower": curr_user_obj["_id"]}))

    encode_data = jsonable_encoder(following, custom_encoder={ObjectId: str, datetime: str})

    return encode_data