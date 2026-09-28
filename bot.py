import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# ==========================================
# Web Server برای Render
# ==========================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Building Estimation Bot is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# ==========================================
# متن‌های ربات
# ==========================================

TEXTS = {

    "fa": {
        "welcome": "🏗️ به ربات برآورد ساختمان خوش آمدید!\n\n🌐 زبان خود را انتخاب کنید:",
        "new_estimate": "🏗️ برآورد ساختمان جدید",
        "projects": "📂 پروژه‌های من",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "menu": "🏠 منوی اصلی",
    },

    "en": {
        "welcome": "🏗️ Welcome to Building Estimation Bot!\n\n🌐 Choose your language:",
        "new_estimate": "🏗️ New Building Estimate",
        "projects": "📂 My Projects",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "menu": "🏠 Main Menu",
    }
}


# ==========================================
# /start
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        TEXTS["fa"]["welcome"],
        reply_markup=reply_markup
    )


# ==========================================
# انتخاب زبان
# ==========================================

async def language_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    lang = query.data.replace("lang_", "")

    context.user_data["language"] = lang

    await show_main_menu(query, lang)


# ==========================================
# منوی اصلی
# ==========================================

async def show_main_menu(query, lang):

    t = TEXTS[lang]

    keyboard = [
        [InlineKeyboardButton(
            t["new_estimate"],
            callback_data="new_estimate"
        )],

        [
            InlineKeyboardButton(
                t["projects"],
                callback_data="projects"
            )
        ],

        [
            InlineKeyboardButton(
                t["settings"],
                callback_data="settings"
            ),

            InlineKeyboardButton(
                t["help"],
                callback_data="help"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        t["menu"],
        reply_markup=reply_markup
    )


# ==========================================
# مدیریت دکمه‌ها
# ==========================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    if query.data == "new_estimate":

        if lang == "fa":
            text = "🏗️ برآورد ساختمان جدید\n\nبه‌زودی اطلاعات ساختمان را از شما می‌گیریم."
        else:
            text = "🏗️ New Building Estimate\n\nWe will collect the building information here."

        await query.edit_message_text(text)

    elif query.data == "projects":

        if lang == "fa":
            text = "📂 پروژه‌های شما\n\nفعلاً پروژه‌ای ثبت نشده است."
        else:
            text = "📂 Your Projects\n\nNo projects have been saved yet."

        await query.edit_message_text(text)

    elif query.data == "settings":

        if lang == "fa":
            text = "⚙️ تنظیمات"
        else:
            text = "⚙️ Settings"

        await query.edit_message_text(text)

    elif query.data == "help":

        if lang == "fa":
            text = (
                "ℹ️ راهنما\n\n"
                "این ربات برای برآورد مصالح و مقادیر ساختمان طراحی شده است."
            )
        else:
            text = (
                "ℹ️ Help\n\n"
                "This bot is designed for building quantity and material estimation."
            )

        await query.edit_message_text(text)


# ==========================================
# اجرای اصلی
# ==========================================

def main():

    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set")

    # Web Server برای Render
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # ساخت ربات
    app = Application.builder().token(token).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))

    # انتخاب زبان
    app.add_handler(
        CallbackQueryHandler(
            language_selected,
            pattern="^lang_(fa|en)$"
        )
    )

    # سایر دکمه‌ها
    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    print("Building Estimation Bot is running...")

    app.run_polling()


# ==========================================

if __name__ == "__main__":
    main()
