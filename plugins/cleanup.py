from config import ADMIN_ID
from database import users_col
import threading

def setup(bot):

    @bot.message_handler(commands=['cleanup', 'cleandb'])
    def cleanup_database_check(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        try:
            # ബ്ലോക്ക് ചെയ്ത യൂസർമാരുടെ എണ്ണം പരിശോധിക്കുന്നു
            banned_count = users_col.count_documents({"banned": True})
            total_users = users_col.count_documents({})
            
            help_text = (
                "🧹 **Database Cleanup Tool:**\n\n"
                f"• **Total Users in DB:** `{total_users}`\n"
                f"• **Banned/Inactive Flagged:** `{banned_count}`\n\n"
                "Use `/cleanup confirm` to remove flagged/banned users from the database permanently."
            )
            
            args = message.text.split()
            if len(args) > 1 and args[1] == "confirm":
                status_msg = bot.reply_to(message, "🧹 Cleaning up database, please wait...")
                
                # ഡാറ്റാബേസിൽ നിന്ന് ബാൻ ചെയ്തവരെ ഡിലീറ്റ് ചെയ്യുന്നു
                result = users_col.delete_many({"banned": True})
                
                bot.edit_message_text(
                    f"✅ **Database Cleanup Completed!**\n\n"
                    f"🗑️ **Removed Users:** `{result.deleted_count}`\n"
                    f"✨ **Remaining Users:** `{users_col.count_documents({})}`",
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(message, help_text, parse_mode='Markdown')
                
        except Exception as e:
            bot.reply_to(message, f"❌ Error during cleanup: `{e}`", parse_mode='Markdown')
