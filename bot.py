import telebot
import os
import importlib
import threading
from flask import Flask
from config import BOT_TOKEN, PORT

# ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
bot = telebot.TeleBot(BOT_TOKEN)

# -----------------------------------------------------------
# പ്ലഗിൻ സിസ്റ്റം (Plugins ഫോൾഡറിലെ ഫീച്ചറുകൾ തനിയെ ലോഡ് ചെയ്യാൻ)
# -----------------------------------------------------------
def load_plugins():
    # plugins ഫോൾഡറിലുള്ള എല്ലാ പൈത്തൺ ഫയലുകളും എടുക്കുന്നു
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"plugins.{filename[:-3]}"
            try:
                # ഓരോ ഫയലും Import ചെയ്യുന്നു
                module = importlib.import_module(module_name)
                # ആ ഫയലിൽ 'setup' എന്നൊരു ഫംഗ്ഷൻ ഉണ്ടെങ്കിൽ അത് പ്രവർത്തിപ്പിക്കുന്നു
                if hasattr(module, 'setup'):
                    module.setup(bot)
                print(f"✅ Loaded plugin: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

# ഫീച്ചറുകൾ ലോഡ് ചെയ്യുന്നു
load_plugins()

# -----------------------------------------------------------
# Flask സെർവർ (Render Keep-Alive)
# -----------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Ultimate Bot is running with Advanced Plugin System!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ബോട്ട് റൺ ചെയ്യാൻ
if __name__ == "__main__":
    print("🚀 Bot is starting...")
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
