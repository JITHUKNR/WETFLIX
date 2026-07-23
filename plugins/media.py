import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_col, stickers_col, videos_col, images_col, settings_col
from config import ADMIN_ID

COOLDOWN_TIME = 180  # 3 minutes timer
user_cooldowns = {}

def is_maintenance():
    state = settings_col.find_one({"_id": "maintenance"})
    return state["status"] if state else False

def delete_message_after_delay(chat_id, message_id):
    try:
        bot_instance.delete_message(chat_id, message_id)
    except:
        pass

bot_instance = None

def setup(bot):
    global bot_instance
    bot_instance = bot

    # -----------------------------------------------------------
    # Media Request Handler (Video, Image, Sticker)
    # -----------------------------------------------------------
    def process_media_request(message, db_collection, send_function, error_text):
        user_id = message.from_user.id
        
        # Check Maintenance Mode
        if is_maintenance() and user_id != ADMIN_ID:
            bot.reply_to(message, "⚙️ The bot is currently under maintenance. Please try again later.")
            return
            
        # Check Banned Status
        user_data = users_col.find_one({"user_id": user_id})
        if user_data and user_data.get("banned", False):
            bot.reply_to(message, "🚫 You are banned from using this bot.")
            return

        # Cooldown Timer Check (Admin is exempt)
        if user_id != ADMIN_ID:
            current_time = time.time()
            last_time = user_cooldowns.get(user_id, 0)
            if current_time - last_time < COOLDOWN_TIME:
                remaining = int(COOLDOWN_TIME - (current_time - last_time))
                mins, secs = divmod(remaining, 60)
                warn_msg = bot.reply_to(message, f"⏳ Please wait {mins} minutes and {secs} seconds before requesting another file.")
                threading.Timer(10.0, delete_message_after_delay, args=[message.chat.id, warn_msg.message_id]).start()
                return

        # Fetch Random Item from Database
        random_item = list(db_collection.aggregate([{"$sample": {"size": 1}}]))
        
        if random_item:
            file_id = random_item[0]["file_id"]
            sent_msg = send_function(message.chat.id, file_id)
            user_cooldowns[user_id] = time.time()
            # Auto-delete sent media after 3 minutes
            threading.Timer(180.0, delete_message_after_delay, args=[message.chat.id, sent_msg.message_id]).start()
        else:
            bot.reply_to(message, error_text)

    @bot.message_handler(commands=['sticker'])
    def cmd_sticker(message):
        process_media_request(message, stickers_col, bot.send_sticker, "No stickers available right now.")

    @bot.message_handler(commands=['video'])
    def cmd_video(message):
        process_media_request(message, videos_col, bot.send_video, "No videos available right now.")

    @bot.message_handler(commands=['image'])
    def cmd_image(message):
        process_media_request(message, images_col, bot.send_photo, "No photos available right now.")

    # -----------------------------------------------------------
    # Auto-Save Media from Channels and Groups
    # -----------------------------------------------------------
    def save_media_to_db(message):
        try:
            if message.content_type == 'video':
                if not videos_col.find_one({"file_id": message.video.file_id}):
                    videos_col.insert_one({"file_id": message.video.file_id})
            
            elif message.content_type == 'photo':
                if not images_col.find_one({"file_id": message.photo[-1].file_id}):
                    images_col.insert_one({"file_id": message.photo[-1].file_id})
                    
            elif message.content_type == 'sticker':
                if not stickers_col.find_one({"file_id": message.sticker.file_id}):
                    stickers_col.insert_one({"file_id": message.sticker.file_id})
        except Exception as e:
            print(f"Error saving media: {e}")

    @bot.channel_post_handler(content_types=['video', 'photo', 'sticker'])
    def handle_channel_post(message):
        save_media_to_db(message)

    @bot.message_handler(content_types=['video', 'photo', 'sticker'], func=lambda message: message.chat.type in ['group', 'supergroup'])
    def handle_group_message(message):
        save_media_to_db(message)
