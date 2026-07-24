from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
try:
    from database import set_fsub_channel, get_fsub_channel
except ImportError:
    pass # ഡാറ്റാബേസ് ഫയൽ ഇല്ലെങ്കിൽ എറർ വരാതിരിക്കാൻ

def setup(bot):

    # 1. അഡ്മിൻ പാനൽ തുറക്കാനുള്ള കമാൻഡ്
    @bot.message_handler(commands=['admin'])
    def send_admin_panel(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അനുവാദമില്ല.")
            return
            
        markup = InlineKeyboardMarkup(row_width=2)
        
        # --- എല്ലാ ഫീച്ചറുകൾക്കുമുള്ള ബട്ടണുകൾ ---
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
            "താഴെ കാണുന്ന ബട്ടണുകൾ ഉപയോഗിച്ച് ബോട്ടിന്റെ എല്ലാ ഫീച്ചറുകളും നിയന്ത്രിക്കാം:"
        )
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

    # 2. ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്യുമ്പോൾ വർക്ക് ചെയ്യാനുള്ള ഭാഗം
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ You are not an admin!", show_alert=True)
            return
            
        action = call.data.split('_')[1]
        
        # --- ഓരോ ബട്ടണിന്റെയും പ്രവർത്തനങ്ങൾ ---

        if action == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Admin Panel Closed.")

        elif action == "fsub":
            bot.answer_callback_query(call.id, "FSub Setup ⚙️")
            msg = bot.send_message(
                call.message.chat.id, 
                "📢 **Force Subscribe സെറ്റ് ചെയ്യാൻ:**\n\nനിങ്ങളുടെ പുതിയ ചാനലിന്റെ യൂസർനെയിം (@ ഉൾപ്പെടെ) താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക.\n(ഉദാഹരണത്തിന്: `@wetflax`)\n\nക്യാൻസൽ ചെയ്യാൻ /cancel എന്ന് അടിക്കുക."
            )
            # യൂസർ ടൈപ്പ് ചെയ്യുന്നത് പിടിച്ചെടുക്കാൻ next_step_handler ഉപയോഗിക്കുന്നു
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
                "🔐 **Group Locks Manager:**\n\nഗ്രൂപ്പിൽ തടയേണ്ട കാര്യങ്ങൾ തിരഞ്ഞെടുക്കുക:", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                reply_markup=lock_markup,
                parse_mode='Markdown'
            )

        elif action == "mod":
            bot.answer_callback_query(call.id, "Moderation Tools 🛡️")
            text = (
                "🛡️ **Moderation Commands Guide:**\n\n"
                "ഗ്രൂപ്പിൽ മെസ്സേജുകൾക്ക് റിപ്ലൈ ആയി താഴെ പറയുന്നവ ഉപയോഗിക്കുക:\n"
                "• `/ban` - യൂസറെ ബാൻ ചെയ്യാൻ\n"
                "• `/mute` - മെസ്സേജ് അയക്കുന്നത് തടയാൻ\n"
                "• `/warn` - വാർണിംഗ് കൊടുക്കാൻ\n"
                "• `/kick` - പുറത്താക്കാൻ"
            )
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

        elif action == "welcome":
            bot.answer_callback_query(call.id, "Welcome Settings 👋")
            bot.send_message(call.message.chat.id, "👋 വെൽക്കം മെസ്സേജ് നിലവിൽ ആക്റ്റീവ് ആണ്. അത് മാറ്റാനുള്ള ഫീച്ചർ വൈകാതെ വരുന്നതാണ്!")

        elif action == "broadcast":
            bot.answer_callback_query(call.id, "Broadcast 📢")
            bot.send_message(call.message.chat.id, "📢 **Broadcast:**\nഎല്ലാവർക്കും മെസ്സേജ് അയക്കാൻ `/broadcast നിങ്ങളുടെ മെസ്സേജ്` എന്ന് ടൈപ്പ് ചെയ്യുക.")

        elif action == "stats":
            bot.answer_callback_query(call.id, "Bot Statistics 📊")
            bot.send_message(call.message.chat.id, "📊 **Bot Stats:**\nഡാറ്റാബേസിൽ നിന്നുള്ള യൂസർമാരുടെ എണ്ണം പരിശോധിക്കാൻ `/stats` എന്ന് ടൈപ്പ് ചെയ്യുക.")

        elif action == "back":
            # തിരികെ മെയിൻ മെനുവിലേക്ക് പോകാൻ
            send_admin_panel(call.message)
            bot.delete_message(call.message.chat.id, call.message.message_id)

    # 3. FSub ചാനൽ സേവ് ചെയ്യാനുള്ള സ്റ്റെപ്പ് ഫംഗ്ഷൻ (കമാൻഡ് ഇല്ലാതെ)
    def process_fsub_step(message, bot):
        if message.text == '/cancel':
            bot.reply_to(message, "❌ പ്രവർത്തനം ക്യാൻസൽ ചെയ്തു.")
            return
            
        channel = message.text.strip()
        if not channel.startswith('@'):
            bot.reply_to(message, "❌ തെറ്റായ രീതി! ചാനൽ യൂസർനെയിം നിർബന്ധമായും '@' ൽ തുടങ്ങണം. വീണ്ടും /admin എടുത്ത് ശ്രമിക്കുക.")
            return
            
        try:
            # ഡാറ്റാബേസിലേക്ക് സേവ് ചെയ്യുന്നു
            set_fsub_channel(channel)
            bot.reply_to(message, f"✅ **Force Subscribe വിജയകരമായി സെറ്റ് ചെയ്തു!**\n\nപുതിയ ചാനൽ: {channel}", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ ഡാറ്റാബേസിൽ സേവ് ചെയ്യാൻ കഴിഞ്ഞില്ല. Database ഫയൽ ശരിയാണോ എന്ന് നോക്കുക.\nError: `{e}`", parse_mode='Markdown')
