import csv
from pathlib import Path

from config import (
    ADMIN_IDS,
    ALLOWED_EXTENSIONS,
    EXAM_TYPE_TITLES,
    EXAMS_CSV_PATH,
    FILE_TYPE_ALIASES,
    SLIDE_TYPE_TITLES,
    SLIDES_CSV_PATH,
)
from logging_config import logger
from bot.errors import notify_admins_error
from bot.instance import bot
from db.connection import db_lock, get_db_connection
from db.queries import course_exists, get_next_ord


def append_row_to_csv(csv_path, row_data, fieldnames):
    file_exists = Path(csv_path).exists()

    with open(csv_path, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)


def remove_row_from_csv(csv_path, match_course_id, match_type, match_title, type_column):
    if not Path(csv_path).exists():
        return

    rows = []

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames

        for row in reader:
            if not (
                row["course_id"] == match_course_id
                and row[type_column] == match_type
                and row["title"] == match_title
            ):
                rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_telegram_document(message, target_folder, new_file_name):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    original_extension = Path(message.document.file_name).suffix.lower()

    if original_extension not in ALLOWED_EXTENSIONS:
        return None, "نوع الملف غير مسموح"

    target_folder.mkdir(parents=True, exist_ok=True)

    final_path = target_folder / f"{new_file_name}{original_extension}"

    with open(final_path, "wb") as file:
        file.write(downloaded_file)

    return final_path, None


@bot.message_handler(content_types=["document"])
def handle_add_file(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    caption = message.caption

    if not caption or not caption.startswith("!Add"):
        return

    parts = caption.split()

    if len(parts) < 5:
        bot.reply_to(
            message,
            "الصيغة غلط.\n\n"
            "استخدم:\n"
            "!Add COURSE SECTION TYPE FILE_NAME\n\n"
            "مثال للسلايدات:\n"
            "!Add CPCS-204 slides lecture CPCS204_CH09\n\n"
            "مثال للاختبارات:\n"
            "!Add CPCS-204 exam midterm CPCS204_Midterm_2024"
        )
        return

    course_id = parts[1].upper()
    section = parts[2].lower().capitalize()
    file_type = FILE_TYPE_ALIASES.get(parts[3].lower(), parts[3].lower()).lower()
    file_title = parts[4]

    if section not in ["Slides", "Exams"]:
        bot.reply_to(message, "القسم لازم يكون slides أو exam")
        return

    if not course_exists(course_id):
        bot.reply_to(message, f"المادة {course_id} غير موجودة في قاعدة البيانات")
        return

    try:
        if section == "Slides":
            target_folder = Path(f"DataBase/Courses/{course_id}/Slides/{file_type}")
            final_file_name = f"{course_id}_{file_title}"
            saved_path, error = save_telegram_document(message, target_folder, final_file_name)

            if error:
                bot.reply_to(message, error)
                return

            button_title = SLIDE_TYPE_TITLES.get(file_type, file_type)
            next_ord = get_next_ord("slides", course_id, "slide_type", file_type)

            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO slides
                    (course_id, slide_type, button_title, title, ord)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (course_id, file_type, button_title, file_title, next_ord)
                )
                conn.commit()
                conn.close()

            append_row_to_csv(
                SLIDES_CSV_PATH,
                {"course_id": course_id, "slide_type": file_type, "button_title": button_title, "title": file_title, "ord": next_ord},
                ["course_id", "slide_type", "button_title", "title", "ord"]
            )

        else:
            target_folder = Path(f"DataBase/Courses/{course_id}/Exams/{file_type}")
            final_file_name = f"{course_id}_{file_title}"
            saved_path, error = save_telegram_document(message, target_folder, final_file_name)

            if error:
                bot.reply_to(message, error)
                return

            button_title = EXAM_TYPE_TITLES.get(file_type, file_type)
            next_ord = get_next_ord("exams", course_id, "exam_type", file_type)

            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO exams
                    (course_id, exam_type, button_title, title, ord)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (course_id, file_type, button_title, file_title, next_ord)
                )
                conn.commit()
                conn.close()

            append_row_to_csv(
                EXAMS_CSV_PATH,
                {"course_id": course_id, "exam_type": file_type, "button_title": button_title, "title": file_title, "ord": next_ord},
                ["course_id", "exam_type", "button_title", "title", "ord"]
            )

        logger.info(
            "Add file by -> userID=%s || Username=%s || Course=%s || Section=%s || Type=%s || Title=%s || Path=%s",
            user_id, message.from_user.username, course_id, section, file_type, file_title, saved_path
        )

        bot.reply_to(
            message,
            f"تمت الإضافة ✅\n"
            f"المادة: {course_id}\n"
            f"القسم: {section}\n"
            f"النوع: {file_type}\n"
            f"اسم الملف: {file_title}"
        )

    except Exception as error:
        logger.error("Add file error -> %s", error)
        notify_admins_error("handle_add_file", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء الإضافة ❌\n{error}")


@bot.message_handler(func=lambda message: message.text and message.text.startswith("!DeleteFile"))
def handle_delete_file(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split()

    if len(parts) < 5:
        bot.reply_to(
            message,
            "الصيغة غلط.\n\n"
            "استخدم:\n"
            "!DeleteFile COURSE SECTION TYPE FILE_NAME\n\n"
            "مثال:\n"
            "!DeleteFile CPCS-204 exams FinalLab Test\n"
            "!DeleteFile CPCS-204 slides lecture CH09"
        )
        return

    course_id = parts[1].upper()
    section = parts[2].lower().capitalize()
    file_type = parts[3].strip().lower()
    file_title = parts[4]

    file_type = FILE_TYPE_ALIASES.get(file_type, file_type).lower()

    if section not in ["Slides", "Exams"]:
        bot.reply_to(message, "القسم لازم يكون slides أو exams")
        return

    if not course_exists(course_id):
        bot.reply_to(message, f"المادة {course_id} غير موجودة في قاعدة البيانات")
        return

    try:
        final_file_name = f"{course_id}_{file_title}"

        if section == "Slides":
            target_folder = Path(f"DataBase/Courses/{course_id}/Slides/{file_type}")
            table_name = "slides"
            type_column = "slide_type"
            csv_path = SLIDES_CSV_PATH
        else:
            target_folder = Path(f"DataBase/Courses/{course_id}/Exams/{file_type}")
            table_name = "exams"
            type_column = "exam_type"
            csv_path = EXAMS_CSV_PATH

        deleted_file = None

        for extension in ALLOWED_EXTENSIONS:
            file_path = target_folder / f"{final_file_name}{extension}"
            if file_path.exists():
                file_path.unlink()
                deleted_file = file_path
                break

        if deleted_file is None:
            bot.reply_to(
                message,
                "ما لقيت الملف في المجلد ❌\n"
                f"بحثت عن: {final_file_name}\n"
                f"داخل: {target_folder}"
            )
            return

        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                DELETE FROM {table_name}
                WHERE course_id = %s AND {type_column} = %s AND title = %s
                """,
                (course_id, file_type, file_title)
            )
            conn.commit()
            conn.close()

        remove_row_from_csv(csv_path, course_id, file_type, file_title, type_column)

        logger.info(
            "Delete file by -> userID=%s || Username=%s || Course=%s || Section=%s || Type=%s || Title=%s || Path=%s",
            user_id, message.from_user.username, course_id, section, file_type, file_title, deleted_file
        )

        bot.reply_to(
            message,
            f"تم حذف الملف ✅\n"
            f"المادة: {course_id}\n"
            f"القسم: {section}\n"
            f"النوع: {file_type}\n"
            f"اسم الملف: {file_title}"
        )

    except Exception as error:
        logger.error("Delete file error -> %s", error)
        notify_admins_error("handle_delete_file", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء الحذف ❌\n{error}")
