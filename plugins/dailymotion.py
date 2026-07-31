import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random
import time

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    BOT_TOKEN = bot.token

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

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (This may take a minute)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ Pyrogram ഒഴിവാക്കി ടെലഗ്രാമിന്റെ ഒറിജിനൽ API വഴി തന്നെ വലിയ ഫയലുകൾ സ്ട്രീം ചെയ്ത് അയക്കുന്നു (റാം ക്രാഷ് ആവില്ല) ⚠️
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
                with open(filename, 'rb') as video_file:
                    files = {'video': video_file}
                    data = {
                        'chat_id': message.chat.id,
                        'caption': f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_",
                        'parse_mode': 'Markdown',
                        'supports_streaming': 'true'
                    }
                    response = requests.post(url, data=data, files=files, timeout=300) # അപ്‌ലോഡ് ചെയ്യാൻ 5 മിനിറ്റ് വരെ സമയം കൊടുക്കുന്നു
                
                if response.status_code == 200:
                    bot.delete_message(message.chat.id, status_msg.message_id)
                else:
                    raise Exception("Failed to upload via Telegram API")

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.edit_message_text(f"❌ **Upload Failed! (Server Timeout)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
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
