from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import TelegramError
import logging


class TelegramBotManager:
    def __init__(self, token, chat_id):
        self.TOKEN = token
        self.CHAT_ID = chat_id
        self.bot = Bot(token=token)

    async def send_message(self, message, chat_id=-1, reply_markup=None):
        """Асинхронная отправка сообщения в Telegram"""
        try:
            if chat_id < 0:
                chat_id = self.CHAT_ID
            await self.bot.send_message(
                chat_id=chat_id,
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
            [KeyboardButton('Изменить частоту проверки')],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_check_time_keyboard():
        buttons = []
        # Создаем кнопки для каждого часа (1-24)
        for i in range(1, 25):
            buttons.append([KeyboardButton(f'Раз в {i} часа')])

        return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
