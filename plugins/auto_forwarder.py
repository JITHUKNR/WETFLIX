from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['autofwd', 'forwarder'])
    def channel_auto_forwarder(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            help_text = (
                "🔄 **Channel Auto Forwarder Guide:**\n\n"
                "Reply to any post or media from your source channel with `/autofwd` to broadcast it instantly to all database users.\n\n"
                "👉 **Usage:** Reply to a message and type `/autofwd`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        reply_msg = message.reply_to_message
        
        def run_autofwd():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            status_msg = bot.send_message(message.chat.id, f"🚀 Forwarding post to {len(users)} users...")
            
            for user in users:
                uid = user.get("user_id")
                try:
                    bot.forward_message(uid, message.chat.id, reply_msg.message_id)
                    success += 1
                    time.sleep(0.1)
                except Exception:
                    failed += 1
                    
            bot.edit_message_text(
                f"✅ **Auto Forward Completed!**\n\n"
                f"📤 **Successfully Forwarded:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_autofwd).start()
