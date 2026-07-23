def setup(bot):

    @bot.message_handler(content_types=['new_chat_members'])
    def welcome_new_members(message):
        try:
            for new_member in message.new_chat_members:
                # ബോട്ട് ജോയിൻ ചെയ്യുമ്പോൾ ഉള്ള മെസ്സേജ് ഒഴിവാക്കാൻ
                if new_member.id == bot.get_me().id:
                    continue
                    
                welcome_text = (
                    f"👋 Welcome, {new_member.first_name}!\n\n"
                    f"We are glad to have you in **{message.chat.title}**. "
                    f"Please read the group rules and enjoy your stay! 🚀"
                )
                
                bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Welcome Error: {e}")

    @bot.message_handler(content_types=['left_chat_member'])
    def goodbye_member(message):
        try:
            left_member = message.left_chat_member
            if left_member.id == bot.get_me().id:
                return
                
            goodbye_text = f"👋 Goodbye, {left_member.first_name}. Hope to see you again!"
            bot.send_message(message.chat.id, goodbye_text)
        except Exception as e:
            print(f"Goodbye Error: {e}")
