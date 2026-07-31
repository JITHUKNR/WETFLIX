import os
import re
import yt_dlp
import time
import requests
import subprocess
import glob
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ⚠️ നിങ്ങൾക്ക് ഈ സമയം മാറ്റാവുന്നതാണ് ⚠️
COOLDOWN_TIME = 60  # ബട്ടൺ വീണ്ടും അമർത്താനുള്ള സമയപരിധി (സെക്കൻഡിൽ)
DELETE_TIME = 120   # വീഡിയോ തനിയെ ഡിലീറ്റ് ആവാനുള്ള സമയം (സെക്കൻഡിൽ)

user_cooldowns = {}

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

    def split_video(input_file, chat_id):
        split_prefix = f"split_{chat_id}_{int(time.time())}"
        try:
            command = [
                'ffmpeg', '-i', input_file,
                '-c', 'copy', '-map', '0',
                '-segment_time', '00:03:00',
                '-f', 'segment',
                '-reset_timestamps', '1',
                f"{split_prefix}_part%03d.mp4"
            ]
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            split_files = sorted(glob.glob(f"{split_prefix}_part*.mp4"))
            return split_files
        except Exception as e:
            print(f"Split Error: {e}")
            return []

    # ⚠️ സ്റ്റാർട്ട് കമാൻഡ് അടിക്കുമ്പോൾ BOOM ബട്ടൺ വരാൻ ⚠️
    @bot.message_handler(commands=['start', 'boom'])
    def send_welcome(message):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💥 BOOM", callback_data="boom_click"))
        
        bot.send_message(
            message.chat.id,
            f"⚡ **Welcome {message.from_user.first_name}!**\n\n👇 Click the **BOOM** button below to get videos:",
            reply_markup=markup,
            parse_mode='Markdown'
        )

    # ⚠️ BOOM ബട്ടൺ വർക്ക് ചെയ്യുന്ന ഭാഗം ⚠️
    @bot.callback_query_handler(func=lambda call: call.data == "boom_click")
    def handle_boom_button(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        current_time = time.time()

        # ടൈമർ പരിശോധിക്കുന്നു
        if user_id in user_cooldowns:
            time_passed = current_time - user_cooldowns[user_id]
            if time_passed < COOLDOWN_TIME:
                time_left = int(COOLDOWN_TIME - time_passed)
                # സമയം കഴിഞ്ഞില്ലെങ്കിൽ സ്ക്രീനിൽ അലർട്ട് കാണിക്കും
                bot.answer_callback_query(call.id, f"⏳ Please wait {time_left} seconds before clicking again!", show_alert=True)
                return
        
        user_cooldowns[user_id] = current_time
        bot.answer_callback_query(call.id, "💥 Processing your request...")

        status_msg = bot.send_message(chat_id, "📂 **Searching for new video...**", parse_mode='Markdown')
        
        filename = f"local_{chat_id}_{int(time.time())}.mp4"
        
        try:
            video_url = get_link_from_channel()
            
            if not video_url:
                bot.edit_message_text("❌ **No new links available right now!**", chat_id, status_msg.message_id, parse_mode='Markdown')
                del user_cooldowns[user_id] # ലിങ്ക് ഇല്ലെങ്കിൽ ടൈമർ ഒഴിവാക്കുന്നു
                return

            bot.edit_message_text(f"⏳ **Downloading in Highest Quality...**\n🔗 `{video_url}`", chat_id, status_msg.message_id, parse_mode='Markdown')

            ydl_opts = {
                'format': 'best', 
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
                'age_limit': 18,
                'socket_timeout': 60,
                'retries': 5,
                'extractor_args': {'generic': {'impersonate': 'chrome'}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate'
                }
            }

            title = "Video"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get('title', 'Video')

            file_size_mb = os.path.getsize(filename) / (1024 * 1024)
            
            messages_to_delete = [] # അയച്ച മെസ്സേജുകൾ സേവ് ചെയ്യാൻ

            if file_size_mb > 48:
                bot.edit_message_text(f"✂️ **Video is {file_size_mb:.1f} MB. Splitting into parts...**", chat_id, status_msg.message_id, parse_mode='Markdown')
                
                parts = split_video(filename, chat_id)
                
                if parts:
                    bot.edit_message_text(f"📤 **Uploading {len(parts)} parts...**", chat_id, status_msg.message_id, parse_mode='Markdown')
                    
                    for i, part in enumerate(parts, 1):
                        with open(part, 'rb') as video_file:
                            # ⚠️ ചാനലിന്റെ പേര് ഇല്ലാതെ ക്ലീൻ ക്യാപ്ഷൻ ⚠️
                            msg = bot.send_video(
                                chat_id=chat_id,
                                video=video_file,
                                caption=f"📁 **{title[:50]}**\n🌟 *Part {i}/{len(parts)}*",
                                parse_mode='Markdown',
                                supports_streaming=True,
                                timeout=120
                            )
                            messages_to_delete.append(msg.message_id)
                        os.remove(part)
                    
                    bot.delete_message(chat_id, status_msg.message_id)
                else:
                    bot.edit_message_text("❌ Failed to split the large video.", chat_id, status_msg.message_id)
            else:
                bot.edit_message_text("📤 **Sending High Quality video...**", chat_id, status_msg.message_id, parse_mode='Markdown')
                
                with open(filename, 'rb') as video_file:
                    # ⚠️ ചാനലിന്റെ പേര് ഇല്ലാതെ ക്ലീൻ ക്യാപ്ഷൻ ⚠️
                    msg = bot.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        caption=f"📁 **{title[:50]}**",
                        parse_mode='Markdown',
                        supports_streaming=True,
                        timeout=120
                    )
                    messages_to_delete.append(msg.message_id)
                
                bot.delete_message(chat_id, status_msg.message_id)

            # ⚠️ ഓട്ടോ ഡിലീറ്റ് ഫംഗ്ഷൻ (ബാക്ക്ഗ്രൗണ്ടിൽ വർക്ക് ചെയ്യും) ⚠️
            def auto_delete_task(chat, msg_ids):
                time.sleep(DELETE_TIME)
                for m_id in msg_ids:
                    try:
                        bot.delete_message(chat, m_id)
                    except:
                        pass

            if messages_to_delete:
                threading.Thread(target=auto_delete_task, args=(chat_id, messages_to_delete)).start()

        except Exception as err:
            try:
                bot.edit_message_text(f"❌ Error processing link: `{str(err)[:100]}`", chat_id, status_msg.message_id, parse_mode='Markdown')
            except: pass
        finally:
            if os.path.exists(filename):
                os.remove(filename)
