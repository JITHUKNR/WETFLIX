from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
try:
    from database import set_fsub_data
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
        markup.add(InlineKeyboardButton("❌ Close Panel", callback_data="admin_close"))
        
        text = (
            "🛠 **WETFLIX SUPER ADMIN PANEL**\n\n"
            "Use the buttons below to manage all bot features:"
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
                "`-1001234567890 https://t.me/+Link1`\n"
                "`-1009876543210 https://t.me/+Link2`\n\n"
                "Type /cancel to abort.",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_fsub_step, bot)

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
            bot.answer_callback_query(call.id, "Broadcast 📢")
            bot.send_message(call.message.chat.id, "📢 **Broadcast:**\nTo send a message to all users, type `/broadcast your message`.")

        elif action == "stats":
            bot.answer_callback_query(call.id, "Bot Statistics 📊")
            bot.send_message(call.message.chat.id, "📊 **Bot Stats:**\nType `/stats` to view the total number of users.")

        elif action == "back":
            send_admin_panel(call.message)
            bot.delete_message(call.message.chat.id, call.message.message_id)

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
            bot.reply_to(message, "❌ Invalid format!\nPlease provide Channel ID and Invite Link separated by space.\nExample:\n`-1001234567890 https://t.me/+AbCdEfGh`", parse_mode='Markdown')
            return
        
        try:
            set_fsub_data(channels_list)
            bot.reply_to(message, f"✅ **Successfully configured {len(channels_list)} channel(s)!**", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to save to database.\nError: `{e}`", parse_mode='Markdown')
