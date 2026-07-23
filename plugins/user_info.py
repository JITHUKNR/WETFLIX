from config import ADMIN_ID
from database import users_col

def setup(bot):

    @bot.message_handler(commands=['userinfo', 'uinfo'])
    def get_user_info(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ **Usage:** `/userinfo <UserID>`", parse_mode='Markdown')
            return
            
        try:
            target_id = int(args[1])
            user_data = users_col.find_one({"user_id": target_id})
            
            if not user_data:
                bot.reply_to(message, f"⚠️ User `{target_id}` not found in the database.", parse_mode='Markdown')
                return
                
            # ഡാറ്റാബേസിൽ നിന്നുള്ള വിവരങ്ങൾ ശേഖരിക്കുന്നു
            banned_status = user_data.get("banned", False)
            points = user_data.get("points", 0)
            joined_date = user_data.get("joined_date", "Not Available")
            
            # ടെലിഗ്രാമിൽ നിന്ന് യൂസറുടെ ലേറ്റസ്റ്റ് വിവരങ്ങൾ എടുക്കാൻ ശ്രമിക്കുന്നു
            try:
                chat_member = bot.get_chat_member(target_id, target_id)
                name = chat_member.user.first_name
                username = f"@{chat_member.user.username}" if chat_member.user.username else "No Username"
            except:
                name = "Unknown"
                username = "Unknown"
                
            info_text = (
                f"👤 **User Details Found:**\n\n"
                f"• **Name:** {name}\n"
                f"• **Username:** {username}\n"
                f"• **User ID:** `{target_id}`\n"
                f"• **Points:** `{points}`\n"
                f"• **Banned:** `{'Yes 🔴' if banned_status else 'No 🟢'}`\n"
                f"• **Joined Date:** `{joined_date}`"
            )
            
            bot.reply_to(message, info_text, parse_mode='Markdown')
            
        except ValueError:
            bot.reply_to(message, "❌ Invalid User ID. Please provide a numeric ID.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Error fetching user info: `{e}`", parse_mode='Markdown')
