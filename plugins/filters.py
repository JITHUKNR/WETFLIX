# ഗ്രൂപ്പ് ഫിൽട്ടറുകൾ സേവ് ചെയ്തുവെക്കാനുള്ള ഡിക്ഷണറി
GROUP_FILTERS = {}

def is_user_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

def setup(bot):

    # 1. ഫിൽട്ടർ ആഡ് ചെയ്യാൻ (/save <keyword> <reply_text>)
    @bot.message_handler(commands=['save', 'addfilter'])
    def save_group_filter(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            bot.reply_to(message, "❌ This command can only be used in groups.")
            return
            
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            help_text = (
                "📌 **Group Filters Guide:**\n\n"
                "Save automatic replies for specific keywords in your group.\n\n"
                "👉 **Usage:** `/save <keyword> <reply_message>`\n"
                "👉 **Example:** `/save price Check out our store for latest pricing!`\n"
                "👉 **List Filters:** `/filters`\n"
                "👉 **Delete Filter:** `/stop <keyword>`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        keyword = args[1].lower().strip()
        reply_text = args[2].strip()
        
        if chat_id not in GROUP_FILTERS:
            GROUP_FILTERS[chat_id] = {}
            
        GROUP_FILTERS[chat_id][keyword] = reply_text
        bot.reply_to(message, f"✅ Saved filter for keyword: `{keyword}`", parse_mode='Markdown')

    # 2. സേവ് ചെയ്ത ഫിൽട്ടറുകൾ കാണാൻ (/filters)
    @bot.message_handler(commands=['filters'])
    def list_group_filters(message):
        chat_id = message.chat.id
        filters = GROUP_FILTERS.get(chat_id, {})
        
        if not filters:
            bot.reply_to(message, "📂 No custom filters saved in this group yet.")
            return
            
        filter_list = "📌 **Saved Group Filters:**\n\n"
        for kw in filters.keys():
            filter_list += f"• `{kw}`\n"
            
        bot.reply_to(message, filter_list, parse_mode='Markdown')

    # 3. ഫിൽട്ടർ ഡിലീറ്റ് ചെയ്യാൻ (/stop <keyword>)
    @bot.message_handler(commands=['stop', 'delfilter'])
    def delete_group_filter(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if message.chat.type == 'private':
            return
        if not is_user_admin(bot, chat_id, user_id):
            bot.reply_to(message, "⚠️ You must be an administrator to use this command.")
            return
            
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "👉 Please specify the keyword to stop.\n\n👉 **Example:** `/stop price`")
            return
            
        keyword = args[1].lower().strip()
        filters = GROUP_FILTERS.get(chat_id, {})
        
        if keyword in filters:
            del filters[keyword]
            bot.reply_to(message, f"🗑️ Successfully deleted filter for: `{keyword}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ No filter found for keyword: `{keyword}`")

    # 4. വരുന്ന മെസ്സേജുകൾ പരിശോധിച്ച് ഫിൽട്ടർ കീവേർഡ് ഉണ്ടെങ്കിൽ റിപ്ലൈ ചെയ്യുന്ന ഹാൻഡ്‌ലർ
    @bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'] and msg.text and not msg.text.startswith('/'), content_types=['text'])
    def check_filters(message):
        chat_id = message.chat.id
        text = message.text.lower().strip()
        filters = GROUP_FILTERS.get(chat_id, {})
        
        for keyword, reply in filters.items():
            # മെസ്സേജിൽ കീവേർഡ് ഉൾപ്പെട്ടിട്ടുണ്ടോ എന്ന് പരിശോധിക്കുന്നു
            if keyword in text:
                try:
                    bot.reply_to(message, reply)
                    break
                except Exception as e:
                    print(f"Filter Reply Error: {e}")
