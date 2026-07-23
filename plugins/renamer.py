def setup(bot):

    @bot.message_handler(commands=['rename'])
    def rename_file_guide(message):
        if message.chat.type != 'private':
            return
            
        help_text = (
            "📝 **File Renamer Guide:**\n\n"
            "To rename any document or file:\n"
            "1. Reply to any document or file with the new name.\n"
            "2. **Format:** `/rename NewFileName.ext`\n\n"
            "👉 *Example:* `/rename MyAwesomeVideo.mp4`"
        )
        bot.reply_to(message, help_text, parse_mode='Markdown')

    @bot.message_handler(commands=['rename'], func=lambda message: message.reply_to_message is not None)
    def execute_rename(message):
        if message.chat.type != 'private':
            return
            
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Please provide a new file name. Example: `/rename MyFile.pdf`", parse_mode='Markdown')
            return
            
        new_name = args[1].strip()
        replied_msg = message.reply_to_message
        
        # ഡോക്യുമെന്റോ ഫയലോ ആണോ എന്ന് പരിശോധിക്കുന്നു
        if replied_msg.document:
            bot.reply_to(message, f"🔄 Renaming file to **{new_name}**... (Processing)", parse_mode='Markdown')
            # ഇവിടെ ഒറിജിനൽ ഫയൽ ഡൗൺലോഡ് ചെയ്ത് പുതിയ പേരിൽ വീണ്ടും അയക്കുന്ന കോഡ് വരും
            # നിലവിൽ യൂസർമാർക്ക് ഗൈഡ് നൽകാനും റിപ്ലൈ ഫങ്ഷൻ സെറ്റ് ചെയ്യാനുമുള്ള ബേസ് കോഡ് ഇതാണ്.
        else:
            bot.reply_to(message, "⚠️ Please reply to a valid document or file to rename it.")
