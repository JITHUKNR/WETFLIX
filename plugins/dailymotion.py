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

    # 🌐 വെബിൽ നിന്നും ഗൂഗിളിൽ നിന്നും ഏത് സൈറ്റിലെ വീഡിയോയും എടുക്കാൻ
    def get_video_urls_from_web(query):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        all_links = []
        
        # ഗൂഗിളിൽ നിന്നുള്ള സെർച്ച് (DuckDuckGo വഴി)
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query + ' video')}"
            res = requests.get(search_url, headers=headers, timeout=10)
            urls = re.findall(r'href="([^"]+)"', res.text)
            
            for u in urls:
                if 'uddg=' in u:
                    u = urllib.parse.unquote(u.split('uddg=')[1].split('&')[0])
                if ('xvideos.com' in u or 'xnxx.com' in u or 'xhamster.com' in u or 'pornhub.com' in u) and 'search' not in u and 'category' not in u:
                    all_links.append(u)
        except: pass
        
        # നേരിട്ടുള്ള സെർച്ച് (Fallback)
        try:
            encoded_query = urllib.parse.quote(query)
            resp = requests.get(f"https://www.xvideos.com/?k={encoded_query}&sort=relevance", headers=headers, timeout=10)
            links = re.findall(r'href="(/video\d+/[^"]+)"', resp.text)
            all_links.extend([f"https://www.xvideos.com{u}" for u in links])
        except: pass
        
        if all_links:
            # കിട്ടിയ ലിങ്കുകൾ ഷഫിൾ ചെയ്ത് കൊടുക്കുന്നു
            links_list = list(set(all_links))
            random.shuffle(links_list)
            return links_list
        return []

    # ⚠️ 150MB ചെക്ക് ചെയ്യാനുള്ള കസ്റ്റം ഡൗൺലോഡ് ഹുക്ക് ⚠️
    class MaxSizeException(Exception):
        pass

    def check_size_hook(d):
        if d['status'] == 'downloading':
            # ഡൗൺലോഡ് ചെയ്തുകൊണ്ടിരിക്കുമ്പോൾ സൈസ് 150MB കഴിഞ്ഞാൽ അപ്പോൾ തന്നെ നിർത്തും
            if d.get('downloaded_bytes', 0) > 150 * 1024 * 1024:
                raise MaxSizeException("Video exceeded 150MB limit.")
            # മുൻകൂട്ടി സൈസ് അറിയാമെങ്കിൽ അതും ചെക്ക് ചെയ്യും
            if d.get('total_bytes', 0) > 150 * 1024 * 1024:
                raise MaxSizeException("Video exceeded 150MB limit.")

    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            filename = f"vid_{message.chat.id}.mp4"
            
            try:
                bot.edit_message_text(f"🔎 **Searching the web** for '{query}'...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                video_urls = get_video_urls_from_web(query)

                if not video_urls:
                    bot.edit_message_text(f"❌ No suitable videos found on the web for '{query}'.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                download_success = False
                title = "HD Video"
                duration = 0
                width = 0
                height = 0

                # ⚠️ കിട്ടിയ ലിങ്കുകളിൽ 150MB-ക്ക് താഴെയുള്ള ഒരെണ്ണം കിട്ടുന്നത് വരെ പരീക്ഷിക്കും ⚠️
                for video_url in video_urls[:5]: # പരമാവധി 5 വീഡിയോകൾ ട്രൈ ചെയ്യും
                    domain_name = urllib.parse.urlparse(video_url).netloc
                    bot.edit_message_text(f"⏳ **Checking Video from `{domain_name}` (Must be under 150MB)...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    ydl_opts = {
                        'format': 'best', # യാതൊരു ഫയൽസൈസ് ലിമിറ്റും ഇവിടെ വെക്കുന്നില്ല (എറർ വരാതിരിക്കാൻ)
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18,
                        'progress_hooks': [check_size_hook] # പകരം ഈ ഹുക്ക് വഴി സൈസ് ചെക്ക് ചെയ്യും
                    }

                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_url, download=True)
                            title = info.get('title', 'HD Video')
                            duration = info.get('duration', 0)
                            width = info.get('width', 0)
                            height = info.get('height', 0)
                            download_success = True
                            break # ഡൗൺലോഡ് വിജയിച്ചാൽ ലൂപ്പിൽ നിന്ന് പുറത്ത് വരും
                    except MaxSizeException:
                        # 150MB കഴിഞ്ഞാൽ ഈ എറർ വരും, അപ്പോൾ ആ ഫയൽ കളഞ്ഞിട്ട് അടുത്ത വീഡിയോ നോക്കും
                        if os.path.exists(filename):
                            os.remove(filename)
                        continue
                    except Exception as e:
                        if os.path.exists(filename):
                            os.remove(filename)
                        continue

                if not download_success:
                    bot.edit_message_text(f"❌ **Download Failed!**\nAll found videos for '{query}' were larger than 150MB or unavailable.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                bot.edit_message_text(f"📤 **Uploading {title[:30]}... (Using Pyrogram)**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                # Pyrogram വഴി ഫയൽ അയക്കുന്നു
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
