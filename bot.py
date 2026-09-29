# bot.py
# -*- coding: utf-8 -*-

import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from calculations import (
    isolated_footing,
    strip_footing,
    raft_foundation,
    column_rectangular,
    column_round,
    beam,
    tie_beam,
    wall_concrete,
    stair_slab,
    roof_slab,
)


# =========================================================
# SETTINGS
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")


# =========================================================
# LANGUAGE
# =========================================================

TEXT = {
    "fa": {
        "home": "🏗️ اسکلت بتنی",
        "foundation": "🧱 فونداسیون",
        "columns": "🏛️ ستون‌ها",
        "beams": "📐 تیرها",
        "roofs": "🏠 سقف‌ها",
        "stairs": "🪜 راه‌پله",
        "ties": "🔗 شناژ و کلاف",
        "walls": "🧱 دیوارها",
        "summary": "📊 خلاصه پروژه",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "back": "🔙 بازگشت",
        "cancel": "❌ لغو",
        "rebar": "🔩 جزئیات میلگرد",
        "cutlist": "✂️ Cut List",
        "language": "🌐 زبان",
        "select_language": "زبان را انتخاب کنید:",
        "invalid": "❌ مقدار واردشده معتبر نیست. دوباره وارد کنید.",
        "cancelled": "❌ عملیات لغو شد.",
        "unknown": "دستور یا مقدار نامعتبر است.",
        "start": "به ربات برآورد اسکلت بتنی خوش آمدید.",
    },
    "en": {
        "home": "🏗️ Concrete Structure",
        "foundation": "🧱 Foundation",
        "columns": "🏛️ Columns",
        "beams": "📐 Beams",
        "roofs": "🏠 Roofs",
        "stairs": "🪜 Stairs",
        "ties": "🔗 Tie Beams",
        "walls": "🧱 Walls",
        "summary": "📊 Project Summary",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "back": "🔙 Back",
        "cancel": "❌ Cancel",
        "rebar": "🔩 Rebar Details",
        "cutlist": "✂️ Cut List",
        "language": "🌐 Language",
        "select_language": "Select language:",
        "invalid": "❌ Invalid value. Please try again.",
        "cancelled": "❌ Operation cancelled.",
        "unknown": "Unknown command or value.",
        "start": "Welcome to the Concrete Structure Estimation Bot.",
    },
}


# =========================================================
# COMMON HELPERS
# =========================================================

def lang(context):
    return context.user_data.get("lang", "fa")


def t(context, key):
    return TEXT[lang(context)].get(key, key)


def set_state(context, state):
    context.user_data["state"] = state


def get_state(context):
    return context.user_data.get("state")


def clear_state(context):
    context.user_data.pop("state", None)
    context.user_data.pop("data", None)


def get_data(context):
    if "data" not in context.user_data:
        context.user_data["data"] = {}
    return context.user_data["data"]


def menu_button(text, callback):
    return InlineKeyboardButton(text, callback_data=callback)


def home_keyboard(context):
    return InlineKeyboardMarkup([
        [
            menu_button(t(context, "foundation"), "foundation"),
            menu_button(t(context, "columns"), "columns"),
        ],
        [
            menu_button(t(context, "beams"), "beams"),
            menu_button(t(context, "roofs"), "roofs"),
        ],
        [
            menu_button(t(context, "stairs"), "stairs"),
            menu_button(t(context, "ties"), "ties"),
        ],
        [
            menu_button(t(context, "walls"), "walls"),
        ],
        [
            menu_button(t(context, "summary"), "summary"),
            menu_button(t(context, "settings"), "settings"),
        ],
        [
            menu_button(t(context, "help"), "help"),
        ],
    ])


async def show_home(update, context):
    clear_state(context)

    text = (
        f"{t(context, 'home')}\n\n"
        "🧱 فونداسیون    🏛️ ستون‌ها\n"
        "📐 تیرها        🏠 سقف‌ها\n"
        "🪜 راه‌پله      🔗 شناژ و کلاف\n"
        "🧱 دیوارها\n\n"
        "📊 خلاصه پروژه\n"
        "⚙️ تنظیمات      ℹ️ راهنما"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=home_keyboard(context),
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=home_keyboard(context),
        )


def back_keyboard(callback):
    return InlineKeyboardMarkup([
        [menu_button("🔙 بازگشت", callback)]
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(context)

    if "lang" not in context.user_data:
        keyboard = InlineKeyboardMarkup([
            [
                menu_button("🇮🇷 فارسی", "lang_fa"),
                menu_button("🇬🇧 English", "lang_en"),
            ]
        ])

        await update.message.reply_text(
            "زبان / Language:",
            reply_markup=keyboard,
        )
        return

    await show_home(update, context)


async def cb_language(update, context):
    query = update.callback_query
    await query.answer()

    selected = query.data.split("_", 1)[1]
    context.user_data["lang"] = selected

    await show_home(update, context)


# =========================================================
# FOUNDATION MENU
# =========================================================

async def foundation_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("پی منفرد", "foundation_isolated")],
        [menu_button("پی نواری", "foundation_strip")],
        [menu_button("پی گسترده / رادیه", "foundation_raft")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🧱 فونداسیون\n\nنوع فونداسیون را انتخاب کنید:",
        reply_markup=keyboard,
    )


# =========================================================
# ISOLATED FOOTING
# =========================================================

ISOLATED_FIELDS = [
    ("count", "تعداد پی"),
    ("length", "طول پی (m)"),
    ("width", "عرض پی (m)"),
    ("thickness", "ضخامت پی (m)"),
    ("lean_length", "طول بتن مگر (m)"),
    ("lean_width", "عرض بتن مگر (m)"),
    ("lean_thickness", "ضخامت بتن مگر (m)"),
    ("bottom_diameter", "قطر میلگرد پایین (mm)"),
    ("bottom_spacing", "فاصله میلگرد پایین (mm)"),
    ("top_diameter", "قطر میلگرد بالا (mm) - اگر ندارد 0"),
    ("top_spacing", "فاصله میلگرد بالا (mm) - اگر ندارد 0"),
    ("cover", "کاور (mm)"),
    ("lap", "درصد اورلپ"),
    ("pedestal_length", "طول پدستال (m)"),
    ("pedestal_width", "عرض پدستال (m)"),
    ("pedestal_height", "ارتفاع پدستال (m)"),
]


async def start_isolated(update, context):
    clear_state(context)

    data = get_data(context)
    data["index"] = 0
    data["fields"] = {}
    data["mode"] = "isolated"

    set_state(context, "isolated")

    await update.callback_query.edit_message_text(
        "🧱 پی منفرد\n\n"
        "اطلاعات را مرحله‌به‌مرحله وارد کنید.\n\n"
        f"تعداد پی را وارد کنید:"
    )


async def isolated_receive(update, context):
    data = get_data(context)

    index = data.get("index", 0)

    if index >= len(ISOLATED_FIELDS):
        return

    key, title = ISOLATED_FIELDS[index]

    try:
        value = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t(context, "invalid"))
        return

    data["fields"][key] = value
    data["index"] = index + 1

    if data["index"] < len(ISOLATED_FIELDS):
        _, next_title = ISOLATED_FIELDS[data["index"]]

        await update.message.reply_text(
            f"🧱 پی منفرد\n\n{next_title}:"
        )
        return

    await calculate_isolated(update, context)


async def calculate_isolated(update, context):
    data = get_data(context)
    f = data["fields"]

    try:
        result = isolated_footing(
            count=int(f["count"]),
            length_m=f["length"],
            width_m=f["width"],
            thickness_m=f["thickness"],
            lean_concrete_length_m=f["lean_length"],
            lean_concrete_width_m=f["lean_width"],
            lean_concrete_thickness_m=f["lean_thickness"],
            bottom_diameter_mm=int(f["bottom_diameter"]),
            bottom_spacing_mm=f["bottom_spacing"],
            top_diameter_mm=(
                int(f["top_diameter"])
                if f["top_diameter"] > 0 else None
            ),
            top_spacing_mm=(
                f["top_spacing"]
                if f["top_spacing"] > 0 else None
            ),
            cover_mm=f["cover"],
            lap_percent=f["lap"],
            pedestal_length_m=f["pedestal_length"],
            pedestal_width_m=f["pedestal_width"],
            pedestal_height_m=f["pedestal_height"],
        )

        data["result"] = result
        set_state(context, "isolated_result")

        await show_isolated_result(update, context)

    except Exception as e:
        logger.exception("isolated footing error")
        await update.message.reply_text(
            f"❌ خطا در محاسبه:\n{e}"
        )


async def show_isolated_result(update, context):
    result = get_data(context)["result"]

    concrete = result.get("structural_concrete_m3", 0)
    lean = result.get("lean_concrete_m3", 0)
    total_rebar = result.get("total_rebar_kg", 0)

    text = (
        "🏗️ نتیجه پی منفرد\n\n"
        "┌──────────────────────┐\n"
        f"│ بتن سازه‌ای: {concrete:.2f} m³\n"
        f"│ بتن مگر:      {lean:.2f} m³\n"
        f"│ میلگرد:       {total_rebar:.1f} kg\n"
        "└──────────────────────┘"
    )

    keyboard = InlineKeyboardMarkup([
        [menu_button("🔩 جزئیات میلگرد", "isolated_rebar")],
        [menu_button("✂️ Cut List", "isolated_cutlist")],
        [menu_button("🔙 فونداسیون", "foundation")],
        [menu_button("🏠 منوی اصلی", "home")],
    ])

    await update.message.reply_text(
        text,
        reply_markup=keyboard,
    )


async def isolated_rebar(update, context):
    result = get_data(context)["result"]

    details = result.get("rebar_details", [])

    if not details:
        text = "🔩 اطلاعات میلگرد موجود نیست."
    else:
        lines = ["🔩 میلگرد\n"]

        total = 0

        for item in details:
            diameter = item.get("diameter_mm", 0)
            weight = item.get("weight_kg", 0)
            pieces = item.get("pieces", 0)

            total += weight

            lines.append(
                f"Φ{diameter:<3} → "
                f"{weight:>8.1f} kg → "
                f"{pieces} قطعه"
            )

        lines.append(f"\nجمع میلگرد: {total:.1f} kg")
        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("isolated_result"),
    )


async def isolated_cutlist(update, context):
    result = get_data(context)["result"]

    cutlist = result.get("cut_list", [])

    if not cutlist:
        text = "✂️ Cut List موجود نیست."
    else:
        lines = [
            "✂️ Cut List\n",
            "قطر    طول قطعه    تعداد",
            "-------------------------",
        ]

        for item in cutlist:
            diameter = item.get("diameter_mm", 0)
            length = item.get("length_m", 0)
            count = item.get("count", 0)

            lines.append(
                f"Φ{diameter:<4} "
                f"{length:<10.2f} "
                f"{count}"
            )

        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("isolated_result"),
    )


# =========================================================
# GENERIC WIZARD
# =========================================================

async def start_generic(
    update,
    context,
    mode,
    title,
    fields,
    result_function,
    back_callback,
):
    clear_state(context)

    data = get_data(context)

    data["mode"] = mode
    data["index"] = 0
    data["fields"] = {}
    data["generic_fields"] = fields
    data["result_function"] = result_function
    data["back_callback"] = back_callback

    set_state(context, "generic")

    await update.callback_query.edit_message_text(
        f"{title}\n\n{fields[0][1]}:"
    )


async def generic_receive(update, context):
    data = get_data(context)

    fields = data["generic_fields"]
    index = data["index"]

    if index >= len(fields):
        return

    key, title = fields[index]

    try:
        value = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            t(context, "invalid")
        )
        return

    data["fields"][key] = value
    data["index"] = index + 1

    if data["index"] < len(fields):
        await update.message.reply_text(
            f"{fields[data['index']][1]}:"
        )
        return

    try:
        fn = data["result_function"]

        result = fn(data["fields"])

        data["result"] = result
        set_state(context, "generic_result")

        await show_generic_result(update, context)

    except Exception as e:
        logger.exception("generic calculation error")

        await update.message.reply_text(
            f"❌ خطا در محاسبه:\n{e}"
        )


async def show_generic_result(update, context):
    data = get_data(context)
    result = data["result"]

    concrete = result.get(
        "total_concrete_m3",
        result.get(
            "concrete",
            result.get("total_concrete", 0)
        )
    )

    rebar = result.get(
        "total_rebar_kg",
        result.get(
            "rebar_weight",
            0
        )
    )

    title = data.get("mode", "نتیجه")

    text = (
        f"🏗️ نتیجه {title}\n\n"
        "┌──────────────────────┐\n"
        f"│ بتن:     {concrete:.2f} m³\n"
        f"│ میلگرد:  {rebar:.1f} kg\n"
        "└──────────────────────┘"
    )

    keyboard = InlineKeyboardMarkup([
        [menu_button("🔩 جزئیات میلگرد", "generic_rebar")],
        [menu_button("✂️ Cut List", "generic_cutlist")],
        [
            menu_button(
                "🔙 بازگشت",
                data.get("back_callback", "home")
            )
        ],
        [menu_button("🏠 منوی اصلی", "home")],
    ])

    await update.message.reply_text(
        text,
        reply_markup=keyboard,
    )


async def generic_rebar(update, context):
    result = get_data(context)["result"]

    details = result.get("rebar_details", [])

    if not details:
        text = "🔩 اطلاعات جزئی میلگرد موجود نیست."
    else:
        lines = ["🔩 میلگرد\n"]

        total = 0

        for item in details:
            diameter = item.get("diameter_mm", 0)
            weight = item.get("weight_kg", 0)
            pieces = item.get("pieces", 0)

            total += weight

            lines.append(
                f"Φ{diameter:<3} → "
                f"{weight:>8.1f} kg → "
                f"{pieces} قطعه"
            )

        lines.append(f"\nجمع میلگرد: {total:.1f} kg")

        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("generic_result"),
    )


async def generic_cutlist(update, context):
    result = get_data(context)["result"]

    cutlist = result.get("cut_list", [])

    if not cutlist:
        text = "✂️ Cut List موجود نیست."
    else:
        lines = [
            "✂️ Cut List\n",
            "قطر    طول قطعه    تعداد",
            "-------------------------",
        ]

        for item in cutlist:
            diameter = item.get("diameter_mm", 0)
            length = item.get("length_m", 0)
            count = item.get("count", 0)

            lines.append(
                f"Φ{diameter:<4} "
                f"{length:<10.2f} "
                f"{count}"
            )

        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("generic_result"),
    )


# =========================================================
# STRIP FOOTING
# =========================================================

async def start_strip(update, context):
    fields = [
        ("strip_count", "تعداد نوارها"),
        ("strip_length", "طول هر نوار (m)"),
        ("footing_width", "عرض پی (m)"),
        ("footing_thickness", "ضخامت پی (m)"),
        ("lean_length", "طول بتن مگر (m)"),
        ("lean_width", "عرض بتن مگر (m)"),
        ("lean_thickness", "ضخامت بتن مگر (m)"),
        ("longitudinal_diameter", "قطر میلگرد طولی (mm)"),
        ("longitudinal_count", "تعداد میلگرد طولی"),
        ("transverse_diameter", "قطر میلگرد عرضی (mm)"),
        ("transverse_spacing", "فاصله میلگرد عرضی (mm)"),
        ("top_longitudinal_diameter", "قطر میلگرد طولی بالا - 0 اگر ندارد"),
        ("top_longitudinal_count", "تعداد میلگرد طولی بالا"),
        ("top_transverse_diameter", "قطر میلگرد عرضی بالا - 0 اگر ندارد"),
        ("top_transverse_spacing", "فاصله میلگرد عرضی بالا"),
        ("cover", "کاور (mm)"),
        ("lap", "درصد اورلپ"),
    ]

    def calc(f):
        return strip_footing(
            strip_count=int(f["strip_count"]),
            strip_length_m=f["strip_length"],
            footing_width_m=f["footing_width"],
            footing_thickness_m=f["footing_thickness"],
            lean_length_m=f["lean_length"],
            lean_width_m=f["lean_width"],
            lean_thickness_m=f["lean_thickness"],
            longitudinal_diameter_mm=int(f["longitudinal_diameter"]),
            longitudinal_count=int(f["longitudinal_count"]),
            transverse_diameter_mm=int(f["transverse_diameter"]),
            transverse_spacing_mm=f["transverse_spacing"],
            top_longitudinal_diameter_mm=(
                int(f["top_longitudinal_diameter"])
                if f["top_longitudinal_diameter"] > 0 else None
            ),
            top_longitudinal_count=(
                int(f["top_longitudinal_count"])
                if f["top_longitudinal_count"] > 0 else None
            ),
            top_transverse_diameter_mm=(
                int(f["top_transverse_diameter"])
                if f["top_transverse_diameter"] > 0 else None
            ),
            top_transverse_spacing_mm=(
                f["top_transverse_spacing"]
                if f["top_transverse_spacing"] > 0 else None
            ),
            cover_mm=f["cover"],
            lap_percent=f["lap"],
        )

    await start_generic(
        update,
        context,
        "پی نواری",
        "🧱 پی نواری",
        fields,
        calc,
        "foundation",
    )


# =========================================================
# RAFT
# =========================================================

async def start_raft(update, context):
    fields = [
        ("length", "طول رادیه (m)"),
        ("width", "عرض رادیه (m)"),
        ("thickness", "ضخامت رادیه (m)"),
        ("lean_length", "طول بتن مگر (m)"),
        ("lean_width", "عرض بتن مگر (m)"),
        ("lean_thickness", "ضخامت بتن مگر (m)"),
        ("bottom_x_diameter", "قطر میلگرد پایین X (mm)"),
        ("bottom_x_spacing", "فاصله پایین X (mm)"),
        ("bottom_y_diameter", "قطر میلگرد پایین Y (mm)"),
        ("bottom_y_spacing", "فاصله پایین Y (mm)"),
        ("top_x_diameter", "قطر میلگرد بالا X - 0 اگر ندارد"),
        ("top_x_spacing", "فاصله بالا X"),
        ("top_y_diameter", "قطر میلگرد بالا Y - 0 اگر ندارد"),
        ("top_y_spacing", "فاصله بالا Y"),
        ("cover", "کاور (mm)"),
        ("lap", "درصد اورلپ"),
    ]

    def calc(f):
        return raft_foundation(
            length_m=f["length"],
            width_m=f["width"],
            thickness_m=f["thickness"],
            lean_length_m=f["lean_length"],
            lean_width_m=f["lean_width"],
            lean_thickness_m=f["lean_thickness"],
            bottom_x_diameter_mm=int(f["bottom_x_diameter"]),
            bottom_x_spacing_mm=f["bottom_x_spacing"],
            bottom_y_diameter_mm=int(f["bottom_y_diameter"]),
            bottom_y_spacing_mm=f["bottom_y_spacing"],
            top_x_diameter_mm=(
                int(f["top_x_diameter"])
                if f["top_x_diameter"] > 0 else None
            ),
            top_x_spacing_mm=(
                f["top_x_spacing"]
                if f["top_x_diameter"] > 0 else None
            ),
            top_y_diameter_mm=(
                int(f["top_y_diameter"])
                if f["top_y_diameter"] > 0 else None
            ),
            top_y_spacing_mm=(
                f["top_y_spacing"]
                if f["top_y_diameter"] > 0 else None
            ),
            cover_mm=f["cover"],
            lap_percent=f["lap"],
        )

    await start_generic(
        update,
        context,
        "پی گسترده",
        "🧱 پی گسترده / رادیه",
        fields,
        calc,
        "foundation",
    )


# =========================================================
# COLUMNS
# =========================================================

async def columns_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("ستون مربعی / مستطیلی", "column_rect")],
        [menu_button("ستون گرد", "column_round")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🏛️ ستون‌ها\n\nنوع ستون را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def start_column_rect(update, context):
    fields = [
        ("count", "تعداد ستون"),
        ("length", "طول ستون (m)"),
        ("width", "عرض ستون (m)"),
        ("height", "ارتفاع ستون (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("main_count", "تعداد میلگرد اصلی"),
        ("tie_diameter", "قطر خاموت (mm)"),
        ("tie_spacing", "فاصله خاموت (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return column_rectangular(
            count=int(f["count"]),
            length_m=f["length"],
            width_m=f["width"],
            height_m=f["height"],
            main_diameter_mm=int(f["main_diameter"]),
            main_count=int(f["main_count"]),
            tie_diameter_mm=int(f["tie_diameter"]),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "ستون مستطیلی",
        "🏛️ ستون مربعی / مستطیلی",
        fields,
        calc,
        "columns",
    )


async def start_column_round(update, context):
    fields = [
        ("count", "تعداد ستون"),
        ("diameter", "قطر ستون (m)"),
        ("height", "ارتفاع ستون (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("main_count", "تعداد میلگرد اصلی"),
        ("tie_diameter", "قطر خاموت (mm)"),
        ("tie_spacing", "فاصله خاموت (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return column_round(
            count=int(f["count"]),
            diameter_m=f["diameter"],
            height_m=f["height"],
            main_diameter_mm=int(f["main_diameter"]),
            main_count=int(f["main_count"]),
            tie_diameter_mm=int(f["tie_diameter"]),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "ستون گرد",
        "🏛️ ستون گرد",
        fields,
        calc,
        "columns",
    )


# =========================================================
# BEAMS
# =========================================================

async def beams_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("تیر اصلی", "beam_main")],
        [menu_button("تیر فرعی", "beam_secondary")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "📐 تیرها\n\nنوع تیر را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def start_beam(update, context):
    fields = [
        ("count", "تعداد تیر"),
        ("length", "طول هر تیر (m)"),
        ("width", "عرض تیر (m)"),
        ("height", "ارتفاع تیر (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("main_count", "تعداد میلگرد اصلی"),
        ("top_diameter", "قطر میلگرد بالایی (mm)"),
        ("top_count", "تعداد میلگرد بالایی"),
        ("tie_diameter", "قطر خاموت (mm)"),
        ("tie_spacing", "فاصله خاموت (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return beam(
            count=int(f["count"]),
            length_m=f["length"],
            width_m=f["width"],
            height_m=f["height"],
            main_diameter_mm=int(f["main_diameter"]),
            main_count=int(f["main_count"]),
            top_diameter_mm=int(f["top_diameter"]),
            top_count=int(f["top_count"]),
            tie_diameter_mm=int(f["tie_diameter"]),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    mode = get_data(context).get("beam_mode", "تیر اصلی")

    await start_generic(
        update,
        context,
        mode,
        f"📐 {mode}",
        fields,
        calc,
        "beams",
    )


async def beam_main(update, context):
    get_data(context)["beam_mode"] = "تیر اصلی"
    await start_beam(update, context)


async def beam_secondary(update, context):
    get_data(context)["beam_mode"] = "تیر فرعی"
    await start_beam(update, context)


# =========================================================
# ROOFS
# =========================================================

async def roofs_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("تیرچه یونولیتی", "roof_poly")],
        [menu_button("تیرچه سفالی", "roof_clay")],
        [menu_button("تیرچه دوبل", "roof_double")],
        [menu_button("کرومیت", "roof_kromit")],
        [menu_button("کامپوزیت", "roof_composite")],
        [menu_button("عرشه فولادی", "roof_deck")],
        [menu_button("دال بتنی", "roof_slab")],
        [menu_button("وافل", "roof_waffle")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🏠 سقف‌ها\n\nنوع سقف را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def start_roof(update, context, roof_type):
    fields = [
        ("area", "مساحت سقف (m²)"),
        ("rebar_kg_m2", "مصرف میلگرد (kg/m²)"),
    ]

    def calc(f):
        return roof_slab(
            area_m2=f["area"],
            roof_type=roof_type,
            rebar_kg_m2=f["rebar_kg_m2"],
        )

    await start_generic(
        update,
        context,
        roof_type,
        f"🏠 {roof_type}",
        fields,
        calc,
        "roofs",
    )


async def roof_poly(update, context):
    await start_roof(update, context, "تیرچه یونولیتی")


async def roof_clay(update, context):
    await start_roof(update, context, "تیرچه سفالی")


async def roof_double(update, context):
    await start_roof(update, context, "تیرچه دوبل")


async def roof_kromit(update, context):
    await start_roof(update, context, "کرومیت")


async def roof_composite(update, context):
    await start_roof(update, context, "کامپوزیت")


async def roof_deck(update, context):
    await start_roof(update, context, "عرشه فولادی")


async def roof_slab_menu(update, context):
    await start_roof(update, context, "دال بتنی")


async def roof_waffle(update, context):
    await start_roof(update, context, "وافل")


# =========================================================
# STAIRS
# =========================================================

async def start_stair(update, context):
    fields = [
        ("count", "تعداد راه‌پله"),
        ("width", "عرض راه‌پله (m)"),
        ("length", "طول شیب/مسیر (m)"),
        ("thickness", "ضخامت دال (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("main_spacing", "فاصله میلگرد اصلی (mm)"),
        ("distribution_diameter", "قطر میلگرد توزیعی (mm)"),
        ("distribution_spacing", "فاصله میلگرد توزیعی (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return stair_slab(
            count=int(f["count"]),
            width_m=f["width"],
            length_m=f["length"],
            thickness_m=f["thickness"],
            main_diameter_mm=int(f["main_diameter"]),
            main_spacing_mm=f["main_spacing"],
            distribution_diameter_mm=int(
                f["distribution_diameter"]
            ),
            distribution_spacing_mm=f["distribution_spacing"],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "راه‌پله",
        "🪜 راه‌پله",
        fields,
        calc,
        "home",
    )


# =========================================================
# TIE BEAMS
# =========================================================

async def ties_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("شناژ", "tie_beam")],
        [menu_button("کلاف", "tie_cowl")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🔗 شناژ و کلاف\n\nانتخاب کنید:",
        reply_markup=keyboard,
    )


async def start_tie(update, context):
    fields = [
        ("count", "تعداد"),
        ("length", "طول هر قطعه (m)"),
        ("width", "عرض (m)"),
        ("height", "ارتفاع (m)"),
        ("main_diameter", "قطر میلگرد طولی (mm)"),
        ("main_count", "تعداد میلگرد طولی"),
        ("tie_diameter", "قطر خاموت (mm)"),
        ("tie_spacing", "فاصله خاموت (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return tie_beam(
            count=int(f["count"]),
            length_m=f["length"],
            width_m=f["width"],
            height_m=f["height"],
            main_diameter_mm=int(f["main_diameter"]),
            main_count=int(f["main_count"]),
            tie_diameter_mm=int(f["tie_diameter"]),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    mode = get_data(context).get("tie_mode", "شناژ")

    await start_generic(
        update,
        context,
        mode,
        f"🔗 {mode}",
        fields,
        calc,
        "ties",
    )


async def tie_beam_start(update, context):
    get_data(context)["tie_mode"] = "شناژ"
    await start_tie(update, context)


async def tie_cowl(update, context):
    get_data(context)["tie_mode"] = "کلاف"
    await start_tie(update, context)


# =========================================================
# WALLS
# =========================================================

async def walls_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("دیوار برشی", "wall_shear")],
        [menu_button("دیوار حائل", "wall_retaining")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🧱 دیوارها\n\nنوع دیوار را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def start_wall(update, context):
    fields = [
        ("count", "تعداد دیوار"),
        ("length", "طول دیوار (m)"),
        ("height", "ارتفاع دیوار (m)"),
        ("thickness", "ضخامت دیوار (m)"),
        ("vertical_diameter", "قطر میلگرد قائم (mm)"),
        ("vertical_spacing", "فاصله میلگرد قائم (mm)"),
        ("horizontal_diameter", "قطر میلگرد افقی (mm)"),
        ("horizontal_spacing", "فاصله میلگرد افقی (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):
        return wall_concrete(
            count=int(f["count"]),
            length_m=f["length"],
            height_m=f["height"],
            thickness_m=f["thickness"],
            vertical_diameter_mm=int(f["vertical_diameter"]),
            vertical_spacing_mm=f["vertical_spacing"],
            horizontal_diameter_mm=int(
                f["horizontal_diameter"]
            ),
            horizontal_spacing_mm=f["horizontal_spacing"],
            cover_mm=f["cover"],
        )

    mode = get_data(context).get("wall_mode", "دیوار برشی")

    await start_generic(
        update,
        context,
        mode,
        f"🧱 {mode}",
        fields,
        calc,
        "walls",
    )


async def wall_shear(update, context):
    get_data(context)["wall_mode"] = "دیوار برشی"
    await start_wall(update, context)


async def wall_retaining(update, context):
    get_data(context)["wall_mode"] = "دیوار حائل"
    await start_wall(update, context)


# =========================================================
# SUMMARY
# =========================================================

async def project_summary(update, context):
    clear_state(context)

    text = (
        "📊 خلاصه پروژه\n\n"
        "فعلاً این بخش آماده اتصال به محاسبات تجمعی پروژه است.\n\n"
        "در نسخه بعدی می‌توانیم نتایج فونداسیون، "
        "ستون، تیر، سقف، راه‌پله، شناژ و دیوار را "
        "در یک جمع کل نمایش دهیم."
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("home"),
    )


# =========================================================
# SETTINGS
# =========================================================

async def settings_menu(update, context):
    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [menu_button("🇮🇷 فارسی", "lang_fa")],
        [menu_button("🇬🇧 English", "lang_en")],
        [menu_button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "⚙️ تنظیمات\n\n"
        "زبان را انتخاب کنید:",
        reply_markup=keyboard,
    )


# =========================================================
# HELP
# =========================================================

async def help_menu(update, context):
    clear_state(context)

    text = (
        "ℹ️ راهنما\n\n"
        "این ربات برای برآورد اولیه مقادیر اسکلت بتنی "
        "طراحی شده است.\n\n"
        "📌 برای نتیجه دقیق‌تر باید ابعاد واقعی عضو، "
        "آرایش میلگرد و جزئیات نقشه وارد شود.\n\n"
        "🔩 جزئیات میلگرد و ✂️ Cut List به‌صورت "
        "جداگانه نمایش داده می‌شوند."
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_keyboard("home"),
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def buttons(update, context):
    query = update.callback_query
    await query.answer()

    callback = query.data

    # ---------- HOME ----------
    if callback == "home":
        await show_home(update, context)
        return

    # ---------- FOUNDATION ----------
    if callback == "foundation":
        await foundation_menu(update, context)
        return

    if callback == "foundation_isolated":
        await start_isolated(update, context)
        return

    if callback == "foundation_strip":
        await start_strip(update, context)
        return

    if callback == "foundation_raft":
        await start_raft(update, context)
        return

    if callback == "isolated_result":
        await show_isolated_result(update, context)
        return

    if callback == "isolated_rebar":
        await isolated_rebar(update, context)
        return

    if callback == "isolated_cutlist":
        await isolated_cutlist(update, context)
        return

    # ---------- COLUMNS ----------
    if callback == "columns":
        await columns_menu(update, context)
        return

    if callback == "column_rect":
        await start_column_rect(update, context)
        return

    if callback == "column_round":
        await start_column_round(update, context)
        return

    # ---------- BEAMS ----------
    if callback == "beams":
        await beams_menu(update, context)
        return

    if callback == "beam_main":
        await beam_main(update, context)
        return

    if callback == "beam_secondary":
        await beam_secondary(update, context)
        return

    # ---------- ROOFS ----------
    if callback == "roofs":
        await roofs_menu(update, context)
        return

    if callback == "roof_poly":
        await roof_poly(update, context)
        return

    if callback == "roof_clay":
        await roof_clay(update, context)
        return

    if callback == "roof_double":
        await roof_double(update, context)
        return

    if callback == "roof_kromit":
        await roof_kromit(update, context)
        return

    if callback == "roof_composite":
        await roof_composite(update, context)
        return

    if callback == "roof_deck":
        await roof_deck(update, context)
        return

    if callback == "roof_slab":
        await roof_slab_menu(update, context)
        return

    if callback == "roof_waffle":
        await roof_waffle(update, context)
        return

    # ---------- STAIRS ----------
    if callback == "stairs":
        await start_stair(update, context)
        return

    # ---------- TIES ----------
    if callback == "ties":
        await ties_menu(update, context)
        return

    if callback == "tie_beam":
        await tie_beam_start(update, context)
        return

    if callback == "tie_cowl":
        await tie_cowl(update, context)
        return

    # ---------- WALLS ----------
    if callback == "walls":
        await walls_menu(update, context)
        return

    if callback == "wall_shear":
        await wall_shear(update, context)
        return

    if callback == "wall_retaining":
        await wall_retaining(update, context)
        return

    # ---------- GENERIC ----------
    if callback == "generic_result":
        await show_generic_result(update, context)
        return

    if callback == "generic_rebar":
        await generic_rebar(update, context)
        return

    if callback == "generic_cutlist":
        await generic_cutlist(update, context)
        return

    # ---------- SUMMARY ----------
    if callback == "summary":
        await project_summary(update, context)
        return

    # ---------- SETTINGS ----------
    if callback == "settings":
        await settings_menu(update, context)
        return

    # ---------- HELP ----------
    if callback == "help":
        await help_menu(update, context)
        return

    await query.edit_message_text(
        t(context, "unknown"),
        reply_markup=back_keyboard("home"),
    )


# =========================================================
# TEXT MESSAGE ROUTER
# =========================================================

async def receive(update, context):
    state = get_state(context)

    if state == "isolated":
        await isolated_receive(update, context)
        return

    if state == "generic":
        await generic_receive(update, context)
        return

    await update.message.reply_text(
        "لطفاً از منوی ربات استفاده کنید."
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):
    logger.exception(
        "Unhandled exception:",
        exc_info=context.error,
    )


# =========================================================
# MAIN - RENDER WEBHOOK
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    if not RENDER_EXTERNAL_URL:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL environment variable is not set."
        )

    webhook_url = (
        RENDER_EXTERNAL_URL.rstrip("/")
        + "/telegram"
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler("start", start)
    )

    # Language
    application.add_handler(
        CallbackQueryHandler(
            cb_language,
            pattern=r"^lang_(fa|en)$"
        )
    )

    # All inline buttons
    application.add_handler(
        CallbackQueryHandler(buttons)
    )

    # Text input
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive
        )
    )

    # Error handler
    application.add_error_handler(error_handler)

    print("======================================")
    print("Concrete Structure Bot")
    print("Render Webhook Mode")
    print("======================================")
    print(f"Port: {PORT}")
    print(f"Webhook: {webhook_url}")
    print("Bot started successfully.")
    print("======================================")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
