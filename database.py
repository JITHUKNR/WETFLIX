import pymongo
import certifi
from config import MONGO_URI

# MongoDB Connection with certifi for SSL security
client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["ultimate_telegram_bot"]

# Collections
users_col = db["users"]
stickers_col = db["stickers"]
videos_col = db["videos"]
images_col = db["images"]
settings_col = db["settings"]
settings_collection = db["settings"]
requested_users_collection = db["requested_users"]

def set_fsub_data(channels_list):
    settings_collection.update_one(
        {"_id": "fsub_settings"}, 
        {"$set": {"channels": channels_list}}, 
        upsert=True
    )

def get_fsub_data():
    data = settings_collection.find_one({"_id": "fsub_settings"})
    if data and "channels" in data:
        return data["channels"]
    return []

def add_requested_user(user_id):
    requested_users_collection.update_one(
        {"user_id": user_id}, 
        {"$set": {"requested": True}}, 
        upsert=True
    )

def is_user_requested(user_id):
    data = requested_users_collection.find_one({"user_id": user_id})
    return True if data else False

def set_cooldown(minutes):
    settings_collection.update_one(
        {"_id": "bot_settings"}, 
        {"$set": {"cooldown": minutes}}, 
        upsert=True
    )

def get_cooldown():
    data = settings_collection.find_one({"_id": "bot_settings"})
    if data and "cooldown" in data:
        return data["cooldown"]
    return 3
