import threading
from urllib.parse import urlsplit

import psycopg2

from config import DATABASE_URL

db_lock = threading.Lock()

_parsed = urlsplit(DATABASE_URL)


def get_db_connection():
    return psycopg2.connect(
        host=_parsed.hostname,
        port=_parsed.port,
        user=_parsed.username,
        password=_parsed.password,
        dbname=_parsed.path.lstrip("/"),
    )
