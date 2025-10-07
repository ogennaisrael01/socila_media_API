from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from typing import Annotated
from app.models import profile_models
from app.utils.security import get_current_user
from app.config.db_config import db
from fastapi.encoders import jsonable_encoder
from pymongo.collection import ReturnDocument
from bson import ObjectId
from datetime import datetime
from app.utils.helper_functions import get_profile_data
from .following_route import list_followers, list_following

router = APIRouter(
    tags=["Profile Management"]
)

user_collection = db.get_collection("social_media_users")
profile_collection = db.get_collection("social_media_user_profiles")


@router.put("/profile/{id}/update", status_code=status.HTTP_200_OK)
def profile_update(
        id: str,
        update_form: Annotated[profile_models.ProfileUpdate, Body(...)] = None,
        email: str = Depends(get_current_user)
    ):

    convert_to_dict = update_form.model_dump(exclude_unset=True)

    user = user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user is associated with this username")
    
    convert_to_dict["updated_at"] = datetime.now()
    try:
        profile =profile_collection.find_one_and_update({
            "_id": ObjectId(id),
            "user_id": user["_id"]
        },
        {
            "$set": convert_to_dict
        },
        return_document=ReturnDocument.AFTER)

    except Exception as e:
        print(e)
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An error occured")
    
    encoded_profile = jsonable_encoder(profile, custom_encoder={ObjectId: str})

    return {
        "success": True,
        "id": str(encoded_profile["_id"])
    }


@router.get("/get-profile", status_code=status.HTTP_200_OK)
def view_profile(
    q: Annotated[str | None, Query(title="retrieve user by their username")] = None,
    current_user : str = Depends(get_current_user)
):

    user = user_collection.find_one({
        "$or": [
            {"username": {"$regex": f"^{q}$", "$options": "i"}},
            {"email":  current_user}
        ]
    })

    if not user:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    
    profile = profile_collection.find_one({
        "user_id": user["_id"]

    })

    if not profile:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    profile_data = get_profile_data(user=user, profile=profile)
    encoded_data = jsonable_encoder(profile_data, custom_encoder={ObjectId: str})

    followers = list_followers(current_user=current_user)
    following = list_following(current_user=current_user)

    encoded_data["followers"] = len(followers)
    encoded_data["following"] = len(following)

    return encoded_data



@router.delete("/delete/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: str = Depends(get_current_user)):

    user = user_collection.find_one_and_delete({
        "email": current_user
    })

    if not user:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No content")
    
    profile_collection.find_one_and_delete({"user_id": user["_id"]})
