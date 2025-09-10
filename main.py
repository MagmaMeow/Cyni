import os
import threading
import logging

from cyni import run as run_bot
from dashboard import app  # import the Flask app directly

# ---------------------------------------------------------
# Ensure TOKEN exists
# ---------------------------------------------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not set")

# ---------------------------------------------------------
# Bot runner (Discord or similar)
# ---------------------------------------------------------
def start_bot():
    logging.info("🤖 Starting bot...")
    run_bot(TOKEN)  # pass the token into your bot runner

# ---------------------------------------------------------
# Flask runner
# ---------------------------------------------------------
def run_production():
    port = int(os.getenv("PORT", 5000))
    logging.info("🌐 Starting Flask dashboard on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=False)

# ---------------------------------------------------------
# Main entry
# ---------------------------------------------------------
if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    # Run Flask server in main thread
    run_production()

    # Wait for bot thread to finish
    bot_thread.join()
