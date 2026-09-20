# Telegram coordinates bot

Asks for a latitude and longitude via `/start`, then replies with a link.
Uses long polling, so it runs as a worker (no web port needed).

## Configuration

| Variable    | Required | Purpose                                              |
|-------------|----------|------------------------------------------------------|
| `BOT_TOKEN` | yes      | Token from @BotFather                                |
| `PROXY_URL` | no       | Only for PythonAnywhere free: `http://proxy.server:3128` |

## Run locally

```powershell
pip install -r requirements.txt
$env:BOT_TOKEN = "<your token>"
python bot.py
```

## Deploy on Railway

1. Push this repo to GitHub.
2. Railway → New Project → Deploy from GitHub repo.
3. Service → Variables → add `BOT_TOKEN`.
4. Deploy. `railway.json` sets the start command and auto-restart.

Only one instance can poll a given token at a time. Stop any other copy
(PythonAnywhere console, local run) or you'll get `Conflict: terminated by
other getUpdates request` errors.
