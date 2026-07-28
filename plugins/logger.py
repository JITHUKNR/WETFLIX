from config import ADMIN_ID

def setup(bot):

    # എന്തിനൊക്കെ നോട്ടിഫിക്കേഷൻ വരണം, വരരുത് എന്ന് തീരുമാനിക്കുന്ന ഭാഗം
    def should_log(message):
        # ഗ്രൂപ്പ് മെസ്സേജുകൾ ഒഴിവാക്കുന്നു
        if message.chat.type != 'private':
            return False
        # അഡ്മിൻ അയക്കുന്ന മെസ്സേജുകൾ ഒഴിവാക്കുന്നു
        if message.from_user.id == ADMIN_ID:
            return False
        # ബട്ടണുകളും കമാൻഡുകളും ഒഴിവാക്കുന്നു (അല്ലെങ്കിൽ അഡ്മിൻ്റെ ഇൻബോക്സ് നിറയും)
        if message.text:
            if message.text in ["🍓 PHOTO", "🔞 VIDEO", "💀 STICKER", "💅🏻 ANIME", "🎁 REFER"]:
                return False
            if message.text.startswith('/'):
                return False
        return True

    @bot.message_handler(func=should_log, content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document', 'audio'])
    def log_user_activity(message):
        try:
            user = message.from_user
            name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            username = f"@{user.username}" if user.username else "No Username"
            
            # യൂസറുടെ വിവരങ്ങൾ അഡ്മിൻ്റെ ചാറ്റിലേക്ക് അയക്കുന്നു
            info_header = (
                f"🕵️ **SPY ALERT - New Message!**\n\n"
                f"👤 **Name:** {name}\n"
                f"📧 **User:** {username}\n"
                f"🆔 **User ID:** `{user.id}`"
            )
            
            bot.send_message(ADMIN_ID, info_header, parse_mode='Markdown')
            
            # യൂസർ അയച്ച ഒറിജിനൽ മെസ്സേജും അഡ്മിനിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            
        except Exception as e:
            print(f"Logger Error: {e}")
