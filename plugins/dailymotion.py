import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # 18+ High Quality Video Downloader (Stable Version)
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

                    # --- Source 1: XVideos ---
                    try:
                        resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
                            if links:
                                video_url = f"https://www.xvideos.com{random.choice(list(set(links))[:15])}"
                    except:
                        pass

                    # --- Source 2: XNXX ---
                    if not video_url:
                        try:
                            resp = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(/video-[^"]+)"', resp.text)
                                if links:
                                    video_url = f"https://www.xnxx.com{random.choice(list(set(links))[:15])}"
                        except:
                            pass
                            
                    # --- Source 3: XHamster ---
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
                        bot.edit_message_text(f"❌ No videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Video found! Downloading Best Available Quality (Max 50MB Limit)...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # 50MB ക്ക് താഴെ കിട്ടാവുന്ന ഏറ്റവും മികച്ച ക്വാളിറ്റി (720p/480p) എടുക്കാൻ നിർദ്ദേശം കൊടുക്കുന്നു
                    ydl_opts = {
                        'format': 'best[ext=mp4][height<=720][filesize<49.5M]/best[ext=mp4][height<=480][filesize<49.5M]/best[ext=mp4][filesize<49.5M]',
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

                    bot.edit_message_text(f"📤 **Uploading {title[:30]}...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # വീഡിയോ ടെലഗ്രാമിലേക്ക് സ്ട്രീമിങ് സപ്പോർട്ടോടെ അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            supports_streaming=True,
                            duration=duration,
                            width=width,
                            height=height,
                            timeout=120
                        )

                    bot.delete_message(message.chat.id, status_msg.message_id)

                except Exception as err:
                    error_str = str(err)[:150]
                    try:
                        bot.edit_message_text(f"❌ **Download Failed! (Video might be larger than 50MB)**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    except:
                        bot.send_message(message.chat.id, f"❌ **Download Failed!**\n\n`{error_str}`")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_process).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
