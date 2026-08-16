from config import ADMIN_IDS
from logging_config import logger
from bot.errors import notify_admins_error
from bot.instance import bot
from DB_settings.DataBaseEditor import execute_sql_query
from DB_settings.syncExcilToSQL import start_sync


@bot.message_handler(commands=['SQL'])
def handle_sql_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية تستخدم هذا الأمر")
        return

    sql_text = message.text[len("/SQL"):].strip()

    if not sql_text:
        bot.reply_to(message, "اكتب استعلام SQL بعد /SQL")
        return

    success, result = execute_sql_query(sql_text)

    logger.info(
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
        logger.error("SQL error by -> userID=%s || Username=%s || Error=%s", user_id, username, result)
        bot.reply_to(message, f"صار خطأ ❌\n{result}")


@bot.message_handler(commands=['Sync'])
def handle_sql_sync(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    logger.info("Sync by -> userID=%s || Username=%s", user_id, message.from_user.username)

    try:
        start_sync()
        bot.send_message(message.chat.id, "تم مزامنة البيانات ✅")
    except Exception as error:
        logger.error("Sync error -> userID=%s || Username=%s || Error=%s", user_id, message.from_user.username, error)
        notify_admins_error("handle_sql_sync", error, f"userID={user_id}")
        bot.send_message(message.chat.id, f"صار خطأ أثناء المزامنة ❌\n{error}")


@bot.message_handler(commands=['Output'])
def send_output_file(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    logger.info("Output requested by -> userID=%s || Username=%s", user_id, message.from_user.username)

    try:
        with open("outputBot.log", "rb") as file:
            bot.send_document(message.chat.id, file)
    except Exception as error:
        logger.error("Output send error -> userID=%s || Username=%s || Error=%s", user_id, message.from_user.username, error)
        bot.send_message(message.chat.id, f"صار خطأ أثناء إرسال الملف ❌\n{error}")


@bot.message_handler(commands=['SendFixError'])
def handle_send_fix_error(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(
            message,
            "الصيغة غلط.\nاستخدم:\n/SendFixError CHAT_ID ملاحظتك"
        )
        return

    chat_id = parts[1]
    note = parts[2]

    fixed_message = (
        "🛠️ تم إصلاح المشكلة التي واجهتك سابقًا.\n\n"
        f"ملاحظة من الادمنℹ️:\n{note}\n\n"
        "🙏🏼 شكرًا لاستخدامك بوت Course_Path\n"
        "💙 نتمنى لك تجربة ممتعة ومفيدة."
    )

    try:
        bot.send_message(chat_id, fixed_message)
        bot.reply_to(message, "تم إرسال رسالة التصليح للمستخدم ✅")
        admin_log_message = (
            "🛠️ تم إصلاح مشكلة مستخدم\n\n"
            f"👤 Chat ID: {chat_id}\n"
            f"🧑‍💻 بواسطة: {message.from_user.first_name}\n"
            f"💬 ملاحظة الأدمن:\n{note}"
        )

        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_log_message)
            except Exception as e:
                logger.error("Failed to send admin log to %s: %s", admin_id, e)

    except Exception as error:
        logger.error("SendFixError error: %s", error)
        bot.reply_to(message, f"صار خطأ أثناء الإرسال ❌\n{error}")
