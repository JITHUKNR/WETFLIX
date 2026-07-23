from config import ADMIN_ID
import subprocess

def setup(bot):

    @bot.message_handler(commands=['speedtest', 'speed'])
    def run_speedtest(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        status_msg = bot.reply_to(message, "⚡ Running server speed test, please wait...")
        
        try:
            # പൈത്തണിന്റെ speedtest-cli ഉപയോഗിച്ച് സ്പീഡ് പരിശോധിക്കുന്നു
            result = subprocess.run(['speedtest-cli', '--simple'], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                output = result.stdout
                text = f"🚀 **Server Speed Test Results:**\n\n```text\n{output}\n```"
            else:
                text = "⚠️ Speedtest failed to execute properly. Make sure 'speedtest-cli' is installed."
                
            bot.edit_message_text(text, message.chat.id, status_msg.message_id, parse_mode='Markdown')
        except subprocess.TimeoutExpired:
            bot.edit_message_text("❌ Speed test took too long and timed out.", message.chat.id, status_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Error running speed test: `{e}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
