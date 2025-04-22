from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import TelegramError
import logging


class TelegramBotManager:
    def __init__(self, token, chat_id):
        self.TOKEN = token
        self.CHAT_ID = chat_id
        self.bot = Bot(token=token)

    async def send_message(self, message, reply_markup=None):
        """Асинхронная отправка сообщения в Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.CHAT_ID,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return True
        except TelegramError as e:
            logging.error(f"Ошибка Telegram (send_message): {str(e)}")
            return False

    @staticmethod
    def get_reply_keyboard():
        """Возвращает клавиатуру с кнопками"""
        keyboard = [
            [KeyboardButton('Показать текущий топ')],
            [KeyboardButton('Топ-10'), KeyboardButton('Топ-25')]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
