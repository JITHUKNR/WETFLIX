import os
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Video Downloader Command (/search or /dm or /video_dl)
    @bot.message_handler(commands=['search', 'dm', 'dl'])
    def request_video_download(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "📥 **Direct Video Downloader:**\n\n📖 *Usage:*\n`/search <Any Video Link>` or type a keyword\n\n💡 *Example:* `/search https://xhamster.com/videos/...`", 
                    parse_mode='Markdown'
                )
                return

            query_or_url = parts[1].strip()
            
            # യൂസർ ലിങ്ക് ആണോ നൽകിയത് എന്ന് പരിശോധിക്കുന്നു
            if query_or_url.startswith("http"):
                download_and_send_video(message.chat.id, query_or_url, bot)
            else:
                # കീവേഡ് ആണെങ്കിൽ yt-dlp വഴി സെർച്ച് ചെയ്ത് ഡൗൺലോഡ് ചെയ്യുന്നു
                status_msg = bot.reply_to(message, f"🔎 Searching and downloading video for **'{query_or_url}'**...", parse_mode='Markdown')
                
                def run_search_download():
                    filename = f"vid_{message.from_user.id}.mp4"
                    ydl_opts = {
                        'format': 'best[height<=360][filesize<48M]/worst',
                        'default_search': 'auto',
                        'max_downloads': 1,
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                    }

                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(f"ytsearch1:{query_or_url}", download=True)
                            if 'entries' in info:
                                info = info['entries'][0]
                            title = info.get('title', 'Downloaded Video')

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
                        bot.edit_message_text(f"❌ **Download Failed!**\n\n`{str(err)[:150]}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                    finally:
                        if os.path.exists(filename):
                            os.remove(filename)

                threading.Thread(target=run_search_download).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")

    def download_and_send_video(chat_id, video_url, bot_instance):
        status_msg = bot_instance.send_message(chat_id, "⏳ **Downloading video file... Please wait.**", parse_mode='Markdown')
        
        def run_dl():
            filename = f"vid_{chat_id}.mp4"
            ydl_opts = {
                'format': 'best[height<=360][filesize<48M]/worst',
                'outtmpl': filename,
                'quiet': True,
                'no_warnings': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    title = info.get('title', 'Downloaded Video')

                with open(filename, 'rb') as video_file:
                    bot_instance.send_video(
                        chat_id, 
                        video_file, 
                        caption=f"🔥 **{title}**\n\n📥 _Downloaded via WETFLIX Bot_", 
                        parse_mode='Markdown',
                        timeout=120
                    )

                bot_instance.delete_message(chat_id, status_msg.message_id)

            except Exception as err:
                bot_instance.edit_message_text(f"❌ **Download Failed!**\n\n`{str(err)[:150]}`", chat_id, status_msg.message_id, parse_mode='Markdown')
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

        threading.Thread(target=run_dl).start()
