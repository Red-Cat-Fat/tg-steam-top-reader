import schedule
import asyncio
import logging
from threading import Thread
import time
from typing import Callable, Optional


class SchedulerManager:
    def __init__(
            self,
            check_coroutine: Callable,
            initial_time: str = ":00",
            interval_hours: int = 1,
            logger: Optional[logging.Logger] = None
    ):
        """
        :param check_coroutine: Асинхронная корутина для выполнения
        :param initial_time: Время выполнения в формате ":MM" (минуты)
        :param interval_hours: Интервал в часах между выполнениями
        :param logger: Кастомный логгер (если None, будет создан стандартный)
        """
        self.check_coroutine = check_coroutine
        self.check_time = initial_time
        self.interval_hours = interval_hours
        self.logger = logger or self._setup_default_logger()

        self.scheduler_thread = None
        self.loop = asyncio.new_event_loop()
        self.scheduled_job = None
        self.running = False

    def _setup_default_logger(self) -> logging.Logger:
        """Настройка логгера по умолчанию"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def start_scheduler(self) -> None:
        """Запускает планировщик в отдельном потоке"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.logger.warning("Планировщик уже запущен")
            return

        self.running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info(f"Планировщик запущен. Проверка каждые {self.interval_hours} час(а/ов) в {self.check_time}")

    def _run_scheduler(self) -> None:
        """Запускает цикл планировщика"""
        asyncio.set_event_loop(self.loop)
        self._schedule_job()

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def _schedule_job(self) -> None:
        """Создает/обновляет задание в планировщике"""
        if self.scheduled_job:
            schedule.cancel_job(self.scheduled_job)

        # Формируем расписание с учетом интервала в часах
        self.scheduled_job = schedule.every(self.interval_hours).hours.at(self.check_time).do(
            lambda: asyncio.run_coroutine_threadsafe(self.check_coroutine(), self.loop)
        )
        self.logger.info(f"Расписание обновлено: каждые {self.interval_hours} час(а/ов) в {self.check_time}")

    def update_schedule(self, new_time: str = None, interval_hours: int = None) -> None:
        """
        Обновляет параметры расписания
        :param new_time: Новое время в формате ":MM" (если None - не изменяется)
        :param interval_hours: Новый интервал в часах (если None - не изменяется)
        """
        if new_time is not None:
            if not new_time.startswith(":"):
                new_time = ":" + new_time
            self.check_time = new_time

        if interval_hours is not None:
            if interval_hours < 1:
                raise ValueError("Интервал должен быть не менее 1 часа")
            self.interval_hours = interval_hours

        self._schedule_job()

    def stop(self) -> None:
        """Останавливает планировщик"""
        self.running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.logger.info("Планировщик остановлен")