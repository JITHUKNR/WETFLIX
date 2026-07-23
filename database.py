import pymongo
import certifi
from config import MONGO_URI

# MongoDB കണക്ഷൻ 
client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["ultimate_telegram_bot"]

# കളക്ഷനുകൾ
users_col = db["users"]
stickers_col = db["stickers"]
videos_col = db["videos"]
images_col = db["images"]
settings_col = db["settings"]
