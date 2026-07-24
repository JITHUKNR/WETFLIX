import os
from pymongo import MongoClient

# Bot credentials and settings
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
PORT = int(os.environ.get("PORT", 10000))

# MongoDB Database Initialization
client = MongoClient(MONGO_URI)
db = client["wetflix_database"]
