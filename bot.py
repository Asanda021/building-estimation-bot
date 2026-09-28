import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# -----------------------------
# Web Server برای Render
# -----------------------------

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# -----------------------------
# Telegram Bot
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏗️ به ربات برآورد ساختمان خوش آمدید!\n\n"
        "🌍 Welcome to Building Estimation Bot!"
    )


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set")

    # اجرای Web Server در یک Thread جدا
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # ساخت ربات
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    print("Telegram bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
