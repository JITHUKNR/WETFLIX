import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Universal 18+ Adult Video Search & Downloader
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def adult_video_downloader(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **18+ Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search mallu bhabhi`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching adult web for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                try:
                    # yt-dlp ഓട്ടോമാറ്റിക് സെർച്ച് ഉപയോഗിച്ച് വെബിൽ നിന്ന് 18+ വീഡിയോ തപ്പുന്നു
                    ydl_opts = {
                        'format': 'best[filesize<49.5M]/bestvideo[filesize<40M]+bestaudio/worst',
                        'default_search': 'auto',
                        'noplaylist': True,
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'extractor_args': {'generic': {'impersonate': True}}
                    }

                    # സെർച്ച് ക്വറിയിൽ അഡൾട്ട് കീവേഡ് ഉറപ്പുവരുത്തുന്നു
                    search_query = f"gvsearch1:hot adult 18+ {query}"

                    bot.edit_message_text(f"⏳ **Found matching 18+ video! Downloading...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(search_query, download=True)
                        if 'entries' in info:
                            if not info['entries']:
                                raise Exception("No adult videos found. Try a different keyword.")
                            info = info['entries'][0]
                        title = info.get('title', '18+ Adult Video')

                    # ഫയൽ സൈസ് 50MB പരിധിക്കുള്ളിലാണോ എന്ന് ഉറപ്പുവരുത്തുന്നു
                    if os.path.exists(filename):
                        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                        if file_size_mb > 49.9:
                            bot.edit_message_text(f"❌ **File is too large ({file_size_mb:.1f} MB)!** Telegram limit is 50MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                            return

                    # ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔞 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=180
                        )

                    bot.delete_message(message.chat.id, status_msg.message_id)

                except Exception as err:
                    error_str = str(err)[:150]
                    try:
                        bot.edit_message_text(f"❌ **Download Failed!**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    except:
                        bot.send_message(message.chat.id, f"❌ **Download Failed!**\n\n`{error_str}`")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_process).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
