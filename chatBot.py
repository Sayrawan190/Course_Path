import telebot
from telebot import types
import logging
import sqlite3
import threading
import sys
import re
from DB_settings.DataBaseEditor import delete_user, execute_sql_query
from DB_settings.syncExcilToSQL import start_sync
import TOTP
from pathlib import Path
from telebot.types import BotCommand

# ==========================================================
# تسجيل اللوق (Logs)
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("FCIT_BOT")


# ==========================================================
# Database (SQLite)
# ==========================================================
DB_PATH = r"DataBase/FCIT_bot.db"
db_lock = threading.Lock()

def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ==========================================================
# History + State
# ==========================================================
user_history = {}
waiting_search = {}
waiting_email = {}


def push_history(user_id, data):
    user_history.setdefault(user_id, []).append(data)


def pop_history(user_id):
    stack = user_history.get(user_id, [])
    if stack:
        stack.pop()
    return stack


# ==========================================================
# Bot
# ==========================================================
# TOKEN: توكن البوت من BotFather
# ملاحظة صيانة: لا تشارك التوكن في أي مكان عام.

# course token = 8554120109:AAHZttTkOfttgX1plyHCasFtno3ZV_geDVw
# test token = 8578172399:AAFimx2WP-q2xGWM6Ge-mLRcH_9rytapUZw

TOKEN = "8578172399:AAFimx2WP-q2xGWM6Ge-mLRcH_9rytapUZw"
bot = telebot.TeleBot(TOKEN)

bot.set_my_commands([
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Help and guide"),
])

# ==========================================================
# ثوابت النصوص/المسميات
# ==========================================================
MAJOR_NAME = {
    "CS": "علوم حاسب 💡",
    "IT": "تقنية معلومات 💻",
    "IS": "نظم معلومات 💸",
    "FD": "التحضيري 👶🏻"
}

HOME_TEXT ="مرحباً بك مجدداً\n" + "القائمة الرئيسية🏠\nاختر تخصصك من القائمة:"


# ==========================================================
# Helpers
# ==========================================================
def cb(*parts):
    return "|".join(parts)


from telebot.apihelper import ApiTelegramException

def edit_message(call, text, kb=None):
    try:
        bot.edit_message_text(
            text=text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            return
        raise

def send_message(call, text, kb=None):
    try:
        bot.send_message(
            text=text,
            chat_id=call.message.chat.id,
            reply_markup=kb
        )
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            return
        raise


def build_nav_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("↩️ رجوع", callback_data=cb("BACK")),
        types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data=cb("HOME")),
    )
    return kb


def build_keyboard_from_buttons(buttons, row_width=2, add_nav=True):
    kb = types.InlineKeyboardMarkup(row_width=row_width)

    if buttons:
        kb.add(*buttons)

    if add_nav:
        kb.add(
            types.InlineKeyboardButton("رجوع ↩️", callback_data=cb("BACK")),
            types.InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data=cb("HOME")),
        )
    return kb


def send_document_file(call, file_path):
    try:
        with open(file_path, "rb") as f:
            bot.send_document(call.message.chat.id, f)
        return True

    except FileNotFoundError as e:
        logger.error("File Not Found Error: %s", e)
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. الرجاء التواصل مع الدعم الفني.", build_nav_keyboard())
        show_help(call, None)
        return False

    except Exception as e:
        logger.error("Error sending file: %s", e)
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. الرجاء التواصل مع الدعم الفني.", build_nav_keyboard())
        show_help(call, None)
        return False


# ==========================================================
# Main Menu
# ==========================================================
def build_login_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🔐 تسجيل الدخول", callback_data=cb("LOGIN")),
        types.InlineKeyboardButton("🤖 عن البوت", callback_data=cb("ABOUT"))
    )
    return kb

def build_main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(MAJOR_NAME["CS"], callback_data=cb("MAJOR", "CS")),
        types.InlineKeyboardButton(MAJOR_NAME["IT"], callback_data=cb("MAJOR", "IT")),
        types.InlineKeyboardButton(MAJOR_NAME["IS"], callback_data=cb("MAJOR", "IS")),
        types.InlineKeyboardButton(MAJOR_NAME["FD"], callback_data=cb("MAJOR", "FD")),
    )
    kb.row(
        types.InlineKeyboardButton("بحث يدوي🔎", callback_data=cb("SEARCH")),
        types.InlineKeyboardButton("مراسلة الدعم الفني👨🏻‍💻", callback_data=cb("HELP")),
    )
    return kb


# ==========================================================
# DB Queries
# ==========================================================
def get_terms_for_major(major_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT term FROM major_Terms WHERE major_code = ?", (major_code,))
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_courses_for_major_term(major_code, term):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT course_id FROM major_Terms WHERE major_code = ? AND term = ?",
            (major_code, term)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_course_title(*args):
    if len(args) == 1:
        course_id = args[0]
        course_name, course_code = course_id.split("-", 1)
    elif len(args) == 2:
        course_name, course_code = args

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT course_title FROM courses WHERE course_name = ? AND course_code = ?",
            (course_name, course_code)
        )
        row = cursor.fetchone()
        conn.close()
    return row[0] if row else None


def get_sections_for_course(course_name, course_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT section, title FROM courses WHERE course_name = ? and course_code = ? ORDER BY ord",
            (course_name, course_code)
        )
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


def get_slide_types(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT slide_type, button_title FROM slides WHERE course_id = ?", (course_id,))
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


def get_exam_types(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT exam_type, button_title FROM exams WHERE course_id = ?", (course_id,))
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


def get_chapters_for_slide(course_id, slide_type):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT title FROM slides WHERE course_id = ? AND slide_type = ? ORDER BY ord",
            (course_id, slide_type)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_exams_titles(course_id, exam_type):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT title FROM exams WHERE course_id = ? AND exam_type = ? ORDER BY ord",
            (course_id, exam_type)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_info_text(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT info FROM info_sources WHERE course_id = ?", (course_id,))
        row = cursor.fetchone()
        conn.close()
    info = row[0] if row else "لا توجد معلومات متاحة حاليًا"
    info = info.replace("||", "\n")
    return info


def get_sources_text(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sources FROM info_sources WHERE course_id = ?", (course_id,))
        row = cursor.fetchone()
        conn.close()
    sources = row[0] if row else "لا توجد مصادر متاحة حاليًا"
    sources = sources.replace("||", "\n")
    return sources


def get_slide_file_path(course_id, slide_type, title):
    pathExams = Path(f"DataBase/Courses/{course_id}/Slides/{slide_type}")
    for f in pathExams.rglob(f"*{title}*"):
        return f


def get_exam_file_path(course_id, exam_type, title):
    pathExams = Path(f"DataBase/Courses/{course_id}/Exams/{exam_type}")
    for f in pathExams.rglob(f"*{title}*"):
        return f


# ==========================================================
# Keyboards Builders
# ==========================================================
def build_terms_keyboard(terms, major_code):
    buttons = [
        types.InlineKeyboardButton(f"الترم {term}️⃣", callback_data=cb("TERM", major_code, str(term)))
        for term in terms
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_courses_keyboard(courses):
    buttons = [
        types.InlineKeyboardButton(course, callback_data=cb("COURSE", course))
        for course in courses
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_sections_keyboard(sections, course_name, course_code):
    buttons = [
        types.InlineKeyboardButton(
            title,
            callback_data=cb("SECTION", f"{course_name}-{course_code}", section_code)
        )
        for section_code, title in sections
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_slide_types_keyboard(course_id, slide_types):
    buttons = [
        types.InlineKeyboardButton(button_title, callback_data=cb("SLIDES", course_id, st))
        for st, button_title in slide_types
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_exam_types_keyboard(course_id, exam_types):
    buttons = [
        types.InlineKeyboardButton(button_title, callback_data=cb("EXAM", course_id, et))
        for et, button_title in exam_types
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_chapters_keyboard(course_id, slide_type, chapters):

    buttons = [
        types.InlineKeyboardButton(ch, callback_data=cb("CHAPTER", course_id, slide_type, ch))
        for ch in chapters
    ]

    kb = types.InlineKeyboardMarkup(row_width=4)

    kb.add(*buttons)

    kb.row(
        types.InlineKeyboardButton("Send all chapters 📂", callback_data=cb("SEND_ALL_CHAPTERS", course_id, slide_type))
    )
    kb.row(
            types.InlineKeyboardButton("رجوع ↩️", callback_data=cb("BACK")),
            types.InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data=cb("HOME")),
        )
    return kb

def build_exams_keyboard(course_id, exam_type, exams_titles):
    buttons = [
        types.InlineKeyboardButton(ex, callback_data=cb("GETEXAM", course_id, exam_type, ex))
        for ex in exams_titles
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


# ==========================================================
# Actions (Handlers)
# ==========================================================
def cheack_itsEmpty(call, array):
    if not array:
        edit_message(
            call,
            "عذرًا، المصادر المطلوبة غير متوفرة حاليًا.\nاذا كان عندك مصادر لهذي المادة ارسلها لنا @Course_path_support ❌",
            build_nav_keyboard()
        )
        return True
    return False

def show_about(call, parts):
    about_text = (
    "للتسجيل في البوت والحصول على صلاحية الوصول للمحتوى، "
    "يلزم إدخال بريدك الجامعي فقط (لا يُقبل البريد الشخصي). "
    "سيتم إرسال رمز التحقق إلى بريدك الإلكتروني.\n\n"
    "⚠️ ملاحظة: في بعض الأحيان قد يصل رمز التحقق إلى البريد غير الهام (Spam).\n\n"
    "في حال واجهتك أي مشكلة، يرجى التواصل مع الدعم الفني عبر:\n"
    "@Course_path_support"
    )

    bot.send_message(call.message.chat.id, about_text, reply_markup=build_login_keyboard())

def show_back(call, parts):
    user_id = call.from_user.id
    stack = user_history.get(user_id, [])

    if not stack:
        edit_message(call, HOME_TEXT, build_main_menu_keyboard())
        return

    current = stack.pop() if stack else None

    while stack and stack[-1] == current:
        stack.pop()

    if not stack:
        edit_message(call, HOME_TEXT, build_main_menu_keyboard())
        return

    prev_data = stack[-1]
    route(call, prev_data)


def show_home(call, parts):
    user_history.pop(call.from_user.id, None)
    edit_message(call, HOME_TEXT, build_main_menu_keyboard())


def show_terms(call, parts):
    major_code = parts[1]
    terms = get_terms_for_major(major_code)
    if cheack_itsEmpty(call, terms):
        return
    kb = build_terms_keyboard(terms, major_code)
    edit_message(call, f"المستويات لتخصص {MAJOR_NAME[major_code]}:", kb)


def show_courses(call, parts):
    major_code, term = parts[1], parts[2]
    courses = get_courses_for_major_term(major_code, term)
    if cheack_itsEmpty(call, courses):
        return
    kb = build_courses_keyboard(courses)
    edit_message(call, f"المواد لتخصص {MAJOR_NAME[major_code]} المستوى {term}:", kb)


def show_sections_for_course(call, parts):
    course_id = parts[1]
    course_name, course_code = course_id.split("-", 1)

    sections = get_sections_for_course(course_name, course_code)
    if cheack_itsEmpty(call, sections):
        return
    kb = build_sections_keyboard(sections, course_name, course_code)
    edit_message(call, f"اقسام مادة  {course_name}-{course_code}  ({get_course_title(course_name, course_code)}):", kb)


def show_section(call, parts):
    course_id = parts[1]
    section = parts[2]

    nav = build_nav_keyboard()

    if section == "info":
        info = get_info_text(course_id)
        edit_message(call, f"معلومات مادة {course_id} ({get_course_title(course_id)}):\n\n{info}", nav)

    elif section == "sources":
        sources = get_sources_text(course_id)
        edit_message(call, f"مصادر مادة  {course_id} ({get_course_title(course_id)}):\n\n{sources}", nav)

    elif section == "slides":
        slide_types = get_slide_types(course_id)
        if cheack_itsEmpty(call, slide_types):
            return
        kb = build_slide_types_keyboard(course_id, slide_types)
        edit_message(call, f"شباتر مادة  {course_id} ({get_course_title(course_id)}):", kb)

    elif section == "old_exams":
        exam_types = get_exam_types(course_id)
        if cheack_itsEmpty(call, exam_types):
            return
        kb = build_exam_types_keyboard(course_id, exam_types)
        edit_message(call, f"الاختبارات لمادة {course_id} ({get_course_title(course_id)}):", kb)

    else:
        edit_message(call, "قسم غير معروف 🤔", nav)


def show_chapters_for_slide(call, parts):
    course_id = parts[1]
    slide_type = parts[2]

    chapters = get_chapters_for_slide(course_id, slide_type)
    kb = build_chapters_keyboard(course_id, slide_type, chapters)
    
    edit_message(call, f"{slide_type} for {course_id} ({get_course_title(course_id)}):", kb)


def show_chapter_file(call, parts):

    course_id = parts[1]
    slide_type = parts[2]
    chapter_title = parts[3]

    file_path = get_slide_file_path(course_id, slide_type, chapter_title)

    if not file_path:
        edit_message(call, "لا يوجد ملف متاح", build_nav_keyboard())
        return

    ok = send_document_file(call, file_path)
    if not ok:
        return

    edit_message(call, f"تم إرسال ملف لـ {course_id} ({chapter_title}) ✅", build_nav_keyboard())

def send_all_chapters(call, parts):
    course_id = parts[1]
    slide_type = parts[2]

    pathSlides = Path(f"DataBase/Courses/{course_id}/Slides/{slide_type}")

    for file_path in pathSlides.iterdir():
        if file_path.is_file():
            ok = send_document_file(call, file_path)
            if not ok:
                return
    send_message(call, f"تم إرسال جميع الملفات لمادة {course_id} ✅", build_nav_keyboard())




def show_exams_for_course(call, parts):
    course_id = parts[1]
    exam_type = parts[2]

    exams_titles = get_exams_titles(course_id, exam_type)
    kb = build_exams_keyboard(course_id, exam_type, exams_titles)
    edit_message(call, f"{exam_type} for {course_id}:", kb)


def show_exam_file(call, parts):
    course_id = parts[1]
    exam_type = parts[2]
    exam_title = parts[3]

    file_path = get_exam_file_path(course_id, exam_type, exam_title)

    if not file_path:
        edit_message(call, "لا يوجد ملف متاح", build_nav_keyboard())
        return

    ok = send_document_file(call, file_path)
    if not ok:
        return

    edit_message(call, f"تم إرسال ملف لـ {course_id} ({exam_title}) ✅", build_nav_keyboard())


def course_exists(course_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM major_Terms WHERE course_id = ? LIMIT 1",
            (course_code,)
        )
        row = cursor.fetchone()
        conn.close()
    return row is not None


def serarch_major(call, parts):
    user_id = call.from_user.id
    waiting_search[user_id] = True
    bot.send_message(call.message.chat.id, "الرجاء ارسال اسم المقرر الذي تريد البحث عنه (مثال: CPCS-204):")


def show_help(call, parts):
    help_command(call.message)

# =========================================================
# TOTP
# =========================================================
def start_verify_button(call, parts):
    user_id = call.from_user.id

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

    if row and row[0] == 1:
        bot.send_message(call.message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
        return

    msg = bot.send_message(call.message.chat.id, "أرسل ايميلك الجامعي للتحقق:")
    bot.register_next_step_handler(msg, ask_email)

# =========================================================


# ==========================================================
# ACTIONS + Route
# ==========================================================
ACTIONS = {
    "BACK": show_back,
    "HOME": show_home,
    "MAJOR": show_terms,
    "TERM": show_courses,
    "COURSE": show_sections_for_course,
    "SECTION": show_section,
    "SLIDES": show_chapters_for_slide,
    "CHAPTER": show_chapter_file,
    "SEND_ALL_CHAPTERS" : send_all_chapters,
    "EXAM": show_exams_for_course,
    "GETEXAM": show_exam_file,
    "SEARCH": serarch_major,
    "HELP": show_help,
    "LOGIN": start_verify_button,
    "ABOUT": show_about
}

def route(call, callback_data):
    parts = callback_data.split("|")
    action = parts[0]

    handler = ACTIONS.get(action)
    if not handler:
        edit_message(call, "زر غير معروف 🤔", build_main_menu_keyboard())
        return

    return handler(call, parts)

# ==========================================================
# Verified
# ==========================================================
def ask_email(message):
    textmsg = message.text
    if textmsg.startswith("/start") or textmsg.startswith("/help"):
        return

    user_id = message.from_user.id
    email = message.text

    if not TOTP.check_Email(email):
        msg = bot.send_message(message.chat.id, "الرجاء ارسال ايميلك الجامعي بشكل صحيح (مثال: xxxxx@stu.kau.edu.sa")
        bot.register_next_step_handler(msg, ask_email)
        return

    if TOTP.is_email_used(email):
        msg = bot.send_message(message.chat.id, "هذا الإيميل مستخدم مسبقاً ادخل ايميل غير مستخدم")
        bot.register_next_step_handler(msg, ask_email)
        return

    otp = TOTP.create_otp(user_id, email)
    TOTP.TOTP_Send(email, otp)
    msg = bot.send_message(message.chat.id, " تم إرسال كود التحقق الرجاء ادخاله خلال 3 دقايق")
    bot.register_next_step_handler(msg, verify)

def verify(message):
    user_id = message.from_user.id
    username = message.from_user.username
    if not username:
        username = "Mohaan"
    try:
        user_input = int(message.text)
    except ValueError:
        msg = bot.send_message(message.chat.id, "الرجاء ادخال كود التحقق من ارقام فقط")
        bot.register_next_step_handler(msg, verify)
        return

    ok, msg_text = TOTP.verify_otp(user_id, user_input)

    if ok:
        email = TOTP.otp_storage.get(user_id, {}).get("email", None)
        logger.info("Verify -> userID= %s || Username= %s || email= %s", message.from_user.id, message.from_user.username, email)
        if email:
            add_or_verify_user(user_id, username , email, verified=True)
            del TOTP.otp_storage[user_id]
            bot.send_message(
                message.chat.id,
                "تم تسجيل دخولك بنجاح",
                reply_markup= build_main_menu_keyboard()
            )

    else:
        msg = bot.send_message(message.chat.id, "أدخل الكود الصحيح:")
        bot.register_next_step_handler(msg, verify)

def add_or_verify_user(user_id, username , email, verified=False):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, email, verified)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET verified=excluded.verified
        """, (user_id, username, email, int(verified)))
        conn.commit()
        conn.close()


# ==========================================================
# Handlers (Telegram)
# ==========================================================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone() is not None

        if not exists:
            conn.close()
            bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())
            return

        cursor.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

    if row and row[0] == 1:
        bot.send_message(message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "للمساعدة، يرجى مراسلة الدعم الفني على @Course_path_support")


ADMIN_IDS = {1401478668, 810634477}
@bot.message_handler(func=lambda message: message.text and message.text.startswith("!SQL"))
def handle_sql_command(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية تستخدم هذا الأمر")
        return

    sql_text = message.text[len("!SQL"):].strip()

    if not sql_text:
        bot.reply_to(message, "اكتب استعلام SQL بعد !SQL")
        return

    success, result = execute_sql_query(sql_text)

    logger.info(
        "SQL command by -> userID=%s || Username=%s || SQL=%s",
        user_id,
        username,
        sql_text
    )

    if success:
        if sql_text.lower().startswith("select"):
            if not result:
                bot.reply_to(message, "تم التنفيذ، لكن ما فيه نتائج")
                return

            output_lines = []
            for row in result:
                output_lines.append(str(row))

            output_text = "\n".join(output_lines)

            if len(output_text) > 4000:
                output_text = output_text[:4000] + "\n...\nالنتيجة طويلة وتم قصها"

            bot.reply_to(message, f"تم تنفيذ الاستعلام ✅\n\n{output_text}")

        else:
            bot.reply_to(message, f"تم تنفيذ العملية ✅\nعدد الصفوف المتأثرة: {result}")

    else:
        logger.error(
            "SQL error by -> userID=%s || Username=%s || Error=%s",
            user_id,
            username,
            result
        )
        bot.reply_to(message, f"صار خطأ ❌\n{result}")
        

@bot.message_handler(func=lambda message: message.text and message.text.startswith("!Delete"))
def handle_delete(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    text = message.text
    parts = text.split()

    if len(parts) < 2:
        bot.reply_to(message, "اكتب الايدي بعد الأمر\n!Delete user_id")
        return

    delete_user_id = parts[1]

    logger.info(
        "Delete by -> userID=%s || Username=%s || UserDeleted=%s",
        user_id,
        message.from_user.username,
        delete_user_id
    )

    isDeleted = delete_user(delete_user_id)

    if isDeleted:
        bot.reply_to(message, f"تم حذف المستخدم {delete_user_id} ✅")
    else:
        bot.reply_to(message, "المستخدم غير موجود")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("!Sync"))
def handle_sql_sync(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    logger.info(
        "Sync by -> userID=%s || Username=%s",
        user_id,
        message.from_user.username
    )

    try:
        start_sync()
        bot.send_message(message.chat.id, "تم مزامنة البيانات ✅")
    except Exception as error:
        logger.error(
            "Sync error -> userID=%s || Username=%s || Error=%s",
            user_id,
            message.from_user.username,
            error
        )
        bot.send_message(message.chat.id, f"صار خطأ أثناء المزامنة ❌\n{error}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("!output"))
def send_output_file(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    logger.info(
        "Output requested by -> userID=%s || Username=%s",
        user_id,
        message.from_user.username
    )

    try:
        with open("outputBot.txt", "rb") as file:
            bot.send_document(message.chat.id, file)
    except Exception as error:
        logger.error(
            "Output send error -> userID=%s || Username=%s || Error=%s",
            user_id,
            message.from_user.username,
            error
        )
        bot.send_message(message.chat.id, f"صار خطأ أثناء إرسال الملف ❌\n{error}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if not waiting_search.get(user_id, False):
        return

    query = message.text.strip().upper()

    if not re.match(r"^[A-Z]+-\d{3}$", query):
        bot.send_message(message.chat.id, "صيغة غير صحيحة! الرجاء ارسال اسم المقرر بصيغة مثل: CPCS-204")
        return

    waiting_search[user_id] = False

    if not course_exists(query):
        print(query)
        bot.send_message(message.chat.id, f"❌ المادة {query} غير موجودة في قاعدة البيانات")
        return

    course_name, course_code = query.split("-", 1)
    sections = get_sections_for_course(course_name, course_code)
    kb = build_sections_keyboard(sections, course_name, course_code)

    bot.send_message(message.chat.id, f"Sections for {course_name}-{course_code}:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def on_callback(call):
    try:
        logger.info("Callback: [%s] -> userID= %s || Username= %s", call.data, call.from_user.id, call.from_user.username)

        if not (call.data.startswith("BACK") or call.data.startswith("HOME")):
            push_history(call.from_user.id, call.data)

        route(call, call.data)

    finally:
        try:
            bot.answer_callback_query(call.id)
        except:
            pass


# ==========================================================
# تشغيل البوت
# ==========================================================
try:
    start_sync()
    print("Sync is completed... ✅")
except:
    print("Sync Error... ❌")

print("Bot is running... ✅")
bot.infinity_polling()