Create .env file with data
```
TELEGRAM_BOT_TOKEN=*your_telegram_token*
TELEGRAM_CHAT_ID=*your_chat_id*
```
Run docker with command:
```
docker run -d --name tg_steam_top_reader --env-file .env -p 5000:5000 redcatfat/tg-steam-top-reader:v1.0
```
