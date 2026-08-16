import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ==========================================================
# Secrets (from .env)
# ==========================================================
BOT_TOKEN = os.environ["BOT_TOKEN"]
MAINTENANCE_BOT_TOKEN = os.environ.get("MAINTENANCE_BOT_TOKEN", BOT_TOKEN)

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

DATABASE_URL = os.environ["DATABASE_URL"]

# ==========================================================
# Admins
# ==========================================================
ADMIN_IDS = {1401478668, 810634477, 8256924843}

COURSE_SECTIONS = [
    ("info", "نبذة عن المادةℹ️", 1),
    ("sources", "مصادر المادة🔗", 2),
    ("old_exams", "النماذج📝", 3),
    ("slides", "سلايدات المادة📚", 4),
]

ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xlsx", ".xls", ".txt", ".zip"}

FILE_TYPE_ALIASES = {
    "lecture": "lecture",
    "lab": "lab",
    "summary": "summary",
    "finallab": "finallab",
    "finalexam": "finalexam",
    "mid": "mid",
    "quiz": "quiz"
}

# ==========================================================
# نصوص/مسميات
# ==========================================================
MAJOR_NAME = {
    "CS": "علوم حاسب 💡",
    "IT": "تقنية معلومات 💻",
    "IS": "نظم معلومات 💸",
    "FD": "التحضيري 👶🏻"
}

HOME_TEXT = "مرحباً بك مجدداً\n" + "القائمة الرئيسية🏠\nاختر تخصصك من القائمة:"

SLIDE_TYPE_TITLES = {
    "lecture": "نظري📚",
    "lab": "عملي💻",
    "summary": "ملخص📄"
}

EXAM_TYPE_TITLES = {
    "mid": "الميدات📝",
    "finalexam": "النهائي💀",
    "finallab": "العملي💻",
    "quiz": "كويزات🍪"
}
