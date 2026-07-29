import os
import requests
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # XHamster Video Search Command (/search or /dm)
    @bot.message_handler(commands=['search', 'dm'])
    def search_xhamster(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **XHamster Video Search:**\n\n📖 *Usage:*\n`/search <video name>`\n\n💡 *Example:* `/search mallu hot`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching XHamster for **'{query}'**...", parse_mode='Markdown')

            # XHamster Public API വഴി സെർച്ച് ചെയ്യുന്നു
            url = f"https://xhamster.com/api/v4/search/videos?q={query}&p=1"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                bot.edit_message_text("❌ Search error. Please try another keyword.", message.chat.id, status_msg.message_id)
                return
                
            data = response.json()
            videos = data.get("videos", [])
            
            if not videos:
                bot.edit_message_text(f"❌ No videos found for '{query}'.", message.chat.id, status_msg.message_id)
                return

            markup = InlineKeyboardMarkup(row_width=1)
            for item in videos[:10]: # ആദ്യത്തെ 10 വീഡിയോകൾ എടുക്കുന്നു
                video_id = str(item.get('id'))
                title = item.get('title', 'Video')[:35]
                duration = item.get('duration', 0)
                mins = duration // 60
                secs = duration % 60
                time_str = f"{mins}:{secs:02d}"
                
                markup.add(InlineKeyboardButton(f"🔞 {title}... ({time_str})", callback_data=f"dl_xh_{video_id}"))

            bot.edit_message_text(
                f"🔥 **XHamster Search Results for:** `{query}`\n\n👇 *Select a video to download:*", 
                message.chat.id, 
                status_msg.message_id, 
                reply_markup=markup, 
                parse_mode='Markdown'
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Search Error: `{e}`")

    # Download Handler (ഡൗൺലോഡ് ചെയ്ത് ഫയലായി അയക്കുന്നു)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("dl_xh_"))
    def download_xhamster_video(call):
        try:
            video_id = call.data.replace("dl_xh_", "")
            video_url = f"https://xhamster.com/videos/{video_id}"
            
            bot.answer_callback_query(call.id, "⬇️ Downloading video...", show_alert=False)
            status_msg = bot.send_message(call.message.chat.id, "⏳ **Downloading video from XHamster... Please wait.**", parse_mode='Markdown')

            def run_download():
                filename = f"xh_{video_id}.mp4"
                
                # ടെലഗ്രാം 50MB ലിമിറ്റ് പാലിക്കാൻ ലോ ക്വാളിറ്റി/മീഡിയം ക്വാളിറ്റി ഫോർമാറ്റ് സെറ്റ് ചെയ്യുന്നു
                ydl_opts = {
                    'format': 'best[height<=360][filesize<48M]/best[height<=480][filesize<48M]/worst',
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', 'XHamster Video')

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
                    error_str = str(err)[:150]
                    bot.edit_message_text(f"❌ **Download Failed! (File might be larger than 50MB)**\n\n`{error_str}`", call.message.chat.id, status_msg.message_id, parse_mode='Markdown')
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_download).start()

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: `{e}`")
