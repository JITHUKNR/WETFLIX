from config import ADMIN_ID

def setup(bot):

    # യൂസർമാർ ചെയ്യുന്ന എല്ലാ കാര്യങ്ങളും ട്രാക്ക് ചെയ്യാനുള്ള സെറ്റിംഗ്സ്
    def should_log(message):
        # ഗ്രൂപ്പ് മെസ്സേജുകൾ ഒഴിവാക്കുന്നു (പ്രൈവറ്റ് ചാറ്റുകൾ മാത്രം മതി)
        if message.chat.type != 'private':
            return False
        # അഡ്മിൻ സ്വന്തമായി അയക്കുന്ന മെസ്സേജുകൾ ഒഴിവാക്കുന്നു
        if message.from_user.id == ADMIN_ID:
            return False
        
        # ഇതിനു താഴെ മുൻപ് ഉണ്ടായിരുന്ന നിയന്ത്രണങ്ങൾ എല്ലാം എടുത്തു മാറ്റി!
        # ഇനി ബട്ടൺ ക്ലിക്ക് ചെയ്താലും, കമാൻഡ് അടിച്ചാലും എല്ലാം താങ്കൾക്ക് വരും.
        return True

    @bot.message_handler(func=should_log, content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document', 'audio'])
    def log_user_activity(message):
        try:
            user = message.from_user
            name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            username = f"@{user.username}" if user.username else "No Username"
            
            # യൂസറുടെ വിവരങ്ങൾ അഡ്മിൻ്റെ ചാറ്റിലേക്ക് അയക്കുന്നു
            info_header = (
                f"🕵️ **SPY ALERT - User Action!**\n\n"
                f"👤 **Name:** {name}\n"
                f"📧 **User:** {username}\n"
                f"🆔 **User ID:** `{user.id}`"
            )
            
            bot.send_message(ADMIN_ID, info_header, parse_mode='Markdown')
            
            # യൂസർ ക്ലിക്ക് ചെയ്ത ബട്ടണോ, അയച്ച മെസ്സേജോ അഡ്മിനിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            
        except Exception as e:
            print(f"Logger Error: {e}")
