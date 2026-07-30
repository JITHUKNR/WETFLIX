import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ക്യൂ സിസ്റ്റം
download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # 🌐 ഗൂഗിളിൽ/വെബിൽ നിന്ന് ഏത് സൈറ്റിൽ നിന്നായാലും വീഡിയോ തപ്പിയെടുക്കാനുള്ള ഫംഗ്ഷൻ
    def get_video_url_from_web(query):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # രീതി 1: DuckDuckGo വഴി വെബിൽ മൊത്തത്തിൽ സെർച്ച് ചെയ്യുന്നു
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query + ' video')}"
            res = requests.get(search_url, headers=headers, timeout=10)
            urls = re.findall(r'href="([^"]+)"', res.text)
            
            # ലോകത്തുള്ള ഒട്ടുമിക്ക പോപ്പുലർ സൈറ്റുകളും ഇതിൽ സപ്പോർട്ട് ചെയ്യും
            valid_domains = ['xvideos.com', 'xnxx.com', 'xhamster.com', 'pornhub.com', 'spankbang.com', 'eporner.com', 'hqporner.com', 'beeg.com', 'tnaflix.com', 'tube8.com']
            for u in urls:
                if 'uddg=' in u:
                    u = urllib.parse.unquote(u.split('uddg=')[1].split('&')[0])
                for domain in valid_domains:
                    if domain in u and 'search' not in u and 'category' not in u:
                        return u
        except: pass
        
        # രീതി 2: മുകളിലത്തെ രീതി കിട്ടിയില്ലെങ്കിൽ നേരിട്ടുള്ള സെർച്ച് (Fallback)
        try:
            encoded_query = urllib.parse.quote(query)
            resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=10)
            links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
            if links: return f"https://www.xvideos.com{random.choice(list(set(links))[:10])}"
        except: pass
        
        return None

    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            filename = f"vid_{message.chat.id}.mp4"
            
            try:
                bot.edit_message_text(f"🔎 **Searching the web** for '{query}'...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                # വെബിൽ നിന്ന് ലിങ്ക് എടുക്കുന്നു
                video_url = get_video_url_from_web(query)

                if not video_url:
                    bot.edit_message_text(f"❌ No suitable videos found on the web for '{query}'.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                # എവിടുന്ന് കിട്ടി എന്ന സൈറ്റിന്റെ പേരും കാണിക്കും
                domain_name = urllib.parse.urlparse(video_url).netloc
                bot.edit_message_text(f"⏳ **Video found! Downloading (Max 150MB)...**\n🔗 Source: `{domain_name}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ 150MB സൈസ് ലിമിറ്റ് ⚠️
                ydl_opts = {
                    'format': 'best[ext=mp4][filesize<150M]/best[filesize<150M]',
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

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (Using Pyrogram for large file)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ MAINTHREAD എറർ ഒഴിവാക്കാൻ PYROGRAM ഉള്ളിലാക്കി വെച്ചിരിക്കുന്നു ⚠️
                def run_pyrogram_upload():
                    import asyncio
                    from pyrogram import Client
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def upload():
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
                            
                    loop.run_until_complete(upload())
                    loop.close()

                # അപ്‌ലോഡ് മറ്റൊരു ത്രെഡിൽ ഓടിക്കുന്നു
                upload_thread = threading.Thread(target=run_pyrogram_upload)
                upload_thread.start()
                upload_thread.join()
                
                bot.delete_message(message.chat.id, status_msg.message_id)

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.edit_message_text(f"❌ **Download Failed! (Might be larger than 150MB)**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                except: pass
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                
                download_queue.task_done()
                is_downloading = False

    # പ്ലഗിൻ ലോഡ് ആകുമ്പോൾ തന്നെ ബാക്ക്ഗ്രൗണ്ട് ക്യൂ സ്റ്റാർട്ട് ചെയ്യുന്നു
    threading.Thread(target=process_queue, daemon=True).start()

    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def ultimate_hd_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **Web Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search hot mallu`", 
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
