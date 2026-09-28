import os
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# =========================================================
# Render Web Server
# =========================================================

PORT = int(os.environ.get("PORT", 10000))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Building Estimation Bot is running!")

    def log_message(self, format, *args):
        return


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================================================
# Concrete / Rebar Calculations
# =========================================================

ROOF_CONCRETE_COEFFICIENT = {
    "joof_polistiren": 0.18,
    "joof_safali": 0.20,
    "joof_double": 0.23,
    "chromit": 0.18,
    "composite": 0.15,
    "steel_deck": 0.15,
    "concrete_slab": 0.20,
    "waffle": 0.20,
}

ROOF_NAMES_FA = {
    "joof_polistiren": "تیرچه یونولیتی",
    "joof_safali": "تیرچه سفالی",
    "joof_double": "تیرچه دوبل",
    "chromit": "کرومیت",
    "composite": "کامپوزیت",
    "steel_deck": "عرشه فولادی",
    "concrete_slab": "دال بتنی",
    "waffle": "وافل",
}

ROOF_NAMES_EN = {
    "joof_polistiren": "Polystyrene Joist",
    "joof_safali": "Clay Block Joist",
    "joof_double": "Double Joist",
    "chromit": "Chromite",
    "composite": "Composite",
    "steel_deck": "Steel Deck",
    "concrete_slab": "Concrete Slab",
    "waffle": "Waffle Slab",
}

REBAR_WEIGHT = {
    8: 0.395,
    10: 0.617,
    12: 0.889,
    14: 1.21,
    16: 1.58,
    18: 2.00,
    20: 2.47,
    22: 2.98,
    25: 3.86,
    28: 4.83,
    32: 6.31,
}


def roof_concrete(area, roof_type):
    coefficient = ROOF_CONCRETE_COEFFICIENT.get(roof_type, 0)
    return area * coefficient


def bar_count(length_m):
    return math.ceil(length_m / 12)


def calculate_basic_estimate(data):
    area = data["area"]
    floors = data["floors"]
    basements = data["basements"]

    total_floors = floors + basements
    total_floor_area = area * total_floors

    # These are preliminary estimation coefficients.
    foundation_concrete = area * 0.30
    columns_concrete = total_floor_area * 0.08
    beams_concrete = total_floor_area * 0.10

    roof_type = data.get("roof_type")
    roof_concrete_value = 0

    if roof_type:
        roof_concrete_value = roof_concrete(area, roof_type)

    stairs_concrete = floors * 2.0

    total_concrete = (
        foundation_concrete
        + columns_concrete
        + beams_concrete
        + roof_concrete_value
        + stairs_concrete
    )

    # Preliminary rebar estimation
    foundation_rebar = area * 55
    columns_rebar = total_floor_area * 35
    beams_rebar = total_floor_area * 30
    roof_rebar = area * 12

    total_rebar = (
        foundation_rebar
        + columns_rebar
        + beams_rebar
        + roof_rebar
    )

    number_of_12m_bars = math.ceil(
        total_rebar / (REBAR_WEIGHT[16] * 12)
    )

    return {
        "foundation_concrete": foundation_concrete,
        "columns_concrete": columns_concrete,
        "beams_concrete": beams_concrete,
        "roof_concrete": roof_concrete_value,
        "stairs_concrete": stairs_concrete,
        "total_concrete": total_concrete,
        "foundation_rebar": foundation_rebar,
        "columns_rebar": columns_rebar,
        "beams_rebar": beams_rebar,
        "roof_rebar": roof_rebar,
        "total_rebar": total_rebar,
        "number_of_12m_bars": number_of_12m_bars,
    }


# =========================================================
# Texts
# =========================================================

TEXTS = {

    "fa": {
        "choose_language": "🌐 زبان را انتخاب کنید:",
        "welcome": (
            "🏗️ <b>دستیار برآورد ساختمان</b>\n\n"
            "برای شروع یکی از گزینه‌های زیر را انتخاب کنید."
        ),
        "new_project": "➕ برآورد جدید",
        "my_projects": "📁 پروژه‌های من",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "back": "🔙 بازگشت",
        "choose_type": "نوع برآورد را انتخاب کنید:",
        "concrete": "🧱 بتن",
        "rebar": "🔩 میلگرد",
        "both": "🧱🔩 بتن + میلگرد",
        "enter_area": "📐 متراژ هر طبقه را به مترمربع وارد کنید:",
        "enter_floors": "🏢 تعداد طبقات روی زمین را وارد کنید:",
        "enter_basements": "⬇️ تعداد طبقات زیرزمین را وارد کنید:",
        "choose_structure": "🏗️ نوع سازه را انتخاب کنید:",
        "steel": "سازه فولادی",
        "concrete_structure": "سازه بتنی",
        "choose_roof": "🏠 نوع سقف را انتخاب کنید:",
        "estimate_ready": "✅ برآورد اولیه آماده شد:",
        "invalid_number": "❌ لطفاً فقط عدد وارد کنید.",
        "invalid_positive": "❌ عدد باید صفر یا بیشتر باشد.",
        "projects_empty": "📁 هنوز پروژه‌ای ثبت نشده است.",
        "help_text": (
            "ℹ️ این ربات برای <b>برآورد اولیه</b> مصالح ساختمان طراحی شده است.\n\n"
            "ضرایب تقریبی هستند و برای متره و برآورد اجرایی دقیق باید "
            "نقشه‌های سازه، معماری و جزئیات اجرایی بررسی شوند."
        ),
        "settings_text": "⚙️ تنظیمات در نسخه فعلی ساده است.",
    },

    "en": {
        "choose_language": "🌐 Choose your language:",
        "welcome": (
            "🏗️ <b>Building Estimation Assistant</b>\n\n"
            "Choose an option to start."
        ),
        "new_project": "➕ New Estimate",
        "my_projects": "📁 My Projects",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "back": "🔙 Back",
        "choose_type": "Choose estimation type:",
        "concrete": "🧱 Concrete",
        "rebar": "🔩 Rebar",
        "both": "🧱🔩 Concrete + Rebar",
        "enter_area": "📐 Enter floor area in square meters:",
        "enter_floors": "🏢 Enter number of above-ground floors:",
        "enter_basements": "⬇️ Enter number of basement floors:",
        "choose_structure": "🏗️ Choose structural type:",
        "steel": "Steel Structure",
        "concrete_structure": "Concrete Structure",
        "choose_roof": "🏠 Choose roof type:",
        "estimate_ready": "✅ Preliminary estimate:",
        "invalid_number": "❌ Please enter a number.",
        "invalid_positive": "❌ Number must be zero or greater.",
        "projects_empty": "📁 No projects yet.",
        "help_text": (
            "ℹ️ This bot provides <b>preliminary building estimates</b>.\n\n"
            "The coefficients are approximate. Final quantity takeoff "
            "requires structural, architectural and execution drawings."
        ),
        "settings_text": "⚙️ Settings are currently basic.",
    }
}


# =========================================================
# Keyboard helpers
# =========================================================

def main_menu(lang):
    t = TEXTS[lang]

    keyboard = [
        [InlineKeyboardButton(t["new_project"], callback_data="new_project")],
        [InlineKeyboardButton(t["my_projects"], callback_data="projects")],
        [InlineKeyboardButton(t["settings"], callback_data="settings")],
        [InlineKeyboardButton(t["help"], callback_data="help")],
    ]

    return InlineKeyboardMarkup(keyboard)


def language_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])


def back_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="back_main")]
    ])


# =========================================================
# Start
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        TEXTS["fa"]["choose_language"],
        reply_markup=language_menu()
    )


# =========================================================
# Language
# =========================================================

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("lang_", "")
    context.user_data["lang"] = lang

    await query.edit_message_text(
        TEXTS[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang)
    )


# =========================================================
# New Estimate
# =========================================================

async def new_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "fa")
    context.user_data["step"] = "area"

    await query.edit_message_text(
        TEXTS[lang]["enter_area"],
        reply_markup=back_menu(lang)
    )


# =========================================================
# Main callback handler
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    lang = context.user_data.get("lang", "fa")
    t = TEXTS[lang]

    # Main menu
    if data == "back_main":
        context.user_data["step"] = None

        await query.edit_message_text(
            t["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )
        return

    # New project
    if data == "new_project":
        context.user_data["step"] = "area"

        await query.edit_message_text(
            t["enter_area"],
            reply_markup=back_menu(lang)
        )
        return

    # Estimate type
    if data in ("estimate_concrete", "estimate_rebar", "estimate_both"):
        context.user_data["estimate_type"] = data.replace(
            "estimate_", ""
        )

        context.user_data["step"] = "roof"

        keyboard = [
            [
                InlineKeyboardButton(
                    "تیرچه یونولیتی" if lang == "fa"
                    else "Polystyrene Joist",
                    callback_data="roof_joof_polistiren"
                )
            ],
            [
                InlineKeyboardButton(
                    "تیرچه سفالی" if lang == "fa"
                    else "Clay Block Joist",
                    callback_data="roof_joof_safali"
                )
            ],
            [
                InlineKeyboardButton(
                    "تیرچه دوبل" if lang == "fa"
                    else "Double Joist",
                    callback_data="roof_joof_double"
                )
            ],
            [
                InlineKeyboardButton(
                    "کرومیت" if lang == "fa"
                    else "Chromite",
                    callback_data="roof_chromit"
                )
            ],
            [
                InlineKeyboardButton(
                    "کامپوزیت" if lang == "fa"
                    else "Composite",
                    callback_data="roof_composite"
                )
            ],
            [
                InlineKeyboardButton(
                    "عرشه فولادی" if lang == "fa"
                    else "Steel Deck",
                    callback_data="roof_steel_deck"
                )
            ],
            [
                InlineKeyboardButton(
                    "دال بتنی" if lang == "fa"
                    else "Concrete Slab",
                    callback_data="roof_concrete_slab"
                )
            ],
            [
                InlineKeyboardButton(
                    "وافل" if lang == "fa"
                    else "Waffle Slab",
                    callback_data="roof_waffle"
                )
            ],
        ]

        await query.edit_message_text(
            t["choose_roof"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Roof selection
    if data.startswith("roof_"):
        roof_type = data.replace("roof_", "")

        context.user_data["roof_type"] = roof_type

        result = calculate_basic_estimate(context.user_data)

        estimate_type = context.user_data.get("estimate_type", "both")

        area = context.user_data["area"]
        floors = context.user_data["floors"]
        basements = context.user_data["basements"]
        structure = context.user_data["structure"]

        if lang == "fa":
            structure_name = (
                "سازه فولادی"
                if structure == "steel"
                else "سازه بتنی"
            )

            roof_name = ROOF_NAMES_FA[roof_type]

            message = (
                "✅ <b>برآورد اولیه آماده شد</b>\n\n"
                f"📐 متراژ هر طبقه: <b>{area:,.0f}</b> مترمربع\n"
                f"🏢 طبقات روی زمین: <b>{floors}</b>\n"
                f"⬇️ زیرزمین: <b>{basements}</b>\n"
                f"🏗️ سازه: <b>{structure_name}</b>\n"
                f"🏠 سقف: <b>{roof_name}</b>\n\n"
            )

            if estimate_type in ("concrete", "both"):
                message += (
                    "🧱 <b>بتن</b>\n"
                    f"فونداسیون: {result['foundation_concrete']:.2f} m³\n"
                    f"ستون‌ها: {result['columns_concrete']:.2f} m³\n"
                    f"تیرها: {result['beams_concrete']:.2f} m³\n"
                    f"سقف: {result['roof_concrete']:.2f} m³\n"
                    f"پله: {result['stairs_concrete']:.2f} m³\n"
                    f"<b>جمع بتن: {result['total_concrete']:.2f} m³</b>\n\n"
                )

            if estimate_type in ("rebar", "both"):
                message += (
                    "🔩 <b>میلگرد</b>\n"
                    f"فونداسیون: {result['foundation_rebar']:,.0f} kg\n"
                    f"ستون‌ها: {result['columns_rebar']:,.0f} kg\n"
                    f"تیرها: {result['beams_rebar']:,.0f} kg\n"
                    f"سقف: {result['roof_rebar']:,.0f} kg\n"
                    f"<b>جمع میلگرد: {result['total_rebar']:,.0f} kg</b>\n"
                    f"تقریبی: <b>{result['number_of_12m_bars']:,}</b> شاخه ۱۲ متری\n\n"
                )

            message += (
                "⚠️ این اعداد <b>برآورد اولیه</b> هستند و "
                "جایگزین متره دقیق نقشه‌های اجرایی نیستند."
            )

        else:
            structure_name = (
                "Steel Structure"
                if structure == "steel"
                else "Concrete Structure"
            )

            roof_name = ROOF_NAMES_EN[roof_type]

            message = (
                "✅ <b>Preliminary Estimate</b>\n\n"
                f"📐 Floor area: <b>{area:,.0f}</b> m²\n"
                f"🏢 Above-ground floors: <b>{floors}</b>\n"
                f"⬇️ Basements: <b>{basements}</b>\n"
                f"🏗️ Structure: <b>{structure_name}</b>\n"
                f"🏠 Roof: <b>{roof_name}</b>\n\n"
            )

            if estimate_type in ("concrete", "both"):
                message += (
                    "🧱 <b>Concrete</b>\n"
                    f"Foundation: {result['foundation_concrete']:.2f} m³\n"
                    f"Columns: {result['columns_concrete']:.2f} m³\n"
                    f"Beams: {result['beams_concrete']:.2f} m³\n"
                    f"Roof: {result['roof_concrete']:.2f} m³\n"
                    f"Stairs: {result['stairs_concrete']:.2f} m³\n"
                    f"<b>Total concrete: {result['total_concrete']:.2f} m³</b>\n\n"
                )

            if estimate_type in ("rebar", "both"):
                message += (
                    "🔩 <b>Rebar</b>\n"
                    f"Foundation: {result['foundation_rebar']:,.0f} kg\n"
                    f"Columns: {result['columns_rebar']:,.0f} kg\n"
                    f"Beams: {result['beams_rebar']:,.0f} kg\n"
                    f"Roof: {result['roof_rebar']:,.0f} kg\n"
                    f"<b>Total rebar: {result['total_rebar']:,.0f} kg</b>\n"
                    f"Approx.: <b>{result['number_of_12m_bars']:,}</b> bars of 12 m\n\n"
                )

            message += (
                "⚠️ These are <b>preliminary estimates</b> and "
                "do not replace detailed quantity takeoff."
            )

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=back_menu(lang)
        )
        return

    # Projects
    if data == "projects":
        await query.edit_message_text(
            t["projects_empty"],
            reply_markup=back_menu(lang)
        )
        return

    # Settings
    if data == "settings":
        await query.edit_message_text(
            t["settings_text"],
            reply_markup=back_menu(lang)
        )
        return

    # Help
    if data == "help":
        await query.edit_message_text(
            t["help_text"],
            parse_mode="HTML",
            reply_markup=back_menu(lang)
        )
        return


# =========================================================
# Text input
# =========================================================

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    t = TEXTS[lang]

    text = update.message.text.strip()
    step = context.user_data.get("step")

    # Area
    if step == "area":
        try:
            area = float(text.replace(",", "."))
            if area <= 0:
                raise ValueError

            context.user_data["area"] = area
            context.user_data["step"] = "floors"

            await update.message.reply_text(
                t["enter_floors"],
                reply_markup=back_menu(lang)
            )

        except ValueError:
            await update.message.reply_text(t["invalid_number"])

        return

    # Floors
    if step == "floors":
        try:
            floors = int(text)

            if floors <= 0:
                raise ValueError

            context.user_data["floors"] = floors
            context.user_data["step"] = "basements"

            await update.message.reply_text(
                t["enter_basements"],
                reply_markup=back_menu(lang)
            )

        except ValueError:
            await update.message.reply_text(t["invalid_number"])

        return

    # Basements
    if step == "basements":
        try:
            basements = int(text)

            if basements < 0:
                raise ValueError

            context.user_data["basements"] = basements
            context.user_data["step"] = "structure"

            keyboard = [
                [
                    InlineKeyboardButton(
                        t["steel"],
                        callback_data="structure_steel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        t["concrete_structure"],
                        callback_data="structure_concrete"
                    )
                ],
            ]

            await update.message.reply_text(
                t["choose_structure"],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except ValueError:
            await update.message.reply_text(t["invalid_number"])

        return


# =========================================================
# Structure selection
# =========================================================

async def structure_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "fa")
    t = TEXTS[lang]

    structure = query.data.replace("structure_", "")

    context.user_data["structure"] = structure
    context.user_data["step"] = "estimate_type"

    keyboard = [
        [
            InlineKeyboardButton(
                t["concrete"],
                callback_data="estimate_concrete"
            )
        ],
        [
            InlineKeyboardButton(
                t["rebar"],
                callback_data="estimate_rebar"
            )
        ],
        [
            InlineKeyboardButton(
                t["both"],
                callback_data="estimate_both"
            )
        ],
    ]

    await query.edit_message_text(
        t["choose_type"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# Main
# =========================================================

def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    # Render needs an open HTTP port.
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )
    web_thread.start()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        CallbackQueryHandler(
            select_language,
            pattern=r"^lang_(fa|en)$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            structure_selected,
            pattern=r"^structure_(steel|concrete)$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    print("Building Estimation Bot started successfully.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
