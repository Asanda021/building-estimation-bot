import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
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
# متن‌ها
# ==========================================

TEXTS = {

    "fa": {
        "welcome": "🏗️ به ربات برآورد ساختمان خوش آمدید!\n\n🌐 زبان خود را انتخاب کنید:",
        "new_estimate": "🏗️ برآورد ساختمان جدید",
        "projects": "📂 پروژه‌های من",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "menu": "🏠 منوی اصلی",

        "enter_area": "📐 مساحت هر طبقه را وارد کنید:\nمثال: 150",
        "enter_floors": "🏢 تعداد طبقات را وارد کنید:\nمثال: 5",
        "enter_basements": "⬇️ تعداد زیرزمین را وارد کنید:\nمثال: 1",

        "choose_structure": "🏗️ نوع سازه را انتخاب کنید:",

        "concrete": "🏢 اسکلت بتنی",
        "steel": "🔩 اسکلت فلزی",

        "building_saved": "✅ اطلاعات ساختمان ثبت شد.",

        "choose_estimation": "📋 چه چیزی را می‌خواهید برآورد کنید؟",

        "concrete_estimate": "🧱 بتن",
        "rebar_estimate": "🔩 میلگرد",
        "both_estimate": "🏗️ بتن و میلگرد",
        "back": "🔙 بازگشت",
    },

    "en": {
        "welcome": "🏗️ Welcome to Building Estimation Bot!\n\n🌐 Choose your language:",
        "new_estimate": "🏗️ New Building Estimate",
        "projects": "📂 My Projects",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "menu": "🏠 Main Menu",

        "enter_area": "📐 Enter the area of each floor:\nExample: 150",
        "enter_floors": "🏢 Enter the number of floors:\nExample: 5",
        "enter_basements": "⬇️ Enter the number of basements:\nExample: 1",

        "choose_structure": "🏗️ Choose the structural system:",

        "concrete": "🏢 Reinforced Concrete",
        "steel": "🔩 Steel Structure",

        "building_saved": "✅ Building information saved.",

        "choose_estimation": "📋 What would you like to estimate?",

        "concrete_estimate": "🧱 Concrete",
        "rebar_estimate": "🔩 Rebar",
        "both_estimate": "🏗️ Concrete & Rebar",
        "back": "🔙 Back",
    }
}


# ==========================================
# /start
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]

    await update.message.reply_text(
        TEXTS["fa"]["welcome"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================
# انتخاب زبان
# ==========================================

async def language_selected(update, context):

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
        [
            InlineKeyboardButton(
                t["new_estimate"],
                callback_data="new_estimate"
            )
        ],
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

    await query.edit_message_text(
        t["menu"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================
# شروع برآورد جدید
# ==========================================

async def start_estimate(update, context):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    context.user_data["step"] = "area"

    await query.edit_message_text(
        TEXTS[lang]["enter_area"]
    )


# ==========================================
# دریافت اطلاعات متنی
# ==========================================

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data.get("language", "fa")
    step = context.user_data.get("step")

    text = update.message.text.strip()

    # --------------------------
    # مساحت
    # --------------------------

    if step == "area":

        try:
            area = float(text)

            if area <= 0:
                raise ValueError

            context.user_data["area"] = area
            context.user_data["step"] = "floors"

            await update.message.reply_text(
                TEXTS[lang]["enter_floors"]
            )

        except ValueError:

            await update.message.reply_text(
                "❌ مقدار واردشده صحیح نیست.\n"
                + TEXTS[lang]["enter_area"]
            )

    # --------------------------
    # تعداد طبقات
    # --------------------------

    elif step == "floors":

        try:
            floors = int(text)

            if floors <= 0:
                raise ValueError

            context.user_data["floors"] = floors
            context.user_data["step"] = "basements"

            await update.message.reply_text(
                TEXTS[lang]["enter_basements"]
            )

        except ValueError:

            await update.message.reply_text(
                "❌ لطفاً یک عدد صحیح وارد کنید.\n"
                + TEXTS[lang]["enter_floors"]
            )

    # --------------------------
    # زیرزمین
    # --------------------------

    elif step == "basements":

        try:
            basements = int(text)

            if basements < 0:
                raise ValueError

            context.user_data["basements"] = basements
            context.user_data["step"] = None

            keyboard = [
                [
                    InlineKeyboardButton(
                        TEXTS[lang]["concrete"],
                        callback_data="structure_concrete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        TEXTS[lang]["steel"],
                        callback_data="structure_steel"
                    )
                ]
            ]

            await update.message.reply_text(
                TEXTS[lang]["choose_structure"],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except ValueError:

            await update.message.reply_text(
                "❌ لطفاً یک عدد صحیح وارد کنید.\n"
                + TEXTS[lang]["enter_basements"]
            )


# ==========================================
# انتخاب نوع سازه
# ==========================================

async def structure_selected(update, context):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    structure = query.data.replace("structure_", "")

    context.user_data["structure"] = structure

    await query.edit_message_text(
        TEXTS[lang]["building_saved"]
    )

    keyboard = [
        [
            InlineKeyboardButton(
                TEXTS[lang]["concrete_estimate"],
                callback_data="estimate_concrete"
            )
        ],
        [
            InlineKeyboardButton(
                TEXTS[lang]["rebar_estimate"],
                callback_data="estimate_rebar"
            )
        ],
        [
            InlineKeyboardButton(
                TEXTS[lang]["both_estimate"],
                callback_data="estimate_both"
            )
        ],
        [
            InlineKeyboardButton(
                TEXTS[lang]["back"],
                callback_data="main_menu"
            )
        ]
    ]

    await query.message.reply_text(
        TEXTS[lang]["choose_estimation"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==========================================
# سایر دکمه‌ها
# ==========================================

async def button_handler(update, context):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    if query.data == "projects":

        text = (
            "📂 پروژه‌های شما\n\nفعلاً پروژه‌ای ثبت نشده است."
            if lang == "fa"
            else
            "📂 Your Projects\n\nNo projects have been saved yet."
        )

        await query.edit_message_text(text)

    elif query.data == "settings":

        text = "⚙️ تنظیمات" if lang == "fa" else "⚙️ Settings"

        await query.edit_message_text(text)

    elif query.data == "help":

        text = (
            "ℹ️ راهنما\n\n"
            "این ربات برای برآورد مصالح و مقادیر ساختمان طراحی شده است."
            if lang == "fa"
            else
            "ℹ️ Help\n\n"
            "This bot is designed for building quantity and material estimation."
        )

        await query.edit_message_text(text)

    elif query.data == "main_menu":

        await show_main_menu(query, lang)

    elif query.data.startswith("estimate_"):

        text = (
            "🔧 این بخش در مرحله بعد ساخته می‌شود."
            if lang == "fa"
            else
            "🔧 This section will be built in the next step."
        )

        await query.edit_message_text(text)


# ==========================================
# اجرای ربات
# ==========================================

def main():

    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set")

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(
            language_selected,
            pattern="^lang_(fa|en)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            start_estimate,
            pattern="^new_estimate$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            structure_selected,
            pattern="^structure_(concrete|steel)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    print("Building Estimation Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
