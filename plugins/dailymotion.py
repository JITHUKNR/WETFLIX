import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Ultimate 18+ Multi-Site Downloader (With Randomizer & Streaming)
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
                            links = list(set(links)) # ഡ്യൂപ്ലിക്കേറ്റ് ഒഴിവാക്കുന്നു
                            if links:
                                # കിട്ടിയതിൽ നിന്ന് വ്യത്യസ്തമായ ഒരെണ്ണം തിരഞ്ഞെടുക്കുന്നു
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
                            resp = requests.get(f"https://xhamster.com/search/{encoded_query}", headers=headers, timeout=10)
                            if resp.status_code == 200:
                                links = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', resp.text)
                                valid_links = [l for l in set(links) if '/videos/' in l and 'user' not in l]
                                if valid_links:
                                    video_url = random.choice(valid_links[:15])
                        except:
                            pass

                    if not video_url:
                        bot.edit_message_text(f"❌ No 18+ videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Video found! Downloading...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # yt-dlp: കൃത്യമായി MP4 ഫോർമാറ്റ് മാത്രം എടുക്കാൻ പറയുന്നു (സ്ട്രീമിങ്ങിന് വേണ്ടി)
                    ydl_opts = {
                        'format': 'best[ext=mp4][height<=480][filesize<49.5M]/best[ext=mp4][height<=360][filesize<49.5M]/worst[ext=mp4]',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', '18+ Adult Video')
                        duration = info.get('duration', 0)
                        width = info.get('width', 0)
                        height = info.get('height', 0)

                    # 50MB പരിധി ഉറപ്പുവരുത്തുന്നു
                    if os.path.exists(filename):
                        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                        if file_size_mb > 49.9:
                            bot.edit_message_text(f"❌ **File is too large ({file_size_mb:.1f} MB)!** Telegram limit is 50MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                            return

                    # വീഡിയോ പ്ലേ ചെയ്യാവുന്ന രീതിയിൽ (Streaming) അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            supports_streaming=True,  # ഇതാണ് ഡൗൺലോഡ് ചെയ്യുമ്പോൾ തന്നെ പ്ലേ ചെയ്യാൻ സഹായിക്കുന്നത്!
                            duration=duration,
                            width=width,
                            height=height,
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
