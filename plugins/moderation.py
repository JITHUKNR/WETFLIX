from telebot.types import ChatPermissions

# അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുന്ന ചെറിയ ഫംഗ്ഷൻ
def is_user_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

def setup(bot):

    # 1. BAN COMMAND
    @bot.message_handler(commands=['ban'])
    def ban_user(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            bot.reply_to(message, "❌ This command can only be used in groups.")
            return
            
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "👉 Please reply to the user you want to ban.")
            return
            
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        
        if is_user_admin(bot, chat_id, target_id):
            bot.reply_to(message, "❌ I cannot ban an administrator!")
            return
            
        try:
            bot.ban_chat_member(chat_id, target_id)
            bot.reply_to(message, f"🔨 Banned user {target_user.first_name} from the group.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to ban user: `{e}`", parse_mode='Markdown')

    # 2. UNBAN COMMAND
    @bot.message_handler(commands=['unban'])
    def unban_user(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            return
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "👉 Please reply to the user you want to unban.")
            return
            
        target_user = message.reply_to_message.from_user
        try:
            bot.unban_chat_member(chat_id, target_user.id, only_if_banned=True)
            bot.reply_to(message, f"🔓 Unbanned user {target_user.first_name}.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to unban user: `{e}`", parse_mode='Markdown')

    # 3. KICK COMMAND
    @bot.message_handler(commands=['kick'])
    def kick_user(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            return
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "👉 Please reply to the user you want to kick.")
            return
            
        target_user = message.reply_to_message.from_user
        if is_user_admin(bot, chat_id, target_user.id):
            bot.reply_to(message, "❌ I cannot kick an administrator!")
            return
            
        try:
            # കിക്ക് ചെയ്യാൻ ബാൻ ചെയ്ത് ഉടൻ അൺബാൻ ചെയ്യുന്നു (യൂസർക്ക് തിരിച്ച് ഗ്രൂപ്പിൽ വരാം)
            bot.ban_chat_member(chat_id, target_user.id)
            bot.unban_chat_member(chat_id, target_user.id)
            bot.reply_to(message, f"👢 Kicked user {target_user.first_name} from the group.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to kick user: `{e}`", parse_mode='Markdown')

    # 4. MUTE COMMAND
    @bot.message_handler(commands=['mute'])
    def mute_user(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            return
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "👉 Please reply to the user you want to mute.")
            return
            
        target_user = message.reply_to_message.from_user
        if is_user_admin(bot, chat_id, target_user.id):
            bot.reply_to(message, "❌ I cannot mute an administrator!")
            return
            
        try:
            # മെസ്സേജുകൾ അയക്കാനുള്ള അനുമതി മാത്രം ഓഫ് ചെയ്യുന്നു
            permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(chat_id, target_user.id, permissions=permissions)
            bot.reply_to(message, f"🔇 Muted user {target_user.first_name}.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to mute user: `{e}`", parse_mode='Markdown')

    # 5. UNMUTE COMMAND
    @bot.message_handler(commands=['unmute'])
    def unmute_user(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            return
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "👉 Please reply to the user you want to unmute.")
            return
            
        target_user = message.reply_to_message.from_user
        try:
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            bot.restrict_chat_member(chat_id, target_user.id, permissions=permissions)
            bot.reply_to(message, f"🔊 Unmuted user {target_user.first_name}.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to unmute user: `{e}`", parse_model='Markdown')
