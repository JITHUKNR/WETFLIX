from config import ADMIN_ID
from database import users_col, videos_col

def setup(bot):

    @bot.message_handler(commands=['stats', 'status'])
    def bot_statistics(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        try:
            # ഡാറ്റാബേസിൽ നിന്ന് യൂസർമാരുടെയും ഫയലുകളുടെയും കണക്കുകൾ എടുക്കുന്നു
            total_users = users_col.count_documents({})
            banned_users = users_col.count_documents({"banned": True})
            active_users = total_users - banned_users
            total_videos = videos_col.count_documents({})
            
            stats_text = (
                f"📊 **Bot Live Statistics**\n\n"
                f"👥 **Total Users:** `{total_users}`\n"
                f"🟢 **Active Users:** `{active_users}`\n"
                f"🔴 **Banned Users:** `{banned_users}`\n"
                f"📁 **Total Media Files:** `{total_videos}`\n\n"
                f"🚀 **Status:** `Online & Healthy`"
            )
            
            bot.reply_to(message, stats_text, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Error fetching stats: {e}")
