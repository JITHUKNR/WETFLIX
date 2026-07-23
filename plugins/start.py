from telebot.types import BotCommand
import time
from database import users_col

def setup(bot):
    # Setting up the English Menu
    bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("sticker", "Get a random sticker"),
        BotCommand("video", "Get a random video"),
        BotCommand("image", "Get a random photo"),
        BotCommand("admin", "Admin Panel (Owner Only)")
    ])

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        
        # Save new user to database
        if not users_col.find_one({"user_id": user_id}):
            users_col.insert_one({"user_id": user_id, "banned": False, "joined_date": time.time()})
            
        bot.reply_to(message, f"Hello {message.from_user.first_name}! 🚀\n\nWelcome to the Ultimate Bot. The bot is ready to use. Please explore the options from the menu.")
