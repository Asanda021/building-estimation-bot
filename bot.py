import os
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

from calculations import (
    isolated_footing,
    strip_footing,
    raft_foundation,
)


# =========================================================
# Render Web Server
# =========================================================

PORT = int(os.environ.get("PORT", 10000))


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-type",
            "text/plain; charset=utf-8"
        )
        self.end_headers()
        self.wfile.write(
            b"Building Estimation Bot is running!"
        )

    def log_message(self, format, *args):
        return


def run_web_server():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )
    server.serve_forever()


# =========================================================
# Texts
# =========================================================

TEXTS = {

    "fa": {

        "language": "🌐 زبان را انتخاب کنید:",

        "welcome":
            "🏗️ <b>دستیار برآورد ساختمان</b>\n\n"
            "یک گزینه را انتخاب کنید:",

        "new":
            "➕ برآورد جدید",

        "help":
            "ℹ️ راهنما",

        "back":
            "🔙 بازگشت",

        "choose_foundation":
            "🏗️ نوع فونداسیون را انتخاب کنید:",

        "isolated":
            "⬛ فونداسیون منفرد",

        "strip":
            "▬ فونداسیون نواری",

        "raft":
            "▰ فونداسیون گسترده (رادیه)",

        "enter":
            "مقدار را وارد کنید:",

        "invalid":
            "❌ مقدار واردشده صحیح نیست. دوباره وارد کنید.",

        "help_text":
            "این ربات برای متره و برآورد مصالح ساختمان "
            "بر اساس اطلاعات واقعی پروژه طراحی می‌شود.\n\n"
            "ربات خودش ابعاد یا آرماتور سازه را حدس نمی‌زند.",

        "done":
            "✅ <b>برآورد فونداسیون</b>\n\n",

    },

    "en": {

        "language": "🌐 Choose language:",

        "welcome":
            "🏗️ <b>Building Estimation Assistant</b>\n\n"
            "Choose an option:",

        "new":
            "➕ New Estimate",

        "help":
            "ℹ️ Help",

        "back":
            "🔙 Back",

        "choose_foundation":
            "🏗️ Choose foundation type:",

        "isolated":
            "⬛ Isolated Footing",

        "strip":
            "▬ Strip Footing",

        "raft":
            "▰ Raft Foundation",

        "enter":
            "Enter the value:",

        "invalid":
            "❌ Invalid value. Please try again.",

        "help_text":
            "This bot estimates building materials "
            "from actual project data.\n\n"
            "It does not guess structural dimensions or reinforcement.",

        "done":
            "✅ <b>Foundation Estimate</b>\n\n",
    }
}


# =========================================================
# Keyboard
# =========================================================

def main_menu(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t["new"],
                callback_data="new_estimate"
            )
        ],
        [
            InlineKeyboardButton(
                t["help"],
                callback_data="help"
            )
        ]
    ])


def back_button(lang):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                TEXTS[lang]["back"],
                callback_data="back"
            )
        ]
    ])


def language_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🇮🇷 فارسی",
                callback_data="lang_fa"
            ),
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_en"
            )
        ]
    ])


def foundation_menu(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t["isolated"],
                callback_data="foundation_isolated"
            )
        ],
        [
            InlineKeyboardButton(
                t["strip"],
                callback_data="foundation_strip"
            )
        ],
        [
            InlineKeyboardButton(
                t["raft"],
                callback_data="foundation_raft"
            )
        ],
        [
            InlineKeyboardButton(
                t["back"],
                callback_data="back"
            )
        ]
    ])


# =========================================================
# Start
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        TEXTS["fa"]["language"],
        reply_markup=language_menu()
    )


# =========================================================
# Language
# =========================================================

async def language_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    lang = query.data.replace(
        "lang_",
        ""
    )

    context.user_data["lang"] = lang

    await query.edit_message_text(
        TEXTS[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang)
    )


# =========================================================
# New Estimate
# =========================================================

async def new_estimate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    context.user_data.clear()
    context.user_data["lang"] = lang

    await query.edit_message_text(
        TEXTS[lang]["choose_foundation"],
        reply_markup=foundation_menu(lang)
    )


# =========================================================
# Foundation Selection
# =========================================================

async def foundation_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    foundation = query.data.replace(
        "foundation_",
        ""
    )

    context.user_data["foundation"] = foundation

    # -----------------------------------------------------
    # Isolated
    # -----------------------------------------------------

    if foundation == "isolated":

        context.user_data["step"] = "iso_count"

        await query.edit_message_text(
            (
                "🔢 تعداد پی‌ها را وارد کنید:"
                if lang == "fa"
                else "🔢 Enter number of footings:"
            ),
            reply_markup=back_button(lang)
        )

        return

    # -----------------------------------------------------
    # Strip
    # -----------------------------------------------------

    if foundation == "strip":

        context.user_data["step"] = "strip_count"

        await query.edit_message_text(
            (
                "🔢 تعداد نوارها را وارد کنید:"
                if lang == "fa"
                else "🔢 Enter number of strips:"
            ),
            reply_markup=back_button(lang)
        )

        return

    # -----------------------------------------------------
    # Raft
    # -----------------------------------------------------

    if foundation == "raft":

        context.user_data["step"] = "raft_length"

        await query.edit_message_text(
            (
                "📏 طول رادیه را بر حسب متر وارد کنید:"
                if lang == "fa"
                else "📏 Enter raft length in meters:"
            ),
            reply_markup=back_button(lang)
        )

        return


# =========================================================
# Text Input
# =========================================================

async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    step = context.user_data.get(
        "step"
    )

    text = update.message.text.strip()

    try:

        value = float(
            text.replace(",", ".")
        )

        if value < 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            TEXTS[lang]["invalid"]
        )

        return

    # =====================================================
    # ISOLATED FOOTING
    # =====================================================

    if step == "iso_count":

        context.user_data["iso_count"] = int(value)
        context.user_data["step"] = "iso_length"

        await update.message.reply_text(
            "📏 طول پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else "📏 Enter footing length in meters:"
        )

        return

    if step == "iso_length":

        context.user_data["iso_length"] = value
        context.user_data["step"] = "iso_width"

        await update.message.reply_text(
            "📐 عرض پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else "📐 Enter footing width in meters:"
        )

        return

    if step == "iso_width":

        context.user_data["iso_width"] = value
        context.user_data["step"] = "iso_thickness"

        await update.message.reply_text(
            "📐 ضخامت پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else "📐 Enter footing thickness in meters:"
        )

        return

    if step == "iso_thickness":

        context.user_data["iso_thickness"] = value
        context.user_data["step"] = "iso_mager_length"

        await update.message.reply_text(
            "📏 طول بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📏 Enter lean concrete length:"
        )

        return

    if step == "iso_mager_length":

        context.user_data["iso_mager_length"] = value
        context.user_data["step"] = "iso_mager_width"

        await update.message.reply_text(
            "📐 عرض بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete width:"
        )

        return

    if step == "iso_mager_width":

        context.user_data["iso_mager_width"] = value
        context.user_data["step"] = "iso_mager_thickness"

        await update.message.reply_text(
            "📐 ضخامت بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete thickness:"
        )

        return

    if step == "iso_mager_thickness":

        context.user_data["iso_mager_thickness"] = value
        context.user_data["step"] = "iso_bottom_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else "🔩 Enter bottom rebar diameter (mm):"
        )

        return

    if step == "iso_bottom_diameter":

        context.user_data["iso_bottom_diameter"] = int(value)
        context.user_data["step"] = "iso_bottom_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else "📏 Enter bottom rebar spacing (mm):"
        )

        return

    if step == "iso_bottom_spacing":

        context.user_data["iso_bottom_spacing"] = int(value)

        try:

            result = isolated_footing(
                count=context.user_data["iso_count"],
                length_m=context.user_data["iso_length"],
                width_m=context.user_data["iso_width"],
                thickness_m=context.user_data["iso_thickness"],

                lean_concrete_length_m=context.user_data["iso_mager_length"],
                lean_concrete_width_m=context.user_data["iso_mager_width"],
                lean_concrete_thickness_m=context.user_data["iso_mager_thickness"],

                bottom_diameter_mm=context.user_data["iso_bottom_diameter"],
                bottom_spacing_mm=context.user_data["iso_bottom_spacing"],
            )

            message = (
                TEXTS[lang]["done"]
                +
                f"🧱 بتن مگر: "
                f"{result['lean_concrete_m3']:.2f} m³\n"
                f"🧱 بتن پی: "
                f"{result['footing_concrete_m3']:.2f} m³\n"
                f"🧱 جمع بتن: "
                f"<b>{result['total_concrete_m3']:.2f} m³</b>\n\n"
                f"🔩 میلگرد شبکه پایین: "
                f"{result['bottom_rebar_weight_kg']:.1f} kg\n"
                f"📦 شاخه ۱۲ متری: "
                f"{result['bottom_bars_12m']}\n\n"
                "⚠️ بر اساس اطلاعات واردشده."
            )

            context.user_data["step"] = None

            await update.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=back_button(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}"
            )

        return

    # =====================================================
    # STRIP FOOTING
    # =====================================================

    if step == "strip_count":

        context.user_data["strip_count"] = int(value)
        context.user_data["step"] = "strip_length"

        await update.message.reply_text(
            "📏 طول هر نوار را وارد کنید:"
            if lang == "fa"
            else "📏 Enter strip length:"
        )

        return

    if step == "strip_length":

        context.user_data["strip_length"] = value
        context.user_data["step"] = "strip_width"

        await update.message.reply_text(
            "📐 عرض فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else "📐 Enter strip footing width:"
        )

        return

    if step == "strip_width":

        context.user_data["strip_width"] = value
        context.user_data["step"] = "strip_thickness"

        await update.message.reply_text(
            "📐 ضخامت فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else "📐 Enter strip footing thickness:"
        )

        return

    if step == "strip_thickness":

        context.user_data["strip_thickness"] = value
        context.user_data["step"] = "strip_lean_length"

        await update.message.reply_text(
            "📏 طول بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📏 Enter lean concrete length:"
        )

        return

    if step == "strip_lean_length":

        context.user_data["strip_lean_length"] = value
        context.user_data["step"] = "strip_lean_width"

        await update.message.reply_text(
            "📐 عرض بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete width:"
        )

        return

    if step == "strip_lean_width":

        context.user_data["strip_lean_width"] = value
        context.user_data["step"] = "strip_lean_thickness"

        await update.message.reply_text(
            "📐 ضخامت بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete thickness:"
        )

        return

    if step == "strip_lean_thickness":

        context.user_data["strip_lean_thickness"] = value
        context.user_data["step"] = "strip_long_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد طولی را وارد کنید (mm):"
            if lang == "fa"
            else "🔩 Enter longitudinal rebar diameter (mm):"
        )

        return

    if step == "strip_long_diameter":

        context.user_data["strip_long_diameter"] = int(value)
        context.user_data["step"] = "strip_long_count"

        await update.message.reply_text(
            "🔢 تعداد میلگردهای طولی را وارد کنید:"
            if lang == "fa"
            else "🔢 Enter number of longitudinal bars:"
        )

        return

    if step == "strip_long_count":

        context.user_data["strip_long_count"] = int(value)
        context.user_data["step"] = "strip_trans_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد عرضی را وارد کنید (mm):"
            if lang == "fa"
            else "🔩 Enter transverse rebar diameter (mm):"
        )

        return

    if step == "strip_trans_diameter":

        context.user_data["strip_trans_diameter"] = int(value)
        context.user_data["step"] = "strip_trans_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای عرضی را وارد کنید (mm):"
            if lang == "fa"
            else "📏 Enter transverse rebar spacing (mm):"
        )

        return

    if step == "strip_trans_spacing":

        context.user_data["strip_trans_spacing"] = int(value)

        try:

            result = strip_footing(
                strip_count=context.user_data["strip_count"],
                strip_length_m=context.user_data["strip_length"],
                footing_width_m=context.user_data["strip_width"],
                footing_thickness_m=context.user_data["strip_thickness"],

                lean_length_m=context.user_data["strip_lean_length"],
                lean_width_m=context.user_data["strip_lean_width"],
                lean_thickness_m=context.user_data["strip_lean_thickness"],

                longitudinal_diameter_mm=context.user_data["strip_long_diameter"],
                longitudinal_count=context.user_data["strip_long_count"],

                transverse_diameter_mm=context.user_data["strip_trans_diameter"],
                transverse_spacing_mm=context.user_data["strip_trans_spacing"],
            )

            message = (
                TEXTS[lang]["done"]
                +
                f"🧱 بتن مگر: "
                f"{result['lean_concrete_m3']:.2f} m³\n"
                f"🧱 بتن فونداسیون: "
                f"{result['footing_concrete_m3']:.2f} m³\n"
                f"🧱 جمع بتن: "
                f"<b>{result['total_concrete_m3']:.2f} m³</b>\n\n"
                f"🔩 میلگرد طولی: "
                f"{result['longitudinal_rebar_weight_kg']:.1f} kg\n"
                f"🔩 میلگرد عرضی: "
                f"{result['transverse_rebar_weight_kg']:.1f} kg\n"
                f"🔩 جمع میلگرد: "
                f"<b>{result['total_rebar_kg']:.1f} kg</b>\n\n"
                f"📦 شاخه طولی ۱۲ متری: "
                f"{result['longitudinal_bars_12m']}\n"
                f"📦 شاخه عرضی ۱۲ متری: "
                f"{result['transverse_bars_12m']}\n"
            )

            context.user_data["step"] = None

            await update.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=back_button(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}"
            )

        return

    # =====================================================
    # RAFT
    # =====================================================

    if step == "raft_length":

        context.user_data["raft_length"] = value
        context.user_data["step"] = "raft_width"

        await update.message.reply_text(
            "📐 عرض رادیه را وارد کنید:"
            if lang == "fa"
            else "📐 Enter raft width:"
        )

        return

    if step == "raft_width":

        context.user_data["raft_width"] = value
        context.user_data["step"] = "raft_thickness"

        await update.message.reply_text(
            "📐 ضخامت رادیه را وارد کنید:"
            if lang == "fa"
            else "📐 Enter raft thickness:"
        )

        return

    if step == "raft_thickness":

        context.user_data["raft_thickness"] = value
        context.user_data["step"] = "raft_lean_length"

        await update.message.reply_text(
            "📏 طول بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📏 Enter lean concrete length:"
        )

        return

    if step == "raft_lean_length":

        context.user_data["raft_lean_length"] = value
        context.user_data["step"] = "raft_lean_width"

        await update.message.reply_text(
            "📐 عرض بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete width:"
        )

        return

    if step == "raft_lean_width":

        context.user_data["raft_lean_width"] = value
        context.user_data["step"] = "raft_lean_thickness"

        await update.message.reply_text(
            "📐 ضخامت بتن مگر را وارد کنید:"
            if lang == "fa"
            else "📐 Enter lean concrete thickness:"
        )

        return

    if step == "raft_lean_thickness":

        context.user_data["raft_lean_thickness"] = value
        context.user_data["step"] = "raft_bottom_x_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else "🔩 Enter bottom X rebar diameter:"
        )

        return

    if step == "raft_bottom_x_diameter":

        context.user_data["raft_bottom_x_diameter"] = int(value)
        context.user_data["step"] = "raft_bottom_x_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else "📏 Enter bottom X spacing:"
        )

        return

    if step == "raft_bottom_x_spacing":

        context.user_data["raft_bottom_x_spacing"] = int(value)
        context.user_data["step"] = "raft_bottom_y_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else "🔩 Enter bottom Y rebar diameter:"
        )

        return

    if step == "raft_bottom_y_diameter":

        context.user_data["raft_bottom_y_diameter"] = int(value)
        context.user_data["step"] = "raft_bottom_y_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else "📏 Enter bottom Y spacing:"
        )

        return

    if step == "raft_bottom_y_spacing":

        context.user_data["raft_bottom_y_spacing"] = int(value)

        try:

            result = raft_foundation(
                length_m=context.user_data["raft_length"],
                width_m=context.user_data["raft_width"],
                thickness_m=context.user_data["raft_thickness"],

                lean_length_m=context.user_data["raft_lean_length"],
                lean_width_m=context.user_data["raft_lean_width"],
                lean_thickness_m=context.user_data["raft_lean_thickness"],

                bottom_x_diameter_mm=context.user_data[
                    "raft_bottom_x_diameter"
                ],
                bottom_x_spacing_mm=context.user_data[
                    "raft_bottom_x_spacing"
                ],

                bottom_y_diameter_mm=context.user_data[
                    "raft_bottom_y_diameter"
                ],
                bottom_y_spacing_mm=context.user_data[
                    "raft_bottom_y_spacing"
                ],
            )

            message = (
                TEXTS[lang]["done"]
                +
                f"🧱 بتن مگر: "
                f"{result['lean_concrete_m3']:.2f} m³\n"
                f"🧱 بتن رادیه: "
                f"{result['raft_concrete_m3']:.2f} m³\n"
                f"🧱 جمع بتن: "
                f"<b>{result['total_concrete_m3']:.2f} m³</b>\n\n"
                f"🔩 شبکه پایین X: "
                f"{result['bottom_x_weight_kg']:.1f} kg\n"
                f"🔩 شبکه پایین Y: "
                f"{result['bottom_y_weight_kg']:.1f} kg\n"
                f"🔩 جمع میلگرد: "
                f"<b>{result['total_rebar_kg']:.1f} kg</b>\n\n"
                f"📦 شاخه X: "
                f"{result['bottom_x_bars_12m']}\n"
                f"📦 شاخه Y: "
                f"{result['bottom_y_bars_12m']}\n"
            )

            context.user_data["step"] = None

            await update.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=back_button(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}"
            )

        return


# =========================================================
# Buttons
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    if data == "new_estimate":

        await new_estimate(
            update,
            context
        )

        return

    if data.startswith("foundation_"):

        await foundation_selected(
            update,
            context
        )

        return

    if data == "help":

        await query.edit_message_text(
            TEXTS[lang]["help_text"],
            reply_markup=back_button(lang)
        )

        return

    if data == "back":

        context.user_data["step"] = None

        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

        return


# =========================================================
# Main
# =========================================================

def main():

    token = os.environ.get("BOT_TOKEN")

    if not token:

        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    application = (
        Application
        .builder()
        .token(token)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            language_selected,
            pattern=r"^lang_(fa|en)$"
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

    print(
        "Building Estimation Bot started successfully."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
