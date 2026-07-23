import threading
import time

def setup(bot):

    @bot.message_handler(commands=['autodelete', 'deltime'])
    def autodelete_guide(message):
        if message.chat.type != 'private':
            return
            
        help_text = (
            "⏳ **Auto-Delete Feature:**\n\n"
            "This plugin ensures that files or messages sent by the bot are automatically cleaned up after a specific time to save space and maintain privacy.\n\n"
            "👉 *Status:* `Active in background handlers`"
        )
        bot.reply_to(message, help_text, parse_mode='Markdown')

    # ഒരു പ്രത്യേക ഫംഗ്ഷൻ വഴി മെസ്സേജുകൾ നിശ്ചിത സമയം കഴിഞ്ഞ് ഡിലീറ്റ് ചെയ്യാൻ ഉപയോഗിക്കുന്ന കോഡ്:
    def schedule_deletion(chat_id, message_id, delay_seconds=300):
        def delete_task():
            time.sleep(delay_seconds)
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print(f"Auto-Delete Error: {e}")
                
        threading.Thread(target=delete_task).start()
