from config import ADMIN_ID

# ഡിഫോൾട്ട് സ്റ്റിക്കർ പാക്ക് നെയിം (താങ്കൾക്ക് ഇഷ്ടമുള്ളത് ഇവിടെ മാറ്റാം)
STICKER_CONFIG = {
    "pack_name": "TRENDA Official Pack 🛍️",
    "pack_shortname": "trendastore_bot"
}

def setup(bot):

    @bot.message_handler(commands=['setpackname', 'stickerpack'])
    def set_sticker_pack_name(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split('|')
        if len(args) < 2:
            help_text = (
                "🏷️ **Sticker Pack Manager:**\n\n"
                f"• **Current Pack Name:** `{STICKER_CONFIG['pack_name']}`\n"
                f"• **Current Shortname:** `{STICKER_CONFIG['pack_shortname']}`\n\n"
                "👉 **Usage:** `/setpackname Pack Title | shortname_bot`\n"
                "👉 **Example:** `/setpackname WETFLAX News Stickers | wetflax_stickers`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        new_title = args[0].replace('/setpackname', '').replace('/stickerpack', '').strip()
        new_shortname = args[1].strip()
        
        STICKER_CONFIG["pack_name"] = new_title
        STICKER_CONFIG["pack_shortname"] = new_shortname
        
        bot.reply_to(
            message,
            f"✅ **Sticker Pack Details Updated Successfully!**\n\n"
            f"🏷️ **Name:** `{new_title}`\n"
            f"🔗 **Shortname:** `{new_shortname}`",
            parse_mode='Markdown'
        )

    # യൂസർമാർ അയക്കുന്ന സ്റ്റിക്കറുകൾ പിടിച്ചെടുത്ത് കസ്റ്റം പേരിൽ റീ-സെൻഡ് ചെയ്യാനോ അല്ലെങ്കിൽ 
    # ബോട്ട് വഴി ഉണ്ടാക്കുന്ന സ്റ്റിക്കറുകൾ ഈ പാക്കിലേക്ക് മാറ്റാനോ ഉള്ള ഹാൻഡ്‌ലർ
    @bot.message_handler(content_types=['sticker'])
    def handle_incoming_sticker(message):
        # താങ്കൾക്ക് വേണമെങ്കിൽ യൂസർ അയക്കുന്ന സ്റ്റിക്കർ ഏത് പാക്കിൽ നിന്നാണെന്ന് 
        # തിരിച്ചറിയാനും ഇവിടെ കോഡ് സെറ്റ് ചെയ്യാം.
        sticker = message.sticker
        
        # ഡിബഗ്ഗിംഗിനായി സ്റ്റിക്കറിന്റെ ഒറിജിനൽ ഫയൽ ഐഡിയും പാക്ക് പേരും പ്രിന്റ് ചെയ്യുന്നു
        print(f"Sticker Received - Pack: {sticker.set_name}, File ID: {sticker.file_id}")
