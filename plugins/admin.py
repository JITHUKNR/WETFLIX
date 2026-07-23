from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from config import ADMIN_ID
from database import users_col, videos_col, images_col, stickers_col, settings_col

def is_maintenance():
    state = settings_col.find_one({"_id": "maintenance"})
    return state["status"] if state else False

def get_admin_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("📊 Stats", callback_data="help_stats"),
        InlineKeyboardButton("📢 Broadcast", callback_data="help_broadcast"),
        InlineKeyboardButton("🚫 Ban User", callback_data="help_ban"),
        InlineKeyboardButton("✅ Unban User", callback_data="help_unban"),
        InlineKeyboardButton("⚙️ Maintenance Mode", callback_data="help_maintenance")
    )
    return markup

def setup(bot):
    @bot.message_handler(commands=['admin'])
    def admin_menu(message):
        if message.from_user.id != ADMIN_ID: return
        bot.reply_to(message, "👑 **Admin Control Panel**\n\nClick the buttons below to see how to use each command:", reply_markup=get_admin_menu(), parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('help_'))
    def admin_help(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Access Denied ❌", show_alert=True)
            return

        text = ""
        if call.data == "help_back":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text="👑 **Admin Control Panel**\n\nClick the buttons below to see how to use each command:", 
                                  reply_markup=get_admin_menu(), parse_mode='Markdown')
            return
        elif call.data == "help_stats":
            text = "📊 **Stats Command**\n\nView bot statistics (users, files, etc.).\n\n👉 **Usage:** `/stats`"
        elif call.data == "help_broadcast":
            text = "📢 **Broadcast Command**\n\nSend a message to all users.\n\n👉 **Usage:** `/broadcast <message>`"
        elif call.data == "help_ban":
            text = "🚫 **Ban Command**\n\nBan a user from using the bot.\n\n👉 **Usage:** `/ban <User ID>`"
        elif call.data == "help_unban":
            text = "✅ **Unban Command**\n\nUnban a previously banned user.\n\n👉 **Usage:** `/unban <User ID>`"
        elif call.data == "help_maintenance":
            text = "⚙️ **Maintenance Command**\n\nToggle maintenance mode ON or OFF.\n\n👉 **Usage:** `/maintenance`"

        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="help_back"))

        bot.answer_callback_query(call.id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='Markdown', reply_markup=back_markup)

    @bot.message_handler(commands=['stats'])
    def admin_stats(message):
        if message.from_user.id != ADMIN_ID: return
        t_users = users_col.count_documents({})
        b_users = users_col.count_documents({"banned": True})
        v_count = videos_col.count_documents({})
        i_count = images_col.count_documents({})
        s_count = stickers_col.count_documents({})
        text = f"📊 **Bot Statistics**\n\n👥 Total Users: {t_users}\n🚫 Banned Users: {b_users}\n\n📁 Saved Videos: {v_count}\n🖼️ Saved Photos: {i_count}\n🎭 Saved Stickers: {s_count}"
        bot.reply_to(message, text)

    @bot.message_handler(commands=['broadcast'])
    def admin_broadcast(message):
        if message.from_user.id != ADMIN_ID: return
        msg_text = message.text.replace('/broadcast', '').strip()
        if not msg_text:
            bot.reply_to(message, "Please provide a message. Example: /broadcast Hello everyone!")
            return
        users = users_col.find({"banned": False})
        success, failed = 0, 0
        bot.reply_to(message, "Broadcast started...")
        for u in users:
            try:
                bot.send_message(u['user_id'], msg_text)
                success += 1
                time.sleep(0.05)
            except:
                failed += 1
        bot.reply_to(message, f"✅ **Broadcast Completed!**\nSuccessful: {success}\nFailed: {failed}")

    @bot.message_handler(commands=['ban', 'unban'])
    def admin_ban_unban(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            target_id = int(message.text.split()[1])
            is_ban = '/ban' in message.text
            users_col.update_one({"user_id": target_id}, {"$set": {"banned": is_ban}}, upsert=True)
            status = "Banned" if is_ban else "Unbanned"
            bot.reply_to(message, f"✅ User {target_id} has been successfully {status}.")
        except:
            bot.reply_to(message, "Invalid format. Example: /ban 12345678")

    @bot.message_handler(commands=['maintenance'])
    def admin_maintenance(message):
        if message.from_user.id != ADMIN_ID: return
        current = is_maintenance()
        new_state = not current
        settings_col.update_one({"_id": "maintenance"}, {"$set": {"status": new_state}}, upsert=True)
        status_text = "Turned ON" if new_state else "Turned OFF"
        bot.reply_to(message, f"⚙️ Maintenance mode {status_text}.")
