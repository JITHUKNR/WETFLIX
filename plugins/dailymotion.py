import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# സുരക്ഷിതമായ ക്യൂ സിസ്റ്റം
download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    BOT_TOKEN = bot.token

    # ബാക്ക്ഗ്രൗണ്ടിൽ വർക്ക് ചെയ്യുന്ന ക്യൂ സിസ്റ്റം
    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            filename = f"vid_{message.chat.id}.mp4"
            video_url = None
            
            try:
                bot.edit_message_text(f"🔎 **Your turn!** Searching HD 18+ Videos for **'{query}'**...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                encoded_query = urllib.parse.quote(query)
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

                # --- Source 1: XVideos Search ---
                try:
                    resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=10)
                    if resp.status_code == 200:
                        links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
                        if links:
                            video_url = f"https://www.xvideos.com{random.choice(list(set(links))[:15])}"
                except: pass

                # --- Source 2: XNXX Search ---
                if not video_url:
                    try:
                        resp = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(/video-[^"]+)"', resp.text)
                            if links:
                                video_url = f"https://www.xnxx.com{random.choice(list(set(links))[:15])}"
                    except: pass
                        
                # --- Source 3: XHamster Search ---
                if not video_url:
                    try:
                        resp = requests.get(f"https://xhamster.com/search/{encoded_query}?sort=best", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', resp.text)
                            valid_links = [l for l in set(links) if '/videos/' in l and 'user' not in l]
                            if valid_links:
                                video_url = random.choice(valid_links[:15])
                    except: pass

                if not video_url:
                    bot.edit_message_text(f"❌ No suitable videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                bot.edit_message_text(f"⏳ **Video found! Downloading Best Quality...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # യാതൊരു ലിമിറ്റും ഇല്ലാതെ വീഡിയോ ഡൗൺലോഡ് ചെയ്യുന്നു
                ydl_opts = {
                    'format': 'best', 
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                    'age_limit': 18
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    title = info.get('title', 'HD 18+ Video')
                    
                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (Bypassing Limits)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ ടെലഗ്രാമിന്റെ ലോക്കൽ API അല്ലെങ്കിൽ Requests ഉപയോഗിച്ച് വലിയ ഫയൽ അയക്കുന്നു ⚠️
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
                with open(filename, 'rb') as video_file:
                    files = {'video': video_file}
                    data = {
                        'chat_id': message.chat.id,
                        'caption': f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot_",
                        'parse_mode': 'Markdown',
                        'supports_streaming': 'true'
                    }
                    response = requests.post(url, data=data, files=files)
                
                # ഫയൽ അയച്ചുകഴിഞ്ഞാൽ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
                if response.status_code == 200:
                    bot.delete_message(message.chat.id, status_msg.message_id)
                else:
                    raise Exception("Failed to upload via API")

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.edit_message_text(f"❌ **Download Failed! (File might be too large for this server)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                except:
                    pass
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                
                download_queue.task_done()
                is_downloading = False

    # പ്ലഗിൻ ലോഡ് ആകുമ്പോൾ തന്നെ ബാക്ക്ഗ്രൗണ്ട് പ്രോസസ്സ് സ്റ്റാർട്ട് ചെയ്യുന്നു
    threading.Thread(target=process_queue, daemon=True).start()

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
            
            if is_downloading or not download_queue.empty():
                position = download_queue.qsize() + 1
                status_msg = bot.reply_to(message, f"⏳ **Added to Queue!**\n\nYou are in position #{position}.\nPlease wait, your video for **'{query}'** will start processing soon...", parse_mode='Markdown')
            else:
                status_msg = bot.reply_to(message, f"🔎 Processing request for **'{query}'**...", parse_mode='Markdown')

            download_queue.put((message, query, status_msg))

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
