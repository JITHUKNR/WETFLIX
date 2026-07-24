import datetime
from database import users_col

def setup(bot):
    # ഈ ഫംഗ്ഷൻ ഓരോ യൂസർ മെസ്സേജ് അയക്കുമ്പോഴും അവരുടെ സമയം അപ്ഡേറ്റ് ചെയ്യും
    @bot.middleware_handler(update_types=['message'])
    def track_activity(bot_instance, message):
        user_id = message.from_user.id
        now = datetime.datetime.now()
        
        try:
            users_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {"last_active": now}, 
                    "$setOnInsert": {"joined_date": now, "banned": False}
                },
                upsert=True
            )
        except Exception as e:
            pass
