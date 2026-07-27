import datetime
import traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import get_fsub_data, is_user_requested

try:
    from database import users_col
except ImportError:
    users_col = None

def is_subscribed(bot, user_id, channel):
    if is_user_requested(user_id):
        return True
    try:
        status = bot.get_chat_member(channel, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

def setup(bot):
    @bot.message_handler(commands=['start'])
    def start_command(message):
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            
            # 1. പുതിയ യൂസറെ കൃത്യമായി ഡാറ്റാബേസിൽ സേവ് ചെയ്യുന്നു
            if users_col is not None:
                try:
                    user_exists = users_col.find_one({"user_id": user_id})
                    if not user_exists:
                        now = datetime.datetime.now()
                        users_col.insert_one({
                            "user_id": user_id,
                            "first_name": first_name,
                            "joined_date": now,
                            "banned": False
                        })
                except Exception as e:
                    print(f"Database Save Error: {e}")

            channels = get_fsub_data()
            not_joined = []
            
            if channels:
                for ch in channels:
                    if not is_subscribed(bot, user_id, ch["id"]):
                        not_joined.append(ch)

            # 2. Force Subscribe Check (ഇത് ഇൻലൈൻ ബട്ടൺ ആയി തന്നെ തുടരും)
            if not_joined:
                markup = InlineKeyboardMarkup(row_width=1)
                for idx, ch in enumerate(not_joined, start=1):
                    markup.add(InlineKeyboardButton(f"📢 Join Channel {idx}", url=ch["link"]))
                markup.add(InlineKeyboardButton("✅ I have requested / joined", callback_data="check_sub"))
                
                fsub_text = (
                    f"Hello <b>{first_name}</b>! 👋\n\n"
                    f"🚨 <b>Access Restricted!</b>\n"
                    f"To use WETFLIX Bot and access our media library, you must join our official update channels below:"
                )
                bot.reply_to(message, fsub_text, reply_markup=markup, parse_mode='HTML')
                return
                
            # 3. Main Welcome Message (ഇവിടെയാണ് താഴെ വരുന്ന വലിയ ബട്ടണുകൾ സെറ്റ് ചെയ്തിരിക്കുന്നത്)
            success_text = (
                f"⚡️ <b>Welcome to WETFLIX Ultimate Bot, {first_name}!</b> 🎉\n\n"
                f"Your ultimate automated media destination. Here is what you can do with me:\n\n"
                f"🖼 /image - Get high-quality random photos instantly.\n"
                f"🔞 /video - Discover and download trending videos.\n"
                f"🥵 /sticker - Access a massive collection of exclusive stickers.\n\n"
                f"💡 <i>Tip: Use the buttons below to explore features seamlessly!</i>"
            )
            
            # പുതിയ കിടിലൻ ബട്ടണുകൾ
            reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            btn1 = KeyboardButton("🍓 PHOTO")
            btn2 = KeyboardButton("🔞 VIDEO")
            btn3 = KeyboardButton("💀 STICKER")
            
            reply_markup.add(btn1, btn2, btn3)
            
            bot.reply_to(message, success_text, reply_markup=reply_markup, parse_mode='HTML')

        # എറർ ഉണ്ടെങ്കിൽ അത് ബോട്ടിൽ തന്നെ കാണിക്കാൻ
        except Exception as e:
            bot.reply_to(message, f"❌ An error occurred:\n`{e}`", parse_mode='Markdown')
            print(traceback.format_exc())

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def check_sub(call):
        try:
            channels = get_fsub_data()
            not_joined = []
            
            if channels:
                for ch in channels:
                    if not is_subscribed(bot, call.from_user.id, ch["id"]):
                        not_joined.append(ch)

            if not not_joined:
                bot.answer_callback_query(call.id, "✅ Verification successful!", show_alert=True)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                
                success_text = (
                    f"✅ <b>Verification Complete!</b>\n"
                    f"You can now fully use the bot. Type /start to begin."
                )
                bot.send_message(call.message.chat.id, success_text, parse_mode='HTML')
            else:
                bot.answer_callback_query(call.id, "❌ Please join all required channels first!", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data == "bot_features")
    def feature_callback(call):
        bot.answer_callback_query(
            call.id, 
            "WETFLIX Bot provides automated media delivery with secure channel protection and cool features!", 
            show_alert=True
        )
