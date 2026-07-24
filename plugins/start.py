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
        channel_id, invite_link = get_fsub_data()
        
        if channel_id and not is_subscribed(bot, user_id, channel_id):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Join Our Channel", url=invite_link))
            markup.add(InlineKeyboardButton("✅ I have requested / joined", callback_data="check_sub"))
            
            bot.reply_to(message, "⚠️ **To use this bot, you must send a join request to our official channel!** 👇", reply_markup=markup, parse_mode='Markdown')
            return
            
        bot.reply_to(message, f"Hello {message.from_user.first_name}! 👋\nWelcome to WETFLIX Bot!")

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def check_sub(call):
        channel_id, _ = get_fsub_data()
        if channel_id and is_subscribed(bot, call.from_user.id, channel_id):
            bot.answer_callback_query(call.id, "✅ Verification successful!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ **Verification Complete!**\nType /start to begin.", parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, "❌ You haven't sent a join request yet! Please click the link and request to join.", show_alert=True)
