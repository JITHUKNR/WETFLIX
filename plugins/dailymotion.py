import os
import re
import yt_dlp
import time
from pyrogram import Client
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    # താങ്കളുടെ ടെലഗ്രാം ചാനലിന്റെ യൂസർനെയിം
    CHANNEL_USERNAME = "@aaawetflix"

    # ടെലഗ്രാം ചാനലിൽ നിന്ന് ലിങ്കുകൾ ഓട്ടോമാറ്റിക് ആയി എടുക്കുന്ന ഫംഗ്ഷൻ
    def get_link_from_channel():
        if not API_ID or not API_HASH:
            return None
            
        try:
            # Pyrogram വഴി ചാനൽ റീഡ് ചെയ്യുന്നു
            with Client("wetflix_channel_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) as app:
                messages = app.get_chat_history(CHANNEL_USERNAME, limit=50)
                
                # ഇതിനകം അയച്ച ലിങ്കുകൾ സേവ് ചെയ്തു വെക്കുന്ന ഫയൽ
                sent_file = "sent_links.txt"
                sent_links = set()
                if os.path.exists(sent_file):
                    with open(sent_file, "r", encoding="utf-8") as sf:
                        sent_links = set(line.strip() for line in sf.readlines())
                
                for message in messages:
                    if message.text:
                        # മെസ്സേജിൽ നിന്ന് ലിങ്കുകൾ കണ്ടുപിടിക്കുന്നു
                        urls = re.findall(r'https?://[^\s]+', message.text)
                        for url in urls:
                            if url not in sent_links:
                                with open(sent_file, "a", encoding="utf-8") as sf:
                                    sf.write(url + "\n")
                                return url
        except Exception as e:
            print(f"Channel Read Error: {e}")
            
        return None

    # സൈസ് 45MB-ൽ കൂടാൻ പാടില്ല എന്ന് ഉറപ്പാക്കാൻ
    class MaxSizeException(Exception): pass

    def check_size_hook(d):
        if d['status'] == 'downloading':
            if d.get('downloaded_bytes', 0) > 45 * 1024 * 1024:
                raise MaxSizeException("Exceeded 45MB limit.")

    # ⚠️ ബട്ടണിന് പകരം കമാൻഡ് വഴി പ്രവർത്തിക്കുന്നു ⚠️
    @bot.message_handler(commands=['local'])
    def fetch_local_video(message):
        status_msg = bot.send_message(message.chat.id, "📂 **Checking your Telegram channel (@aaawetflix) for links...**", parse_mode='Markdown')
        
        filename = f"local_{message.chat.id}_{int(time.time())}.mp4"
        
        try:
            video_url = get_link_from_channel()
            
            if not video_url:
                bot.edit_message_text("❌ **No new links found in @aaawetflix!**\nPlease post some video links in your channel first.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return

            bot.edit_message_text(f"⏳ **Downloading video from channel link...**\n🔗 `{video_url}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

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
