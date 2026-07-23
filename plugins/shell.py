from config import ADMIN_ID
import subprocess

def setup(bot):

    @bot.message_handler(commands=['shell', 'sh', 'cmd'])
    def run_shell_command(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        cmd = message.text.split(maxsplit=1)
        if len(cmd) < 2:
            help_text = (
                "⚡ **Admin Shell Command Guide:**\n\n"
                "Use this command to execute terminal commands on your server directly from Telegram.\n\n"
                "👉 **Usage:** `/shell <command>`\n"
                "👉 **Example:** `/shell pip list` or `/shell ls -la`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        command_to_run = cmd[1]
        status_msg = bot.reply_to(message, f"⚙️ Executing: `{command_to_run}`...", parse_mode='Markdown')
        
        try:
            # കമാൻഡ് എക്സിക്യൂട്ട് ചെയ്യുന്നു
            result = subprocess.run(command_to_run, shell=True, capture_output=True, text=True, timeout=60)
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "Command executed successfully with no output."
                
            # ടെലിഗ്രാം മെസ്സേജ് ലെങ്ത് പരിധി (4096 അക്ഷരങ്ങൾ) ഉള്ളതിനാൽ കട്ട് ചെയ്യുന്നു
            if len(output) > 4000:
                output = output[:4000] + "\n\n... [Output truncated due to length]"
                
            response_text = (
                f"💻 **Shell Execution Result:**\n\n"
                f"📥 **Command:** `{command_to_run}`\n\n"
                f"```text\n{output}\n```"
            )
            
            bot.edit_message_text(response_text, message.chat.id, status_msg.message_id, parse_mode='Markdown')
            
        except subprocess.TimeoutExpired:
            bot.edit_message_text("❌ Command execution timed out (limit: 60 seconds).", message.chat.id, status_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Error executing command: `{e}`", message.chat.id, status_msg.message_id, parse_mode='Markdown')
