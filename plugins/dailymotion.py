import os
import re
import yt_dlp
import time
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

def setup(bot):

    CHANNEL_USERNAME = "aaawetflix"
    
    # ⚠️ വലിയ ഫയലുകൾ അപ്‌ലോഡ് ചെയ്യാൻ Pyrogram വേണം ⚠️
    # നിങ്ങളുടെ മെയിൻ ഫയലിലെ API_ID ഉം API_HASH ഉം ഇവിടെ ലഭിക്കുന്നുണ്ടെന്ന് ഉറപ്പാക്കുക
    API_ID_STR = os.environ.get("API_ID")
    API_ID = int(API_ID_STR) if API_ID_STR else 0
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = bot.token

    def get_link_from_channel():
        try:
            url = f"https://t.me/s/{CHANNEL_USERNAME}"
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

    @bot.message_handler(commands=['local'])
    def fetch_local_video(message):
        status_msg = bot.send_message(message.chat.id, "📂 **Checking @aaawetflix for new links...**", parse_mode='Markdown')
        
        filename = f"local_{message.chat.id}_{int(time.time())}.mp4"
        
        try:
            video_url = get_link_from_channel()
            
            if not video_url:
                bot.edit_message_text("❌ **No new links found in @aaawetflix!**\nPlease post some video links in your channel.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return

            bot.edit_message_text(f"⏳ **Downloading video in High Quality...**\n🔗 `{video_url}`\n*(Bypassing Cloudflare...)*", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            # ⚠️ 45MB Limit പൂർണ്ണമായും ഒഴിവാക്കി, ഒപ്പം 'best' (ഏറ്റവും കൂടിയ ക്വാളിറ്റി) ആക്കി ⚠️
            ydl_opts = {
                'format': 'best', # യാതൊരു നിയന്ത്രണവുമില്ലാതെ ഏറ്റവും നല്ല ക്വാളിറ്റി എടുക്കും
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
                'age_limit': 18,
                'socket_timeout': 60, # വലിയ വീഡിയോ ആയതുകൊണ്ട് സമയം കൂട്ടി നൽകി
                'retries': 5,
                'extractor_args': {'generic': {'impersonate': 'chrome'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate'
                }
                # progress_hooks പൂർണ്ണമായും എടുത്തുകളഞ്ഞു (സൈസ് ചെക്ക് ചെയ്യില്ല)
            }

            title = "Channel Video"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get('title', 'Channel Video')

            bot.edit_message_text("📤 **Sending High Quality video to chat (Might take a while)...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            # ഫയൽ സൈസ് പരിശോധിക്കുന്നു
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            # ⚠️ 50MB ക്ക് മുകളിലാണെങ്കിൽ Pyrogram ഉപയോഗിച്ച് അപ്‌ലോഡ് ചെയ്യുന്നു ⚠️
            if file_size_mb > 50:
                if not API_ID or not API_HASH:
                    bot.edit_message_text("❌ Error: Cannot upload videos larger than 50MB without API_ID and API_HASH set in your environment.", message.chat.id, status_msg.message_id)
                else:
                    bot.edit_message_text(f"📤 **Uploading large video ({file_size_mb:.1f} MB)...**\n_Please wait, this might take a while._", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    
                    with Client("wetflix_upload_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) as app:
                        app.send_video(
                            chat_id=message.chat.id,
                            video=filename,
                            caption=f"📁 **{title[:50]}**\n🌟 *High Quality | {file_size_mb:.1f} MB*\n📥 _Sourced from @aaawetflix_",
                            parse_mode='Markdown' # Pyrogram ഉപയോഗിക്കുമ്പോൾ supports_streaming ആവശ്യമില്ല
                        )
                    bot.delete_message(message.chat.id, status_msg.message_id)
            else:
                # 50MB ക്ക് താഴെയാണെങ്കിൽ സാധാരണ പോലെ telebot ഉപയോഗിച്ച് വേഗത്തിൽ അപ്‌ലോഡ് ചെയ്യുന്നു
                with open(filename, 'rb') as video_file:
                    bot.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption=f"📁 **{title[:50]}**\n🌟 *High Quality | {file_size_mb:.1f} MB*\n📥 _Sourced from @aaawetflix_",
                        parse_mode='Markdown',
                        supports_streaming=True,
                        timeout=120
                    )
                bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as err:
            try:
                bot.edit_message_text(f"❌ Error processing link: `{str(err)[:100]}`\n\n*(Check if Cloudflare Blocked or Link Invalid)*", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            except: pass
        finally:
            if os.path.exists(filename):
                os.remove(filename)
