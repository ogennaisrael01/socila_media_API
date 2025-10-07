from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi 
from .settings import settings


uri = settings.DATABASE_URL

client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

db = client["socialmediaAPI"]

# Test the connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Error connecting to MongoDB:")
    print(e)
