from config import MAJOR_NAME
from bot.errors import cheack_itsEmpty, safe_callback
from bot.keyboards import (
    build_chapters_keyboard,
    build_courses_keyboard,
    build_exam_types_keyboard,
    build_exams_keyboard,
    build_nav_keyboard,
    build_sections_keyboard,
    build_slide_types_keyboard,
    build_terms_keyboard,
)
from bot.messaging import edit_message
from db.queries import (
    get_chapters_for_slide,
    get_course_title,
    get_courses_for_major_term,
    get_exam_types,
    get_exams_titles,
    get_info_text,
    get_sections_for_course,
    get_slide_types,
    get_sources_text,
    get_terms_for_major,
)


@safe_callback
def show_terms(call, parts):
    major_code = parts[1]
    terms = get_terms_for_major(major_code)
    if cheack_itsEmpty(call, terms):
        return
    kb = build_terms_keyboard(terms, major_code)
    edit_message(call, f"المستويات لتخصص {MAJOR_NAME[major_code]}:", kb)


@safe_callback
def show_courses(call, parts):
    major_code, term = parts[1], parts[2]
    courses = get_courses_for_major_term(major_code, term)
    if cheack_itsEmpty(call, courses):
        return
    kb = build_courses_keyboard(courses)
    edit_message(call, f"المواد لتخصص {MAJOR_NAME[major_code]} المستوى {term}:", kb)


@safe_callback
def show_sections_for_course(call, parts):
    course_id = parts[1]
    course_name, course_code = course_id.split("-", 1)

    sections = get_sections_for_course(course_name, course_code)
    if cheack_itsEmpty(call, sections):
        return
    kb = build_sections_keyboard(sections, course_name, course_code)
    edit_message(call, f"اقسام مادة  {course_name}-{course_code}  ({get_course_title(course_name, course_code)}):", kb)


@safe_callback
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


@safe_callback
def show_chapters_for_slide(call, parts):
    course_id = parts[1]
    slide_type = parts[2]

    chapters = get_chapters_for_slide(course_id, slide_type)
    if cheack_itsEmpty(call, chapters):
        return
    kb = build_chapters_keyboard(course_id, slide_type, chapters)
    edit_message(call, f"{slide_type} for {course_id} ({get_course_title(course_id)}):", kb)


@safe_callback
def show_exams_for_course(call, parts):
    course_id = parts[1]
    exam_type = parts[2]

    exams_titles = get_exams_titles(course_id, exam_type)
    if cheack_itsEmpty(call, exams_titles):
        return
    kb = build_exams_keyboard(course_id, exam_type, exams_titles)
    edit_message(call, f"{exam_type} for {course_id}:", kb)
