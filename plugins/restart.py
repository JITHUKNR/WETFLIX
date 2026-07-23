from config import ADMIN_ID
import os
import sys

def setup(bot):

    @bot.message_handler(commands=['restart', 'reboot'])
    def restart_bot(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        try:
            bot.reply_to(message, "🔄 **Restarting bot...** Please wait a few seconds.", parse_mode='Markdown')
            
            # പൈത്തൺ പ്രോസസ്സ് വീണ്ടും റീസ്റ്റാർട്ട് ചെയ്യുന്നു
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to restart bot: `{e}`", parse_mode='Markdown')

    @bot.message_handler(commands=['shutdown', 'stopbot'])
    def shutdown_bot(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        try:
            bot.reply_to(message, "🛑 **Shutting down bot process...** Goodbye!", parse_mode='Markdown')
            # പ്രോസസ്സ് പൂർണ്ണമായി നിർത്തിവെക്കുന്നു
            os._exit(0)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to shutdown bot: `{e}`", parse_mode='Markdown')
