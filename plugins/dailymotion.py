import os
import re
import yt_dlp
import time
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    CHANNEL_USERNAME = "aaawetflix"

    def get_link_from_channel():
        try:
            url = f"https://t.me/s/{CHANNEL_USERNAME}"
            # Cloudflare-നെ പറ്റിക്കാൻ ഒറിജിനൽ ബ്രൗസർ ഹെഡറുകൾ നൽകുന്നു
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            r = requests.get(url, headers=headers)
            
            urls = re.findall(r'(https?://[^\s"\'<>]+)', r.text)
            
            if not urls:
                return None
                
            valid_urls = []
            for u in urls:
                if 't.me' not in u and 'telegram.org' not in u and len(u) > 25:
                    if 'embed' in u or '/video/' in u or '/videos/' in u or 'xhaccess' in u or 'txnhh' in u:
                        valid_urls.append(u)
            
            if not valid_urls:
                valid_urls = [u for u in urls if 't.me' not in u and len(u) > 20]
                
            if not valid_urls:
                return None

            valid_urls.reverse()
            
            sent_file = "sent_links.txt"
            sent_links = set()
            if os.path.exists(sent_file):
                with open(sent_file, "r", encoding="utf-8") as sf:
                    sent_links = set(line.strip() for line in sf.readlines())
            
            for u in valid_urls:
                if u not in sent_links:
                    with open(sent_file, "a", encoding="utf-8") as sf:
                        sf.write(u + "\n")
                    return u
        except Exception as e:
            print(f"Scraping Error: {e}")
            
        return None

    class MaxSizeException(Exception): pass

    def check_size_hook(d):
        if d['status'] == 'downloading':
            if d.get('downloaded_bytes', 0) > 45 * 1024 * 1024:
                raise MaxSizeException("Exceeded 45MB limit.")

    @bot.message_handler(commands=['local'])
    def fetch_local_video(message):
        status_msg = bot.send_message(message.chat.id, "📂 **Checking @aaawetflix for new links...**", parse_mode='Markdown')
        
        filename = f"local_{message.chat.id}_{int(time.time())}.mp4"
        
        try:
            video_url = get_link_from_channel()
            
            if not video_url:
                bot.edit_message_text("❌ **No new links found in @aaawetflix!**\nPlease post some video links in your channel.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return

            bot.edit_message_text(f"⏳ **Downloading video...**\n🔗 `{video_url}`\n*(Bypassing Cloudflare...)*", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            # ⚠️ Cloudflare ബ്ലോക്ക് മറികടക്കാനുള്ള പ്രത്യേക yt-dlp സെറ്റിംഗ്സ് ⚠️
            ydl_opts = {
                'format': 'best[height<=480]/worst', 
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
                'age_limit': 18,
                'socket_timeout': 30, # സമയം കൂട്ടി നൽകുന്നു
                'retries': 5, # ബ്ലോക്ക് ആയാലും 5 തവണ വീണ്ടും ശ്രമിക്കും
                'extractor_args': {'generic': {'impersonate': 'chrome'}}, # ഒറിജിനൽ ക്രോം ആണെന്ന് തെറ്റിദ്ധരിപ്പിക്കുന്നു
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate'
                },
                'progress_hooks': [check_size_hook]
            }

            title = "Channel Video"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get('title', 'Channel Video')

            bot.edit_message_text("📤 **Sending video to chat...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            with open(filename, 'rb') as video_file:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=video_file,
                    caption=f"📁 **{title[:50]}**\n\n📥 _Sourced from @aaawetflix_",
                    parse_mode='Markdown',
                    supports_streaming=True
                )
            
            bot.delete_message(message.chat.id, status_msg.message_id)

        except MaxSizeException:
            bot.edit_message_text("❌ The video from this link was larger than 45MB. Skipped to next!", message.chat.id, status_msg.message_id)
        except Exception as err:
            try:
                bot.edit_message_text(f"❌ Error downloading link: `{str(err)[:80]}`\n\n*(Cloudflare Blocked or Invalid Link)*", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            except: pass
        finally:
            if os.path.exists(filename):
                os.remove(filename)
