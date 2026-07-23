from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['adminpoll', 'apoll'])
    def broadcast_poll(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split('|')
        if len(args) < 3:
            help_text = (
                "📊 **Admin Poll Broadcast Guide:**\n\n"
                "Use this command to send a poll to all database users.\n\n"
                "👉 **Usage:** `/apoll Question? | Option 1 | Option 2 | Option 3`\n"
                "👉 **Example:** `/apoll Do you like this bot? | Yes | No | Maybe`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        question = args[0].replace('/apoll', '').replace('/adminpoll', '').strip()
        options = [opt.strip() for opt in args[1:]]
        
        if len(options) < 2 or len(options) > 10:
            bot.reply_to(message, "❌ A poll must have between 2 and 10 options, separated by `|`.", parse_mode='Markdown')
            return
            
        status_msg = bot.reply_to(message, "📊 Starting poll broadcast...", parse_mode='Markdown')
        
        def run_poll_broadcast():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            for user in users:
                uid = user.get("user_id")
                try:
                    bot.send_poll(
                        chat_id=uid,
                        question=question,
                        options=options,
                        is_anonymous=False
                    )
                    success += 1
                    time.sleep(0.1)
                except Exception:
                    failed += 1
                    
            bot.edit_message_text(
                f"✅ **Poll Broadcast Completed!**\n\n"
                f"📊 **Question:** `{question}`\n"
                f"📤 **Sent Successfully:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_poll_broadcast).start()
