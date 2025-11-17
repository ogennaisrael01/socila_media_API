import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Setting(BaseSettings):
    DATABASE_URL: str = ''
    SECRET_KEY: str = "default_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: str = "30"
    BASE_URL: str = "https://easyconnect-mu.vercel.app/"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    EMAIL_HOST: str = ""
    EMAIL_PORT: str = ""
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""

    class config:
        env_file = ".env"

settings = Setting()