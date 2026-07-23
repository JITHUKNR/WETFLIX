from config import ADMIN_ID

def setup(bot):

    @bot.my_chat_member_handler()
    def chat_member_updated(message):
        try:
            new_chat_member = message.new_chat_member
            chat = message.chat
            
            # ബോട്ടിന്റെ സ്റ്റാറ്റസ് മാറ്റങ്ങൾ പരിശോധിക്കുന്നു
            if new_chat_member.user.id == bot.get_me().id:
                if new_chat_member.status in ['member', 'administrator']:
                    log_text = (
                        f"🤖 **Bot Added to New Group/Channel!**\n\n"
                        f"📌 **Name:** `{chat.title}`\n"
                        f"🆔 **ID:** `{chat.id}`\n"
                        f"👥 **Type:** `{chat.type}`\n"
                        f"👤 **Added By:** `{message.from_user.first_name}` (`{message.from_user.id}`)"
                    )
                    bot.send_message(ADMIN_ID, log_text, parse_mode='Markdown')
                    
                elif new_chat_member.status in ['left', 'kicked']:
                    log_text = (
                        f"🚫 **Bot Removed from Group/Channel!**\n\n"
                        f"📌 **Name:** `{chat.title}`\n"
                        f"🆔 **ID:** `{chat.id}`\n"
                        f"👥 **Type:** `{chat.type}`"
                    )
                    bot.send_message(ADMIN_ID, log_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Chat Logger Error: {e}")
