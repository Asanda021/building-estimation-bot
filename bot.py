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
    optimize_12m_bars,
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
            "🌐 <b>زبان ربات را انتخاب کنید</b>",

        "welcome":
            "🏗️ <b>دستیار برآورد ساختمان</b>\n\n"
            "📐 متره و برآورد مصالح و میلگرد\n"
            "📊 محاسبه بر اساس اطلاعات پروژه\n\n"
            "از منوی زیر انتخاب کنید:",

        "new":
            "➕ برآورد جدید",

        "help":
            "ℹ️ راهنما",

        "home":
            "🏠 منوی اصلی",

        "cancel":
            "❌ لغو",

        "previous":
            "⬅️ مرحله قبل",

        "new_again":
            "🔄 برآورد جدید",

        "back_foundation":
            "⬅️ انتخاب فونداسیون",

        "choose_foundation":
            "🧱 <b>فونداسیون</b>\n\n"
            "نوع فونداسیون را انتخاب کنید:",

        "isolated":
            "⬛ پی منفرد",

        "strip":
            "▬ پی نواری",

        "raft":
            "▰ پی گسترده (رادیه)",

        "invalid":
            "❌ مقدار واردشده صحیح نیست.\n"
            "لطفاً دوباره وارد کنید.",

        "done":
            "✅ <b>برآورد با موفقیت انجام شد</b>\n\n",

        "help_text":
            "ℹ️ <b>راهنمای ربات</b>\n\n"
            "این ربات برای متره و برآورد ساختمان طراحی شده است.\n\n"
            "🏗️ فونداسیون:\n"
            "• پی منفرد\n"
            "• پی نواری\n"
            "• پی گسترده\n\n"
            "🔩 برای میلگرد، قطر، تعداد، فاصله، طول قطعات "
            "و Cut List محاسبه می‌شود.\n\n"
            "⚠️ ربات ابعاد یا آرماتور سازه را حدس نمی‌زند "
            "و محاسبات بر اساس اطلاعات واردشده انجام می‌شود.",

        "stage":
            "مرحله",
    },

    "en": {

        "language":
            "🌐 <b>Choose bot language</b>",

        "welcome":
            "🏗️ <b>Building Estimation Assistant</b>\n\n"
            "📐 Quantity takeoff and rebar estimation\n"
            "📊 Based on actual project data\n\n"
            "Choose an option:",

        "new":
            "➕ New Estimate",

        "help":
            "ℹ️ Help",

        "home":
            "🏠 Main Menu",

        "cancel":
            "❌ Cancel",

        "previous":
            "⬅️ Previous",

        "new_again":
            "🔄 New Estimate",

        "back_foundation":
            "⬅️ Foundation Types",

        "choose_foundation":
            "🧱 <b>Foundation</b>\n\n"
            "Choose foundation type:",

        "isolated":
            "⬛ Isolated Footing",

        "strip":
            "▬ Strip Footing",

        "raft":
            "▰ Raft Foundation",

        "invalid":
            "❌ Invalid value.\n"
            "Please enter the value again.",

        "done":
            "✅ <b>Estimate completed successfully</b>\n\n",

        "help_text":
            "ℹ️ <b>Bot Guide</b>\n\n"
            "This bot is designed for building quantity takeoff "
            "and estimation.\n\n"
            "🏗️ Foundations:\n"
            "• Isolated footing\n"
            "• Strip footing\n"
            "• Raft foundation\n\n"
            "🔩 Rebar diameter, quantity, spacing, piece length "
            "and Cut List are calculated.\n\n"
            "⚠️ The bot does not guess structural dimensions "
            "or reinforcement. Calculations are based on entered data.",

        "stage":
            "Stage",
    }
}


# =========================================================
# Main Menu
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
                "🧱 فونداسیون" if lang == "fa"
                else "🧱 Foundation",
                callback_data="foundation_menu"
            )
        ],

        [
            InlineKeyboardButton(
                t["help"],
                callback_data="help"
            )
        ]

    ])


# =========================================================
# Foundation Menu
# =========================================================

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
                t["home"],
                callback_data="home"
            )
        ]

    ])


# =========================================================
# Step Keyboard
# =========================================================

def step_keyboard(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                t["previous"],
                callback_data="previous_step"
            ),

            InlineKeyboardButton(
                t["cancel"],
                callback_data="cancel_estimate"
            )
        ],

        [
            InlineKeyboardButton(
                t["home"],
                callback_data="home"
            )
        ]

    ])


# =========================================================
# Result Keyboard
# =========================================================

def result_keyboard(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                t["new_again"],
                callback_data="new_estimate"
            )
        ],

        [
            InlineKeyboardButton(
                t["home"],
                callback_data="home"
            )
        ]

    ])


# =========================================================
# Language Menu
# =========================================================

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
# Stage Information
# =========================================================

STAGE_NAMES = {

    "fa": {

        "iso_count": "تعداد پی",
        "iso_length": "طول پی",
        "iso_width": "عرض پی",
        "iso_thickness": "ضخامت پی",
        "iso_bottom_diameter": "قطر میلگرد پایین",
        "iso_bottom_spacing": "فاصله میلگرد پایین",
        "iso_top_diameter": "قطر میلگرد بالا",
        "iso_top_spacing": "فاصله میلگرد بالا",
        "iso_pedestal_length": "طول پدستال",
        "iso_pedestal_width": "عرض پدستال",
        "iso_pedestal_height": "ارتفاع پدستال",
        "iso_starter_diameter": "قطر میلگرد انتظار",
        "iso_starter_count": "تعداد میلگرد انتظار",
        "iso_starter_length": "طول میلگرد انتظار",

        "strip_count": "تعداد نوار",
        "strip_length": "طول نوار",
        "strip_width": "عرض پی",
        "strip_thickness": "ضخامت پی",
        "strip_long_diameter": "قطر طولی پایین",
        "strip_long_count": "تعداد طولی پایین",
        "strip_trans_diameter": "قطر عرضی پایین",
        "strip_trans_spacing": "فاصله عرضی پایین",
        "strip_top_long_diameter": "قطر طولی بالا",
        "strip_top_long_count": "تعداد طولی بالا",
        "strip_top_trans_diameter": "قطر عرضی بالا",
        "strip_top_trans_spacing": "فاصله عرضی بالا",

        "raft_length": "طول رادیه",
        "raft_width": "عرض رادیه",
        "raft_thickness": "ضخامت رادیه",
        "raft_bottom_x_diameter": "قطر X پایین",
        "raft_bottom_x_spacing": "فاصله X پایین",
        "raft_bottom_y_diameter": "قطر Y پایین",
        "raft_bottom_y_spacing": "فاصله Y پایین",
        "raft_top_x_diameter": "قطر X بالا",
        "raft_top_x_spacing": "فاصله X بالا",
        "raft_top_y_diameter": "قطر Y بالا",
        "raft_top_y_spacing": "فاصله Y بالا",
    },

    "en": {

        "iso_count": "Footing count",
        "iso_length": "Footing length",
        "iso_width": "Footing width",
        "iso_thickness": "Footing thickness",
        "iso_bottom_diameter": "Bottom rebar diameter",
        "iso_bottom_spacing": "Bottom rebar spacing",
        "iso_top_diameter": "Top rebar diameter",
        "iso_top_spacing": "Top rebar spacing",
        "iso_pedestal_length": "Pedestal length",
        "iso_pedestal_width": "Pedestal width",
        "iso_pedestal_height": "Pedestal height",
        "iso_starter_diameter": "Starter bar diameter",
        "iso_starter_count": "Starter bar count",
        "iso_starter_length": "Starter bar length",

        "strip_count": "Strip count",
        "strip_length": "Strip length",
        "strip_width": "Footing width",
        "strip_thickness": "Footing thickness",
        "strip_long_diameter": "Bottom longitudinal diameter",
        "strip_long_count": "Bottom longitudinal count",
        "strip_trans_diameter": "Bottom transverse diameter",
        "strip_trans_spacing": "Bottom transverse spacing",
        "strip_top_long_diameter": "Top longitudinal diameter",
        "strip_top_long_count": "Top longitudinal count",
        "strip_top_trans_diameter": "Top transverse diameter",
        "strip_top_trans_spacing": "Top transverse spacing",

        "raft_length": "Raft length",
        "raft_width": "Raft width",
        "raft_thickness": "Raft thickness",
        "raft_bottom_x_diameter": "Bottom X diameter",
        "raft_bottom_x_spacing": "Bottom X spacing",
        "raft_bottom_y_diameter": "Bottom Y diameter",
        "raft_bottom_y_spacing": "Bottom Y spacing",
        "raft_top_x_diameter": "Top X diameter",
        "raft_top_x_spacing": "Top X spacing",
        "raft_top_y_diameter": "Top Y diameter",
        "raft_top_y_spacing": "Top Y spacing",
    }
}


# =========================================================
# Progress / Step Message
# =========================================================

def step_message(lang, step, current, total, question):

    name = STAGE_NAMES[lang].get(
        step,
        ""
    )

    if lang == "fa":

        return (
            f"📐 <b>{name}</b>\n\n"
            f"{question}\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"📍 مرحله <b>{current}</b> از <b>{total}</b>"
        )

    return (
        f"📐 <b>{name}</b>\n\n"
        f"{question}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📍 <b>Stage {current}</b> of <b>{total}</b>"
    )


# =========================================================
# Rebar Detail + Cut List Formatter
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
            "🔩 <b>تفکیک و لیست برش میلگرد</b>\n\n"
        )

        for item in details:

            diameter = item["diameter_mm"]
            length = item["length_m"]
            weight = item["weight_kg"]
            bars = item["bars_12m"]

            piece_count = item.get(
                "piece_count",
                len(
                    item.get(
                        "piece_lengths_m",
                        []
                    )
                )
            )

            waste = item.get(
                "waste_m",
                0
            )

            description = item.get(
                "description",
                ""
            )

            message += (
                "━━━━━━━━━━━━━━\n"
                f"🔹 <b>Φ{diameter}</b>\n"
            )

            if description:

                message += (
                    f"   📌 {description}\n"
                )

            message += (
                f"   🔢 تعداد قطعه: {piece_count} عدد\n"
                f"   📏 طول کل: {length:.2f} m\n"
                f"   ⚖️ وزن: {weight:.1f} kg\n"
                f"   📦 شاخه ۱۲ متری: {bars} عدد\n"
                f"   ♻️ پرت برش: {waste:.2f} m\n\n"
            )

            cut_plan = item.get(
                "cut_plan",
                []
            )

            if cut_plan:

                message += "✂️ <b>Cut List:</b>\n"

                max_plans = 15

                for index, plan in enumerate(
                    cut_plan[:max_plans],
                    start=1
                ):

                    pieces = plan.get(
                        "pieces",
                        []
                    )

                    used = plan.get(
                        "used_m",
                        0
                    )

                    plan_waste = plan.get(
                        "waste_m",
                        0
                    )

                    pieces_text = " + ".join(
                        f"{p:.2f}"
                        for p in pieces
                    )

                    message += (
                        f"   شاخه {index}: "
                        f"{pieces_text}"
                        f" = {used:.2f} m"
                        f" | پرت {plan_waste:.2f} m\n"
                    )

                if len(cut_plan) > max_plans:

                    remaining = (
                        len(cut_plan)
                        - max_plans
                    )

                    message += (
                        f"   ... و {remaining} شاخه دیگر\n"
                    )

                message += "\n"

        return message

    # =====================================================
    # English
    # =====================================================

    message = (
        "🔩 <b>Rebar Breakdown & Cut List</b>\n\n"
    )

    for item in details:

        diameter = item["diameter_mm"]
        length = item["length_m"]
        weight = item["weight_kg"]
        bars = item["bars_12m"]

        piece_count = item.get(
            "piece_count",
            len(
                item.get(
                    "piece_lengths_m",
                    []
                )
            )
        )

        waste = item.get(
            "waste_m",
            0
        )

        description = item.get(
            "description",
            ""
        )

        message += (
            "━━━━━━━━━━━━━━\n"
            f"🔹 <b>Φ{diameter}</b>\n"
        )

        if description:

            message += (
                f"   📌 {description}\n"
            )

        message += (
            f"   🔢 Pieces: {piece_count}\n"
            f"   📏 Total length: {length:.2f} m\n"
            f"   ⚖️ Weight: {weight:.1f} kg\n"
            f"   📦 12m bars: {bars}\n"
            f"   ♻️ Cutting waste: {waste:.2f} m\n\n"
        )

        cut_plan = item.get(
            "cut_plan",
            []
        )

        if cut_plan:

            message += (
                "✂️ <b>Cut List:</b>\n"
            )

            max_plans = 15

            for index, plan in enumerate(
                cut_plan[:max_plans],
                start=1
            ):

                pieces = plan.get(
                    "pieces",
                    []
                )

                used = plan.get(
                    "used_m",
                    0
                )

                plan_waste = plan.get(
                    "waste_m",
                    0
                )

                pieces_text = " + ".join(
                    f"{p:.2f}"
                    for p in pieces
                )

                message += (
                    f"   Bar {index}: "
                    f"{pieces_text}"
                    f" = {used:.2f} m"
                    f" | waste {plan_waste:.2f} m\n"
                )

            if len(cut_plan) > max_plans:

                remaining = (
                    len(cut_plan)
                    - max_plans
                )

                message += (
                    f"   ... and {remaining} more bars\n"
                )

            message += "\n"

    return message


# =========================================================
# Start
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        TEXTS["fa"]["language"],
        parse_mode="HTML",
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

    context.user_data.clear()

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
        parse_mode="HTML",
        reply_markup=foundation_menu(lang)
    )


# =========================================================
# Foundation Menu
# =========================================================

async def show_foundation_menu(
    update,
    context
):

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    query = update.callback_query

    await query.edit_message_text(
        TEXTS[lang]["choose_foundation"],
        parse_mode="HTML",
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
            step_message(
                lang,
                "iso_count",
                1,
                14,
                (
                    "🔢 تعداد پی‌ها را وارد کنید:"
                    if lang == "fa"
                    else
                    "🔢 Enter number of footings:"
                )
            ),
            parse_mode="HTML",
            reply_markup=step_keyboard(lang)
        )

        return

    # -----------------------------------------------------
    # Strip
    # -----------------------------------------------------

    if foundation == "strip":

        context.user_data["step"] = "strip_count"

        await query.edit_message_text(
            step_message(
                lang,
                "strip_count",
                1,
                12,
                (
                    "🔢 تعداد نوارها را وارد کنید:"
                    if lang == "fa"
                    else
                    "🔢 Enter number of strips:"
                )
            ),
            parse_mode="HTML",
            reply_markup=step_keyboard(lang)
        )

        return

    # -----------------------------------------------------
    # Raft
    # -----------------------------------------------------

    if foundation == "raft":

        context.user_data["step"] = "raft_length"

        await query.edit_message_text(
            step_message(
                lang,
                "raft_length",
                1,
                11,
                (
                    "📏 طول رادیه را بر حسب متر وارد کنید:"
                    if lang == "fa"
                    else
                    "📏 Enter raft length in meters:"
                )
            ),
            parse_mode="HTML",
            reply_markup=step_keyboard(lang)
        )

        return


# =========================================================
# Question Helper
# =========================================================

async def ask_next(
    update,
    context,
    step,
    current,
    total,
    question
):

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    context.user_data["step"] = step

    await update.message.reply_text(
        step_message(
            lang,
            step,
            current,
            total,
            question
        ),
        parse_mode="HTML",
        reply_markup=step_keyboard(lang)
    )


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
            TEXTS[lang]["invalid"],
            reply_markup=step_keyboard(lang)
        )

        return

    # =====================================================
    # ISOLATED
    # =====================================================

    if step == "iso_count":

        context.user_data["iso_count"] = int(value)

        await ask_next(
            update,
            context,
            "iso_length",
            2,
            14,
            "📏 طول پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else
            "📏 Enter footing length in meters:"
        )

        return

    if step == "iso_length":

        context.user_data["iso_length"] = value

        await ask_next(
            update,
            context,
            "iso_width",
            3,
            14,
            "📐 عرض پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter footing width in meters:"
        )

        return

    if step == "iso_width":

        context.user_data["iso_width"] = value

        await ask_next(
            update,
            context,
            "iso_thickness",
            4,
            14,
            "📐 ضخامت پی را بر حسب متر وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter footing thickness in meters:"
        )

        return

    if step == "iso_thickness":

        context.user_data["iso_thickness"] = value

        await ask_next(
            update,
            context,
            "iso_bottom_diameter",
            5,
            14,
            "🔩 قطر میلگرد شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom rebar diameter (mm):"
        )

        return

    if step == "iso_bottom_diameter":

        context.user_data["iso_bottom_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "iso_bottom_spacing",
            6,
            14,
            "📏 فاصله میلگردهای شبکه پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom rebar spacing (mm):"
        )

        return

    if step == "iso_bottom_spacing":

        context.user_data["iso_bottom_spacing"] = int(value)

        await ask_next(
            update,
            context,
            "iso_top_diameter",
            7,
            14,
            "🔩 قطر میلگرد شبکه بالایی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top rebar diameter (mm):"
        )

        return

    if step == "iso_top_diameter":

        context.user_data["iso_top_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "iso_top_spacing",
            8,
            14,
            "📏 فاصله میلگردهای شبکه بالایی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top rebar spacing (mm):"
        )

        return

    if step == "iso_top_spacing":

        context.user_data["iso_top_spacing"] = int(value)

        await ask_next(
            update,
            context,
            "iso_pedestal_length",
            9,
            14,
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

        await ask_next(
            update,
            context,
            "iso_pedestal_width",
            10,
            14,
            "📐 عرض پدستال را وارد کنید (m):"
            if lang == "fa"
            else
            "📐 Enter pedestal width (m):"
        )

        return

    if step == "iso_pedestal_width":

        context.user_data["iso_pedestal_width"] = value

        await ask_next(
            update,
            context,
            "iso_pedestal_height",
            11,
            14,
            "📐 ارتفاع پدستال را وارد کنید (m):"
            if lang == "fa"
            else
            "📐 Enter pedestal height (m):"
        )

        return

    if step == "iso_pedestal_height":

        context.user_data["iso_pedestal_height"] = value

        await ask_next(
            update,
            context,
            "iso_starter_diameter",
            12,
            14,
            "🔩 قطر میلگردهای انتظار ستون را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter column starter bar diameter (mm):"
        )

        return

    if step == "iso_starter_diameter":

        context.user_data["iso_starter_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "iso_starter_count",
            13,
            14,
            "🔢 تعداد میلگردهای انتظار هر پی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of starter bars per footing:"
        )

        return

    if step == "iso_starter_count":

        context.user_data["iso_starter_count"] = int(value)

        await ask_next(
            update,
            context,
            "iso_starter_length",
            14,
            14,
            "📏 طول هر میلگرد انتظار را وارد کنید (m):"
            if lang == "fa"
            else
            "📏 Enter length of each starter bar (m):"
        )

        return

    # =====================================================
    # FINAL ISOLATED
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
                    context.user_data[
                        "iso_bottom_diameter"
                    ],

                bottom_spacing_mm=
                    context.user_data[
                        "iso_bottom_spacing"
                    ],

                top_diameter_mm=
                    context.user_data[
                        "iso_top_diameter"
                    ],

                top_spacing_mm=
                    context.user_data[
                        "iso_top_spacing"
                    ],

                pedestal_length_m=
                    context.user_data[
                        "iso_pedestal_length"
                    ],

                pedestal_width_m=
                    context.user_data[
                        "iso_pedestal_width"
                    ],

                pedestal_height_m=
                    context.user_data[
                        "iso_pedestal_height"
                    ],
            )

            starter_diameter = (
                context.user_data[
                    "iso_starter_diameter"
                ]
            )

            starter_piece_length = (
                context.user_data[
                    "iso_starter_length"
                ]
            )

            starter_piece_count = (
                context.user_data["iso_count"]
                * context.user_data["iso_starter_count"]
            )

            starter_piece_lengths = [
                starter_piece_length
                for _ in range(
                    starter_piece_count
                )
            ]

            starter_length_total = sum(
                starter_piece_lengths
            )

            starter_weight = steel_weight(
                starter_length_total,
                starter_diameter
            )

            starter_cut_plan = optimize_12m_bars(
                starter_piece_lengths
            )

            starter_bars_12m = (
                starter_cut_plan["stock_bars"]
            )

            total_rebar = (
                result["total_rebar_kg"]
                + starter_weight
            )

            rebar_details = list(
                result.get(
                    "rebar_details",
                    []
                )
            )

            starter_found = False

            for item in rebar_details:

                if (
                    item["diameter_mm"]
                    == starter_diameter
                ):

                    item["length_m"] += (
                        starter_length_total
                    )

                    item["weight_kg"] += (
                        starter_weight
                    )

                    existing_pieces = item.get(
                        "piece_lengths_m",
                        []
                    )

                    existing_pieces.extend(
                        starter_piece_lengths
                    )

                    item["piece_lengths_m"] = (
                        existing_pieces
                    )

                    item["piece_count"] = (
                        len(existing_pieces)
                    )

                    optimization = optimize_12m_bars(
                        existing_pieces
                    )

                    item["bars_12m"] = (
                        optimization["stock_bars"]
                    )

                    item["waste_m"] = (
                        optimization["waste_m"]
                    )

                    item["cut_plan"] = (
                        optimization["plans"]
                    )

                    if item.get("description"):

                        item["description"] += (
                            " + پی منفرد - میلگرد انتظار"
                        )

                    else:

                        item["description"] = (
                            "پی منفرد - میلگرد انتظار"
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

                    "piece_count":
                        starter_piece_count,

                    "piece_lengths_m":
                        starter_piece_lengths,

                    "waste_m":
                        starter_cut_plan["waste_m"],

                    "cut_plan":
                        starter_cut_plan["plans"],

                    "description":
                        "پی منفرد - میلگرد انتظار",
                })

            rebar_details.sort(
                key=lambda x:
                    x["diameter_mm"]
            )

            message = (

                TEXTS[lang]["done"]

                + "⬛ <b>پی منفرد</b>\n\n"

                + f"🧱 بتن خود پی: "
                f"{result['footing_concrete_m3']:.2f} m³\n"

                + f"🧱 بتن پدستال: "
                f"{result['pedestal_concrete_m3']:.2f} m³\n"

                + f"🧱 جمع بتن سازه‌ای: "
                f"<b>"
                f"{result['footing_concrete_m3'] + result['pedestal_concrete_m3']:.2f}"
                f" m³"
                f"</b>\n\n"

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
                reply_markup=result_keyboard(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}",
                reply_markup=step_keyboard(lang)
            )

        return

    # =====================================================
    # STRIP
    # =====================================================

    if step == "strip_count":

        context.user_data["strip_count"] = int(value)

        await ask_next(
            update,
            context,
            "strip_length",
            2,
            12,
            "📏 طول هر نوار را وارد کنید:"
            if lang == "fa"
            else
            "📏 Enter strip length:"
        )

        return

    if step == "strip_length":

        context.user_data["strip_length"] = value

        await ask_next(
            update,
            context,
            "strip_width",
            3,
            12,
            "📐 عرض فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter strip footing width:"
        )

        return

    if step == "strip_width":

        context.user_data["strip_width"] = value

        await ask_next(
            update,
            context,
            "strip_thickness",
            4,
            12,
            "📐 ضخامت فونداسیون نواری را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter strip footing thickness:"
        )

        return

    if step == "strip_thickness":

        context.user_data["strip_thickness"] = value

        await ask_next(
            update,
            context,
            "strip_long_diameter",
            5,
            12,
            "🔩 قطر میلگرد طولی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom longitudinal rebar diameter (mm):"
        )

        return

    if step == "strip_long_diameter":

        context.user_data["strip_long_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "strip_long_count",
            6,
            12,
            "🔢 تعداد میلگردهای طولی تحتانی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of bottom longitudinal bars:"
        )

        return

    if step == "strip_long_count":

        context.user_data["strip_long_count"] = int(value)

        await ask_next(
            update,
            context,
            "strip_trans_diameter",
            7,
            12,
            "🔩 قطر میلگرد عرضی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom transverse rebar diameter (mm):"
        )

        return

    if step == "strip_trans_diameter":

        context.user_data["strip_trans_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "strip_trans_spacing",
            8,
            12,
            "📏 فاصله میلگردهای عرضی تحتانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom transverse spacing (mm):"
        )

        return

    if step == "strip_trans_spacing":

        context.user_data["strip_trans_spacing"] = int(value)

        await ask_next(
            update,
            context,
            "strip_top_long_diameter",
            9,
            12,
            "🔩 قطر میلگرد طولی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top longitudinal rebar diameter (mm):"
        )

        return

    if step == "strip_top_long_diameter":

        context.user_data["strip_top_long_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "strip_top_long_count",
            10,
            12,
            "🔢 تعداد میلگردهای طولی فوقانی را وارد کنید:"
            if lang == "fa"
            else
            "🔢 Enter number of top longitudinal bars:"
        )

        return

    if step == "strip_top_long_count":

        context.user_data["strip_top_long_count"] = int(value)

        await ask_next(
            update,
            context,
            "strip_top_trans_diameter",
            11,
            12,
            "🔩 قطر میلگرد عرضی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top transverse rebar diameter (mm):"
        )

        return

    if step == "strip_top_trans_diameter":

        context.user_data["strip_top_trans_diameter"] = int(value)

        await ask_next(
            update,
            context,
            "strip_top_trans_spacing",
            12,
            12,
            "📏 فاصله میلگردهای عرضی فوقانی را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top transverse spacing (mm):"
        )

        return

    # =====================================================
    # FINAL STRIP
    # =====================================================

    if step == "strip_top_trans_spacing":

        context.user_data[
            "strip_top_trans_spacing"
        ] = int(value)

        try:

            result = strip_footing(

                strip_count=
                    context.user_data[
                        "strip_count"
                    ],

                strip_length_m=
                    context.user_data[
                        "strip_length"
                    ],

                footing_width_m=
                    context.user_data[
                        "strip_width"
                    ],

                footing_thickness_m=
                    context.user_data[
                        "strip_thickness"
                    ],

                lean_length_m=0,
                lean_width_m=0,
                lean_thickness_m=0,

                longitudinal_diameter_mm=
                    context.user_data[
                        "strip_long_diameter"
                    ],

                longitudinal_count=
                    context.user_data[
                        "strip_long_count"
                    ],

                transverse_diameter_mm=
                    context.user_data[
                        "strip_trans_diameter"
                    ],

                transverse_spacing_mm=
                    context.user_data[
                        "strip_trans_spacing"
                    ],

                top_longitudinal_diameter_mm=
                    context.user_data[
                        "strip_top_long_diameter"
                    ],

                top_longitudinal_count=
                    context.user_data[
                        "strip_top_long_count"
                    ],

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
                reply_markup=result_keyboard(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}",
                reply_markup=step_keyboard(lang)
            )

        return

    # =====================================================
    # RAFT
    # =====================================================

    if step == "raft_length":

        context.user_data["raft_length"] = value

        await ask_next(
            update,
            context,
            "raft_width",
            2,
            11,
            "📐 عرض رادیه را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter raft width:"
        )

        return

    if step == "raft_width":

        context.user_data["raft_width"] = value

        await ask_next(
            update,
            context,
            "raft_thickness",
            3,
            11,
            "📐 ضخامت رادیه را وارد کنید:"
            if lang == "fa"
            else
            "📐 Enter raft thickness:"
        )

        return

    if step == "raft_thickness":

        context.user_data["raft_thickness"] = value

        await ask_next(
            update,
            context,
            "raft_bottom_x_diameter",
            4,
            11,
            "🔩 قطر میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom X rebar diameter (mm):"
        )

        return

    if step == "raft_bottom_x_diameter":

        context.user_data[
            "raft_bottom_x_diameter"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_bottom_x_spacing",
            5,
            11,
            "📏 فاصله میلگرد X پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom X spacing (mm):"
        )

        return

    if step == "raft_bottom_x_spacing":

        context.user_data[
            "raft_bottom_x_spacing"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_bottom_y_diameter",
            6,
            11,
            "🔩 قطر میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter bottom Y rebar diameter (mm):"
        )

        return

    if step == "raft_bottom_y_diameter":

        context.user_data[
            "raft_bottom_y_diameter"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_bottom_y_spacing",
            7,
            11,
            "📏 فاصله میلگرد Y پایین را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter bottom Y spacing (mm):"
        )

        return

    if step == "raft_bottom_y_spacing":

        context.user_data[
            "raft_bottom_y_spacing"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_top_x_diameter",
            8,
            11,
            "🔩 قطر میلگرد X بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top X rebar diameter (mm):"
        )

        return

    if step == "raft_top_x_diameter":

        context.user_data[
            "raft_top_x_diameter"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_top_x_spacing",
            9,
            11,
            "📏 فاصله میلگرد X بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top X spacing (mm):"
        )

        return

    if step == "raft_top_x_spacing":

        context.user_data[
            "raft_top_x_spacing"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_top_y_diameter",
            10,
            11,
            "🔩 قطر میلگرد Y بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "🔩 Enter top Y rebar diameter (mm):"
        )

        return

    if step == "raft_top_y_diameter":

        context.user_data[
            "raft_top_y_diameter"
        ] = int(value)

        await ask_next(
            update,
            context,
            "raft_top_y_spacing",
            11,
            11,
            "📏 فاصله میلگرد Y بالا را وارد کنید (mm):"
            if lang == "fa"
            else
            "📏 Enter top Y spacing (mm):"
        )

        return

    # =====================================================
    # FINAL RAFT
    # =====================================================

    if step == "raft_top_y_spacing":

        context.user_data[
            "raft_top_y_spacing"
        ] = int(value)

        try:

            result = raft_foundation(

                length_m=
                    context.user_data[
                        "raft_length"
                    ],

                width_m=
                    context.user_data[
                        "raft_width"
                    ],

                thickness_m=
                    context.user_data[
                        "raft_thickness"
                    ],

                lean_length_m=0,
                lean_width_m=0,
                lean_thickness_m=0,

                bottom_x_diameter_mm=
                    context.user_data[
                        "raft_bottom_x_diameter"
                    ],

                bottom_x_spacing_mm=
                    context.user_data[
                        "raft_bottom_x_spacing"
                    ],

                bottom_y_diameter_mm=
                    context.user_data[
                        "raft_bottom_y_diameter"
                    ],

                bottom_y_spacing_mm=
                    context.user_data[
                        "raft_bottom_y_spacing"
                    ],

                top_x_diameter_mm=
                    context.user_data[
                        "raft_top_x_diameter"
                    ],

                top_x_spacing_mm=
                    context.user_data[
                        "raft_top_x_spacing"
                    ],

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
                reply_markup=result_keyboard(lang)
            )

        except Exception as error:

            await update.message.reply_text(
                f"❌ خطا در محاسبه: {error}",
                reply_markup=step_keyboard(lang)
            )

        return


# =========================================================
# Previous Step
# =========================================================

async def previous_step(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    step = context.user_data.get(
        "step"
    )

    previous_map = {

        # Isolated
        "iso_length": (
            "iso_count",
            1,
            14,
            "🔢 تعداد پی‌ها را وارد کنید:"
        ),

        "iso_width": (
            "iso_length",
            2,
            14,
            "📏 طول پی را بر حسب متر وارد کنید:"
        ),

        "iso_thickness": (
            "iso_width",
            3,
            14,
            "📐 عرض پی را بر حسب متر وارد کنید:"
        ),

        "iso_bottom_diameter": (
            "iso_thickness",
            4,
            14,
            "📐 ضخامت پی را بر حسب متر وارد کنید:"
        ),

        "iso_bottom_spacing": (
            "iso_bottom_diameter",
            5,
            14,
            "🔩 قطر میلگرد شبکه پایین را وارد کنید (mm):"
        ),

        "iso_top_diameter": (
            "iso_bottom_spacing",
            6,
            14,
            "📏 فاصله میلگردهای شبکه پایین را وارد کنید (mm):"
        ),

        "iso_top_spacing": (
            "iso_top_diameter",
            7,
            14,
            "🔩 قطر میلگرد شبکه بالایی را وارد کنید (mm):"
        ),

        "iso_pedestal_length": (
            "iso_top_spacing",
            8,
            14,
            "📏 فاصله میلگردهای شبکه بالایی را وارد کنید (mm):"
        ),

        "iso_pedestal_width": (
            "iso_pedestal_length",
            9,
            14,
            "📏 طول پدستال را وارد کنید (m):"
        ),

        "iso_pedestal_height": (
            "iso_pedestal_width",
            10,
            14,
            "📐 عرض پدستال را وارد کنید (m):"
        ),

        "iso_starter_diameter": (
            "iso_pedestal_height",
            11,
            14,
            "📐 ارتفاع پدستال را وارد کنید (m):"
        ),

        "iso_starter_count": (
            "iso_starter_diameter",
            12,
            14,
            "🔩 قطر میلگردهای انتظار ستون را وارد کنید (mm):"
        ),

        "iso_starter_length": (
            "iso_starter_count",
            13,
            14,
            "🔢 تعداد میلگردهای انتظار هر پی را وارد کنید:"
        ),

        # Strip
        "strip_length": (
            "strip_count",
            1,
            12,
            "🔢 تعداد نوارها را وارد کنید:"
        ),

        "strip_width": (
            "strip_length",
            2,
            12,
            "📏 طول هر نوار را وارد کنید:"
        ),

        "strip_thickness": (
            "strip_width",
            3,
            12,
            "📐 عرض فونداسیون نواری را وارد کنید:"
        ),

        "strip_long_diameter": (
            "strip_thickness",
            4,
            12,
            "📐 ضخامت فونداسیون نواری را وارد کنید:"
        ),

        "strip_long_count": (
            "strip_long_diameter",
            5,
            12,
            "🔩 قطر میلگرد طولی تحتانی را وارد کنید (mm):"
        ),

        "strip_trans_diameter": (
            "strip_long_count",
            6,
            12,
            "🔢 تعداد میلگردهای طولی تحتانی را وارد کنید:"
        ),

        "strip_trans_spacing": (
            "strip_trans_diameter",
            7,
            12,
            "🔩 قطر میلگرد عرضی تحتانی را وارد کنید (mm):"
        ),

        "strip_top_long_diameter": (
            "strip_trans_spacing",
            8,
            12,
            "📏 فاصله میلگردهای عرضی تحتانی را وارد کنید (mm):"
        ),

        "strip_top_long_count": (
            "strip_top_long_diameter",
            9,
            12,
            "🔩 قطر میلگرد طولی فوقانی را وارد کنید (mm):"
        ),

        "strip_top_trans_diameter": (
            "strip_top_long_count",
            10,
            12,
            "🔢 تعداد میلگردهای طولی فوقانی را وارد کنید:"
        ),

        "strip_top_trans_spacing": (
            "strip_top_trans_diameter",
            11,
            12,
            "🔩 قطر میلگرد عرضی فوقانی را وارد کنید (mm):"
        ),

        # Raft
        "raft_width": (
            "raft_length",
            1,
            11,
            "📏 طول رادیه را بر حسب متر وارد کنید:"
        ),

        "raft_thickness": (
            "raft_width",
            2,
            11,
            "📐 عرض رادیه را وارد کنید:"
        ),

        "raft_bottom_x_diameter": (
            "raft_thickness",
            3,
            11,
            "📐 ضخامت رادیه را وارد کنید:"
        ),

        "raft_bottom_x_spacing": (
            "raft_bottom_x_diameter",
            4,
            11,
            "🔩 قطر میلگرد X پایین را وارد کنید (mm):"
        ),

        "raft_bottom_y_diameter": (
            "raft_bottom_x_spacing",
            5,
            11,
            "📏 فاصله میلگرد X پایین را وارد کنید (mm):"
        ),

        "raft_bottom_y_spacing": (
            "raft_bottom_y_diameter",
            6,
            11,
            "🔩 قطر میلگرد Y پایین را وارد کنید (mm):"
        ),

        "raft_top_x_diameter": (
            "raft_bottom_y_spacing",
            7,
            11,
            "📏 فاصله میلگرد Y پایین را وارد کنید (mm):"
        ),

        "raft_top_x_spacing": (
            "raft_top_x_diameter",
            8,
            11,
            "🔩 قطر میلگرد X بالا را وارد کنید (mm):"
        ),

        "raft_top_y_diameter": (
            "raft_top_x_spacing",
            9,
            11,
            "📏 فاصله میلگرد X بالا را وارد کنید (mm):"
        ),

        "raft_top_y_spacing": (
            "raft_top_y_diameter",
            10,
            11,
            "🔩 قطر میلگرد Y بالا را وارد کنید (mm):"
        ),
    }

    if step not in previous_map:

        await query.edit_message_text(
            TEXTS[lang]["choose_foundation"],
            parse_mode="HTML",
            reply_markup=foundation_menu(lang)
        )

        return

    previous_step_name, current, total, question = (
        previous_map[step]
    )

    context.user_data["step"] = previous_step_name

    await query.edit_message_text(
        step_message(
            lang,
            previous_step_name,
            current,
            total,
            question
        ),
        parse_mode="HTML",
        reply_markup=step_keyboard(lang)
    )


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

    # -----------------------------------------------------
    # Home
    # -----------------------------------------------------

    if data == "home":

        context.user_data.clear()

        context.user_data["lang"] = lang

        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

        return

    # -----------------------------------------------------
    # New Estimate
    # -----------------------------------------------------

    if data == "new_estimate":

        await new_estimate(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # Foundation Menu
    # -----------------------------------------------------

    if data == "foundation_menu":

        await show_foundation_menu(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # Foundation Selection
    # -----------------------------------------------------

    if data.startswith("foundation_"):

        await foundation_selected(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # Help
    # -----------------------------------------------------

    if data == "help":

        await query.edit_message_text(
            TEXTS[lang]["help_text"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        TEXTS[lang]["home"],
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    # -----------------------------------------------------
    # Previous
    # -----------------------------------------------------

    if data == "previous_step":

        await previous_step(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # Cancel
    # -----------------------------------------------------

    if data == "cancel_estimate":

        context.user_data.clear()

        context.user_data["lang"] = lang

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

    token = os.environ.get(
        "BOT_TOKEN"
    )

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
