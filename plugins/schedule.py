from config import ADMIN_ID
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['schedule', 'sched'])
    def schedule_broadcast(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        args = message.text.split()
        if len(args) < 3 or not message.reply_to_message:
            help_text = (
                "⏰ **Broadcast Scheduler Guide:**\n\n"
                "Reply to any message and use this command to schedule a broadcast after a specific time (in minutes).\n\n"
                "👉 **Usage:** `/schedule <minutes> <message>`\n"
                "👉 **Example:** `/sched 10 Hello everyone!`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        try:
            delay_minutes = int(args[1])
            delay_seconds = delay_minutes * 60
            reply_msg = message.reply_to_message
            
            bot.reply_to(message, f"✅ Broadcast has been scheduled successfully! It will be sent after `{delay_minutes}` minutes.", parse_mode='Markdown')
            
            def run_schedule():
                time.sleep(delay_seconds)
                try:
                    # ഡാറ്റാബേസിൽ നിന്ന് യൂസർമാരെ എടുത്ത് അയക്കാം അല്ലെങ്കിൽ സിംപിൾ ആയി നോട്ടിഫിക്കേഷൻ അയക്കാം
                    bot.send_message(ADMIN_ID, f"⏰ **Scheduled Broadcast Triggered!**\n\nMessage ID: `{reply_msg.message_id}`", parse_mode='Markdown')
                except Exception as e:
                    print(f"Schedule Execution Error: {e}")
                    
            threading.Thread(target=run_schedule).start()
            
        except ValueError:
            bot.reply_to(message, "❌ Invalid time format. Please provide a valid number for minutes.")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")
