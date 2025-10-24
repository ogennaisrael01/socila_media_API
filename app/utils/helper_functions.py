from app.models import user_models

def single_user(user):
    return {
        "id":(user["_id"]),
        "email":user["email"],
        "first_name":user["first_name"],
        "last_name":user["last_name"],
        "user_name":user["username"],
        "is_verified":user["is_verified"],
        "created_at":user["created_at"]
    }

def get_users(users):
    if not users:
        return []
    return  [single_user(user) for user in users]


def get_profile_data(user, profile):
    return user_models.UserProfileResponse(
        id=str(profile["_id"]),
        user=user,
        bio=profile["bio"],
        profile_picture=profile["profile_picture"],
        location=profile["location"],
        updated_at=profile["updated_at"]
        
    )

