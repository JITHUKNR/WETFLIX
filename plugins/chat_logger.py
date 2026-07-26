from config import ADMIN_ID

def setup(bot):

    @bot.my_chat_member_handler()
    def chat_member_updated(message):
        try:
            new_chat_member = message.new_chat_member
            chat = message.chat
            
            # ബോട്ടിന്റെ സ്റ്റാറ്റസ് മാറ്റങ്ങൾ പരിശോധിക്കുന്നു
            if new_chat_member.user.id == bot.get_me().id:
                
                # ബോട്ട് ആഡ് ചെയ്യപ്പെടുമ്പോൾ അല്ലെങ്കിൽ അൺബ്ലോക്ക് ചെയ്യുമ്പോൾ
                if new_chat_member.status in ['member', 'administrator']:
                    if chat.type == 'private':
                        name = getattr(chat, 'first_name', 'Unknown User')
                        username = f"@{chat.username}" if chat.username else "No Username"
                        log_text = (
                            f"✅ **User Unblocked / Started Bot!**\n\n"
                            f"👤 **Name:** `{name}`\n"
                            f"🌐 **Username:** `{username}`\n"
                            f"🆔 **User ID:** `{chat.id}`\n"
                            f"👥 **Type:** `Private Chat`"
                        )
                    else:
                        log_text = (
                            f"🤖 **Bot Added to New Group/Channel!**\n\n"
                            f"📌 **Name:** `{chat.title}`\n"
                            f"🆔 **ID:** `{chat.id}`\n"
                            f"👥 **Type:** `{chat.type}`\n"
                            f"👤 **Added By:** `{message.from_user.first_name}` (`{message.from_user.id}`)"
                        )
                    bot.send_message(ADMIN_ID, log_text, parse_mode='Markdown')
                    
                # ബോട്ട് റിമൂവ് ചെയ്യുമ്പോൾ അല്ലെങ്കിൽ ബ്ലോക്ക് ചെയ്യുമ്പോൾ
                elif new_chat_member.status in ['left', 'kicked']:
                    if chat.type == 'private':
                        name = getattr(chat, 'first_name', 'Unknown User')
                        username = f"@{chat.username}" if chat.username else "No Username"
                        log_text = (
                            f"🚫 **User Blocked the Bot!**\n\n"
                            f"👤 **Name:** `{name}`\n"
                            f"🌐 **Username:** `{username}`\n"
                            f"🆔 **User ID:** `{chat.id}`\n"
                            f"👥 **Type:** `Private Chat`"
                        )
                    else:
                        log_text = (
                            f"🚫 **Bot Removed from Group/Channel!**\n\n"
                            f"📌 **Name:** `{chat.title}`\n"
                            f"🆔 **ID:** `{chat.id}`\n"
                            f"👥 **Type:** `{chat.type}`\n"
                            f"👤 **Removed By:** `{message.from_user.first_name}`"
                        )
                    bot.send_message(ADMIN_ID, log_text, parse_mode='Markdown')
                    
        except Exception as e:
            print(f"Chat Logger Error: {e}")
