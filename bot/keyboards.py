from telebot import types

from config import MAJOR_NAME


def cb(*parts):
    return "|".join(parts)


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
        types.InlineKeyboardButton("مراسلة الدعم الفني👨🏻‍💻", callback_data=cb("HELP")),
    )
    return kb


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
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.add(*buttons)
    kb.row(
        types.InlineKeyboardButton("Send all fils 📂", callback_data=cb("SEND_ALL_EXAMS", course_id, exam_type))
    )
    kb.row(
        types.InlineKeyboardButton("رجوع ↩️", callback_data=cb("BACK")),
        types.InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data=cb("HOME")),
    )
    return kb
