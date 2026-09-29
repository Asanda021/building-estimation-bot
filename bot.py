# bot.py
# -*- coding: utf-8 -*-

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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


# ============================================================
# تنظیمات
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# ابزارهای عمومی
# ============================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🧱 فونداسیون", callback_data="foundation"),
            InlineKeyboardButton("🏛️ ستون‌ها", callback_data="columns"),
        ],
        [
            InlineKeyboardButton("📐 تیرها", callback_data="beams"),
            InlineKeyboardButton("🏠 سقف‌ها", callback_data="roofs"),
        ],
        [
            InlineKeyboardButton("🪜 راه‌پله", callback_data="stairs"),
            InlineKeyboardButton("🔗 شناژ و کلاف", callback_data="ties"),
        ],
        [
            InlineKeyboardButton("🧱 دیوارها", callback_data="walls"),
        ],
        [
            InlineKeyboardButton("📊 خلاصه پروژه", callback_data="summary"),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def back_button(callback_data="home"):
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)
        ]]
    )


def clear_input(context):
    context.user_data.pop("step", None)


def set_step(context, step):
    context.user_data["step"] = step


def get_step(context):
    return context.user_data.get("step")


def start_message():
    return (
        "🏗️ <b>محاسبه‌گر اسکلت بتنی</b>\n\n"
        "نوع عضو سازه‌ای را انتخاب کنید:"
    )


# ============================================================
# /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        start_message(),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# منوی اصلی
# ============================================================

async def show_home(query, context):

    clear_input(context)

    await query.edit_message_text(
        start_message(),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# فونداسیون
# ============================================================

async def foundation_menu(query, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "🧱 پی منفرد",
                callback_data="foundation_isolated",
            )
        ],
        [
            InlineKeyboardButton(
                "🧱 پی نواری",
                callback_data="foundation_strip",
            )
        ],
        [
            InlineKeyboardButton(
                "🧱 پی گسترده / رادیه",
                callback_data="foundation_raft",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(
        "🧱 <b>فونداسیون</b>\n\n"
        "نوع فونداسیون را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# پی منفرد - شروع
# ============================================================

async def isolated_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "isolated"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "🧱 <b>پی منفرد</b>\n\n"
        "تعداد پی را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("foundation"),
    )


async def isolated_process(update, context, text):

    step = get_step(context)

    try:

        if step == "count":

            context.user_data["count"] = int(text)
            context.user_data["step"] = "length"

            await update.message.reply_text(
                "طول پی را بر حسب متر وارد کنید:"
            )
            return

        if step == "length":

            context.user_data["length"] = float(text)
            context.user_data["step"] = "width"

            await update.message.reply_text(
                "عرض پی را بر حسب متر وارد کنید:"
            )
            return

        if step == "width":

            context.user_data["width"] = float(text)
            context.user_data["step"] = "thickness"

            await update.message.reply_text(
                "ضخامت پی را بر حسب متر وارد کنید:"
            )
            return

        if step == "thickness":

            context.user_data["thickness"] = float(text)
            context.user_data["step"] = "lean_length"

            await update.message.reply_text(
                "طول بتن مگر را وارد کنید:"
            )
            return

        if step == "lean_length":

            context.user_data["lean_length"] = float(text)
            context.user_data["step"] = "lean_width"

            await update.message.reply_text(
                "عرض بتن مگر را وارد کنید:"
            )
            return

        if step == "lean_width":

            context.user_data["lean_width"] = float(text)
            context.user_data["step"] = "lean_thickness"

            await update.message.reply_text(
                "ضخامت بتن مگر را بر حسب متر وارد کنید:"
            )
            return

        if step == "lean_thickness":

            context.user_data["lean_thickness"] = float(text)
            context.user_data["step"] = "bottom_diameter"

            await update.message.reply_text(
                "قطر میلگرد پایین را وارد کنید. مثال: 16"
            )
            return

        if step == "bottom_diameter":

            context.user_data["bottom_diameter"] = int(text)
            context.user_data["step"] = "bottom_spacing"

            await update.message.reply_text(
                "فاصله میلگرد پایین را بر حسب میلی‌متر وارد کنید. مثال: 150"
            )
            return

        if step == "bottom_spacing":

            context.user_data["bottom_spacing"] = float(text)
            context.user_data["step"] = "top_diameter"

            await update.message.reply_text(
                "قطر میلگرد بالایی را وارد کنید.\n"
                "اگر میلگرد بالایی ندارید: 0"
            )
            return

        if step == "top_diameter":

            context.user_data["top_diameter"] = int(text)
            context.user_data["step"] = "top_spacing"

            await update.message.reply_text(
                "فاصله میلگرد بالایی را وارد کنید.\n"
                "اگر میلگرد بالایی ندارید: 0"
            )
            return

        if step == "top_spacing":

            context.user_data["top_spacing"] = float(text)
            context.user_data["step"] = "pedestal_length"

            await update.message.reply_text(
                "طول پدستال / ستونک را وارد کنید.\n"
                "اگر ندارد: 0"
            )
            return

        if step == "pedestal_length":

            context.user_data["pedestal_length"] = float(text)
            context.user_data["step"] = "pedestal_width"

            await update.message.reply_text(
                "عرض پدستال را وارد کنید.\n"
                "اگر ندارد: 0"
            )
            return

        if step == "pedestal_width":

            context.user_data["pedestal_width"] = float(text)
            context.user_data["step"] = "pedestal_height"

            await update.message.reply_text(
                "ارتفاع پدستال را وارد کنید.\n"
                "اگر ندارد: 0"
            )
            return

        if step == "pedestal_height":

            context.user_data["pedestal_height"] = float(text)

            result = isolated_footing(
                count=context.user_data["count"],
                length_m=context.user_data["length"],
                width_m=context.user_data["width"],
                thickness_m=context.user_data["thickness"],
                lean_concrete_length_m=context.user_data["lean_length"],
                lean_concrete_width_m=context.user_data["lean_width"],
                lean_concrete_thickness_m=context.user_data["lean_thickness"],
                bottom_diameter_mm=context.user_data["bottom_diameter"],
                bottom_spacing_mm=context.user_data["bottom_spacing"],
                top_diameter_mm=(
                    context.user_data["top_diameter"]
                    if context.user_data["top_diameter"] > 0
                    else None
                ),
                top_spacing_mm=(
                    context.user_data["top_spacing"]
                    if context.user_data["top_spacing"] > 0
                    else None
                ),
                pedestal_length_m=context.user_data["pedestal_length"],
                pedestal_width_m=context.user_data["pedestal_width"],
                pedestal_height_m=context.user_data["pedestal_height"],
            )

            context.user_data["last_result"] = result
            context.user_data["step"] = None

            await show_isolated_result(update, context)
            return

    except Exception as e:

        logger.exception("Calculation error")

        await update.message.reply_text(
            f"❌ خطا در ورودی:\n{e}\n\n"
            "لطفاً مقدار را دوباره وارد کنید."
        )


async def show_isolated_result(update, context):

    result = context.user_data["last_result"]

    keyboard = [
        [
            InlineKeyboardButton(
                "🔩 جزئیات میلگرد",
                callback_data="isolated_rebar",
            )
        ],
        [
            InlineKeyboardButton(
                "✂️ Cut List",
                callback_data="isolated_cutlist",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 فونداسیون",
                callback_data="foundation",
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            )
        ],
    ]

    text = (
        "🧱 <b>نتیجه پی منفرد</b>\n\n"
        f"تعداد پی: {result['count']}\n"
        f"بتن مگر: {result['lean_concrete']:.2f} m³\n"
        f"بتن پی: {result['footing_concrete']:.2f} m³\n"
        f"بتن پدستال: {result['pedestal_concrete']:.2f} m³\n"
        f"بتن سازه‌ای: {result['structural_concrete']:.2f} m³\n\n"
        f"🔹 <b>کل بتن: {result['total_concrete']:.2f} m³</b>\n"
        f"🔩 <b>کل میلگرد: {result['rebar']['total_weight']:.1f} kg</b>"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ============================================================
# جزئیات میلگرد پی منفرد
# ============================================================

async def isolated_rebar(query, context):

    result = context.user_data.get("last_result")

    if not result:
        await query.answer("نتیجه‌ای وجود ندارد.")
        return

    lines = [
        "🔩 <b>جزئیات میلگرد پی منفرد</b>",
        "",
    ]

    for item in result["rebar"]["details"]:

        lines.append(
            f"Φ{item['diameter']} | "
            f"{item['description']}\n"
            f"تعداد: {item['pieces']}\n"
            f"طول هر قطعه: {item['piece_length']:.2f} m\n"
            f"طول کل: {item['total_length']:.2f} m\n"
            f"وزن: {item['weight']:.1f} kg\n"
            f"شاخه 12 متری: {item['bars_12m']}"
        )

        lines.append("")

    lines.append(
        f"🔩 جمع میلگرد: "
        f"{result['rebar']['total_weight']:.1f} kg"
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=back_button("isolated_result"),
    )


# ============================================================
# Cut List
# ============================================================

async def isolated_cutlist(query, context):

    result = context.user_data.get("last_result")

    if not result:
        await query.answer("نتیجه‌ای وجود ندارد.")
        return

    lines = [
        "✂️ <b>Cut List</b>",
        "",
        "قطر   طول قطعه   تعداد",
        "-----------------------",
    ]

    for item in result["rebar"]["details"]:

        lines.append(
            f"Φ{item['diameter']:<4}"
            f"{item['piece_length']:<10.2f}"
            f"{item['pieces']}"
        )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=back_button("isolated_result"),
    )


async def isolated_result(query, context):

    fake_update = type(
        "FakeUpdate",
        (),
        {
            "callback_query": query,
            "message": None,
        },
    )()

    await show_isolated_result(
        fake_update,
        context,
    )


# ============================================================
# پی نواری
# ============================================================

async def strip_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "strip"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "🧱 <b>پی نواری</b>\n\n"
        "تعداد نوار / پی را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("foundation"),
    )


async def strip_process(update, context, text):

    step = get_step(context)

    try:

        if step == "count":
            context.user_data["count"] = int(text)
            context.user_data["step"] = "length"
            await update.message.reply_text("طول نوار را بر حسب متر وارد کنید:")
            return

        if step == "length":
            context.user_data["length"] = float(text)
            context.user_data["step"] = "width"
            await update.message.reply_text("عرض پی را وارد کنید:")
            return

        if step == "width":
            context.user_data["width"] = float(text)
            context.user_data["step"] = "thickness"
            await update.message.reply_text("ضخامت پی را وارد کنید:")
            return

        if step == "thickness":
            context.user_data["thickness"] = float(text)
            context.user_data["step"] = "lean_length"
            await update.message.reply_text("طول بتن مگر را وارد کنید:")
            return

        if step == "lean_length":
            context.user_data["lean_length"] = float(text)
            context.user_data["step"] = "lean_width"
            await update.message.reply_text("عرض بتن مگر را وارد کنید:")
            return

        if step == "lean_width":
            context.user_data["lean_width"] = float(text)
            context.user_data["step"] = "lean_thickness"
            await update.message.reply_text("ضخامت بتن مگر را وارد کنید:")
            return

        if step == "lean_thickness":
            context.user_data["lean_thickness"] = float(text)
            context.user_data["step"] = "long_diameter"
            await update.message.reply_text("قطر میلگرد طولی پایین:")
            return

        if step == "long_diameter":
            context.user_data["long_diameter"] = int(text)
            context.user_data["step"] = "long_count"
            await update.message.reply_text("تعداد میلگرد طولی:")
            return

        if step == "long_count":
            context.user_data["long_count"] = int(text)
            context.user_data["step"] = "trans_diameter"
            await update.message.reply_text("قطر میلگرد عرضی:")
            return

        if step == "trans_diameter":
            context.user_data["trans_diameter"] = int(text)
            context.user_data["step"] = "trans_spacing"
            await update.message.reply_text("فاصله میلگرد عرضی بر حسب میلی‌متر:")
            return

        if step == "trans_spacing":

            result = strip_footing(
                strip_count=context.user_data["count"],
                strip_length_m=context.user_data["length"],
                footing_width_m=context.user_data["width"],
                footing_thickness_m=context.user_data["thickness"],
                lean_length_m=context.user_data["lean_length"],
                lean_width_m=context.user_data["lean_width"],
                lean_thickness_m=context.user_data["lean_thickness"],
                longitudinal_diameter_mm=context.user_data["long_diameter"],
                longitudinal_count=context.user_data["long_count"],
                transverse_diameter_mm=context.user_data["trans_diameter"],
                transverse_spacing_mm=float(text),
            )

            context.user_data["last_result"] = result
            context.user_data["step"] = None

            await show_generic_result(
                update,
                context,
                "🧱 نتیجه پی نواری",
                result,
                "foundation",
            )

    except Exception as e:

        logger.exception("Strip footing error")

        await update.message.reply_text(
            f"❌ خطا: {e}"
        )


# ============================================================
# پی گسترده
# ============================================================

async def raft_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "raft"
    context.user_data["step"] = "length"

    await query.edit_message_text(
        "🧱 <b>پی گسترده / رادیه</b>\n\n"
        "طول رادیه را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("foundation"),
    )


async def raft_process(update, context, text):

    step = get_step(context)

    try:

        if step == "length":
            context.user_data["length"] = float(text)
            context.user_data["step"] = "width"
            await update.message.reply_text("عرض رادیه:")
            return

        if step == "width":
            context.user_data["width"] = float(text)
            context.user_data["step"] = "thickness"
            await update.message.reply_text("ضخامت رادیه:")
            return

        if step == "thickness":
            context.user_data["thickness"] = float(text)
            context.user_data["step"] = "lean_length"
            await update.message.reply_text("طول بتن مگر:")
            return

        if step == "lean_length":
            context.user_data["lean_length"] = float(text)
            context.user_data["step"] = "lean_width"
            await update.message.reply_text("عرض بتن مگر:")
            return

        if step == "lean_width":
            context.user_data["lean_width"] = float(text)
            context.user_data["step"] = "lean_thickness"
            await update.message.reply_text("ضخامت بتن مگر:")
            return

        if step == "lean_thickness":
            context.user_data["lean_thickness"] = float(text)
            context.user_data["step"] = "bottom_x_diameter"
            await update.message.reply_text("قطر میلگرد پایین X:")
            return

        if step == "bottom_x_diameter":
            context.user_data["bottom_x_diameter"] = int(text)
            context.user_data["step"] = "bottom_x_spacing"
            await update.message.reply_text("فاصله پایین X:")
            return

        if step == "bottom_x_spacing":
            context.user_data["bottom_x_spacing"] = float(text)
            context.user_data["step"] = "bottom_y_diameter"
            await update.message.reply_text("قطر میلگرد پایین Y:")
            return

        if step == "bottom_y_diameter":
            context.user_data["bottom_y_diameter"] = int(text)
            context.user_data["step"] = "bottom_y_spacing"
            await update.message.reply_text("فاصله پایین Y:")
            return

        if step == "bottom_y_spacing":

            result = raft_foundation(
                length_m=context.user_data["length"],
                width_m=context.user_data["width"],
                thickness_m=context.user_data["thickness"],
                lean_length_m=context.user_data["lean_length"],
                lean_width_m=context.user_data["lean_width"],
                lean_thickness_m=context.user_data["lean_thickness"],
                bottom_x_diameter_mm=context.user_data["bottom_x_diameter"],
                bottom_x_spacing_mm=context.user_data["bottom_x_spacing"],
                bottom_y_diameter_mm=context.user_data["bottom_y_diameter"],
                bottom_y_spacing_mm=float(text),
            )

            context.user_data["last_result"] = result
            context.user_data["step"] = None

            await show_generic_result(
                update,
                context,
                "🧱 نتیجه پی گسترده",
                result,
                "foundation",
            )

    except Exception as e:

        logger.exception("Raft error")

        await update.message.reply_text(
            f"❌ خطا: {e}"
        )


# ============================================================
# ستون‌ها
# ============================================================

async def columns_menu(query, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "⬛ ستون مستطیلی",
                callback_data="column_rect",
            )
        ],
        [
            InlineKeyboardButton(
                "⚪ ستون گرد",
                callback_data="column_round",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(
        "🏛️ <b>ستون‌ها</b>\n\n"
        "نوع ستون را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def column_rect_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "column_rect"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "⬛ <b>ستون مستطیلی</b>\n\n"
        "تعداد ستون:",
        parse_mode="HTML",
        reply_markup=back_button("columns"),
    )


async def column_round_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "column_round"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "⚪ <b>ستون گرد</b>\n\n"
        "تعداد ستون:",
        parse_mode="HTML",
        reply_markup=back_button("columns"),
    )


# ============================================================
# تیرها
# ============================================================

async def beams_menu(query, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "📐 تیر اصلی",
                callback_data="beam_main",
            )
        ],
        [
            InlineKeyboardButton(
                "📐 تیر فرعی",
                callback_data="beam_secondary",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(
        "📐 <b>تیرها</b>\n\n"
        "نوع تیر را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def beam_start(query, context, beam_type):

    context.user_data.clear()
    context.user_data["section"] = "beam"
    context.user_data["beam_type"] = beam_type
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "📐 <b>تیر</b>\n\n"
        "تعداد تیر را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("beams"),
    )


# ============================================================
# سقف‌ها
# ============================================================

async def roofs_menu(query, context):

    roof_types = [
        "تیرچه یونولیتی",
        "تیرچه سفالی",
        "تیرچه دوبل",
        "کرومیت",
        "کامپوزیت",
        "عرشه فولادی",
        "دال بتنی",
        "وافل",
    ]

    keyboard = []

    for i in range(0, len(roof_types), 2):

        row = []

        for roof_type in roof_types[i:i + 2]:

            row.append(
                InlineKeyboardButton(
                    roof_type,
                    callback_data=f"roof:{roof_type}",
                )
            )

        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="home",
        )
    ])

    await query.edit_message_text(
        "🏠 <b>سقف‌ها</b>\n\n"
        "نوع سقف را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def roof_start(query, context, roof_type):

    context.user_data.clear()
    context.user_data["section"] = "roof"
    context.user_data["roof_type"] = roof_type
    context.user_data["step"] = "area"

    await query.edit_message_text(
        f"🏠 <b>{roof_type}</b>\n\n"
        "مساحت سقف را بر حسب مترمربع وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("roofs"),
    )


# ============================================================
# راه‌پله
# ============================================================

async def stairs_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "stairs"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "🪜 <b>راه‌پله</b>\n\n"
        "تعداد راه‌پله را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("home"),
    )


# ============================================================
# شناژ و کلاف
# ============================================================

async def ties_start(query, context):

    context.user_data.clear()
    context.user_data["section"] = "ties"
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "🔗 <b>شناژ و کلاف</b>\n\n"
        "تعداد شناژ / کلاف را وارد کنید:",
        parse_mode="HTML",
        reply_markup=back_button("home"),
    )


# ============================================================
# دیوارها
# ============================================================

async def walls_menu(query, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "🧱 دیوار برشی",
                callback_data="wall_shear",
            )
        ],
        [
            InlineKeyboardButton(
                "🧱 دیوار حائل",
                callback_data="wall_retaining",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home",
            )
        ],
    ]

    await query.edit_message_text(
        "🧱 <b>دیوارها</b>\n\n"
        "نوع دیوار را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def wall_start(query, context, wall_type):

    context.user_data.clear()
    context.user_data["section"] = "wall"
    context.user_data["wall_type"] = wall_type
    context.user_data["step"] = "count"

    await query.edit_message_text(
        "🧱 <b>دیوار بتنی</b>\n\n"
        "تعداد دیوار:",
        parse_mode="HTML",
        reply_markup=back_button("walls"),
    )


# ============================================================
# منوی خلاصه
# ============================================================

async def summary_menu(query, context):

    await query.edit_message_text(
        "📊 <b>خلاصه پروژه</b>\n\n"
        "فعلاً محاسبات هر عضو به صورت مستقل انجام می‌شود.\n\n"
        "در مرحله بعدی می‌توانیم نتایج همه اعضا را "
        "به یک خلاصه پروژه واحد متصل کنیم.",
        parse_mode="HTML",
        reply_markup=back_button("home"),
    )


# ============================================================
# تنظیمات
# ============================================================

async def settings_menu(query, context):

    await query.edit_message_text(
        "⚙️ <b>تنظیمات</b>\n\n"
        "نسخه فعلی:\n"
        "🏗️ اسکلت بتنی\n"
        "📐 محاسبات بتن و میلگرد\n"
        "✂️ Cut List\n"
        "🔩 جزئیات آرماتور",
        parse_mode="HTML",
        reply_markup=back_button("home"),
    )


# ============================================================
# راهنما
# ============================================================

async def help_menu(query, context):

    await query.edit_message_text(
        "ℹ️ <b>راهنما</b>\n\n"
        "1️⃣ عضو سازه‌ای را انتخاب کنید.\n"
        "2️⃣ ابعاد و مشخصات را وارد کنید.\n"
        "3️⃣ مقدار بتن و میلگرد محاسبه می‌شود.\n"
        "4️⃣ جزئیات میلگرد و Cut List جداگانه قابل مشاهده است.\n\n"
        "⚠️ محاسبات این نسخه برای برآورد اولیه است "
        "و برای متره دقیق اجرایی باید نقشه‌های سازه "
        "و دیتیل‌های آرماتور بررسی شوند.",
        parse_mode="HTML",
        reply_markup=back_button("home"),
    )


# ============================================================
# نمایش نتیجه عمومی
# ============================================================

async def show_generic_result(
    update,
    context,
    title,
    result,
    back_to,
):

    concrete = result.get(
        "total_concrete",
        result.get("concrete", 0),
    )

    rebar = result.get(
        "rebar",
        {},
    )

    rebar_weight = rebar.get(
        "total_weight",
        result.get("rebar_weight", 0),
    )

    text = (
        f"{title}\n\n"
        f"🧱 بتن: <b>{concrete:.2f} m³</b>\n"
        f"🔩 میلگرد: <b>{rebar_weight:.1f} kg</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=back_to,
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            )
        ],
    ]

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ============================================================
# پردازش پیام‌های متنی
# ============================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    section = context.user_data.get("section")

    if not section:
        await update.message.reply_text(
            "از منوی اصلی یک گزینه را انتخاب کنید.",
            reply_markup=main_menu(),
        )
        return

    try:

        # ----------------------------------------------------
        # سقف
        # ----------------------------------------------------

        if section == "roof":

            step = get_step(context)

            if step == "area":

                context.user_data["area"] = float(text)
                context.user_data["step"] = "rebar"

                await update.message.reply_text(
                    "مقدار میلگرد تقریبی سقف را بر حسب kg/m² وارد کنید.\n"
                    "اگر نمی‌خواهید محاسبه شود: 0"
                )

                return

            if step == "rebar":

                result = roof_slab(
                    roof_type=context.user_data["roof_type"],
                    area_m2=context.user_data["area"],
                    rebar_kg_per_m2=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    f"🏠 {context.user_data['roof_type']}",
                    result,
                    "roofs",
                )

                return

        # ----------------------------------------------------
        # شناژ
        # ----------------------------------------------------

        if section == "ties":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "length"
                await update.message.reply_text("طول شناژ:")
                return

            if step == "length":
                context.user_data["length"] = float(text)
                context.user_data["step"] = "width"
                await update.message.reply_text("عرض شناژ:")
                return

            if step == "width":
                context.user_data["width"] = float(text)
                context.user_data["step"] = "height"
                await update.message.reply_text("ارتفاع شناژ:")
                return

            if step == "height":
                context.user_data["height"] = float(text)
                context.user_data["step"] = "main_diameter"
                await update.message.reply_text("قطر میلگرد طولی:")
                return

            if step == "main_diameter":
                context.user_data["main_diameter"] = int(text)
                context.user_data["step"] = "main_count"
                await update.message.reply_text("تعداد میلگرد طولی:")
                return

            if step == "main_count":
                context.user_data["main_count"] = int(text)
                context.user_data["step"] = "stirrup_diameter"
                await update.message.reply_text("قطر خاموت:")
                return

            if step == "stirrup_diameter":
                context.user_data["stirrup_diameter"] = int(text)
                context.user_data["step"] = "stirrup_spacing"
                await update.message.reply_text("فاصله خاموت:")
                return

            if step == "stirrup_spacing":

                result = tie_beam(
                    count=context.user_data["count"],
                    length_m=context.user_data["length"],
                    width_m=context.user_data["width"],
                    height_m=context.user_data["height"],
                    main_diameter_mm=context.user_data["main_diameter"],
                    main_count=context.user_data["main_count"],
                    stirrup_diameter_mm=context.user_data["stirrup_diameter"],
                    stirrup_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "🔗 نتیجه شناژ / کلاف",
                    result,
                    "home",
                )

                return

        # ----------------------------------------------------
        # ستون مستطیلی
        # ----------------------------------------------------

        if section == "column_rect":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "width"
                await update.message.reply_text("عرض ستون:")
                return

            if step == "width":
                context.user_data["width"] = float(text)
                context.user_data["step"] = "depth"
                await update.message.reply_text("طول / عمق ستون:")
                return

            if step == "depth":
                context.user_data["depth"] = float(text)
                context.user_data["step"] = "height"
                await update.message.reply_text("ارتفاع ستون:")
                return

            if step == "height":
                context.user_data["height"] = float(text)
                context.user_data["step"] = "main_diameter"
                await update.message.reply_text("قطر میلگرد طولی:")
                return

            if step == "main_diameter":
                context.user_data["main_diameter"] = int(text)
                context.user_data["step"] = "main_count"
                await update.message.reply_text("تعداد میلگرد طولی:")
                return

            if step == "main_count":
                context.user_data["main_count"] = int(text)
                context.user_data["step"] = "stirrup_diameter"
                await update.message.reply_text("قطر خاموت:")
                return

            if step == "stirrup_diameter":
                context.user_data["stirrup_diameter"] = int(text)
                context.user_data["step"] = "stirrup_spacing"
                await update.message.reply_text("فاصله خاموت:")
                return

            if step == "stirrup_spacing":

                result = column_rectangular(
                    count=context.user_data["count"],
                    width_m=context.user_data["width"],
                    depth_m=context.user_data["depth"],
                    height_m=context.user_data["height"],
                    main_diameter_mm=context.user_data["main_diameter"],
                    main_count=context.user_data["main_count"],
                    stirrup_diameter_mm=context.user_data["stirrup_diameter"],
                    stirrup_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "⬛ نتیجه ستون مستطیلی",
                    result,
                    "columns",
                )

                return

        # ----------------------------------------------------
        # ستون گرد
        # ----------------------------------------------------

        if section == "column_round":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "diameter"
                await update.message.reply_text("قطر ستون:")
                return

            if step == "diameter":
                context.user_data["diameter"] = float(text)
                context.user_data["step"] = "height"
                await update.message.reply_text("ارتفاع ستون:")
                return

            if step == "height":
                context.user_data["height"] = float(text)
                context.user_data["step"] = "main_diameter"
                await update.message.reply_text("قطر میلگرد طولی:")
                return

            if step == "main_diameter":
                context.user_data["main_diameter"] = int(text)
                context.user_data["step"] = "main_count"
                await update.message.reply_text("تعداد میلگرد طولی:")
                return

            if step == "main_count":
                context.user_data["main_count"] = int(text)
                context.user_data["step"] = "stirrup_diameter"
                await update.message.reply_text("قطر خاموت:")
                return

            if step == "stirrup_diameter":
                context.user_data["stirrup_diameter"] = int(text)
                context.user_data["step"] = "stirrup_spacing"
                await update.message.reply_text("فاصله خاموت:")
                return

            if step == "stirrup_spacing":

                result = column_round(
                    count=context.user_data["count"],
                    diameter_m=context.user_data["diameter"],
                    height_m=context.user_data["height"],
                    main_diameter_mm=context.user_data["main_diameter"],
                    main_count=context.user_data["main_count"],
                    stirrup_diameter_mm=context.user_data["stirrup_diameter"],
                    stirrup_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "⚪ نتیجه ستون گرد",
                    result,
                    "columns",
                )

                return

        # ----------------------------------------------------
        # تیر
        # ----------------------------------------------------

        if section == "beam":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "length"
                await update.message.reply_text("طول تیر:")
                return

            if step == "length":
                context.user_data["length"] = float(text)
                context.user_data["step"] = "width"
                await update.message.reply_text("عرض تیر:")
                return

            if step == "width":
                context.user_data["width"] = float(text)
                context.user_data["step"] = "height"
                await update.message.reply_text("ارتفاع تیر:")
                return

            if step == "height":
                context.user_data["height"] = float(text)
                context.user_data["step"] = "main_diameter"
                await update.message.reply_text("قطر میلگرد طولی:")
                return

            if step == "main_diameter":
                context.user_data["main_diameter"] = int(text)
                context.user_data["step"] = "top_count"
                await update.message.reply_text("تعداد میلگرد بالایی:")
                return

            if step == "top_count":
                context.user_data["top_count"] = int(text)
                context.user_data["step"] = "bottom_count"
                await update.message.reply_text("تعداد میلگرد پایینی:")
                return

            if step == "bottom_count":
                context.user_data["bottom_count"] = int(text)
                context.user_data["step"] = "stirrup_diameter"
                await update.message.reply_text("قطر خاموت:")
                return

            if step == "stirrup_diameter":
                context.user_data["stirrup_diameter"] = int(text)
                context.user_data["step"] = "stirrup_spacing"
                await update.message.reply_text("فاصله خاموت:")
                return

            if step == "stirrup_spacing":

                result = beam(
                    count=context.user_data["count"],
                    length_m=context.user_data["length"],
                    width_m=context.user_data["width"],
                    height_m=context.user_data["height"],
                    main_diameter_mm=context.user_data["main_diameter"],
                    main_top_count=context.user_data["top_count"],
                    main_bottom_count=context.user_data["bottom_count"],
                    stirrup_diameter_mm=context.user_data["stirrup_diameter"],
                    stirrup_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "📐 نتیجه تیر",
                    result,
                    "beams",
                )

                return

        # ----------------------------------------------------
        # دیوار
        # ----------------------------------------------------

        if section == "wall":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "length"
                await update.message.reply_text("طول دیوار:")
                return

            if step == "length":
                context.user_data["length"] = float(text)
                context.user_data["step"] = "thickness"
                await update.message.reply_text("ضخامت دیوار:")
                return

            if step == "thickness":
                context.user_data["thickness"] = float(text)
                context.user_data["step"] = "height"
                await update.message.reply_text("ارتفاع دیوار:")
                return

            if step == "height":
                context.user_data["height"] = float(text)
                context.user_data["step"] = "vertical_diameter"
                await update.message.reply_text("قطر میلگرد قائم:")
                return

            if step == "vertical_diameter":
                context.user_data["vertical_diameter"] = int(text)
                context.user_data["step"] = "vertical_spacing"
                await update.message.reply_text("فاصله میلگرد قائم:")
                return

            if step == "vertical_spacing":
                context.user_data["vertical_spacing"] = float(text)
                context.user_data["step"] = "horizontal_diameter"
                await update.message.reply_text("قطر میلگرد افقی:")
                return

            if step == "horizontal_diameter":
                context.user_data["horizontal_diameter"] = int(text)
                context.user_data["step"] = "horizontal_spacing"
                await update.message.reply_text("فاصله میلگرد افقی:")
                return

            if step == "horizontal_spacing":

                result = wall_concrete(
                    count=context.user_data["count"],
                    length_m=context.user_data["length"],
                    thickness_m=context.user_data["thickness"],
                    height_m=context.user_data["height"],
                    vertical_diameter_mm=context.user_data["vertical_diameter"],
                    vertical_spacing_mm=context.user_data["vertical_spacing"],
                    horizontal_diameter_mm=context.user_data["horizontal_diameter"],
                    horizontal_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "🧱 نتیجه دیوار",
                    result,
                    "walls",
                )

                return

        # ----------------------------------------------------
        # راه‌پله
        # ----------------------------------------------------

        if section == "stairs":

            step = get_step(context)

            if step == "count":
                context.user_data["count"] = int(text)
                context.user_data["step"] = "length"
                await update.message.reply_text("طول مسیر راه‌پله:")
                return

            if step == "length":
                context.user_data["length"] = float(text)
                context.user_data["step"] = "width"
                await update.message.reply_text("عرض راه‌پله:")
                return

            if step == "width":
                context.user_data["width"] = float(text)
                context.user_data["step"] = "thickness"
                await update.message.reply_text("ضخامت دال راه‌پله:")
                return

            if step == "thickness":
                context.user_data["thickness"] = float(text)
                context.user_data["step"] = "main_diameter"
                await update.message.reply_text("قطر میلگرد اصلی:")
                return

            if step == "main_diameter":
                context.user_data["main_diameter"] = int(text)
                context.user_data["step"] = "main_spacing"
                await update.message.reply_text("فاصله میلگرد اصلی:")
                return

            if step == "main_spacing":
                context.user_data["main_spacing"] = float(text)
                context.user_data["step"] = "distribution_diameter"
                await update.message.reply_text("قطر میلگرد توزیعی:")
                return

            if step == "distribution_diameter":
                context.user_data["distribution_diameter"] = int(text)
                context.user_data["step"] = "distribution_spacing"
                await update.message.reply_text("فاصله میلگرد توزیعی:")
                return

            if step == "distribution_spacing":

                result = stair_slab(
                    count=context.user_data["count"],
                    length_m=context.user_data["length"],
                    width_m=context.user_data["width"],
                    thickness_m=context.user_data["thickness"],
                    main_diameter_mm=context.user_data["main_diameter"],
                    main_spacing_mm=context.user_data["main_spacing"],
                    distribution_diameter_mm=context.user_data["distribution_diameter"],
                    distribution_spacing_mm=float(text),
                )

                context.user_data["last_result"] = result
                context.user_data["step"] = None

                await show_generic_result(
                    update,
                    context,
                    "🪜 نتیجه راه‌پله",
                    result,
                    "home",
                )

                return

        # ----------------------------------------------------
        # پی منفرد
        # ----------------------------------------------------

        if section == "isolated":

            await isolated_process(
                update,
                context,
                text,
            )

            return

        # ----------------------------------------------------
        # پی نواری
        # ----------------------------------------------------

        if section == "strip":

            await strip_process(
                update,
                context,
                text,
            )

            return

        # ----------------------------------------------------
        # پی گسترده
        # ----------------------------------------------------

        if section == "raft":

            await raft_process(
                update,
                context,
                text,
            )

            return

        await update.message.reply_text(
            "ورودی نامعتبر است."
        )

    except Exception as e:

        logger.exception("Text handler error")

        await update.message.reply_text(
            f"❌ خطا در محاسبه:\n{e}"
        )


# ============================================================
# مدیریت دکمه‌ها
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    try:

        # ----------------------------------------------------
        # خانه
        # ----------------------------------------------------

        if data == "home":
            await show_home(query, context)
            return

        # ----------------------------------------------------
        # فونداسیون
        # ----------------------------------------------------

        if data == "foundation":
            await foundation_menu(query, context)
            return

        if data == "foundation_isolated":
            await isolated_start(query, context)
            return

        if data == "foundation_strip":
            await strip_start(query, context)
            return

        if data == "foundation_raft":
            await raft_start(query, context)
            return

        # ----------------------------------------------------
        # ستون
        # ----------------------------------------------------

        if data == "columns":
            await columns_menu(query, context)
            return

        if data == "column_rect":
            await column_rect_start(query, context)
            return

        if data == "column_round":
            await column_round_start(query, context)
            return

        # ----------------------------------------------------
        # تیر
        # ----------------------------------------------------

        if data == "beams":
            await beams_menu(query, context)
            return

        if data == "beam_main":
            await beam_start(query, context, "main")
            return

        if data == "beam_secondary":
            await beam_start(query, context, "secondary")
            return

        # ----------------------------------------------------
        # سقف
        # ----------------------------------------------------

        if data == "roofs":
            await roofs_menu(query, context)
            return

        if data.startswith("roof:"):

            roof_type = data.split(":", 1)[1]

            await roof_start(
                query,
                context,
                roof_type,
            )

            return

        # ----------------------------------------------------
        # راه‌پله
        # ----------------------------------------------------

        if data == "stairs":
            await stairs_start(query, context)
            return

        # ----------------------------------------------------
        # شناژ
        # ----------------------------------------------------

        if data == "ties":
            await ties_start(query, context)
            return

        # ----------------------------------------------------
        # دیوار
        # ----------------------------------------------------

        if data == "walls":
            await walls_menu(query, context)
            return

        if data == "wall_shear":
            await wall_start(query, context, "shear")
            return

        if data == "wall_retaining":
            await wall_start(query, context, "retaining")
            return

        # ----------------------------------------------------
        # خلاصه
        # ----------------------------------------------------

        if data == "summary":
            await summary_menu(query, context)
            return

        # ----------------------------------------------------
        # تنظیمات
        # ----------------------------------------------------

        if data == "settings":
            await settings_menu(query, context)
            return

        # ----------------------------------------------------
        # راهنما
        # ----------------------------------------------------

        if data == "help":
            await help_menu(query, context)
            return

        # ----------------------------------------------------
        # نتیجه پی منفرد
        # ----------------------------------------------------

        if data == "isolated_result":
            await isolated_result(query, context)
            return

        if data == "isolated_rebar":
            await isolated_rebar(query, context)
            return

        if data == "isolated_cutlist":
            await isolated_cutlist(query, context)
            return

    except Exception as e:

        logger.exception("Button error")

        await query.edit_message_text(
            f"❌ خطا:\n{e}",
            reply_markup=back_button("home"),
        )


# ============================================================
# اجرای بات
# ============================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN در Environment Variables تنظیم نشده است."
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler,
        )
    )

    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
