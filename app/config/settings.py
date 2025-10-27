import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Setting(BaseSettings):
    DATABASE_URL: str = 'mongodb+srv://ogennaisrael98_db_user:FnR4YwZgRzSmbREm@cluster0.itj4xbo.mongodb.net/test_db'
    SECRET_KEY: str = "default_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: str = "30"
    BASE_URL: str = "http://127.0.0.1:8000"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    class config:
        env_file = ".env"

settings = Setting()