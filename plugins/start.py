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
            now = datetime.datetime.now()
            
            # റഫറൽ വഴി വന്നതാണോ എന്ന് നോക്കുന്നു
            parts = message.text.split()
            referrer_id = None
            if len(parts) > 1 and parts[1].startswith("REF_"):
                try:
                    referrer_id = int(parts[1].split("_")[1])
                except:
                    pass
            
            # 1. പുതിയ യൂസറെ കൃത്യമായി ഡാറ്റാബേസിൽ സേവ് ചെയ്യുന്നു
            if users_col is not None:
                try:
                    user_exists = users_col.find_one({"user_id": user_id})
                    if not user_exists:
                        users_col.insert_one({
                            "user_id": user_id,
                            "first_name": first_name,
                            "joined_date": now,
                            "banned": False,
                            "referrals": 0,
                            "vip_until": None,
                            "referred_by": referrer_id
                        })
                        
                        # റഫർ ചെയ്ത ആൾക്ക് പോയിൻ്റ് കൊടുക്കുന്നു
                        if referrer_id and referrer_id != user_id:
                            referrer_data = users_col.find_one({"user_id": referrer_id})
                            if referrer_data:
                                new_refs = referrer_data.get("referrals", 0) + 1
                                
                                if new_refs >= 5:
                                    # 5 പേരായി! 7 ദിവസത്തെ VIP കൊടുക്കുന്നു
                                    vip_time = now + datetime.timedelta(days=7)
                                    users_col.update_one({"user_id": referrer_id}, {"$set": {"referrals": 0, "vip_until": vip_time}})
                                    try:
                                        bot.send_message(referrer_id, "🎉 **Congratulations!** 5 friends joined using your link.\n\n👑 **You are now a VIP for 7 Days!** You have NO WAITING TIME for videos! 🚀", parse_mode="Markdown")
                                    except:
                                        pass
                                else:
                                    users_col.update_one({"user_id": referrer_id}, {"$set": {"referrals": new_refs}})
                                    try:
                                        bot.send_message(referrer_id, f"🎉 Someone joined using your link! You now have **{new_refs}/5** referrals for VIP.", parse_mode="Markdown")
                                    except:
                                        pass
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
                
            # 3. Main Welcome Message 
            success_text = (
                f"⚡️ <b>Welcome to WETFLIX Ultimate Bot, {first_name}!</b> 🎉\n\n"
                f"Your ultimate automated media destination. Here is what you can do with me:\n\n"
                f"🖼 /image - Get high-quality random photos instantly.\n"
                f"🔞 /video - Discover and download trending videos.\n"
                f"🥵 /sticker - Access a massive collection of exclusive stickers.\n"
                f"🎁 /refer - Invite 5 friends and get NO TIME LIMIT access!\n\n"
                f"💡 <i>Tip: Use the buttons below to explore features seamlessly!</i>"
            )
            
            # പുതിയ കിടിലൻ ബട്ടണുകൾ
            reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            btn1 = KeyboardButton("🍓 PHOTO")
            btn2 = KeyboardButton("🔞 VIDEO")
            btn3 = KeyboardButton("💀 STICKER")
            btn4 = KeyboardButton("💅🏻 ANIME")
            btn5 = KeyboardButton("🎁 REFER")
            
            reply_markup.add(btn1, btn2, btn3, btn4, btn5)
            
            bot.reply_to(message, success_text, reply_markup=reply_markup, parse_mode='HTML')

        except Exception as e:
            bot.reply_to(message, f"❌ An error occurred:\n`{e}`", parse_mode='Markdown')
            print(traceback.format_exc())

    # റഫറൽ ലിങ്ക് ജനറേറ്റ് ചെയ്യാനുള്ള കമാൻഡ്
    @bot.message_handler(commands=['refer'])
    @bot.message_handler(func=lambda message: message.text == "🎁 REFER")
    def refer_command(message):
        try:
            bot_info = bot.get_me()
            user_id = message.from_user.id
            ref_link = f"https://t.me/{bot_info.username}?start=REF_{user_id}"
            
            user_data = users_col.find_one({"user_id": user_id}) if users_col else None
            current_refs = user_data.get("referrals", 0) if user_data else 0
            
            # Markdown പ്രശ്നം ഒഴിവാക്കാൻ HTML ഉപയോഗിക്കുന്നു
            text = (
                f"🎁 <b>Invite Friends & Get VIP Access!</b>\n\n"
                f"Share your unique link with friends. If <b>5 people</b> join using your link, "
                f"you will get <b>7 Days of VIP Access</b> (No waiting time for videos!).\n\n"
                f"📊 <b>Your Progress:</b> {current_refs} / 5 Referrals\n\n"
                f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>"
            )
            bot.reply_to(message, text, parse_mode='HTML')
            
        except Exception as e:
            # എറർ എന്താണെന്ന് കൃത്യമായി കാണിക്കാൻ ഇത് സഹായിക്കും
            bot.reply_to(message, f"❌ Error generating invite link: `{e}`", parse_mode='Markdown')
            print(f"Referral Error: {e}")

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
