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

        # Force Subscribe Check
        if not_joined:
            markup = InlineKeyboardMarkup(row_width=1)
            for idx, ch in enumerate(not_joined, start=1):
                markup.add(InlineKeyboardButton(f"📢 Join Channel {idx}", url=ch["link"]))
            markup.add(InlineKeyboardButton("✅ I have requested / joined", callback_data="check_sub"))
            
            fsub_text = (
                f"Hello **{first_name}**! 👋\n\n"
                f"🚨 **Access Restricted!**\n"
                f"To use WETFLIX Bot and access our media library, you must join our official update channels below:"
            )
            bot.reply_to(message, fsub_text, reply_markup=markup, parse_mode='Markdown')
            return
            
        # Attractive and Detailed Intro Message for Subscribed Users
        success_text = (
            f"⚡️ **Welcome to WETFLIX Ultimate Bot, {first_name}!** 🎉\n\n"
            f"Your ultimate automated media destination. Here is what you can do with me:\n\n"
            f"🖼 `/image` - Get high-quality random photos instantly.\n"
            f"🎬 `/video` - Discover and download trending videos.\n"
            f"🎭 `/sticker` - Access a massive collection of exclusive stickers.\n\n"
            f"💡 *Tip: Use the commands or the Menu button below to explore features seamlessly!*"
        )
        
        # Inline Buttons under the intro message
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✨ Bot Features", callback_data="bot_features"),
            InlineKeyboardButton("📢 Support Channel", url="https://t.me/+BP8pKgd_28ZmMDA0")
        )
        
        bot.reply_to(message, success_text, reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def check_sub(call):
        channels = get_fsub_data()
        not_joined = []
        
        if channels:
            for ch in channels:
                if not is_subscribed(bot, call.from_user.id, ch["id"]):
                    not_joined.append(ch)

        if not not_joined:
            bot.answer_callback_query(call.id, "✅ Verification successful!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ **Verification Complete!**\nYou can now use the bot. Type /start to begin.", parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, "❌ Please join all required channels first!", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data == "bot_features")
    def feature_callback(call):
        bot.answer_callback_query(
            call.id, 
            "WETFLIX Bot provides automated media delivery with secure channel protection and cool features!", 
            show_alert=True
        )
