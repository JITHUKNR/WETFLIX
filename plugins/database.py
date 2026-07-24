# database.py യിലോ അത്തരത്തിലുള്ള ഫയലിലോ ചേർക്കുക

# നിങ്ങളുടെ ഡാറ്റാബേസ് കളക്ഷൻ (ഉദാഹരണത്തിന് settings)
settings_collection = db["settings"] 

def set_fsub_channel(channel_username):
    # ചാനൽ നെയിം ഡാറ്റാബേസിൽ സേവ് ചെയ്യുന്നു
    settings_collection.update_one(
        {"_id": "fsub_settings"}, 
        {"$set": {"channel": channel_username}}, 
        upsert=True
    )

def get_fsub_channel():
    # ഡാറ്റാബേസിൽ നിന്ന് ചാനൽ നെയിം എടുക്കുന്നു
    data = settings_collection.find_one({"_id": "fsub_settings"})
    if data and "channel" in data:
        return data["channel"]
    return None # സെറ്റ് ചെയ്തിട്ടില്ലെങ്കിൽ None തരും
