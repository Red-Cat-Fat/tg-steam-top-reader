Создать .env файл. Например steam_top.env с содержимым
```
TELEGRAM_BOT_TOKEN=*your_telegram_token*
TELEGRAM_CHAT_ID=*your_chat_id*
```
Запустить докер через команду
```
docker run -d --name tg_steam_top_reader --env-file steam_top.env -p 5000:5000 redcatfat/tg-steam-top-reader:v1.0
```
Либо запустить bash скрипт и следовать инструкциям:
```
#!/bin/bash

# --- Конфигурация ---
CONTAINER_NAME="tg-steam-top-reader-container"  # Имя контейнера
IMAGE_BASE="redcatfat/tg-steam-top-reader"      # Репозиторий образа (с дефисами)
ENV_FILE="steam_top.env"                        # Путь к .env файлу

# --- Проверка аргументов ---
if [ -z "$1" ]; then
  echo "Ошибка: Укажите тег образа (например: ./run-docker.sh latest)"
  exit 1
fi
TAG="$1"

# --- Загружаем переменные из .env ---
set -a  # Автоматически экспортировать все переменные
source "$ENV_FILE" || { echo "❌ Ошибка загрузки $ENV_FILE"; exit 1; }
set +a

# --- Проверка обязательных переменных ---
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "Ошибка: Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в $ENV_FILE"
  exit 1
fi

TELEGRAM_API_URL="https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage"

# --- Функция отправки в Telegram ---
send_telegram() {
  local message="$1"
  curl -s -X POST "$TELEGRAM_API_URL" \
    -d chat_id="$TELEGRAM_CHAT_ID" \
    -d text="$message" \
    -d parse_mode="Markdown" > /dev/null || echo "⚠️ Не удалось отправить в Telegram"
}

# --- 1. Останавливаем и удаляем старый контейнер ---
echo "Останавливаем старый контейнер '$CONTAINER_NAME'..."
docker stop "$CONTAINER_NAME" 2>/dev/null || echo "Контейнер не найден (пропускаем)"
docker rm "$CONTAINER_NAME" 2>/dev/null || echo "Контейнер не найден (пропускаем)"

# --- 2. Авторизация в Docker Hub (если требуется) ---
if ! docker info | grep -q "Username: redcatfat"; then
  echo "Требуется вход в Docker Hub..."
  docker login -u redcatfat || {
    send_telegram "❌ *Ошибка авторизации Docker Hub*"
    exit 1
  }
fi

# --- 3. Скачиваем новый образ ---
echo "Скачиваем образ '$IMAGE_BASE:$TAG'..."
docker pull "$IMAGE_BASE:$TAG" || {
  send_telegram "❌ *Ошибка при скачивании образа*: \`$IMAGE_BASE:$TAG\`"
  send_telegram "ℹ️ Проверьте: 1) Существует ли образ 2) Доступы 3) Сетевые настройки"
  exit 1
}

# --- 4. Запускаем новый контейнер ---
echo "Запускаем контейнер с тегом '$TAG'..."
docker run \
  --env-file "$ENV_FILE" \
  -d \
  --name "$CONTAINER_NAME" \
  "$IMAGE_BASE:$TAG" || {
  send_telegram "❌ *Ошибка при запуске контейнера*: $CONTAINER_NAME"
  exit 1
}

# --- Успешное завершение ---
send_telegram "✅ *Контейнер успешно обновлён!* 
- Имя: \`$CONTAINER_NAME\`
- Образ: \`$IMAGE_BASE:$TAG\`
- Статус: \`$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")\`"

echo "Статус контейнера:"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}"
```