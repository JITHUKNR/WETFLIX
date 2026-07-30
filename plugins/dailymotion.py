import os
import re
import urllib.parse
import threading
import queue
import requests
import yt_dlp
import random
import asyncio

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

# ക്യൂ സിസ്റ്റം
download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    # API വിവരങ്ങൾ
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # ബാക്ക്ഗ്രൗണ്ടിൽ ഓരോരുത്തർക്കും വരിവരിയായി വീഡിയോ കൊടുക്കാനുള്ള സിസ്റ്റം
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

                bot.edit_message_text(f"⏳ **Video found! Downloading Best Quality (No 50MB Limit)...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # യാതൊരു ലിമിറ്റുമില്ലാതെ ഫുൾ HD വീഡിയോ എടുക്കുന്നു
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
                    duration = info.get('duration', 0)
                    width = info.get('width', 0)
                    height = info.get('height', 0)

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (This might take a while for large files)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # ⚠️ 150MB+ വീഡിയോകൾ അയക്കാൻ പഴയ Pyrogram കോഡ് (എറർ വരാത്ത രീതിയിൽ) ⚠️
                def run_pyrogram_upload():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def upload():
                        async with Client("wetflix_pyro_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) as app:
                            await app.send_video(
                                chat_id=message.chat.id,
                                video=filename,
                                caption=f"🔞 **{title[:50]}...**\n\n📥 _Downloaded via WETFLIX Bot (HD)_",
                                duration=duration,
                                width=width,
                                height=height,
                                supports_streaming=True
                            )
                            
                    loop.run_until_complete(upload())
                    loop.close()

                # അപ്‌ലോഡ് മാത്രം ഒരു പ്രത്യേക ത്രെഡിൽ ഓടിക്കുന്നു (MainThread എറർ ഒഴിവാക്കാൻ)
                upload_thread = threading.Thread(target=run_pyrogram_upload)
                upload_thread.start()
                upload_thread.join()
                
                bot.delete_message(message.chat.id, status_msg.message_id)

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.edit_message_text(f"❌ **Download Failed!**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                except:
                    pass
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
                    "🔥 **18+ HD Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search hot mallu`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            
            # ക്യൂ സിസ്റ്റം
            if is_downloading or not download_queue.empty():
                position = download_queue.qsize() + 1
                status_msg = bot.reply_to(message, f"⏳ **Added to Queue!**\n\nYou are in position #{position}.\nPlease wait, your video for **'{query}'** will start processing soon...", parse_mode='Markdown')
            else:
                status_msg = bot.reply_to(message, f"🔎 Processing request for **'{query}'**...", parse_mode='Markdown')

            download_queue.put((message, query, status_msg))

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
