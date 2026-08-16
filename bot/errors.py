import traceback

from config import ADMIN_IDS
from logging_config import logger
from bot.instance import bot
from bot.keyboards import build_nav_keyboard
from bot.messaging import edit_message


def notify_admins_error(context: str, error: Exception, extra_info: str = "", call=None):
    """يرسل رسالة لكل الأدمن لما يصير خطأ غير متوقع"""
    tb = traceback.format_exc()

    msg = (
        f"⚠️ *خطأ غير متوقع في البوت*\n\n"
        f"📍 *المكان:* `{context}`\n"
        f"❌ *الخطأ:* `{type(error).__name__}: {error}`\n"
    )

    if call:
        user_id = call.from_user.id
        username = call.from_user.username or "None"
        full_name = f"{call.from_user.first_name or ''} {call.from_user.last_name or ''}".strip() or "None"
        chat_id = call.message.chat.id
        msg += (
            f"\n👤 *الاسم:* {full_name}\n"
            f"🔗 *اليوزرنيم:* \n@{username}\n"
            f"💬 *Chat ID:* `{chat_id}`\n"
        )

    if extra_info:
        msg += f"ℹ️ *معلومات إضافية:* {extra_info}\n"

    msg += f"\n```\n{tb[-1000:]}\n```"

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, msg, parse_mode="Markdown")
        except Exception as e:
            logger.error("Failed to notify admin %s: %s", admin_id, e)


def safe_callback(func):
    """Decorator يلتقط أي خطأ في callback handlers ويرسله للأدمن"""
    def wrapper(call, parts):
        try:
            return func(call, parts)
        except Exception as e:
            logger.error("Error in %s: %s", func.__name__, e)
            extra = f"UserID={call.from_user.id} | Username={call.from_user.username} | Data={call.data}"
            notify_admins_error(func.__name__, e, extra, call)
            try:
                edit_message(call, "عذرًا، حدث خطأ غير متوقع. تم إبلاغ الدعم الفني تلقائيًا. 🛠️", build_nav_keyboard())
            except Exception:
                pass
    return wrapper


def cheack_itsEmpty(call, array):
    if not array:
        # رسالة للمستخدم
        edit_message(
            call,
            "عذرًا، المصادر المطلوبة غير متوفرة حاليًا.\nاذا كان عندك مصادر لهذي المادة ارسلها لنا @Course_path_support ❌",
            build_nav_keyboard()
        )

        # رسالة للأدمن
        user_id = call.from_user.id
        username = call.from_user.username or "None"
        chat_id = call.message.chat.id
        requested = call.data

        admin_msg = (
            f"📭 *محتوى غير متوفر*\n\n"
            f"👤 *المستخدم:* `{user_id}`\n"
            f"🔗 *اليوزرنيم:* @\n{username}\n"
            f"💬 *Chat ID:* `{chat_id}`\n"
            f"📌 *الطلب:* `{requested}`"
        )

        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error("Failed to notify admin %s: %s", admin_id, e)

        return True
    return False
