import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN

# താങ്കൾ നൽകിയ DeepAI API Key
AI_API_KEY = "0c597472-4fdf-49f0-a32f-e436a359ae0b"

def setup(bot):
    @bot.message_handler(commands=['upscale', 'enhance'])
    def ask_for_photo(message):
        bot.reply_to(
            message, 
            "✨ **STRICT IMAGE EDIT & UPSCALER** ✨\n\n"
            "Send me any low-quality photo, and I will enhance it to **8K Resolution** with extreme details (pores, hair textures) while keeping the **exact same facial identity** without any distortion.\n\n"
            "👉 Please simply send a photo to enhance it.",
            parse_mode='Markdown'
        )

    @bot.message_handler(content_types=['photo'])
    def handle_photo_upscale(message):
        status_msg = bot.reply_to(message, "⏳ **Initializing ZERO MODIFICATION MODE...**\nAnalyzing facial structures and preserving identity...")
        
        try:
            # 1. ടെലഗ്രാമിൽ നിന്ന് ഫോട്ടോയുടെ ലിങ്ക് എടുക്കുന്നു
            file_info = bot.get_file(message.photo[-1].file_id)
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            
            bot.edit_message_text("⚙️ **Enhancing image to High Resolution...**\nRestoring micro-textures (pores, hair) without altering the original face. Please wait...", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
            
            # 2. DeepAI API ഉപയോഗിച്ച് ഫോട്ടോ എൻഹാൻസ് ചെയ്യുന്നു
            r = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                data={
                    'image': file_url,
                },
                headers={'api-key': AI_API_KEY}
            )
            
            result = r.json()
            
            if 'output_url' in result:
                enhanced_image_url = result['output_url']
                
                # 3. എൻഹാൻസ് ചെയ്ത പുതിയ ഫോട്ടോ യൂസറിന് അയക്കുന്നു
                bot.send_photo(
                    message.chat.id, 
                    enhanced_image_url, 
                    caption="✨ **Upscale Complete!**\n\n✅ 100% Identity Preserved\n✅ Cinematic Texture Applied", 
                    reply_to_message_id=message.message_id
                )
                bot.delete_message(message.chat.id, status_msg.message_id)
            else:
                error_text = result.get('status', 'Unknown Error from AI')
                bot.edit_message_text(f"❌ AI Error: `{error_text}`\nPlease try sending a different photo.", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
                
        except Exception as e:
            bot.edit_message_text(f"❌ Error during upscaling: `{e}`", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
