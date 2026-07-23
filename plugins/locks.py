# ഗ്രൂപ്പിലെ ലോക്ക് സ്റ്റാറ്റസ് സ്റ്റോർ ചെയ്യാൻ (മെമ്മറി ഡിക്ഷണറി)
GROUP_LOCKS = {}

def is_user_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

def setup(bot):

    @bot.message_handler(commands=['lock', 'unlock'])
    def toggle_lock(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            bot.reply_to(message, "❌ This command can only be used in groups.")
            return
            
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            # നിലവിലെ ലോക്ക് വിവരങ്ങൾ കാണിക്കുന്നു
            locks = GROUP_LOCKS.get(chat_id, {})
            status_text = "🔒 **Group Locks Status:**\n\n"
            for item in ['links', 'stickers', 'photos', 'documents']:
                status = "Locked 🔒" if locks.get(item, False) else "Unlocked 🔓"
                status_text += f"• **{item.capitalize()}:** {status}\n"
            status_text += "\n👉 **Usage:** `/lock links` or `/unlock stickers`"
            bot.reply_to(message, status_text, parse_mode='Markdown')
            return
            
        command = args[0].replace('/', '').lower()
        target_lock = args[1].lower().strip()
        
        allowed_locks = ['links', 'stickers', 'photos', 'documents']
        if target_lock not in allowed_locks:
            bot.reply_to(message, f"❌ Invalid lock type. Choose from: `{', '.join(allowed_locks)}`", parse_mode='Markdown')
            return
            
        if chat_id not in GROUP_LOCKS:
            GROUP_LOCKS[chat_id] = {}
            
        is_lock = (command == 'lock')
        GROUP_LOCKS[chat_id][target_lock] = is_lock
        
        action_text = "Locked 🔒" if is_lock else "Unlocked 🔓"
        bot.reply_to(message, f"✅ **{target_lock.capitalize()}** has been **{action_text}** for this group.", parse_mode='Markdown')

    # ലോക്ക് ചെയ്തിട്ടുള്ള കണ്ടന്റുകൾ വരുന്ന മുറയ്ക്ക് ഡിലീറ്റ് ചെയ്യുന്ന ഹാൻഡ്‌ലർ
    @bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'] and not is_user_admin(bot, msg.chat.id, msg.from_user.id), content_types=['text', 'sticker', 'photo', 'document'])
    def check_group_locks(message):
        chat_id = message.chat.id
        locks = GROUP_LOCKS.get(chat_id, {})
        
        # അഡ്മിൻ അല്ലാത്തവർ അയക്കുന്നവ പരിശോധിക്കുന്നു
        should_delete = False
        
        # 1. സ്റ്റിക്കർ ലോക്ക്
        if message.sticker and locks.get('stickers', False):
            should_delete = True
            
        # 2. ഫോട്ടോ ലോക്ക്
        elif message.photo and locks.get('photos', False):
            should_delete = True
            
        # 3. ഡോക്യുമെന്റ് ലോക്ക്
        elif message.document and locks.get('documents', False):
            should_delete = True
            
        # 4. ലിങ്ക് ലോക്ക് (ടെക്സ്റ്റിലോ ക്യാപ്ഷനിലോ http ഉണ്ടെങ്കിൽ)
        elif message.text and locks.get('links', False):
            if "http://" in message.text or "https://" in message.text or "t.me/" in message.text:
                should_delete = True
                
        if should_delete:
            try:
                bot.delete_message(chat_id, message.message_id)
                # മുന്നറിയിപ്പ് മെസ്സേജ് അയച്ച് പെട്ടെന്ന് ഡിലീറ്റ് ചെയ്യാം അല്ലെങ്കിൽ സൈലന്റ് ആകാം
                warn_msg = bot.send_message(chat_id, f"⚠️ Hey {message.from_user.first_name}, that content is restricted in this group!")
                # 5 സെക്കൻഡിന് ശേഷം വാർണിംഗ് മെസ്സേജ് ഒഴിവാക്കാൻ സഹായിക്കുന്ന ചെറിയ കോഡ് കൊടുക്കാം
            except Exception as e:
                print(f"Lock Delete Error: {e}")
