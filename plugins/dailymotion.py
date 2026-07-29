import os
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Global 18+ Video Search & Downloader
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def global_adult_downloader(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **18+ Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search hot mallu`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching Global 18+ Network for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                try:
                    # Google SafeSearch ഒഴിവാക്കി, നേരിട്ട് ഏറ്റവും വലിയ 18+ ഡാറ്റാബേസിൽ (Pornhub) സെർച്ച് ചെയ്യുന്നു
                    search_query = f"phsearch1:{query}"

                    ydl_opts = {
                        'format': 'best[height<=480][filesize<49.5M]/best[height<=360][filesize<49.5M]/worst',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18  # 18+ ഫിൽറ്റർ ബൈപ്പാസ് ചെയ്യാൻ
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(search_query, download=True)
                        if 'entries' in info:
                            if not info['entries']:
                                raise Exception("No 18+ videos found for this exact keyword. Try another word.")
                            info = info['entries'][0]
                        title = info.get('title', '18+ Adult Video')

                    # 50MB പരിധി ഉറപ്പുവരുത്തുന്നു
                    if os.path.exists(filename):
                        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                        if file_size_mb > 49.9:
                            bot.edit_message_text(f"❌ **File is too large ({file_size_mb:.1f} MB)!** Telegram limit is 50MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                            return

                    # ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
                    with open(filename, 'rb') as video_file:
                        bot.send_video(
                            message.chat.id, 
                            video_file, 
                            caption=f"🔞 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                            parse_mode='Markdown',
                            timeout=180
                        )

                    bot.delete_message(message.chat.id, status_msg.message_id)

                except Exception as err:
                    error_str = str(err)[:150]
                    try:
                        bot.edit_message_text(f"❌ **Download Failed!**\n\n`{error_str}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    except:
                        bot.send_message(message.chat.id, f"❌ **Download Failed!**\n\n`{error_str}`")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

            threading.Thread(target=run_process).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
