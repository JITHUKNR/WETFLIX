import os
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Automatic Google Search & Video Downloader Command
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def auto_google_downloader(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Auto Video Search & Downloader:**\n\n📖 *Usage:*\n`/search <Any Video Name>`\n\n💡 *Example:* `/search mallu comedy`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching Google for **'{query}'** and downloading...", parse_mode='Markdown')

            def run_download():
                filename = f"vid_{message.chat.id}.mp4"
                
                # yt-dlp ഓട്ടോമാറ്റിക് സെർച്ച് വഴി ഗൂഗിളിൽ നിന്ന്/വെബിൽ നിന്ന് ആദ്യത്തെ വീഡിയോ എടുക്കുന്നു
                ydl_opts = {
                    'format': 'best[height<=360][filesize<48M]/best[height<=480][filesize<48M]/worst',
                    'default_search': 'ytsearch1',  # വെബിൽ നിന്ന് നേരിട്ട് സെർച്ച് ചെയ്യാൻ
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(query, download=True)
                        if 'entries' in info:
                            info = info['entries'][0]
                        title = info.get('title', 'Downloaded Video')

                    # ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔥 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=120
                        )

                    bot.delete_message(message.chat.id, status_msg.message_id)

                except Exception as err:
                    error_str = str(err)[:150]
                    bot.edit_message_text(f"❌ **Download Failed!**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_download).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
