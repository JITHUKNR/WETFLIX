from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(commands=['dm', 'sendto'])
    def admin_direct_message(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            help_text = (
                "✉️ **Admin Direct Message Guide:**\n\n"
                "Use this command to send a direct message to a specific user through the bot.\n\n"
                "👉 **Usage:** `/dm <UserID> <Message>`\n"
                "👉 **Example:** `/dm 123456789 Hello, your request has been approved!`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        try:
            target_id = int(args[1])
            dm_text = args[2]
            
            # യൂസർക്ക് മെസ്സേജ് അയക്കുന്നു
            bot.send_message(
                target_id,
                f"📬 **Message from Admin:**\n\n{dm_text}",
                parse_mode='Markdown'
            )
            
            bot.reply_to(message, f"✅ Message successfully sent to user `{target_id}`.", parse_mode='Markdown')
            
        except ValueError:
            bot.reply_to(message, "❌ Invalid User ID. Please provide a valid numeric ID.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send message: `{e}`", parse_mode='Markdown')
