import os
import re
import urllib.parse
import threading
import requests
import yt_dlp
import random
import asyncio

# ⚠️ പ്രധാനപ്പെട്ട പരിഹാരം: Event Loop ക്രാഷ് ഒഴിവാക്കാൻ ⚠️
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

# ⚠️ ഇവിടെയാണ് നമ്മൾ ക്യൂ സിസ്റ്റം ഉണ്ടാക്കുന്നത് ⚠️
download_queue = asyncio.Queue()
is_downloading = False

def setup(bot):

    # Render Environment-ൽ നിന്നും API വിവരങ്ങൾ എടുക്കുന്നു
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    if not API_ID or not API_HASH:
        print("⚠️ Warning: API_ID or API_HASH is missing in Environment Variables!")

    # ബാക്ക്ഗ്രൗണ്ടിൽ ക്യൂവിലുള്ള ഓരോ വീഡിയോയും വരിവരിയായി എടുത്ത് പ്രോസസ്സ് ചെയ്യാൻ ഒരു വർക്കർ ഫംഗ്ഷൻ
    async def process_queue():
        global is_downloading
        while True:
            # ക്യൂവിൽ നിന്ന് അടുത്ത റിക്വസ്റ്റ് എടുക്കുന്നു
            task = await download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            
            try:
                # താങ്കളുടെ പഴയ ഡൗൺലോഡ് & അപ്‌ലോഡ് കോഡ് ഇവിടെ വരുന്നു
                filename = f"vid_{message.chat.id}.mp4"
                video_url = None
                
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
                except:
                    pass

                # --- Source 2: XNXX Search ---
                if not video_url:
                    try:
                        resp = requests.get(f"https://www.xnxx.com/search/{encoded_query}", headers=headers, timeout=10)
                        if resp.status_code == 200:
                            links = re.findall(r'href="(/video-[^"]+)"', resp.text)
                            if links:
                                video_url = f"https://www.xnxx.com{random.choice(list(set(links))[:15])}"
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
                    download_queue.task_done()
                    is_downloading = False
                    continue

                bot.edit_message_text(f"⏳ **Video found! Downloading Best Quality...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                ydl_opts = {
                    'format': 'best', 
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                    'age_limit': 18
                }

                # ബ്ലോക്കിംഗ് കോഡായ yt_dlp യെ മറ്റൊരു ത്രെഡിൽ ഓടിക്കുന്നു, അപ്പോൾ ബോട്ട് ഹാങ് ആവില്ല
                loop = asyncio.get_event_loop()
                def extract_info():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(video_url, download=True)
                
                info = await loop.run_in_executor(None, extract_info)
                title = info.get('title', 'HD 18+ Video')
                duration = info.get('duration', 0)
                width = info.get('width', 0)
                height = info.get('height', 0)

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (This might take a while for large files)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # Pyrogram വഴി അപ്‌ലോഡ് ചെയ്യുന്നു (No 50MB Limit)
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
                
                # ഈ ടാസ്ക് കഴിഞ്ഞതായി ക്യൂവിനെ അറിയിക്കുന്നു
                download_queue.task_done()
                is_downloading = False

    # ബോട്ട് ഓൺ ആകുമ്പോൾ തന്നെ വർക്കർ ഫംഗ്ഷൻ ബാക്ക്ഗ്രൗണ്ടിൽ ഓടാൻ തുടങ്ങും
    threading.Thread(target=lambda: asyncio.run(process_queue()), daemon=True).start()


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
            
            # വീഡിയോ ഡൗൺലോഡ് ചെയ്തുകൊണ്ടിരിക്കുകയാണെങ്കിൽ വരിയിൽ നിർത്തുന്നു
            if is_downloading or not download_queue.empty():
                position = download_queue.qsize() + 1
                status_msg = bot.reply_to(message, f"⏳ **Added to Queue!**\n\nYou are in position #{position}.\nPlease wait, your video for **'{query}'** will start processing soon...", parse_mode='Markdown')
            else:
                status_msg = bot.reply_to(message, f"🔎 Processing request for **'{query}'**...", parse_mode='Markdown')

            # റിക്വസ്റ്റ് ക്യൂവിലേക്ക് ചേർക്കുന്നു
            asyncio.run(download_queue.put((message, query, status_msg)))

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
