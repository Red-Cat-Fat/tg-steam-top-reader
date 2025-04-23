import re
import schedule
import time
import asyncio
from telegram.error import TelegramError
from SchedulerManager import SchedulerManager


class BotLogic:
    def __init__(self, steam_manager, telegram_manager, logging):
        self.steam = steam_manager
        self.telegram = telegram_manager
        self.logging = logging

        self.manager = SchedulerManager(
            check_coroutine=self.check_and_notify,
            initial_time=":00",
            interval_hours=3,
            logger=self.logging
        )

    async def check_and_notify(self):
        """Проверка изменений и отправка уведомлений"""
        self.logging.info("Проверка изменений...")

        current_top = self.steam.get_current_top()
        if not current_top:
            error_message = "⚠️ Не удалось получить текущий топ игр из Steam API"
            self.logging.error(error_message)
            await self.telegram.send_message(error_message)
            return

        previous_top = self.steam.load_previous_top()

        if previous_top:
            changes = self.steam.compare_tops(previous_top, current_top)
            if changes:
                message = "🎮 *Изменения в Steam Топ-10:*\n\n" + "\n".join(changes)
                await self.telegram.send_message(message)
            else:
                self.logging.info("Изменений не обнаружено")
        else:
            self.logging.info("Первая проверка, сохраняем текущий топ")

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
                                chat_id=chat_id,
                                reply_markup=self.telegram.get_reply_keyboard()
                            )
                        elif text in ['Изменить частоту проверки']:
                            await self.telegram.send_message(
                                'Как часто нужно проверять обновления?',
                                chat_id=chat_id,
                                reply_markup=self.telegram.get_check_time_keyboard()
                            )
                        else:
                            match = re.search(r'Раз в (\d+) час(?:а|ов)?', text)  # Ищем "час", "часа", "часов"
                            if match:
                                i = int(match.group(1))  # Извлекаем число и преобразуем в int
                                self.manager.update_schedule(':00', interval_hours=i)
                                await self.telegram.send_message(
                                    'Теперь проверка будет осуществляться каждые {0} часа'.format(i),
                                    chat_id=chat_id,
                                    reply_markup=self.telegram.get_reply_keyboard()
                                )

                await asyncio.sleep(1)
            except TelegramError as e:
                self.logging.error(f"Ошибка Telegram (handle_updates): {str(e)}")
                await asyncio.sleep(5)

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

        self.manager.start_scheduler()

        # Первая проверка при запуске
        asyncio.run_coroutine_threadsafe(self.check_and_notify(), loop)

        # Основной цикл
        while True:
            schedule.run_pending()
            time.sleep(1)
