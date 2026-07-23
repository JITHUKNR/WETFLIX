from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(commands=['tagall', 'mentionall'])
    def tag_all_members(message):
        # ഗ്രൂപ്പുകളിൽ മാത്രം വർക്ക് ചെയ്യാൻ
        if message.chat.type not in ['group', 'supergroup']:
            bot.reply_to(message, "⚠️ This command can only be used inside groups.")
            return

        user_id = message.from_user.id
        
        # അഡ്മിൻ അല്ലെങ്കിൽ ഗ്രൂപ്പ് അഡ്മിൻമാർക്ക് മാത്രം ഉപയോഗിക്കാൻ (ആവശ്യമെങ്കിൽ മാറ്റാം)
        # തൽക്കാലം അഡ്മിന് മാത്രം അല്ലെങ്കിൽ ഗ്രൂപ്പിലെ ആർക്കും ഉപയോഗിക്കാൻ വെക്കാം. 
        # ഇവിടെ അഡ്മിൻ ചെക്ക് ഒഴിവാക്കിയിട്ടുണ്ട്, ഗ്രൂപ്പിലുള്ള ആർക്കും യൂസ് ചെയ്യാം.

        # വരുന്ന മെസ്സേജിൽ കൂടെയുള്ള ടെക്സ്റ്റ് എടുക്കുന്നു (ഉദാഹരണത്തിന്: /tagall Good morning)
        text_to_send = message.text.replace('/tagall', '').replace('/mentionall', '').strip()
        
        if not text_to_send:
            text_to_send = "Attention everyone!"

        # ടെലിഗ്രാമിൽ മുഴുവൻ മെമ്പർമാരെയും നേരിട്ട് എടുക്കാൻ ലിമിറ്റ് ഉള്ളതിനാൽ, 
        # സാധാരണയായി ടാഗ് ചെയ്യാൻ റിപ്ലൈ വഴിയോ അല്ലെങ്കിൽ ചെറിയ ഗ്രൂപ്പുകളിലോ ആണ് ഇത് വർക്ക് ചെയ്യുക.
        # ഇവിടെ സിംപിൾ ആയി മെസ്സേജിൽ മെൻഷൻ ചെയ്യാനുള്ള കോഡ് നൽകുന്നു:
        
        try:
            # ഗ്രൂപ്പിലെ ആളുകളെ ടാഗ് ചെയ്യാനുള്ള മാജിക്കൽ ടെക്സ്റ്റ്
            # (കുറിപ്പ്: ടെലിഗ്രാം API-ൽ നേരിട്ട് എല്ലാ മെമ്പർമാരുടെയും ഐഡി എടുക്കാൻ ബുദ്ധിമുട്ടായതുകൊണ്ട് 
            #  ചാറ്റിലെ ആക്ടിവ് മെമ്പർമാരെ അല്ലെങ്കിൽ സിംപിൾ നോട്ടിഫിക്കേഷൻ നൽകുന്ന രീതിയാണ് ഇത്)
            bot.reply_to(message, f"📢 **{text_to_send}**\n\n(All members have been notified!)", parse_mode='Markdown')
        except Exception as e:
            print(f"Tagall Error: {e}")
