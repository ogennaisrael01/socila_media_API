from fastapi import APIRouter, status, HTTPException, Depends , Query, Form
from typing import Annotated
from ..utils import security, cloudinary_utils
from ..models.post__models import PostCreateResponse, PostCreate, PostUpdate
from ..config.db_config import (
    post_collection,
    user_collection,
    follower_collection
)
from bson import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError
from fastapi.encoders import jsonable_encoder
from .user_route import get_user_byEmail, get_user_byId
from pymongo import ReturnDocument


router = APIRouter(
    tags=["Post Management"]
)


@router.post("/posts", status_code=status.HTTP_201_CREATED, response_model=PostCreateResponse)
def create_post(
    form: PostCreate,
    current_user:str = Depends(security.get_current_user),
):
    form_dump = form.model_dump()
    user = user_collection.find_one({"email": current_user})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "User Not Found"})
    
    user_id = user["_id"]
    form_dump.update({"user_id": ObjectId(user_id), "created_at": datetime.now()})
    if form_dump["image_url"]:
        cloudinary_image = cloudinary_utils.upload_image(form_dump.get("image_url"))
    else:
        pass
    try:
        post = post_collection.insert_one(form_dump)
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": True, "message": f"Error occured while connecting to db. check your internet connectivity: {e}"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail={"success": False, "message": f"An Error Occures while inserting post {e}"})

    return {
        "success": True,
        "id": str(post.inserted_id),
        "message": "Post Created Successful",
        "post_image": cloudinary_image.get("secure_url") if form_dump["image_url"] else None
    }
        
@router.get("/posts", status_code=status.HTTP_200_OK)
def list_post(*, page: Annotated[int, Query()] = 1,
            size: Annotated[int, Query()] = 10,
            q: Annotated[str | None, Query] = None,
            ):
    offset = (page - 1) * size

    if q:
        posts = list(post_collection.find({
             "$or": [
            {"title": {"$regex": f"^{q}$", "$options": "i"}},
            {"content": {"$regex": f"^{q}$", "$options": "i"}}
        ],
            "is_deleted": False,

        }).skip(offset).limit(size).sort("created_at", -1))

        if not posts:
            return [] or "No post matching your search"

    else:
        posts = list(post_collection.find({
            "is_deleted": False
        }
        ).limit(size).skip(offset).sort("created_at", -1))

        encoded_posts = jsonable_encoder(posts, custom_encoder={ObjectId: str, datetime: str})

        return {
            "success": True,
            "posts": encoded_posts
        }


@router.get("/post/following", status_code=status.HTTP_200_OK)
def following_post(
    page: Annotated[int | None, Query] = 1,
    size: Annotated[int| None, Query()] = 10,
    q: Annotated[str| None, Query] = None,
    current_user: str = Depends(security.get_current_user)
):
    offset = (page - 1) * size
    user = get_user_byEmail(email=current_user)
    followers = list(follower_collection.find({'follower': user["_id"]}))
    if not followers:
        return [] or "No active follower"
    all_followers = list(get_user_byId(follower["followed"]) for follower in followers)
    encoded_followers = jsonable_encoder(all_followers, custom_encoder={ObjectId: str, datetime:str})
    posts = list(post_collection.find({
        "user_id": {"$in": [ObjectId(follower["_id"]) for follower in encoded_followers]},
        "is_deleted": False}).limit(size).skip(offset).sort("created_at", -1))
    if not posts:
        return [] or "No Posts"
    
    encoded_posts = jsonable_encoder(posts, custom_encoder={ObjectId: str, datetime: str})
    return {
        "success": True,
        "posts": encoded_posts
    }

@router.get("/feed", status_code=status.HTTP_200_OK)
def feed(
    current_user: str = Depends(security.get_current_user),
    page: Annotated[int | None, Query()] = 1,
    size: Annotated[int | None, Query()] = 10
):
    offset = (page -1) * size
    user = get_user_byEmail(email=current_user)
    followers = list(follower_collection.find({'follower': user["_id"]}))
    if not followers:
        return [] or "No active follower"
    all_following = list(get_user_byId(follower["followed"]) for follower in followers)
    follower_ids = [ObjectId(follower["_id"]) for follower in all_following]
    follower_ids.append(ObjectId(user["_id"]))
    posts = list(post_collection.find({
        "user_id": {
            "$in": follower_ids
        },
        "is_deleted": False
    }).limit(size).skip(offset).sort("created_at", -1))
    encoded_posts = jsonable_encoder(posts, custom_encoder={ObjectId: str, datetime: str})
    return {
        "success": True,
        "posts": encoded_posts
    }


@router.get("/my-posts")
def my_posts( current_user: str = Depends(security.get_current_user),
    page: Annotated[int | None, Query()] = 1,
    size: Annotated[int | None, Query()] = 10):

    offset = (page - 1) * size

    user = get_user_byEmail(email=current_user)
    posts = list(post_collection.find({"user_id": user["_id"], "is_deleted": False}).skip(offset).limit(size).sort("created_at", -1))
    if not posts:
        return [] or "No posts Available"
    
    encoded_posts = jsonable_encoder(posts, custom_encoder={ObjectId: str, datetime: str})
    return {
        "success": True,
        "posts": encoded_posts
    }

@router.get("/p/{post}")
def get_post_byId(post: str, current_user:str = Depends(security.get_current_user)):
    try:
        posts = post_collection.find_one({
            "_id": ObjectId(post),
            "is_deleted": False
        })
        if posts:
            return posts
        # else:
        #     return [] or "No Posts"
    except  PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detaial={"success": False, "message": f"Error fetching posts! {e}"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"Error occured while retrieving posts"})
    

@router.put("/update")
def update_post(post_id: str, update_form: PostUpdate,  current_user: str = Depends(security.get_current_user)):
    dump_form = update_form.model_dump(exclude_unset=True)
    post = get_post_byId(post=post_id, current_user=current_user)
    user = get_user_byEmail(email=current_user)
    if post["user_id"] != user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= {'success': False, "message": "You are not permitted to perform this action"})
    try:
        dump_form["updated_at"] = datetime.now()
        if dump_form["image_url"]:
            upload_clodinary = cloudinary_utils.upload_image(dump_form["image_url"])
        else:
            pass
        updated_post = post_collection.find_one_and_update({"_id": ObjectId(post_id), "is_deleted": False}, {"$set": dump_form}, return_document=ReturnDocument.AFTER)
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success":True, "message": f"Error occureed while updating post: {e}"})

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False, "message": f"error {e}"})   
    encode_updated_post = jsonable_encoder(updated_post, custom_encoder={ObjectId:str, datetime:str})
    return {
        "success": True,
        "updated_post": encode_updated_post,
        "image_url": upload_clodinary.get("secure_url") if dump_form["image_url"] else None
    }


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: str, current_user: str = Depends(security.get_current_user)):
    user = get_user_byEmail(email=current_user)
    try:
        post_collection.find_one_and_update({"user_id": user["_id"], "_id": ObjectId(post_id)}, {"$set": {"is_deleted": True, "deleted_at": datetime.now()}}) 
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"error deleting post: {e}"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error deleting post {e}"})
    return {
        "success": True
    }

@router.get("/users/{user_id}/posts")
def get_users_post(user_id: str, current_user:str = Depends(security.get_current_user)):
    user = get_user_byId(user=user_id, current_user=current_user)
    posts = list(post_collection.find({"user_id": user["_id"]}).sort("created_at", -1))
    if not posts:
        return [] or "No available posts"
    
    encode_posts = jsonable_encoder(posts, custom_encoder={ObjectId:str, datetime:str})
    return {
        "success": True,
        "posts": encode_posts
    }

@router.post("/upload")
def upload_to_clodinary(image_url: Annotated[str, Form()]):
    uploader = cloudinary_utils.upload_image(image_url)
    return uploader
    