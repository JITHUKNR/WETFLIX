from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from config import ADMIN_ID
from database import users_col

def setup(bot):

    @bot.message_handler(commands=['broadcast'])
    def admin_broadcast(message):
        if message.from_user.id != ADMIN_ID: return
        
        # ഉദാഹരണ ഫോർമാറ്റ് പരിശോധിക്കുന്നു
        # ഫോർമാറ്റ്: /broadcast Message Text | Button Name - https://t.me/...
        help_text = (
            "📢 **Broadcast Guide:**\n\n"
            "Simple text broadcast:\n"
            "`/broadcast Hello everyone!`\n\n"
            "Broadcast with an Inline Button:\n"
            "`/broadcast Check out our new update! | Join Channel - https://t.me/YourChannel`"
        )
        
        raw_text = message.text.replace('/broadcast', '').strip()
        if not raw_text:
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        msg_text = raw_text
        btn_text = None
        btn_url = None

        # ബട്ടൺ നൽകിയിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുന്നു (| ചിഹ്നം വെച്ച് വേർതിരിക്കുന്നു)
        if "|" in raw_text:
            parts = raw_text.split("|", 1)
            msg_text = parts[0].strip()
            button_part = parts[1].strip()
            
            if "-" in button_part:
                btn_parts = button_part.split("-", 1)
                btn_text = btn_parts[0].strip()
                btn_url = btn_parts[1].strip()

        users = users_col.find({"banned": False})
        success, failed = 0, 0
        
        status_msg = bot.reply_to(message, "🚀 Broadcast started...")

        markup = None
        if btn_text and btn_url:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(btn_text, url=btn_url))

        for u in users:
            try:
                if markup:
                    bot.send_message(u['user_id'], msg_text, reply_markup=markup, parse_mode='Markdown')
                else:
                    bot.send_message(u['user_id'], msg_text, parse_mode='Markdown')
                success += 1
                time.sleep(0.05) # ടെലിഗ്രാം സ്പാം തടയാൻ
            except:
                failed += 1
                
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"✅ **Broadcast Completed!**\n\nSuccessful: {success}\nFailed: {failed}",
            parse_mode='Markdown'
        )
