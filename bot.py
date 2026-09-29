import os
import threading
import math
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

        "language":
            "🌐 زبان را انتخاب کنید:",

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

        "invalid":
            "❌ مقدار واردشده صحیح نیست. دوباره وارد کنید.",

        "done":
            "✅ <b>برآورد فونداسیون</b>\n\n",

        "help_text":
            "این ربات برای متره و برآورد مصالح ساختمان "
            "بر اساس اطلاعات واقعی پروژه طراحی می‌شود.\n\n"
            "ربات خودش ابعاد یا آرماتور سازه را حدس نمی‌زند.",

    },

    "en": {

        "language":
            "🌐 Choose language:",

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

        "invalid":
            "❌ Invalid value. Please try again.",

        "done":
            "✅ <b>Foundation Estimate</b>\n\n",

        "help_text":
            "This bot estimates building materials "
            "from actual project data.\n\n"
            "It does not guess structural dimensions or reinforcement.",

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
# Utility
# =========================================================

def steel_weight(length_m, diameter_mm):

    if length_m <= 0 or diameter_mm <= 0:
        return 0

    return length_m * (diameter_mm ** 2) / 162


def twelve_meter_bars(length_m):

    if length_m <= 0:
        return 0

    return math.ceil(length_m / 12)


# =========================================================
# Rebar Detail Formatter
# =========================================================

def format_rebar_details(
    details,
    lang="fa"
):

    if not details:
        return ""

    details = sorted(
        details,
        key=lambda x: x["diameter_mm"]
    )

    if lang == "fa":

        message = (
            "🔩 <b>تفکیک میلگرد بر اساس قطر</b>\n\n"
        )

        for item in details:

            diameter = item["diameter_mm"]
            length = item["length_m"]
            weight = item["weight_kg"]
            bars = item["bars_12m"]

            message += (
                f"🔹 <b>Φ{diameter}</b>\n"
                f"   📏 طول کل: {length:.1f} m\n"
                f"   ⚖️ وزن: {weight:.1f} kg\n"
                f"   📦 شاخه ۱۲ متری: {bars} عدد\n\n"
            )

        return message

    else:

        message = (
            "🔩 <b>Rebar Breakdown by Diameter</b>\n\n"
        )

        for item in details:

            diameter = item["diameter_mm"]
            length = item["length_m"]
            weight = item["weight_kg"]
            bars = item["bars_12m"]

            message += (
                f"🔹 <b>Φ{diameter}</b>\n"
                f"   📏 Total length: {length:.1f} m\n"
                f"   ⚖️ Weight: {weight:.1f} kg\n"
                f"   📦 12m bars: {bars}\n\n"
            )

        return message


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

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    foundation = query.data.replace(
        "foundation_",
        ""
    )

    context.user_data["foundation"] = foundation

    # =====================================================
    # Isolated
    # =====================================================

    if foundation == "isolated":

        context.user_data["step"] = "iso_count"

        await query.edit_message_text(
            (
                "🔢 تعداد پی‌ها را وارد کنید:"
                if lang == "fa"
                else
                "🔢 Enter number of footings:"
            ),
            reply_markup=back_button(lang)
        )

        return

    # =====================================================
    # Strip
    # =====================================================

    if foundation == "strip":

        context.user_data["step"] = "strip_count"

        await query.edit_message_text(
            (
                "🔢 تعداد نوارها را وارد کنید:"
                if lang == "fa"
                else
                "🔢 Enter number of strips:"
            ),
            reply_markup=back_button(lang)
        )

        return

    # =====================================================
    # Raft
    # =====================================================

    if foundation == "raft":

        context.user_data["step"] = "raft_length"

        await query.edit_message_text(
            (
                "📏 طول رادیه را بر حسب متر وارد کنید:"
                if lang == "fa"
                else
                "📏 Enter raft length in meters:"
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

    if not step:
        return

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
            else
            "📏 Enter footing length in meters:"
        )

        return

    if step == "iso_length":

        context.user_data["iso_length"] = value
        context.user_data["step"] = "iso_width"

        await update.message.reply_text(
            "📐 عرض پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter footing width in meters:"
        )

        return

    if step == "iso_width":

        context.user_data["iso_width"] = value
        context.user_data["step"] = "iso_thickness"

        await update.message.reply_text(
            "📐 ضخامت پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter footing thickness in meters:"
        )

        return

    # -----------------------------------------------------
    # Bottom Rebar
    # -----------------------------------------------------

    if step == "iso_thickness":

        context.user_data["iso_thickness"] = value
        context.user_data["step"] = "iso_bottom_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom rebar diameter (mm):"
        )

        return

    if step == "iso_bottom_diameter":

        context.user_data["iso_bottom_diameter"] = int(value)
        context.user_data["step"] = "iso_bottom_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom rebar spacing (mm):"
        )

        return

    # -----------------------------------------------------
    # Top Rebar
    # -----------------------------------------------------

    if step == "iso_bottom_spacing":

        context.user_data["iso_bottom_spacing"] = int(value)
        context.user_data["step"] = "iso_top_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد شبکه بالایی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top rebar diameter (mm):"
        )

        return

    if step == "iso_top_diameter":

        context.user_data["iso_top_diameter"] = int(value)
        context.user_data["step"] = "iso_top_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای شبکه بالایی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top rebar spacing (mm):"
        )

        return

    # -----------------------------------------------------
    # Pedestal
    # -----------------------------------------------------

    if step == "iso_top_spacing":

        context.user_data["iso_top_spacing"] = int(value)
        context.user_data["step"] = "iso_pedestal_length"

        await update.message.reply_text(
            (
                "📏 طول پدستال را وارد کنید (m):\n"
                "اگر پدستال ندارید 0 وارد کنید."
                if lang == "fa"
                else
                "📏 Enter pedestal length (m):\n"
                "Enter 0 if there is no pedestal."
            )
        )

        return

    if step == "iso_pedestal_length":

        context.user_data["iso_pedestal_length"] = value
        context.user_data["step"] = "iso_pedestal_width"

        await update.message.reply_text(
            "📐 عرض پدستال را وارد کنید (m):"
            if lang == "fa"
            else
            "📐 Enter pedestal width (m):"
        )

        return

    if step == "iso_pedestal_width":

        context.user_data["iso_pedestal_width"] = value
        context.user_data["step"] = "iso_pedestal_height"

        await update.message.reply_text(
            "📐 ارتفاع پدستال را وارد کنید (m):"
            if lang == "fa"
            else
            "📐 Enter pedestal height (m):"
        )

        return

    # -----------------------------------------------------
    # Starter bars
    # -----------------------------------------------------

    if step == "iso_pedestal_height":

        context.user_data["iso_pedestal_height"] = value
        context.user_data["step"] = "iso_starter_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگردهای انتظار ستون را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter column starter bar diameter (mm):"
        )

        return

    if step == "iso_starter_diameter":

        context.user_data["iso_starter_diameter"] = int(value)
        context.user_data["step"] = "iso_starter_count"

        await update.message.reply_text(
            "🔢 تعداد میلگردهای انتظار هر پی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of starter bars per footing:"
        )

        return

    if step == "iso_starter_count":

        context.user_data["iso_starter_count"] = int(value)
        context.user_data["step"] = "iso_starter_length"

        await update.message.reply_text(
            "📏 طول هر میلگرد انتظار را وارد کنید (m):"
            if lang == "fa"
            else
            "📏 Enter length of each starter bar (m):"
        )

        return

    # =====================================================
    # Final isolated calculation
    # =====================================================

    if step == "iso_starter_length":

        context.user_data["iso_starter_length"] = value

        try:

            result = isolated_footing(

                count=context.user_data["iso_count"],

                length_m=context.user_data["iso_length"],

                width_m=context.user_data["iso_width"],

                thickness_m=context.user_data["iso_thickness"],

                lean_concrete_length_m=0,
                lean_concrete_width_m=0,
                lean_concrete_thickness_m=0,

                bottom_diameter_mm=
                    context.user_data["iso_bottom_diameter"],

                bottom_spacing_mm=
                    context.user_data["iso_bottom_spacing"],

                top_diameter_mm=
                    context.user_data["iso_top_diameter"],

                top_spacing_mm=
                    context.user_data["iso_top_spacing"],

                pedestal_length_m=
                    context.user_data["iso_pedestal_length"],

                pedestal_width_m=
                    context.user_data["iso_pedestal_width"],

                pedestal_height_m=
                    context.user_data["iso_pedestal_height"],
            )

            # -------------------------------------------------
            # Starter bars
            # -------------------------------------------------

            starter_length_total = (
                context.user_data["iso_count"]
                * context.user_data["iso_starter_count"]
                * context.user_data["iso_starter_length"]
            )

            starter_weight = steel_weight(
                starter_length_total,
                context.user_data["iso_starter_diameter"]
            )

            starter_bars_12m = twelve_meter_bars(
                starter_length_total
            )

            total_rebar = (
                result["total_rebar_kg"]
                + starter_weight
            )

            # -------------------------------------------------
            # Rebar details
            # -------------------------------------------------

            rebar_details = list(
                result.get(
                    "rebar_details",
                    []
                )
            )

            starter_diameter = (
                context.user_data[
                    "iso_starter_diameter"
                ]
            )

            starter_found = False

            for item in rebar_details:

                if item["diameter_mm"] == starter_diameter:

                    item["length_m"] += (
                        starter_length_total
                    )

                    item["weight_kg"] += (
                        starter_weight
                    )

                    item["bars_12m"] = twelve_meter_bars(
                        item["length_m"]
                    )

                    starter_found = True

                    break

            if not starter_found:

                rebar_details.append({
                    "diameter_mm":
                        starter_diameter,

                    "length_m":
                        starter_length_total,

                    "weight_kg":
                        starter_weight,

                    "bars_12m":
                        starter_bars_12m,
                })

            rebar_details.sort(
                key=lambda x: x["diameter_mm"]
            )

            message = (

                TEXTS[lang]["done"]

                + "⬛ <b>پی منفرد</b>\n\n"

                + f"🧱 بتن خود پی: "
                f"{result['footing_concrete_m3']:.2f} m³\n"

                + f"🧱 بتن پدستال: "
                f"{result['pedestal_concrete_m3']:.2f} m³\n"

                + f"🧱 جمع بتن سازه‌ای: "
                f"<b>{result['footing_concrete_m3'] + result['pedestal_concrete_m3']:.2f} m³</b>\n\n"

                + format_rebar_details(
                    rebar_details,
                    lang
                )

                + f"⚖️ <b>جمع کل میلگرد: "
                f"{total_rebar:.1f} kg</b>\n\n"

                + "⚠️ مقادیر بر اساس اطلاعات واردشده "
                  "محاسبه شده‌اند."
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
            else
            "📏 Enter strip length:"
        )

        return

    if step == "strip_length":

        context.user_data["strip_length"] = value
        context.user_data["step"] = "strip_width"

        await update.message.reply_text(
            "📐 عرض فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter strip footing width:"
        )

        return

    if step == "strip_width":

        context.user_data["strip_width"] = value
        context.user_data["step"] = "strip_thickness"

        await update.message.reply_text(
            "📐 ضخامت فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter strip footing thickness:"
        )

        return

    # =====================================================
    # Strip bottom longitudinal
    # =====================================================

    if step == "strip_thickness":

        context.user_data["strip_thickness"] = value
        context.user_data["step"] = "strip_long_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد طولی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom longitudinal rebar diameter (mm):"
        )

        return

    if step == "strip_long_diameter":

        context.user_data["strip_long_diameter"] = int(value)
        context.user_data["step"] = "strip_long_count"

        await update.message.reply_text(
            "🔢 تعداد میلگردهای طولی تحتانی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of bottom longitudinal bars:"
        )

        return

    # =====================================================
    # Strip bottom transverse
    # =====================================================

    if step == "strip_long_count":

        context.user_data["strip_long_count"] = int(value)
        context.user_data["step"] = "strip_trans_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد عرضی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom transverse rebar diameter (mm):"
        )

        return

    if step == "strip_trans_diameter":

        context.user_data["strip_trans_diameter"] = int(value)
        context.user_data["step"] = "strip_trans_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای عرضی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom transverse spacing (mm):"
        )

        return

    # =====================================================
    # Strip top longitudinal
    # =====================================================

    if step == "strip_trans_spacing":

        context.user_data["strip_trans_spacing"] = int(value)
        context.user_data["step"] = "strip_top_long_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد طولی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top longitudinal rebar diameter (mm):"
        )

        return

    if step == "strip_top_long_diameter":

        context.user_data["strip_top_long_diameter"] = int(value)
        context.user_data["step"] = "strip_top_long_count"

        await update.message.reply_text(
            "🔢 تعداد میلگردهای طولی فوقانی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of top longitudinal bars:"
        )

        return

    # =====================================================
    # Strip top transverse
    # =====================================================

    if step == "strip_top_long_count":

        context.user_data["strip_top_long_count"] = int(value)
        context.user_data["step"] = "strip_top_trans_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد عرضی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top transverse rebar diameter (mm):"
        )

        return

    if step == "strip_top_trans_diameter":

        context.user_data["strip_top_trans_diameter"] = int(value)
        context.user_data["step"] = "strip_top_trans_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگردهای عرضی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top transverse spacing (mm):"
        )

        return

    # =====================================================
    # Final strip calculation
    # =====================================================

    if step == "strip_top_trans_spacing":

        context.user_data["strip_top_trans_spacing"] = int(value)

        try:

            result = strip_footing(

                strip_count=
                    context.user_data["strip_count"],

                strip_length_m=
                    context.user_data["strip_length"],

                footing_width_m=
                    context.user_data["strip_width"],

                footing_thickness_m=
                    context.user_data["strip_thickness"],

                # بتن مگر حذف شده
                lean_length_m=0,
                lean_width_m=0,
                lean_thickness_m=0,

                # تحتانی طولی
                longitudinal_diameter_mm=
                    context.user_data[
                        "strip_long_diameter"
                    ],

                longitudinal_count=
                    context.user_data[
                        "strip_long_count"
                    ],

                # تحتانی عرضی
                transverse_diameter_mm=
                    context.user_data[
                        "strip_trans_diameter"
                    ],

                transverse_spacing_mm=
                    context.user_data[
                        "strip_trans_spacing"
                    ],

                # فوقانی طولی
                top_longitudinal_diameter_mm=
                    context.user_data[
                        "strip_top_long_diameter"
                    ],

                top_longitudinal_count=
                    context.user_data[
                        "strip_top_long_count"
                    ],

                # فوقانی عرضی
                top_transverse_diameter_mm=
                    context.user_data[
                        "strip_top_trans_diameter"
                    ],

                top_transverse_spacing_mm=
                    context.user_data[
                        "strip_top_trans_spacing"
                    ],
            )

            message = (

                TEXTS[lang]["done"]

                + "▬ <b>پی نواری</b>\n\n"

                + f"🧱 بتن فونداسیون: "
                f"{result['footing_concrete_m3']:.2f} m³\n\n"

                + "🔻 <b>آرماتوربندی</b>\n"
                + "تحتانی طولی + تحتانی عرضی\n"
                + "فوقانی طولی + فوقانی عرضی\n\n"

                + format_rebar_details(
                    result.get(
                        "rebar_details",
                        []
                    ),
                    lang
                )

                + f"⚖️ <b>جمع کل میلگرد: "
                f"{result['total_rebar_kg']:.1f} kg</b>\n\n"

                + "⚠️ مقادیر بر اساس اطلاعات واردشده "
                  "محاسبه شده‌اند."
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
            else
            "📐 Enter raft width:"
        )

        return

    if step == "raft_width":

        context.user_data["raft_width"] = value
        context.user_data["step"] = "raft_thickness"

        await update.message.reply_text(
            "📐 ضخامت رادیه را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter raft thickness:"
        )

        return

    # =====================================================
    # Raft bottom X
    # =====================================================

    if step == "raft_thickness":

        context.user_data["raft_thickness"] = value
        context.user_data["step"] = "raft_bottom_x_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom X rebar diameter (mm):"
        )

        return

    if step == "raft_bottom_x_diameter":

        context.user_data["raft_bottom_x_diameter"] = int(value)
        context.user_data["step"] = "raft_bottom_x_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom X spacing (mm):"
        )

        return

    # =====================================================
    # Raft bottom Y
    # =====================================================

    if step == "raft_bottom_x_spacing":

        context.user_data["raft_bottom_x_spacing"] = int(value)
        context.user_data["step"] = "raft_bottom_y_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom Y rebar diameter (mm):"
        )

        return

    if step == "raft_bottom_y_diameter":

        context.user_data["raft_bottom_y_diameter"] = int(value)
        context.user_data["step"] = "raft_bottom_y_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom Y spacing (mm):"
        )

        return

    # =====================================================
    # Raft top X
    # =====================================================

    if step == "raft_bottom_y_spacing":

        context.user_data["raft_bottom_y_spacing"] = int(value)
        context.user_data["step"] = "raft_top_x_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد X بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top X rebar diameter (mm):"
        )

        return

    if step == "raft_top_x_diameter":

        context.user_data["raft_top_x_diameter"] = int(value)
        context.user_data["step"] = "raft_top_x_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد X بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top X spacing (mm):"
        )

        return

    # =====================================================
    # Raft top Y
    # =====================================================

    if step == "raft_top_x_spacing":

        context.user_data["raft_top_x_spacing"] = int(value)
        context.user_data["step"] = "raft_top_y_diameter"

        await update.message.reply_text(
            "🔩 قطر میلگرد Y بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top Y rebar diameter (mm):"
        )

        return

    if step == "raft_top_y_diameter":

        context.user_data["raft_top_y_diameter"] = int(value)
        context.user_data["step"] = "raft_top_y_spacing"

        await update.message.reply_text(
            "📏 فاصله میلگرد Y بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top Y spacing (mm):"
        )

        return

    # =====================================================
    # Final raft calculation
    # =====================================================

    if step == "raft_top_y_spacing":

        context.user_data["raft_top_y_spacing"] = int(value)

        try:

            result = raft_foundation(

                length_m=
                    context.user_data["raft_length"],

                width_m=
                    context.user_data["raft_width"],

                thickness_m=
                    context.user_data["raft_thickness"],

                # بتن مگر حذف شده
                lean_length_m=0,
                lean_width_m=0,
                lean_thickness_m=0,

                # تحتانی X
                bottom_x_diameter_mm=
                    context.user_data[
                        "raft_bottom_x_diameter"
                    ],

                bottom_x_spacing_mm=
                    context.user_data[
                        "raft_bottom_x_spacing"
                    ],

                # تحتانی Y
                bottom_y_diameter_mm=
                    context.user_data[
                        "raft_bottom_y_diameter"
                    ],

                bottom_y_spacing_mm=
                    context.user_data[
                        "raft_bottom_y_spacing"
                    ],

                # فوقانی X
                top_x_diameter_mm=
                    context.user_data[
                        "raft_top_x_diameter"
                    ],

                top_x_spacing_mm=
                    context.user_data[
                        "raft_top_x_spacing"
                    ],

                # فوقانی Y
                top_y_diameter_mm=
                    context.user_data[
                        "raft_top_y_diameter"
                    ],

                top_y_spacing_mm=
                    context.user_data[
                        "raft_top_y_spacing"
                    ],
            )

            message = (

                TEXTS[lang]["done"]

                + "▰ <b>پی رادیه</b>\n\n"

                + f"🧱 بتن رادیه: "
                f"{result['raft_concrete_m3']:.2f} m³\n\n"

                + "🔻 <b>آرماتوربندی</b>\n"
                + "تحتانی X + تحتانی Y\n"
                + "فوقانی X + فوقانی Y\n\n"

                + format_rebar_details(
                    result.get(
                        "rebar_details",
                        []
                    ),
                    lang
                )

                + f"⚖️ <b>جمع کل میلگرد: "
                f"{result['total_rebar_kg']:.1f} kg</b>\n\n"

                + "⚠️ مقادیر بر اساس اطلاعات واردشده "
                  "محاسبه شده‌اند."
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
