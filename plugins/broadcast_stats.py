from config import ADMIN_ID
from database import users_col
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['bcast', 'broadcast'])
    def advanced_broadcast(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            help_text = (
                "📢 **Broadcast Analytics Guide:**\n\n"
                "Reply to any message with `/bcast` to start a tracked broadcast with live progress reporting.\n\n"
                "👉 **Usage:** Reply to a message and type `/bcast`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        reply_msg = message.reply_to_message
        
        def run_analytics_broadcast():
            users = list(users_col.find({"banned": {"$ne": True}}))
            total_users = len(users)
            
            success = 0
            blocked = 0
            failed = 0
            
            # പ്രോഗ്രസ്സ് കാണിക്കാൻ ഒരു സ്റ്റാറ്റസ് മെസ്സേജ് അയക്കുന്നു
            status_msg = bot.send_message(
                message.chat.id,
                f"🚀 **Broadcast Started...**\n\n"
                f"👥 Total Target: `{total_users}`\n"
                f"✅ Success: `0`\n"
                f"🚫 Blocked/Inactive: `0`\n"
                f"❌ Failed: `0`",
                parse_mode='Markdown'
            )
            
            start_time = time.time()
            
            for index, user in enumerate(users, start=1):
                uid = user.get("user_id")
                try:
                    bot.copy_message(uid, message.chat.id, reply_msg.message_id)
                    success += 1
                except Exception as e:
                    error_str = str(e).lower()
                    if "blocked" in error_str or "deactivated" in error_str or "chat not found" in error_str:
                        blocked += 1
                        # ഓട്ടോമാറ്റിക് ആയി ഡാറ്റാബേസിൽ യൂസറെ ബാൻ ആയി മാർക്ക് ചെയ്യാം
                        users_col.update_one({"user_id": uid}, {"$set": {"banned": True}})
                    else:
                        failed += 1
                
                # ഫ്ലഡ് ലിമിറ്റ് ഒഴിവാക്കാനും ലൈവ് അപ്ഡേറ്റ് നൽകാനും ചെറിയ ഇടവേള
                time.sleep(0.1)
                
                # ഓരോ 20 യൂസർമാർക്ക് കഴിയുമ്പോഴും സ്റ്റാറ്റസ് മെസ്സേജ് അപ്ഡേറ്റ് ചെയ്യുന്നു
                if index % 20 == 0 or index == total_users:
                    try:
                        bot.edit_message_text(
                            f"📢 **Broadcast in Progress...**\n\n"
                            f"👥 Progress: `{index}/{total_users}`\n"
                            f"✅ Success: `{success}`\n"
                            f"🚫 Blocked/Inactive: `{blocked}`\n"
                            f"❌ Failed: `{failed}`",
                            message.chat.id,
                            status_msg.message_id,
                            parse_mode='Markdown'
                        )
                    except Exception:
                        pass
                        
            elapsed_time = round(time.time() - start_time, 2)
            
            # ഫൈനൽ റിപ്പോർട്ട്
            bot.edit_message_text(
                f"✅ **Broadcast Completed Successfully!**\n\n"
                f"⏱️ Time Taken: `{elapsed_time} seconds`\n"
                f"👥 Total Reach: `{total_users}`\n"
                f"✅ Delivered: `{success}`\n"
                f"🚫 Blocked Bot: `{blocked}`\n"
                f"❌ Failed: `{failed}`",
                message.chat.id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_analytics_broadcast).start()
