import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging to see errors in the console/log file
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# httpx logs full request URLs at INFO, and Telegram URLs contain the bot token
logging.getLogger("httpx").setLevel(logging.WARNING)

# Define conversation states
LATITUDE, LONGITUDE = range(2)

# Helper function to check if the input is a valid coordinate number
def is_valid_coordinate(text: str) -> bool:
    try:
        float(text.strip())
        return True
    except ValueError:
        return False

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

        # Success response sending the requested short link
        await update.message.reply_text(
            "🎉 Coordinates accepted! Here is your link:\n"
            "https://www.youtube.com/shorts/St5pdFmoFe4"
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

def main():
    # Token comes from the environment (Railway "Variables" tab) so it never lives in the repo
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        raise SystemExit("BOT_TOKEN environment variable is not set.")

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
    main()
