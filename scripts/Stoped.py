"""بوت وضع الصيانة: يشتغل بدل البوت الرئيسي لما يكون متوقف مؤقتاً.
تشغيل من جذر المشروع: py -3 -m scripts.Stoped
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import telebot

from config import ADMIN_IDS, MAINTENANCE_BOT_TOKEN
from db.connection import db_lock, get_db_connection
from DB_settings.DataBaseEditor import execute_sql_query

bot = telebot.TeleBot(MAINTENANCE_BOT_TOKEN)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

CLOSED_MESSAGE = "🚧 البوت متوقف مؤقتاً للصيانة والتحديث."


def init_database():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correct_users (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()


def save_correct_user(chat_id, username):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO correct_users (chat_id, username, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            chat_id,
            username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        added = cursor.rowcount == 1

        conn.commit()
        conn.close()
    return added


@bot.message_handler(commands=['SQL'])
def handle_sql_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    sql_text = message.text[len("/SQL"):].strip()

    if not sql_text:
        bot.reply_to(message, "اكتب استعلام SQL بعد /SQL")
        return

    success, result = execute_sql_query(sql_text)

    logging.info(
        "SQL command by -> userID=%s || Username=%s || SQL=%s",
        user_id, username, sql_text
    )

    if success:
        if sql_text.lower().startswith("select"):
            if not result:
                bot.reply_to(message, "تم التنفيذ، لكن ما فيه نتائج")
                return

            output_lines = [str(row) for row in result]
            output_text = "\n".join(output_lines)

            if len(output_text) > 4000:
                output_text = output_text[:4000] + "\n...\nالنتيجة طويلة وتم قصها"

            bot.reply_to(message, f"تم تنفيذ الاستعلام ✅\n\n{output_text}")
        else:
            bot.reply_to(message, f"تم تنفيذ العملية ✅\nعدد الصفوف المتأثرة: {result}")
    else:
        logging.error("SQL error by -> userID=%s || Username=%s || Error=%s", user_id, username, result)
        bot.reply_to(message, f"صار خطأ ❌\n{result}")


@bot.message_handler(commands=['Output'])
def send_output_file(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    logging.info("Output requested by -> userID=%s || Username=%s", user_id, message.from_user.username)

    try:
        with open("outputBot.log", "rb") as file:
            bot.send_document(message.chat.id, file)
    except Exception as error:
        logging.error("Output send error -> userID=%s || Username=%s || Error=%s", user_id, message.from_user.username, error)
        bot.send_message(message.chat.id, f"صار خطأ أثناء إرسال الملف ❌\n{error}")


@bot.message_handler(func=lambda message: True)
def bot_closed(message):
    username = message.from_user.username or "NoUsername"
    chat_id = message.chat.id
    text = message.text or "[Non-Text Message]"

    if message.text and message.text.strip().lower() in ("/sql", "/output"):
        return

    logging.info(
        f"Username: @{username} | ChatID: {chat_id} | Message: {text}"
    )

    if message.text and message.text.strip().lower() == "aspath":
        added = save_correct_user(chat_id, username)

        if added:
            bot.send_message(chat_id, "✅ تم تسجيلك بنجاح.")

    bot.reply_to(message, CLOSED_MESSAGE)


if __name__ == "__main__":
    init_database()
    print("Bot is running...")
    bot.infinity_polling()
