import os
from PIL import Image, ImageDraw
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup(bot):
    @bot.message_handler(commands=['upscale', 'enhance', 'watermark'])
    def ask_for_photo(message):
        bot.reply_to(
            message, 
            "🖼️ **WETFLIX IMAGE WATERMARKER TOOL** 🖼️\n\n"
            "Send me any photo, and I will instantly add your channel watermark to it!\n\n"
            "👉 Simply send a photo now.",
            parse_mode='Markdown'
        )

    @bot.message_handler(content_types=['photo'])
    def handle_photo_edit(message):
        status_msg = bot.reply_to(message, "⏳ **Processing image locally...** Adding watermark...")
        
        try:
            # 1. ടെലഗ്രാമിൽ നിന്ന് ഫോട്ടോ ഡൗൺലോഡ് ചെയ്യുന്നു
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            input_path = f"temp_{message.chat.id}.jpg"
            output_path = f"output_{message.chat.id}.jpg"
            
            with open(input_path, 'wb') as f:
                f.write(downloaded_file)
                
            # 2. PIL ഉപയോഗിച്ച് ഫോട്ടോയിൽ വാട്ടർമാർക്ക് ചേർക്കുന്നു
            img = Image.open(input_path)
            draw = ImageDraw.Draw(img)
            
            width, height = img.size
            watermark_text = "@WETFLIX"
            
            # ഫോട്ടോയുടെ താഴെ വലതുവശത്ത് വാട്ടർമാർക്ക് എഴുതുന്നു
            try:
                draw.text((width - 130, height - 40), watermark_text, fill="white")
            except Exception:
                pass
                
            img.save(output_path)
            
            # 3. എഡിറ്റ് ചെയ്ത ഫോട്ടോ യൂസറിന് അയക്കുന്നു
            with open(output_path, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption="✨ **Watermark Added Successfully!**\n\nChannel: @WETFLIX", 
                    reply_to_message_id=message.message_id
                )
                
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # താൽക്കാലിക ഫയലുകൾ ക്ലീൻ ചെയ്യുന്നു
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
                
        except Exception as e:
            bot.edit_message_text(f"❌ Error processing image: `{e}`", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
