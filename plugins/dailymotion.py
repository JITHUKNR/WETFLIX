import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Automatic Keyword Search & Video Downloader
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def search_and_download(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search mallu girl`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                try:
                    # Step 1: XHamster-ൽ കീവേഡ് സെർച്ച് ചെയ്ത് ആദ്യത്തെ വീഡിയോ ലിങ്ക് എടുക്കുന്നു
                    encoded_query = urllib.parse.quote(query)
                    search_url = f"https://xhamster.com/search/{encoded_query}"
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    
                    resp = requests.get(search_url, headers=headers, timeout=15)
                    if resp.status_code != 200:
                        bot.edit_message_text(f"❌ Search failed. Status: {resp.status_code}", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    # HTML-ൽ നിന്ന് വീഡിയോ ലിങ്കുകൾ regex വഴി കണ്ടെത്തുന്നു
                    links = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', resp.text)
                    
                    video_url = None
                    for link in links:
                        if '/videos/' in link and 'user' not in link and 'channels' not in link:
                            video_url = link
                            break

                    if not video_url:
                        bot.edit_message_text(f"❌ No videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Video found! Downloading... Please wait.**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # Step 2: yt-dlp ഉപയോഗിച്ച് വീഡിയോ ഡൗൺലോഡ് ചെയ്യുന്നു (50MB ലിമിറ്റിനുള്ളിൽ)
                    ydl_opts = {
                        'format': 'best[height<=360][filesize<48M]/best[height<=480][filesize<48M]/worst',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'headers': headers
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', 'XHamster Video')

                    # Step 3: ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔥 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=120
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
