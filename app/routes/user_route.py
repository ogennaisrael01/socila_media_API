from fastapi import APIRouter, status, Body, HTTPException, status, Depends
from app.models import user_models
from app.config.db_config import db
from app.utils.security import hash_password, verify_password, get_access_token, get_current_user
from bson import ObjectId
from fastapi.security import OAuth2PasswordRequestForm
import random
from app.utils.helper_functions import get_user, get_profile_data
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
router = APIRouter(
    tags=["Authentication and profile management"]
)


user_collection = db.get_collection("social_media_users")
otp_collection = db.get_collection("social_media_otp")
profile_collection = db.get_collection("social_media_user_profiles")

def get_random_code():
    return random.randint(100000, 999999)

@router.post("/register", response_model=user_models.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(registration_form: user_models.UserCreate = Body(...)):
    created = False
    user = user_collection.find_one({"email": registration_form.email})
    if user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="User with this email already exists")
    
    try:

        to_dict = registration_form.model_dump()
        to_dict["password"] = hash_password(registration_form.password)
        to_dict["is_verified"] = False
        resp = user_collection.insert_one(to_dict)
        created = True
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occured {e}")
    
    if created:
        profile = user_models.UserProfile()
        encoded_profile = jsonable_encoder(profile)
        encoded_profile["user_id"] = resp.inserted_id
        profile_collection.insert_one(encoded_profile)

        otp_code = otp_collection.insert_one({
            "email": registration_form.email,
            "code": get_random_code()
        })
        # Simulate sending email by printing the OTP code to the console
        otp_data = otp_collection.find_one({"_id": otp_code.inserted_id})
        print(f"OTP code: {otp_data["code"]}")

    return {
        "id": str(resp.inserted_id),
        "email": registration_form.email,
        "status_code": str(status.HTTP_201_CREATED)
    }
    
@router.post("/login", response_model=user_models.LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(login_form: OAuth2PasswordRequestForm = Depends()):
    user = user_collection.find_one({"email": login_form.username})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user with this given credentials dosent exists")
    
    if not user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your account")
    
    verified = verify_password(login_form.password, user["password"])
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detial="invalid credentials")
    
    access_token = get_access_token(data={"email": login_form.username}, expire_minites=10)

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }


@router.put("/resend/otp")
def resend_otp(form: user_models.ResendOTP):
    to_dict = form.model_dump()
    otp = otp_collection.find_one({"email": to_dict["email"]})

    if not otp: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered")

    otp["code"] = get_random_code()
    new_code = otp["code"]
    otp_collection.update_one({"_id": otp["_id"]}, {"$set": otp})
    return {
        "new_code": new_code
    }

@router.post("/verify/user", status_code=status.HTTP_200_OK)
def verify_user(otp_code: user_models.OTPCode):
    to_dict = otp_code.model_dump()
    code = to_dict["code"]

    retrive_code_from_db = otp_collection.find_one({
        "code": code
    })
    if not retrive_code_from_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code")

    user = user_collection.find_one_and_update({"email": retrive_code_from_db["email"]}, {"$set": {"is_verified": True}})

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error loading finding user")
    
    otp_collection.delete_one({"_id": retrive_code_from_db["_id"]})

    return {
        "success": True,
        "message": "account verification successful"
    }


@router.get("/user/me", status_code=status.HTTP_200_OK, response_model=user_models.UserProfileResponse)
def get_profile(email: str = Depends(get_current_user)):
    user = user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="An error occured")
    
    user_dict = get_user(user)
    user_id  = ObjectId(user["_id"])
    profile = profile_collection.find_one({
        "user_id": user_id
        })
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile is associated with this user")
    
    
    return get_profile_data(user=user_dict, profile=profile)


