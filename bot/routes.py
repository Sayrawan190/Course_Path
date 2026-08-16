from bot.keyboards import build_main_menu_keyboard
from bot.messaging import edit_message
from bot.handlers.auth import start_verify_button
from bot.handlers.catalog import (
    show_courses,
    show_exams_for_course,
    show_chapters_for_slide,
    show_section,
    show_sections_for_course,
    show_terms,
)
from bot.handlers.files import send_all_chapters, send_all_exams, show_chapter_file, show_exam_file
from bot.handlers.navigation import show_about, show_back, show_help, show_home

ACTIONS = {
    "BACK": show_back,
    "HOME": show_home,
    "MAJOR": show_terms,
    "TERM": show_courses,
    "COURSE": show_sections_for_course,
    "SECTION": show_section,
    "SLIDES": show_chapters_for_slide,
    "CHAPTER": show_chapter_file,
    "SEND_ALL_CHAPTERS": send_all_chapters,
    "SEND_ALL_EXAMS": send_all_exams,
    "EXAM": show_exams_for_course,
    "GETEXAM": show_exam_file,
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
