import schedule
import time
import asyncio
import logging
from telegram.error import TelegramError


class BotLogic:
    def __init__(self, steam_manager, telegram_manager, check_time='12:00'):
        self.steam = steam_manager
        self.telegram = telegram_manager
        self.CHECK_TIME = check_time

    async def check_and_notify(self):
        """Проверка изменений и отправка уведомлений"""
        logging.info("Проверка изменений...")

        current_top = self.steam.get_current_top()
        if not current_top:
            await self.telegram.send_message("⚠️ Не удалось получить текущий топ игр из Steam API")
            return

        previous_top = self.steam.load_previous_top()

        if previous_top:
            changes = self.steam.compare_tops(previous_top, current_top)
            if changes:
                message = "🎮 *Изменения в Steam Топ-10:*\n\n" + "\n".join(changes)
                await self.telegram.send_message(message)
            else:
                logging.info("Изменений не обнаружено")
        else:
            logging.info("Первая проверка, сохраняем текущий топ")

        self.steam.save_current_top(current_top)

    async def handle_updates(self):
        """Обработка входящих сообщений"""
        last_update_id = 0

        while True:
            try:
                updates = await self.telegram.bot.get_updates(offset=last_update_id + 1, timeout=1000)

                for update in updates:
                    if update.message and update.message.text:
                        text = update.message.text
                        chat_id = update.message.chat.id
                        last_update_id = update.update_id

                        if text in ['Показать текущий топ', '/top']:
                            await self.telegram.send_message(
                                self.steam.get_top_message(),
                                reply_markup=self.telegram.get_reply_keyboard()
                            )
                        elif text == 'Топ-10':
                            await self.telegram.send_message(self.steam.get_top_message(10))
                        elif text == 'Топ-25':
                            await self.telegram.send_message(self.steam.get_top_message(25))

                await asyncio.sleep(1)
            except TelegramError as e:
                logging.error(f"Ошибка Telegram (handle_updates): {str(e)}")
                await asyncio.sleep(5)

    @staticmethod
    def run_async(func):
        """Запускает асинхронную функцию в отдельном потоке"""

        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return wrapper

    def main(self):
        """Основной цикл работы бота"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Запускаем обработчик сообщений
        import threading
        threading.Thread(
            target=lambda: loop.run_until_complete(self.handle_updates()),
            daemon=True
        ).start()

        # Стартовое сообщение
        asyncio.run_coroutine_threadsafe(
            self.telegram.send_message(
                "Бот перезапущен. Используйте /top или кнопки для получения топа игр.",
                self.telegram.get_reply_keyboard()
            ),
            loop
        )

        # Настройка расписания
        schedule.every().day.at(self.CHECK_TIME).do(
            lambda: asyncio.run_coroutine_threadsafe(self.check_and_notify(), loop)
        )

        # Первая проверка при запуске
        asyncio.run_coroutine_threadsafe(self.check_and_notify(), loop)

        # Основной цикл
        while True:
            schedule.run_pending()
            time.sleep(1)
