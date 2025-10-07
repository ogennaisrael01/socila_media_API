from app.models import user_models


def get_user(user):
    return user_models.UserBase(
        id=str(user["_id"]),
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        user_name=user["username"],
        is_verified=user["is_verified"],
        created_at=user["created_at"]
    )

def get_profile_data(user, profile):
    return user_models.UserProfileResponse(
        id=str(profile["_id"]),
        user=user,
        bio=profile["bio"],
        profile_picture=profile["profile_picture"],
        location=profile["location"],
        updated_at=profile["updated_at"]
        
    )

