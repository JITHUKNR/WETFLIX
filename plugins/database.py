from config import db

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
