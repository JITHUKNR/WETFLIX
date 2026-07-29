import time
import datetime
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultCachedVideo, InlineQueryResultCachedPhoto
from database import users_col, stickers_col, videos_col, images_col, settings_col, get_fsub_data, is_user_requested
from config import ADMIN_ID

# -----------------------------------------------------------
# പുതിയ ഡാറ്റാബേസ് ഉണ്ടാക്കാൻ ഇത് ചേർത്തു
# -----------------------------------------------------------
db = videos_col.database
hntai_col = db['hntai_videos']

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
                
            # Check VIP and Banned Status
            user_data = users_col.find_one({"user_id": user_id})
            is_vip = False
            
            if user_data:
                if user_data.get("banned", False):
                    bot.reply_to(message, "🚫 You are banned from using this bot.")
                    return
                
                vip_until = user_data.get("vip_until")
                if vip_until and isinstance(vip_until, datetime.datetime):
                    if datetime.datetime.now() < vip_until:
                        is_vip = True

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

            # Dynamic Cooldown Timer Check (VIP Bypass)
            if user_id != ADMIN_ID and not is_vip:
                cooldown_limit = get_dynamic_cooldown()
                current_time = time.time()
                last_time = user_cooldowns.get(user_id, 0)
                if current_time - last_time < cooldown_limit:
                    remaining = int(cooldown_limit - (current_time - last_time))
                    # ⚠️ ഇവിടെയാണ് ആ പുതിയ ബോൾഡ് മെസ്സേജ് കൃത്യമായി ചേർത്തിട്ടുള്ളത് ⚠️
                    warn_msg = bot.reply_to(message, f"⏳ Please wait **{remaining} seconds** before requesting another file.\n\n💡 **TIP: Want 7 Days FREE Premium? Click the 🎁 REFER button and invite 5 friends to use the bot without any wait time!**", parse_mode='Markdown')
                    threading.Timer(10.0, delete_message_after_delay, args=[bot, message.chat.id, warn_msg.message_id]).start()
                    return

            # Fetch Random Item from Database
            random_item = list(db_collection.aggregate([{"$sample": {"size": 1}}]))
            
            if random_item:
                file_id = random_item[0]["file_id"]
                del_time = get_delete_time()
                
                if is_vip:
                    caption = f"👑 **VIP Access** | ⚠️ *This file will auto-delete in {int(del_time)} seconds!*"
                else:
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

    # -----------------------------------------------------------
    # Inline Mode Handler (പുതിയതായി ചേർത്തത്)
    # -----------------------------------------------------------
    @bot.inline_handler(func=lambda query: True)
    def inline_query_handler(inline_query):
        try:
            query_text = inline_query.query.lower().strip()
            results = []
            
            # 'photo' എന്ന് ടൈപ്പ് ചെയ്താൽ ഫോട്ടോകൾ കാണിക്കും
            if query_text == "photo":
                random_items = list(images_col.aggregate([{"$sample": {"size": 30}}]))
                for idx, item in enumerate(random_items):
                    results.append(InlineQueryResultCachedPhoto(
                        id=f"photo_{idx}",
                        photo_file_id=item["file_id"]
                    ))
            
            # വെറുതെ യൂസർനെയിം അടിച്ചാൽ വീഡിയോകൾ കാണിക്കും
            else:
                random_items = list(videos_col.aggregate([{"$sample": {"size": 30}}]))
                for idx, item in enumerate(random_items):
                    results.append(InlineQueryResultCachedVideo(
                        id=f"video_{idx}",
                        video_file_id=item["file_id"],
                        title=f"🎥 WETFLIX Video {idx+1}",
                        description="Click to send this viral video"
                    ))
            
            if results:
                # 1 സെക്കൻഡ് കാഷെ വെക്കുന്നത് പുതിയ വീഡിയോകൾ റാൻഡം ആയി വരാൻ സഹായിക്കും
                bot.answer_inline_query(inline_query.id, results, cache_time=1, is_personal=True)
        except Exception as e:
            print(f"Inline Query Error: {e}")

    # --- ബട്ടണുകൾ വർക്ക് ആകാൻ ചേർത്ത മാറ്റങ്ങൾ ---
    
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

    # --- പുതിയ HNTAI ബട്ടൺ ഇവിടെ ചേർത്തു ---
    @bot.message_handler(func=lambda message: message.text == "💅🏻 ANIME")
    def cmd_hntai(message):
        process_media_request(message, hntai_col, bot.send_video, "No exclusive videos available right now.")

    # -----------------------------------------------------------
    # Auto-Save Media from Channels and Groups (മാറ്റം വരുത്തിയത്)
    # -----------------------------------------------------------
    def save_media_to_db(message):
        try:
            # പുതിയ ചാനൽ ആണെങ്കിൽ വേറെ ഡാറ്റാബേസിൽ സേവ് ആകും
            if message.chat.id == -1003986796720:
                if message.content_type == 'video':
                    if not hntai_col.find_one({"file_id": message.video.file_id}):
                        hntai_col.insert_one({"file_id": message.video.file_id})
                        print("✅ Exclusive Video saved to HNTAI DB")
            else:
                # മറ്റ് ഗ്രൂപ്പുകളിൽ/ചാനലുകളിൽ നിന്നുള്ളവ സാധാരണ പോലെ സേവ് ആകും
                if message.content_type == 'video':
                    if not videos_col.find_one({"file_id": message.video.file_id}):
                        videos_col.insert_one({"file_id": message.video.file_id})
                        print("✅ Video saved to Normal DB")
                
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
