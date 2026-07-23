import qrcode
import os

def setup(bot):

    @bot.message_handler(commands=['qr', 'qrcode'])
    def generate_qrcode(message):
        if message.chat.type != 'private':
            return
            
        text = message.text.replace('/qr', '').replace('/qrcode', '').strip()
        
        if not text:
            bot.reply_to(message, "⚠️ Please provide text or a link to generate QR code.\n\n👉 **Usage:** `/qr https://example.com`", parse_mode='Markdown')
            return
            
        try:
            # ക്യുആർ കോഡ് ഇമേജ് ഉണ്ടാക്കുന്നു
            img = qrcode.make(text)
            file_path = f"qr_{message.from_user.id}.png"
            img.save(file_path)
            
            # യൂസർക്ക് ഫോട്ടോയായി അയച്ചു കൊടുക്കുന്നു
            with open(file_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=f"✅ QR Code generated successfully for:\n`{text}`", parse_mode='Markdown')
                
            # സെർവറിൽ നിന്ന് താൽക്കാലിക ഫയൽ ഡിലീറ്റ് ചെയ്യുന്നു
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to generate QR code: {e}")
