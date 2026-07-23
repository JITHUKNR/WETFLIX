from config import ADMIN_ID
from database import users_col

def setup(bot):

    @bot.message_handler(commands=['ban'])
    def ban_user(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/ban UserID`", parse_mode='Markdown')
            return
            
        try:
            target_id = int(args[1])
            
            # യൂസറെ ബാൻ ചെയ്തതായി ഡാറ്റാബേസിൽ അപ്ഡേറ്റ് ചെയ്യുന്നു
            result = users_col.update_one({"user_id": target_id}, {"$set": {"banned": True}})
            
            if result.modified_count > 0 or result.matched_count > 0:
                bot.reply_to(message, f"🚫 User `{target_id}` has been banned successfully.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"⚠️ User `{target_id}` not found in database.", parse_mode='Markdown')
        except ValueError:
            bot.reply_to(message, "❌ Invalid User ID. Please provide a numeric ID.")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

    @bot.message_handler(commands=['unban'])
    def unban_user(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/unban UserID`", parse_mode='Markdown')
            return
            
        try:
            target_id = int(args[1])
            
            # യൂസറുടെ ബാൻ ഒഴിവാക്കുന്നു
            result = users_col.update_one({"user_id": target_id}, {"$set": {"banned": False}})
            
            if result.modified_count > 0 or result.matched_count > 0:
                bot.reply_to(message, f"✅ User `{target_id}` has been unbanned successfully.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"⚠️ User `{target_id}` not found in database.", parse_mode='Markdown')
        except ValueError:
            bot.reply_to(message, "❌ Invalid User ID. Please provide a numeric ID.")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")
