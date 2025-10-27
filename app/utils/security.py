from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.models import user_models
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config.settings import settings

oauth2 = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


def get_access_token(data: dict, expire_minites: int | None = None):
    to_encode = data.copy()

    if not expire_minites:
        expire = str(datetime.utcnow()) + str(timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    else:
        expire = str(datetime.utcnow()) + str(timedelta(minutes=expire_minites))

    to_encode.update({"expire": expire})

    generate_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return generate_token


def verify_token(token: str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_email = payload.get("email")

        if not user_email:
            return credential_exception

        token_data = user_models.ToeknData(email=user_email)
    except Exception:
        return credential_exception

    return token_data.email


def get_current_user(token:str = Depends(oauth2)):
    exceptions = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials are not provided")

    return verify_token(token=token, credential_exception=exceptions)

