import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # Safe Search ഇല്ലാതെ നേരിട്ട് സെർച്ച് ചെയ്യാൻ
    def get_video_url(query):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        encoded_query = urllib.parse.quote(query)
        links = []
        
        try:
            r = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=5)
            urls = re.findall(r'href="(/video\d+/[^"]+)"', r.text)
            links.extend([f"https://www.xvideos.com{u}" for u in urls])
        except: pass
        
        if not links:
            try:
                r = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=5)
                urls = re.findall(r'href="(/video-[^"]+)"', r.text)
                links.extend([f"https://www.xnxx.com{u}" for u in urls])
            except: pass
            
        if not links:
            try:
                r = requests.get(f"https://xhamster.com/search/{encoded_query}?sort=best", headers=headers, timeout=5)
                urls = re.findall(r'href="(https://xhamster\.com/videos/[^"]+)"', r.text)
                links.extend([u for u in urls if '/videos/' in u and 'user' not in u])
            except: pass

        if links:
            return random.choice(list(set(links))[:15])
        return None

    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            filename = f"vid_{message.chat.id}.mp4"
            
            try:
                bot.edit_message_text(f"🔎 **Searching** for '{query}'...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                video_url = get_video_url(query)

                if not video_url:
                    bot.edit_message_text(f"❌ No suitable videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    # ⚠️ ഇവിടെ നിന്നും task_done ഒഴിവാക്കി (Error പരിഹരിച്ചു) ⚠️
                    continue

                domain_name = urllib.parse.urlparse(video_url).netloc
                bot.edit_message_text(f"⏳ **Video found! Downloading (Max 150MB)...**\n🔗 Source: `{domain_name}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # താങ്കൾ പറഞ്ഞപോലെ 150MB വരെ ഉള്ള ഏത് വീഡിയോയും എടുക്കും
                ydl_opts = {
                    'format': 'best[ext=mp4][filesize<=150M]/best[filesize<=150M]',
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                    'age_limit': 18
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    title = info.get('title', 'HD Video')
                    duration = info.get('duration', 0)
                    width = info.get('width', 0)
                    height = info.get('height', 0)

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (Using Pyrogram)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

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
                
                # ⚠️ ടാസ്ക് കഴിഞ്ഞതായി ക്യൂവിനെ അറിയിക്കുന്നത് ഇവിടെ മാത്രമായി ചുരുക്കി ⚠️
                download_queue.task_done()
                is_downloading = False

    threading.Thread(target=process_queue, daemon=True).start()

    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def ultimate_hd_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "🔥 **Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`", parse_mode='Markdown')
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
