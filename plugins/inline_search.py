from telebot.types import InlineQueryResultArticle, InputTextMessageContent
from database import videos_col

def setup(bot):

    @bot.inline_handler(func=lambda query: True)
    def inline_query_handler(query):
        try:
            search_text = query.query.strip().lower()
            
            # ഡാറ്റാബേസിൽ നിന്ന് വീഡിയോകൾ/ഫയലുകൾ എടുക്കുന്നു
            if search_text:
                # യൂസർ അടിക്കുന്ന കീവേഡ് വെച്ച് ഫിൽട്ടർ ചെയ്യാം അല്ലെങ്കിൽ മൊത്തമുള്ളവ കാണിക്കാം
                results_db = list(videos_col.find().limit(10))
            else:
                results_db = list(videos_col.find().limit(10))

            articles = []
            for idx, item in enumerate(results_db):
                file_id = item.get("file_id")
                # ഇൻലൈൻ റിസൾട്ട് ഉണ്ടാക്കുന്നു
                articles.append(
                    InlineQueryResultArticle(
                        id=str(idx),
                        title=f"🎬 Video File {idx + 1}",
                        description="Click to send this media from bot database.",
                        input_message_content=InputTextMessageContent(
                            message_text=f"Here is your requested file ID:\n`{file_id}`",
                            parse_mode='Markdown'
                        )
                    )
                )

            bot.answer_inline_query(query.id, articles, cache_time=1)
        except Exception as e:
            print(f"Inline Search Error: {e}")
