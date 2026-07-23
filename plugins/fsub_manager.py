from config import ADMIN_ID

# ഒരു ഗ്ലോബൽ വേരിയബിൾ അല്ലെങ്കിൽ ഡാറ്റാബേസ് വഴി ചാനൽ സൂക്ഷിക്കാൻ (താൽക്കാലികമായി മെമ്മറിയിൽ)
FSUBCONFIG = {"channel": "@YourChannelUsername"}

def setup(bot):

    @bot.message_handler(commands=['setfsub', 'fsubchannel'])
    def set_fsub_channel(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            current_ch = FSUBCONFIG["channel"]
            help_text = (
                "📢 **Force Subscribe Manager:**\n\n"
                f"• **Current FSub Channel:** `{current_ch}`\n\n"
                "👉 **Usage:** `/setfsub @NewChannelUsername`\n"
                "👉 **Disable:** `/setfsub none`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        new_channel = args[1].strip()
        FSUBCONFIG["channel"] = new_channel
        
        bot.reply_to(
            message,
            f"✅ **Force Subscribe Channel Updated Successfully!**\n\n"
            f"📢 New Channel: `{new_channel}`",
            parse_mode='Markdown'
        )

# മറ്റ് പ്ലഗിനുകൾക്ക് ഈ ചാനൽ എടുക്കാൻ ഉപയോഗിക്കാവുന്ന ഫംഗ്ഷൻ
def get_current_fsub():
    return FSUBCONFIG["channel"]
