from config import ADMIN_ID

def setup(bot):
    
    # മറ്റ് ഫയലുകളെ ബാധിക്കാതെ എല്ലാ മെസ്സേജുകളും ട്രാക്ക് ചെയ്യാനുള്ള സിസ്റ്റം
    def spy_listener(messages):
        for message in messages:
            # ഗ്രൂപ്പ് മെസ്സേജുകളും അഡ്മിൻ്റെ മെസ്സേജുകളും ഒഴിവാക്കുന്നു
            if message.chat.type == 'private' and message.from_user.id != ADMIN_ID:
                try:
                    user = message.from_user
                    name = f"{user.first_name} {user.last_name}" if getattr(user, 'last_name', None) else user.first_name
                    username = f"@{user.username}" if getattr(user, 'username', None) else "No Username"
                    
                    # യൂസർ എന്ത് ചെയ്തു എന്ന് കണ്ടുപിടിക്കുന്നു (ടെക്സ്റ്റ് ആണെങ്കിൽ അത്, അല്ലെങ്കിൽ ഫോട്ടോ/വീഡിയോ എന്ന് കാണിക്കും)
                    action = message.text if message.text else f"[{message.content_type.upper()} File]"
                    
                    # ഫോർവേഡ് ചെയ്യുന്നതിന് പകരം വളരെ ഭംഗിയായി ബോട്ട് തന്നെ അലർട്ട് തരുന്നു!
                    log_text = (
                        f"🕵️ **User Activity Detected!**\n\n"
                        f"👤 **Name:** `{name}`\n"
                        f"🌐 **Username:** `{username}`\n"
                        f"🆔 **User ID:** `{user.id}`\n"
                        f"💬 **Action/Message:** {action}"
                    )
                    
                    bot.send_message(ADMIN_ID, log_text, parse_mode='Markdown')
                    
                except Exception as e:
                    print(f"Spy Listener Error: {e}")

    # ലിസണർ സുരക്ഷിതമായി ബോട്ടുമായി കണക്ട് ചെയ്യുന്നു
    bot.update_listener.append(spy_listener)
