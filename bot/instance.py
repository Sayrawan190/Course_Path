import telebot
from telebot.types import BotCommand

from config import BOT_TOKEN, MAINTENANCE_BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

bot.set_my_commands([
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Help and guide"),
])
