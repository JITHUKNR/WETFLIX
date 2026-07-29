import os
import threading
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # XHamster Direct Search & Download Command (/search or /dm or /dl)
    @bot.message_handler(commands=['search', 'dm', 'dl'])
    def search_and_download(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "📥 **XHamster Video Downloader:**\n\n📖 *Usage:*\n`/search <video name>`\n\n💡 *Example:* `/search mallu mms`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            
            # യൂസർ ലിങ്ക് ആണോ അതോ കീവേഡ് ആണോ എന്ന് നോക്കുന്നു
            if query.startswith("http"):
                video_url = query
            else:
                # യൂട്യൂബ് ഒഴിവാക്കി, നേരിട്ട് xhamster സെർച്ച് ലിങ്ക് നൽകുന്നു
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                video_url = f"https://xhamster.com/search/{encoded_query}"

            status_msg = bot.reply_to(message, f"⏳ **Downloading video from XHamster... Please wait.**", parse_mode='Markdown')

            def run_dl():
                filename = f"vid_{message.chat.id}.mp4"
                
                # yt-dlp ഓപ്ഷൻസ് (യൂട്യൂബ് ഒഴിവാക്കി മറ്റ് സൈറ്റുകൾ മാത്രം എടുക്കാൻ)
                ydl_opts = {
                    'format': 'best[height<=360][filesize<48M]/worst',
                    'outtmpl': filename,
                    'quiet': True,
                    'no_warnings': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        if 'entries' in info:
                            # പ്ലേലിസ്റ്റ് അല്ലെങ്കിൽ സെർച്ച് പേജ് ആണെങ്കിൽ ആദ്യത്തെ വീഡിയോ എടുക്കുന്നു
                            info = info['entries'][0]
                        title = info.get('title', 'XHamster Video')

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

            threading.Thread(target=run_dl).start()

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{e}`")
