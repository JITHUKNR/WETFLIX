import os
import requests
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Video Search Command (/search or /dm)
    @bot.message_handler(commands=['search', 'dm'])
    def search_videos(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Video Search:**\n\n📖 *Usage:*\n`/search <video name>`\n\n💡 *Example:* `/search mallu`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching for **'{query}'**...", parse_mode='Markdown')

            # Redgifs / Free API വഴി സെർച്ച് ചെയ്യുന്നു (എല്ലാ വീഡിയോസും കിട്ടും)
            url = f"https://api.redgifs.com/v2/search/gifs?search_text={query}&count=10"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                bot.edit_message_text("❌ Search error. Please try another keyword.", message.chat.id, status_msg.message_id)
                return
                
            data = response.json()
            gifs = data.get("gifs", [])
            
            if not gifs:
                bot.edit_message_text(f"❌ No videos found for '{query}'.", message.chat.id, status_msg.message_id)
                return

            markup = InlineKeyboardMarkup(row_width=1)
            for idx, item in enumerate(gifs):
                title = item.get('title', f'Video {idx+1}')
                if not title or title.strip() == "":
                    title = f"Exclusive Video {idx+1}"
                title = title[:35]
                
                # വീഡിയോയുടെ ഡൗൺലോഡ് ലിങ്ക് സേവ് ചെയ്യുന്നു
                urls = item.get('urls', {})
                hd_url = urls.get('hd') or urls.get('sd')
                
                if hd_url:
                    # കോൾബാക്ക് ഡാറ്റ വലുതാകാതിരിക്കാൻ ഷോർട്ട് ഐഡി നൽകുന്നു
                    markup.add(InlineKeyboardButton(f"🔞 {title}", callback_data=f"dl_rg_{idx}"))

            # താൽക്കാലികമായി ലിങ്ക് സേവ് ചെയ്യാൻ ഗ്ലോബൽ ഡിക്ഷണറി ഉപയോഗിക്കുന്നു
            if not hasattr(bot, 'search_cache'):
                bot.search_cache = {}
            bot.search_cache[message.from_user.id] = gifs

            bot.edit_message_text(
                f"🔥 **Search Results for:** `{query}`\n\n👇 *Select a video to download:*", 
                message.chat.id, 
                status_msg.message_id, 
                reply_markup=markup, 
                parse_mode='Markdown'
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Search Error: `{e}`")

    # Download Handler (ഡൗൺലോഡ് ചെയ്ത് ഫയലായി അയക്കുന്നു)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("dl_rg_"))
    def download_video_file(call):
        try:
            idx = int(call.data.replace("dl_rg_", ""))
            user_id = call.from_user.id
            
            if not hasattr(bot, 'search_cache') or user_id not in bot.search_cache:
                bot.answer_callback_query(call.id, "❌ Session expired. Please search again.", show_alert=True)
                return

            gifs = bot.search_cache[user_id]
            if idx >= len(gifs):
                bot.answer_callback_query(call.id, "❌ Invalid selection.", show_alert=True)
                return

            item = gifs[idx]
            urls = item.get('urls', {})
            video_url = urls.get('hd') or urls.get('sd')
            title = item.get('title', 'Video')

            bot.answer_callback_query(call.id, "⬇️ Downloading video...", show_alert=False)
            status_msg = bot.send_message(call.message.chat.id, "⏳ **Downloading video file... Please wait.**", parse_mode='Markdown')

            def run_download():
                filename = f"video_{user_id}.mp4"
                try:
                    # വീഡിയോ ഡൗൺലോഡ് ചെയ്യുന്നു
                    vid_data = requests.get(video_url, stream=True, timeout=30)
                    with open(filename, 'wb') as f:
                        for chunk in vid_data.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)

                    # ഫയൽ സൈസ് പരിശോധിക്കുന്നു (50MB മുകളിലാണോ എന്ന് നോക്കാൻ)
                    file_size = os.path.getsize(filename) / (1024 * 1024)
                    if file_size > 48:
                        bot.edit_message_text("❌ **File is larger than 50MB limit.** Please try a smaller video.", call.message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    # ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            call.message.chat.id, 
                            video_file, 
                            caption=f"🔥 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=120
                        )

                    bot.delete_message(call.message.chat.id, status_msg.message_id)

                except Exception as err:
                    bot.edit_message_text(f"❌ **Download Failed:** `{err}`", call.message.chat.id, status_msg.message_id, parse_mode='Markdown')
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_download).start()

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: `{e}`")
