import telebot
import os
import importlib
import threading
from flask import Flask
from telebot.types import BotCommand
from config import BOT_TOKEN, PORT

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# -----------------------------------------------------------
# Plugin System (Auto-load features from plugins folder)
# -----------------------------------------------------------
def load_plugins():
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"plugins.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, 'setup'):
                    module.setup(bot)
                print(f"✅ Loaded plugin: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

# Load features
load_plugins()

# -----------------------------------------------------------
# Flask Server (Render Keep-Alive)
# -----------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Ultimate Bot is running with Advanced Plugin System!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# Run bot
if __name__ == "__main__":
    print("🚀 Bot is starting...")
    
    # Set Bot Commands (Hides admin command from the menu)
    try:
        bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("sticker", "Get a random sticker"),
            BotCommand("video", "Get a random video"),
            BotCommand("image", "Get a random photo")
        ])
        print("✅ Menu updated successfully! (Admin command hidden)")
    except Exception as e:
        print(f"❌ Error setting menu: {e}")

    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
