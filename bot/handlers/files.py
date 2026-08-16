from pathlib import Path

from bot.documents import send_document_file
from bot.errors import notify_admins_error, safe_callback
from bot.keyboards import build_nav_keyboard
from bot.messaging import edit_message, send_message
from db.file_paths import get_exam_file_path, get_slide_file_path


@safe_callback
def show_chapter_file(call, parts):
    course_id = parts[1]
    slide_type = parts[2]
    chapter_title = parts[3]

    file_path = get_slide_file_path(course_id, slide_type, chapter_title)

    if not file_path:
        notify_admins_error(
            "show_chapter_file",
            FileNotFoundError("Slide file not found"),
            f"course_id={course_id} | slide_type={slide_type} | title={chapter_title}",
            call
        )
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    ok = send_document_file(call, file_path)
    if not ok:
        return

    edit_message(call, f"تم إرسال ملف لـ {course_id} ({chapter_title}) ✅", build_nav_keyboard())


@safe_callback
def send_all_chapters(call, parts):
    course_id = parts[1]
    slide_type = parts[2]

    pathSlides = Path(f"DataBase/Courses/{course_id}/Slides/{slide_type}")

    if not pathSlides.exists() or not pathSlides.is_dir():
        notify_admins_error(
            "send_all_chapters",
            FileNotFoundError("Slides folder not found"),
            f"course_id={course_id} | slide_type={slide_type} | path={pathSlides}",
            call
        )
        edit_message(call, "عذرًا، مجلد الملفات غير متوفر. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    files = [f for f in pathSlides.iterdir() if f.is_file()]
    if not files:
        notify_admins_error(
            "send_all_chapters",
            FileNotFoundError("Slides folder is empty"),
            f"course_id={course_id} | slide_type={slide_type} | path={pathSlides}",
            call
        )
        edit_message(call, "عذرًا، لا توجد ملفات في هذا المجلد. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    for file_path in files:
        ok = send_document_file(call, file_path)
        if not ok:
            return

    send_message(call, f"تم إرسال جميع الملفات لمادة {course_id} ✅", build_nav_keyboard())


@safe_callback
def show_exam_file(call, parts):
    course_id = parts[1]
    exam_type = parts[2]
    exam_title = parts[3]

    file_path = get_exam_file_path(course_id, exam_type, exam_title)

    if not file_path:
        notify_admins_error(
            "show_exam_file",
            FileNotFoundError("Exam file not found"),
            f"course_id={course_id} | exam_type={exam_type} | title={exam_title}",
            call
        )
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    ok = send_document_file(call, file_path)
    if not ok:
        return

    edit_message(call, f"تم إرسال ملف لـ {course_id} ({exam_title}) ✅", build_nav_keyboard())


@safe_callback
def send_all_exams(call, parts):
    course_id = parts[1]
    exam_type = parts[2]

    pathExams = Path(f"DataBase/Courses/{course_id}/Exams/{exam_type}")

    if not pathExams.exists() or not pathExams.is_dir():
        notify_admins_error(
            "send_all_exams",
            FileNotFoundError("Exams folder not found"),
            f"course_id={course_id} | exam_type={exam_type} | path={pathExams}",
            call
        )
        edit_message(call, "عذرًا، مجلد الاختبارات غير متوفر. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    files = [f for f in pathExams.iterdir() if f.is_file()]
    if not files:
        notify_admins_error(
            "send_all_exams",
            FileNotFoundError("Exams folder is empty"),
            f"course_id={course_id} | exam_type={exam_type} | path={pathExams}",
            call
        )
        edit_message(call, "عذرًا، لا توجد ملفات في هذا المجلد. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return

    for file_path in files:
        ok = send_document_file(call, file_path)
        if not ok:
            return

    send_message(call, f"تم إرسال جميع الملفات لمادة {course_id} ✅", build_nav_keyboard())
