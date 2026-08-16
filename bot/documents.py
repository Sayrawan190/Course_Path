from logging_config import logger
from bot.instance import bot
from bot.errors import notify_admins_error
from bot.keyboards import build_nav_keyboard
from bot.messaging import edit_message


def send_document_file(call, file_path):
    try:
        with open(file_path, "rb") as f:
            bot.send_document(call.message.chat.id, f)
        return True

    except FileNotFoundError as e:
        logger.error("File Not Found Error: %s", e)
        notify_admins_error("send_document_file", e, f"Path={file_path}", call)
        edit_message(call, "عذرًا، الملف غير متوفر حاليًا. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return False

    except Exception as e:
        logger.error("Error sending file: %s", e)
        notify_admins_error("send_document_file", e, f"Path={file_path}", call)
        edit_message(call, "عذرًا، حدث خطأ أثناء إرسال الملف. تم إبلاغ الدعم الفني. 🛠️", build_nav_keyboard())
        return False
