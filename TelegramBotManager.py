from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import TelegramError
import logging
import asyncio


class TelegramBotManager:
    def __init__(self, token, chat_id):
        self.TOKEN = token
        self.CHAT_ID = chat_id
        self.bot = Bot(token=token)

    async def send_message(
            self,
            message: str,
            chat_id: int = -1,
            reply_markup: ReplyKeyboardMarkup = None,
            max_retries: int = 3,
            max_length: int = 3000
    ) -> bool:
        """Асинхронная отправка сообщения с разбивкой и повторами при ошибках."""
        if chat_id < 0:
            chat_id = self.CHAT_ID

        message_parts = self._split_message(message, max_length)

        for part in message_parts:
            for attempt in range(max_retries):
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    break
                except TelegramError as e:
                    logging.error(f"Ошибка Telegram (попытка {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        return False
                    await asyncio.sleep(2 ** attempt)
        return True

    @staticmethod
    def _split_message(message: str, max_length: int) -> list[str]:
        """Разбивает сообщение на части, не превышающие max_length."""
        if len(message) <= max_length:
            return [message]

        parts = []
        while message:
            split_pos = max_length
            if len(message) > max_length:
                split_pos = message.rfind('\n', 0, max_length)
                if split_pos == -1:
                    split_pos = message.rfind(' ', 0, max_length)
                if split_pos == -1:
                    split_pos = max_length

            parts.append(message[:split_pos])
            message = message[split_pos:].lstrip()
        return parts

    @staticmethod
    def get_reply_keyboard():
        """Возвращает клавиатуру с кнопками"""
        keyboard = [
            [KeyboardButton('Посмотреть изменения с прошлой проверки')],
            [KeyboardButton('Показать текущий топ')],
            #[KeyboardButton('Изменить частоту проверки')],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_check_time_keyboard():
        buttons = []
        # Создаем кнопки для каждого часа (1-24)
        for i in range(1, 25):
            buttons.append([KeyboardButton(f'Раз в {i} часа')])

        return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
