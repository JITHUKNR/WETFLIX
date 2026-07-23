from config import ADMIN_ID
from database import users_col
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time

def setup(bot):

    @bot.message_handler(commands=['sbroadcast', 'sbc'])
    def selective_broadcast_menu(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        if not message.reply_to_message:
            help_text = (
                "📢 **Selective Broadcast Guide:**\n\n"
                "Reply to any message with `/sbc` to choose how you want to broadcast it.\n\n"
                "👉 **Usage:** Reply to a message and type `/sbc`"
            )
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
            
        # ബ്രോഡ്കാസ്റ്റ് രീതി തെരഞ്ഞെടുക്കാൻ ബട്ടണുകൾ നൽകുന്നു
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📤 Copy Mode", callback_data="bc_copy"),
            InlineKeyboardButton("🔄 Forward Mode", callback_data="bc_fwd")
        )
        
        bot.reply_to(
            message,
            "🎛️ **Choose Broadcast Mode:**\n\n"
            "• **Copy Mode:** Sends the message cleanly without the 'Forwarded from' tag.\n"
            "• **Forward Mode:** Forwards the exact message with the original sender tag.",
            reply_markup=markup,
            parse_mode='Markdown'
        )

    @bot.callback_query_handler(func=lambda call: call.data in ["bc_copy", "bc_fwd"])
    def execute_selective_broadcast(call):
        if call.from_user.id != ADMIN_ID:
            return
            
        if not call.message.reply_to_message:
            bot.answer_callback_query(call.id, "⚠️ Original message not found!", show_alert=True)
            return
            
        mode = call.data
        reply_msg = call.message.reply_to_message
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        
        bot.edit_message_text("🚀 Broadcast is running in the background...", chat_id, msg_id)
        
        def run_broadcast():
            users = list(users_col.find({"banned": {"$ne": True}}))
            success = 0
            failed = 0
            
            for user in users:
                uid = user.get("user_id")
                try:
                    if mode == "bc_copy":
                        bot.copy_message(uid, chat_id, reply_msg.message_id)
                    else:
                        bot.forward_message(uid, chat_id, reply_msg.message_id)
                        
                    success += 1
                    time.sleep(0.1)
                except Exception:
                    failed += 1
                    
            bot.send_message(
                chat_id,
                f"✅ **Selective Broadcast Completed!**\n\n"
                f"📊 **Mode:** `{'Copy Mode' if mode == 'bc_copy' else 'Forward Mode'}`\n"
                f"📤 **Success:** `{success}`\n"
                f"❌ **Failed:** `{failed}`",
                parse_mode='Markdown'
            )
            
        threading.Thread(target=run_broadcast).start()
