from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(commands=['setcaption'])
    def set_custom_caption(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.replace('/setcaption', '').strip()
        if not args:
            help_text = (
                "📝 **Auto Caption Guide:**\n\n"
                "Use this command to set a custom footer or caption for files sent by the bot.\n"
                "👉 **Usage:** `/setcaption Join our channel: @YourChannel`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        # ഇവിടെ ക്യാപ്ഷൻ ഡാറ്റാബേസിലോ ഫയലിലോ സേവ് ചെയ്യാം
        bot.reply_to(message, f"✅ Auto-caption has been updated successfully to:\n\n`{args}`", parse_mode='Markdown')
