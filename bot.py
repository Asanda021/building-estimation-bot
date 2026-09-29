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
# TEXT
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
        "previous": "⬅️ مرحله قبل",
        "cancel": "❌ لغو",
        "rebar": "🔩 جزئیات میلگرد",
        "cutlist": "✂️ Cut List",
        "invalid": "❌ مقدار واردشده معتبر نیست.",
    }
}


def t(context, key):
    return TEXT["fa"].get(key, key)


# =========================================================
# USER STATE
# =========================================================

def clear_state(context):
    context.user_data.clear()


def get_data(context):
    if "data" not in context.user_data:
        context.user_data["data"] = {}
    return context.user_data["data"]


# =========================================================
# KEYBOARDS
# =========================================================

def button(text, callback):
    return InlineKeyboardButton(
        text,
        callback_data=callback
    )


def home_keyboard():
    return InlineKeyboardMarkup([
        [
            button("🧱 فونداسیون", "foundation"),
            button("🏛️ ستون‌ها", "columns"),
        ],
        [
            button("📐 تیرها", "beams"),
            button("🏠 سقف‌ها", "roofs"),
        ],
        [
            button("🪜 راه‌پله", "stairs"),
            button("🔗 شناژ و کلاف", "ties"),
        ],
        [
            button("🧱 دیوارها", "walls"),
        ],
        [
            button("📊 خلاصه پروژه", "summary"),
            button("⚙️ تنظیمات", "settings"),
        ],
        [
            button("ℹ️ راهنما", "help"),
        ],
    ])


# =========================================================
# HOME
# =========================================================

async def show_home(update, context):

    clear_state(context)

    text = (
        "🏗️ اسکلت بتنی\n\n"
        "🧱 فونداسیون    🏛️ ستون‌ها\n"
        "📐 تیرها        🏠 سقف‌ها\n"
        "🪜 راه‌پله      🔗 شناژ و کلاف\n"
        "🧱 دیوارها\n\n"
        "📊 خلاصه پروژه\n"
        "⚙️ تنظیمات      ℹ️ راهنما"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=home_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=home_keyboard()
        )


async def start(update, context):

    clear_state(context)

    await update.message.reply_text(
        "🏗️ به ربات برآورد اسکلت بتنی خوش آمدید.",
        reply_markup=home_keyboard()
    )


# =========================================================
# FOUNDATION MENU
# =========================================================

async def foundation_menu(update, context):

    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [button("پی منفرد", "foundation_isolated")],
        [button("پی نواری", "foundation_strip")],
        [button("پی گسترده / رادیه", "foundation_raft")],
        [button("🔙 بازگشت", "home")],
    ])

    await update.callback_query.edit_message_text(
        "🧱 فونداسیون\n\n"
        "نوع فونداسیون را انتخاب کنید:",
        reply_markup=keyboard
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

    data["mode"] = "isolated"
    data["index"] = 0
    data["fields"] = {}

    await update.callback_query.edit_message_text(
        "🧱 پی منفرد\n\n"
        "برای شروع تعداد پی را وارد کنید:"
    )


async def isolated_receive(update, context):

    data = get_data(context)

    index = data.get("index", 0)

    if index >= len(ISOLATED_FIELDS):
        return

    key, title = ISOLATED_FIELDS[index]

    try:
        value = float(
            update.message.text.strip().replace(",", ".")
        )
    except ValueError:

        await update.message.reply_text(
            "❌ لطفاً فقط عدد وارد کنید."
        )
        return

    data["fields"][key] = value
    data["index"] = index + 1

    # هنوز اطلاعات باقی مانده
    if data["index"] < len(ISOLATED_FIELDS):

        next_title = ISOLATED_FIELDS[data["index"]][1]

        keyboard = InlineKeyboardMarkup([
            [
                button(
                    "⬅️ مرحله قبل",
                    "isolated_previous"
                )
            ],
            [
                button(
                    "❌ لغو",
                    "foundation"
                )
            ],
        ])

        await update.message.reply_text(
            f"✅ ثبت شد.\n\n"
            f"{next_title}:",
            reply_markup=keyboard
        )

        return

    # آخرین فیلد
    await calculate_isolated(update, context)


# =========================================================
# PREVIOUS ISOLATED
# =========================================================

async def isolated_previous(update, context):

    query = update.callback_query
    await query.answer()

    data = get_data(context)

    index = data.get("index", 0)

    if index <= 0:
        await query.answer(
            "این اولین مرحله است.",
            show_alert=True
        )
        return

    index -= 1

    key, title = ISOLATED_FIELDS[index]

    data["index"] = index
    data["fields"].pop(key, None)

    await query.edit_message_text(
        f"⬅️ مرحله قبل\n\n"
        f"{title}:"
    )


# =========================================================
# CALCULATE ISOLATED
# =========================================================

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

            bottom_diameter_mm=int(
                f["bottom_diameter"]
            ),
            bottom_spacing_mm=f["bottom_spacing"],

            top_diameter_mm=(
                int(f["top_diameter"])
                if f["top_diameter"] > 0
                else None
            ),

            top_spacing_mm=(
                f["top_spacing"]
                if f["top_spacing"] > 0
                else None
            ),

            cover_mm=f["cover"],
            lap_percent=f["lap"],

            pedestal_length_m=f["pedestal_length"],
            pedestal_width_m=f["pedestal_width"],
            pedestal_height_m=f["pedestal_height"],
        )

        data["result"] = result

        await show_isolated_result(
            update,
            context
        )

    except Exception as e:

        logger.exception(
            "Isolated footing calculation error"
        )

        await update.message.reply_text(
            "❌ خطا در محاسبه:\n\n"
            f"{str(e)}"
        )


# =========================================================
# RESULT HELPERS
# =========================================================

def get_number(result, *keys):

    for key in keys:

        value = result.get(key)

        if value is not None:
            try:
                return float(value)
            except:
                pass

    return 0.0


def get_rebar_details(result):

    details = result.get("rebar_details")

    if details:
        return details

    details = result.get("rebar")

    if isinstance(details, list):
        return details

    if isinstance(details, dict):

        output = []

        for diameter, item in details.items():

            if isinstance(item, dict):

                output.append({
                    "diameter_mm": diameter,
                    "weight_kg": item.get(
                        "weight_kg",
                        item.get("weight", 0)
                    ),
                    "pieces": item.get(
                        "pieces",
                        item.get("count", 0)
                    ),
                })

        return output

    return []


# =========================================================
# ISOLATED RESULT
# =========================================================

async def show_isolated_result(update, context):

    result = get_data(context)["result"]

    footing_concrete = get_number(
        result,
        "footing_concrete_m3",
        "concrete_m3"
    )

    pedestal_concrete = get_number(
        result,
        "pedestal_concrete_m3"
    )

    lean_concrete = get_number(
        result,
        "lean_concrete_m3",
        "lean_concrete"
    )

    structural_concrete = get_number(
        result,
        "structural_concrete_m3"
    )

    if structural_concrete == 0:

        structural_concrete = (
            footing_concrete +
            pedestal_concrete
        )

    total_concrete = (
        structural_concrete +
        lean_concrete
    )

    total_rebar = get_number(
        result,
        "total_rebar_kg",
        "rebar_weight"
    )

    text = (
        "🏗️ نتیجه پی منفرد\n\n"
        "```text\n"
        "┌────────────────────────┐\n"
        f"│ تعداد پی       {int(result.get('count', get_data(context)['fields']['count'])):>5} │\n"
        f"│ بتن پی        {footing_concrete:>7.2f} m³ │\n"
        f"│ پدستال        {pedestal_concrete:>7.2f} m³ │\n"
        f"│ بتن مگر       {lean_concrete:>7.2f} m³ │\n"
        "│ ────────────────────── │\n"
        f"│ کل بتن        {total_concrete:>7.2f} m³ │\n"
        f"│ کل میلگرد     {total_rebar:>7.1f} kg │\n"
        "└────────────────────────┘\n"
        "```"
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "🔩 جزئیات میلگرد",
                "isolated_rebar"
            )
        ],
        [
            button(
                "✂️ Cut List",
                "isolated_cutlist"
            )
        ],
        [
            button(
                "🧱 فونداسیون",
                "foundation"
            ),
            button(
                "🏠 منوی اصلی",
                "home"
            )
        ],
    ])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# =========================================================
# REBAR RESULT
# =========================================================

async def isolated_rebar(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context)["result"]

    details = get_rebar_details(result)

    if not details:

        text = (
            "🔩 جزئیات میلگرد\n\n"
            "اطلاعات میلگرد در خروجی محاسبات پیدا نشد."
        )

    else:

        lines = [
            "🔩 جزئیات میلگرد",
            "",
            "```text",
            "قطر       وزن        تعداد",
            "────────────────────────",
        ]

        total = 0

        for item in details:

            diameter = item.get(
                "diameter_mm",
                0
            )

            weight = float(
                item.get(
                    "weight_kg",
                    0
                )
            )

            pieces = int(
                item.get(
                    "pieces",
                    0
                )
            )

            total += weight

            lines.append(
                f"Φ{diameter:<4}"
                f"{weight:>9.1f} kg"
                f"{pieces:>8}"
            )

        lines.extend([
            "────────────────────────",
            f"جمع      {total:>9.1f} kg",
            "```",
        ])

        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "⬅️ نتیجه",
                "isolated_result"
            )
        ],
        [
            button(
                "🏠 منوی اصلی",
                "home"
            )
        ],
    ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# =========================================================
# CUT LIST
# =========================================================

async def isolated_cutlist(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context)["result"]

    cutlist = result.get(
        "cut_list",
        []
    )

    if not cutlist:

        # بعضی نسخه‌های calculations ممکن است
        # نام دیگری برای Cut List داشته باشند.
        cutlist = result.get(
            "cutlist",
            result.get(
                "cut_list_details",
                []
            )
        )

    if not cutlist:

        text = (
            "✂️ Cut List\n\n"
            "در خروجی فعلی Cut List ثبت نشده است."
        )

    else:

        lines = [
            "✂️ Cut List",
            "",
            "```text",
            "قطر      طول قطعه      تعداد",
            "──────────────────────────",
        ]

        for item in cutlist:

            diameter = item.get(
                "diameter_mm",
                0
            )

            length = item.get(
                "length_m",
                item.get(
                    "piece_length_m",
                    0
                )
            )

            count = item.get(
                "count",
                item.get(
                    "pieces",
                    0
                )
            )

            lines.append(
                f"Φ{diameter:<5}"
                f"{float(length):>8.2f} m"
                f"{int(count):>8}"
            )

        lines.append(
            "```"
        )

        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "⬅️ نتیجه",
                "isolated_result"
            )
        ],
        [
            button(
                "🏠 منوی اصلی",
                "home"
            )
        ],
    ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# =========================================================
# COLUMNS MENU
# =========================================================

async def columns_menu(update, context):

    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [button(
            "ستون مربعی / مستطیلی",
            "column_rect"
        )],
        [button(
            "ستون گرد",
            "column_round"
        )],
        [button(
            "🔙 بازگشت",
            "home"
        )],
    ])

    await update.callback_query.edit_message_text(
        "🏛️ ستون‌ها\n\n"
        "نوع ستون را انتخاب کنید:",
        reply_markup=keyboard
    )


# =========================================================
# GENERIC CALCULATION
# =========================================================

async def start_generic(
    update,
    context,
    mode,
    title,
    fields,
    calculation_function,
    back_callback
):

    clear_state(context)

    data = get_data(context)

    data["mode"] = mode
    data["title"] = title
    data["fields_list"] = fields
    data["fields"] = {}
    data["index"] = 0
    data["calculation_function"] = calculation_function
    data["back_callback"] = back_callback

    await update.callback_query.edit_message_text(
        f"{title}\n\n"
        f"{fields[0][1]}:"
    )


async def generic_receive(update, context):

    data = get_data(context)

    fields = data["fields_list"]
    index = data["index"]

    key, title = fields[index]

    try:

        value = float(
            update.message.text
            .strip()
            .replace(",", ".")
        )

    except ValueError:

        await update.message.reply_text(
            "❌ لطفاً فقط عدد وارد کنید."
        )

        return

    data["fields"][key] = value
    data["index"] = index + 1

    if data["index"] < len(fields):

        next_title = fields[data["index"]][1]

        keyboard = InlineKeyboardMarkup([
            [
                button(
                    "⬅️ مرحله قبل",
                    "generic_previous"
                )
            ],
            [
                button(
                    "❌ لغو",
                    data["back_callback"]
                )
            ],
        ])

        await update.message.reply_text(
            f"✅ ثبت شد.\n\n"
            f"{next_title}:",
            reply_markup=keyboard
        )

        return

    try:

        fn = data["calculation_function"]

        result = fn(data["fields"])

        data["result"] = result

        await show_generic_result(
            update,
            context
        )

    except Exception as e:

        logger.exception(
            "Generic calculation error"
        )

        await update.message.reply_text(
            "❌ خطا در محاسبه:\n\n"
            f"{str(e)}"
        )


async def generic_previous(update, context):

    query = update.callback_query
    await query.answer()

    data = get_data(context)

    index = data["index"]

    if index <= 0:

        await query.answer(
            "این اولین مرحله است.",
            show_alert=True
        )

        return

    index -= 1

    key, title = data["fields_list"][index]

    data["index"] = index
    data["fields"].pop(key, None)

    await query.edit_message_text(
        f"⬅️ مرحله قبل\n\n"
        f"{title}:"
    )


# =========================================================
# GENERIC RESULT
# =========================================================

async def show_generic_result(update, context):

    data = get_data(context)
    result = data["result"]

    concrete = get_number(
        result,
        "total_concrete_m3",
        "concrete",
        "total_concrete"
    )

    rebar = get_number(
        result,
        "total_rebar_kg",
        "rebar_weight"
    )

    title = data.get(
        "title",
        "نتیجه"
    )

    text = (
        f"🏗️ {title}\n\n"
        "```text\n"
        "┌──────────────────────┐\n"
        f"│ بتن       {concrete:>8.2f} m³ │\n"
        f"│ میلگرد    {rebar:>8.1f} kg │\n"
        "└──────────────────────┘\n"
        "```"
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "🔩 جزئیات میلگرد",
                "generic_rebar"
            )
        ],
        [
            button(
                "✂️ Cut List",
                "generic_cutlist"
            )
        ],
        [
            button(
                "🔙 بازگشت",
                data.get(
                    "back_callback",
                    "home"
                )
            ),
            button(
                "🏠 خانه",
                "home"
            )
        ],
    ])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def generic_rebar(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context)["result"]

    details = get_rebar_details(result)

    if not details:

        text = (
            "🔩 جزئیات میلگرد\n\n"
            "اطلاعاتی موجود نیست."
        )

    else:

        lines = [
            "🔩 جزئیات میلگرد",
            "",
            "```text",
            "قطر       وزن        تعداد",
            "────────────────────────",
        ]

        total = 0

        for item in details:

            diameter = item.get(
                "diameter_mm",
                0
            )

            weight = float(
                item.get(
                    "weight_kg",
                    0
                )
            )

            pieces = int(
                item.get(
                    "pieces",
                    0
                )
            )

            total += weight

            lines.append(
                f"Φ{diameter:<4}"
                f"{weight:>9.1f} kg"
                f"{pieces:>8}"
            )

        lines.extend([
            "────────────────────────",
            f"جمع      {total:>9.1f} kg",
            "```",
        ])

        text = "\n".join(lines)

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "⬅️ نتیجه",
                    "generic_result"
                )
            ],
            [
                button(
                    "🏠 خانه",
                    "home"
                )
            ],
        ])
    )


async def generic_cutlist(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context)["result"]

    cutlist = result.get(
        "cut_list",
        result.get(
            "cutlist",
            []
        )
    )

    if not cutlist:

        text = (
            "✂️ Cut List\n\n"
            "در خروجی فعلی موجود نیست."
        )

    else:

        lines = [
            "✂️ Cut List",
            "",
            "```text",
            "قطر      طول قطعه      تعداد",
            "──────────────────────────",
        ]

        for item in cutlist:

            diameter = item.get(
                "diameter_mm",
                0
            )

            length = item.get(
                "length_m",
                item.get(
                    "piece_length_m",
                    0
                )
            )

            count = item.get(
                "count",
                item.get(
                    "pieces",
                    0
                )
            )

            lines.append(
                f"Φ{diameter:<5}"
                f"{float(length):>8.2f} m"
                f"{int(count):>8}"
            )

        lines.append("```")

        text = "\n".join(lines)

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "⬅️ نتیجه",
                    "generic_result"
                )
            ],
            [
                button(
                    "🏠 خانه",
                    "home"
                )
            ],
        ])
    )


# =========================================================
# SIMPLE SECTION MENUS
# =========================================================

async def beams_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "📐 تیرها\n\n"
        "نوع تیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [button("تیر اصلی", "beam_main")],
            [button("تیر فرعی", "beam_secondary")],
            [button("🔙 بازگشت", "home")],
        ])
    )


async def roofs_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🏠 سقف‌ها\n\n"
        "نوع سقف را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [button("تیرچه یونولیتی", "roof_poly")],
            [button("تیرچه سفالی", "roof_clay")],
            [button("تیرچه دوبل", "roof_double")],
            [button("کرومیت", "roof_kromit")],
            [button("کامپوزیت", "roof_composite")],
            [button("عرشه فولادی", "roof_deck")],
            [button("دال بتنی", "roof_slab")],
            [button("وافل", "roof_waffle")],
            [button("🔙 بازگشت", "home")],
        ])
    )


async def ties_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🔗 شناژ و کلاف\n\n"
        "انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [button("شناژ", "tie_beam")],
            [button("کلاف", "tie_cowl")],
            [button("🔙 بازگشت", "home")],
        ])
    )


async def walls_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🧱 دیوارها\n\n"
        "نوع دیوار را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [button("دیوار برشی", "wall_shear")],
            [button("دیوار حائل", "wall_retaining")],
            [button("🔙 بازگشت", "home")],
        ])
    )


# =========================================================
# COLUMN FUNCTIONS
# =========================================================

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
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_count=int(
                f["main_count"]
            ),
            tie_diameter_mm=int(
                f["tie_diameter"]
            ),
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
        "columns"
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
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_count=int(
                f["main_count"]
            ),
            tie_diameter_mm=int(
                f["tie_diameter"]
            ),
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
        "columns"
    )


# =========================================================
# BEAM
# =========================================================

async def start_beam(update, context, beam_type):

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
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_count=int(
                f["main_count"]
            ),
            top_diameter_mm=int(
                f["top_diameter"]
            ),
            top_count=int(
                f["top_count"]
            ),
            tie_diameter_mm=int(
                f["tie_diameter"]
            ),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        beam_type,
        f"📐 {beam_type}",
        fields,
        calc,
        "beams"
    )


# =========================================================
# ROOF
# =========================================================

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
        "roofs"
    )


# =========================================================
# STAIR
# =========================================================

async def start_stair(update, context):

    fields = [
        ("count", "تعداد راه‌پله"),
        ("width", "عرض راه‌پله (m)"),
        ("length", "طول مسیر (m)"),
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
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_spacing_mm=f["main_spacing"],
            distribution_diameter_mm=int(
                f["distribution_diameter"]
            ),
            distribution_spacing_mm=f[
                "distribution_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "راه‌پله",
        "🪜 راه‌پله",
        fields,
        calc,
        "home"
    )


# =========================================================
# TIE BEAM
# =========================================================

async def start_tie(update, context, tie_type):

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
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_count=int(
                f["main_count"]
            ),
            tie_diameter_mm=int(
                f["tie_diameter"]
            ),
            tie_spacing_mm=f["tie_spacing"],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        tie_type,
        f"🔗 {tie_type}",
        fields,
        calc,
        "ties"
    )


# =========================================================
# WALL
# =========================================================

async def start_wall(update, context, wall_type):

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
            vertical_diameter_mm=int(
                f["vertical_diameter"]
            ),
            vertical_spacing_mm=f[
                "vertical_spacing"
            ],
            horizontal_diameter_mm=int(
                f["horizontal_diameter"]
            ),
            horizontal_spacing_mm=f[
                "horizontal_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        wall_type,
        f"🧱 {wall_type}",
        fields,
        calc,
        "walls"
    )


# =========================================================
# SUMMARY / SETTINGS / HELP
# =========================================================

async def summary_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "📊 خلاصه پروژه\n\n"
        "این بخش در مرحله بعد به جمع کل "
        "تمام اعضای پروژه متصل می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [button("🔙 بازگشت", "home")]
        ])
    )


async def settings_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "⚙️ تنظیمات\n\n"
        "تنظیمات پروژه در نسخه بعدی تکمیل می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [button("🔙 بازگشت", "home")]
        ])
    )


async def help_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "ℹ️ راهنما\n\n"
        "این ربات برای برآورد اولیه مقادیر "
        "اسکلت بتنی طراحی شده است.\n\n"
        "برای نتیجه دقیق‌تر باید ابعاد و جزئیات "
        "واقعی نقشه وارد شوند.",
        reply_markup=InlineKeyboardMarkup([
            [button("🔙 بازگشت", "home")]
        ])
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def buttons(update, context):

    query = update.callback_query

    await query.answer()

    callback = query.data

    # HOME
    if callback == "home":
        await show_home(update, context)
        return

    # FOUNDATION
    if callback == "foundation":
        await foundation_menu(update, context)
        return

    if callback == "foundation_isolated":
        await start_isolated(update, context)
        return

    if callback == "isolated_previous":
        await isolated_previous(update, context)
        return

    if callback == "isolated_rebar":
        await isolated_rebar(update, context)
        return

    if callback == "isolated_cutlist":
        await isolated_cutlist(update, context)
        return

    # GENERIC
    if callback == "generic_previous":
        await generic_previous(update, context)
        return

    if callback == "generic_rebar":
        await generic_rebar(update, context)
        return

    if callback == "generic_cutlist":
        await generic_cutlist(update, context)
        return

    # COLUMNS
    if callback == "columns":
        await columns_menu(update, context)
        return

    if callback == "column_rect":
        await start_column_rect(update, context)
        return

    if callback == "column_round":
        await start_column_round(update, context)
        return

    # BEAMS
    if callback == "beams":
        await beams_menu(update, context)
        return

    if callback == "beam_main":
        await start_beam(
            update,
            context,
            "تیر اصلی"
        )
        return

    if callback == "beam_secondary":
        await start_beam(
            update,
            context,
            "تیر فرعی"
        )
        return

    # ROOFS
    if callback == "roofs":
        await roofs_menu(update, context)
        return

    if callback == "roof_poly":
        await start_roof(
            update,
            context,
            "تیرچه یونولیتی"
        )
        return

    if callback == "roof_clay":
        await start_roof(
            update,
            context,
            "تیرچه سفالی"
        )
        return

    if callback == "roof_double":
        await start_roof(
            update,
            context,
            "تیرچه دوبل"
        )
        return

    if callback == "roof_kromit":
        await start_roof(
            update,
            context,
            "کرومیت"
        )
        return

    if callback == "roof_composite":
        await start_roof(
            update,
            context,
            "کامپوزیت"
        )
        return

    if callback == "roof_deck":
        await start_roof(
            update,
            context,
            "عرشه فولادی"
        )
        return

    if callback == "roof_slab":
        await start_roof(
            update,
            context,
            "دال بتنی"
        )
        return

    if callback == "roof_waffle":
        await start_roof(
            update,
            context,
            "وافل"
        )
        return

    # STAIRS
    if callback == "stairs":
        await start_stair(update, context)
        return

    # TIES
    if callback == "ties":
        await ties_menu(update, context)
        return

    if callback == "tie_beam":
        await start_tie(
            update,
            context,
            "شناژ"
        )
        return

    if callback == "tie_cowl":
        await start_tie(
            update,
            context,
            "کلاف"
        )
        return

    # WALLS
    if callback == "walls":
        await walls_menu(update, context)
        return

    if callback == "wall_shear":
        await start_wall(
            update,
            context,
            "دیوار برشی"
        )
        return

    if callback == "wall_retaining":
        await start_wall(
            update,
            context,
            "دیوار حائل"
        )
        return

    # SUMMARY
    if callback == "summary":
        await summary_menu(update, context)
        return

    # SETTINGS
    if callback == "settings":
        await settings_menu(update, context)
        return

    # HELP
    if callback == "help":
        await help_menu(update, context)
        return

    # RESULT
    if callback == "isolated_result":

        await show_isolated_result(
            update,
            context
        )

        return

    await query.edit_message_text(
        "❌ گزینه نامعتبر است.",
        reply_markup=InlineKeyboardMarkup([
            [button("🏠 خانه", "home")]
        ])
    )


# =========================================================
# MESSAGE ROUTER
# =========================================================

async def receive(update, context):

    data = context.user_data.get(
        "data",
        {}
    )

    mode = data.get("mode")

    if mode == "isolated":

        await isolated_receive(
            update,
            context
        )

        return

    if data.get("fields_list"):

        await generic_receive(
            update,
            context
        )

        return

    await update.message.reply_text(
        "لطفاً از منوی ربات استفاده کنید.",
        reply_markup=home_keyboard()
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    logger.exception(
        "Unhandled exception:",
        exc_info=context.error
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
            "RENDER_EXTERNAL_URL environment variable "
            "is not set."
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

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive
        )
    )

    application.add_error_handler(
        error_handler
    )

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
