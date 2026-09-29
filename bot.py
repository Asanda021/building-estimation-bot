# bot.py
# -*- coding: utf-8 -*-

import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
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
# CONSTANTS
# =========================================================

MENU_TEXT = "☰ منو"


# =========================================================
# PERSISTENT BOTTOM MENU
# =========================================================

def bottom_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(MENU_TEXT)
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="انتخاب از منوی ربات..."
    )


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
# BUTTON
# =========================================================

def button(text, callback):
    return InlineKeyboardButton(
        text=text,
        callback_data=callback
    )


# =========================================================
# MAIN INLINE MENU
# =========================================================

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

HOME_TEXT = (
    "🏗️ <b>برآورد اسکلت بتنی</b>\n\n"
    "سیستم برآورد اولیه مقادیر مصالح و میلگرد\n"
    "برای اعضای مختلف اسکلت بتنی.\n\n"
    "👇 بخش موردنظر را انتخاب کنید:"
)


async def show_home(update, context):

    clear_state(context)

    if update.callback_query:

        await update.callback_query.edit_message_text(
            HOME_TEXT,
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )

    else:

        await update.message.reply_text(
            HOME_TEXT,
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )


async def start(update, context):

    clear_state(context)

    await update.message.reply_text(
        "🏗️ <b>به ربات برآورد اسکلت بتنی خوش آمدید.</b>\n\n"
        "برای شروع روی «☰ منو» بزنید.",
        parse_mode="HTML",
        reply_markup=bottom_menu()
    )

    await update.message.reply_text(
        HOME_TEXT,
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )


# =========================================================
# FOUNDATION MENU
# =========================================================

async def foundation_menu(update, context):

    clear_state(context)

    keyboard = InlineKeyboardMarkup([
        [
            button("◼️ پی منفرد", "foundation_isolated")
        ],
        [
            button("▬ پی نواری", "foundation_strip")
        ],
        [
            button("▣ پی گسترده / رادیه", "foundation_raft")
        ],
        [
            button("🔙 بازگشت", "home")
        ],
    ])

    await update.callback_query.edit_message_text(
        "🧱 <b>فونداسیون</b>\n\n"
        "نوع فونداسیون را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# FIELD HELPERS
# =========================================================

def parse_number(text):

    text = text.strip()

    text = text.replace(",", ".")
    text = text.replace("٫", ".")

    return float(text)


def fmt(value, decimals=2):

    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return "0"


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
    ("top_diameter", "قطر میلگرد بالا (mm) — اگر ندارد 0"),
    ("top_spacing", "فاصله میلگرد بالا (mm) — اگر ندارد 0"),
    ("cover", "کاور (mm)"),
    ("lap", "درصد اورلپ"),
    ("pedestal_length", "طول پدستال (m)"),
    ("pedestal_width", "عرض پدستال (m)"),
    ("pedestal_height", "ارتفاع پدستال (m)"),
]


def wizard_keyboard(back_callback):

    return InlineKeyboardMarkup([
        [
            button("⬅️ مرحله قبل", "wizard_previous")
        ],
        [
            button("❌ لغو", back_callback)
        ],
    ])


async def start_isolated(update, context):

    clear_state(context)

    data = get_data(context)

    data["mode"] = "isolated"
    data["fields"] = {}
    data["index"] = 0
    data["parent"] = "foundation"

    await update.callback_query.edit_message_text(
        "🧱 <b>محاسبه پی منفرد</b>\n\n"
        "مرحله ۱ از ۱۶\n\n"
        "تعداد پی را وارد کنید:",
        parse_mode="HTML",
        reply_markup=wizard_keyboard("foundation")
    )


async def isolated_receive(update, context):

    data = get_data(context)

    index = data.get("index", 0)

    if index >= len(ISOLATED_FIELDS):
        return

    key, title = ISOLATED_FIELDS[index]

    try:
        value = parse_number(update.message.text)

    except ValueError:

        await update.message.reply_text(
            "❌ مقدار واردشده معتبر نیست.\n"
            "لطفاً فقط عدد وارد کنید.",
            reply_markup=wizard_keyboard("foundation")
        )
        return

    if value < 0:

        await update.message.reply_text(
            "❌ مقدار نمی‌تواند منفی باشد."
        )
        return

    data["fields"][key] = value
    data["index"] = index + 1

    if data["index"] < len(ISOLATED_FIELDS):

        next_title = ISOLATED_FIELDS[
            data["index"]
        ][1]

        await update.message.reply_text(
            f"✅ ثبت شد.\n\n"
            f"مرحله {data['index'] + 1} از "
            f"{len(ISOLATED_FIELDS)}\n\n"
            f"<b>{next_title}</b>:",
            parse_mode="HTML",
            reply_markup=wizard_keyboard("foundation")
        )

        return

    await calculate_isolated(update, context)


# =========================================================
# GENERIC PREVIOUS
# =========================================================

async def wizard_previous(update, context):

    query = update.callback_query
    await query.answer()

    data = get_data(context)

    mode = data.get("mode")

    if mode == "isolated":

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
            f"⬅️ <b>مرحله قبل</b>\n\n"
            f"مرحله {index + 1} از "
            f"{len(ISOLATED_FIELDS)}\n\n"
            f"<b>{title}</b>:",
            parse_mode="HTML",
            reply_markup=wizard_keyboard("foundation")
        )

        return

    fields = data.get("fields_list")

    if fields:

        index = data.get("index", 0)

        if index <= 0:

            await query.answer(
                "این اولین مرحله است.",
                show_alert=True
            )
            return

        index -= 1

        key, title = fields[index]

        data["index"] = index
        data["fields"].pop(key, None)

        await query.edit_message_text(
            f"⬅️ <b>مرحله قبل</b>\n\n"
            f"مرحله {index + 1} از {len(fields)}\n\n"
            f"<b>{title}</b>:",
            parse_mode="HTML",
            reply_markup=wizard_keyboard(
                data.get("back_callback", "home")
            )
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
            "❌ <b>خطا در محاسبه</b>\n\n"
            f"{str(e)}",
            parse_mode="HTML"
        )


# =========================================================
# REBAR HELPERS
# =========================================================

def get_rebar_summary(result):

    rebar = result.get("rebar", {})

    if not isinstance(rebar, dict):
        return {
            "details": [],
            "total_weight": 0,
            "total_length": 0,
        }

    return {
        "details": rebar.get("details", []),
        "total_weight": float(
            rebar.get("total_weight", 0)
        ),
        "total_length": float(
            rebar.get("total_length", 0)
        ),
    }


def get_total_rebar(result):

    rebar = result.get("rebar", {})

    if isinstance(rebar, dict):

        return float(
            rebar.get(
                "total_weight",
                0
            )
        )

    return 0


# =========================================================
# RESULT KEYBOARD
# =========================================================

def result_keyboard(
    rebar_callback,
    cutlist_callback,
    back_callback
):

    return InlineKeyboardMarkup([
        [
            button(
                "🔩 جزئیات میلگرد",
                rebar_callback
            )
        ],
        [
            button(
                "✂️ Cut List",
                cutlist_callback
            )
        ],
        [
            button(
                "🔙 بازگشت",
                back_callback
            ),
            button(
                "🏠 خانه",
                "home"
            )
        ],
    ])


# =========================================================
# ISOLATED RESULT
# =========================================================

async def show_isolated_result(update, context):

    data = get_data(context)
    result = data.get("result")

    if not result:
        return

    footing_concrete = float(
        result.get("footing_concrete", 0)
    )

    pedestal_concrete = float(
        result.get("pedestal_concrete", 0)
    )

    lean_concrete = float(
        result.get("lean_concrete", 0)
    )

    total_concrete = float(
        result.get("total_concrete", 0)
    )

    total_rebar = get_total_rebar(result)

    count = int(
        result.get(
            "count",
            data["fields"].get("count", 0)
        )
    )

    text = (
        "🏗️ <b>نتیجه پی منفرد</b>\n\n"
        "```text\n"
        "┌────────────────────────┐\n"
        f"│ تعداد پی      {count:>6} عدد │\n"
        f"│ بتن پی        {footing_concrete:>6.2f} m³ │\n"
        f"│ پدستال        {pedestal_concrete:>6.2f} m³ │\n"
        f"│ بتن مگر       {lean_concrete:>6.2f} m³ │\n"
        "│────────────────────────│\n"
        f"│ کل بتن        {total_concrete:>6.2f} m³ │\n"
        f"│ کل میلگرد     {total_rebar:>6.1f} kg │\n"
        "└────────────────────────┘\n"
        "```"
    )

    keyboard = result_keyboard(
        "isolated_rebar",
        "isolated_cutlist",
        "foundation"
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# =========================================================
# ISOLATED REBAR
# =========================================================

async def isolated_rebar(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context).get("result", {})

    summary = get_rebar_summary(result)
    details = summary["details"]

    lines = [
        "🔩 <b>جزئیات میلگرد پی</b>",
        "",
        "```text",
        "قطر      قطعه      طول      وزن",
        "────────────────────────────",
    ]

    if not details:

        lines.append(
            "اطلاعات میلگرد موجود نیست."
        )

    else:

        for item in details:

            diameter = item.get(
                "diameter",
                0
            )

            pieces = item.get(
                "pieces",
                0
            )

            length = item.get(
                "piece_length",
                0
            )

            weight = item.get(
                "weight",
                0
            )

            lines.append(
                f"Φ{int(diameter):<5}"
                f"{int(pieces):>6}"
                f"{float(length):>9.2f}"
                f"{float(weight):>9.1f}"
            )

        lines.append(
            "────────────────────────────"
        )

        lines.append(
            f"جمع میلگرد: "
            f"{summary['total_weight']:.1f} kg"
        )

    lines.append("```")

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "⬅️ نتیجه",
                "isolated_result"
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
                "🏠 خانه",
                "home"
            )
        ],
    ])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# CUT LIST
# =========================================================

async def isolated_cutlist(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context).get("result", {})

    summary = get_rebar_summary(result)
    details = summary["details"]

    lines = [
        "✂️ <b>Cut List</b>",
        "",
        "```text",
        "قطر      طول قطعه      تعداد",
        "──────────────────────────",
    ]

    if not details:

        lines.append(
            "اطلاعات برش موجود نیست."
        )

    else:

        for item in details:

            diameter = item.get(
                "diameter",
                0
            )

            length = item.get(
                "piece_length",
                0
            )

            pieces = item.get(
                "pieces",
                0
            )

            lines.append(
                f"Φ{int(diameter):<6}"
                f"{float(length):>8.2f} m"
                f"{int(pieces):>8}"
            )

    lines.append("```")

    lines.append(
        "\n⚠️ Cut List فعلی بر اساس طول قطعات محاسباتی "
        "است و هنوز بهینه‌سازی واقعی شاخه‌های ۱۲ متری "
        "در خروجی نهایی متصل نشده است."
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "⬅️ نتیجه",
                "isolated_result"
            )
        ],
        [
            button(
                "🔩 میلگرد",
                "isolated_rebar"
            )
        ],
        [
            button(
                "🏠 خانه",
                "home"
            )
        ],
    ])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# STRIP FOOTING
# =========================================================

async def start_strip(update, context):

    fields = [
        ("count", "تعداد نوار"),
        ("length", "طول نوار (m)"),
        ("width", "عرض پی (m)"),
        ("thickness", "ضخامت پی (m)"),
        ("lean_length", "طول بتن مگر (m)"),
        ("lean_width", "عرض بتن مگر (m)"),
        ("lean_thickness", "ضخامت بتن مگر (m)"),
        ("long_diameter", "قطر میلگرد طولی پایین (mm)"),
        ("long_count", "تعداد میلگرد طولی پایین"),
        ("trans_diameter", "قطر میلگرد عرضی پایین (mm)"),
        ("trans_spacing", "فاصله میلگرد عرضی پایین (mm)"),
        ("top_long_diameter", "قطر میلگرد طولی بالا (mm) — اگر ندارد 0"),
        ("top_long_count", "تعداد میلگرد طولی بالا — اگر ندارد 0"),
        ("top_trans_diameter", "قطر میلگرد عرضی بالا (mm) — اگر ندارد 0"),
        ("top_trans_spacing", "فاصله میلگرد عرضی بالا (mm) — اگر ندارد 0"),
        ("cover", "کاور (mm)"),
        ("lap", "درصد اورلپ"),
    ]

    def calc(f):

        return strip_footing(
            strip_count=int(f["count"]),
            strip_length_m=f["length"],
            footing_width_m=f["width"],
            footing_thickness_m=f["thickness"],
            lean_length_m=f["lean_length"],
            lean_width_m=f["lean_width"],
            lean_thickness_m=f["lean_thickness"],
            longitudinal_diameter_mm=int(
                f["long_diameter"]
            ),
            longitudinal_count=int(
                f["long_count"]
            ),
            transverse_diameter_mm=int(
                f["trans_diameter"]
            ),
            transverse_spacing_mm=f["trans_spacing"],
            top_longitudinal_diameter_mm=(
                int(f["top_long_diameter"])
                if f["top_long_diameter"] > 0
                else None
            ),
            top_longitudinal_count=(
                int(f["top_long_count"])
                if f["top_long_count"] > 0
                else None
            ),
            top_transverse_diameter_mm=(
                int(f["top_trans_diameter"])
                if f["top_trans_diameter"] > 0
                else None
            ),
            top_transverse_spacing_mm=(
                f["top_trans_spacing"]
                if f["top_trans_spacing"] > 0
                else None
            ),
            cover_mm=f["cover"],
            lap_percent=f["lap"],
        )

    await start_generic(
        update,
        context,
        "strip",
        "▬ پی نواری",
        fields,
        calc,
        "foundation"
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
        ("bottom_x_spacing", "فاصله میلگرد پایین X (mm)"),
        ("bottom_y_diameter", "قطر میلگرد پایین Y (mm)"),
        ("bottom_y_spacing", "فاصله میلگرد پایین Y (mm)"),
        ("top_x_diameter", "قطر میلگرد بالا X (mm) — اگر ندارد 0"),
        ("top_x_spacing", "فاصله میلگرد بالا X (mm) — اگر ندارد 0"),
        ("top_y_diameter", "قطر میلگرد بالا Y (mm) — اگر ندارد 0"),
        ("top_y_spacing", "فاصله میلگرد بالا Y (mm) — اگر ندارد 0"),
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
            bottom_x_diameter_mm=int(
                f["bottom_x_diameter"]
            ),
            bottom_x_spacing_mm=f["bottom_x_spacing"],
            bottom_y_diameter_mm=int(
                f["bottom_y_diameter"]
            ),
            bottom_y_spacing_mm=f["bottom_y_spacing"],
            top_x_diameter_mm=(
                int(f["top_x_diameter"])
                if f["top_x_diameter"] > 0
                else None
            ),
            top_x_spacing_mm=(
                f["top_x_spacing"]
                if f["top_x_spacing"] > 0
                else None
            ),
            top_y_diameter_mm=(
                int(f["top_y_diameter"])
                if f["top_y_diameter"] > 0
                else None
            ),
            top_y_spacing_mm=(
                f["top_y_spacing"]
                if f["top_y_spacing"] > 0
                else None
            ),
            cover_mm=f["cover"],
            lap_percent=f["lap"],
        )

    await start_generic(
        update,
        context,
        "raft",
        "▣ پی گسترده / رادیه",
        fields,
        calc,
        "foundation"
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
        f"🏗️ <b>{title}</b>\n\n"
        f"مرحله 1 از {len(fields)}\n\n"
        f"<b>{fields[0][1]}</b>:",
        parse_mode="HTML",
        reply_markup=wizard_keyboard(back_callback)
    )


async def generic_receive(update, context):

    data = get_data(context)

    fields = data.get("fields_list", [])
    index = data.get("index", 0)

    if index >= len(fields):
        return

    key, title = fields[index]

    try:

        value = parse_number(
            update.message.text
        )

    except ValueError:

        await update.message.reply_text(
            "❌ لطفاً فقط عدد وارد کنید."
        )
        return

    if value < 0:

        await update.message.reply_text(
            "❌ مقدار نمی‌تواند منفی باشد."
        )
        return

    data["fields"][key] = value
    data["index"] = index + 1

    if data["index"] < len(fields):

        next_title = fields[
            data["index"]
        ][1]

        await update.message.reply_text(
            f"✅ ثبت شد.\n\n"
            f"مرحله {data['index'] + 1} از "
            f"{len(fields)}\n\n"
            f"<b>{next_title}</b>:",
            parse_mode="HTML",
            reply_markup=wizard_keyboard(
                data["back_callback"]
            )
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
            "❌ <b>خطا در محاسبه</b>\n\n"
            f"{str(e)}",
            parse_mode="HTML"
        )


# =========================================================
# GENERIC RESULT
# =========================================================

async def show_generic_result(update, context):

    data = get_data(context)
    result = data.get("result", {})

    concrete = float(
        result.get("total_concrete", 0)
    )

    if concrete == 0:
        concrete = float(
            result.get("concrete", 0)
        )

    rebar = get_total_rebar(result)

    title = data.get(
        "title",
        "نتیجه محاسبه"
    )

    text = (
        f"🏗️ <b>نتیجه {title}</b>\n\n"
        "```text\n"
        "┌────────────────────────┐\n"
        f"│ کل بتن       {concrete:>7.2f} m³ │\n"
        f"│ کل میلگرد    {rebar:>7.1f} kg │\n"
        "└────────────────────────┘\n"
        "```"
    )

    keyboard = result_keyboard(
        "generic_rebar",
        "generic_cutlist",
        data.get(
            "back_callback",
            "home"
        )
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


async def generic_rebar(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context).get("result", {})

    summary = get_rebar_summary(result)
    details = summary["details"]

    lines = [
        "🔩 <b>جزئیات میلگرد</b>",
        "",
        "```text",
        "قطر      قطعه      طول      وزن",
        "────────────────────────────",
    ]

    if not details:

        lines.append(
            "اطلاعات میلگرد موجود نیست."
        )

    else:

        for item in details:

            diameter = item.get(
                "diameter",
                0
            )

            pieces = item.get(
                "pieces",
                0
            )

            length = item.get(
                "piece_length",
                0
            )

            weight = item.get(
                "weight",
                0
            )

            lines.append(
                f"Φ{int(diameter):<5}"
                f"{int(pieces):>6}"
                f"{float(length):>9.2f}"
                f"{float(weight):>9.1f}"
            )

        lines.append(
            "────────────────────────────"
        )

        lines.append(
            f"جمع میلگرد: "
            f"{summary['total_weight']:.1f} kg"
        )

    lines.append("```")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "⬅️ نتیجه",
                    "generic_result"
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
                    "🏠 خانه",
                    "home"
                )
            ],
        ])
    )


async def generic_cutlist(update, context):

    query = update.callback_query
    await query.answer()

    result = get_data(context).get("result", {})

    summary = get_rebar_summary(result)
    details = summary["details"]

    lines = [
        "✂️ <b>Cut List</b>",
        "",
        "```text",
        "قطر      طول قطعه      تعداد",
        "──────────────────────────",
    ]

    if not details:

        lines.append(
            "اطلاعات برش موجود نیست."
        )

    else:

        for item in details:

            diameter = item.get(
                "diameter",
                0
            )

            length = item.get(
                "piece_length",
                0
            )

            pieces = item.get(
                "pieces",
                0
            )

            lines.append(
                f"Φ{int(diameter):<6}"
                f"{float(length):>8.2f} m"
                f"{int(pieces):>8}"
            )

    lines.append("```")

    lines.append(
        "\n⚠️ این Cut List فعلاً بر اساس "
        "طول قطعات محاسباتی است."
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "⬅️ نتیجه",
                    "generic_result"
                )
            ],
            [
                button(
                    "🔩 میلگرد",
                    "generic_rebar"
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
# COLUMNS MENU
# =========================================================

async def columns_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🏛️ <b>ستون‌ها</b>\n\n"
        "نوع ستون را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "ستون مربعی / مستطیلی",
                    "column_rect"
                )
            ],
            [
                button(
                    "ستون گرد",
                    "column_round"
                )
            ],
            [
                button(
                    "🔙 بازگشت",
                    "home"
                )
            ],
        ])
    )


async def start_column_rect(update, context):

    fields = [
        ("count", "تعداد ستون"),
        ("width", "عرض ستون (m)"),
        ("depth", "عمق ستون (m)"),
        ("height", "ارتفاع ستون (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("main_count", "تعداد میلگرد اصلی"),
        ("stirrup_diameter", "قطر خاموت (mm)"),
        ("stirrup_spacing", "فاصله خاموت (mm)"),
        ("cover", "کاور (mm)"),
    ]

    def calc(f):

        return column_rectangular(
            count=int(f["count"]),
            width_m=f["width"],
            depth_m=f["depth"],
            height_m=f["height"],
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_count=int(
                f["main_count"]
            ),
            stirrup_diameter_mm=int(
                f["stirrup_diameter"]
            ),
            stirrup_spacing_mm=f[
                "stirrup_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "column_rect",
        "ستون مربعی / مستطیلی",
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
        ("stirrup_diameter", "قطر خاموت (mm)"),
        ("stirrup_spacing", "فاصله خاموت (mm)"),
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
            stirrup_diameter_mm=int(
                f["stirrup_diameter"]
            ),
            stirrup_spacing_mm=f[
                "stirrup_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "column_round",
        "ستون گرد",
        fields,
        calc,
        "columns"
    )


# =========================================================
# BEAMS
# =========================================================

async def beams_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "📐 <b>تیرها</b>\n\n"
        "نوع تیر را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("تیر اصلی", "beam_main")
            ],
            [
                button("تیر فرعی", "beam_secondary")
            ],
            [
                button("🔙 بازگشت", "home")
            ],
        ])
    )


async def start_beam(update, context, beam_type):

    fields = [
        ("count", "تعداد تیر"),
        ("length", "طول هر تیر (m)"),
        ("width", "عرض تیر (m)"),
        ("height", "ارتفاع تیر (m)"),
        ("main_diameter", "قطر میلگرد اصلی (mm)"),
        ("bottom_count", "تعداد میلگرد پایین"),
        ("top_count", "تعداد میلگرد بالا"),
        ("stirrup_diameter", "قطر خاموت (mm)"),
        ("stirrup_spacing", "فاصله خاموت (mm)"),
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
            main_top_count=int(
                f["top_count"]
            ),
            main_bottom_count=int(
                f["bottom_count"]
            ),
            stirrup_diameter_mm=int(
                f["stirrup_diameter"]
            ),
            stirrup_spacing_mm=f[
                "stirrup_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "beam",
        f"تیر {beam_type}",
        fields,
        calc,
        "beams"
    )


# =========================================================
# ROOFS
# =========================================================

async def roofs_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🏠 <b>سقف‌ها</b>\n\n"
        "نوع سقف را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("تیرچه یونولیتی", "roof_poly")
            ],
            [
                button("تیرچه سفالی", "roof_clay")
            ],
            [
                button("تیرچه دوبل", "roof_double")
            ],
            [
                button("کرومیت", "roof_kromit")
            ],
            [
                button("کامپوزیت", "roof_composite")
            ],
            [
                button("عرشه فولادی", "roof_deck")
            ],
            [
                button("دال بتنی", "roof_slab")
            ],
            [
                button("وافل", "roof_waffle")
            ],
            [
                button("🔙 بازگشت", "home")
            ],
        ])
    )


async def start_roof(update, context, roof_type):

    fields = [
        ("area", "مساحت سقف (m²)"),
        ("rebar_kg_m2", "مصرف میلگرد (kg/m²)"),
    ]

    def calc(f):

        return roof_slab(
            roof_type=roof_type,
            area_m2=f["area"],
            rebar_kg_per_m2=f[
                "rebar_kg_m2"
            ],
        )

    await start_generic(
        update,
        context,
        "roof",
        roof_type,
        fields,
        calc,
        "roofs"
    )


# =========================================================
# STAIRS
# =========================================================

async def start_stair(update, context):

    fields = [
        ("count", "تعداد راه‌پله"),
        ("length", "طول مسیر (m)"),
        ("width", "عرض راه‌پله (m)"),
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
            length_m=f["length"],
            width_m=f["width"],
            thickness_m=f["thickness"],
            main_diameter_mm=int(
                f["main_diameter"]
            ),
            main_spacing_mm=f[
                "main_spacing"
            ],
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
        "stair",
        "راه‌پله",
        fields,
        calc,
        "home"
    )


# =========================================================
# TIES
# =========================================================

async def ties_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🔗 <b>شناژ و کلاف</b>\n\n"
        "انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("شناژ", "tie_beam")
            ],
            [
                button("کلاف", "tie_cowl")
            ],
            [
                button("🔙 بازگشت", "home")
            ],
        ])
    )


async def start_tie(update, context, tie_type):

    fields = [
        ("count", "تعداد"),
        ("length", "طول هر قطعه (m)"),
        ("width", "عرض (m)"),
        ("height", "ارتفاع (m)"),
        ("main_diameter", "قطر میلگرد طولی (mm)"),
        ("main_count", "تعداد میلگرد طولی"),
        ("stirrup_diameter", "قطر خاموت (mm)"),
        ("stirrup_spacing", "فاصله خاموت (mm)"),
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
            stirrup_diameter_mm=int(
                f["stirrup_diameter"]
            ),
            stirrup_spacing_mm=f[
                "stirrup_spacing"
            ],
            cover_mm=f["cover"],
        )

    await start_generic(
        update,
        context,
        "tie",
        tie_type,
        fields,
        calc,
        "ties"
    )


# =========================================================
# WALLS
# =========================================================

async def walls_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "🧱 <b>دیوارها</b>\n\n"
        "نوع دیوار را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("دیوار برشی", "wall_shear")
            ],
            [
                button("دیوار حائل", "wall_retaining")
            ],
            [
                button("🔙 بازگشت", "home")
            ],
        ])
    )


async def start_wall(update, context, wall_type):

    fields = [
        ("count", "تعداد دیوار"),
        ("length", "طول دیوار (m)"),
        ("thickness", "ضخامت دیوار (m)"),
        ("height", "ارتفاع دیوار (m)"),
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
            thickness_m=f["thickness"],
            height_m=f["height"],
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
        "wall",
        wall_type,
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
        "📊 <b>خلاصه پروژه</b>\n\n"
        "این بخش در مرحله بعد به جمع کل "
        "اعضای پروژه متصل می‌شود.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("🔙 بازگشت", "home")
            ]
        ])
    )


async def settings_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "⚙️ <b>تنظیمات</b>\n\n"
        "تنظیمات پروژه در نسخه بعدی تکمیل می‌شود.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("🔙 بازگشت", "home")
            ]
        ])
    )


async def help_menu(update, context):

    clear_state(context)

    await update.callback_query.edit_message_text(
        "ℹ️ <b>راهنما</b>\n\n"
        "این ربات برای برآورد اولیه مقادیر "
        "اسکلت بتنی طراحی شده است.\n\n"
        "برای نتیجه دقیق‌تر، ابعاد واقعی اعضا "
        "و جزئیات میلگرد نقشه وارد شود.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                button("🔙 بازگشت", "home")
            ]
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

    if callback == "foundation_strip":
        await start_strip(update, context)
        return

    if callback == "foundation_raft":
        await start_raft(update, context)
        return

    # WIZARD
    if callback == "wizard_previous":
        await wizard_previous(update, context)
        return

    # ISOLATED
    if callback == "isolated_rebar":
        await isolated_rebar(update, context)
        return

    if callback == "isolated_cutlist":
        await isolated_cutlist(update, context)
        return

    if callback == "isolated_result":
        await show_isolated_result(update, context)
        return

    # GENERIC
    if callback == "generic_rebar":
        await generic_rebar(update, context)
        return

    if callback == "generic_cutlist":
        await generic_cutlist(update, context)
        return

    if callback == "generic_result":
        await show_generic_result(update, context)
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
            "اصلی"
        )
        return

    if callback == "beam_secondary":
        await start_beam(
            update,
            context,
            "فرعی"
        )
        return

    # ROOFS
    if callback == "roofs":
        await roofs_menu(update, context)
        return

    roof_callbacks = {
        "roof_poly": "تیرچه یونولیتی",
        "roof_clay": "تیرچه سفالی",
        "roof_double": "تیرچه دوبل",
        "roof_kromit": "کرومیت",
        "roof_composite": "کامپوزیت",
        "roof_deck": "عرشه فولادی",
        "roof_slab": "دال بتنی",
        "roof_waffle": "وافل",
    }

    if callback in roof_callbacks:

        await start_roof(
            update,
            context,
            roof_callbacks[callback]
        )

        return

    # STAIR
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

    await query.edit_message_text(
        "❌ گزینه نامعتبر است.",
        reply_markup=InlineKeyboardMarkup([
            [
                button("🏠 خانه", "home")
            ]
        ])
    )


# =========================================================
# TEXT MESSAGE ROUTER
# =========================================================

async def receive(update, context):

    text = update.message.text.strip()

    # منوی پایین
    if text == MENU_TEXT:

        clear_state(context)

        await update.message.reply_text(
            HOME_TEXT,
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )

        return

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
        "برای ادامه، از دکمه «☰ منو» استفاده کنید.",
        reply_markup=bottom_menu()
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
