import os
import logging
from math import ceil

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
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
# تنظیمات
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# ابزارهای عمومی
# =========================================================

PERSIAN_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_number(value: str) -> float:
    """
    تبدیل اعداد فارسی/عربی به انگلیسی
    و پشتیبانی از , و ، و ممیز فارسی.
    """
    value = str(value).strip().translate(PERSIAN_DIGITS)
    value = value.replace("٬", "").replace(",", "")
    value = value.replace("،", "")
    value = value.replace("٫", ".")
    value = value.replace(" ", "")

    return float(value)


def fmt(value, digits=2):
    try:
        value = float(value)
    except Exception:
        return "0"

    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))

    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def fmt_kg(value):
    return f"{fmt(value, 1)} kg"


def fmt_m3(value):
    return f"{fmt(value, 2)} m³"


def fmt_m(value):
    return f"{fmt(value, 2)} m"


def reset_flow(context: ContextTypes.DEFAULT_TYPE):
    """
    فقط اطلاعات مربوط به محاسبه جاری را پاک می‌کند.
    """
    keys = [
        "mode",
        "title",
        "fields_list",
        "fields",
        "index",
        "calc",
        "back_callback",
        "result",
        "result_title",
    ]

    for key in keys:
        context.user_data.pop(key, None)


def bottom_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("☰ منو"),
                KeyboardButton("🏠 خانه"),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
    )


# =========================================================
# منوی اصلی
# =========================================================

def home_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧱 فونداسیون", callback_data="foundation"),
                InlineKeyboardButton("🏛️ ستون‌ها", callback_data="columns"),
            ],
            [
                InlineKeyboardButton("📐 تیرها", callback_data="beams"),
                InlineKeyboardButton("🏠 سقف‌ها", callback_data="roofs"),
            ],
            [
                InlineKeyboardButton("🪜 راه‌پله", callback_data="stair"),
                InlineKeyboardButton("🔗 شناژ و کلاف", callback_data="ties"),
            ],
            [
                InlineKeyboardButton("🧱 دیوارها", callback_data="walls"),
            ],
            [
                InlineKeyboardButton("📊 خلاصه پروژه", callback_data="summary"),
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
            ],
            [
                InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
            ],
        ]
    )


async def send_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_flow(context)

    text = (
        "🏗️ <b>اسکلت بتنی</b>\n\n"
        "محاسبه تقریبی حجم بتن و وزن میلگرد\n"
        "بر اساس مشخصات واردشده\n\n"
        "👇 بخش موردنظر را انتخاب کنید:"
    )

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            text=text,
            reply_markup=home_keyboard(),
            parse_mode="HTML",
        )
        await query.message.reply_text(
            "☰ منوی سریع",
            reply_markup=bottom_menu(),
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=bottom_menu(),
            parse_mode="HTML",
        )
        await update.message.reply_text(
            "👇 بخش موردنظر را انتخاب کنید:",
            reply_markup=home_keyboard(),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_home(update, context)


# =========================================================
# منوهای بخش‌ها
# =========================================================

async def foundation_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧱 پی منفرد", callback_data="foundation_isolated"),
            ],
            [
                InlineKeyboardButton("📏 پی نواری", callback_data="foundation_strip"),
            ],
            [
                InlineKeyboardButton("⬛ پی گسترده (رادیه)", callback_data="foundation_raft"),
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    text = "🧱 <b>فونداسیون</b>\n\nنوع فونداسیون را انتخاب کنید:"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def columns_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬛ ستون مربعی / مستطیلی",
                    callback_data="column_rect",
                )
            ],
            [
                InlineKeyboardButton(
                    "⭕ ستون گرد",
                    callback_data="column_round",
                )
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    text = "🏛️ <b>ستون‌ها</b>\n\nنوع ستون را انتخاب کنید:"

    await update.callback_query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def beams_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📐 تیر اصلی", callback_data="beam_main"),
            ],
            [
                InlineKeyboardButton("📐 تیر فرعی", callback_data="beam_secondary"),
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        "📐 <b>تیرها</b>\n\nنوع تیر را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def roofs_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🟨 تیرچه یونولیتی", callback_data="roof_یونولیتی"),
                InlineKeyboardButton("🧱 تیرچه سفالی", callback_data="roof_سفالی"),
            ],
            [
                InlineKeyboardButton("➿ تیرچه دوبل", callback_data="roof_دوبل"),
                InlineKeyboardButton("🔩 کرومیت", callback_data="roof_کرومیت"),
            ],
            [
                InlineKeyboardButton("🏗️ کامپوزیت", callback_data="roof_کامپوزیت"),
                InlineKeyboardButton("〰️ عرشه فولادی", callback_data="roof_عرشه"),
            ],
            [
                InlineKeyboardButton("⬛ دال بتنی", callback_data="roof_دال"),
                InlineKeyboardButton("🔳 وافل", callback_data="roof_وافل"),
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        "🏠 <b>سقف‌ها</b>\n\nنوع سقف را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def ties_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔗 شناژ", callback_data="tie_beam"),
                InlineKeyboardButton("🔗 کلاف", callback_data="tie_beam"),
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        "🔗 <b>شناژ و کلاف</b>\n\nنوع عضو را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def walls_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🧱 دیوار برشی", callback_data="wall_shear"),
            ],
            [
                InlineKeyboardButton("🧱 دیوار حائل", callback_data="wall_retaining"),
            ],
            [
                InlineKeyboardButton("🔙 برگشت", callback_data="home"),
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        "🧱 <b>دیوارها</b>\n\nنوع دیوار را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# =========================================================
# فیلدهای ورودی
# =========================================================

ISOLATED_FIELDS = [
    ("count", "تعداد پی", "int"),
    ("length", "طول پی (m)", "float"),
    ("width", "عرض پی (m)", "float"),
    ("thickness", "ضخامت پی (m)", "float"),

    ("lean_length", "طول بتن مگر (m)", "float"),
    ("lean_width", "عرض بتن مگر (m)", "float"),
    ("lean_thickness", "ضخامت بتن مگر (m)", "float"),

    ("bottom_diameter", "قطر میلگرد پایین (mm)", "int"),
    ("bottom_spacing", "فاصله میلگرد پایین (mm)", "float"),

    ("top_diameter", "قطر میلگرد بالا (mm) - در صورت نداشتن 0", "int"),
    ("top_spacing", "فاصله میلگرد بالا (mm) - در صورت نداشتن 0", "float"),

    ("cover", "کاور بتن (mm)", "float"),
    ("lap", "درصد اورلپ", "float"),

    ("pedestal_length", "طول پدستال (m) - در صورت نداشتن 0", "float"),
    ("pedestal_width", "عرض پدستال (m) - در صورت نداشتن 0", "float"),
    ("pedestal_height", "ارتفاع پدستال (m) - در صورت نداشتن 0", "float"),
]


STRIP_FIELDS = [
    ("count", "تعداد نوار / پی", "int"),
    ("length", "طول نوار پی (m)", "float"),
    ("footing_width", "عرض پی نواری (m)", "float"),
    ("footing_thickness", "ضخامت پی (m)", "float"),

    ("lean_length", "طول بتن مگر (m)", "float"),
    ("lean_width", "عرض بتن مگر (m)", "float"),
    ("lean_thickness", "ضخامت بتن مگر (m)", "float"),

    ("longitudinal_diameter", "قطر میلگرد طولی (mm)", "int"),
    ("longitudinal_count", "تعداد میلگرد طولی", "int"),

    ("transverse_diameter", "قطر میلگرد عرضی (mm)", "int"),
    ("transverse_spacing", "فاصله میلگرد عرضی (mm)", "float"),

    ("top_longitudinal_diameter", "قطر میلگرد طولی بالا (mm) - بدون آن 0", "int"),
    ("top_longitudinal_count", "تعداد میلگرد طولی بالا - بدون آن 0", "int"),

    ("top_transverse_diameter", "قطر میلگرد عرضی بالا (mm) - بدون آن 0", "int"),
    ("top_transverse_spacing", "فاصله میلگرد عرضی بالا (mm) - بدون آن 0", "float"),

    ("cover", "کاور بتن (mm)", "float"),
    ("lap", "درصد اورلپ", "float"),
]


RAFT_FIELDS = [
    ("length", "طول رادیه (m)", "float"),
    ("width", "عرض رادیه (m)", "float"),
    ("thickness", "ضخامت رادیه (m)", "float"),

    ("lean_length", "طول بتن مگر (m)", "float"),
    ("lean_width", "عرض بتن مگر (m)", "float"),
    ("lean_thickness", "ضخامت بتن مگر (m)", "float"),

    ("bottom_x_diameter", "قطر میلگرد پایین X (mm)", "int"),
    ("bottom_x_spacing", "فاصله میلگرد پایین X (mm)", "float"),

    ("bottom_y_diameter", "قطر میلگرد پایین Y (mm)", "int"),
    ("bottom_y_spacing", "فاصله میلگرد پایین Y (mm)", "float"),

    ("top_x_diameter", "قطر میلگرد بالا X (mm) - بدون آن 0", "int"),
    ("top_x_spacing", "فاصله میلگرد بالا X (mm) - بدون آن 0", "float"),

    ("top_y_diameter", "قطر میلگرد بالا Y (mm) - بدون آن 0", "int"),
    ("top_y_spacing", "فاصله میلگرد بالا Y (mm) - بدون آن 0", "float"),

    ("cover", "کاور بتن (mm)", "float"),
    ("lap", "درصد اورلپ", "float"),
]


COLUMN_RECT_FIELDS = [
    ("count", "تعداد ستون", "int"),
    ("width", "عرض ستون (m)", "float"),
    ("depth", "عمق ستون (m)", "float"),
    ("height", "ارتفاع ستون (m)", "float"),
    ("main_diameter", "قطر میلگرد طولی (mm)", "int"),
    ("main_count", "تعداد میلگرد طولی", "int"),
    ("stirrup_diameter", "قطر خاموت (mm)", "int"),
    ("stirrup_spacing", "فاصله خاموت (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


COLUMN_ROUND_FIELDS = [
    ("count", "تعداد ستون", "int"),
    ("diameter", "قطر ستون (m)", "float"),
    ("height", "ارتفاع ستون (m)", "float"),
    ("main_diameter", "قطر میلگرد طولی (mm)", "int"),
    ("main_count", "تعداد میلگرد طولی", "int"),
    ("stirrup_diameter", "قطر خاموت (mm)", "int"),
    ("stirrup_spacing", "فاصله خاموت (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


BEAM_FIELDS = [
    ("count", "تعداد تیر", "int"),
    ("length", "طول تیر (m)", "float"),
    ("width", "عرض تیر (m)", "float"),
    ("height", "ارتفاع تیر (m)", "float"),
    ("main_diameter", "قطر میلگرد اصلی (mm)", "int"),
    ("bottom_count", "تعداد میلگرد پایین", "int"),
    ("top_count", "تعداد میلگرد بالا", "int"),
    ("stirrup_diameter", "قطر خاموت (mm)", "int"),
    ("stirrup_spacing", "فاصله خاموت (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


TIE_FIELDS = [
    ("count", "تعداد شناژ / کلاف", "int"),
    ("length", "طول (m)", "float"),
    ("width", "عرض (m)", "float"),
    ("height", "ارتفاع (m)", "float"),
    ("main_diameter", "قطر میلگرد طولی (mm)", "int"),
    ("main_count", "تعداد میلگرد طولی", "int"),
    ("stirrup_diameter", "قطر خاموت (mm)", "int"),
    ("stirrup_spacing", "فاصله خاموت (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


WALL_FIELDS = [
    ("count", "تعداد دیوار", "int"),
    ("length", "طول دیوار (m)", "float"),
    ("height", "ارتفاع دیوار (m)", "float"),
    ("thickness", "ضخامت دیوار (m)", "float"),
    ("main_diameter", "قطر میلگرد اصلی (mm)", "int"),
    ("main_spacing", "فاصله میلگرد اصلی (mm)", "float"),
    ("secondary_diameter", "قطر میلگرد توزیعی (mm)", "int"),
    ("secondary_spacing", "فاصله میلگرد توزیعی (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


STAIR_FIELDS = [
    ("count", "تعداد راه‌پله", "int"),
    ("width", "عرض راه‌پله (m)", "float"),
    ("length", "طول شیب / رمپ (m)", "float"),
    ("thickness", "ضخامت دال (m)", "float"),
    ("main_diameter", "قطر میلگرد اصلی (mm)", "int"),
    ("main_spacing", "فاصله میلگرد اصلی (mm)", "float"),
    ("secondary_diameter", "قطر میلگرد توزیعی (mm)", "int"),
    ("secondary_spacing", "فاصله میلگرد توزیعی (mm)", "float"),
    ("cover", "کاور بتن (mm)", "float"),
]


ROOF_FIELDS = [
    ("area", "مساحت سقف (m²)", "float"),
    ("rebar_kg_m2", "وزن میلگرد تقریبی به ازای هر m² (kg/m²)", "float"),
]


# =========================================================
# Wizard
# =========================================================

async def start_wizard(
    update,
    context,
    title,
    fields_list,
    calc,
    back_callback,
):
    reset_flow(context)

    context.user_data["mode"] = "wizard"
    context.user_data["title"] = title
    context.user_data["fields_list"] = fields_list
    context.user_data["fields"] = {}
    context.user_data["index"] = 0
    context.user_data["calc"] = calc
    context.user_data["back_callback"] = back_callback

    await ask_current_field(update, context)


async def ask_current_field(update, context):
    index = context.user_data["index"]
    fields_list = context.user_data["fields_list"]

    if index >= len(fields_list):
        await calculate_wizard(update, context)
        return

    key, label, field_type = fields_list[index]

    text = (
        f"🏗️ <b>{context.user_data['title']}</b>\n\n"
        f"مرحله {index + 1} از {len(fields_list)}\n\n"
        f"✏️ <b>{label}</b>\n\n"
        f"مقدار را وارد کنید:"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="wizard_back",
                ),
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="home",
                ),
            ]
        ]
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def calculate_wizard(update, context):
    try:
        result = context.user_data["calc"](context.user_data["fields"])
        context.user_data["result"] = result

        await show_generic_result(update, context)

    except Exception as e:
        logger.exception("Calculation error")

        text = (
            "❌ <b>خطا در محاسبه</b>\n\n"
            "اطلاعات واردشده با محاسبات سازگار نیست.\n\n"
            f"<code>{str(e)}</code>"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 برگشت",
                                callback_data=context.user_data.get(
                                    "back_callback",
                                    "home",
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            await update.message.reply_text(text, parse_mode="HTML")


async def wizard_back(update, context):
    query = update.callback_query

    index = context.user_data.get("index", 0)

    if index <= 0:
        callback = context.user_data.get("back_callback", "home")
        await route_callback(query, context, callback)
        return

    index -= 1
    context.user_data["index"] = index

    key, _, _ = context.user_data["fields_list"][index]
    context.user_data["fields"].pop(key, None)

    await ask_current_field(update, context)


# =========================================================
# شروع محاسبات
# =========================================================

async def start_isolated(update, context):
    await start_wizard(
        update,
        context,
        "پی منفرد",
        ISOLATED_FIELDS,
        calc_isolated,
        "foundation",
    )


async def start_strip(update, context):
    await start_wizard(
        update,
        context,
        "پی نواری",
        STRIP_FIELDS,
        calc_strip,
        "foundation",
    )


async def start_raft(update, context):
    await start_wizard(
        update,
        context,
        "پی گسترده (رادیه)",
        RAFT_FIELDS,
        calc_raft,
        "foundation",
    )


async def start_column_rect(update, context):
    await start_wizard(
        update,
        context,
        "ستون مستطیلی",
        COLUMN_RECT_FIELDS,
        calc_column_rect,
        "columns",
    )


async def start_column_round(update, context):
    await start_wizard(
        update,
        context,
        "ستون گرد",
        COLUMN_ROUND_FIELDS,
        calc_column_round,
        "columns",
    )


async def start_beam(update, context, secondary=False):
    await start_wizard(
        update,
        context,
        "تیر فرعی" if secondary else "تیر اصلی",
        BEAM_FIELDS,
        calc_beam,
        "beams",
    )


async def start_tie(update, context):
    await start_wizard(
        update,
        context,
        "شناژ / کلاف",
        TIE_FIELDS,
        calc_tie,
        "ties",
    )


async def start_wall(update, context, wall_type="دیوار"):
    await start_wizard(
        update,
        context,
        wall_type,
        WALL_FIELDS,
        calc_wall,
        "walls",
    )


async def start_stair(update, context):
    await start_wizard(
        update,
        context,
        "راه‌پله",
        STAIR_FIELDS,
        calc_stair,
        "home",
    )


async def start_roof(update, context, roof_type):
    async def roof_calc(fields):
        return roof_slab(
            roof_type=roof_type,
            area_m2=float(fields["area"]),
            rebar_kg_per_m2=float(fields["rebar_kg_m2"]),
        )

    await start_wizard(
        update,
        context,
        f"سقف {roof_type}",
        ROOF_FIELDS,
        roof_calc,
        "roofs",
    )


# =========================================================
# توابع محاسبات
# =========================================================

def calc_isolated(f):
    top_diameter = int(f["top_diameter"])
    top_spacing = float(f["top_spacing"])

    if top_diameter <= 0 or top_spacing <= 0:
        top_diameter = None
        top_spacing = None

    return isolated_footing(
        count=int(f["count"]),
        length_m=float(f["length"]),
        width_m=float(f["width"]),
        thickness_m=float(f["thickness"]),
        lean_concrete_length_m=float(f["lean_length"]),
        lean_concrete_width_m=float(f["lean_width"]),
        lean_concrete_thickness_m=float(f["lean_thickness"]),
        bottom_diameter_mm=int(f["bottom_diameter"]),
        bottom_spacing_mm=float(f["bottom_spacing"]),
        top_diameter_mm=top_diameter,
        top_spacing_mm=top_spacing,
        cover_mm=float(f["cover"]),
        lap_percent=float(f["lap"]),
        pedestal_length_m=float(f["pedestal_length"]),
        pedestal_width_m=float(f["pedestal_width"]),
        pedestal_height_m=float(f["pedestal_height"]),
    )


def calc_strip(f):
    top_long_diameter = int(f["top_longitudinal_diameter"])
    top_long_count = int(f["top_longitudinal_count"])
    top_trans_diameter = int(f["top_transverse_diameter"])
    top_trans_spacing = float(f["top_transverse_spacing"])

    if top_long_diameter <= 0 or top_long_count <= 0:
        top_long_diameter = None
        top_long_count = None

    if top_trans_diameter <= 0 or top_trans_spacing <= 0:
        top_trans_diameter = None
        top_trans_spacing = None

    return strip_footing(
        count=int(f["count"]),
        length_m=float(f["length"]),
        width_m=float(f["footing_width"]),
        thickness_m=float(f["footing_thickness"]),
        lean_concrete_length_m=float(f["lean_length"]),
        lean_concrete_width_m=float(f["lean_width"]),
        lean_concrete_thickness_m=float(f["lean_thickness"]),
        longitudinal_diameter_mm=int(f["longitudinal_diameter"]),
        longitudinal_count=int(f["longitudinal_count"]),
        transverse_diameter_mm=int(f["transverse_diameter"]),
        transverse_spacing_mm=float(f["transverse_spacing"]),
        top_longitudinal_diameter_mm=top_long_diameter,
        top_longitudinal_count=top_long_count,
        top_transverse_diameter_mm=top_trans_diameter,
        top_transverse_spacing_mm=top_trans_spacing,
        cover_mm=float(f["cover"]),
        lap_percent=float(f["lap"]),
    )


def calc_raft(f):
    top_x_diameter = int(f["top_x_diameter"])
    top_x_spacing = float(f["top_x_spacing"])
    top_y_diameter = int(f["top_y_diameter"])
    top_y_spacing = float(f["top_y_spacing"])

    if top_x_diameter <= 0 or top_x_spacing <= 0:
        top_x_diameter = None
        top_x_spacing = None

    if top_y_diameter <= 0 or top_y_spacing <= 0:
        top_y_diameter = None
        top_y_spacing = None

    return raft_foundation(
        length_m=float(f["length"]),
        width_m=float(f["width"]),
        thickness_m=float(f["thickness"]),
        lean_concrete_length_m=float(f["lean_length"]),
        lean_concrete_width_m=float(f["lean_width"]),
        lean_concrete_thickness_m=float(f["lean_thickness"]),
        bottom_x_diameter_mm=int(f["bottom_x_diameter"]),
        bottom_x_spacing_mm=float(f["bottom_x_spacing"]),
        bottom_y_diameter_mm=int(f["bottom_y_diameter"]),
        bottom_y_spacing_mm=float(f["bottom_y_spacing"]),
        top_x_diameter_mm=top_x_diameter,
        top_x_spacing_mm=top_x_spacing,
        top_y_diameter_mm=top_y_diameter,
        top_y_spacing_mm=top_y_spacing,
        cover_mm=float(f["cover"]),
        lap_percent=float(f["lap"]),
    )


def calc_column_rect(f):
    return column_rectangular(
        count=int(f["count"]),
        width_m=float(f["width"]),
        depth_m=float(f["depth"]),
        height_m=float(f["height"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_count=int(f["main_count"]),
        stirrup_diameter_mm=int(f["stirrup_diameter"]),
        stirrup_spacing_mm=float(f["stirrup_spacing"]),
        cover_mm=float(f["cover"]),
    )


def calc_column_round(f):
    return column_round(
        count=int(f["count"]),
        diameter_m=float(f["diameter"]),
        height_m=float(f["height"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_count=int(f["main_count"]),
        stirrup_diameter_mm=int(f["stirrup_diameter"]),
        stirrup_spacing_mm=float(f["stirrup_spacing"]),
        cover_mm=float(f["cover"]),
    )


def calc_beam(f):
    return beam(
        count=int(f["count"]),
        length_m=float(f["length"]),
        width_m=float(f["width"]),
        height_m=float(f["height"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_top_count=int(f["top_count"]),
        main_bottom_count=int(f["bottom_count"]),
        stirrup_diameter_mm=int(f["stirrup_diameter"]),
        stirrup_spacing_mm=float(f["stirrup_spacing"]),
        cover_mm=float(f["cover"]),
    )


def calc_tie(f):
    return tie_beam(
        count=int(f["count"]),
        length_m=float(f["length"]),
        width_m=float(f["width"]),
        height_m=float(f["height"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_count=int(f["main_count"]),
        stirrup_diameter_mm=int(f["stirrup_diameter"]),
        stirrup_spacing_mm=float(f["stirrup_spacing"]),
        cover_mm=float(f["cover"]),
    )


def calc_wall(f):
    return wall_concrete(
        count=int(f["count"]),
        length_m=float(f["length"]),
        height_m=float(f["height"]),
        thickness_m=float(f["thickness"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_spacing_mm=float(f["main_spacing"]),
        secondary_diameter_mm=int(f["secondary_diameter"]),
        secondary_spacing_mm=float(f["secondary_spacing"]),
        cover_mm=float(f["cover"]),
    )


def calc_stair(f):
    return stair_slab(
        count=int(f["count"]),
        width_m=float(f["width"]),
        length_m=float(f["length"]),
        thickness_m=float(f["thickness"]),
        main_diameter_mm=int(f["main_diameter"]),
        main_spacing_mm=float(f["main_spacing"]),
        secondary_diameter_mm=int(f["secondary_diameter"]),
        secondary_spacing_mm=float(f["secondary_spacing"]),
        cover_mm=float(f["cover"]),
    )


# =========================================================
# استخراج خروجی محاسبات
# =========================================================

def get_concrete_total(result):
    if not isinstance(result, dict):
        return 0

    if result.get("total_concrete") is not None:
        return result.get("total_concrete", 0)

    if result.get("concrete") is not None:
        return result.get("concrete", 0)

    total = 0

    for key in [
        "lean_concrete",
        "footing_concrete",
        "pedestal_concrete",
        "raft_concrete",
        "structural_concrete",
    ]:
        total += float(result.get(key, 0) or 0)

    return total


def get_rebar_total(result):
    if not isinstance(result, dict):
        return 0

    rebar = result.get("rebar")

    if isinstance(rebar, dict):
        return float(rebar.get("total_weight", 0) or 0)

    return float(result.get("rebar_weight", 0) or 0)


def get_rebar_details(result):
    if not isinstance(result, dict):
        return []

    rebar = result.get("rebar")

    if isinstance(rebar, dict):
        details = rebar.get("details", [])
        return details if isinstance(details, list) else []

    return []


def detail_value(item, *keys, default=0):
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return default


# =========================================================
# خروجی ستونی
# =========================================================

def make_summary_block(result):
    title = context_title_placeholder = ""

    result_type = result.get("type", "")

    lines = []

    if result_type == "isolated_footing":
        lines.append("🏗️ مشخصات پی منفرد")
        lines.append("")

        lines.append(f"تعداد پی:       {result.get('count', 0)} عدد")
        lines.append(
            f"بتن پی:         {fmt_m3(result.get('footing_concrete', 0))}"
        )
        lines.append(
            f"بتن پدستال:     {fmt_m3(result.get('pedestal_concrete', 0))}"
        )
        lines.append(
            f"بتن مگر:        {fmt_m3(result.get('lean_concrete', 0))}"
        )

    elif result_type == "strip_footing":
        lines.append("📏 مشخصات پی نواری")
        lines.append("")

        lines.append(
            f"تعداد:          {result.get('count', 0)}"
        )
        lines.append(
            f"بتن پی:         {fmt_m3(result.get('footing_concrete', 0))}"
        )
        lines.append(
            f"بتن مگر:        {fmt_m3(result.get('lean_concrete', 0))}"
        )

    elif result_type == "raft_foundation":
        lines.append("⬛ مشخصات رادیه")
        lines.append("")

        lines.append(
            f"بتن رادیه:      {fmt_m3(result.get('raft_concrete', 0))}"
        )
        lines.append(
            f"بتن مگر:        {fmt_m3(result.get('lean_concrete', 0))}"
        )

    elif result_type == "column":
        lines.append("🏛️ مشخصات ستون")
        lines.append("")
        lines.append(
            f"تعداد ستون:     {result.get('count', 0)} عدد"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    elif result_type == "beam":
        lines.append("📐 مشخصات تیر")
        lines.append("")
        lines.append(
            f"تعداد تیر:      {result.get('count', 0)} عدد"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    elif result_type == "wall":
        lines.append("🧱 مشخصات دیوار")
        lines.append("")
        lines.append(
            f"تعداد دیوار:    {result.get('count', 0)} عدد"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    elif result_type == "stair":
        lines.append("🪜 مشخصات راه‌پله")
        lines.append("")
        lines.append(
            f"تعداد:          {result.get('count', 0)} عدد"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    elif result_type == "roof":
        lines.append("🏠 مشخصات سقف")
        lines.append("")
        lines.append(
            f"نوع سقف:        {result.get('roof_type', '-')}"
        )
        lines.append(
            f"مساحت:          {fmt(result.get('area', 0), 2)} m²"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    elif result_type == "tie_beam":
        lines.append("🔗 مشخصات شناژ / کلاف")
        lines.append("")
        lines.append(
            f"تعداد:          {result.get('count', 0)} عدد"
        )
        lines.append(
            f"بتن:            {fmt_m3(result.get('concrete', 0))}"
        )

    else:
        lines.append("📊 نتیجه محاسبه")
        lines.append("")

        concrete = result.get("concrete", result.get("total_concrete", 0))
        lines.append(f"بتن:            {fmt_m3(concrete)}")

    concrete_total = get_concrete_total(result)
    rebar_total = get_rebar_total(result)

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━")
    lines.append(f"کل بتن:         {fmt_m3(concrete_total)}")
    lines.append(f"کل میلگرد:      {fmt_kg(rebar_total)}")
    lines.append("━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


def make_rebar_block(result):
    details = get_rebar_details(result)
    total = get_rebar_total(result)

    lines = [
        "🔩 جزئیات میلگرد",
        "",
        "━━━━━━━━━━━━━━━━",
    ]

    if not details:
        lines.append("جزئیات میلگرد در این محاسبه موجود نیست.")
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"جمع میلگرد:     {fmt_kg(total)}")
        return "\n".join(lines)

    for i, item in enumerate(details, start=1):
        diameter = detail_value(
            item,
            "diameter",
            "diameter_mm",
        )

        pieces = detail_value(
            item,
            "pieces",
            "count",
        )

        piece_length = detail_value(
            item,
            "piece_length",
            "piece_length_m",
        )

        weight = detail_value(
            item,
            "weight",
            "weight_kg",
        )

        lines.extend(
            [
                f"میلگرد {i}",
                f"قطر:            Φ{fmt(diameter)}",
                f"تعداد:          {fmt(pieces)} عدد",
                f"طول هر قطعه:    {fmt_m(piece_length)}",
                f"وزن:            {fmt_kg(weight)}",
                "",
            ]
        )

    lines.append("━━━━━━━━━━━━━━━━")
    lines.append(f"جمع میلگرد:     {fmt_kg(total)}")

    return "\n".join(lines)


def make_cutlist_block(result):
    details = get_rebar_details(result)

    lines = [
        "✂️ Cut List",
        "",
        "━━━━━━━━━━━━━━━━",
    ]

    if not details:
        lines.append("لیست برش برای این محاسبه موجود نیست.")
        lines.append("")
        lines.append(
            "برای این بخش فعلاً فقط جزئیات میلگرد ثبت شده است."
        )
        lines.append("━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    for i, item in enumerate(details, start=1):
        diameter = detail_value(
            item,
            "diameter",
            "diameter_mm",
        )

        pieces = detail_value(
            item,
            "pieces",
            "count",
        )

        piece_length = detail_value(
            item,
            "piece_length",
            "piece_length_m",
        )

        bars_12m = detail_value(
            item,
            "bars_12m",
        )

        lines.extend(
            [
                f"قطعه {i}",
                f"قطر:            Φ{fmt(diameter)}",
                f"طول:            {fmt_m(piece_length)}",
                f"تعداد:          {fmt(pieces)} عدد",
                f"شاخه ۱۲ متری:   {fmt(bars_12m)} شاخه",
                "",
            ]
        )

    lines.append("━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


# =========================================================
# نتیجه
# =========================================================

def result_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔩 جزئیات میلگرد",
                    callback_data="result_rebar",
                ),
                InlineKeyboardButton(
                    "✂️ Cut List",
                    callback_data="result_cutlist",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 محاسبه جدید",
                    callback_data="result_new",
                ),
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="result_back",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home",
                )
            ],
        ]
    )


async def show_generic_result(update, context):
    result = context.user_data.get("result")

    if not result:
        await send_home(update, context)
        return

    text = make_summary_block(result)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"<pre>{text}</pre>",
            reply_markup=result_keyboard(),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"<pre>{text}</pre>",
            reply_markup=result_keyboard(),
            parse_mode="HTML",
        )


async def show_rebar_result(update, context):
    result = context.user_data.get("result")

    if not result:
        await send_home(update, context)
        return

    text = make_rebar_block(result)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✂️ Cut List",
                    callback_data="result_cutlist",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 نتیجه اصلی",
                    callback_data="result_main",
                )
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        f"<pre>{text}</pre>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def show_cutlist_result(update, context):
    result = context.user_data.get("result")

    if not result:
        await send_home(update, context)
        return

    text = make_cutlist_block(result)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔩 جزئیات میلگرد",
                    callback_data="result_rebar",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 نتیجه اصلی",
                    callback_data="result_main",
                )
            ],
        ]
    )

    await update.callback_query.edit_message_text(
        f"<pre>{text}</pre>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# =========================================================
# منوهای عمومی
# =========================================================

async def show_help(update, context):
    text = (
        "ℹ️ <b>راهنمای ربات</b>\n\n"
        "این ربات برای برآورد اولیه حجم بتن و مقدار میلگرد "
        "اعضای مختلف اسکلت بتنی طراحی شده است.\n\n"
        "مقادیر ابعادی و مشخصات میلگرد را وارد کنید تا نتیجه "
        "بر اساس اطلاعات واردشده محاسبه شود.\n\n"
        "⚠️ نتایج متره و برآورد اولیه هستند و جایگزین نقشه "
        "سازه و محاسبات مهندس محاسب نیستند."
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 برگشت", callback_data="home")]]
        ),
        parse_mode="HTML",
    )


async def show_settings(update, context):
    text = (
        "⚙️ <b>تنظیمات</b>\n\n"
        "واحد طول: متر / میلی‌متر\n"
        "واحد بتن: مترمکعب\n"
        "واحد میلگرد: کیلوگرم\n"
        "طول شاخه استاندارد: ۱۲ متر"
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 برگشت", callback_data="home")]]
        ),
        parse_mode="HTML",
    )


async def show_summary(update, context):
    text = (
        "📊 <b>خلاصه پروژه</b>\n\n"
        "فعلاً نتیجه‌ها برای هر محاسبه جداگانه نمایش داده می‌شوند.\n\n"
        "در مرحله بعد می‌توانیم نتایج چند عضو را در یک پروژه "
        "ذخیره و جمع کل بتن و میلگرد پروژه را محاسبه کنیم."
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 برگشت", callback_data="home")]]
        ),
        parse_mode="HTML",
    )


# =========================================================
# Callback Router
# =========================================================

async def route_callback(query, context, data):
    update = Update(
        update_id=0,
        callback_query=query,
    )

    if data == "home":
        await send_home(update, context)

    elif data == "foundation":
        await foundation_menu(update, context)

    elif data == "columns":
        await columns_menu(update, context)

    elif data == "beams":
        await beams_menu(update, context)

    elif data == "roofs":
        await roofs_menu(update, context)

    elif data == "ties":
        await ties_menu(update, context)

    elif data == "walls":
        await walls_menu(update, context)

    elif data == "foundation_isolated":
        await start_isolated(update, context)

    elif data == "foundation_strip":
        await start_strip(update, context)

    elif data == "foundation_raft":
        await start_raft(update, context)

    elif data == "column_rect":
        await start_column_rect(update, context)

    elif data == "column_round":
        await start_column_round(update, context)

    elif data == "beam_main":
        await start_beam(update, context, secondary=False)

    elif data == "beam_secondary":
        await start_beam(update, context, secondary=True)

    elif data == "tie_beam":
        await start_tie(update, context)

    elif data == "wall_shear":
        await start_wall(update, context, "دیوار برشی")

    elif data == "wall_retaining":
        await start_wall(update, context, "دیوار حائل")

    elif data == "stair":
        await start_stair(update, context)

    elif data.startswith("roof_"):
        roof_map = {
            "roof_یونولیتی": "تیرچه یونولیتی",
            "roof_سفالی": "تیرچه سفالی",
            "roof_دوبل": "تیرچه دوبل",
            "roof_کرومیت": "کرومیت",
            "roof_کامپوزیت": "کامپوزیت",
            "roof_عرشه": "عرشه فولادی",
            "roof_دال": "دال بتنی",
            "roof_وافل": "وافل",
        }

        roof_type = roof_map.get(data)

        if roof_type:
            await start_roof(update, context, roof_type)

    elif data == "wizard_back":
        await wizard_back(update, context)

    elif data == "result_rebar":
        await show_rebar_result(update, context)

    elif data == "result_cutlist":
        await show_cutlist_result(update, context)

    elif data == "result_main":
        await show_generic_result(update, context)

    elif data == "result_back":
        callback = context.user_data.get(
            "back_callback",
            "home",
        )
        await route_callback(query, context, callback)

    elif data == "result_new":
        callback = context.user_data.get(
            "back_callback",
            "home",
        )
        await route_callback(query, context, callback)

    elif data == "summary":
        await show_summary(update, context)

    elif data == "settings":
        await show_settings(update, context)

    elif data == "help":
        await show_help(update, context)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    await route_callback(query, context, query.data)


# =========================================================
# دریافت ورودی عددی
# =========================================================

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text in ("☰ منو", "🏠 خانه"):
        await send_home(update, context)
        return

    if context.user_data.get("mode") != "wizard":
        await update.message.reply_text(
            "از منوی پایین استفاده کن 👇",
            reply_markup=bottom_menu(),
        )
        return

    fields_list = context.user_data.get("fields_list", [])
    index = context.user_data.get("index", 0)

    if index >= len(fields_list):
        return

    key, label, field_type = fields_list[index]

    try:
        number = normalize_number(text)

        if field_type == "int":
            if number != int(number):
                raise ValueError("integer required")

            value = int(number)

        else:
            value = float(number)

        if value < 0:
            raise ValueError("negative")

    except Exception:
        await update.message.reply_text(
            "❌ مقدار واردشده معتبر نیست.\n\n"
            "لطفاً فقط عدد وارد کن.\n"
            "مثال: <code>2.5</code>",
            parse_mode="HTML",
            reply_markup=bottom_menu(),
        )
        return

    context.user_data["fields"][key] = value
    context.user_data["index"] = index + 1

    await ask_current_field(update, context)


# =========================================================
# Error Handler
# =========================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception(
        "Exception while handling update:",
        exc_info=context.error,
    )

    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ یک خطای غیرمنتظره رخ داد.\n"
                "لطفاً دوباره از منو شروع کن.",
                reply_markup=bottom_menu(),
            )
    except Exception:
        pass


# =========================================================
# Main
# =========================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(buttons)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive,
        )
    )

    application.add_error_handler(error_handler)

    webhook_url = f"{RENDER_EXTERNAL_URL}/telegram"

    logger.info("Starting bot with webhook...")
    logger.info("Webhook URL: %s", webhook_url)

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
