from config import ADMIN_IDS, HOME_TEXT
from logging_config import logger
from bot.instance import bot
from bot.keyboards import build_login_keyboard, build_main_menu_keyboard
from bot.state import user_history
from db.queries import create_user, get_user_verified


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "None"
    stack = user_history.get(user_id, [])
    stack.clear()

    row = get_user_verified(user_id)

    if row is None:
        # مستخدم جديد → احفظه في الديتابيس وسجل في اللوق
        create_user(user_id, username)

        logger.info("New user joined -> userID=%s || Username=%s", user_id, username)

        bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())
        return

    logger.info("User started bot -> userID=%s || Username=%s || Verified=%s", user_id, username, row[0])

    if row[0] > 0:
        bot.send_message(message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "للمساعدة، يرجى مراسلة الدعم الفني على @Course_path_support")


@bot.message_handler(commands=['Commands'])
def handle_commands(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    commands_text = (
        "🛠️ <b>لوحة أوامر الإدارة</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "🎓 <b>إدارة المواد</b>\n\n"

        "➕ <code>!AddCourse MAJOR TERM COURSE_ID اسم_المادة</code>\n"
        "تسجيل مادة جديدة (تخصص + مستوى + اسمها).\n"
        "مثال: <code>!AddCourse IT 7 CPCS-203 برمجة 2 - OOP</code>\n"
        "التخصصات: CS, IT, IS, FD\n\n"

        "ℹ️ <code>!SetInfo COURSE_ID النص</code>\n"
        "تعديل \"نبذة عن المادة\".\n\n"

        "🔗 <code>!SetSources COURSE_ID النص</code>\n"
        "تعديل \"مصادر المادة\".\n\n"

        "🗑️ <code>!DeleteCourse COURSE_ID</code>\n"
        "حذف مادة كاملة من الداتابيس (يعرض تأكيد أول، ما يمس الملفات على السيرفر).\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
        "📁 <b>إدارة الملفات</b>\n\n"

        "📤 <code>!Add COURSE SECTION TYPE FILE_NAME</code>\n"
        "(اكتبها caption على الملف)\n"
        "إضافة ملف جديد لمادة مسجّلة أصلاً.\n"
        "مثال: <code>!Add CPCS-204 slides lecture Ch09</code>\n\n"

        "🗑️ <code>!DeleteFile COURSE SECTION TYPE FILE_NAME</code>\n"
        "حذف ملف من النظام.\n\n"

        "🔀 <code>!Reorder COURSE_ID slides|exams TYPE TITLE POSITION</code>\n"
        "تغيير ترتيب ظهور ملف بالقائمة.\n"
        "مثال: <code>!Reorder CPCS-204 slides lecture Ch05 2</code>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
        "🗄️ <b>قاعدة البيانات</b>\n\n"

        "💻 <code>/SQL استعلام</code>\n"
        "تنفيذ استعلام SQL مباشرة.\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ <b>النظام</b>\n\n"

        "📄 <code>/Output</code>\n"
        "إرسال ملف السجل (Log File).\n\n"

        "✅ <code>/SendFixError CHAT_ID الملاحظة</code>\n"
        "إشعار مستخدم بإصلاح مشكلته."
    )

    bot.send_message(
        message.chat.id,
        commands_text,
        parse_mode="HTML"
    )
