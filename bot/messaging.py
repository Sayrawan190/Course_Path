from telebot.apihelper import ApiTelegramException

from bot.instance import bot


def edit_message(call, text, kb=None):
    try:
        bot.edit_message_text(
            text=text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            return
        raise


def send_message(call, text, kb=None):
    try:
        bot.send_message(
            text=text,
            chat_id=call.message.chat.id,
            reply_markup=kb
        )
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            return
        raise
