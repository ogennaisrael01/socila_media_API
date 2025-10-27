from fastapi import APIRouter, status, HTTPException, Depends
from .post_route import get_post_byId, get_user_byEmail
from app.utils.security import get_current_user
from app.models.likes_models import Like
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
import datetime
from app.config.db_config import post_collection, likes_collection

router = APIRouter(tags=["Likes"])


@router.post("/like", status_code=status.HTTP_201_CREATED)
def like_post(post_id: str, current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    try:
        if likes_collection.find_one({"user_id": str(user["_id"]), "post_id": post_id}):
            raise HTTPException(status_code=status.HTTP_302_FOUND, detail={'success': True, "message": "You alerady liked this post"})
        like_form = Like(user_id=str(user["_id"]), post_id=post_id)
        save_to_dict = jsonable_encoder(like_form)
        add_like = likes_collection.insert_one(save_to_dict)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"Error while inserting like: {e}"})

    return {
        "success": True,
        "id": str(add_like.inserted_id)
    }

@router.delete("/unlike", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(post_id: str, current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    if not likes_collection.find_one({"user_id": str(user["_id"]), "post_id": post_id}):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'success': False, "message": "You dont have access to perform this action"})

    unlike = likes_collection.find_one_and_delete({"user_id": str(user["_id"]), "post_id": post_id})
    return jsonable_encoder(unlike, custom_encoder={ObjectId: str, datetime: str})

