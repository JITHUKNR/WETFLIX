import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Ultimate 18+ Multi-Site Downloader
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def ultimate_adult_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **18+ Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search pussy eat`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching 18+ Networks for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                video_url = None
                
                try:
                    encoded_query = urllib.parse.quote(query)
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                    # --- Source 1: XVideos Search ---
                    try:
                        resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
                            if links:
                                video_url = f"https://www.xvideos.com{links[0]}"
                    except:
                        pass

                    # --- Source 2: XNXX Search (If XVideos fails) ---
                    if not video_url:
                        try:
                            resp = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(/video-[^"]+)"', resp.text)
                                if links:
                                    video_url = f"https://www.xnxx.com{links[0]}"
                        except:
                            pass
                            
                    # --- Source 3: XHamster Search (If XNXX fails) ---
                    if not video_url:
                        try:
                            resp = requests.get(f"https://xhamster.com/search/{encoded_query}", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', resp.text)
                                for link in links:
                                    if '/videos/' in link and 'user' not in link:
                                        video_url = link
                                        break
                        except:
                            pass

                    # വീഡിയോ എവിടെ നിന്നും കിട്ടിയില്ലെങ്കിൽ
                    if not video_url:
                        bot.edit_message_text(f"❌ No 18+ videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Video found! Downloading...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # yt-dlp ഉപയോഗിച്ച് ഡൗൺലോഡ് ചെയ്യുന്നു
                    ydl_opts = {
                        'format': 'best[height<=480][filesize<49.5M]/best[height<=360][filesize<49.5M]/worst',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', '18+ Adult Video')

                    # 50MB പരിധി ഉറപ്പുവരുത്തുന്നു
                    if os.path.exists(filename):
                        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                        if file_size_mb > 49.9:
                            bot.edit_message_text(f"❌ **File is too large ({file_size_mb:.1f} MB)!** Telegram limit is 50MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                            return

                    # വീഡിയോ ടെലഗ്രാമിലേക്ക് ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_", 
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
