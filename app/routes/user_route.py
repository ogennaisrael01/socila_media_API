from fastapi import APIRouter, status, Body, HTTPException, status, Depends, BackgroundTasks
from app.models import user_models
from app.utils.security import hash_password, verify_password, get_access_token, get_current_user
from bson import ObjectId
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.helper_functions import single_user, get_profile_data
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from pymongo.errors import PyMongoError
import jwt
import logging
from ..config.settings import settings
from datetime import datetime, timedelta
from pymongo.collection import ReturnDocument
from ..utils.email_utility import verification_email, send_updated_verification, password_reset_email
from ..utils.cloudinary_utils import upload_image
from ..config.db_config import (
    user_collection,
    profile_collection
)

logging.basicConfig(level=logging.INFO)
router = APIRouter(
    tags=["Authentication and profile management"],
    prefix="/auth"
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHMS = settings.ALGORITHM
BASE_URL = settings.BASE_URL
TOKEN_LIFESPAN = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@router.post("/register", response_model=user_models.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(*, registration_form: user_models.UserCreate = Body(...), background_tasks: BackgroundTasks):
    created = False 
    encoded_form = jsonable_encoder(registration_form)
    if user_collection.find_one({"email": encoded_form["email"]}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists, try signing in")
    encoded_form["password"] = hash_password(encoded_form["password"])
    try: 
        user = user_collection.insert_one(encoded_form)
        created = True
    except PyMongoError as e:
        logging.error(f"Error while connecting to pymongo: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        logging.error(f"An Error occured while creating new user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    else:
        logging.info("User registration is successful")


    if created: 
        exp = datetime.now() + timedelta(minutes=30)
        payload = {"sub": str(user.inserted_id), "exp": exp}
        try:
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHMS)
            verification_url = f"{BASE_URL}/api/v1/verify-user/{token}"
            background_tasks.add_task(
                verification_email,
                url=verification_url,
                email=encoded_form["email"]
            )
        except Exception as e:
            logging.error(f"Error: An error occured while sending email: {e}")
        else:
            logging.info("Email proceded to send function")
        create_profile = user_models.UserProfile(user_id= str(user.inserted_id))
        profile_collection.insert_one(create_profile.model_dump())
        

    return {
        "success": True,
        "result": {
            "id": str(user.inserted_id),
            "email": encoded_form["email"],
            "username": encoded_form["username"]
        },
    }

@router.post("/verify-user/{token}")
async def verify_user(token: str, background_tasks: BackgroundTasks):
    updated = False
    if not token:
        logging.error("Can't verify a user with out sending the veification token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="can't verify a user without verification token")
    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHMS])
        user_id = decode_token.get("sub")

        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            logging.info("user does not exists in our database")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        
        verify_user = user_collection.find_one_and_update({"_id": ObjectId(user_id)}, {"$set": {"is_verified": True}}, return_document= ReturnDocument.AFTER)
        updated = True
    except jwt.DecodeError as e:
        logging.error(f"error decoding the provided token {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"error decoding jwt token: {e}")
    except Exception as e:
        logging.error(f"error ocured: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"an unknown error occures: {e}")

    if updated and verify_user:
        try:
            background_tasks.add_task(
                send_updated_verification,
                email=verify_user["email"],

            )
        except Exception:
            logging.errors("Error occured")
    return {
        "success": True,
        "result": {
            "email": verify_user["email"],
            "is_verified": verify_user["is_verified"]
        }
    }
        

@router.post("/login", response_model=user_models.LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(login_form: OAuth2PasswordRequestForm = Depends()):
    user = user_collection.find_one({"email": login_form.username})
    if not user:
        logging.error("user not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user with this given credentials dosent exists")
    
    if not user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your account")
    
    verified = verify_password(login_form.password, user["password"])
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid credentials")
    
    access_token = get_access_token(data={"email": login_form.username}, expire_minites=10)

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }

@router.post("/password/reset")
def reset_password(email_form: user_models.PasswordResetForm, background_tasts: BackgroundTasks):
    user = user_collection.find_one({"email": email_form.email})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    exp = datetime.now() + timedelta(minutes=30)
    payload = {"sub": email_form.email, "exp": exp}
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHMS)
        passwoord_reset_url = f"{BASE_URL}/api/v1/password/reset/confirm/{token}"
        background_tasts.add_task(
            password_reset_email,
            email= email_form.email,
            reset_url=passwoord_reset_url
        )
    except jwt.DecodeError: 
        logging.error("error decoding jwt payload")
        raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, detail="error decoding payload")
    except Exception:
        logging.error("an error occured")
    

    return {
        "success": True,
        "message": "password reset link sent",
        "password_reset_link": passwoord_reset_url
    }
    

@router.put("/password/reset/confirm/{token}")
def confirm_password_reset(token: str, form: user_models.PasswordConfirm, backgroud_tasks: BackgroundTasks):
    # first compare password
    if form.new_password.strip() != form.confirm_password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credential(password mismatch)")
    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHMS])
        user_email = decode_token.get("sub")
        if not user_email: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        user = user_collection.find_one({"email": user_email})
        print("saved passwrod", user["password"])
        user_collection.update_one({"email": user_email}, {"$set": {"password": hash_password(form.new_password)}})
    except jwt.DecodeError as e:
        logging.error(f"error decoding token {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"error decoding jwt token {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"errro {e}")

    return {
        "success": True,
        "message": "password reset done"
}

 
@router.get("/me", status_code=status.HTTP_200_OK)
def profile(email: str = Depends(get_current_user)):
    user = user_collection.find_one({"email": email})
    if not user:
        logging.info("user not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    encode_user = jsonable_encoder(user, custom_encoder={ObjectId: str, datetime: str})
    return_user_data = single_user(encode_user)
    try:  
        profile_data = profile_collection.find_one({"user_id": encode_user["_id"]})
        if not profile_data:
            logging.info("no profile is associted with this user")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No profile associated with this user {e}")
    encode_profile = jsonable_encoder(profile_data, custom_encoder={ObjectId: str, datetime:str})
    return get_profile_data(user=return_user_data, profile=encode_profile)

@router.get("/user/{user}")
def get_user_byId(user: str, current_user: str = Depends(get_current_user)):
    try:
        user = user_collection.find_one({"_id": ObjectId(user)})
        if user:
            return user
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": True, "message": "user not found"})
    except Exception as e:
        logging.error(f"Error occured while retrieving user info by id: {e}")
        raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False, "message": f"Error: {e}"})


@router.get("/user/{email}")
def get_user_byEmail(email:str = Depends(get_current_user)):
    try:
        user = user_collection.find_one({"email": email})
        if user:
            return user
        else:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": True, "message": "user not found"})
    except Exception as e:
        logging.error(f"Error occured while retrieving user info by id: {e}")
        raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={'success': False, "message": f"Error: {e}"})
    
@router.put("/me/update", response_model=user_models.UserResponse)
def updete_info(*, current_user: str = Depends(get_current_user), update_form: user_models.UserCreate):
    user = get_user_byEmail(email=current_user)
    try:
        convert_to_dict = update_form.model_dump(exclude_unset=True)
        convert_to_dict["updated_at"] = datetime.now()
        user_update = user_collection.find_one_and_update({"_id": user["_id"], "email": user["email"]}, {"$set": convert_to_dict}, return_document=ReturnDocument.AFTER)
    except Exception or PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Error: {e}"})

    encoed_user_info = jsonable_encoder(user_update, custom_encoder={ObjectId:ste, datetime: str})

    return {
        "success": True,
        "result": encoed_user_info
    }

@router.post("/upload-avatar", status_code=status.HTTP_200_OK)
def upload_image(image_url: user_models.UploadImage, current_user: str = Depends(get_current_user)):
    user = get_user_byEmail(email=current_user)
    try:
        upload_to_clodinary = upload_image(image_url)
        save_to_db = user_collection.update_one({"_id": user["_id"], "email": user["email"]}, {"$set": {"image_url": image_url}})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"{e}"})
    return {
        "success": True,
        "secure_url": upload_to_clodinary.get("secure_url")
    }
