import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
try:
    from database import set_fsub_data, set_cooldown, settings_col, users_col
except ImportError:
    pass 

def setup(bot):
    @bot.message_handler(commands=['admin'])
    def send_admin_panel(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return
            
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")
        )
        markup.add(
            InlineKeyboardButton("⚙️ FSub Channels", callback_data="admin_fsub"),
            InlineKeyboardButton("🔐 Group Locks", callback_data="admin_locks")
        )
        markup.add(
            InlineKeyboardButton("🛡️ Moderation Tools", callback_data="admin_mod"),
            InlineKeyboardButton("👋 Welcome Setup", callback_data="admin_welcome")
        )
        markup.add(
            InlineKeyboardButton("⏳ Command Delay", callback_data="admin_delay"), 
            InlineKeyboardButton("⏱️ Auto-Delete Time", callback_data="admin_deletetime")
        )
        markup.add(
            InlineKeyboardButton("❌ Close Panel", callback_data="admin_close")
        )
        
        text = (
            "🛠 **WETFLIX SUPER ADMIN PANEL**\n\n"
            "Use the buttons below to manage all bot features directly:"
        )
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ You are not an admin!", show_alert=True)
            return
            
        action = call.data.split('_')[1]

        if action == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Admin Panel Closed.")

        elif action == "fsub":
            bot.answer_callback_query(call.id, "FSub Setup ⚙️")
            msg = bot.send_message(
                call.message.chat.id, 
                "📢 **Force Subscribe Setup (Multiple Channels):**\n\n"
                "Send the Channel ID and Invite Link separated by a space.\n"
                "For multiple channels, put each on a new line.\n\n"
                "**Example:**\n"
                "`-1001234567890 https://t.me/+Link1`\n\n"
                "Type /cancel to abort.",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_fsub_step, bot)

        elif action == "delay":
            bot.answer_callback_query(call.id, "Delay Settings ⏳")
            msg = bot.send_message(
                call.message.chat.id, 
                "⏳ **Set Command Delay (Cooldown in Seconds):**\n\n"
                "Enter the delay time in **seconds** between media requests.\n"
                "(Example: Type `5` for 5 seconds, `30` for 30 seconds, or `120` for 2 minutes).\n\n"
                "Type /cancel to abort.",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_delay_step, bot)

        elif action == "deletetime":
            bot.answer_callback_query(call.id, "Auto-Delete Timer ⏱️")
            msg = bot.send_message(
                call.message.chat.id, 
                "⏱️ **Set Auto-Delete Time:**\n\n"
                "Enter the auto-delete time in seconds for media files.\n"
                "(Example: Type `5` for 5 seconds, or `30` for 30 seconds).\n\n"
                "Type /cancel to abort.",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_deletetime_step, bot)

        elif action == "locks":
            bot.answer_callback_query(call.id, "Group Locks 🔐")
            lock_markup = InlineKeyboardMarkup(row_width=2)
            lock_markup.add(
                InlineKeyboardButton("🔒 Lock Links", callback_data="toggle_links"),
                InlineKeyboardButton("🔒 Lock Stickers", callback_data="toggle_stickers")
            )
            lock_markup.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="admin_back"))
            
            bot.edit_message_text(
                "🔐 **Group Locks Manager:**\n\nSelect the items to restrict:", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                reply_markup=lock_markup,
                parse_mode='Markdown'
            )

        elif action == "mod":
            bot.answer_callback_query(call.id, "Moderation Tools 🛡️")
            text = (
                "🛡️ **Moderation Commands Guide:**\n\n"
                "Reply to messages in the group with the following:\n"
                "• `/ban` - Ban user\n"
                "• `/mute` - Mute user\n"
                "• `/warn` - Warn user\n"
                "• `/kick` - Kick user"
            )
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

        elif action == "welcome":
            bot.answer_callback_query(call.id, "Welcome Settings 👋")
            bot.send_message(call.message.chat.id, "👋 Welcome message is active. Customization coming soon!")

        elif action == "broadcast":
            bot.answer_callback_query(call.id, "Broadcast Mode 📢")
            msg = bot.send_message(
                call.message.chat.id, 
                "📢 **Step 1: Send Broadcast Message**\n\n"
                "Send the message (Text, Photo, Video, Sticker, etc.) you want to broadcast.\n\n"
                "Type /cancel to abort.",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_broadcast_step_1, bot)

        elif action == "stats":
            bot.answer_callback_query(call.id, "Fetching Details... 📊")
            
            now = datetime.datetime.now()
            today = datetime.datetime(now.year, now.month, now.day)
            yesterday = today - datetime.timedelta(days=1)
            five_mins_ago = now - datetime.timedelta(minutes=5)
            
            try:
                if 'users_col' in globals():
                    total_users = users_col.count_documents({})
                    new_today = users_col.count_documents({"joined_date": {"$gte": today}})
                    active_today = users_col.count_documents({"last_active": {"$gte": today}})
                    active_yesterday = users_col.count_documents({"last_active": {"$gte": yesterday, "$lt": today}})
                    live_users = users_col.count_documents({"last_active": {"$gte": five_mins_ago}})
                else:
                    total_users = new_today = active_today = active_yesterday = live_users = 0

                text = (
                    "📊 **WETFLIX BOT STATISTICS**\n\n"
                    f"👥 **Total Users:** `{total_users}`\n"
                    f"🆕 **New Users Today:** `{new_today}`\n"
                    f"🟢 **Active Today:** `{active_today}`\n"
                    f"🟡 **Active Yesterday:** `{active_yesterday}`\n"
                    f"🔥 **Currently Using (Live):** `{live_users}`"
                )
                bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Error fetching stats: `{e}`")
                
        elif action == "back":
            send_admin_panel(call.message)
            bot.delete_message(call.message.chat.id, call.message.message_id)

    # -----------------------------------------------------------
    # Step Handlers
    # -----------------------------------------------------------
    
    def process_broadcast_step_1(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Broadcast cancelled.")
            return
            
        # സേവ് ചെയ്ത മെസ്സേജ് രണ്ടാമത്തെ സ്റ്റെപ്പിലേക്ക് പാസ്സ് ചെയ്യുന്നു
        msg_to_broadcast = message
        
        bot_reply = bot.reply_to(
            message, 
            "🔘 **Step 2: Add Inline Button (Optional)**\n\n"
            "If you want to add a button below this message, type it in this format:\n"
            "`Button Name - https://yourlink.com`\n\n"
            "*(Example: Join Channel - https://t.me/wetflix)*\n\n"
            "If you don't need a button, simply type `/skip`.\n"
            "To cancel, type `/cancel`.",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(bot_reply, process_broadcast_step_2, bot, msg_to_broadcast)

    def process_broadcast_step_2(message, bot, msg_to_broadcast):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Broadcast cancelled.")
            return

        markup = None
        # യൂസർ ഇൻലൈൻ ബട്ടൺ നൽകിയാൽ അത് സെറ്റ് ചെയ്യുന്നു
        if message.text != '/skip':
            try:
                parts = message.text.split('-', 1)
                if len(parts) == 2:
                    btn_text = parts[0].strip()
                    btn_url = parts[1].strip()
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(btn_text, url=btn_url))
                else:
                    bot_reply = bot.reply_to(message, "❌ Invalid format. Please use exactly like this:\n`Button Name - https://link.com`\n\nOr type `/skip` to send without a button.", parse_mode='Markdown')
                    bot.register_next_step_handler(bot_reply, process_broadcast_step_2, bot, msg_to_broadcast)
                    return
            except Exception:
                bot.reply_to(message, "❌ Error creating button. Broadcasting without button.")

        bot.reply_to(message, "🚀 **Broadcasting started...** Please wait, this might take some time.", parse_mode='Markdown')
        
        try:
            users = users_col.find({})
            success = 0
            failed = 0
            
            for user in users:
                try:
                    # ഫോട്ടോയോ വീഡിയോയോ ടെക്സ്റ്റോ ഇൻലൈൻ ബട്ടൺ ഉൾപ്പെടെ ഫോർവേഡ് ടാഗ് ഇല്ലാതെ അയക്കുന്നു
                    bot.copy_message(
                        chat_id=user['user_id'], 
                        from_chat_id=msg_to_broadcast.chat.id, 
                        message_id=msg_to_broadcast.message_id,
                        reply_markup=markup
                    )
                    success += 1
                except Exception:
                    failed += 1
                    
            report = (
                "📢 **Broadcast Completed!**\n\n"
                f"✅ Successfully sent to: `{success}` users\n"
                f"❌ Failed (Blocked bot): `{failed}` users"
            )
            bot.send_message(message.chat.id, report, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Broadcast failed due to an error: `{e}`")

    def process_fsub_step(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return
            
        lines = message.text.strip().split('\n')
        channels_list = []
        
        for line in lines:
            args = line.strip().split()
            if len(args) >= 2:
                ch_id_str = args[0]
                inv_link = args[1]
                try:
                    ch_id = int(ch_id_str) if ch_id_str.startswith('-100') else ch_id_str
                    channels_list.append({"id": ch_id, "link": inv_link})
                except ValueError:
                    continue
                    
        if not channels_list:
            bot.reply_to(message, "❌ Invalid format!\nPlease provide Channel ID and Invite Link separated by space.", parse_mode='Markdown')
            return
        
        try:
            set_fsub_data(channels_list)
            bot.reply_to(message, f"✅ **Successfully configured {len(channels_list)} channel(s)!**", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to save to database.\nError: `{e}`", parse_mode='Markdown')

    def process_delay_step(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return
            
        try:
            seconds = float(message.text.strip())
            if seconds < 0:
                bot.reply_to(message, "⚠️ Time cannot be negative.")
                return
            set_cooldown(seconds)
            bot.reply_to(message, f"✅ **Command delay successfully set to {seconds} seconds!**", parse_mode='Markdown')
        except ValueError:
            bot.reply_to(message, "❌ Invalid input. Please enter a valid number (e.g., 5 or 30).", parse_mode='Markdown')

    def process_deletetime_step(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return
            
        try:
            new_time = float(message.text.strip())
            if new_time < 1:
                bot.reply_to(message, "⚠️ Time must be at least 1 second.")
                return
                
            settings_col.update_one(
                {"_id": "bot_settings"},
                {"$set": {"delete_time": new_time}},
                upsert=True
            )
            bot.reply_to(message, f"✅ **Auto-delete time successfully set to {new_time} seconds!**", parse_mode='Markdown')
        except ValueError:
            bot.reply_to(message, "❌ Invalid input. Please enter a valid number (e.g., 5 or 30).", parse_mode='Markdown')
