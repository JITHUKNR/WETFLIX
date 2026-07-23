from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['pincast'])
    def pin_broadcast_message(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Please reply to any message or media with `/pincast` to broadcast and pin it for all users.", parse_mode='Markdown')
            return
            
        reply_msg = message.reply_to_message
        
        def run_pincast():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            status_msg = bot.send_message(message.chat.id, f"📌 Pin Broadcast started to {len(users)} users...")
            
            for user in users:
                uid = user.get("user_id")
                try:
                    # മെസ്സേജുകൾ അയക്കുന്നു
                    sent_msg = bot.copy_message(uid, message.chat.id, reply_msg.message_id)
                    # എല്ലാ യൂസർമാരുടെയും ചാറ്റിൽ അത് പിൻ ചെയ്യുന്നു
                    bot.pin_chat_message(uid, sent_msg.message_id)
                    success += 1
                    time.sleep(0.2) # ഫ്ലഡ് ലിമിറ്റ് ഒഴിവാക്കാൻ ചെറിയ ഇടവേള
                except Exception:
                    failed += 1
                    
            bot.edit_message_text(
                f"✅ **Pin Broadcast Completed!**\n\n"
                f"📤 **Success & Pinned:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_pincast).start()
