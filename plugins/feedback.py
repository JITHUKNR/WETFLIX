from config import ADMIN_ID

def setup(bot):

    @bot.message_handler(commands=['feedback', 'report'])
    def send_feedback(message):
        if message.chat.type != 'private':
            return
            
        text = message.text.replace('/feedback', '').replace('/report', '').strip()
        
        if not text:
            bot.reply_to(message, "⚠️ Please write your feedback or bug report after the command.\n\n👉 **Usage:** `/feedback The bot is working great!`", parse_mode='Markdown')
            return
            
        user = message.from_user
        feedback_msg = (
            f"📩 **New Feedback Received!**\n\n"
            f"👤 **From:** {user.first_name} (@{user.username if user.username else 'No username'})\n"
            f"🆔 **User ID:** `{user.id}`\n\n"
            f"💬 **Message:**\n{text}"
        )
        
        try:
            # അഡ്മിന് ഫീഡ്‌ബാക്ക് അയക്കുന്നു
            bot.send_message(ADMIN_ID, feedback_msg, parse_mode='Markdown')
            bot.reply_to(message, "✅ Thank you! Your feedback has been sent to the admin successfully.")
        except Exception as e:
            bot.reply_to(message, "❌ Failed to send feedback. Please try again later.")
