import os
import requests
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Dailymotion Search Command (/search അല്ലെങ്കിൽ /dm)
    @bot.message_handler(commands=['search', 'dm'])
    def search_dailymotion(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Dailymotion Search:**\n\nഉപയോഗിക്കേണ്ട വിധം:\n`/search <വീഡിയോയുടെ പേര്>`\n\nഉദാഹരണത്തിന്: `/search funny cats`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Dailymotion-ൽ **'{query}'** സെർച്ച് ചെയ്യുന്നു...", parse_mode='Markdown')

            # Dailymotion API വഴി സെർച്ച് ചെയ്യുന്നു
            url = f"https://api.dailymotion.com/videos?fields=id,title,duration&search={query}&limit=5"
            response = requests.get(url, timeout=10)
            data = response.json()

            videos = data.get("list", [])
            if not videos:
                bot.edit_message_text("❌ ഈ പേരിൽ Dailymotion-ൽ വീഡിയോകൾ ഒന്നും കണ്ടില്ല.", message.chat.id, status_msg.message_id)
                return

            markup = InlineKeyboardMarkup(row_width=1)
            for item in videos:
                video_id = item['id']
                title = item['title'][:35]  # ബട്ടണിൽ ഒതുങ്ങാൻ ടൈറ്റിൽ ചെറുതാക്കുന്നു
                duration = item.get('duration', 0)
                mins = duration // 60
                secs = duration % 60
                time_str = f"{mins}:{secs:02d}"
                
                button_text = f"🎬 {title}... ({time_str})"
                markup.add(InlineKeyboardButton(button_text, callback_data=f"dl_dm_{video_id}"))

            bot.edit_message_text(
                f"🔍 **Dailymotion Search Results:** `{query}`\n\nഡൗൺലോഡ് ചെയ്യേണ്ട വീഡിയോ താഴെ നിന്ന് തിരഞ്ഞെടുക്കൂ 👇", 
                message.chat.id, 
                status_msg.message_id, 
                reply_markup=markup, 
                parse_mode='Markdown'
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Search Error: `{e}`")

    # ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ വീഡിയോ ഡൗൺലോഡ് ചെയ്ത് അയക്കുന്ന ഫംഗ്ഷൻ
    @bot.callback_query_handler(func=lambda call: call.data.startswith("dl_dm_"))
    def download_dailymotion_video(call):
        try:
            video_id = call.data.replace("dl_dm_", "")
            video_url = f"https://www.dailymotion.com/video/{video_id}"
            
            bot.answer_callback_query(call.id, "⬇️ Downloading video...", show_alert=False)
            status_msg = bot.send_message(call.message.chat.id, "⏳ **Dailymotion-ൽ നിന്ന് വീഡിയോ ഡൗൺലോഡ് ചെയ്യുന്നു...**\nദയവായി കുറച്ചു സെക്കൻഡ് കാത്തിരിക്കൂ.")

            def run_download():
                filename = f"dm_{video_id}.mp4"
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        title = info.get('title', 'Dailymotion Video')

                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            call.message.chat.id, 
                            video_file, 
                            caption=f"🎥 **{title}**\n\n📥 Downloaded from Dailymotion via WETFLIX Bot", 
                            parse_mode='Markdown'
                        )

                    bot.delete_message(call.message.chat.id, status_msg.message_id)

                except Exception as err:
                    bot.edit_message_text(f"❌ Video Download Failed: `{err}`", call.message.chat.id, status_msg.message_id, parse_mode='Markdown')
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_download).start()

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: `{e}`")
