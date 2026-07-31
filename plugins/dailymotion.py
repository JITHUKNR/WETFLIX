import os
import re
import urllib.parse
import threading
import queue
import requests
import random

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

download_queue = queue.Queue()
is_downloading = False

def setup(bot):
    def get_video_urls(query):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36"}
        encoded = urllib.parse.quote(query)
        all_links = []
        
        try:
            r = requests.get(f"https://www.xvideos.com/?k={encoded}", headers=headers, timeout=5)
            urls = re.findall(r'href="(/video[^"]+)"', r.text)
            for u in urls:
                if 'tags' not in u and 'search' not in u and 'profiles' not in u:
                    all_links.append(f"https://www.xvideos.com{u}")
        except: pass
        
        try:
            r = requests.get(f"https://www.xnxx.com/search/{encoded}", headers=headers, timeout=5)
            urls = re.findall(r'href="(/video-[^"]+)"', r.text)
            for u in urls:
                all_links.append(f"https://www.xnxx.com{u}")
        except: pass
        
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

    # ⚠️ നേരിട്ടുള്ള വീഡിയോ ലിങ്ക് കണ്ടുപിടിക്കാൻ ⚠️
    def get_direct_mp4_url(video_page_url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36"}
        try:
            r = requests.get(video_page_url, headers=headers, timeout=10)
            
            # XVideos & XNXX
            match = re.search(r"setVideoUrlHigh\('([^']+)'\)", r.text)
            if match: return match.group(1), "HD Video"
            
            match = re.search(r"setVideoUrlLow\('([^']+)'\)", r.text)
            if match: return match.group(1), "SD Video"

            # Pornhub
            match = re.search(r'"quality":"720","videoUrl":"([^"]+)"', r.text)
            if match: return match.group(1).replace("\\/", "/"), "720p Video"
            
        except Exception:
            pass
        return None, None

    def process_queue():
        global is_downloading
        while True:
            task = download_queue.get()
            is_downloading = True
            
            message, query, status_msg = task
            
            try:
                bot.edit_message_text(f"🔎 **Searching** for '{query}'...", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                video_urls = get_video_urls(query)

                if not video_urls:
                    bot.edit_message_text(f"❌ No videos found for '{query}'.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                direct_url = None
                title = "Video"

                for video_url in video_urls[:5]:
                    domain_name = urllib.parse.urlparse(video_url).netloc
                    try:
                        bot.edit_message_text(f"⏳ **Checking Video from `{domain_name}`...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    except: pass 

                    direct_url, title = get_direct_mp4_url(video_url)
                    if direct_url:
                        break # നേരിട്ടുള്ള mp4 ലിങ്ക് കിട്ടിയാൽ അവിടെ വെച്ച് നിർത്തും

                if not direct_url:
                    bot.edit_message_text(f"❌ **Failed!**\nCould not extract direct video link.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    download_queue.task_done()
                    is_downloading = False
                    continue

                try:
                    bot.edit_message_text(f"📤 **Sending {title[:30]}...**\n(Using Telegram Direct Link)", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                except: pass

                # ⚠️ ട്രിക്ക് ഇവിടെയാണ്: ഫയൽ ഡൗൺലോഡ് ചെയ്യുന്നില്ല, ലിങ്ക് നേരിട്ട് അയക്കുന്നു! ⚠️
                bot.send_video(
                    chat_id=message.chat.id,
                    video=direct_url,
                    caption=f"🔞 **{query.title()}...**\n\n📥 _Sent via WETFLIX (Direct Stream)_",
                    parse_mode='Markdown',
                    supports_streaming=True
                )
                
                try:
                    bot.delete_message(message.chat.id, status_msg.message_id)
                except: pass

            except Exception as err:
                error_str = str(err)[:150]
                try:
                    bot.send_message(message.chat.id, f"❌ **Error!**\n\n`{error_str}`", parse_mode='Markdown')
                except: pass
            finally:
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
