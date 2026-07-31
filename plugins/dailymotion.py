import requests
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):
    
    # റെഡ്ഡിറ്റിൽ നിന്നും വീഡിയോ എടുക്കുന്ന ഫംഗ്ഷൻ
    def get_reddit_video(query):
        # റെഡ്ഡിറ്റ് നമ്മളെ ബ്ലോക്ക് ചെയ്യാതിരിക്കാൻ ഒരു കസ്റ്റം User-Agent വെക്കുന്നു
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # റെഡ്ഡിറ്റിലെ പോപ്പുലർ ആയ NSFW സബ്-റെഡ്ഡിറ്റുകൾ (ഇവയിൽ നിന്നാണ് സെർച്ച് ചെയ്യുക)
        subreddits = ["nsfw", "porn_gifs", "NSFW_GIF", "60fpsporn", "NSFW_HTML5"]
        selected_sub = random.choice(subreddits)
        
        # സെർച്ച് ചെയ്യാനുള്ള റെഡ്ഡിറ്റ് API ലിങ്ക് (JSON ഫോർമാറ്റിൽ)
        search_url = f"https://www.reddit.com/r/{selected_sub}/search.json?q={query}&restrict_sr=on&sort=relevance&t=all"
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                
                valid_videos = []
                for post in posts:
                    post_data = post['data']
                    # പോസ്റ്റിൽ വീഡിയോ ഉണ്ടോ എന്ന് ചെക്ക് ചെയ്യുന്നു
                    if post_data.get('is_video') or post_data.get('url', '').endswith(('.mp4', '.gifv')):
                        
                        video_url = post_data.get('url')
                        # Reddit-ന്റെ സ്വന്തം വീഡിയോ പ്ലെയർ ആണെങ്കിൽ അതിലെ ലിങ്ക് എടുക്കുന്നു
                        if 'v.redd.it' in video_url and 'secure_media' in post_data and post_data['secure_media'] and 'reddit_video' in post_data['secure_media']:
                            video_url = post_data['secure_media']['reddit_video']['fallback_url']
                        
                        title = post_data.get('title', 'Reddit Video')
                        valid_videos.append({'url': video_url, 'title': title})
                
                if valid_videos:
                    # കിട്ടിയ വീഡിയോകളിൽ നിന്നും ഒരെണ്ണം തിരഞ്ഞെടുക്കുന്നു
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

            # ⚠️ ഡൗൺലോഡ് ചെയ്യുന്നില്ല! പകരം റെഡ്ഡിറ്റ് ലിങ്ക് നേരിട്ട് ടെലഗ്രാമിന് നൽകുന്നു ⚠️
            # ടെലഗ്രാം സ്വന്തമായി ആ ലിങ്കിൽ നിന്ന് വീഡിയോ പ്ലേ ചെയ്യും (സെർവറിന് യാതൊരു ലോഡുമില്ല!)
            bot.send_video(
                chat_id=message.chat.id,
                video=video_url,
                caption=f"🔞 **{title[:60]}...**\n\n📥 _Sourced from Reddit via WETFLIX_",
                parse_mode='Markdown'
            )
            
            bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as e:
            bot.reply_to(message, f"❌ Error: `{str(e)[:100]}`")
