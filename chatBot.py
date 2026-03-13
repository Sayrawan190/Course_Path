import telebot
from telebot import types
import logging
import sqlite3
import threading
import sys
import re
from DB_settings.syncExcilToSQL import start_sync
import TOTP
from pathlib import Path
from telebot.types import BotCommand

# ==========================================================
# تسجيل اللوق (Logs)
# ==========================================================
# الهدف:
# - نطبع INFO/ERROR في التيرمنال عشان تعرف وش يصير أثناء التشغيل.
# - force=True مهم: لو مكتبة ثانية كانت مفعّلة logging قبل، هذا يجبر الإعداد الجديد.
# - StreamHandler(sys.stdout): يطلع اللوق في Terminal/Output حق VS Code.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("FCIT_BOT")  # اسم اللوقر (بس للتنظيم)


# ==========================================================
# Database (SQLite)
# ==========================================================
# cunn: اتصال قاعدة البيانات
# cur : المؤشر (cursor) لتنفيذ الاستعلامات
# db_lock: قفل عشان التزامن (telebot يستخدم threads، فبدون lock ممكن يصير تضارب)
cunn = sqlite3.connect(r"DataBase/FCIT_bot.db", check_same_thread=False)
cur = cunn.cursor()
db_lock = threading.Lock()

# ==========================================================
# History + State
# ==========================================================
# user_history:
# - ستاك (stack) لكل مستخدم عشان زر الرجوع ↩️
# - نخزن callback_data اللي ضغطه المستخدم بالترتيب
user_history = {}  # {user_id: [callback_data1, callback_data2, ...]}

# waiting_search:
# - حالة (state) للمستخدم: هل هو الآن في وضع "بحث يدوي"؟
# - إذا True: أي رسالة يرسلها المستخدم نعتبرها استعلام بحث
waiting_search = {}  # {user_id: True/False}
waiting_email = {}  # {user_id: True/False}


def push_history(user_id, data):
    """
    يحفظ آخر صفحة ضغطها المستخدم (callback_data) في الستاك.
    يستخدمها زر الرجوع عشان يرجع للصفحة السابقة.
    """
    user_history.setdefault(user_id, []).append(data)


def pop_history(user_id):
    """
    يشيل الصفحة الحالية من الستاك ويرجع الستاك بعد الحذف.
    ملاحظة: زر الرجوع يشيل "الحالية" ثم يرجع "اللي قبلها".
    """
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

TOKEN = "8554120109:AAHZttTkOfttgX1plyHCasFtno3ZV_geDVw"
bot = telebot.TeleBot(TOKEN)

bot.set_my_commands([
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Help and guide"),
])

# ==========================================================
# ثوابت النصوص/المسميات
# ==========================================================
# MAJOR_NAME: أسماء التخصصات المعروضة في القائمة الرئيسية
MAJOR_NAME = {
    "CS": "علوم حاسب 💡",
    "IT": "تقنية معلومات 💻",
    "IS": "نظم معلومات 💸",
    "FD": "التحضيري 👶🏻"
}

# HOME_TEXT: رسالة القائمة الرئيسية
HOME_TEXT ="مرحباً بك مجدداً\n" + "القائمة الرئيسية🏠\nاختر تخصصك من القائمة:"


# ==========================================================
# Helpers (دوال مساعدة للتنظيم وتقليل التكرار)
# ==========================================================
def cb(*parts):
    """
    يبني callback_data بشكل موحد.
    مثال: cb("TERM","CS","1") => "TERM|CS|1"
    الفائدة: يمنع أخطاء الكتابة اليدوية ويخلي parsing ثابت.
    """
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


def build_nav_keyboard():
    """
    كيبورد موحد للصفحات (رجوع + الرئيسية).
    أي صفحة داخلية غالبًا تحتاجه.
    """
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("↩️ رجوع", callback_data=cb("BACK")),
        types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data=cb("HOME")),
    )
    return kb


def build_keyboard_from_buttons(buttons, row_width=2, add_nav=True):
    """
    دالة عامة تبني كيبورد من قائمة أزرار جاهزة.
    buttons: قائمة InlineKeyboardButton
    row_width: عدد الأزرار بالصف الواحد
    add_nav: هل نضيف رجوع + الرئيسية بالآخر؟
    """
    kb = types.InlineKeyboardMarkup(row_width=row_width)

    # نضيف كل الأزرار مرة وحدة
    if buttons:
        kb.add(*buttons)

    # نضيف شريط التنقل تحت
    if add_nav:
        kb.add(
            types.InlineKeyboardButton("رجوع ↩️", callback_data=cb("BACK")),
            types.InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data=cb("HOME")),
        )
    return kb


def send_document_file(call, file_path):
    """
    إرسال ملف (PDF/غيره) للمستخدم.

    ليه تمرير call بدل chat_id؟
    - عشان إذا صار خطأ نقدر نستخدم نفس call لعرض رسالة + زر دعم/مساعدة.
    - وأهم شيء: ما نبني Message وهمي (يسبب Exceptions).

    يرجع:
    - True إذا الإرسال نجح
    - False إذا فشل (ملف غير موجود أو خطأ ثاني)
    """
    try:
        # ملاحظة: file_path لازم يكون صحيح وموجود فعليًا في جهاز السيرفر/المشروع
        with open(file_path, "rb") as f:
            bot.send_document(call.message.chat.id, f)
        return True

    except FileNotFoundError as e:
        # هذا يعني المسار مخزن في DB لكن الملف فعليًا مو موجود في الفولدر
        logger.error("File Not Found Error: %s", e)
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. الرجاء التواصل مع الدعم الفني.", build_nav_keyboard())
        # نرسل للمستخدم مساعدة بدل ما يطيح البوت
        show_help(call, None)
        return False

    except Exception as e:
        # أي خطأ ثاني (صلاحيات/شبكة/مشكلة في إرسال تليجرام)
        logger.error("Error sending file: %s", e)
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. الرجاء التواصل مع الدعم الفني.", build_nav_keyboard())
        show_help(call, None)
        return False


# ==========================================================
# Main Menu (القائمة الرئيسية)
# ==========================================================
def build_login_keyboard():
    """
    كيبورد تسجيل الدخول (للمستخدمين غير الموثقين).
    - زر "تسجيل الدخول" يربط على ACTIONS["LOGIN"] (راجع تحت).
    """
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🔐 تسجيل الدخول", callback_data=cb("LOGIN")),
        types.InlineKeyboardButton("🤖 عن البوت", callback_data=cb("ABOUT"))
    )
    return kb

def build_main_menu_keyboard():
    """
    تبني الكيبورد الرئيسي.
    تنبيه صيانة:
    - لاحظ إن زر "بحث يدوي" و "الدعم الفني" هنا callback_data حقها مو متوافق غالبًا (راجع تحت).
    - لو تبغى: "بحث يدوي" => cb("SEARCH")
    - و "الدعم الفني" => cb("HELP")
    """
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(MAJOR_NAME["CS"], callback_data=cb("MAJOR", "CS")),
        types.InlineKeyboardButton(MAJOR_NAME["IT"], callback_data=cb("MAJOR", "IT")),
        types.InlineKeyboardButton(MAJOR_NAME["IS"], callback_data=cb("MAJOR", "IS")),
        types.InlineKeyboardButton(MAJOR_NAME["FD"], callback_data=cb("MAJOR", "FD")),
    )
        # ⚠️ تنبيه: هنا في نسختك الحالية:
        # - "بحث يدوي" مربوط على MAJOR|FD
        # - "الدعم الفني" مربوط على SEARCH
        # إذا هذا مقصود عندك اتركه، إذا لا راجع التوجيه في ACTIONS.
    kb.row(
        types.InlineKeyboardButton("بحث يدوي🔎", callback_data=cb("SEARCH")),
        types.InlineKeyboardButton("مراسلة الدعم الفني👨🏻‍💻", callback_data=cb("HELP")),
    )
    return kb


# ==========================================================
# DB Queries (دوال قراءة من قاعدة البيانات فقط)
# ==========================================================
# مبدأ الصيانة هنا:
# - كل دالة ترجع بيانات خام (list/tuple)
# - بدون أي UI/Keyboard داخلها
def get_terms_for_major(major_code):
    """
    يرجع قائمة الترمات المتاحة لتخصص معيّن.
    من جدول: major_Terms
    """
    with db_lock:
        cur.execute("SELECT DISTINCT term FROM major_Terms WHERE major_code = ?", (major_code,))
        rows = cur.fetchall()
    return [row[0] for row in rows]


def get_courses_for_major_term(major_code, term):
    """
    يرجع قائمة course_id (مثل CPCS-204) لتخصص + ترم.
    """
    with db_lock:
        cur.execute(
            "SELECT DISTINCT course_id FROM major_Terms WHERE major_code = ? AND term = ?",
            (major_code, term)
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]

# ============================================================================================================
def get_course_title(*args):
    """
    يرجع course_title لمادة معينة.
    """
    if len(args) == 1:
        course_id = args[0]
        course_name, course_code = course_id.split("-", 1)
    elif len(args) == 2:
        course_name, course_code = args

    with db_lock:
        cur.execute(
            "SELECT DISTINCT course_title FROM courses WHERE course_name = ? AND course_code = ?",
            (course_name, course_code)
        )
        row = cur.fetchone()
    return row[0] if row else None

def get_sections_for_course(course_name, course_code):
    """
    يرجع الأقسام داخل المادة (section + title) بترتيب ord.
    جدول: courses
    مثال sections: info, sources, slides, old_exams ... حسب DB عندك.
    """
    with db_lock:
        cur.execute(
            "SELECT DISTINCT section, title FROM courses WHERE course_name = ? and course_code = ? ORDER BY ord",
            (course_name, course_code)
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_slide_types(course_id):
    """
    يرجع أنواع السلايدات داخل المادة (مثل: lab, lecture, summary ...).
    جدول: slides
    """
    with db_lock:
        cur.execute("SELECT DISTINCT slide_type, button_title FROM slides WHERE course_id = ?", (course_id,))
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_exam_types(course_id):
    """
    يرجع أنواع الاختبارات داخل المادة (مثل: mid, final, quizzes ...).
    جدول: exams
    """
    with db_lock:
        cur.execute("SELECT DISTINCT exam_type, button_title FROM exams WHERE course_id = ?", (course_id,))
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_chapters_for_slide(course_id, slide_type):
    """
    يرجع عناوين الشابتر/الملفات التابعة لـ slide_type.
    جدول: slides
    """
    with db_lock:
        cur.execute(
            "SELECT DISTINCT title FROM slides WHERE course_id = ? AND slide_type = ? ORDER BY ord",
            (course_id, slide_type)
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]


def get_exams_titles(course_id, exam_type):
    """
    يرجع عناوين ملفات الاختبارات لنوع معيّن.
    جدول: exams
    """
    with db_lock:
        cur.execute(
            "SELECT DISTINCT title FROM exams WHERE course_id = ? AND exam_type = ? ORDER BY ord",
            (course_id, exam_type)
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]


def get_info_text(course_id):
    """
    يرجع نص معلومات المادة من جدول info_sources.
    """
    with db_lock:
        cur.execute("SELECT info FROM info_sources WHERE course_id = ?", (course_id,))
        row = cur.fetchone()
    info = row[0] if row else "لا توجد معلومات متاحة حاليًا"
    info = info.replace("||", "\n")  # تحويل \n إلى سطر جديد حقيقي
    return info

def get_sources_text(course_id):
    """
    يرجع نص المصادر من جدول info_sources.
    """
    with db_lock:
        cur.execute("SELECT sources FROM info_sources WHERE course_id = ?", (course_id,))
        row = cur.fetchone()
    sources = row[0] if row else "لا توجد مصادر متاحة حاليًا"
    sources = sources.replace("||", "\n")  # تحويل \n إلى سطر جديد حقيقي
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
# Keyboards Builders (دوال بناء الكيبورد فقط)
# ==========================================================
# مبدأ الصيانة:
# - هذه الدوال تاخذ بيانات جاهزة (lists)
# - وتطلع InlineKeyboardMarkup
def build_terms_keyboard(terms, major_code):
    """
    كيبورد الترمات لتخصص معين.
    """
    buttons = [
        types.InlineKeyboardButton(f"الترم {term}️⃣", callback_data=cb("TERM", major_code, str(term)))
        for term in terms
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_courses_keyboard(courses):
    """
    كيبورد المواد داخل ترم (يعرض CPCS-204 مثلًا).
    """
    buttons = [
        types.InlineKeyboardButton(course, callback_data=cb("COURSE", course))
        for course in courses
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_sections_keyboard(sections, course_name, course_code):
    """
    كيبورد الأقسام داخل مادة:
    - sections: قائمة tuples (section_code, title)
    - callback_data: SECTION|courseName-courseCode|section
    """
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
    """
    كيبورد أنواع الاختبارات داخل المادة.
    """
    buttons = [
        types.InlineKeyboardButton(button_title, callback_data=cb("EXAM", course_id, et))
        for et, button_title in exam_types
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


def build_chapters_keyboard(course_id, slide_type, chapters):
    """
    كيبورد عناوين الشابتر/الملفات لسلايد معين.
    ملاحظة: row_width=4 عشان يطلع أكثر من زر في صف.
    """
    buttons = [
        types.InlineKeyboardButton(ch, callback_data=cb("CHAPTER", course_id, slide_type, ch))
        for ch in chapters
    ]
    return build_keyboard_from_buttons(buttons, row_width=4)


def build_exams_keyboard(course_id, exam_type, exams_titles):
    """
    كيبورد عناوين ملفات الاختبارات.
    callback_data: GETEXAM|course_id|exam_type|title
    """
    buttons = [
        types.InlineKeyboardButton(ex, callback_data=cb("GETEXAM", course_id, exam_type, ex))
        for ex in exams_titles
    ]
    return build_keyboard_from_buttons(buttons, row_width=2)


# ==========================================================
# Actions (Handlers) - دوال التنقل لكل callback
# ==========================================================
def cheack_itsEmpty(call, array):
    if not array:   # يعني العدد = 0
        edit_message(
            call,
            "عذرًا، المصادر المطلوبة غير متوفرة حاليًا.\nاذا كان عندك مصادر لهذي المادة ارسلها لنا @Course_path_support ❌",
            build_nav_keyboard()
        )
        return True    
    return False

def show_about(call, parts):
    """
    زر "عن البوت":
    - يعرض رسالة ثابتة عن البوت (يمكنك تعديلها حسب الحاجة).
    - يستخدم نفس كيبورد الرئيسية للسهولة.
    """
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
    """
    زر الرئيسية:
    - يمسح history للمستخدم
    - يعرض القائمة الرئيسية من جديد
    """
    user_history.pop(call.from_user.id, None)
    edit_message(call, HOME_TEXT, build_main_menu_keyboard())


def show_terms(call, parts):
    """
    بعد اختيار التخصص (MAJOR):
    - نجيب الترمات
    - نعرضها كأزرار
    """
    major_code = parts[1]
    terms = get_terms_for_major(major_code)
    if cheack_itsEmpty(call, terms):
        return
    kb = build_terms_keyboard(terms, major_code)
    edit_message(call, f"المستويات لتخصص {MAJOR_NAME[major_code]}:", kb)


def show_courses(call, parts):
    """
    بعد اختيار الترم (TERM):
    - نجيب المواد داخل الترم
    - نعرضها كأزرار
    """
    major_code, term = parts[1], parts[2]
    courses = get_courses_for_major_term(major_code, term)
    if cheack_itsEmpty(call, courses):
        return
    kb = build_courses_keyboard(courses)
    edit_message(call, f"المواد لتخصص {MAJOR_NAME[major_code]} المستوى {term}:", kb)


def show_sections_for_course(call, parts):
    """
    بعد اختيار مادة (COURSE):
    - parts[1] = course_id مثل CPCS-204
    - نفصلها إلى course_name + course_code
    - نعرض أقسام المادة
    """
    course_id = parts[1]
    course_name, course_code = course_id.split("-", 1)

    sections = get_sections_for_course(course_name, course_code)
    if cheack_itsEmpty(call, sections):
        return
    kb = build_sections_keyboard(sections, course_name, course_code)
    edit_message(call, f"اقسام مادة  {course_name}-{course_code}  ({get_course_title(course_name, course_code)}):", kb)


def show_section(call, parts):
    """
    داخل أقسام المادة (SECTION):
    - course_id: courseName-courseCode
    - section: info / sources / slides / old_exams
    """
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
        # إذا DB فيها section جديد وما أضفته هنا
        edit_message(call, "قسم غير معروف 🤔", nav)


def show_chapters_for_slide(call, parts):
    """
    بعد اختيار نوع السلايد (SLIDES):
    - نعرض قائمة الملفات/الشابترات
    """
    course_id = parts[1]
    slide_type = parts[2]

    chapters = get_chapters_for_slide(course_id, slide_type)
    kb = build_chapters_keyboard(course_id, slide_type, chapters)
    edit_message(call, f"{slide_type} for {course_id} ({get_course_title(course_id)}):", kb)


def show_chapter_file(call, parts):
    """
    بعد اختيار شابتر/ملف (CHAPTER):
    - نجيب file_path من DB
    - نرسل الملف
    """
    course_id = parts[1]
    slide_type = parts[2]
    chapter_title = parts[3]

    file_path = get_slide_file_path(course_id, slide_type, chapter_title)

    if not file_path:
        edit_message(call, "لا يوجد ملف متاح", build_nav_keyboard())
        return

    # إرسال الملف (يرجع True/False)
    ok = send_document_file(call, file_path)
    if not ok:
        # send_document_file يعرض help عند الفشل
        return

    edit_message(call, f"تم إرسال ملف لـ {course_id} ({chapter_title}) ✅", build_nav_keyboard())


def show_exams_for_course(call, parts):
    """
    بعد اختيار نوع اختبار (EXAM):
    - نعرض عناوين الملفات المتاحة
    """
    course_id = parts[1]
    exam_type = parts[2]

    exams_titles = get_exams_titles(course_id, exam_type)
    kb = build_exams_keyboard(course_id, exam_type, exams_titles)
    edit_message(call, f"{exam_type} for {course_id}:", kb)


def show_exam_file(call, parts):
    """
    بعد اختيار ملف اختبار (GETEXAM):
    - نجيب file_path
    - نرسل الملف
    """
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
    """
    فحص سريع: هل المادة موجودة في DB؟
    نستخدم SELECT 1 + LIMIT 1 عشان يكون سريع.
    """
    with db_lock:
        cur.execute(
            "SELECT 1 FROM major_Terms WHERE course_id = ? LIMIT 1",
            (course_code,)
        )
        row = cur.fetchone()
    return row is not None


def serarch_major(call, parts):
    """
    بداية البحث اليدوي:
    - نخلي المستخدم في وضع انتظار إدخال مادة
    - نطلب منه يرسل اسم المادة
    """
    user_id = call.from_user.id
    waiting_search[user_id] = True
    bot.send_message(call.message.chat.id, "الرجاء ارسال اسم المقرر الذي تريد البحث عنه (مثال: CPCS-204):")


def show_help(call, parts):
    """
    هذا handler للزر HELP (من الكيبورد).
    نعيد استخدام help_command عشان نرسل نفس رسالة /help.
    """
    help_command(call.message)

# =========================================================
#                 TOTP (التحقق عبر الايميل)

def start_verify_button(call, parts):
    user_id = call.from_user.id

    cur.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row and row[0] == 1:
        bot.send_message(call.message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
        return
   
    msg = bot.send_message(call.message.chat.id, "أرسل ايميلك الجامعي للتحقق:")
    bot.register_next_step_handler(msg, ask_email)

# =========================================================


# ==========================================================
# ACTIONS + Route
# ==========================================================
# ACTIONS: ماب يربط أول جزء من callback_data بالدالة المناسبة
ACTIONS = {
    "BACK": show_back,
    "HOME": show_home,
    "MAJOR": show_terms,
    "TERM": show_courses,
    "COURSE": show_sections_for_course,
    "SECTION": show_section,
    "SLIDES": show_chapters_for_slide,
    "CHAPTER": show_chapter_file,
    "EXAM": show_exams_for_course,
    "GETEXAM": show_exam_file,
    "SEARCH": serarch_major,
    "HELP": show_help,
    "LOGIN": start_verify_button,  # راجع TOTP.py
    "ABOUT": show_about   # راجع TOTP.py
}

def route(call, callback_data):
    """
    الراوتر:
    - يفك callback_data إلى أجزاء (split by |)
    - يحدد الأكشن (parts[0])
    - ينادي الدالة من ACTIONS
    """
    parts = callback_data.split("|")
    action = parts[0]

    handler = ACTIONS.get(action)
    if not handler:
        edit_message(call, "زر غير معروف 🤔", build_main_menu_keyboard())
        return

    return handler(call, parts)

# ==========================================================
#                   Verified (موثقين)
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
    conn = sqlite3.connect(r"DataBase/FCIT_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, email, verified)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET verified=excluded.verified
    """, (user_id, username, email, int(verified)))
    conn.commit()




# ==========================================================
# ==========================================================
# ==========================================================


# ==========================================================
# Handlers (Telegram)
# ==========================================================

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    exists = cur.fetchone() is not None
    if not exists:
        bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())
        return

    cur.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row and row[0] == 1:
        bot.send_message(message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "أهلاً! لتسجيل الدخول، اضغط على الزر أدناه.", reply_markup=build_login_keyboard())


@bot.message_handler(commands=['help'])
def help_command(message):
    """
    /help:
    - يرسل طريقة التواصل مع الدعم الفني
    ملاحظة: هذه دالة message_handler (تحتاج message حقيقي).
    """
    bot.send_message(message.chat.id, "للمساعدة، يرجى مراسلة الدعم الفني على @Course_path_support")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    """
    هذا handler لأي رسالة نصية.
    نستخدمه فقط للبحث اليدوي:
    - إذا المستخدم waiting_search=True => نقرأ رسالته كاسم مادة.
    - غير كذا: نتجاهل الرسالة (أو تقدر لاحقًا تضيف وظائف ثانية).
    """
    user_id = message.from_user.id

    # إذا المستخدم مو في وضع بحث، تجاهل
    if not waiting_search.get(user_id, False):
        return


    query = message.text.strip().upper()

    # تحقق صيغة المادة (مثال: CPCS-204)
    if not re.match(r"^[A-Z]+-\d{3}$", query):
        bot.send_message(message.chat.id, "صيغة غير صحيحة! الرجاء ارسال اسم المقرر بصيغة مثل: CPCS-204")
        return

    waiting_search[user_id] = False

    # تحقق هل المادة موجودة في DB
    if not course_exists(query):
        print(query)
        bot.send_message(message.chat.id, f"❌ المادة {query} غير موجودة في قاعدة البيانات")
        return


    # هنا ما عندنا call، لذلك نرسل رسالة جديدة بدل edit_message
    course_name, course_code = query.split("-", 1)
    sections = get_sections_for_course(course_name, course_code)
    kb = build_sections_keyboard(sections, course_name, course_code)

    bot.send_message(message.chat.id, f"Sections for {course_name}-{course_code}:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def on_callback(call):
    """
    أي ضغط زر Inline:
    - نسجل اللوق (مفيد للصيانة)
    - نخزن history (إلا BACK/HOME)
    - ننادي route
    - finally: نعمل answer_callback_query عشان تليجرام ما يعتبر الطلب معلق
    """
    try:
        logger.info("Callback: [%s] -> userID= %s || Username= %s", call.data, call.from_user.id, call.from_user.username)

        # خزّن الصفحة (إلا إذا BACK/HOME)
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
# bot.polling():
# - يبدأ يسمع للرسائل والـ callbacks
# ملاحظة: إذا صار crash متكرر، راجع آخر Traceback بالترتيب.

try:
    start_sync()
    print("Sync is completed... ✅")
except:
    print("Sync Error... ❌")

print("Bot is running... ✅")
bot.infinity_polling()
# sfsdssdfsdsdfdsd