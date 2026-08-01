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
            
            parts = message.text.split()
            referrer_id = None
            if len(parts) > 1 and parts[1].startswith("REF_"):
                try:
                    referrer_id = int(parts[1].split("_")[1])
                except:
                    pass
            
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
                        
                        if referrer_id and referrer_id != user_id:
                            referrer_data = users_col.find_one({"user_id": referrer_id})
                            if referrer_data:
                                new_refs = referrer_data.get("referrals", 0) + 1
                                
                                if new_refs >= 5:
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
                
            success_text = (
                f"⚡️ <b>Welcome to WETFLIX Ultimate Bot, {first_name}!</b> 🎉\n\n"
                f"Your ultimate automated media destination. Here is what you can do with me:\n\n"
                f"🖼 /image - Get high-quality random photos instantly.\n"
                f"🔞 /video - Discover and download trending videos.\n"
                f"🥵 /sticker - Access a massive collection of exclusive stickers.\n"
                f"🎁 /refer - Invite 5 friends and get NO TIME LIMIT access!\n\n"
                f"💡 <i>Tip: Use the buttons below to explore features seamlessly!</i>"
            )
            
            reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            btn1 = KeyboardButton("🍓 PHOTO")
            btn2 = KeyboardButton("🔞 VIDEO")
            btn3 = KeyboardButton("💀 STICKER")
            btn4 = KeyboardButton("💅🏻 ANIME")
            btn6 = KeyboardButton("👤 MY PROFILE")
            btn7 = KeyboardButton("💥 BOOM") # ⚠️ ഇവിടെ BOOM ബട്ടൺ ചേർത്തു ⚠️
            
            # ബട്ടണുകൾ ഭംഗിയായി അടുക്കിവെക്കുന്നു
            reply_markup.row(btn1, btn2)
            reply_markup.row(btn3, btn4)
            reply_markup.row(btn7) # നടുക്കായി കൊടുത്തിട്ടുണ്ട്
            reply_markup.row(btn6)
            
            bot.reply_to(message, success_text, reply_markup=reply_markup, parse_mode='HTML')

        except Exception as e:
            bot.reply_to(message, f"❌ An error occurred:\n`{e}`", parse_mode='Markdown')
            print(traceback.format_exc())

    # റഫറൽ മെസ്സേജ് അയക്കുന്നതിനുള്ള ഫംഗ്ഷൻ വേർതിരിച്ചു
    def send_referral_msg(chat_id, user_id):
        try:
            bot_info = bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start=REF_{user_id}"
            
            user_data = users_col.find_one({"user_id": user_id}) if users_col is not None else None
            current_refs = user_data.get("referrals", 0) if user_data else 0
            
            text = (
                f"🎁 <b>Invite Friends & Get VIP Access!</b>\n\n"
                f"Share your unique link with friends. If <b>5 people</b> join using your link, "
                f"you will get <b>7 Days of VIP Access</b> (No waiting time for videos!).\n\n"
                f"📊 <b>Your Progress:</b> {current_refs} / 5 Referrals\n\n"
                f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>"
            )
            bot.send_message(chat_id, text, parse_mode='HTML')
        except Exception as e:
            print(f"Referral Error: {e}")

    @bot.message_handler(commands=['refer'])
    def refer_command(message):
        send_referral_msg(message.chat.id, message.from_user.id)


    @bot.message_handler(func=lambda message: message.text == "👤 MY PROFILE")
    def profile_command(message):
        try:
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
            
            user_data = users_col.find_one({"user_id": user_id}) if users_col is not None else None
            
            if not user_data:
                bot.reply_to(message, "❌ Profile not found. Please type /start to register.")
                return

            joined_date = user_data.get("joined_date", datetime.datetime.now()).strftime("%Y-%m-%d")
            referrals = user_data.get("referrals", 0)
            vip_until = user_data.get("vip_until")
            
            is_vip = False
            vip_status = "🔴 Free User"
            
            if vip_until and isinstance(vip_until, datetime.datetime) and datetime.datetime.now() < vip_until:
                is_vip = True
                vip_status = f"🟢 VIP User (Valid till {vip_until.strftime('%d-%m-%Y')})"
            
            remaining_refs = max(0, 5 - referrals)
            if is_vip:
                ref_text = f"🎉 You are a Premium VIP Member!"
            else:
                ref_text = f"⚠️ Need {remaining_refs} more referrals for VIP."

            profile_text = (
                f"👤 **YOUR WETFLIX PROFILE** 👤\n\n"
                f"📛 **Name:** `{first_name}`\n"
                f"📧 **Username:** {username}\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"📅 **Joined On:** `{joined_date}`\n\n"
                f"👑 **Account Status:** {vip_status}\n"
                f"👥 **Total Referrals:** `{referrals}`\n"
                f"🎯 **Goal:** {ref_text}\n\n"
                f"💡 _Tip: Click 🎁 REFER to invite friends and get VIP instantly!_"
            )

            # പുതിയ ഇൻലൈൻ ബട്ടൺ ഉണ്ടാക്കുന്നു
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🎁 REFER & EARN VIP", callback_data="show_referral"))
            
            # bot.reply_to ൽ reply_markup കൂടി ചേർക്കുന്നു
            bot.reply_to(message, profile_text, parse_mode='Markdown', reply_markup=markup)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Error loading profile: `{e}`", parse_mode='Markdown')
            print(f"Profile Error: {e}")

    # ഇൻലൈൻ റഫർ ബട്ടൺ വർക്ക് ചെയ്യാൻ
    @bot.callback_query_handler(func=lambda call: call.data == "show_referral")
    def show_referral_callback(call):
        send_referral_msg(call.message.chat.id, call.from_user.id)
        bot.answer_callback_query(call.id)

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
                
                first_name = call.from_user.first_name
                success_text = (
                    f"⚡️ <b>Welcome to WETFLIX Ultimate Bot, {first_name}!</b> 🎉\n\n"
                    f"Your ultimate automated media destination. Here is what you can do with me:\n\n"
                    f"🖼 /image - Get high-quality random photos instantly.\n"
                    f"🔞 /video - Discover and download trending videos.\n"
                    f"🥵 /sticker - Access a massive collection of exclusive stickers.\n"
                    f"🎁 /refer - Invite 5 friends and get NO TIME LIMIT access!\n\n"
                    f"💡 <i>Tip: Use the buttons below to explore features seamlessly!</i>"
                )
                
                reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                btn1 = KeyboardButton("🍓 PHOTO")
                btn2 = KeyboardButton("🔞 VIDEO")
                btn3 = KeyboardButton("💀 STICKER")
                btn4 = KeyboardButton("💅🏻 ANIME")
                btn6 = KeyboardButton("👤 MY PROFILE")
                btn7 = KeyboardButton("💥 BOOM") # ⚠️ ഇവിടെയും BOOM ബട്ടൺ ചേർത്തു ⚠️
                
                reply_markup.row(btn1, btn2)
                reply_markup.row(btn3, btn4)
                reply_markup.row(btn7) 
                reply_markup.row(btn6) # btn5 ഒഴിവാക്കി btn6 (പ്രൊഫൈൽ) മാത്രം കൊടുത്തു

                
                bot.send_message(call.message.chat.id, success_text, reply_markup=reply_markup, parse_mode='HTML')
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
