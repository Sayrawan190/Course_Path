import re

from bot.instance import bot
from bot.keyboards import build_sections_keyboard
from db.queries import course_exists, get_sections_for_course

COURSE_CODE_RE = re.compile(r"^([A-Z]+)[\s-]*(\d{3})$")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    raw = message.text.strip().upper()

    match = COURSE_CODE_RE.match(raw)
    if not match:
        # نص ما له علاقة برمز مادة (مثل CPCS-204 / CPCS 204 / CPCS204) → تجاهله
        return

    query = f"{match.group(1)}-{match.group(2)}"

    if not course_exists(query):
        bot.send_message(
            message.chat.id,
            f"❌ المادة {query} غير موجودة عندنا.\n"
            "إذا عندك مصادر لهذي المادة ارسلها لنا @Course_path_support حتى يتم إضافتها."
        )
        return

    course_name, course_code = query.split("-", 1)
    sections = get_sections_for_course(course_name, course_code)
    kb = build_sections_keyboard(sections, course_name, course_code)

    bot.send_message(message.chat.id, f"Sections for {course_name}-{course_code}:", reply_markup=kb)
