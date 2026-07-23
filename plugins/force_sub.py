from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID

# നിങ്ങളുടെ ചാനലിന്റെ യൂസർനെയിം അല്ലെങ്കിൽ ലിങ്ക് ഇവിടെ നൽകുക (ഉദാഹരണത്തിന്: "@YourChannelUsername")
# ചാനൽ ഐഡി അല്ലെങ്കിൽ യൂസർനെയിം താഴെ മാറ്റുക:
UPDATE_CHANNEL = "@YourChannelUsername" 

def setup(bot):
    
    def check_forcesub(message):
        user_id = message.from_user.id
        # അഡ്മിന് ഫോഴ്സ് സബ്സ്ക്രൈബ് ബാധകമല്ല
        if user_id == ADMIN_ID:
            return True
            
        try:
            # യൂസർ ചാനലിൽ ജോയിൻ ചെയ്തിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുന്നു
            member = bot.get_chat_member(UPDATE_CHANNEL, user_id)
            if member.status in ['left', 'kicked']:
                return False
            return True
        except Exception as e:
            print(f"ForceSub Error: {e}")
            # ചാനൽ സെറ്റിംഗ്സ് തെറ്റാണെങ്കിൽ ബോട്ട് ബ്ലോക്ക് ആവാതിരിക്കാൻ തൽക്കാലം True കൊടുക്കുന്നു
            return True

    # ഏതെങ്കിലും കമാൻഡ് അടിക്കുമ്പോൾ ഫോഴ്സ് സബ്സ്ക്രൈബ് പരിശോധിക്കുന്ന മിഡ്‌വെയർ/ഫംഗ്ഷൻ
    @bot.message_handler(func=lambda message: True, content_types=['text', 'video', 'photo', 'sticker'])
    def force_sub_check(message):
        # അഡ്മിൻ കമാൻഡുകൾക്കോ മറ്റ് ചാറ്റുകൾക്കോ ഇത് ബാധകമാക്കണ്ടെങ്കിൽ ഇവിടെ ഫിൽട്ടർ ചെയ്യാം
        if message.chat.type != 'private':
            return
            
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            return

        # സ്റ്റാർട്ട് കമാൻഡ് ആണെങ്കിൽ ആദ്യം അത് വർക്ക് ചെയ്യാൻ അനുവദിക്കുക
        if message.text and message.text.startswith('/start'):
            return

        if not check_forcesub(message):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}"))
            markup.add(InlineKeyboardButton("🔄 Try Again", callback_data="check_sub"))
            
            bot.reply_to(
                message, 
                "⚠️ **Access Denied!**\n\nTo use this bot, you must join our update channel first. Please join the channel and click 'Try Again'.", 
                reply_markup=markup, 
                parse_mode='Markdown'
            )
            # താഴെയുള്ള മറ്റ് ഹാൻഡ്‌ലറുകൾ വർക്ക് ചെയ്യാതിരിക്കാൻ ഇത് തടയും
            return True

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def callback_check_sub(call):
        user_id = call.from_user.id
        try:
            member = bot.get_chat_member(UPDATE_CHANNEL, user_id)
            if member.status in ['left', 'kicked']:
                bot.answer_callback_query(call.id, "❌ You have not joined the channel yet!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "✅ Thank you for joining! You can now use the bot.")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🎉 **Thank you!** You are now verified. You can use the bot commands now."
                )
        except Exception as e:
            bot.answer_callback_query(call.id, "⚠️ Error checking subscription. Please try again later.", show_alert=True)
