from config import ADMIN_ID

# മെയിന്റനൻസ് സ്റ്റാറ്റസ് സൂക്ഷിക്കാനുള്ള ഗ്ലോബൽ വേരിയബിൾ
MAINTENANCE_CONFIG = {"status": False, "reason": "Bot is under scheduled maintenance. Please try again later."}

def setup(bot):

    @bot.message_handler(commands=['maintenance', 'maint'])
    def toggle_maintenance(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split(maxsplit=1)
        current_status = MAINTENANCE_CONFIG["status"]
        
        if len(args) < 2:
            status_text = "🟢 **ENABLED**" if current_status else "🔴 **DISABLED**"
            help_text = (
                "🛠️ **Maintenance Mode Manager:**\n\n"
                f"• **Current Status:** {status_text}\n"
                f"• **Reason:** `{MAINTENANCE_CONFIG['reason']}`\n\n"
                "👉 **Turn ON:** `/maintenance on <reason>`\n"
                "👉 **Turn OFF:** `/maintenance off`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        action = args[0].lower()
        sub_args = args[1].split(maxsplit=1)
        command = sub_args[0].lower()
        
        if command == "on":
            MAINTENANCE_CONFIG["status"] = True
            if len(sub_args) > 1:
                MAINTENANCE_CONFIG["reason"] = sub_args[1]
                
            bot.reply_to(message, "🛠️ **Maintenance Mode Enabled!** Users will now receive a maintenance notice.", parse_mode='Markdown')
            
        elif command == "off":
            MAINTENANCE_CONFIG["status"] = False
            bot.reply_to(message, "🟢 **Maintenance Mode Disabled!** Bot is fully operational for all users.", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Invalid argument. Use `/maintenance on [reason]` or `/maintenance off`.", parse_mode='Markdown')

    @bot.message_handler(func=lambda message: message.chat.type == 'private' and not message.text.startswith('/') and MAINTENANCE_CONFIG["status"])
    def maintenance_middleware(message):
        if message.from_user.id == ADMIN_ID:
            return False # അഡ്മിന് മെയിന്റനൻസ് ബാധകമല്ല, ബോട്ട് യൂസ് ചെയ്യാം
            
        # സാധാരണ യൂസർമാർക്ക് മെയിന്റനൻസ് മെസ്സേജ് അയക്കുന്നു
        bot.reply_to(
            message,
            f"🛠️ **Maintenance Notice:**\n\n{MAINTENANCE_CONFIG['reason']}",
            parse_mode='Markdown'
        )
        return True
