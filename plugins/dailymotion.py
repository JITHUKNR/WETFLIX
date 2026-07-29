import os
import requests
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Premium Video Search Command (/search or /dm)
    @bot.message_handler(commands=['search', 'dm'])
    def search_videos(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Premium Video Search:**\n\n📖 *Usage:*\n`/search <video name>`\n\n💡 *Example:* `/search hot mallu`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching for **'{query}'**...", parse_mode='Markdown')

            url = f"https://www.eporner.com/api/v2/video/search/?query={query}&per_page=10"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                bot.edit_message_text("❌ API Error. Please try again later.", message.chat.id, status_msg.message_id)
                return
                
            data = response.json()
            videos = data.get("videos", [])
            
            if not videos:
                bot.edit_message_text(f"❌ No videos found for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id)
                return

            markup = InlineKeyboardMarkup(row_width=1)
            for item in videos:
                video_id = item['id']
                title = item['title'][:35]
                duration = item.get('length_sec', 0)
                mins = duration // 60
                secs = duration % 60
                time_str = f"{mins}:{secs:02d}"
                
                button_text = f"🔞 {title}... ({time_str})"
                markup.add(InlineKeyboardButton(button_text, callback_data=f"dl_ep_{video_id}"))

            bot.edit_message_text(
                f"🔥 **Premium Search Results:** `{query}`\n\n👇 *Select a video to download:*", 
                message.chat.id, 
                status_msg.message_id, 
                reply_markup=markup, 
                parse_mode='Markdown'
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Search Error: `{e}`")

    # Download Handler
    @bot.callback_query_handler(func=lambda call: call.data.startswith("dl_ep_"))
    def download_premium_video(call):
        try:
            video_id = call.data.replace("dl_ep_", "")
            
            bot.answer_callback_query(call.id, "⬇️ Preparing video...", show_alert=False)
            status_msg = bot.send_message(call.message.chat.id, "⏳ **Downloading Premium Video...**\n*This might take a minute based on size.*", parse_mode='Markdown')

            def run_download():
                filename = f"vid_{video_id}.mp4"
                
                try:
                    api_url = f"https://www.eporner.com/api/v2/video/id/?id={video_id}"
                    res = requests.get(api_url, timeout=10).json()
                    video_url = res.get('url')
                    title = res.get('title', 'Premium Video')

                    if not video_url:
                        bot.edit_message_text("❌ Could not fetch video link.", call.message.chat.id, status_msg.message_id)
                        return

                    # ⚠️ 50MB ലിമിറ്റ് മറികടക്കാൻ സൈസ് കുറഞ്ഞ ഫോർമാറ്റ് മാത്രം എടുക്കാൻ പറയുന്നു
                    ydl_opts = {
                        'format': 'best[height<=360][filesize<45M]/worst',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])

                    # ഡൗൺലോഡ് കഴിഞ്ഞാൽ വീഡിയോ അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            call.message.chat.id, 
                            video_file, 
                            caption=f"🔥 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=120  # വലിയ ഫയലുകൾ അയക്കാൻ സമയം കൊടുക്കുന്നു
                        )

                    bot.delete_message(call.message.chat.id, status_msg.message_id)

                except Exception as err:
                    # എറർ വന്നാൽ യഥാർത്ഥ കാരണം പ്രിന്റ് ചെയ്യുന്നു
                    error_str = str(err)[:150]
                    bot.edit_message_text(f"❌ **Download Failed!**\n\n`{error_str}`\n\n*(Tip: Try selecting a shorter video under 5 minutes)*", call.message.chat.id, status_msg.message_id, parse_mode='Markdown')
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_download).start()

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: `{e}`")
