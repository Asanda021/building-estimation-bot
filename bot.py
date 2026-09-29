# bot.py
# -*- coding: utf-8 -*-

import os
import logging
import math
from html import escape

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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")


# ============================================================
# TEXT
# ============================================================

TEXT = {
    "fa": {
        "welcome": (
            "🏗️ <b>اسکلت بتنی</b>\n\n"
            "عضو موردنظر را انتخاب کنید:"
        ),
        "invalid": "❌ مقدار واردشده معتبر نیست. دوباره تلاش کن.",
        "calc_error": "❌ خطا در محاسبه:\n<code>{}</code>",
        "back": "🔙 بازگشت",
        "home": "🏠 صفحه اصلی",
        "cancel": "❌ لغو",
        "custom": "✏️ عدد دلخواه",
        "review": "📋 بررسی اطلاعات",
        "calculate": "✅ محاسبه",
        "edit": "✏️ ویرایش",
        "none": "🚫 ندارد",
    },

    "en": {
        "welcome": (
            "🏗️ <b>Concrete Frame</b>\n\n"
            "Choose a member:"
        ),
        "invalid": "❌ Invalid value. Try again.",
        "calc_error": "❌ Calculation error:\n<code>{}</code>",
        "back": "🔙 Back",
        "home": "🏠 Main Menu",
        "cancel": "❌ Cancel",
        "custom": "✏️ Custom value",
        "review": "📋 Review",
        "calculate": "✅ Calculate",
        "edit": "✏️ Edit",
        "none": "🚫 None",
    },
}


# ============================================================
# INTERNAL DEFAULTS
# فعلاً برای سازگاری با calculations.py فعلی
# بعداً با محاسبات واقعی مبحث ۹ جایگزین می‌شوند.
# ============================================================

DEFAULT_COVER_FOUNDATION = 50
DEFAULT_COVER_MEMBER = 40
DEFAULT_LAP_PERCENT = 0


# ============================================================
# ROOF
# ============================================================

ROOF_COEFF = {
    "foam": 0.18,
    "clay": 0.20,
    "double": 0.23,
    "kromit": 0.18,
    "composite": 0.15,
    "steeldeck": 0.15,
    "slab": 0.20,
    "waffle": 0.20,
}

ROOF_NAMES = {
    "foam": "تیرچه یونولیتی",
    "clay": "تیرچه سفالی",
    "double": "تیرچه دوبل",
    "kromit": "کرومیت",
    "composite": "کامپوزیت",
    "steeldeck": "عرشه فولادی",
    "slab": "دال بتنی",
    "waffle": "وافل",
}


# ============================================================
# COMMON BUTTON VALUES
# ============================================================

COUNT_VALUES = [
    1, 2, 3, 4, 5, 6,
    8, 10, 12, 15, 20, 24,
    30, 40, 50
]

DIMENSION_VALUES = [
    0.20, 0.25, 0.30, 0.35,
    0.40, 0.45, 0.50, 0.60,
    0.70, 0.80, 1.00, 1.20,
    1.50, 2.00, 2.50, 3.00,
    4.00, 5.00, 6.00
]

THICKNESS_VALUES = [
    0.10, 0.12, 0.15, 0.18,
    0.20, 0.25, 0.30, 0.35,
    0.40, 0.45, 0.50, 0.60
]

SPACING_VALUES = [
    10, 15, 20, 25, 30, 35, 40, 45, 50
]

DIAMETERS = [
    6, 8, 10, 12, 14, 16,
    18, 20, 22, 25, 28, 32, 36
]


# ============================================================
# FIELD DEFINITIONS
# ============================================================

STEPS = {

    "iso": [
        ("count", "تعداد پی", "count"),
        ("L", "طول پی", "dimension"),
        ("W", "عرض پی", "dimension"),
        ("T", "ضخامت پی", "thickness"),

        ("leanL", "طول بتن مگر", "dimension"),
        ("leanW", "عرض بتن مگر", "dimension"),
        ("leanT", "ضخامت بتن مگر", "thickness"),

        ("bd", "قطر میلگرد پایین", "diameter"),
        ("bs", "فاصله میلگرد پایین", "spacing"),

        ("td", "قطر میلگرد بالا", "diameter_optional"),
        ("ts", "فاصله میلگرد بالا", "spacing_optional"),

        ("pl", "طول پدستال", "dimension_zero"),
        ("pw", "عرض پدستال", "dimension_zero"),
        ("ph", "ارتفاع پدستال", "dimension_zero"),
    ],

    "strip": [
        ("count", "تعداد نوار", "count"),
        ("L", "طول نوار", "dimension"),
        ("W", "عرض پی", "dimension"),
        ("T", "ضخامت پی", "thickness"),

        ("leanL", "طول بتن مگر", "dimension"),
        ("leanW", "عرض بتن مگر", "dimension"),
        ("leanT", "ضخامت بتن مگر", "thickness"),

        ("ld", "قطر میلگرد طولی پایین", "diameter"),
        ("lc", "تعداد میلگرد طولی پایین", "count"),

        ("td", "قطر میلگرد عرضی پایین", "diameter"),
        ("ts", "فاصله میلگرد عرضی پایین", "spacing"),

        ("tld", "قطر میلگرد طولی بالا", "diameter_optional"),
        ("tlc", "تعداد میلگرد طولی بالا", "count_optional"),

        ("ttd", "قطر میلگرد عرضی بالا", "diameter_optional"),
        ("tts", "فاصله میلگرد عرضی بالا", "spacing_optional"),
    ],

    "raft": [
        ("L", "طول رادیه", "dimension"),
        ("W", "عرض رادیه", "dimension"),
        ("T", "ضخامت رادیه", "thickness"),

        ("leanL", "طول بتن مگر", "dimension"),
        ("leanW", "عرض بتن مگر", "dimension"),
        ("leanT", "ضخامت بتن مگر", "thickness"),

        ("bxd", "قطر X پایین", "diameter"),
        ("bxs", "فاصله X پایین", "spacing"),

        ("byd", "قطر Y پایین", "diameter"),
        ("bys", "فاصله Y پایین", "spacing"),

        ("txd", "قطر X بالا", "diameter_optional"),
        ("txs", "فاصله X بالا", "spacing_optional"),

        ("tyd", "قطر Y بالا", "diameter_optional"),
        ("tys", "فاصله Y بالا", "spacing_optional"),
    ],

    "column_rect": [
        ("count", "تعداد ستون", "count"),
        ("W", "عرض ستون", "dimension"),
        ("D", "عمق ستون", "dimension"),
        ("H", "ارتفاع ستون", "dimension"),

        ("ld", "قطر میلگرد طولی", "diameter"),
        ("lc", "تعداد میلگرد طولی هر ستون", "count"),

        ("sd", "قطر خاموت", "diameter"),
        ("ss", "فاصله خاموت", "spacing"),
    ],

    "column_round": [
        ("count", "تعداد ستون گرد", "count"),
        ("D", "قطر ستون", "dimension"),
        ("H", "ارتفاع ستون", "dimension"),

        ("ld", "قطر میلگرد طولی", "diameter"),
        ("lc", "تعداد میلگرد طولی هر ستون", "count"),

        ("sd", "قطر خاموت", "diameter"),
        ("ss", "فاصله خاموت", "spacing"),
    ],

    "beam": [
        ("count", "تعداد تیر", "count"),
        ("L", "طول تیر", "dimension"),
        ("W", "عرض تیر", "dimension"),
        ("H", "ارتفاع تیر", "dimension"),

        ("bd", "قطر میلگرد پایین", "diameter"),
        ("bc", "تعداد میلگرد پایین", "count"),

        ("td", "قطر میلگرد بالا", "diameter"),
        ("tc", "تعداد میلگرد بالا", "count"),

        ("sd", "قطر خاموت", "diameter"),
        ("ss", "فاصله خاموت", "spacing"),
    ],

    "tie": [
        ("count", "تعداد شناژ / کلاف", "count"),
        ("L", "طول", "dimension"),
        ("W", "عرض", "dimension"),
        ("H", "ارتفاع", "dimension"),

        ("ld", "قطر میلگرد طولی", "diameter"),
        ("lc", "تعداد میلگرد طولی", "count"),

        ("sd", "قطر خاموت", "diameter"),
        ("ss", "فاصله خاموت", "spacing"),
    ],

    "wall": [
        ("L", "طول دیوار", "dimension"),
        ("H", "ارتفاع دیوار", "dimension"),
        ("T", "ضخامت دیوار", "thickness"),

        ("vd", "قطر میلگرد قائم", "diameter"),
        ("vs", "فاصله میلگرد قائم", "spacing"),

        ("hd", "قطر میلگرد افقی", "diameter"),
        ("hs", "فاصله میلگرد افقی", "spacing"),
    ],

    "stair": [
        ("L", "طول شیب / دال", "dimension"),
        ("W", "عرض راه‌پله", "dimension"),
        ("T", "ضخامت دال", "thickness"),

        ("md", "قطر میلگرد اصلی", "diameter"),
        ("ms", "فاصله میلگرد اصلی", "spacing"),

        ("dd", "قطر میلگرد توزیعی", "diameter"),
        ("ds", "فاصله میلگرد توزیعی", "spacing"),

        ("steps", "تعداد پله", "count"),
        ("riser", "ارتفاع رایزر", "dimension"),
        ("tread", "کف پله", "dimension"),
    ],

    "roof": [
        ("L", "طول سقف", "dimension"),
        ("W", "عرض سقف", "dimension"),

        ("dia", "قطر شبکه حرارتی", "diameter"),
        ("spacing", "فاصله شبکه حرارتی", "spacing"),
    ],
}


# ============================================================
# BASIC KEYBOARD HELPERS
# ============================================================

def kb(rows):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text, callback_data=data)
            for text, data in row
        ]
        for row in rows
    ])


def chunk_buttons(items, width=3):
    return [
        items[i:i + width]
        for i in range(0, len(items), width)
    ]


def fmt_num(value):
    value = float(value)

    if value.is_integer():
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".")


def parse_number(raw):
    raw = raw.strip()

    # Persian digits
    trans = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٫",
        "0123456789."
    )

    raw = raw.translate(trans)
    raw = raw.replace(",", ".")
    raw = raw.replace("/", ".")

    value = float(raw)

    if value < 0:
        raise ValueError

    return value


# ============================================================
# MAIN MENU
# ============================================================

def main_menu(lang):

    if lang == "fa":
        return kb([
            [
                ("🧱 فونداسیون", "foundation"),
                ("🏛️ ستون‌ها", "columns"),
            ],
            [
                ("📐 تیرها", "beams"),
                ("🏠 سقف‌ها", "roofs"),
            ],
            [
                ("🪜 راه‌پله", "stairs"),
                ("🔗 شناژ و کلاف", "ties"),
            ],
            [
                ("🧱 دیوارها", "walls"),
            ],
            [
                ("🔄 معادل‌سازی میلگرد", "equiv"),
            ],
            [
                ("📊 خلاصه پروژه", "summary"),
                ("🌐 زبان", "language"),
            ],
            [
                ("⚙️ تنظیمات", "settings"),
            ],
            [
                ("ℹ️ راهنما", "help"),
            ],
        ])

    return kb([
        [
            ("🧱 Foundation", "foundation"),
            ("🏛️ Columns", "columns"),
        ],
        [
            ("📐 Beams", "beams"),
            ("🏠 Roofs", "roofs"),
        ],
        [
            ("🪜 Stairs", "stairs"),
            ("🔗 Tie Beams", "ties"),
        ],
        [
            ("🧱 Walls", "walls"),
        ],
        [
            ("🔄 Rebar Equivalency", "equiv"),
        ],
        [
            ("📊 Summary", "summary"),
            ("🌐 Language", "language"),
        ],
        [
            ("⚙️ Settings", "settings"),
        ],
        [
            ("ℹ️ Help", "help"),
        ],
    ])


def back_home_kb(lang, back="home"):
    return kb([
        [
            (TEXT[lang]["back"], back),
            (TEXT[lang]["home"], "home"),
        ]
    ])


# ============================================================
# FIELD KEYBOARDS
# ============================================================

def field_keyboard(lang, field_type):

    rows = []

    if field_type == "count":
        values = [
            (str(x), f"val_{x}")
            for x in COUNT_VALUES
        ]

        rows.extend(chunk_buttons(values, 5))
        rows.append([
            (TEXT[lang]["custom"], "custom")
        ])

    elif field_type == "count_optional":
        values = [
            (str(x), f"val_{x}")
            for x in COUNT_VALUES
        ]

        rows.extend(chunk_buttons(values, 5))
        rows.append([
            (TEXT[lang]["none"], "val_0"),
            (TEXT[lang]["custom"], "custom"),
        ])

    elif field_type in ("dimension", "dimension_zero"):

        values = [
            (fmt_num(x), f"val_{fmt_num(x)}")
            for x in DIMENSION_VALUES
        ]

        rows.extend(chunk_buttons(values, 3))

        if field_type == "dimension_zero":
            rows.append([
                ("0", "val_0"),
                (TEXT[lang]["custom"], "custom"),
            ])
        else:
            rows.append([
                (TEXT[lang]["custom"], "custom")
            ])

    elif field_type == "thickness":

        values = [
            (fmt_num(x), f"val_{fmt_num(x)}")
            for x in THICKNESS_VALUES
        ]

        rows.extend(chunk_buttons(values, 3))
        rows.append([
            (TEXT[lang]["custom"], "custom")
        ])

    elif field_type == "diameter":

        values = [
            (f"Φ{x}", f"val_{x}")
            for x in DIAMETERS
        ]

        rows.extend(chunk_buttons(values, 4))
        rows.append([
            (TEXT[lang]["custom"], "custom")
        ])

    elif field_type == "diameter_optional":

        values = [
            (f"Φ{x}", f"val_{x}")
            for x in DIAMETERS
        ]

        rows.extend(chunk_buttons(values, 4))
        rows.append([
            (TEXT[lang]["none"], "val_0"),
            (TEXT[lang]["custom"], "custom"),
        ])

    elif field_type == "spacing":

        values = [
            (f"{x} cm", f"val_{x}")
            for x in SPACING_VALUES
        ]

        rows.extend(chunk_buttons(values, 3))
        rows.append([
            (TEXT[lang]["custom"], "custom")
        ])

    elif field_type == "spacing_optional":

        values = [
            (f"{x} cm", f"val_{x}")
            for x in SPACING_VALUES
        ]

        rows.extend(chunk_buttons(values, 3))
        rows.append([
            (TEXT[lang]["none"], "val_0"),
            (TEXT[lang]["custom"], "custom"),
        ])

    rows.append([
        ("⬅️ مرحله قبل", "prev"),
        (TEXT[lang]["cancel"], "cancel"),
    ])

    rows.append([
        (TEXT[lang]["home"], "home")
    ])

    return kb(rows)


# ============================================================
# PROMPT
# ============================================================

def prompt_text(lang, label, i, total, field_type):

    unit = ""

    if field_type in (
        "dimension",
        "dimension_zero",
        "thickness",
    ):
        unit = "\nواحد: متر"

    elif field_type == "spacing":
        unit = "\nواحد: سانتی‌متر"

    elif field_type == "spacing_optional":
        unit = "\nواحد: سانتی‌متر"

    elif field_type in (
        "diameter",
        "diameter_optional",
    ):
        unit = "\nواحد: میلی‌متر"

    return (
        f"📐 <b>{escape(label)}</b>\n"
        f"{unit}\n\n"
        "یکی از گزینه‌ها را انتخاب کن.\n"
        "اگر گزینه مناسب نبود، «عدد دلخواه» را بزن.\n\n"
        "━━━━━━━━━━━━━━\n"
        f"📍 مرحله <b>{i}</b> از <b>{total}</b>"
    )


# ============================================================
# START / LANGUAGE
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "🌐 زبان / Language:",
        reply_markup=kb([
            [
                ("🇮🇷 فارسی", "lang_fa"),
                ("🇸🇦 العربية", "lang_ar"),
            ],
            [
                ("🇬🇧 English", "lang_en"),
                ("🇨🇳 中文", "lang_zh"),
            ],
        ]),
    )


async def choose_language(update, context):

    q = update.callback_query
    await q.answer()

    lang = q.data.split("_", 1)[1]

    if lang not in ("fa", "en"):
        # فعلاً UI محاسباتی کامل برای فارسی و انگلیسی است.
        # زبان‌های دیگر در مرحله بعد متن کامل می‌گیرند.
        lang = "fa"

    old = dict(context.user_data)

    context.user_data.clear()

    context.user_data["lang"] = lang

    # استاندارد پیش‌فرض فعلی
    context.user_data["standard"] = old.get(
        "standard",
        "iran"
    )

    await show_standard_selection(
        update,
        context,
        after_language=True
    )


# ============================================================
# STANDARD
# ============================================================

def standard_keyboard(lang):

    return kb([
        [
            ("🇮🇷 مبحث ۹ ایران", "std_iran"),
        ],
        [
            ("🇺🇸 ACI 318", "std_aci"),
        ],
        [
            ("🇪🇺 Eurocode 2", "std_ec2"),
        ],
        [
            (TEXT[lang]["home"], "home"),
        ],
    ])


async def show_standard_selection(
    update,
    context,
    after_language=False
):

    lang = context.user_data.get("lang", "fa")

    if lang == "fa":
        text = (
            "📚 <b>استاندارد محاسباتی</b>\n\n"
            "استاندارد مورد استفاده برای محاسبات را انتخاب کن:"
        )
    else:
        text = (
            "📚 <b>Calculation Standard</b>\n\n"
            "Choose the calculation standard:"
        )

    q = update.callback_query

    await q.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=standard_keyboard(lang)
    )


# ============================================================
# WIZARD
# ============================================================

async def begin_wizard(update, context, kind):

    q = update.callback_query

    lang = context.user_data.get("lang", "fa")

    context.user_data["kind"] = kind
    context.user_data["step_index"] = 0
    context.user_data["values"] = {}
    context.user_data["history"] = []
    context.user_data["custom_mode"] = False

    fields = STEPS[kind]

    key, label, field_type = fields[0]

    await q.edit_message_text(
        prompt_text(
            lang,
            label,
            1,
            len(fields),
            field_type
        ),
        parse_mode="HTML",
        reply_markup=field_keyboard(
            lang,
            field_type
        ),
    )


# ============================================================
# SAVE FIELD
# ============================================================

async def save_field(update, context, value):

    q = update.callback_query

    lang = context.user_data.get("lang", "fa")
    kind = context.user_data.get("kind")
    idx = context.user_data.get("step_index")

    if kind is None or idx is None:
        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    fields = STEPS[kind]

    key, label, field_type = fields[idx]

    # spacing is stored in mm
    if field_type in (
        "spacing",
        "spacing_optional",
    ):
        value = float(value) * 10

    context.user_data["values"][key] = value

    context.user_data["history"].append(idx)

    next_idx = idx + 1

    if next_idx < len(fields):

        context.user_data["step_index"] = next_idx
        context.user_data["custom_mode"] = False

        next_key, next_label, next_type = fields[next_idx]

        await q.edit_message_text(
            prompt_text(
                lang,
                next_label,
                next_idx + 1,
                len(fields),
                next_type
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                next_type
            ),
        )

        return

    # پایان ورودی‌ها
    context.user_data["step_index"] = None
    context.user_data["custom_mode"] = False

    await show_review(
        update,
        context
    )


# ============================================================
# REVIEW
# ============================================================

def review_value(key, value):

    if value is None:
        return "-"

    if key in (
        "bd", "td", "ld", "tld",
        "ttd", "bxd", "byd",
        "txd", "tyd", "sd",
        "vd", "hd", "md", "dd",
        "dia"
    ):
        if float(value) == 0:
            return "ندارد"

        return f"Φ{int(value)}"

    if key in (
        "bs", "ts", "tds",
        "bxs", "bys", "txs",
        "tys", "ss", "vs",
        "hs", "ms", "ds",
        "spacing"
    ):
        if float(value) == 0:
            return "ندارد"

        return f"{float(value) / 10:g} cm"

    if isinstance(value, float):

        if value.is_integer():
            return str(int(value))

        return f"{value:.2f}".rstrip("0").rstrip(".")

    return str(value)


def review_text(kind, values):

    names = {
        "iso": "⬛ پی منفرد",
        "strip": "▬ پی نواری",
        "raft": "▰ پی گسترده / رادیه",
        "column_rect": "▯ ستون مستطیلی",
        "column_round": "◯ ستون گرد",
        "beam": "📐 تیر",
        "tie": "🔗 شناژ / کلاف",
        "wall": "🧱 دیوار",
        "stair": "🪜 راه‌پله",
        "roof": "🏠 سقف",
    }

    lines = [
        "📋 <b>بررسی اطلاعات</b>",
        "",
        f"🏗️ <b>{names.get(kind, kind)}</b>",
        "",
        "<pre>",
    ]

    fields = STEPS[kind]

    for key, label, field_type in fields:

        if key not in values:
            continue

        val = review_value(
            key,
            values[key]
        )

        lines.append(
            f"{label}: {val}"
        )

    lines += [
        "</pre>",
        "",
        "اگر اطلاعات درست است، محاسبه را بزن.",
    ]

    return "\n".join(lines)


def review_keyboard(lang):

    return kb([
        [
            (TEXT[lang]["calculate"], "do_calc"),
        ],
        [
            (TEXT[lang]["edit"], "edit_restart"),
            (TEXT[lang]["cancel"], "cancel"),
        ],
        [
            (TEXT[lang]["home"], "home")
        ],
    ])


async def show_review(update, context):

    q = update.callback_query

    lang = context.user_data.get("lang", "fa")
    kind = context.user_data.get("kind")
    values = context.user_data.get("values", {})

    await q.edit_message_text(
        review_text(kind, values),
        parse_mode="HTML",
        reply_markup=review_keyboard(lang)
    )


# ============================================================
# RECEIVE MANUAL VALUE
# ============================================================

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data.get("lang", "fa")

    kind = context.user_data.get("kind")
    idx = context.user_data.get("step_index")

    # معادل‌سازی دستی
    if context.user_data.get("equiv_manual"):

        mode = context.user_data.get(
            "equiv_manual"
        )

        try:
            value = parse_number(
                update.message.text
            )

            if value <= 0:
                raise ValueError

        except Exception:

            await update.message.reply_text(
                TEXT[lang]["invalid"]
            )

            return

        if mode == "count":
            context.user_data["equiv_count"] = int(value)

        elif mode == "current_dia":
            context.user_data["equiv_current_dia"] = int(value)

        elif mode == "replacement_dia":
            context.user_data["equiv_replacement_dia"] = int(value)

        context.user_data["equiv_manual"] = None

        await continue_equiv(
            update,
            context
        )

        return

    if kind is None or idx is None:

        await update.message.reply_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

        return

    fields = STEPS[kind]

    key, label, field_type = fields[idx]

    try:

        value = parse_number(
            update.message.text
        )

        if field_type.startswith("count"):

            if value != int(value):
                raise ValueError

            value = int(value)

        elif field_type.startswith("diameter"):

            if value != int(value):
                raise ValueError

            value = int(value)

        elif field_type.startswith("spacing"):

            if value <= 0:
                raise ValueError

        elif value < 0:

            raise ValueError

    except Exception:

        await update.message.reply_text(
            TEXT[lang]["invalid"],
            reply_markup=field_keyboard(
                lang,
                field_type
            )
        )

        return

    # spacing input is cm
    if field_type.startswith("spacing"):
        value = value * 10

    context.user_data["values"][key] = value

    context.user_data["history"].append(idx)

    next_idx = idx + 1

    if next_idx < len(fields):

        context.user_data["step_index"] = next_idx

        next_key, next_label, next_type = fields[next_idx]

        await update.message.reply_text(
            prompt_text(
                lang,
                next_label,
                next_idx + 1,
                len(fields),
                next_type
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                next_type
            )
        )

        return

    context.user_data["step_index"] = None

    await update.message.reply_text(
        review_text(
            kind,
            context.user_data["values"]
        ),
        parse_mode="HTML",
        reply_markup=review_keyboard(lang)
    )


# ============================================================
# CALCULATIONS
# ============================================================

def calculate(kind, v):

    if kind == "iso":

        return isolated_footing(
            int(v["count"]),
            v["L"],
            v["W"],
            v["T"],

            v["leanL"],
            v["leanW"],
            v["leanT"],

            int(v["bd"]),
            v["bs"],

            int(v["td"])
            if v.get("td", 0) > 0
            else None,

            v.get("ts")
            if v.get("td", 0) > 0
            and v.get("ts", 0) > 0
            else None,

            DEFAULT_COVER_FOUNDATION,
            DEFAULT_LAP_PERCENT,

            v.get("pl", 0),
            v.get("pw", 0),
            v.get("ph", 0),
        )

    if kind == "strip":

        return strip_footing(
            int(v["count"]),
            v["L"],
            v["W"],
            v["T"],

            v["leanL"],
            v["leanW"],
            v["leanT"],

            int(v["ld"]),
            int(v["lc"]),

            int(v["td"]),
            v["ts"],

            int(v["tld"])
            if v.get("tld", 0) > 0
            else None,

            int(v["tlc"])
            if v.get("tlc", 0) > 0
            else None,

            int(v["ttd"])
            if v.get("ttd", 0) > 0
            else None,

            v.get("tts")
            if v.get("ttd", 0) > 0
            and v.get("tts", 0) > 0
            else None,

            DEFAULT_COVER_FOUNDATION,
            DEFAULT_LAP_PERCENT,
        )

    if kind == "raft":

        return raft_foundation(
            v["L"],
            v["W"],
            v["T"],

            v["leanL"],
            v["leanW"],
            v["leanT"],

            int(v["bxd"]),
            v["bxs"],

            int(v["byd"]),
            v["bys"],

            int(v["txd"])
            if v.get("txd", 0) > 0
            else None,

            v.get("txs")
            if v.get("txd", 0) > 0
            and v.get("txs", 0) > 0
            else None,

            int(v["tyd"])
            if v.get("tyd", 0) > 0
            else None,

            v.get("tys")
            if v.get("tyd", 0) > 0
            and v.get("tys", 0) > 0
            else None,

            DEFAULT_COVER_FOUNDATION,
            DEFAULT_LAP_PERCENT,
        )

    if kind == "column_rect":

        return column_rectangular(
            int(v["count"]),
            v["W"],
            v["D"],
            v["H"],

            int(v["ld"]),
            int(v["lc"]),

            int(v["sd"]),
            v["ss"],

            DEFAULT_COVER_MEMBER
        )

    if kind == "column_round":

        return column_round(
            int(v["count"]),
            v["D"],
            v["H"],

            int(v["ld"]),
            int(v["lc"]),

            int(v["sd"]),
            v["ss"],

            DEFAULT_COVER_MEMBER
        )

    if kind == "beam":

        return beam(
            int(v["count"]),
            v["L"],
            v["W"],
            v["H"],

            int(v["bd"]),
            int(v["bc"]),

            int(v["td"]),
            int(v["tc"]),

            int(v["sd"]),
            v["ss"],

            DEFAULT_COVER_MEMBER
        )

    if kind == "tie":

        return tie_beam(
            int(v["count"]),
            v["L"],
            v["W"],
            v["H"],

            int(v["ld"]),
            int(v["lc"]),

            int(v["sd"]),
            v["ss"],

            DEFAULT_COVER_MEMBER
        )

    if kind == "wall":

        return wall_concrete(
            v["L"],
            v["H"],
            v["T"],

            int(v["vd"]),
            v["vs"],

            int(v["hd"]),
            v["hs"],

            DEFAULT_COVER_MEMBER
        )

    if kind == "stair":

        return stair_slab(
            v["L"],
            v["W"],
            v["T"],

            int(v["md"]),
            v["ms"],

            int(v["dd"]),
            v["ds"],

            int(v["steps"]),
            v["riser"],
            v["tread"]
        )

    raise ValueError(
        f"Unknown calculation type: {kind}"
    )


# ============================================================
# RESULT TEXT
# ============================================================

def summary_text(kind, result, lang):

    names = {
        "iso": "⬛ پی منفرد",
        "strip": "▬ پی نواری",
        "raft": "▰ پی گسترده / رادیه",
        "column_rect": "▯ ستون مستطیلی",
        "column_round": "◯ ستون گرد",
        "beam": "📐 تیر",
        "tie": "🔗 شناژ / کلاف",
        "wall": "🧱 دیوار",
        "stair": "🪜 راه‌پله",
        "roof": "🏠 سقف",
    }

    name = names.get(kind, kind)

    concrete = float(
        result.get(
            "total_concrete_m3",
            result.get("concrete_m3", 0)
        ) or 0
    )

    rebar = float(
        result.get(
            "total_rebar_kg",
            0
        ) or 0
    )

    lines = [
        "🏗️ <b>نتیجه محاسبه</b>",
        "",
        f"🏷️ <b>{name}</b>",
        "",
        "<pre>",
        f"بتن کل:       {concrete:.2f} m³",
        f"میلگرد کل:    {rebar:.1f} kg",
    ]

    if kind == "iso":

        lean = float(
            result.get(
                "lean_concrete_m3",
                0
            ) or 0
        )

        footing = float(
            result.get(
                "footing_concrete_m3",
                0
            ) or 0
        )

        pedestal = float(
            result.get(
                "pedestal_concrete_m3",
                0
            ) or 0
        )

        lines.extend([
            "",
            f"بتن مگر:      {lean:.2f} m³",
            f"بتن پی:       {footing:.2f} m³",
            f"بتن پدستال:   {pedestal:.2f} m³",
        ])

    lines.extend([
        "</pre>",
        "",
        "🔎 جزئیات میلگرد و Cut List را ببین.",
    ])

    return "\n".join(lines)


# ============================================================
# REBAR DETAILS
# ============================================================

def rebar_text(details):

    if not details:
        return (
            "🔩 <b>جزئیات میلگرد</b>\n\n"
            "میلگردی ثبت نشده است."
        )

    chunks = [
        "🔩 <b>جزئیات میلگرد</b>",
        ""
    ]

    total_weight = 0.0
    total_bars = 0

    for index, x in enumerate(details, 1):

        dia = int(
            x.get(
                "diameter_mm",
                0
            )
        )

        pieces = int(
            x.get(
                "piece_count",
                0
            )
        )

        length = float(
            x.get(
                "length_m",
                0
            ) or 0
        )

        weight = float(
            x.get(
                "weight_kg",
                0
            ) or 0
        )

        bars = int(
            x.get(
                "bars_12m",
                0
            )
        )

        desc = x.get(
            "description",
            ""
        )

        total_weight += weight
        total_bars += bars

        chunks.extend([
            "━━━━━━━━━━━━━━━━",
            f"میلگرد {index}",
            "<pre>",
            f"قطر:            Φ{dia}",
            f"تعداد قطعات:    {pieces} عدد",
            f"طول کل:         {length:.2f} m",
            f"وزن:            {weight:.1f} kg",
            f"شاخه ۱۲ متری:   {bars} عدد",
            "</pre>",
        ])

        if desc:
            chunks.append(
                f"📌 {escape(desc)}"
            )

    chunks.extend([
        "━━━━━━━━━━━━━━━━",
        "<pre>",
        f"کل وزن:         {total_weight:.1f} kg",
        f"کل شاخه:        {total_bars} عدد",
        "</pre>",
    ])

    return "\n".join(chunks)


# ============================================================
# CUT LIST
# ============================================================

def cut_text(details):

    if not details:
        return (
            "✂️ <b>Cut List</b>\n\n"
            "موردی وجود ندارد."
        )

    chunks = [
        "✂️ <b>Cut List</b>",
        ""
    ]

    for x in details:

        dia = int(
            x.get(
                "diameter_mm",
                0
            )
        )

        plans = x.get(
            "cut_plan",
            []
        )

        bars = len(plans)

        chunks.extend([
            "━━━━━━━━━━━━━━━━",
            f"🔩 Φ{dia}",
            f"شاخه ۱۲ متری: {bars} عدد",
            ""
        ])

        for i, plan in enumerate(
            plans,
            1
        ):

            pieces = " + ".join(
                f"{float(v):.2f}"
                for v in plan.get(
                    "pieces",
                    []
                )
            )

            used = sum(
                float(v)
                for v in plan.get(
                    "pieces",
                    []
                )
            )

            # طبق درخواست: پرت مستقیماً از 12-used
            waste = max(
                12.0 - used,
                0
            )

            chunks.extend([
                "<pre>",
                f"قطعه {i}",
                f"برش:   {pieces}",
                f"مصرف:  {used:.2f} m",
                f"پرت:   {waste:.2f} m",
                "</pre>",
            ])

            if i >= 15:

                if len(plans) > 15:
                    chunks.append(
                        f"… و {len(plans) - 15} شاخه دیگر"
                    )

                break

    return "\n".join(chunks)


# ============================================================
# EQUIVALENCY
# ============================================================

def equivalency_keyboard_diameter(prefix):

    rows = []

    values = [
        (
            f"Φ{x}",
            f"{prefix}_{x}"
        )
        for x in DIAMETERS
    ]

    rows.extend(
        chunk_buttons(
            values,
            4
        )
    )

    rows.append([
        ("✏️ عدد دلخواه", f"{prefix}_custom")
    ])

    rows.append([
        ("🏠 صفحه اصلی", "home")
    ])

    return kb(rows)


def equiv_area(count, diameter):

    return (
        float(count)
        * math.pi
        * diameter
        * diameter
        / 4.0
    )


def equiv_result(
    count,
    current_dia,
    replacement_dia
):

    current_area = equiv_area(
        count,
        current_dia
    )

    one_replacement_area = equiv_area(
        1,
        replacement_dia
    )

    required_count = math.ceil(
        current_area /
        one_replacement_area
    )

    provided_area = equiv_area(
        required_count,
        replacement_dia
    )

    difference = (
        provided_area -
        current_area
    )

    if difference >= -0.000001:
        status = "🟢 از نظر سطح مقطع، معادل یا بیشتر است."
    else:
        status = "🔴 از نظر سطح مقطع، معادل نیست."

    return (
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "<pre>"
        f"میلگرد فعلی:\n"
        f"تعداد:        {count} عدد\n"
        f"قطر:          Φ{current_dia}\n"
        f"سطح مقطع:     {current_area:.1f} mm²\n\n"
        f"قطر جایگزین:  Φ{replacement_dia}\n"
        f"تعداد لازم:   {required_count} عدد\n"
        f"سطح مقطع:     {provided_area:.1f} mm²\n"
        "</pre>\n"
        f"{status}\n\n"
        "📌 این نتیجه فقط کنترل سطح مقطع است؛ "
        "کنترل فاصله، حداقل/حداکثر آرماتور، مهاری و وصله "
        "باید در طراحی عضو و طبق استاندارد انتخاب‌شده بررسی شود."
    )


async def start_equiv(update, context):

    q = update.callback_query
    lang = context.user_data.get("lang", "fa")

    context.user_data["equiv_count"] = None
    context.user_data["equiv_current_dia"] = None
    context.user_data["equiv_replacement_dia"] = None
    context.user_data["equiv_manual"] = None

    await q.edit_message_text(
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "تعداد میلگرد فعلی را انتخاب کن:",
        parse_mode="HTML",
        reply_markup=kb(
            chunk_buttons(
                [
                    (str(x), f"eqcount_{x}")
                    for x in COUNT_VALUES
                ],
                5
            )
            + [
                [(TEXT[lang]["custom"], "eqcount_custom")],
                [(TEXT[lang]["home"], "home")]
            ]
        )
    )


async def continue_equiv(update, context):

    q = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    count = context.user_data.get(
        "equiv_count"
    )

    current = context.user_data.get(
        "equiv_current_dia"
    )

    replacement = context.user_data.get(
        "equiv_replacement_dia"
    )

    if count is None:

        await q.edit_message_text(
            "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
            "تعداد میلگرد فعلی را انتخاب کن:",
            parse_mode="HTML",
            reply_markup=kb(
                chunk_buttons(
                    [
                        (
                            str(x),
                            f"eqcount_{x}"
                        )
                        for x in COUNT_VALUES
                    ],
                    5
                )
                + [
                    [
                        (
                            TEXT[lang]["custom"],
                            "eqcount_custom"
                        )
                    ],
                    [
                        (
                            TEXT[lang]["home"],
                            "home"
                        )
                    ]
                ]
            )
        )

        return

    if current is None:

        await q.edit_message_text(
            "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
            f"تعداد فعلی: <b>{count}</b>\n\n"
            "قطر میلگرد فعلی را انتخاب کن:",
            parse_mode="HTML",
            reply_markup=equivalency_keyboard_diameter(
                "eqcur"
            )
        )

        return

    if replacement is None:

        await q.edit_message_text(
            "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
            f"میلگرد فعلی: <b>{count}Φ{current}</b>\n\n"
            "قطر میلگرد جایگزین را انتخاب کن:",
            parse_mode="HTML",
            reply_markup=equivalency_keyboard_diameter(
                "eqrep"
            )
        )

        return

    await q.edit_message_text(
        equiv_result(
            count,
            current,
            replacement
        ),
        parse_mode="HTML",
        reply_markup=kb([
            [
                ("🔄 معادل‌سازی جدید", "equiv"),
            ],
            [
                (TEXT[lang]["home"], "home")
            ]
        ])
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def buttons(update, context):

    q = update.callback_query

    await q.answer()

    data = q.data

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    # --------------------------------------------------------
    # Language
    # --------------------------------------------------------

    if data.startswith("lang_"):
        return await choose_language(
            update,
            context
        )

    # --------------------------------------------------------
    # Standard
    # --------------------------------------------------------

    if data.startswith("std_"):

        standard = data[4:]

        context.user_data[
            "standard"
        ] = standard

        await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

        return

    # --------------------------------------------------------
    # Home
    # --------------------------------------------------------

    if data == "home":

        old_lang = lang
        standard = context.user_data.get(
            "standard",
            "iran"
        )

        context.user_data.clear()

        context.user_data["lang"] = old_lang
        context.user_data["standard"] = standard

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # Cancel
    # --------------------------------------------------------

    if data == "cancel":

        standard = context.user_data.get(
            "standard",
            "iran"
        )

        context.user_data.clear()

        context.user_data["lang"] = lang
        context.user_data["standard"] = standard

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # Previous
    # --------------------------------------------------------

    if data == "prev":

        kind = context.user_data.get(
            "kind"
        )

        idx = context.user_data.get(
            "step_index"
        )

        if not kind or idx is None:

            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(lang)
            )

        if idx == 0:

            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(lang)
            )

        previous = idx - 1

        key, label, field_type = STEPS[
            kind
        ][previous]

        context.user_data[
            "values"
        ].pop(
            key,
            None
        )

        context.user_data[
            "step_index"
        ] = previous

        if context.user_data.get(
            "history"
        ):
            context.user_data[
                "history"
            ].pop()

        await q.edit_message_text(
            prompt_text(
                lang,
                label,
                previous + 1,
                len(STEPS[kind]),
                field_type
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                field_type
            )
        )

        return

    # --------------------------------------------------------
    # Main sections
    # --------------------------------------------------------

    if data == "foundation":

        return await q.edit_message_text(
            "🧱 <b>فونداسیون</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("⬛ پی منفرد", "foundation_iso")
                ],
                [
                    ("▬ پی نواری", "foundation_strip")
                ],
                [
                    ("▰ پی گسترده / رادیه", "foundation_raft")
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    if data == "columns":

        return await q.edit_message_text(
            "🏛️ <b>ستون‌ها</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        "▯ ستون مربعی / مستطیلی",
                        "column_rect"
                    )
                ],
                [
                    (
                        "◯ ستون گرد",
                        "column_round"
                    )
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    if data == "beams":

        return await q.edit_message_text(
            "📐 <b>تیرها</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("📐 تیر اصلی", "beam_main")
                ],
                [
                    ("📏 تیر فرعی", "beam_secondary")
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    if data == "roofs":

        return await q.edit_message_text(
            "🏠 <b>سقف‌ها</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("🟦 تیرچه یونولیتی", "roof_foam")
                ],
                [
                    ("🟫 تیرچه سفالی", "roof_clay")
                ],
                [
                    ("🟪 تیرچه دوبل", "roof_double")
                ],
                [
                    ("🔩 کرومیت", "roof_kromit")
                ],
                [
                    ("🏗️ کامپوزیت", "roof_composite")
                ],
                [
                    ("🔩 عرشه فولادی", "roof_steeldeck")
                ],
                [
                    ("⬜ دال بتنی", "roof_slab")
                ],
                [
                    ("🔳 وافل", "roof_waffle")
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    if data == "ties":

        return await q.edit_message_text(
            "🔗 <b>شناژ و کلاف</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("🔗 شناژ", "tie_beam")
                ],
                [
                    ("⛓️ کلاف", "tie_cowl")
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    if data == "walls":

        return await q.edit_message_text(
            "🧱 <b>دیوارها</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("🏢 دیوار برشی", "wall_shear")
                ],
                [
                    ("🧱 دیوار حائل", "wall_retaining")
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    # --------------------------------------------------------
    # Language menu
    # --------------------------------------------------------

    if data == "language":

        return await q.edit_message_text(
            "🌐 <b>انتخاب زبان</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("🇮🇷 فارسی", "lang_fa"),
                    ("🇸🇦 العربية", "lang_ar"),
                ],
                [
                    ("🇬🇧 English", "lang_en"),
                    ("🇨🇳 中文", "lang_zh"),
                ],
                [
                    (TEXT[lang]["back"], "home")
                ]
            ])
        )

    # --------------------------------------------------------
    # Settings
    # --------------------------------------------------------

    if data == "settings":

        standard = context.user_data.get(
            "standard",
            "iran"
        )

        standard_name = {
            "iran": "🇮🇷 مبحث ۹ ایران",
            "aci": "🇺🇸 ACI 318",
            "ec2": "🇪🇺 Eurocode 2",
        }.get(
            standard,
            "🇮🇷 مبحث ۹ ایران"
        )

        return await q.edit_message_text(
            "⚙️ <b>تنظیمات</b>\n\n"
            f"استاندارد فعلی:\n<b>{standard_name}</b>\n\n"
            "برای تغییر استاندارد انتخاب کن:",
            parse_mode="HTML",
            reply_markup=standard_keyboard(lang)
        )

    # --------------------------------------------------------
    # Help
    # --------------------------------------------------------

    if data == "help":

        return await q.edit_message_text(
            "ℹ️ <b>راهنما</b>\n\n"
            "برای بیشتر ورودی‌ها می‌توانی مستقیماً از "
            "دکمه‌ها استفاده کنی.\n\n"
            "📐 ابعاد بر حسب متر هستند.\n"
            "🔩 قطر میلگرد بر حسب میلی‌متر است.\n"
            "📏 فاصله میلگرد بر حسب سانتی‌متر است.\n\n"
            "نتایج این ربات برآوردی هستند و جایگزین "
            "نقشه و محاسبات مهندس محاسب نیستند.",
            parse_mode="HTML",
            reply_markup=back_home_kb(lang)
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    if data == "summary":

        return await q.edit_message_text(
            "📊 <b>خلاصه پروژه</b>\n\n"
            "بخش خلاصه پروژه در مرحله بعد به "
            "جمع‌آوری نتایج تمام اعضای پروژه متصل می‌شود.",
            parse_mode="HTML",
            reply_markup=back_home_kb(lang)
        )

    # --------------------------------------------------------
    # Equivalency
    # --------------------------------------------------------

    if data == "equiv":

        return await start_equiv(
            update,
            context
        )

    # --------------------------------------------------------
    # Equivalency count
    # --------------------------------------------------------

    if data.startswith("eqcount_"):

        raw = data.split("_", 1)[1]

        if raw == "custom":

            context.user_data[
                "equiv_manual"
            ] = "count"

            return await q.edit_message_text(
                "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
                "تعداد میلگرد فعلی را وارد کن:",
                parse_mode="HTML",
                reply_markup=back_home_kb(
                    lang,
                    "equiv"
                )
            )

        context.user_data[
            "equiv_count"
        ] = int(raw)

        return await continue_equiv(
            update,
            context
        )

    # --------------------------------------------------------
    # Equivalency current diameter
    # --------------------------------------------------------

    if data.startswith("eqcur_"):

        raw = data.split("_", 1)[1]

        if raw == "custom":

            context.user_data[
                "equiv_manual"
            ] = "current_dia"

            return await q.edit_message_text(
                "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
                "قطر میلگرد فعلی را وارد کن:\n"
                "مثلاً 20",
                parse_mode="HTML",
                reply_markup=back_home_kb(
                    lang,
                    "equiv"
                )
            )

        context.user_data[
            "equiv_current_dia"
        ] = int(raw)

        return await continue_equiv(
            update,
            context
        )

    # --------------------------------------------------------
    # Equivalency replacement diameter
    # --------------------------------------------------------

    if data.startswith("eqrep_"):

        raw = data.split("_", 1)[1]

        if raw == "custom":

            context.user_data[
                "equiv_manual"
            ] = "replacement_dia"

            return await q.edit_message_text(
                "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
                "قطر میلگرد جایگزین را وارد کن:\n"
                "مثلاً 25",
                parse_mode="HTML",
                reply_markup=back_home_kb(
                    lang,
                    "equiv"
                )
            )

        context.user_data[
            "equiv_replacement_dia"
        ] = int(raw)

        return await continue_equiv(
            update,
            context
        )

    # --------------------------------------------------------
    # Wizard value buttons
    # --------------------------------------------------------

    if data.startswith("val_"):

        raw = data[4:]

        try:
            value = parse_number(raw)
        except Exception:

            return await q.edit_message_text(
                TEXT[lang]["invalid"],
                reply_markup=main_menu(lang)
            )

        return await save_field(
            update,
            context,
            value
        )

    # --------------------------------------------------------
    # Custom field
    # --------------------------------------------------------

    if data == "custom":

        kind = context.user_data.get(
            "kind"
        )

        idx = context.user_data.get(
            "step_index"
        )

        if kind is None or idx is None:
            return

        key, label, field_type = STEPS[
            kind
        ][idx]

        context.user_data[
            "custom_mode"
        ] = True

        await q.edit_message_text(
            f"✏️ <b>{escape(label)}</b>\n\n"
            "عدد را وارد کن.\n"
            "فقط خود عدد را بنویس.",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        "⬅️ مرحله قبل",
                        "prev"
                    ),
                    (
                        TEXT[lang]["cancel"],
                        "cancel"
                    )
                ]
            ])
        )

        return

    # --------------------------------------------------------
    # Edit
    # --------------------------------------------------------

    if data == "edit_restart":

        kind = context.user_data.get(
            "kind"
        )

        if kind:

            return await begin_wizard(
                update,
                context,
                kind
            )

    # --------------------------------------------------------
    # Calculate
    # --------------------------------------------------------

    if data == "do_calc":

        kind = context.user_data.get(
            "kind"
        )

        values = context.user_data.get(
            "values",
            {}
        )

        try:

            result = calculate(
                kind,
                values
            )

            context.user_data[
                "result"
            ] = result

            await q.edit_message_text(
                summary_text(
                    kind,
                    result,
                    lang
                ),
                parse_mode="HTML",
                reply_markup=result_keyboard(
                    lang
                )
            )

        except Exception as exc:

            logger.exception(
                "Calculation failed"
            )

            await q.edit_message_text(
                TEXT[lang]["calc_error"].format(
                    escape(str(exc))
                ),
                parse_mode="HTML",
                reply_markup=main_menu(lang)
            )

        return

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    if data == "show_rebar":

        return await q.edit_message_text(
            rebar_text(
                context.user_data
                .get("result", {})
                .get("rebar_details", [])
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("✂️ Cut List", "show_cut"),
                    ("⬅️ نتیجه", "back_result"),
                ],
                [
                    (TEXT[lang]["home"], "home")
                ]
            ])
        )

    if data == "show_cut":

        return await q.edit_message_text(
            cut_text(
                context.user_data
                .get("result", {})
                .get("rebar_details", [])
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("🔩 میلگرد", "show_rebar"),
                    ("⬅️ نتیجه", "back_result"),
                ],
                [
                    (TEXT[lang]["home"], "home")
                ]
            ])
        )

    if data == "back_result":

        return await q.edit_message_text(
            summary_text(
                context.user_data.get(
                    "kind",
                    ""
                ),
                context.user_data.get(
                    "result",
                    {}
                ),
                lang
            ),
            parse_mode="HTML",
            reply_markup=result_keyboard(
                lang
            )
        )

    if data == "new_member":

        standard = context.user_data.get(
            "standard",
            "iran"
        )

        context.user_data.clear()

        context.user_data["lang"] = lang
        context.user_data["standard"] = standard

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # Member mapping
    # --------------------------------------------------------

    if data == "stairs":

        return await begin_wizard(
            update,
            context,
            "stair"
        )

    mapping = {
        "foundation_iso": "iso",
        "foundation_strip": "strip",
        "foundation_raft": "raft",

        "column_rect": "column_rect",
        "column_round": "column_round",

        "beam_main": "beam",
        "beam_secondary": "beam",

        "tie_beam": "tie",
        "tie_cowl": "tie",

        "wall_shear": "wall",
        "wall_retaining": "wall",
    }

    if data in mapping:

        return await begin_wizard(
            update,
            context,
            mapping[data]
        )

    # --------------------------------------------------------
    # Roof
    # --------------------------------------------------------

    if data.startswith("roof_"):

        roof_type = data[5:]

        context.user_data[
            "kind"
        ] = "roof"

        context.user_data[
            "step_index"
        ] = 0

        context.user_data[
            "values"
        ] = {
            "coeff": ROOF_COEFF[
                roof_type
            ]
        }

        context.user_data[
            "history"
        ] = []

        context.user_data[
            "roof_name"
        ] = ROOF_NAMES[
            roof_type
        ]

        fields = STEPS[
            "roof"
        ]

        key, label, field_type = fields[0]

        return await q.edit_message_text(
            f"🏠 <b>{ROOF_NAMES[roof_type]}</b>\n\n"
            + prompt_text(
                lang,
                label,
                1,
                len(fields),
                field_type
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                field_type
            )
        )

    # fallback

    await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang)
    )


# ============================================================
# RESULT KEYBOARD
# ============================================================

def result_keyboard(lang):

    return kb([
        [
            ("🔩 جزئیات میلگرد", "show_rebar"),
            ("✂️ Cut List", "show_cut"),
        ],
        [
            ("➕ محاسبه جدید", "new_member"),
        ],
        [
            (TEXT[lang]["home"], "home")
        ]
    ])


# ============================================================
# ERROR
# ============================================================

async def error_handler(update, context):

    logger.exception(
        "Unhandled bot error",
        exc_info=context.error
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set"
        )

    if not RENDER_EXTERNAL_URL:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL environment variable is not set"
        )

    webhook_url = (
        f"{RENDER_EXTERNAL_URL}/telegram"
    )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "======================================"
    )
    print(
        "Concrete Structure Bot"
    )
    print(
        "Render Webhook Mode"
    )
    print(
        f"Port: {PORT}"
    )
    print(
        f"Webhook: {webhook_url}"
    )
    print(
        "Bot started successfully."
    )
    print(
        "======================================"
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
