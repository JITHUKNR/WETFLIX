import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random
import time
import asyncio

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

download_queue = queue.Queue()
is_downloading = False

# ⚠️ Pyrogram-ന് വേണ്ടി ഒരു സ്ഥിരമായ ഇവന്റ് ലൂപ്പ് ഉണ്ടാക്കുന്നു (ഇത് എറർ വരുന്നത് തടയും) ⚠️
pyrogram_loop = asyncio.new_event_loop()
def start_pyrogram_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_pyrogram_loop, args=(pyrogram_loop,), daemon=True).start()

def setup(bot):
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # 🌐 യാതൊരുവിധ ഹാങ്ങിങ്ങും ഇല്ലാതെ നേരിട്ട് 3 വലിയ സൈറ്റുകളിൽ നിന്ന് വീഡിയോ എടുക്കുന്നു
    def get_video_urls(query):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36"}
        encoded = urllib.parse.quote(query)
        all_links = []
        
        # 1. XVideos
        try:
            r = requests.get(f"https://www.xvideos.com/?k={encoded}", headers=headers, timeout=5)
            urls = re.findall(r'href="(/video[^"]+)"', r.text)
            for u in urls:
                if 'tags' not in u and 'search' not in u and 'profiles' not in u:
                    all_links.append(f"https://www.xvideos.com{u}")
        except: pass
        
        # 2. XNXX
        try:
            r = requests.get(f"https://www.xnxx.com/search/{encoded}", headers=headers, timeout=5)
            urls = re.findall(r'href="(/video-[^"]+)"', r.text)
            for u in urls:
                all_links.append(f"https://www.xnxx.com{u}")
        except: pass
        
        # 3. Pornhub
        try:
            r = requests.get(f"https://www.pornhub.com/video/search?search={encoded}", headers=headers, timeout=5)
            urls = re.findall(r'href="(/view_video\.php\?viewkey=[^"]+)"', r.text)
            for u in urls:
                all_links.append(f"https://www.pornhub.com{u}")
        except: pass

        if all_links:
            links_list = list(set(all_links))
            random.shuffle(links_list) 
            return links_list
        return []

    # ⚠️ 150MB ചെക്ക് ചെയ്യാൻ വേണ്ടി മാത്രമുള്ള സിസ്റ്റം
    class MaxSizeException(Exception): pass

    def check_size_hook(d):
        if d['status'] == 'downloading':
            if d.get('downloaded_bytes', 0) > 150 * 1024 * 1024:
                raise MaxSizeException("Exceeded 150MB limit.")
            if d.get('total_bytes', 0) > 150 * 1024 * 1024:
                raise MaxSizeException("Exceeded 150MB limit.")

    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            filename = f"vid_{message.chat.id}_{int(time.time())}.mp4"
            
            try:
                bot.edit_message_text(f"🔎 **Searching** for '{query}'...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                video_urls = get_video_urls(query)

                if not video_urls:
                    bot.edit_message_text(f"❌ No videos found for '{query}'. Try a different word.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                download_success = False
                title = "HD Video"
                duration = 0
                width = 0
                height = 0

                for video_url in video_urls[:5]:
                    domain_name = urllib.parse.urlparse(video_url).netloc
                    bot.edit_message_text(f"⏳ **Checking Video from `{domain_name}`...**\n(Looking for under 150MB)", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    ydl_opts = {
                        'format': 'best',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18,
                        'socket_timeout': 15,
                        'progress_hooks': [check_size_hook]
                    }

                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_url, download=True)
                            title = info.get('title', 'HD Video')
                            duration = info.get('duration', 0)
                            width = info.get('width', 0)
                            height = info.get('height', 0)
                            download_success = True
                            break 
                    except MaxSizeException:
                        if os.path.exists(filename): os.remove(filename)
                        continue
                    except Exception as e:
                        if os.path.exists(filename): os.remove(filename)
                        continue

                if not download_success:
                    bot.edit_message_text(f"❌ **Download Failed!**\nAll found videos were larger than 150MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (Using Pyrogram)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ മുൻപ് ഉണ്ടാക്കിവെച്ച സ്ഥിരമായ ലൂപ്പിലേക്ക് അപ്‌ലോഡ് ടാസ്ക് കൊടുക്കുന്നു (ഇതോടെ എറർ വരില്ല) ⚠️
                async def do_upload():
                    async with Client("wetflix_pyro_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) as app:
                        await app.send_video(
                            chat_id=message.chat.id,
                            video=filename,
                            caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX_",
                            duration=duration,
                            width=width,
                            height=height,
                            supports_streaming=True
                        )

                # ടാസ്ക് റൺ ചെയ്യാൻ കാത്തിരിക്കുന്നു
                future = asyncio.run_coroutine_threadsafe(do_upload(), pyrogram_loop)
                future.result() # അപ്‌ലോഡ് തീരുന്നതുവരെ വെയിറ്റ് ചെയ്യും
                
                bot.delete_message(message.chat.id, status_msg.message_id)

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.edit_message_text(f"❌ **Error occurred!**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                except: pass
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                
                download_queue.task_done()
                is_downloading = False

    threading.Thread(target=process_queue, daemon=True).start()

    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def ultimate_hd_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "🔥 **Web Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`", parse_mode='Markdown')
                return

            query = parts[1].strip()
            
            if is_downloading or not download_queue.empty():
                position = download_queue.qsize() + 1
                status_msg = bot.reply_to(message, f"⏳ **Added to Queue!**\n\nYou are in position #{position}.\nPlease wait...", parse_mode='Markdown')
            else:
                status_msg = bot.reply_to(message, f"🔎 Processing request for **'{query}'**...", parse_mode='Markdown')

            download_queue.put((message, query, status_msg))

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
