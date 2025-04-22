import requests
import json
import logging


class SteamTopManager:
    def __init__(self, top_size=100, data_file='steam_top_games.json', cache_file='steam_names_cache.json'):
        self.TOP_SIZE = top_size
        self.DATA_FILE = data_file
        self.CACHE_FILE = cache_file
        self.STEAM_API_URL = 'https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/'
        self._load_name_cache()

    def _load_name_cache(self):
        """Загружает кеш названий из файла"""
        try:
            with open(self.CACHE_FILE, 'r') as f:
                self._name_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._name_cache = {}

    def _save_name_cache(self):
        """Сохраняет кеш названий в файл"""
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(self._name_cache, f, indent=2)

    def get_game_name(self, appid):
        """Получает название игры по её AppID и возвращает в формате ссылки на SteamDB"""
        # Проверяем кеш
        if appid in self._name_cache:
            return self._name_cache[appid]

        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            response = requests.get(url, timeout=5)
            data = response.json()
            name = data.get(str(appid), {}).get('data', {}).get('name')

            # Формируем ссылку, если имя получено
            if name:
                steamdb_url = f"https://steamdb.info/app/{appid}/charts/"
                result = f"[{name}]({steamdb_url})"
            else:
                result = f"[AppID: {appid}](https://steamdb.info/app/{appid}/charts/)"

            self._name_cache[appid] = result
            return result
        except Exception as e:
            logging.error(f"Ошибка при получении имени игры {appid}: {str(e)}")
            # Возвращаем хотя бы ссылку с appid, если не удалось получить имя
            result = f"[AppID: {appid}](https://steamdb.info/app/{appid}/charts/)"
            self._name_cache[appid] = result
            return result

    def get_current_top(self):
        """Получает текущий топ игр через Steam API"""
        try:
            response = requests.get(self.STEAM_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get('response', {}).get('ranks'):
                raise ValueError("Нет данных в ответе API")

            top_games = []
            for item in data['response']['ranks']:
                if item['rank'] <= self.TOP_SIZE:
                    # Теперь get_game_name возвращает уже отформатированную ссылку
                    game_info = self.get_game_name(item['appid'])
                    top_games.append({
                        'rank': item['rank'],
                        'appid': item['appid'],
                        'name': game_info  # Здесь уже будет ссылка в формате Markdown
                    })

            return top_games
        except Exception as e:
            logging.error(f"Ошибка Steam API: {str(e)}")
            return None

    def load_previous_top(self):
        """Загружает предыдущий топ из файла"""
        try:
            with open(self.DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save_current_top(self, top):
        """Сохраняет текущий топ в файл"""
        with open(self.DATA_FILE, 'w') as f:
            json.dump(top, f, indent=2)

    def compare_tops(self, prev_top, curr_top):
        """Сравнивает два топа и возвращает список изменений, отслеживая перемещения игр"""
        changes = []

        # Создаем словари {appid: rank} для быстрого поиска
        prev_appid_to_rank = {game['appid']: game['rank'] for game in prev_top}
        curr_appid_to_rank = {game['appid']: game['rank'] for game in curr_top}

        # Словарь для отслеживания перемещений (чтобы не дублировать сообщения)
        moved_games = set()

        for curr_game in curr_top:
            appid = curr_game['appid']
            curr_rank = curr_game['rank']

            # Если игры не было в предыдущем топе
            if appid not in prev_appid_to_rank:
                changes.append(f"🆕 Новая игра в топе: {curr_game['name']} (место {curr_rank})")
                continue

            prev_rank = prev_appid_to_rank[appid]

            # Если ранг изменился
            if prev_rank != curr_rank and appid not in moved_games:
                moved_games.add(appid)
                if prev_rank < curr_rank:
                    changes.append(
                        f"🔼 Игра поднялась: {curr_game['name']} "
                        f"(с {prev_rank} места на {curr_rank})"
                    )
                else:
                    changes.append(
                        f"🔽 Игра опустилась: {curr_game['name']} "
                        f"(с {prev_rank} места на {curr_rank})"
                    )

        # Проверяем игры, которые выбыли из топа
        for prev_game in prev_top:
            appid = prev_game['appid']
            if appid not in curr_appid_to_rank:
                changes.append(f"❌ Игра выбыла из топа: {prev_game['name']} (была на {prev_game['rank']})")

        return changes

    def get_top_message(self, count=-1):
        if count < 0:
            count = self.TOP_SIZE
        """Формирует сообщение с текущим топом игр"""
        current_top = self.load_previous_top()
        if not current_top:
            return "Топ игр ещё не был сформирован или не доступен."

        message = f"🎮 *Текущий Топ-{count} игр в Steam:*\n\n"
        for game in current_top[:count]:
            message += f"{game['rank']}. {game['name']}\n"

        return message
