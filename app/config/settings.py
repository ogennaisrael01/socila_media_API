import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Setting(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: str

    class config:
        env_file = ".env"

settings = Setting()