import logging
import os
from telegram import Update
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
    await update.message.reply_text("🌐 Let's get started!\n\n**Step 1:** Please enter the latitude:")
    return LATITUDE

async def process_latitude(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates and saves latitude, then asks for longitude."""
    user_input = update.message.text.strip()
    
    if is_valid_coordinate(user_input):
        context.user_data['latitude'] = user_input
        await update.message.reply_text("✅ Latitude saved.\n\n**Step 2:** Please enter the longitude:")
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
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Invalid input. Please enter a valid number for longitude (e.g., 80.2707 or 12.5):")
        return LONGITUDE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Process cancelled. Type /start to try again.")
    return ConversationHandler.END

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

    # Manage step-by-step user input flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LATITUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_latitude)],
            LONGITUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_longitude)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()