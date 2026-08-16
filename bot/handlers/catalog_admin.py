import csv
import re
from pathlib import Path

from config import (
    ADMIN_IDS,
    COURSE_SECTIONS,
    COURSES_CSV_PATH,
    EXAMS_CSV_PATH,
    INFO_SOURCES_CSV_PATH,
    MAJOR_NAME,
    MAJOR_TERMS_CSV_PATH,
    SLIDES_CSV_PATH,
)
from logging_config import logger
from bot.errors import notify_admins_error
from bot.instance import bot
from db.connection import db_lock, get_db_connection

COURSE_ID_RE = re.compile(r"^[A-Z]+-\d+$")


def read_csv_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def write_csv_rows(csv_path, rows, fieldnames):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_csv_row(csv_path, row_data, fieldnames):
    file_exists = Path(csv_path).exists()
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)


# ==========================================================
# !AddCourse MAJOR TERM COURSE_ID اسم_المادة
# ==========================================================
@bot.message_handler(func=lambda message: message.text and message.text.startswith("!AddCourse"))
def handle_add_course(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        bot.reply_to(
            message,
            "الصيغة غلط.\n\n"
            "استخدم:\n"
            "!AddCourse MAJOR TERM COURSE_ID اسم_المادة\n\n"
            "مثال:\n"
            "!AddCourse IT 7 CPCS-203 برمجة 2 - OOP\n\n"
            f"التخصصات المتاحة: {', '.join(MAJOR_NAME.keys())}"
        )
        return

    major_code = parts[1].upper()
    term_raw = parts[2]
    course_id = parts[3].upper()
    course_title = parts[4].strip()

    if major_code not in MAJOR_NAME:
        bot.reply_to(message, f"تخصص غير معروف: {major_code}\nالمتاح: {', '.join(MAJOR_NAME.keys())}")
        return

    if not term_raw.isdigit():
        bot.reply_to(message, "المستوى (Term) لازم يكون رقم")
        return

    if not COURSE_ID_RE.match(course_id):
        bot.reply_to(message, "صيغة رمز المادة غلط. مثال صحيح: CPCS-203")
        return

    if not course_title:
        bot.reply_to(message, "لازم تكتب اسم المادة")
        return

    term = int(term_raw)
    course_name, course_code = course_id.split("-", 1)

    try:
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO major_terms (major_code, term, course_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (major_code, term, course_id)
            )
            cur.executemany(
                """
                INSERT INTO courses (course_name, course_code, course_title, section, title, ord)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                [(course_name, int(course_code), course_title, sec, title, ord_) for sec, title, ord_ in COURSE_SECTIONS]
            )
            conn.commit()
            conn.close()

        append_csv_row(
            MAJOR_TERMS_CSV_PATH,
            {"major_code": major_code, "term": term, "course_id": course_id},
            ["major_code", "term", "course_id"]
        )
        for sec, title, ord_ in COURSE_SECTIONS:
            append_csv_row(
                COURSES_CSV_PATH,
                {"course_name": course_name, "course_code": course_code, "course_title": course_title, "section": sec, "title": title, "ord": ord_},
                ["course_name", "course_code", "course_title", "section", "title", "ord"]
            )

        logger.info(
            "AddCourse by -> userID=%s || course=%s || major=%s || term=%s || title=%s",
            user_id, course_id, major_code, term, course_title
        )

        bot.reply_to(
            message,
            f"تمت إضافة المادة ✅\n"
            f"الرمز: {course_id}\n"
            f"التخصص: {MAJOR_NAME[major_code]}\n"
            f"المستوى: {term}\n"
            f"الاسم: {course_title}\n\n"
            f"تقدر الحين تضيف ملفاتها بـ !Add"
        )

    except Exception as error:
        logger.error("AddCourse error -> %s", error)
        notify_admins_error("handle_add_course", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء الإضافة ❌\n{error}")


# ==========================================================
# !SetInfo COURSE_ID <نص المعلومات> / !SetSources COURSE_ID <نص المصادر>
# ==========================================================
def _set_info_sources(message, column, label):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(
            message,
            f"الصيغة غلط.\n\nاستخدم:\n!Set{label} COURSE_ID النص\n\n"
            f"مثال:\n!Set{label} CPCS-204 المادة تركيزها نظري..."
        )
        return

    course_id = parts[1].upper()
    text = parts[2].strip().replace("\n", "||")

    try:
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO info_sources (course_id, {column})
                VALUES (%s, %s)
                ON CONFLICT (course_id) DO UPDATE SET {column} = excluded.{column}
                """,
                (course_id, text)
            )
            conn.commit()
            conn.close()

        rows, fieldnames = read_csv_rows(INFO_SOURCES_CSV_PATH)
        for row in rows:
            if row["course_id"] == course_id:
                row[column] = text
                break
        else:
            new_row = {"course_id": course_id, "info": "", "sources": ""}
            new_row[column] = text
            rows.append(new_row)
        write_csv_rows(INFO_SOURCES_CSV_PATH, rows, fieldnames or ["course_id", "info", "sources"])

        logger.info("Set%s by -> userID=%s || course=%s", label, user_id, course_id)
        bot.reply_to(message, f"تم تحديث {'المعلومات' if column == 'info' else 'المصادر'} لمادة {course_id} ✅")

    except Exception as error:
        logger.error("Set%s error -> %s", label, error)
        notify_admins_error(f"handle_set_{column}", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء التحديث ❌\n{error}")


@bot.message_handler(func=lambda message: message.text and message.text.startswith("!SetInfo"))
def handle_set_info(message):
    _set_info_sources(message, "info", "Info")


@bot.message_handler(func=lambda message: message.text and message.text.startswith("!SetSources"))
def handle_set_sources(message):
    _set_info_sources(message, "sources", "Sources")


# ==========================================================
# !DeleteCourse COURSE_ID [CONFIRM]
# ==========================================================
@bot.message_handler(func=lambda message: message.text and message.text.startswith("!DeleteCourse"))
def handle_delete_course(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "الصيغة غلط.\n\nاستخدم:\n!DeleteCourse COURSE_ID\n\nمثال:\n!DeleteCourse CPCS-999")
        return

    course_id = parts[1].upper()
    confirmed = len(parts) >= 3 and parts[2].upper() == "CONFIRM"
    course_name, course_code = course_id.split("-", 1)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM slides WHERE course_id=%s", (course_id,))
    n_slides = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM exams WHERE course_id=%s", (course_id,))
    n_exams = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM major_terms WHERE course_id=%s", (course_id,))
    n_terms = cur.fetchone()[0]
    conn.close()

    if not confirmed:
        bot.reply_to(
            message,
            f"⚠️ بيتحذف من الداتابيس (مو الملفات نفسها من على السيرفر):\n\n"
            f"المادة: {course_id}\n"
            f"صفوف major_terms: {n_terms}\n"
            f"سلايدات: {n_slides}\n"
            f"اختبارات: {n_exams}\n\n"
            f"للتأكيد أرسل:\n!DeleteCourse {course_id} CONFIRM"
        )
        return

    try:
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM major_terms WHERE course_id=%s", (course_id,))
            cur.execute("DELETE FROM courses WHERE course_name=%s AND course_code=%s", (course_name, int(course_code)))
            cur.execute("DELETE FROM slides WHERE course_id=%s", (course_id,))
            cur.execute("DELETE FROM exams WHERE course_id=%s", (course_id,))
            cur.execute("DELETE FROM info_sources WHERE course_id=%s", (course_id,))
            conn.commit()
            conn.close()

        rows, fn = read_csv_rows(MAJOR_TERMS_CSV_PATH)
        write_csv_rows(MAJOR_TERMS_CSV_PATH, [r for r in rows if r["course_id"] != course_id], fn)

        rows, fn = read_csv_rows(COURSES_CSV_PATH)
        write_csv_rows(COURSES_CSV_PATH, [r for r in rows if not (r["course_name"] == course_name and r["course_code"] == course_code)], fn)

        rows, fn = read_csv_rows(SLIDES_CSV_PATH)
        write_csv_rows(SLIDES_CSV_PATH, [r for r in rows if r["course_id"] != course_id], fn)

        rows, fn = read_csv_rows(EXAMS_CSV_PATH)
        write_csv_rows(EXAMS_CSV_PATH, [r for r in rows if r["course_id"] != course_id], fn)

        rows, fn = read_csv_rows(INFO_SOURCES_CSV_PATH)
        write_csv_rows(INFO_SOURCES_CSV_PATH, [r for r in rows if r["course_id"] != course_id], fn)

        logger.info("DeleteCourse by -> userID=%s || course=%s", user_id, course_id)
        bot.reply_to(message, f"تم حذف مادة {course_id} من الداتابيس ✅\n(الملفات نفسها على السيرفر ما اتحذفت)")

    except Exception as error:
        logger.error("DeleteCourse error -> %s", error)
        notify_admins_error("handle_delete_course", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء الحذف ❌\n{error}")


# ==========================================================
# !Reorder COURSE_ID SECTION TYPE TITLE POSITION
# ==========================================================
@bot.message_handler(func=lambda message: message.text and message.text.startswith("!Reorder"))
def handle_reorder(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "ما عندك صلاحية استخدام هذا الأمر")
        return

    parts = message.text.split()
    if len(parts) < 6:
        bot.reply_to(
            message,
            "الصيغة غلط.\n\n"
            "استخدم:\n!Reorder COURSE_ID slides|exams TYPE TITLE POSITION\n\n"
            "مثال:\n!Reorder CPCS-204 slides lecture Ch05 2"
        )
        return

    course_id = parts[1].upper()
    section = parts[2].lower()
    type_ = parts[3].lower()
    title = parts[4]

    if section not in ("slides", "exams"):
        bot.reply_to(message, "القسم لازم يكون slides أو exams")
        return

    try:
        new_position = int(parts[5])
    except ValueError:
        bot.reply_to(message, "الموضع (POSITION) لازم يكون رقم")
        return

    table = "slides" if section == "slides" else "exams"
    type_col = "slide_type" if section == "slides" else "exam_type"
    csv_path = SLIDES_CSV_PATH if section == "slides" else EXAMS_CSV_PATH

    try:
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT title FROM {table} WHERE course_id=%s AND {type_col}=%s ORDER BY ord", (course_id, type_))
            titles = [r[0] for r in cur.fetchall()]

            if title not in titles:
                conn.close()
                bot.reply_to(message, f"ما لقيت عنوان {title!r} داخل {course_id}/{section}/{type_}")
                return

            titles.remove(title)
            new_position = max(1, min(new_position, len(titles) + 1))
            titles.insert(new_position - 1, title)

            for i, t in enumerate(titles, start=1):
                cur.execute(f"UPDATE {table} SET ord=%s WHERE course_id=%s AND {type_col}=%s AND title=%s", (i, course_id, type_, t))
            conn.commit()
            conn.close()

        rows, fn = read_csv_rows(csv_path)
        ord_col = "ord"
        id_col = "slide_type" if section == "slides" else "exam_type"
        new_ord = {t: i for i, t in enumerate(titles, start=1)}
        for row in rows:
            if row["course_id"] == course_id and row[id_col] == type_ and row["title"] in new_ord:
                row[ord_col] = str(new_ord[row["title"]])
        write_csv_rows(csv_path, rows, fn)

        logger.info("Reorder by -> userID=%s || course=%s || %s/%s/%s -> %s", user_id, course_id, section, type_, title, new_position)
        bot.reply_to(message, f"تم ترتيب {title} بالموضع {new_position} ✅\n\nالترتيب الحالي:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(titles, start=1)))

    except Exception as error:
        logger.error("Reorder error -> %s", error)
        notify_admins_error("handle_reorder", error, f"userID={user_id} | course={course_id}")
        bot.reply_to(message, f"صار خطأ أثناء إعادة الترتيب ❌\n{error}")
