from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document', 'audio'])
    def log_user_activity(message):
        user_id = message.from_user.id
        
        # അഡ്മിൻ അയക്കുന്ന മെസ്സേജുകൾ ലോഗ് ചെയ്യേണ്ടതില്ല
        if user_id == ADMIN_ID:
            return

        try:
            user = message.from_user
            name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            username = f"@{user.username}" if user.username else "No Username"
            
            # യൂസറുടെ വിവരങ്ങൾ ബോട്ടിന്റെ ചാറ്റിലേക്ക് അയക്കുന്നു
            info_header = (
                f"👤 **User Activity**\n\n"
                f"• **Name:** {name}\n"
                f"• **Username:** {username}\n"
                f"• **User ID:** `{user.id}`\n"
                f"• **Type:** `{message.content_type}`"
            )
            
            bot.send_message(message.chat.id, info_header, parse_mode='Markdown')
            # യൂസർ അയച്ച ഒറിജിനൽ മെസ്സേജും ബോട്ട് വഴി തിരിച്ച് ഫോർവേഡ് ചെയ്യുന്നു
            bot.forward_message(message.chat.id, message.chat.id, message.message_id)
            
        except Exception as e:
            print(f"Logger Error: {e}")
