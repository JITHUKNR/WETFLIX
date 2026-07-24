from database import add_requested_user

def setup(bot):
    @bot.chat_join_request_handler()
    def handle_join_request(message):
        user_id = message.from_user.id
        add_requested_user(user_id)
        
        try:
            bot.send_message(user_id, "✅ **Request Approved!**\nYou can now use the bot. Type /start to begin.", parse_mode='Markdown')
        except:
            pass
