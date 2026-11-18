import logging
import os
from pathlib import Path
from urllib.parse import quote

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Define conversation states
LATITUDE, LONGITUDE = range(2)

# The one coordinate pair that unlocks the next clue
SECRET_LATITUDE = 43.91522763578687
SECRET_LONGITUDE = -113.61173108716417
SECRET_LINK = "https://youtu.be/ZKcN9mXCPP0"
SECRET_DESCRIPTION = "go with 37 with the number where lilly is locked"


class TokenRedactingFormatter(logging.Formatter):
    def __init__(self, token: str) -> None:
        super().__init__("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.token = token
        self.encoded_token = quote(token, safe="")

    def format(self, record: logging.LogRecord) -> str:
        # Format first so exception messages and chained tracebacks are redacted too.
        message = super().format(record)
        return message.replace(self.token, "[REDACTED]").replace(self.encoded_token, "[REDACTED]")


# Helper function to check if the input is a valid coordinate number
def is_valid_coordinate(text: str) -> bool:
    try:
        float(text.strip())
        return True
    except ValueError:
        return False

def is_secret_location(latitude: str, longitude: str) -> bool:
    """True only for the exact secret coordinates.

    Both numbers must be entered in full; a shortened or rounded version
    such as 43.9152 does not count.
    """
    return float(latitude) == SECRET_LATITUDE and float(longitude) == SECRET_LONGITUDE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for latitude."""
    # A repeat /start restarts cleanly instead of reusing half-filled data
    context.user_data.clear()
    await update.message.reply_text(
        "🌐 Let's get started!\n\n<b>Step 1:</b> Please enter the latitude:",
        parse_mode=ParseMode.HTML,
    )
    return LATITUDE

async def process_latitude(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates and saves latitude, then asks for longitude."""
    user_input = update.message.text.strip()

    if is_valid_coordinate(user_input):
        context.user_data['latitude'] = user_input
        await update.message.reply_text(
            "✅ Latitude saved.\n\n<b>Step 2:</b> Please enter the longitude:",
            parse_mode=ParseMode.HTML,
        )
        return LONGITUDE
    else:
        await update.message.reply_text("❌ Invalid input. Please enter a valid number for latitude (e.g., 13.0827 or -45.2):")
        return LATITUDE

async def process_longitude(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates longitude and returns the YouTube short link."""
    user_input = update.message.text.strip()

    if is_valid_coordinate(user_input):
        context.user_data['longitude'] = user_input

        # Only the secret pair unlocks the link and its clue
        if is_secret_location(context.user_data['latitude'], user_input):
            await update.message.reply_text(
                "🎉 Coordinates accepted! Here is your link:\n"
                f"{SECRET_LINK}\n\n"
                f"{SECRET_DESCRIPTION}"
            )
        else:
            await update.message.reply_text(
                "Coordinates not accepted. Type /start to try again."
            )
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Invalid input. Please enter a valid number for longitude (e.g., 80.2707 or 12.5):")
        return LONGITUDE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    context.user_data.clear()
    await update.message.reply_text("Process cancelled. Type /start to try again.")
    return ConversationHandler.END

async def outside_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Replies to anything sent when no conversation is active, so the bot is never silent."""
    await update.message.reply_text("Type /start to enter coordinates.")

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs errors instead of letting them crash the bot."""
    logging.error("Unhandled error while processing an update", exc_info=context.error)

def load_bot_token() -> str:
    token = os.environ.get("BOT_TOKEN")
    if token:
        return token

    base_dir = Path(__file__).resolve().parent
    try:
        with (base_dir / ".env").open(encoding="utf-8-sig") as env_file:
            for line in env_file:
                if line.strip().startswith("BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except (OSError, UnicodeError):
        pass
    if token:
        return token

    try:
        return (base_dir / "key.txt").read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        return ""

def main():
    TOKEN = load_bot_token()
    if not TOKEN:
        raise SystemExit("Set BOT_TOKEN in the environment or .env before starting the bot.")

    handler = logging.StreamHandler()
    handler.setFormatter(TokenRedactingFormatter(TOKEN))
    logging.basicConfig(handlers=[handler], level=logging.INFO)
    # httpx logs full request URLs at INFO, and Telegram URLs contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Optional: only PythonAnywhere free accounts need a proxy (http://proxy.server:3128)
    PROXY_URL = os.environ.get("PROXY_URL")

    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        builder = builder.proxy_url(PROXY_URL).get_updates_proxy_url(PROXY_URL)
    app = builder.build()

    app.add_error_handler(on_error)

    # Manage step-by-step user input flow.
    # allow_reentry lets /start restart the flow while a conversation is still
    # open; without it the entry point is skipped and /start is silently ignored.
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LATITUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_latitude)],
            LONGITUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_longitude)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, outside_conversation))

    print("Bot is running...")
    # State lives in memory, so updates queued during a restart refer to a flow
    # that no longer exists; dropping them avoids answering out of step.
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Bot stopped due to an unexpected error")
        raise SystemExit(1) from None
