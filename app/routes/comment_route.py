from fastapi import status, Depends, HTTPException, APIRouter
from bson import ObjectId
from ..models.comment_models import Comment, UpdateForm
from typing import Annotated
from ..utils.security import get_current_user
from ..routes.post_route import get_post_byId, get_user_byEmail
from ..config.db_config import comment_collection
from fastapi.encoders import jsonable_encoder
from pymongo.errors import PyMongoError
from datetime import datetime
from pymongo import ReturnDocument

router = APIRouter(tags=["Comment Management"])


@router.post("/comment", status_code=status.HTTP_200_OK)
async def add_comment(post_id: str, comment_form: Comment, current_user: str = Depends(get_current_user)):
    try:
        user = get_user_byEmail(email=current_user)
        post = get_post_byId(post=post_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"Error: {e}"})
    convert_to_dict = comment_form.model_dump()
    convert_to_dict.update({
        "post_id": post["_id"],
        "user_id": user["_id"]
    })
    
    add_comment = comment_collection.insert_one(convert_to_dict)
    return {
        "success": True,
        "id": str(add_comment.inserted_id)
    }
    

@router.get("/comment")
async def get_comment(post_id: str, current_user:str = Depends(get_current_user)):
    """"Current all comment associated to the particular provided post"""
    post = get_post_byId(post=post_id)
    try:
        comments = list(comment_collection.find({"post_id": post["_id"]}).sort("date_created", -1))
        encoded_comment = jsonable_encoder(comments, custom_encoder={ObjectId:str, datetime:str})
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error occured while fetching documents: {e}"})
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': True, "message": f"Unknown error occured: {e}"})

    return {
        "succcess": True,
        "commencts": encoded_comment
    }

@router.get("/user/comments", status_code=status.HTTP_200_OK)
async def comments(current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    try: 
        comments = list(comment_collection.find({"user_id": user["_id"]}).sort("date_created", -1))
        encoded_comment = jsonable_encoder(comments, custom_encoder={ObjectId:str, datetime:str})
    except PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error occured while fetching documents: {e}"})
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': True, "message": f"Unknown error occured: {e}"})

    return {
        "succcess": True,
        "commencts": encoded_comment
    }

@router.get("/retrieve/comment", status_code=status.HTTP_200_OK)
def retrieve_comment(comment_id: str, current_user: str = Depends(get_current_user)):
    try:
        comment = comment_collection.find_one({"_id": ObjectId(comment_id)})
        if comment:
            # encode_comment = jsonable_encoder(comment, custom_encoder={ObjectId: str, datetime: str})
            return comment
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False, "message": "No comment with this provided ID"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False,  "message": f"{e}"})


@router.put("/update-comment")
async def update_comment(comment_id: str, update_form: UpdateForm, current_user: str = Depends(get_current_user)):
    try:
        user = get_user_byEmail(email=current_user)
        comment = retrieve_comment(comment_id, current_user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"{e}"})

    if  str(comment["user_id"]) != str(user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'success': False, "message": "You can't perform this action"})

    convert_to_dict = update_form.model_dump(exclude_unset=True)
    convert_to_dict["date_updated"] = datetime.now()
    try:
        save = comment_collection.find_one_and_update({"_id": comment["_id"], "user_id": user["_id"]},{"$set": convert_to_dict}, return_document=ReturnDocument.AFTER )
    except Exception or PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'success': False, "message": f"error occured while updating comment {e}"})

    encode_updated_comment = jsonable_encoder(save, custom_encoder={ObjectId: str, datetime: str})

    return {
        "success": True,
        "comment": encode_updated_comment
    }


@router.delete("/delete-comment", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: str, current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    try:
        do_delete = comment_collection.delete_one({'_id': ObjectId(comment_id), "user_id": user["_id"]})
    except Exception or PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False, 'message': f"{e}"})



@router.post("/comment/reply", status_code=status.HTTP_201_CREATED)
def reply_to_comment(comment_id: str, reply_form: Comment, current_user: str = Depends(get_current_user)):
    comment = retrieve_comment(comment_id, current_user)
    user = get_user_byEmail(email=current_user)
    try:
        convert_to_dict = reply_form.model_dump()
        convert_to_dict.update({
            "user_id": user["_id"],
            "post_id": comment["post_id"],
            "comment_id": comment["_id"]
        })
        reply = comment_collection.insert_one(convert_to_dict)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Errro: {e}"})
    
    return {
        "success": True,
        "id": str(reply.inserted_id)
    }


@router.get("/comment/replies", status_code=status.HTTP_200_OK)
def get_replies(comment_id: str, current_user: str = Depends(get_current_user)):
    try:
        replies = list(comment_collection.find({"comment_id": ObjectId(comment_id)}))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": True, "message": f"Error occured while retriving comment: {e}"})
    
    encode_replies = jsonable_encoder(replies, custom_encoder={ObjectId:str, datetime:str})

    return {
        "success":True,
        "replies": encode_replies
    }