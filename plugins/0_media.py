import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import users_col, stickers_col, videos_col, images_col, settings_col, get_fsub_data, is_user_requested
from config import ADMIN_ID

user_cooldowns = {}

# സുരക്ഷിതമായ ഡാറ്റാബേസ് ഫെച്ചിങ്
def get_dynamic_cooldown():
    try:
        data = settings_col.find_one({"_id": "bot_settings"})
        if data and "cooldown" in data:
            return float(data["cooldown"])  
    except:
        pass
    return 180.0  

def get_delete_time():
    try:
        data = settings_col.find_one({"_id": "bot_settings"})
        if data and "delete_time" in data:
            return float(data["delete_time"])
    except:
        pass
    return 30.0  

def is_maintenance():
    try:
        state = settings_col.find_one({"_id": "maintenance"})
        return state["status"] if state else False
    except:
        return False

def is_user_subscribed(bot, user_id):
    try:
        channels = get_fsub_data()
        if not channels:
            return True
            
        if is_user_requested(user_id):
            return True
            
        for ch in channels:
            status = bot.get_chat_member(ch["id"], user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except:
        return False

def delete_message_after_delay(bot_instance, chat_id, message_id):
    try:
        bot_instance.delete_message(chat_id, message_id)
    except:
        pass

def setup(bot):

    # -----------------------------------------------------------
    # Media Request Handler (Video, Image, Sticker)
    # -----------------------------------------------------------
    def process_media_request(message, db_collection, send_function, error_text):
        try:
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

            # Force Subscribe Check (Admin is exempt)
            if user_id != ADMIN_ID and not is_user_subscribed(bot, user_id):
                channels = get_fsub_data()
                markup = InlineKeyboardMarkup(row_width=1)
                if channels:
                    for idx, ch in enumerate(channels, start=1):
                        markup.add(InlineKeyboardButton(f"📢 Join Channel {idx}", url=ch["link"]))
                markup.add(InlineKeyboardButton("✅ I have requested / joined", callback_data="check_sub"))
                
                bot.reply_to(message, "⚠️ **To use this command, you must send join requests to our official channels!** 👇", reply_markup=markup, parse_mode='Markdown')
                return

            # Dynamic Cooldown Timer Check
            cooldown_limit = get_dynamic_cooldown()
            if user_id != ADMIN_ID:
                current_time = time.time()
                last_time = user_cooldowns.get(user_id, 0)
                if current_time - last_time < cooldown_limit:
                    remaining = int(cooldown_limit - (current_time - last_time))
                    warn_msg = bot.reply_to(message, f"⏳ Please wait **{remaining} seconds** before requesting another file.")
                    threading.Timer(10.0, delete_message_after_delay, args=[bot, message.chat.id, warn_msg.message_id]).start()
                    return

            # Fetch Random Item from Database
            random_item = list(db_collection.aggregate([{"$sample": {"size": 1}}]))
            
            if random_item:
                file_id = random_item[0]["file_id"]
                del_time = get_delete_time()
                caption = f"⚠️ *This file will auto-delete in {int(del_time)} seconds! Forward or save it quickly.*"
                
                try:
                    sent_msg = send_function(message.chat.id, file_id, caption=caption, parse_mode='Markdown')
                except TypeError:
                    sent_msg = send_function(message.chat.id, file_id)
                
                user_cooldowns[user_id] = time.time()
                
                threading.Timer(del_time, delete_message_after_delay, args=[bot, message.chat.id, sent_msg.message_id]).start()
            else:
                bot.reply_to(message, error_text)
                
        except Exception as e:
            bot.reply_to(message, f"❌ Error loading media: `{e}`", parse_mode='Markdown')
            print(f"Media Fetch Error: {e}")

    # --- പുതിയ ബട്ടണുകൾ വർക്ക് ആകാൻ ചേർത്ത മാറ്റങ്ങൾ ---
    
    @bot.message_handler(commands=['sticker'])
    @bot.message_handler(func=lambda message: message.text == "💀 STICKER")
    def cmd_sticker(message):
        process_media_request(message, stickers_col, bot.send_sticker, "No stickers available right now.")

    @bot.message_handler(commands=['video'])
    @bot.message_handler(func=lambda message: message.text == "🔞 VIDEO")
    def cmd_video(message):
        process_media_request(message, videos_col, bot.send_video, "No videos available right now.")

    @bot.message_handler(commands=['image'])
    @bot.message_handler(func=lambda message: message.text == "🍓 PHOTO")
    def cmd_image(message):
        process_media_request(message, images_col, bot.send_photo, "No photos available right now.")

    # -----------------------------------------------------------

    # -----------------------------------------------------------
    # Auto-Save Media from Channels and Groups
    # -----------------------------------------------------------
    def save_media_to_db(message):
        try:
            if message.content_type == 'video':
                if not videos_col.find_one({"file_id": message.video.file_id}):
                    videos_col.insert_one({"file_id": message.video.file_id})
                    print("✅ Video saved to DB")
            
            elif message.content_type == 'photo':
                if not images_col.find_one({"file_id": message.photo[-1].file_id}):
                    images_col.insert_one({"file_id": message.photo[-1].file_id})
                    print("✅ Photo saved to DB")
                    
            elif message.content_type == 'sticker':
                if not stickers_col.find_one({"file_id": message.sticker.file_id}):
                    stickers_col.insert_one({"file_id": message.sticker.file_id})
                    print("✅ Sticker saved to DB")
        except Exception as e:
            print(f"Error saving media: {e}")

    @bot.channel_post_handler(content_types=['video', 'photo', 'sticker'])
    def handle_channel_post(message):
        save_media_to_db(message)

    @bot.message_handler(content_types=['video', 'photo', 'sticker'], func=lambda message: message.chat.type in ['group', 'supergroup'])
    def handle_group_message(message):
        save_media_to_db(message)
