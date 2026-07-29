import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

def setup(bot):

    # Render Environment-ൽ നിന്നും API വിവരങ്ങൾ എടുക്കുന്നു
    # Pyrogram-ൽ API_ID ഒരു Number (Integer) ആയിരിക്കണം, അതുകൊണ്ട് int() കൊടുക്കുന്നു.
    API_ID = int(os.environ.get("API_ID", 0)) 
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # Pyrogram Client ഉണ്ടാക്കുന്നു
    app = Client("wetflix_pyro_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.start()

    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def ultimate_hd_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **18+ HD Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search hot mallu`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching HD 18+ Videos for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                video_url = None
                
                try:
                    encoded_query = urllib.parse.quote(query)
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                    # --- Source 1: XVideos Search ---
                    try:
                        resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
                            links = list(set(links))
                            if links:
                                video_url = f"https://www.xvideos.com{random.choice(links[:15])}"
                    except:
                        pass

                    # --- Source 2: XNXX Search ---
                    if not video_url:
                        try:
                            resp = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(/video-[^"]+)"', resp.text)
                                links = list(set(links))
                                if links:
                                    video_url = f"https://www.xnxx.com{random.choice(links[:15])}"
                        except:
                            pass
                            
                    # --- Source 3: XHamster Search ---
                    if not video_url:
                        try:
                            resp = requests.get(f"https://xhamster.com/search/{encoded_query}?sort=best", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', resp.text)
                                valid_links = [l for l in set(links) if '/videos/' in l and 'user' not in l]
                                if valid_links:
                                    video_url = random.choice(valid_links[:15])
                        except:
                            pass

                    if not video_url:
                        bot.edit_message_text(f"❌ No suitable videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Video found! Downloading Best Quality (No 50MB Limit)...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    ydl_opts = {
                        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', 'HD 18+ Video')
                        duration = info.get('duration', 0)
                        width = info.get('width', 0)
                        height = info.get('height', 0)

                    bot.edit_message_text(f"📤 **Uploading {title[:30]}... (This might take a while for large HD files)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # Pyrogram വഴി ഫയലുകൾ അയക്കുന്നു
                    app.send_video(
                        chat_id=message.chat.id,
                        video=filename,
                        caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_",
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True
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
