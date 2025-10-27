from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi 
from .settings import settings
import os 
from dotenv import load_dotenv

load_dotenv()


uri = os.getenv("DATABASE_URL", 'mongodb+srv://ogennaisrael98_db_user:FnR4YwZgRzSmbREm@cluster0.itj4xbo.mongodb.net/test_db')

client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
# Test the connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Error connecting to MongoDB:")
    print(e)


db = client["socialmediaAPI"]
user_collection = db.get_collection("social_media_users")
otp_collection = db.get_collection("social_media_otp")
profile_collection = db.get_collection("social_media_user_profiles")
post_collection = db.get_collection("social_media_posts")
follower_collection = db.get_collection("social_media_followers")
likes_collection = db.get_collection("social_media_likes")
comment_collection= db.get_collection("social_media_comment")