import os
import re
import yt_dlp
import time
import requests
import subprocess
import glob
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    CHANNEL_USERNAME = "aaawetflix"

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

    # വീഡിയോ മുറിക്കാനുള്ള ഫംഗ്ഷൻ (48MB വെച്ച് മുറിക്കും)
    def split_video(input_file, chat_id):
        split_prefix = f"split_{chat_id}_{int(time.time())}"
        # 48MB-ക്ക് തുല്യമായ സൈസ് ലിമിറ്റ് നൽകുന്നു (ടെലഗ്രാം സേഫ്റ്റിക്ക് വേണ്ടി)
        target_size_bytes = 48 * 1024 * 1024 
        
        try:
            # ffmpeg ഉപയോഗിച്ച് വീഡിയോ സൈസ് അടിസ്ഥാനമാക്കി മുറിക്കുന്നു
            command = [
                'ffmpeg', '-i', input_file,
                '-c', 'copy', '-map', '0',
                '-segment_time', '00:03:00', # ശരാശരി 3 മിനിറ്റ് വെച്ച് മുറിക്കുന്നു (സൈസ് കുറയ്ക്കാൻ)
                '-f', 'segment',
                '-reset_timestamps', '1',
                f"{split_prefix}_part%03d.mp4"
            ]
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # മുറിച്ച ഫയലുകളുടെ ലിസ്റ്റ് എടുക്കുന്നു
            split_files = sorted(glob.glob(f"{split_prefix}_part*.mp4"))
            return split_files
        except Exception as e:
            print(f"Split Error: {e}")
            return []

    @bot.message_handler(commands=['local'])
    def fetch_local_video(message):
        status_msg = bot.send_message(message.chat.id, "📂 **Checking @aaawetflix for new links...**", parse_mode='Markdown')
        
        filename = f"local_{message.chat.id}_{int(time.time())}.mp4"
        
        try:
            video_url = get_link_from_channel()
            
            if not video_url:
                bot.edit_message_text("❌ **No new links found in @aaawetflix!**\nPlease post some video links in your channel.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return

            bot.edit_message_text(f"⏳ **Downloading video in Highest Quality...**\n🔗 `{video_url}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            # ⚠️ 45MB ലിമിറ്റ് ഒഴിവാക്കി, ക്വാളിറ്റി 'best' ആക്കി ⚠️
            ydl_opts = {
                'format': 'best', # യാതൊരു നിയന്ത്രണവുമില്ലാതെ ഏറ്റവും നല്ല ക്വാളിറ്റി എടുക്കും
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
                'age_limit': 18,
                'socket_timeout': 60, # വലിയ ഫയലുകൾക്ക് സമയം കൂടുതൽ നൽകി
                'retries': 5,
                'extractor_args': {'generic': {'impersonate': 'chrome'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate'
                }
            }

            title = "Channel Video"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get('title', 'Channel Video')

            # ഡൗൺലോഡ് ചെയ്ത ഫയലിന്റെ സൈസ് പരിശോധിക്കുന്നു
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            if file_size_mb > 48:
                # 48MB-ക്ക് മുകളിലാണെങ്കിൽ വീഡിയോ മുറിക്കുന്നു
                bot.edit_message_text(f"✂️ **Video is {file_size_mb:.1f} MB (Too Large). Splitting into parts...**\n_Please wait..._", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                parts = split_video(filename, message.chat.id)
                
                if parts:
                    bot.edit_message_text(f"📤 **Uploading {len(parts)} parts...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    
                    for i, part in enumerate(parts, 1):
                        with open(part, 'rb') as video_file:
                            bot.send_video(
                                chat_id=message.chat.id,
                                video=video_file,
                                caption=f"📁 **{title[:40]}**\n🌟 *High Quality (Part {i}/{len(parts)})*\n📥 _Sourced from @aaawetflix_",
                                parse_mode='Markdown',
                                supports_streaming=True,
                                timeout=120
                            )
                        os.remove(part) # അയച്ച ശേഷം പാർട്ട് ഡിലീറ്റ് ചെയ്യുന്നു
                    
                    bot.delete_message(message.chat.id, status_msg.message_id)
                else:
                    bot.edit_message_text("❌ Failed to split the large video.", message.chat.id, status_msg.message_id)
            else:
                # 48MB-ക്ക് താഴെയാണെങ്കിൽ നേരിട്ട് അയക്കുന്നു
                bot.edit_message_text("📤 **Sending High Quality video to chat...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                
                with open(filename, 'rb') as video_file:
                    bot.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption=f"📁 **{title[:50]}**\n🌟 *High Quality*\n📥 _Sourced from @aaawetflix_",
                        parse_mode='Markdown',
                        supports_streaming=True,
                        timeout=120
                    )
                bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as err:
            try:
                bot.edit_message_text(f"❌ Error processing link: `{str(err)[:100]}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            except: pass
        finally:
            if os.path.exists(filename):
                os.remove(filename)
