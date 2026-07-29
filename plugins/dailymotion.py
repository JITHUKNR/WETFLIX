import os
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Safe Video Downloader Command (/search or /dm or /dl or /video)
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def robust_video_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔍 **Video Search & Downloader:**\n\n📖 *Usage:*\n`/search <Video Name>`\n\n💡 *Example:* `/search mallu hot`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching and downloading **'{query}'**...", parse_mode='Markdown')

            def run_download():
                filename = f"vid_{message.chat.id}.mp4"
                
                # yt-dlp സുരക്ഷിതമായി വെബിൽ നിന്ന് വീഡിയോ തപ്പി എടുക്കാനുള്ള കോൺഫിഗറേഷൻ
                ydl_opts = {
                    'format': 'best[height<=360][filesize<48M]/worst',
                    'default_search': 'auto',
                    'noplaylist': True,
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                }

                try:
                    search_query = f"gvsearch1:{query}"  # യൂട്യൂബ് ഒഴിവാക്കി ജനറൽ വെബ് സെർച്ച് ഉപയോഗിക്കുന്നു
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(search_query, download=True)
                        if 'entries' in info:
                            if not info['entries']:
                                raise Exception("No videos found for this keyword. Try another name.")
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
