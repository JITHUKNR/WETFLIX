from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['apin', 'adminpin'])
    def admin_pin_message(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            help_text = (
                "📌 **Admin Pin Guide:**\n\n"
                "Reply to any message with `/apin` to broadcast and pin it across all users, or use it directly to pin in the admin chat.\n\n"
                "👉 **Usage:** Reply to a message and type `/apin`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        reply_msg = message.reply_to_message
        
        def run_global_pin():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            status_msg = bot.send_message(message.chat.id, f"📌 Global Pinning started to {len(users)} users...")
            
            for user in users:
                uid = user.get("user_id")
                try:
                    sent_msg = bot.copy_message(uid, message.chat.id, reply_msg.message_id)
                    bot.pin_chat_message(uid, sent_msg.message_id)
                    success += 1
                    time.sleep(0.1)
                except Exception:
                    failed += 1
                    
            bot.edit_message_text(
                f"✅ **Global Pin Completed!**\n\n"
                f"📌 **Successfully Pinned:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_global_pin).start()
