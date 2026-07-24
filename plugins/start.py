from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_fsub_data, is_user_requested

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
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        channels = get_fsub_data()
        
        not_joined = []
        if channels:
            for ch in channels:
                if not is_subscribed(bot, user_id, ch["id"]):
                    not_joined.append(ch)

        intro_text = (
            f"Hello **{first_name}**! 👋\n\n"
            f"**Welcome to the WETFLIX Bot!** 🎉\n\n"
            f"I am an advanced bot designed to provide you with random videos, stickers, and images.\n\n"
            f"To keep this service free, we require users to join our official channels. 👇"
        )

        if not_joined:
            markup = InlineKeyboardMarkup(row_width=1)
            # ഡാറ്റാബേസിലെ ചാനലുകളുടെ എണ്ണത്തിന് അനുസരിച്ച് ബട്ടണുകൾ ഉണ്ടാക്കുന്നു
            for idx, ch in enumerate(not_joined, start=1):
                markup.add(InlineKeyboardButton(f"📢 Join Channel {idx}", url=ch["link"]))
            
            markup.add(InlineKeyboardButton("✅ I have requested / joined", callback_data="check_sub"))
            
            bot.reply_to(message, intro_text, reply_markup=markup, parse_mode='Markdown')
            return
            
        success_text = (
            f"Hello **{first_name}**! 👋\n\n"
            f"Welcome back to WETFLIX Bot! 🎉\n\n"
            f"You can now use all my features. Please check the Menu."
        )
        bot.reply_to(message, success_text, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def check_sub(call):
        channels = get_fsub_data()
        not_joined = []
        
        if channels:
            for ch in channels:
                if not is_subscribed(bot, call.from_user.id, ch["id"]):
                    not_joined.append(ch)

        # എല്ലാ ചാനലിലും ജോയിൻ ചെയ്താൽ മാത്രം വെരിഫൈ ആകും
        if not not_joined:
            bot.answer_callback_query(call.id, "✅ Verification successful!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ **Verification Complete!**\nYou can now use the bot. Type /start to begin.", parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, "❌ You haven't sent join requests to all channels! Please request to join all of them.", show_alert=True)
