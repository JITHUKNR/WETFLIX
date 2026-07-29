import os
import urllib.parse
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # XHamster Direct Search Command (/search or /dm)
    @bot.message_handler(commands=['search', 'dm'])
    def search_xhamster(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Video Search:**\n\n📖 *Usage:*\n`/search <video name>`\n\n💡 *Example:* `/search mallu girl`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            
            # XHamster സെർച്ച് ലിങ്ക് ജനേറ്റ് ചെയ്യുന്നു
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://xhamster.com/search/{encoded_query}"

            markup = InlineKeyboardMarkup(row_width=1)
            # യൂസർക്ക് നേരിട്ട് സൈറ്റിൽ പോയി കാണാനും ഡൗൺലോഡ് ചെയ്യാനും ഉള്ള ബട്ടൺ
            markup.add(InlineKeyboardButton(f"🔞 Click Here to View '{query}' Videos", url=search_url))

            bot.reply_to(
                message, 
                f"🔥 **Search Results for:** `{query}`\n\n👇 *Click the button below to watch and download all videos directly from XHamster:*", 
                reply_markup=markup, 
                parse_mode='Markdown'
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Search Error: `{e}`")
