import telebot
import os
import importlib
import threading
import time
import traceback  # എറർ കണ്ടുപിടിക്കാൻ പുതിയതായി ചേർത്തത്
from flask import Flask
from telebot.types import BotCommand
from config import BOT_TOKEN, PORT

# -----------------------------------------------------------
# Error Catcher System (എററുകൾ ലോഗിൽ കൃത്യമായി കാണിക്കാൻ)
# -----------------------------------------------------------
class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("\n" + "="*50)
        print("🔥 BOT CRASHED OR COMMAND FAILED! 🔥")
        print("👇 എറർ വന്ന ഫയലും ലൈൻ നമ്പറും താഴെ നോക്കുക 👇\n")
        traceback.print_exc()
        print("="*50 + "\n")
        return True

# Initialize bot (Clean initialization + Error Catcher)
bot = telebot.TeleBot(BOT_TOKEN, exception_handler=ExceptionHandler())

# -----------------------------------------------------------
# Plugin System (Sorted Priority Loading!)
# -----------------------------------------------------------
def load_plugins():
    # 1. ഏറ്റവും ആദ്യം start.py ലോഡ് ചെയ്യുന്നു
    try:
        if os.path.exists("plugins/start.py"):
            importlib.import_module("plugins.start").setup(bot)
            print("✅ Loaded plugin: start.py (PRIORITY)")
    except Exception as e:
        print(f"❌ Failed to load start.py: {e}")

    # 2. ബാക്കിയുള്ള പ്ലഗിനുകൾ എല്ലാം അക്ഷരമാലാ ക്രമത്തിൽ (Sorted) ലോഡ് ചെയ്യുന്നു
    # ഇവിടെയാണ് നമ്മൾ sorted() ചേർത്തത്!
    for filename in sorted(os.listdir("plugins")):
        # track.py ഉം ഇപ്പോൾ ലോഡ് ചെയ്ത start.py ഉം ഒഴിവാക്കുന്നു
        if filename.endswith(".py") and filename not in ["__init__.py", "track.py", "start.py"]:
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
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5)
