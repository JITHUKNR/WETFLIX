from database import users_col

def setup(bot):

    @bot.message_handler(commands=['leaderboard', 'top'])
    def show_leaderboard(message):
        try:
            # ഡാറ്റാബേസിൽ നിന്ന് ഏറ്റവും കൂടുതൽ പോയിന്റുള്ള ടോപ്പ് 10 ആളുകളെ എടുക്കുന്നു
            top_users = list(users_col.find().sort("points", -1).limit(10))
            
            if not top_users:
                bot.reply_to(message, "📊 Leaderboard is currently empty.")
                return
                
            text = "🏆 **Top 10 Active Users Leaderboard**\n\n"
            
            for idx, user in enumerate(top_users, 1):
                uid = user.get("user_id")
                points = user.get("points", 0)
                
                # യൂസറുടെ പേര് കണ്ടെത്താൻ ശ്രമിക്കുന്നു
                try:
                    chat_member = bot.get_chat_member(message.chat.id, uid)
                    name = chat_member.user.first_name
                except:
                    name = f"User {uid}"
                    
                # മെഡലുകൾ നൽകുന്നു
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
                text += f"{medal} **{name}** — `{points}` Points\n"
                
            bot.reply_to(message, text, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Error loading leaderboard: {e}")
