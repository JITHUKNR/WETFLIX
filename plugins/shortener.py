import urllib.request
import json

def setup(post_bot):

    @post_bot.message_handler(commands=['short', 'shorten'])
    def shorten_url_handler(message):
        if message.chat.type != 'private':
            return
            
        args = message.text.replace('/short', '').replace('/shorten', '').strip()
        
        if not args:
            help_text = (
                "🔗 **URL Shortener Guide:**\n\n"
                "Use this command to shorten any long URL instantly.\n\n"
                "👉 **Usage:** `/short https://example.com/very/long/link`"
            )
            post_bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        status_msg = post_bot.reply_to(message, "⏳ Shortening your link, please wait...")
        
        try:
            # പൊതുവായി ലഭ്യമായ ഒരു ഫ്രീ API (TinyURL) ഉപയോഗിച്ച് ലിങ്ക് ഷോർട്ട് ചെയ്യുന്നു
            api_url = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(args)}"
            
            with urllib.request.urlopen(api_url) as response:
                short_url = response.read().decode('utf-8')
                
            if short_url.startswith("http"):
                result_text = (
                    f"🔗 **URL Shortened Successfully!**\n\n"
                    f"🌐 **Original:** `{args}`\n"
                    f"✨ **Short Link:** `{short_url}`"
                )
                post_bot.edit_message_text(result_text, message.chat.id, status_msg.message_id, parse_mode='Markdown')
            else:
                post_bot.edit_message_text("❌ Failed to shorten the URL. Please check if the link is valid.", message.chat.id, status_msg.message_id)
                
        except Exception as e:
            post_bot.edit_message_text(f"❌ Error: `{e}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
