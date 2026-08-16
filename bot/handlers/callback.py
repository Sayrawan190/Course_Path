from logging_config import logger
from bot.errors import notify_admins_error
from bot.instance import bot
from bot.keyboards import build_nav_keyboard
from bot.messaging import edit_message
from bot.routes import route
from bot.state import push_history


@bot.callback_query_handler(func=lambda call: True)
def on_callback(call):
    try:
        logger.info("Callback: [%s] -> userID= %s || Username= %s", call.data, call.from_user.id, call.from_user.username)

        if not (call.data.startswith("BACK") or call.data.startswith("HOME")):
            push_history(call.from_user.id, call.data)

        route(call, call.data)

    except Exception as e:
        logger.error("Unhandled callback error: %s", e)
        notify_admins_error(
            "on_callback",
            e,
            f"UserID={call.from_user.id} | Username={call.from_user.username} | Data={call.data}"
        )
        try:
            edit_message(call, "عذرًا، حدث خطأ غير متوقع. تم إبلاغ الدعم الفني تلقائيًا. 🛠️", build_nav_keyboard())
            notify_admins_error(
                "on_callback_user_notification", e, f"UserID={call.from_user.id} | Username={call.from_user.username} | Data={call.data}"
            )
        except Exception:
            pass

    finally:
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
