import threading
import time
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
try:
    from database import users_col
except ImportError:
    pass

# ഷെഡ്യൂൾ ചെയ്ത കാര്യങ്ങൾ സേവ് ചെയ്യാൻ ഒരു ലിസ്റ്റ്
scheduled_tasks = []

def setup(bot):
    @bot.message_handler(commands=['setschedule'])
    def start_schedule(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return
            
        msg = bot.reply_to(message, "⏰ **Step 1: Send Message**\n\nSend the message (Text/Photo/Video) you want to schedule for broadcast.\n\nType /cancel to abort.", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_sch_msg, bot)

    def process_sch_msg(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return
            
        msg_to_broadcast = message
        bot_reply = bot.reply_to(
            message, 
            "🔘 **Step 2: Add Inline Button (Optional)**\n\n"
            "If you want to add a button, type it like:\n`Button Name - https://link.com`\n\n"
            "If no button is needed, type `/skip`.",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(bot_reply, process_sch_btn, bot, msg_to_broadcast)

    def process_sch_btn(message, bot, msg_to_broadcast):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return

        markup = None
        if message.text != '/skip':
            try:
                parts = message.text.split('-', 1)
                btn_text = parts[0].strip()
                btn_url = parts[1].strip()
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(btn_text, url=btn_url))
            except Exception:
                bot.reply_to(message, "❌ Invalid format. Proceeding without button.")
        
        bot_reply = bot.reply_to(
            message, 
            "⏰ **Step 3: Set Time**\n\n"
            "Enter the time in **24-hour format** (HH:MM).\n"
            "*(Example: For 2:30 PM type `14:30`, For 9:00 AM type `09:00`)*",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(bot_reply, process_sch_time, bot, msg_to_broadcast, markup)

    def process_sch_time(message, bot, msg_to_broadcast, markup):
        time_str = message.text.strip()
        
        # സമയം ശരിയായ ഫോർമാറ്റിൽ ആണോ എന്ന് ചെക്ക് ചെയ്യുന്നു
        if len(time_str) != 5 or ':' not in time_str:
            bot.reply_to(message, "❌ Invalid time format! Please try again with /setschedule")
            return
            
        scheduled_tasks.append({
            'time': time_str,
            'msg': msg_to_broadcast,
            'markup': markup,
            'admin_chat_id': message.chat.id
        })
        
        bot.reply_to(message, f"✅ **Success!** Your broadcast has been securely scheduled for **{time_str}**.", parse_mode='Markdown')

    # ബാക്ക്ഗ്രൗണ്ടിൽ സമയം ചെക്ക് ചെയ്തുകൊണ്ടിരിക്കുന്ന ഫംഗ്ഷൻ
    def schedule_checker():
        while True:
            # നിലവിലെ സമയം HH:MM ഫോർമാറ്റിൽ എടുക്കുന്നു
            now = datetime.datetime.now().strftime("%H:%M")
            
            for task in scheduled_tasks[:]:
                if task['time'] == now:
                    bot.send_message(task['admin_chat_id'], f"🚀 **Starting your scheduled broadcast for {task['time']}...**", parse_mode='Markdown')
                    success = 0
                    failed = 0
                    try:
                        if 'users_col' in globals():
                            users = users_col.find({})
                            for user in users:
                                try:
                                    bot.copy_message(
                                        chat_id=user['user_id'], 
                                        from_chat_id=task['msg'].chat.id, 
                                        message_id=task['msg'].message_id,
                                        reply_markup=task['markup']
                                    )
                                    success += 1
                                except Exception:
                                    failed += 1
                            
                            report = f"✅ **Scheduled Broadcast Completed!**\n\n🎯 Sent to: `{success}` users\n❌ Failed: `{failed}` users"
                            bot.send_message(task['admin_chat_id'], report, parse_mode='Markdown')
                        
                    except Exception as e:
                        bot.send_message(task['admin_chat_id'], f"❌ Broadcast error: {e}")
                    
                    # അയച്ചതിന് ശേഷം ലിസ്റ്റിൽ നിന്ന് ആ ടാസ്ക് നീക്കം ചെയ്യുന്നു
                    scheduled_tasks.remove(task)
                    
            time.sleep(60) # ഓരോ ഒരു മിനിറ്റിലും സമയം ചെക്ക് ചെയ്യും

    # ബാക്ക്ഗ്രൗണ്ട് ത്രെഡ് സ്റ്റാർട്ട് ചെയ്യുന്നു
    t = threading.Thread(target=schedule_checker, daemon=True)
    t.start()
