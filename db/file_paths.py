import re
from pathlib import Path

from logging_config import logger


def get_slide_file_path(course_id, slide_type, title):
    try:
        pathSlides = Path(f"DataBase/Courses/{course_id}/Slides/{slide_type}")

        if not pathSlides.exists():
            return None

        matches = list(pathSlides.rglob("*"))

        # تطابق Ch09 في نهاية الاسم
        for f in matches:
            if f.is_file() and re.search(rf"_{re.escape(title)}$", f.stem):
                return f

        # احتياط: البحث الجزئي مع تفضيل الاسم الأقصر
        partial_matches = [
            f for f in matches
            if f.is_file() and title in f.stem
        ]

        if partial_matches:
            return min(partial_matches, key=lambda f: len(f.stem))

    except Exception as e:
        logger.error("get_slide_file_path error: %s", e)

    return None


def get_exam_file_path(course_id, exam_type, title):
    try:
        pathExams = Path(f"DataBase/Courses/{course_id}/Exams/{exam_type}")
        if not pathExams.exists():
            return None
        for f in pathExams.rglob("*"):
            name = f.stem.split("_", 1)[-1]
            if name == title:
                return f
    except Exception as e:
        logger.error("get_exam_file_path error: %s", e)
    return None
