from cyni import run as run_bot
from dashboard import run_production
import threading

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    run_production()
    bot_thread.join()
    import os

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not set")

# later in the file
bot.run(TOKEN)

