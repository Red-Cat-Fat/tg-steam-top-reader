import logging
import os

from BotLogic import BotLogic
from SteamTopManager import SteamTopManager
from TelegramBotManager import TelegramBotManager

# Настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_TIME = os.getenv("CHECK_TIME")  # Время проверки (UTC)

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('steam_monitor.log'), logging.StreamHandler()]
)

if __name__ == "__main__":
    steam_manager = SteamTopManager(top_size=100)
    telegram_manager = TelegramBotManager(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    bot_logic = BotLogic(steam_manager, telegram_manager, CHECK_TIME)

    bot_logic.main()
    logging.info("Ready to work")