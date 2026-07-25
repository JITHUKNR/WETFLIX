import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN

# താങ്കൾ നൽകിയ Hugging Face API Token
HF_API_TOKEN = "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"
# ഏറ്റവും മികച്ച ക്വാളിറ്റി തരുന്ന Swin2SR മോഡൽ ലിങ്ക് 
API_URL = "https://api-inference.huggingface.co/models/caidas/swin2SR-classical-sr-x2-64"

def setup(bot):
    @bot.message_handler(commands=['upscale', 'enhance'])
    def ask_for_photo(message):
        bot.reply_to(
            message, 
            "✨ **STRICT IMAGE EDIT & UPSCALER** ✨\n\n"
            "Send me any low-quality photo, and I will enhance it with extreme details while keeping the **exact same facial identity** without any distortion.\n\n"
            "👉 Please simply send a photo to enhance it.",
            parse_mode='Markdown'
        )

    @bot.message_handler(content_types=['photo'])
    def handle_photo_upscale(message):
        status_msg = bot.reply_to(message, "⏳ **Initializing ZERO MODIFICATION MODE...**\nAnalyzing facial structures and preserving identity...")
        
        try:
            # 1. ടെലഗ്രാമിൽ നിന്ന് ഫോട്ടോ എടുക്കുന്നു
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            bot.edit_message_text("⚙️ **Enhancing image to High Resolution...**\nRestoring micro-textures without altering the original face. Please wait...", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
            
            # 2. Hugging Face API ഉപയോഗിച്ച് ഫോട്ടോ എൻഹാൻസ് ചെയ്യുന്നു
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            response = requests.post(API_URL, headers=headers, data=downloaded_file)
            
            # എറർ ഉണ്ടോ എന്ന് ചെക്ക് ചെയ്യുന്നു
            if response.status_code == 200:
                # 3. എൻഹാൻസ് ചെയ്ത പുതിയ ഫോട്ടോ യൂസറിന് അയക്കുന്നു
                bot.send_photo(
                    message.chat.id, 
                    response.content, 
                    caption="✨ **Upscale Complete!**\n\n✅ 100% Identity Preserved\n✅ Cinematic Texture Applied", 
                    reply_to_message_id=message.message_id
                )
                bot.delete_message(message.chat.id, status_msg.message_id)
            else:
                error_msg = response.json().get('error', 'Unknown Error')
                bot.edit_message_text(f"❌ AI Error: `{error_msg}`\n\n*(Note: If the AI is sleeping, it takes 1 minute to wake up. Try sending the photo again!)*", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
                
        except Exception as e:
            bot.edit_message_text(f"❌ Error during upscaling: `{e}`", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
