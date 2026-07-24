import telebot
import os
import importlib
import threading
import time
from flask import Flask
from telebot.types import BotCommand
from config import BOT_TOKEN, PORT

# Initialize bot (Clean initialization without blocking listeners)
bot = telebot.TeleBot(BOT_TOKEN)

# -----------------------------------------------------------
# Plugin System (Auto-load features from plugins folder)
# -----------------------------------------------------------
def load_plugins():
    for filename in os.listdir("plugins"):
        # ട്രാക്കിംഗ് പ്ലഗിൻ കാരണം കമാൻഡുകൾ ബ്ലോക്ക് ആവാതിരിക്കാൻ അത് ഒഴിവാക്കുന്നു
        if filename.endswith(".py") and filename not in ["__init__.py", "track.py"]:
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
    return "WETFLIX Bot is running smoothly!"

def run_flask():
    try:
        app.run(host="0.0.0.0", port=PORT, use_reloader=False, debug=False)
    except Exception as e:
        pass

# Run bot with safe auto-reconnect loop
if __name__ == "__main__":
    print("🚀 WETFLIX Bot is starting...")
    
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("sticker", "Get a random sticker"),
            BotCommand("video", "Get a random video"),
            BotCommand("image", "Get a random photo")
        ])
        print("✅ Menu updated successfully!")
    except Exception as e:
        print(f"❌ Error setting menu: {e}")

    # Start Flask server safely in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Safe polling loop
    while True:
        try:
            print("🔄 Starting bot polling...")
            # skip_pending=True കൊടുത്തിട്ടുള്ളതുകൊണ്ട് ബോട്ട് ഓഫ് ആയിരുന്ന സമയത്തെ മെസ്സേജുകൾ സ്കിപ്പ് ചെയ്യും
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            time.sleep(5)
