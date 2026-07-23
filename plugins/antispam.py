from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text'])
    def anti_spam_filter(message):
        user_id = message.from_user.id
        
        # അഡ്മിൻമാരുടെ മെസ്സേജുകൾക്ക് ഇത് ബാധകമല്ല
        if user_id == ADMIN_ID:
            return

        text = message.text.lower() if message.text else ""
        
        # ലിങ്കുകൾ അടങ്ങിയിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുന്നു (t.me അല്ലെങ്കിൽ http)
        if "t.me/" in text or "http://" in text or "https://" in text or "www." in text:
            try:
                # സ്പാം മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
                bot.delete_message(message.chat.id, message.message_id)
                
                # യൂസർക്ക് വാണിംഗ് നൽകുന്നു
                warning_msg = bot.send_message(
                    message.chat.id, 
                    f"⚠️ Hey {message.from_user.first_name}, sending links or spam is not allowed here!"
                )
            except Exception as e:
                print(f"Anti-Spam Error: {e}")
