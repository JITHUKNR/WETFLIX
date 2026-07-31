import os
import re
import yt_dlp
import time
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # താങ്കളുടെ ചാനലിന്റെ പേര്
    CHANNEL_USERNAME = "aaawetflix"

    def get_link_from_channel():
        try:
            # ടെലഗ്രാം വെബ് വഴി പബ്ലിക് ചാനൽ വായിക്കുന്നു
            url = f"https://t.me/s/{CHANNEL_USERNAME}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers)
            
            # ⚠️ ഏത് വെബ്സൈറ്റിന്റെ ലിങ്ക് ആയാലും (http/https) അത് എടുക്കാൻ പറയുന്നു ⚠️
            urls = re.findall(r'(https?://[^\s"\'<>]+)', r.text)
            
            if not urls:
                return None
                
            # വെബ്സൈറ്റിന്റെ പേര് മാത്രമുള്ള ലിങ്കുകളും അനാവശ്യ ലിങ്കുകളും ഒഴിവാക്കുന്നു
            valid_urls = []
            for u in urls:
                # ടെലഗ്രാമിന്റെ സ്വന്തം ലിങ്കുകളോ, വെറും .com മാത്രമുള്ള ലിങ്കുകളോ ഒഴിവാക്കുന്നു
                if 't.me' not in u and 'telegram.org' not in u and len(u) > 25:
                    # iframe കോഡിൽ നിന്നുള്ള ലിങ്ക് ആണെങ്കിൽ അതെടുക്കുന്നു
                    if 'embed' in u or '/video/' in u or '/videos/' in u or 'xhaccess' in u or 'txnhh' in u:
                        valid_urls.append(u)
            
            if not valid_urls:
                # മുകളിലെ കണ്ടീഷൻ വർക്ക് ആയില്ലെങ്കിൽ കിട്ടിയ വലിയ ലിങ്കുകൾ എല്ലാം എടുക്കുന്നു
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

            bot.edit_message_text(f"⏳ **Downloading video...**\n🔗 `{video_url}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            ydl_opts = {
                'format': 'best[height<=480]/worst', 
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
                'age_limit': 18,
                'socket_timeout': 15,
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
                bot.edit_message_text(f"❌ Error downloading link: `{str(err)[:80]}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            except: pass
        finally:
            if os.path.exists(filename):
                os.remove(filename)
