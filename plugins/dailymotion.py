import os
import threading
import urllib.parse
import yt_dlp
import requests
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):

    # Universal 18+ Global Video Search (Uncensored)
    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def global_uncensored_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(
                    message, 
                    "🔥 **Global 18+ Video Downloader:**\n\n📖 *Usage:*\n`/search <keyword>`\n\n💡 *Example:* `/search mallu bhabhi`", 
                    parse_mode='Markdown'
                )
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching Global Web for **'{query}'**...", parse_mode='Markdown')

            def run_process():
                filename = f"vid_{message.chat.id}.mp4"
                try:
                    # Step 1: DuckDuckGo വഴി അഡൾട്ട് വീഡിയോകൾ സെർച്ച് ചെയ്യുന്നു (No SafeSearch limit)
                    # അഡൾട്ട് റിസൾട്ടുകൾ മാത്രം കിട്ടാൻ 'porn' അല്ലെങ്കിൽ 'video' എന്ന വാക്ക് ചേർക്കുന്നു
                    search_term = f"{query} porn video"
                    encoded_query = urllib.parse.quote(search_term)
                    
                    # DuckDuckGo HTML വെർഷൻ ഉപയോഗിക്കുന്നു (API ബ്ലോക്ക് ഒഴിവാക്കാൻ)
                    html_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    
                    resp = requests.get(html_url, headers=headers, timeout=10)
                    
                    if resp.status_code != 200:
                        raise Exception("Failed to fetch search results from web.")

                    # റിസൾട്ടിൽ നിന്ന് വീഡിയോ ഉള്ള വെബ്സൈറ്റ് ലിങ്കുകൾ കണ്ടെത്തുന്നു (ഉദാഹരണത്തിന് xhamster, pornhub, xnxx തുടങ്ങിയവ)
                    links = re.findall(r'href="(https?://[^"]+)"', resp.text)
                    
                    valid_video_url = None
                    # പ്രധാനപ്പെട്ട 18+ സൈറ്റുകളുടെ ലിങ്കുകൾ മാത്രം ഫിൽറ്റർ ചെയ്തെടുക്കുന്നു
                    adult_sites = ['xhamster', 'pornhub', 'xnxx', 'eporner', 'spankbang', 'xvideos']
                    
                    for link in links:
                        # ഗൂഗിൾ, ഡക്ക്ഡക്ക്ഗോ ലിങ്കുകൾ ഒഴിവാക്കുന്നു
                        if 'duckduckgo' in link or 'google' in link:
                            continue
                        
                        # വീഡിയോ സൈറ്റുകൾ ആണോ എന്ന് നോക്കുന്നു
                        if any(site in link for site in adult_sites):
                            # redirect URL ആണെങ്കിൽ അത് ഡീകോഡ് ചെയ്തെടുക്കുന്നു
                            if 'uddg=' in link:
                                try:
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                                    if 'uddg' in parsed:
                                        valid_video_url = parsed['uddg'][0]
                                        break
                                except:
                                    pass
                            else:
                                valid_video_url = link
                                break

                    if not valid_video_url:
                        bot.edit_message_text(f"❌ No suitable 18+ videos found globally for '{query}'. Try another keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                        return

                    bot.edit_message_text(f"⏳ **Found Video Globally! Downloading...**\n`{valid_video_url[:30]}...`", message.chat.id, status_msg.message_id, parse_mode='Markdown')

                    # Step 2: yt-dlp ഉപയോഗിച്ച് വീഡിയോ ഡൗൺലോഡ് ചെയ്യുന്നു
                    ydl_opts = {
                        'format': 'best[height<=480][filesize<49.5M]/best[height<=360][filesize<49.5M]/worst',
                        'outtmpl': filename,
                        'quiet': True,
                        'no_warnings': True,
                        'age_limit': 18
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(valid_video_url, download=True)
                        title = info.get('title', 'Global 18+ Video')

                    # 50MB പരിധി ഉറപ്പുവരുത്തുന്നു
                    if os.path.exists(filename):
                        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                        if file_size_mb > 49.9:
                            bot.edit_message_text(f"❌ **File is too large ({file_size_mb:.1f} MB)!** Telegram limit is 50MB.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                            return

                    # Step 3: ടെലഗ്രാമിലേക്ക് നേരിട്ട് വീഡിയോ ഫയലായി അയക്കുന്നു
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
