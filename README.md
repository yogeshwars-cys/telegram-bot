# Telegram coordinates bot

Asks for a latitude and longitude via `/start`. Only the exact pair
`43.91522763578687`, `-113.61173108716417` receives the YouTube link.
Other coordinates receive no link.
Uses long polling, so it runs as a worker (no web port needed).

## Configuration

| Variable    | Required | Purpose                                              |
|-------------|----------|------------------------------------------------------|
| `BOT_TOKEN` | yes      | Token from @BotFather                                |
| `PROXY_URL` | no       | Only for PythonAnywhere free: `http://proxy.server:3128` |

## Run locally

From the repository folder, install the dependency:

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file in this folder with one line (no quotes):

```text
BOT_TOKEN=your_token_from_BotFather
```

The `.env` file is ignored by Git. Load the token into the current PowerShell
session and start the bot:

```powershell
$env:BOT_TOKEN = ((Get-Content .env -Raw).Trim() -replace '^BOT_TOKEN=', '')
python bot.py
```

Keep this terminal open while testing. In Telegram, send `/start` to your bot,
then send `43.91522763578687` and `-113.61173108716417` as separate messages.
The reply should contain `https://youtu.be/ZKcN9mXCPP0`. Any other valid pair
receives a rejection without a link. Press `Ctrl+C` in the terminal to stop the bot.

## Deploy on Railway

1. Push this repo to GitHub.
2. Railway → New Project → Deploy from GitHub repo.
3. Service → Variables → add `BOT_TOKEN`.
4. Deploy. `railway.json` sets the start command and auto-restart.

Only one instance can poll a given token at a time. Stop any other copy
(PythonAnywhere console, local run) or you'll get `Conflict: terminated by
other getUpdates request` errors.

## Troubleshooting

**`/start` works once, then the bot goes silent.**
The conversation is still open on an earlier `/start`, so the flow is waiting for a
coordinate, not a command. `allow_reentry=True` on the `ConversationHandler` makes a
repeat `/start` restart the flow; `/cancel` also closes it. Without that flag the entry
point is never re-checked while a conversation is active, and the command is dropped.

**`Conflict: terminated by other getUpdates request` in the logs.**
Two processes are polling the same token and each one steals half the updates, so replies
land in whichever copy has no conversation state. Leave exactly one running — check for an
old Railway deployment, a second service or replica, and any local or PythonAnywhere copy.
