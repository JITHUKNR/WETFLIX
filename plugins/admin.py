from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
try:
    from database import set_fsub_data
except ImportError:
    pass # To prevent errors if the database file is missing

def setup(bot):

    # 1. Command to open the Admin Panel
    @bot.message_handler(commands=['admin'])
    def send_admin_panel(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return
            
        markup = InlineKeyboardMarkup(row_width=2)
        
        # --- Buttons for all features ---
        markup.add(
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")
        )
        markup.add(
            InlineKeyboardButton("⚙️ FSub Channel", callback_data="admin_fsub"),
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

    # 2. Handler for button clicks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ You are not an admin!", show_alert=True)
            return
            
        action = call.data.split('_')[1]
        
        # --- Actions for each button ---

        if action == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Admin Panel Closed.")

        elif action == "fsub":
            bot.answer_callback_query(call.id, "FSub Setup ⚙️")
            msg = bot.send_message(
                call.message.chat.id, 
                "📢 **Force Subscribe Setup:**\n\n"
                "Please send the Channel ID and Invite Link separated by a space.\n"
                "(Example: `-1001234567890 https://t.me/+AbCdEfGh`)\n\n"
                "Type /cancel to cancel the operation.",
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
                "🔐 **Group Locks Manager:**\n\nSelect the items to restrict in the group:", 
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
            bot.send_message(call.message.chat.id, "👋 Welcome message is currently active. Customization features coming soon!")

        elif action == "broadcast":
            bot.answer_callback_query(call.id, "Broadcast 📢")
            bot.send_message(call.message.chat.id, "📢 **Broadcast:**\nTo send a message to all users, type `/broadcast your message`.")

        elif action == "stats":
            bot.answer_callback_query(call.id, "Bot Statistics 📊")
            bot.send_message(call.message.chat.id, "📊 **Bot Stats:**\nType `/stats` to view the total number of users from the database.")

        elif action == "back":
            # Go back to main menu
            send_admin_panel(call.message)
            bot.delete_message(call.message.chat.id, call.message.message_id)

    # 3. Step function to save FSub Channel and Link
    def process_fsub_step(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ Operation cancelled.")
            return
            
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Invalid format!\nPlease provide the Channel ID and Invite Link separated by a space.\nExample:\n`-1001234567890 https://t.me/+AbCdEfGh`", parse_mode='Markdown')
            return
            
        channel_id_str = args[0]
        invite_link = args[1]
        
        try:
            channel_id = int(channel_id_str) if channel_id_str.startswith('-100') else channel_id_str
            set_fsub_data(channel_id, invite_link)
            bot.reply_to(message, f"✅ **Force Subscribe configured successfully!**\n\n📢 Channel ID: `{channel_id}`\n🔗 Link: {invite_link}", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to save to database.\nError: `{e}`", parse_mode='Markdown')
