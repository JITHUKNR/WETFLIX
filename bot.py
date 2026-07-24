import telebot
import os
import importlib
import threading
import time
import datetime
from flask import Flask
from telebot.types import BotCommand
from config import BOT_TOKEN, PORT

# Database import for tracking
try:
    from database import users_col
except ImportError:
    pass

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# -----------------------------------------------------------
# Silent User Tracking System (Update Listener)
# -----------------------------------------------------------
def activity_tracker(messages):
    for message in messages:
        try:
            # ഓരോ മെസ്സേജ് വരുമ്പോഴും യൂസറുടെ സമയം ഡാറ്റാബേസിൽ സേവ് ചെയ്യുന്നു
            if message.from_user:
                user_id = message.from_user.id
                now = datetime.datetime.now()
                if 'users_col' in globals():
                    users_col.update_one(
                        {"user_id": user_id},
                        {
                            "$set": {"last_active": now}, 
                            "$setOnInsert": {"joined_date": now, "banned": False}
                        },
                        upsert=True
                    )
        except Exception:
            pass

# ട്രാക്കിംഗ് സിസ്റ്റം ബോട്ടുമായി കണക്ട് ചെയ്യുന്നു
bot.set_update_listener(activity_tracker)

# -----------------------------------------------------------
# Plugin System (Auto-load features from plugins folder)
# -----------------------------------------------------------
def load_plugins():
    for filename in os.listdir("plugins"):
        # track.py ഉണ്ടെങ്കിൽ അത് ഒഴിവാക്കുന്നു 
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
        print(f"Flask error: {e}")

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

    # Start Flask server in background thread safely
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Safe polling loop
    while True:
        try:
            print("🔄 Starting bot polling...")
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling reconnected after error: {e}")
            time.sleep(5)
