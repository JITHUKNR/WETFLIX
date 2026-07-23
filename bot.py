import telebot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import pymongo
import certifi
import time
import threading
import os
from flask import Flask

# -----------------------------------------------------------
# സുരക്ഷയ്ക്കായി Environment Variables ഉപയോഗിക്കുന്നു
# -----------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN", "നിങ്ങളുടെ_ടോക്കൺ")
MONGO_URI = os.environ.get("MONGO_URI", "നിങ്ങളുടെ_മൊംഗോ_ലിങ്ക്")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789)) # താങ്കളുടെ ടെലിഗ്രാം ഐഡി ഇവിടെ നൽകുക

bot = telebot.TeleBot(TOKEN)

# -----------------------------------------------------------
# MongoDB കണക്ഷൻ (SSL എറർ ഒഴിവാക്കാൻ certifi ഉപയോഗിച്ചിരിക്കുന്നു)
# -----------------------------------------------------------
client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["ultimate_telegram_bot"]

users_col = db["users"]
stickers_col = db["stickers"]
videos_col = db["videos"]
images_col = db["images"]
settings_col = db["settings"]

# -----------------------------------------------------------
# അടിസ്ഥാന സെറ്റിംഗ്സ്
# -----------------------------------------------------------
COOLDOWN_TIME = 180  # 3 മിനിറ്റ് ടൈമർ
user_cooldowns = {}

# മെയിൻ്റനൻസ് മോഡ് ഓൺ ആണോ എന്ന് നോക്കാൻ
def is_maintenance():
    state = settings_col.find_one({"_id": "maintenance"})
    return state["status"] if state else False

# ബോട്ടിൻ്റെ മെനു ബട്ടണുകൾ
bot.set_my_commands([
    BotCommand("start", "ബോട്ട് ആരംഭിക്കാൻ"),
    BotCommand("sticker", "റാൻഡം സ്റ്റിക്കർ"),
    BotCommand("video", "റാൻഡം വീഡിയോ"),
    BotCommand("image", "റാൻഡം ഫോട്ടോ")
])

def delete_message_after_delay(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# -----------------------------------------------------------
# യൂസർ മാനേജ്‌മെൻ്റ് & സ്റ്റാർട്ട് കമാൻഡ്
# -----------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # പുതിയ യൂസറെ ഡാറ്റാബേസിൽ സേവ് ചെയ്യുന്നു (ബ്രോഡ്കാസ്റ്റിനും സ്റ്റാറ്റ്സിനും വേണ്ടി)
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id, "banned": False, "joined_date": time.time()})
        
    bot.reply_to(message, f"ഹലോ {message.from_user.first_name}! ബോട്ട് ഉപയോഗിക്കാൻ തയ്യാറാണ്. മെനുവിൽ നിന്ന് ഓപ്ഷനുകൾ തിരഞ്ഞെടുക്കുക.")

# ടൈമർ പരിശോധിക്കാൻ
def check_cooldown(user_id):
    current_time = time.time()
    last_time = user_cooldowns.get(user_id, 0)
    if current_time - last_time < COOLDOWN_TIME:
        return int(COOLDOWN_TIME - (current_time - last_time))
    return 0

# -----------------------------------------------------------
# മീഡിയ അയക്കുന്ന ഫംഗ്ഷൻ (സ്റ്റിക്കർ, വീഡിയോ, ഫോട്ടോ)
# -----------------------------------------------------------
def process_media_request(message, db_collection, send_function, error_text):
    user_id = message.from_user.id
    
    # മെയിൻ്റനൻസ് മോഡ് ആണോ എന്ന് നോക്കുന്നു
    if is_maintenance() and user_id != ADMIN_ID:
        bot.reply_to(message, "⚙️ ബോട്ട് ഇപ്പോൾ അപ്ഡേറ്റ് ചെയ്തുകൊണ്ടിരിക്കുകയാണ്. കുറച്ചു കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക.")
        return
        
    # യൂസർ ബാൻ ചെയ്യപ്പെട്ട ആളാണോ എന്ന് നോക്കുന്നു
    user_data = users_col.find_one({"user_id": user_id})
    if user_data and user_data.get("banned", False):
        bot.reply_to(message, "🚫 താങ്കളെ ഈ ബോട്ട് ഉപയോഗിക്കുന്നതിൽ നിന്ന് വിലക്കിയിരിക്കുന്നു.")
        return

    # ടൈമർ പരിശോധന (അഡ്മിന് ടൈമർ ബാധകമല്ല)
    if user_id != ADMIN_ID: 
        remaining_time = check_cooldown(user_id)
        if remaining_time > 0:
            mins, secs = divmod(remaining_time, 60)
            warn_msg = bot.reply_to(message, f"⏳ അടുത്ത ഫയൽ ലഭിക്കാൻ {mins} മിനിറ്റും {secs} സെക്കൻഡും കാത്തിരിക്കുക.")
            threading.Timer(10.0, delete_message_after_delay, args=[message.chat.id, warn_msg.message_id]).start()
            return

    # ഡാറ്റാബേസിൽ നിന്ന് റാൻഡം ഫയൽ എടുക്കുന്നു
    random_item = list(db_collection.aggregate([{"$sample": {"size": 1}}]))
    
    if random_item:
        file_id = random_item[0]["file_id"]
        sent_msg = send_function(message.chat.id, file_id)
        user_cooldowns[user_id] = time.time()
        # 3 മിനിറ്റ് കഴിയുമ്പോൾ ഡിലീറ്റ് ചെയ്യുന്നു
        threading.Timer(180.0, delete_message_after_delay, args=[message.chat.id, sent_msg.message_id]).start()
    else:
        bot.reply_to(message, error_text)

@bot.message_handler(commands=['sticker'])
def cmd_sticker(message):
    process_media_request(message, stickers_col, bot.send_sticker, "സ്റ്റിക്കറുകൾ ലഭ്യമല്ല.")

@bot.message_handler(commands=['video'])
def cmd_video(message):
    process_media_request(message, videos_col, bot.send_video, "വീഡിയോകൾ ലഭ്യമല്ല.")

@bot.message_handler(commands=['image'])
def cmd_image(message):
    process_media_request(message, images_col, bot.send_photo, "ഫോട്ടോകൾ ലഭ്യമല്ല.")

# -----------------------------------------------------------
# ചാനലിൽ നിന്നും ഗ്രൂപ്പിൽ നിന്നും ഓട്ടോമാറ്റിക് ആയി മീഡിയ സേവ് ചെയ്യാൻ
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
                
        elif message.content_type == 'text' and "addstickers/" in message.text:
            pack_name = message.text.split("addstickers/")[-1].split()[0]
            sticker_set = bot.get_sticker_set(pack_name)
            for sticker in sticker_set.stickers:
                if not stickers_col.find_one({"file_id": sticker.file_id}):
                    stickers_col.insert_one({"file_id": sticker.file_id})
    except Exception as e:
        print(f"Error saving media: {e}")

@bot.channel_post_handler(content_types=['text', 'video', 'photo', 'sticker'])
def handle_channel_post(message):
    save_media_to_db(message)

@bot.message_handler(content_types=['text', 'video', 'photo', 'sticker'], func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group_message(message):
    save_media_to_db(message)


# -----------------------------------------------------------
# ADMIN PANEL COMMANDS (പുതിയ ഇൻലൈൻ അഡ്മിൻ മെനു)
# -----------------------------------------------------------

# മെനു ഡിസൈൻ ഉണ്ടാക്കാനുള്ള ഫംഗ്ഷൻ
def get_admin_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("📊 Stats (സ്റ്റാറ്റിസ്റ്റിക്സ്)", callback_data="help_stats"),
        InlineKeyboardButton("📢 Broadcast (ബ്രോഡ്കാസ്റ്റ്)", callback_data="help_broadcast"),
        InlineKeyboardButton("🚫 Ban User (ബാൻ ചെയ്യാൻ)", callback_data="help_ban"),
        InlineKeyboardButton("✅ Unban User (അൺബാൻ ചെയ്യാൻ)", callback_data="help_unban"),
        InlineKeyboardButton("⚙️ Maintenance (മെയിൻ്റനൻസ്)", callback_data="help_maintenance")
    )
    return markup

# /admin എന്ന് ടൈപ്പ് ചെയ്യുമ്പോൾ മെനു വരാൻ
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "👑 **അഡ്മിൻ പാനൽ**\n\nതാഴെ കാണുന്ന ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്താൽ ഓരോ കമാൻഡും എങ്ങനെ ഉപയോഗിക്കണം എന്ന് കാണാം:", reply_markup=get_admin_menu_markup(), parse_mode='Markdown')

# ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്യുമ്പോൾ നിർദ്ദേശങ്ങൾ വരാൻ
@bot.callback_query_handler(func=lambda call: call.data.startswith('help_'))
def admin_help_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "നിങ്ങൾക്ക് ഇതിനുള്ള അനുമതിയില്ല ❌", show_alert=True)
        return

    text = ""
    # Back ബട്ടൺ ക്ലിക്ക് ചെയ്താൽ മെനുവിലേക്ക് തിരികെ പോകാൻ
    if call.data == "help_back":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text="👑 **അഡ്മിൻ പാനൽ**\n\nതാഴെ കാണുന്ന ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്താൽ ഓരോ കമാൻഡും എങ്ങനെ ഉപയോഗിക്കണം എന്ന് കാണാം:", 
                              reply_markup=get_admin_menu_markup(), parse_mode='Markdown')
        return

    # ഓരോ ബട്ടണിനുമുള്ള നിർദ്ദേശങ്ങൾ
    if call.data == "help_stats":
        text = "📊 **Stats കമാൻഡ്**\n\nബോട്ടിലെ ആകെ യൂസർമാർ, സേവ് ചെയ്ത ഫോട്ടോകൾ, വീഡിയോകൾ എന്നിവ എത്രയെന്ന് ഒറ്റനോട്ടത്തിൽ അറിയാൻ ഈ കമാൻഡ് ഉപയോഗിക്കാം.\n\n👉 **ഉപയോഗിക്കേണ്ട വിധം:** `/stats`\n\n💡 വെറുതെ `/stats` എന്ന് ടൈപ്പ് ചെയ്ത് സെൻ്റ് ചെയ്യുക."
    elif call.data == "help_broadcast":
        text = "📢 **Broadcast കമാൻഡ്**\n\nബോട്ടിലുള്ള എല്ലാവർക്കും ഒരേസമയം ഒരു മെസ്സേജ് അയക്കാൻ ഇത് ഉപയോഗിക്കാം.\n\n👉 **ഉപയോഗിക്കേണ്ട വിധം:** `/broadcast <നിങ്ങളുടെ മെസ്സേജ്>`\n\n💡 **ഉദാഹരണത്തിന്:** `/broadcast നാളെ മുതൽ പുതിയ ഫോട്ടോകൾ വരും!`"
    elif call.data == "help_ban":
        text = "🚫 **Ban കമാൻഡ്**\n\nബോട്ട് ഉപയോഗിക്കുന്നതിൽ നിന്നും ഒരാളെ വിലക്കാൻ ഇത് ഉപയോഗിക്കാം. അവരുടെ യൂസർ ഐഡി നൽകണം.\n\n👉 **ഉപയോഗിക്കേണ്ട വിധം:** `/ban <User_ID>`\n\n💡 **ഉദാഹരണത്തിന്:** `/ban 123456789`"
    elif call.data == "help_unban":
        text = "✅ **Unban കമാൻഡ്**\n\nബാൻ ചെയ്ത ഒരാളെ തിരികെ ബോട്ട് ഉപയോഗിക്കാൻ അനുവദിക്കുന്നതിന് ഈ കമാൻഡ് ഉപയോഗിക്കാം.\n\n👉 **ഉപയോഗിക്കേണ്ട വിധം:** `/unban <User_ID>`\n\n💡 **ഉദാഹരണത്തിന്:** `/unban 123456789`"
    elif call.data == "help_maintenance":
        text = "⚙️ **Maintenance കമാൻഡ്**\n\nബോട്ട് താൽക്കാലികമായി ഓഫ് ചെയ്തു വെക്കാൻ ഇത് ഉപയോഗിക്കാം. ഇത് ഒന്നുകൂടി അടിച്ചാൽ ബോട്ട് ഓൺ ആകും.\n\n👉 **ഉപയോഗിക്കേണ്ട വിധം:** `/maintenance`\n\n💡 വെറുതെ `/maintenance` എന്ന് ടൈപ്പ് ചെയ്ത് സെൻ്റ് ചെയ്യുക."

    # Back ബട്ടൺ നിർദ്ദേശങ്ങൾക്ക് താഴെ കാണിക്കാൻ
    back_markup = InlineKeyboardMarkup()
    back_markup.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="help_back"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='Markdown', reply_markup=back_markup)

# -----------------------------------------------------------
# അഡ്മിൻ കമാൻഡുകളുടെ യഥാർത്ഥ പ്രവർത്തനങ്ങൾ
# -----------------------------------------------------------

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text:
        bot.reply_to(message, "അയക്കേണ്ട മെസ്സേജ് കൂടി ടൈപ്പ് ചെയ്യുക. ഉദാഹരണത്തിന്: /broadcast Hello")
        return
    users = users_col.find({"banned": False})
    success, failed = 0, 0
    bot.reply_to(message, "ബ്രോഡ്കാസ്റ്റ് ആരംഭിച്ചു...")
    for u in users:
        try:
            bot.send_message(u['user_id'], msg_text)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
    bot.reply_to(message, f"✅ ബ്രോഡ്കാസ്റ്റ് പൂർത്തിയായി!\nവിജയകരം: {success}\nപരാജയം: {failed}")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = users_col.count_documents({})
    banned_users = users_col.count_documents({"banned": True})
    vid_count = videos_col.count_documents({})
    img_count = images_col.count_documents({})
    stk_count = stickers_col.count_documents({})
    text = f"📊 **ബോട്ട് സ്റ്റാറ്റിസ്റ്റിക്സ്**\n\n👥 ആകെ യൂസർമാർ: {total_users}\n🚫 ബാൻ ചെയ്യപ്പെട്ടവർ: {banned_users}\n\n📁 സേവ് ചെയ്ത വീഡിയോകൾ: {vid_count}\n🖼️ സേവ് ചെയ്ത ഫോട്ടോകൾ: {img_count}\n🎭 സേവ് ചെയ്ത സ്റ്റിക്കറുകൾ: {stk_count}"
    bot.reply_to(message, text)

@bot.message_handler(commands=['ban', 'unban'])
def admin_ban_unban(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        is_ban = '/ban' in message.text
        users_col.update_one({"user_id": target_id}, {"$set": {"banned": is_ban}}, upsert=True)
        status = "ബാൻ ചെയ്തു" if is_ban else "അൺബാൻ ചെയ്തു"
        bot.reply_to(message, f"✅ യൂസർ {target_id} -നെ വിജയകരമായി {status}.")
    except:
        bot.reply_to(message, "ശരിയായ ഫോർമാറ്റിൽ നൽകുക. ഉദാഹരണത്തിന്: /ban 12345678")

@bot.message_handler(commands=['maintenance'])
def admin_maintenance(message):
    if message.from_user.id != ADMIN_ID: return
    current = is_maintenance()
    new_state = not current
    settings_col.update_one({"_id": "maintenance"}, {"$set": {"status": new_state}}, upsert=True)
    status_text = "ഓൺ ആക്കി" if new_state else "ഓഫ് ആക്കി"
    bot.reply_to(message, f"⚙️ മെയിൻ്റനൻസ് മോഡ് {status_text}.")

# -----------------------------------------------------------
# Flask സെർവർ (Render Keep-Alive)
# -----------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Ultimate Bot is running with Admin Menu!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
