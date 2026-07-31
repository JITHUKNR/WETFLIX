import requests
import random
import urllib.parse
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):
    
    # റെഡ്ഡിറ്റിൽ നിന്നും വീഡിയോ എടുക്കുന്ന ഫംഗ്ഷൻ
    def get_reddit_video(query):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        encoded_query = urllib.parse.quote(query)
        # ⚠️ ഏറ്റവും പുതിയ മാറ്റം: പ്രത്യേക ഗ്രൂപ്പുകൾ ഒഴിവാക്കി റെഡ്ഡിറ്റിൽ മുഴുവനായി തിരയുന്നു (include_over_18=on) ⚠️
        search_url = f"https://www.reddit.com/search.json?q={encoded_query}&include_over_18=on&sort=relevance&t=all"
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # കിട്ടിയ റിസൾട്ടുകൾ എടുക്കുന്നു
                posts = data.get('data', {}).get('children', [])
                
                valid_videos = []
                for post in posts:
                    post_data = post['data']
                    
                    # 1. റെഡ്ഡിറ്റിൽ നേരിട്ട് അപ്‌ലോഡ് ചെയ്ത വീഡിയോകൾ (v.redd.it)
                    if post_data.get('is_video'):
                        if 'secure_media' in post_data and post_data['secure_media'] and 'reddit_video' in post_data['secure_media']:
                            video_url = post_data['secure_media']['reddit_video']['fallback_url']
                            title = post_data.get('title', 'Reddit Video')
                            valid_videos.append({'url': video_url, 'title': title})
                            
                    # 2. മറ്റ് ഡയറക്റ്റ് ലിങ്കുകൾ (.mp4 അല്ലെങ്കിൽ .gifv)
                    elif 'url' in post_data:
                        url = post_data['url']
                        if url.endswith(('.mp4', '.gifv')):
                            url = url.replace('.gifv', '.mp4')
                            title = post_data.get('title', 'Reddit Video')
                            valid_videos.append({'url': url, 'title': title})
                
                if valid_videos:
                    # കിട്ടിയ വീഡിയോകളിൽ നിന്നും ഒരെണ്ണം റാൻഡം ആയി എടുക്കുന്നു
                    return random.choice(valid_videos)
        except Exception as e:
            print(f"Reddit Search Error: {e}")
            pass
            
        return None

    @bot.message_handler(commands=['search', 'dm', 'dl', 'video'])
    def reddit_video_search(message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "🔥 **Reddit Video Search:**\n\n📖 *Usage:*\n`/search <keyword>`", parse_mode='Markdown')
                return

            query = parts[1].strip()
            status_msg = bot.reply_to(message, f"🔎 Searching Reddit for **'{query}'**...", parse_mode='Markdown')

            video_data = get_reddit_video(query)

            if not video_data:
                bot.edit_message_text(f"❌ No videos found on Reddit for '{query}'. Try a different keyword.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
                return
            
            video_url = video_data['url']
            title = video_data['title']

            bot.edit_message_text(f"⏳ **Video found! Sending...**", message.chat.id, status_msg.message_id, parse_mode='Markdown')

            # ⚠️ ഡൗൺലോഡ് ചെയ്യാതെ റെഡ്ഡിറ്റ് ലിങ്ക് നേരിട്ട് ടെലഗ്രാമിന് നൽകുന്നു ⚠️
            bot.send_video(
                chat_id=message.chat.id,
                video=video_url,
                caption=f"🔞 **{title[:60]}...**\n\n📥 _Sourced from Reddit via WETFLIX_",
                parse_mode='Markdown'
            )
            
            # വീഡിയോ അയച്ചു കഴിഞ്ഞാൽ ആ status മെസ്സേജ് ഡിലീറ്റ് ചെയ്യും
            bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as e:
            try:
                bot.edit_message_text(f"❌ Error sending video. Telegram couldn't process the video link.", message.chat.id, status_msg.message_id, parse_mode='Markdown')
            except: pass
