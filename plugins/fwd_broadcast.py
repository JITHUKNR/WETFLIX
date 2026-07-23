from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['fwdcast'])
    def forward_broadcast_message(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Please reply to any message or media with `/fwdcast` to forward it to all users.", parse_mode='Markdown')
            return
            
        reply_msg = message.reply_to_message
        
        # ബാക്ക്ഗ്രൗണ്ടിൽ ബ്രോഡ്കാസ്റ്റ് റൺ ചെയ്യാൻ ത്രെഡിങ് ഉപയോഗിക്കുന്നു
        def send_fwd():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            status_msg = bot.send_message(message.chat.id, f"🚀 Forward Broadcast started to {len(users)} users...")
            
            for user in users:
                uid = user.get("user_id")
                try:
                    bot.forward_message(uid, message.chat.id, reply_msg.message_id)
                    success += 1
                    time.sleep(0.1) # ടെലിഗ്രാം ഫ്ലഡ് ലിമിറ്റ് ഒഴിവാക്കാൻ ചെറിയൊരു ഇടവേള
                except Exception:
                    failed += 1
                    
            bot.edit_message_text(
                f"✅ **Forward Broadcast Completed!**\n\n"
                f"📤 **Success:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=send_fwd).start()
