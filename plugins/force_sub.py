from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import settings_col

def setup(bot):
    
    # ഡാറ്റാബേസിൽ നിന്ന് ഫോഴ്സ് സബ്സ്ക്രൈബ് ചാനലുകൾ എടുക്കാൻ
    def get_forced_channels():
        data = settings_col.find_one({"_id": "forced_channels"})
        return data.get("channels", []) if data else []

    # ഫോഴ്സ് സബ്സ്ക്രൈബ് ചെക്ക് ചെയ്യുന്ന ഫംഗ്ഷൻ
    @bot.message_handler(func=lambda message: True, content_types=['text', 'video', 'photo', 'sticker'])
    def force_sub_check(message):
        if message.chat.type != 'private':
            return
            
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            return

        if message.text and message.text.startswith('/start'):
            return

        channels = get_forced_channels()
        if not channels:
            return # ചാനലുകൾ സെറ്റ് ചെയ്തിട്ടില്ലെങ്കിൽ തടസ്സമില്ലാതെ വർക്ക് ചെയ്യും

        not_joined_channels = []
        
        for ch in channels:
            try:
                member = bot.get_chat_member(ch, user_id)
                if member.status in ['left', 'kicked']:
                    not_joined_channels.append(ch)
            except Exception as e:
                print(f"Error checking channel {ch}: {e}")

        if not_joined_channels:
            markup = InlineKeyboardMarkup()
            for ch in not_joined_channels:
                # ചാനലിന്റെ ലിങ്ക് അല്ലെങ്കിൽ യൂസർനെയിം വെച്ച് ബട്ടൺ ഉണ്ടാക്കുന്നു
                clean_ch = ch.replace('@', '')
                markup.add(InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{clean_ch}"))
            
            markup.add(InlineKeyboardButton("🔄 Try Again", callback_data="check_sub"))
            
            bot.reply_to(
                message, 
                "⚠️ **Subscription Required!**\n\nTo use this bot, you must join our update channels first. Please join them and click 'Try Again'.", 
                reply_markup=markup, 
                parse_mode='Markdown'
            )
            return True

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def callback_check_sub(call):
        user_id = call.from_user.id
        channels = get_forced_channels()
        still_not_joined = False

        for ch in channels:
            try:
                member = bot.get_chat_member(ch, user_id)
                if member.status in ['left', 'kicked']:
                    still_not_joined = True
                    break
            except:
                pass

        if still_not_joined:
            bot.answer_callback_query(call.id, "❌ You have not joined all required channels yet!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "✅ Verified successfully! You can now use the bot.", show_alert=True)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎉 **Thank you!** You are now verified. You can use the bot commands now."
            )

    # അഡ്മിന് ചാനലുകൾ മാനേജ് ചെയ്യാനുള്ള കമാൻഡുകൾ
    @bot.message_handler(commands=['addchannel'])
    def add_channel(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "Usage: `/addchannel @ChannelUsername`", parse_mode='Markdown')
                return
            
            ch_username = args[1]
            channels = get_forced_channels()
            if ch_username not in channels:
                channels.append(ch_username)
                settings_col.update_one({"_id": "forced_channels"}, {"$set": {"channels": channels}}, upsert=True)
                bot.reply_to(message, f"✅ Channel `{ch_username}` added to Force Subscribe list successfully.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"⚠️ Channel `{ch_username}` is already in the list.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"Error: {e}")

    @bot.message_handler(commands=['removechannel'])
    def remove_channel(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "Usage: `/removechannel @ChannelUsername`", parse_mode='Markdown')
                return
            
            ch_username = args[1]
            channels = get_forced_channels()
            if ch_username in channels:
                channels.remove(ch_username)
                settings_col.update_one({"_id": "forced_channels"}, {"$set": {"channels": channels}}, upsert=True)
                bot.reply_to(message, f"✅ Channel `{ch_username}` removed from Force Subscribe list.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"⚠️ Channel `{ch_username}` not found in the list.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"Error: {e}")

    @bot.message_handler(commands=['listchannels'])
    def list_channels(message):
        if message.from_user.id != ADMIN_ID: return
        channels = get_forced_channels()
        if not channels:
            bot.reply_to(message, "📂 No force subscribe channels added yet.")
        else:
            ch_list = "\n".join([f"• {ch}" for ch in channels])
            bot.reply_to(message, f"📢 **Forced Channels List:**\n\n{ch_list}", parse_mode='Markdown')
