# bot.py
# -*- coding: utf-8 -*-

import os
import logging
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
    equivalent_rebar_count,
    optimize_12m_bars,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get(
    "RENDER_EXTERNAL_URL", ""
).rstrip("/")


# =========================================================
# LANGUAGE / STANDARD
# =========================================================

TEXT = {
    "fa": {
        "language": "🌐 زبان را انتخاب کنید:",
        "standard": "📚 استاندارد محاسبات را انتخاب کنید:",
        "welcome": "🏗️ <b>اسکلت بتنی</b>\n\nعضو موردنظر را انتخاب کنید:",
        "project": "🏗️ <b>مشخصات پروژه</b>",
        "invalid": "❌ مقدار واردشده معتبر نیست. دوباره وارد کنید.",
        "calc_error": "❌ خطا در محاسبه:\n<code>{}</code>",
        "back": "🔙 بازگشت",
        "home": "🏠 صفحه اصلی",
        "cancel": "❌ لغو",
        "manual": "✏️ ورود دستی",
        "confirm": "📋 بررسی اطلاعات",
        "calculate": "✅ محاسبه",
        "edit": "✏️ ویرایش",
        "new": "➕ محاسبه جدید",
        "rebar": "🔩 جزئیات میلگرد",
        "cut": "✂️ Cut List",
        "language": "🌐 زبان",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "summary": "📊 خلاصه پروژه",
        "equivalent": "🔄 معادل‌سازی میلگرد",
        "prev": "⬅️ مرحله قبل",
        "custom": "✏️ عدد دلخواه",
    },
    "en": {
        "language": "🌐 Choose language:",
        "standard": "📚 Choose calculation standard:",
        "welcome": "🏗️ <b>Concrete Frame</b>\n\nChoose a member:",
        "project": "🏗️ <b>Project Information</b>",
        "invalid": "❌ Invalid value. Try again.",
        "calc_error": "❌ Calculation error:\n<code>{}</code>",
        "back": "🔙 Back",
        "home": "🏠 Main Menu",
        "cancel": "❌ Cancel",
        "manual": "✏️ Enter manually",
        "confirm": "📋 Review information",
        "calculate": "✅ Calculate",
        "edit": "✏️ Edit",
        "new": "➕ New calculation",
        "rebar": "🔩 Rebar details",
        "cut": "✂️ Cut List",
        "language": "🌐 Language",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "summary": "📊 Project summary",
        "equivalent": "🔄 Rebar equivalency",
        "prev": "⬅️ Previous",
        "custom": "✏️ Custom value",
    },
    "ar": {
        "language": "🌐 اختر اللغة:",
        "standard": "📚 اختر معيار الحساب:",
        "welcome": "🏗️ <b>الهيكل الخرساني</b>\n\nاختر العنصر:",
        "project": "🏗️ <b>بيانات المشروع</b>",
        "invalid": "❌ القيمة غير صحيحة. حاول مرة أخرى.",
        "calc_error": "❌ خطأ في الحساب:\n<code>{}</code>",
        "back": "🔙 رجوع",
        "home": "🏠 الرئيسية",
        "cancel": "❌ إلغاء",
        "manual": "✏️ إدخال يدوي",
        "confirm": "📋 مراجعة البيانات",
        "calculate": "✅ حساب",
        "edit": "✏️ تعديل",
        "new": "➕ حساب جديد",
        "rebar": "🔩 تفاصيل التسليح",
        "cut": "✂️ Cut List",
        "language": "🌐 اللغة",
        "settings": "⚙️ الإعدادات",
        "help": "ℹ️ مساعدة",
        "summary": "📊 ملخص المشروع",
        "equivalent": "🔄 معادلة التسليح",
        "prev": "⬅️ السابق",
        "custom": "✏️ قيمة مخصصة",
    },
    "zh": {
        "language": "🌐 请选择语言：",
        "standard": "📚 请选择计算标准：",
        "welcome": "🏗️ <b>混凝土结构</b>\n\n请选择构件：",
        "project": "🏗️ <b>项目参数</b>",
        "invalid": "❌ 输入无效，请重新输入。",
        "calc_error": "❌ 计算错误：\n<code>{}</code>",
        "back": "🔙 返回",
        "home": "🏠 主菜单",
        "cancel": "❌ 取消",
        "manual": "✏️ 手动输入",
        "confirm": "📋 检查信息",
        "calculate": "✅ 计算",
        "edit": "✏️ 编辑",
        "new": "➕ 新计算",
        "rebar": "🔩 钢筋详情",
        "cut": "✂️ Cut List",
        "language": "🌐 语言",
        "settings": "⚙️ 设置",
        "help": "ℹ️ 帮助",
        "summary": "📊 项目汇总",
        "equivalent": "🔄 钢筋替换",
        "prev": "⬅️ 上一步",
        "custom": "✏️ 自定义数值",
    },
}


STANDARDS = {
    "iran": {
        "fa": "🇮🇷 مبحث ۹ ایران",
        "en": "🇮🇷 Iran – Mبحث ۹",
        "ar": "🇮🇷 كود إيران – مبحث 9",
        "zh": "🇮🇷 伊朗规范 – Mبحث 9",
    },
    "aci": {
        "fa": "🇺🇸 ACI 318",
        "en": "🇺🇸 ACI 318",
        "ar": "🇺🇸 ACI 318",
        "zh": "🇺🇸 ACI 318",
    },
    "eurocode": {
        "fa": "🇪🇺 Eurocode 2",
        "en": "🇪🇺 Eurocode 2",
        "ar": "🇪🇺 Eurocode 2",
        "zh": "🇪🇺 Eurocode 2",
    },
}


# =========================================================
# ROOF
# =========================================================

ROOF_NAMES = {
    "foam": {
        "fa": "🟦 تیرچه یونولیتی",
        "en": "🟦 EPS Joist",
        "ar": "🟦 بلوك بوليسترين",
        "zh": "🟦 EPS 楼板",
    },
    "clay": {
        "fa": "🟫 تیرچه سفالی",
        "en": "🟫 Clay Block Joist",
        "ar": "🟫 بلوك فخاري",
        "zh": "🟫 陶土楼板",
    },
    "double": {
        "fa": "🟪 تیرچه دوبل",
        "en": "🟪 Double Joist",
        "ar": "🟪 جويست مزدوج",
        "zh": "🟪 双梁楼板",
    },
    "kromit": {
        "fa": "🔩 کرومیت",
        "en": "🔩 Kromit",
        "ar": "🔩 كروميت",
        "zh": "🔩 Kromit",
    },
    "composite": {
        "fa": "🏗️ کامپوزیت",
        "en": "🏗️ Composite",
        "ar": "🏗️ مركب",
        "zh": "🏗️ 组合楼板",
    },
    "steeldeck": {
        "fa": "🔩 عرشه فولادی",
        "en": "🔩 Steel Deck",
        "ar": "🔩 Deck فولاذي",
        "zh": "🔩 钢承板",
    },
    "slab": {
        "fa": "⬜ دال بتنی",
        "en": "⬜ Concrete Slab",
        "ar": "⬜ بلاطة خرسانية",
        "zh": "⬜ 混凝土板",
    },
    "waffle": {
        "fa": "🔳 وافل",
        "en": "🔳 Waffle",
        "ar": "🔳 وافل",
        "zh": "🔳 华夫板",
    },
}


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


# =========================================================
# MEMBER STEPS
# =========================================================

STEPS = {
    "iso": [
        ("count", "تعداد پی", "int"),
        ("L", "طول پی", "float"),
        ("W", "عرض پی", "float"),
        ("T", "ضخامت پی", "float"),
        ("leanL", "طول بتن مگر", "float"),
        ("leanW", "عرض بتن مگر", "float"),
        ("leanT", "ضخامت بتن مگر", "float"),
        ("bd", "قطر میلگرد پایین", "int"),
        ("bs", "فاصله میلگرد پایین", "int"),
        ("td", "قطر میلگرد بالا", "int"),
        ("ts", "فاصله میلگرد بالا", "int"),
        ("pl", "طول پدستال", "float"),
        ("pw", "عرض پدستال", "float"),
        ("ph", "ارتفاع پدستال", "float"),
    ],

    "strip": [
        ("count", "تعداد نوار", "int"),
        ("L", "طول نوار", "float"),
        ("W", "عرض پی", "float"),
        ("T", "ضخامت پی", "float"),
        ("leanL", "طول بتن مگر", "float"),
        ("leanW", "عرض بتن مگر", "float"),
        ("leanT", "ضخامت بتن مگر", "float"),
        ("ld", "قطر طولی پایین", "int"),
        ("lc", "تعداد طولی پایین", "int"),
        ("td", "قطر عرضی پایین", "int"),
        ("ts", "فاصله عرضی پایین", "int"),
        ("tld", "قطر طولی بالا", "int"),
        ("tlc", "تعداد طولی بالا", "int"),
        ("ttd", "قطر عرضی بالا", "int"),
        ("tts", "فاصله عرضی بالا", "int"),
    ],

    "raft": [
        ("L", "طول رادیه", "float"),
        ("W", "عرض رادیه", "float"),
        ("T", "ضخامت رادیه", "float"),
        ("leanL", "طول بتن مگر", "float"),
        ("leanW", "عرض بتن مگر", "float"),
        ("leanT", "ضخامت بتن مگر", "float"),
        ("bxd", "قطر X پایین", "int"),
        ("bxs", "فاصله X پایین", "int"),
        ("byd", "قطر Y پایین", "int"),
        ("bys", "فاصله Y پایین", "int"),
        ("txd", "قطر X بالا", "int"),
        ("txs", "فاصله X بالا", "int"),
        ("tyd", "قطر Y بالا", "int"),
        ("tys", "فاصله Y بالا", "int"),
    ],

    "column_rect": [
        ("count", "تعداد ستون", "int"),
        ("W", "عرض ستون", "float"),
        ("D", "عمق ستون", "float"),
        ("H", "ارتفاع ستون", "float"),
        ("ld", "قطر میلگرد طولی", "int"),
        ("lc", "تعداد میلگرد طولی هر ستون", "int"),
        ("sd", "قطر خاموت", "int"),
        ("ss", "فاصله خاموت", "int"),
    ],

    "column_round": [
        ("count", "تعداد ستون گرد", "int"),
        ("D", "قطر ستون", "float"),
        ("H", "ارتفاع ستون", "float"),
        ("ld", "قطر میلگرد طولی", "int"),
        ("lc", "تعداد میلگرد طولی هر ستون", "int"),
        ("sd", "قطر خاموت", "int"),
        ("ss", "فاصله خاموت", "int"),
    ],

    "beam": [
        ("count", "تعداد تیر", "int"),
        ("L", "طول تیر", "float"),
        ("W", "عرض تیر", "float"),
        ("H", "ارتفاع تیر", "float"),
        ("bd", "قطر میلگرد پایین", "int"),
        ("bc", "تعداد میلگرد پایین", "int"),
        ("td", "قطر میلگرد بالا", "int"),
        ("tc", "تعداد میلگرد بالا", "int"),
        ("sd", "قطر خاموت", "int"),
        ("ss", "فاصله خاموت", "int"),
    ],

    "tie": [
        ("count", "تعداد شناژ/کلاف", "int"),
        ("L", "طول", "float"),
        ("W", "عرض", "float"),
        ("H", "ارتفاع", "float"),
        ("ld", "قطر میلگرد طولی", "int"),
        ("lc", "تعداد میلگرد طولی", "int"),
        ("sd", "قطر خاموت", "int"),
        ("ss", "فاصله خاموت", "int"),
    ],

    "wall": [
        ("L", "طول دیوار", "float"),
        ("H", "ارتفاع دیوار", "float"),
        ("T", "ضخامت دیوار", "float"),
        ("vd", "قطر میلگرد قائم", "int"),
        ("vs", "فاصله میلگرد قائم", "int"),
        ("hd", "قطر میلگرد افقی", "int"),
        ("hs", "فاصله میلگرد افقی", "int"),
    ],

    "stair": [
        ("L", "طول شیب/دال", "float"),
        ("W", "عرض راه‌پله", "float"),
        ("T", "ضخامت دال", "float"),
        ("md", "قطر میلگرد اصلی", "int"),
        ("ms", "فاصله میلگرد اصلی", "int"),
        ("dd", "قطر میلگرد توزیعی", "int"),
        ("ds", "فاصله میلگرد توزیعی", "int"),
        ("steps", "تعداد پله", "int"),
        ("riser", "ارتفاع رایزر", "float"),
        ("tread", "کف پله", "float"),
    ],

    "roof": [
        ("L", "طول سقف", "float"),
        ("W", "عرض سقف", "float"),
        ("T", "ضخامت سقف", "float"),
        ("dia", "قطر شبکه حرارتی", "int"),
        ("spacing", "فاصله شبکه حرارتی", "int"),
    ],
}


# =========================================================
# KEYBOARDS
# =========================================================

def kb(rows):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text,
                callback_data=data
            )
            for text, data in row
        ]
        for row in rows
    ])


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
                ("📊 خلاصه پروژه", "summary"),
            ],
            [
                ("🔄 معادل‌سازی میلگرد", "equivalent"),
            ],
            [
                ("🌐 زبان", "language"),
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
            ("📊 Summary", "summary"),
        ],
        [
            ("🔄 Rebar equivalency", "equivalent"),
        ],
        [
            (TEXT[lang]["language"], "language"),
            (TEXT[lang]["settings"], "settings"),
        ],
        [
            (TEXT[lang]["help"], "help"),
        ],
    ])


def standard_kb(lang):
    return kb([
        [
            (
                STANDARDS["iran"][lang],
                "standard_iran"
            )
        ],
        [
            (
                STANDARDS["aci"][lang],
                "standard_aci"
            )
        ],
        [
            (
                STANDARDS["eurocode"][lang],
                "standard_eurocode"
            )
        ],
    ])


def language_kb():
    return kb([
        [
            ("🇮🇷 فارسی", "lang_fa"),
            ("🇸🇦 العربية", "lang_ar"),
        ],
        [
            ("🇬🇧 English", "lang_en"),
            ("🇨🇳 中文", "lang_zh"),
        ],
    ])


def back_kb(lang, callback="home"):
    return kb([
        [
            (TEXT[lang]["back"], callback),
            (TEXT[lang]["home"], "home"),
        ]
    ])


def step_kb(lang):
    return kb([
        [
            (TEXT[lang]["prev"], "prev"),
            (TEXT[lang]["cancel"], "cancel"),
        ],
        [
            (TEXT[lang]["home"], "home"),
        ],
    ])


def result_kb(lang):
    return kb([
        [
            (TEXT[lang]["rebar"], "show_rebar"),
            (TEXT[lang]["cut"], "show_cut"),
        ],
        [
            (TEXT[lang]["new"], "new_member"),
        ],
        [
            (TEXT[lang]["home"], "home"),
        ],
    ])


def section_kb(lang, items, parent="home"):
    rows = []

    for text, data in items:
        rows.append([(text, data)])

    rows.append([
        (TEXT[lang]["back"], parent)
    ])

    return kb(rows)


# =========================================================
# NUMBER BUTTONS
# =========================================================

def diameter_kb(lang, prefix="dia"):
    values = [
        8, 10, 12,
        14, 16, 18,
        20, 22, 25,
        28, 32, 36,
    ]

    rows = []

    for i in range(0, len(values), 3):
        rows.append([
            (f"Φ{v}", f"{prefix}_{v}")
            for v in values[i:i + 3]
        ])

    rows.append([
        (TEXT[lang]["manual"], f"{prefix}_manual")
    ])

    rows.append([
        (TEXT[lang]["cancel"], "cancel")
    ])

    return kb(rows)


def spacing_kb(lang, prefix="spacing"):
    values = [
        10, 12.5, 15,
        17.5, 20, 22.5,
        25, 27.5, 30,
        35, 40, 45,
        50,
    ]

    rows = []

    for i in range(0, len(values), 3):
        rows.append([
            (
                f"{str(v).replace('.', '/')} cm",
                f"{prefix}_{str(v).replace('.', '_')}"
            )
            for v in values[i:i + 3]
        ])

    rows.append([
        (TEXT[lang]["manual"], f"{prefix}_manual")
    ])

    rows.append([
        (TEXT[lang]["cancel"], "cancel")
    ])

    return kb(rows)


def count_kb(lang, prefix="count"):
    values = [
        1, 2, 3,
        4, 5, 6,
        8, 10, 12,
        15, 20, 24,
        30, 40, 50,
        60, 80, 100,
    ]

    rows = []

    for i in range(0, len(values), 3):
        rows.append([
            (str(v), f"{prefix}_{v}")
            for v in values[i:i + 3]
        ])

    rows.append([
        (TEXT[lang]["manual"], f"{prefix}_manual")
    ])

    rows.append([
        (TEXT[lang]["cancel"], "cancel")
    ])

    return kb(rows)


def dimension_kb(
    lang,
    prefix,
    values,
    unit="m",
):
    rows = []

    for i in range(0, len(values), 3):
        row = []

        for value in values[i:i + 3]:
            label = f"{value:g} {unit}"
            encoded = str(value).replace(".", "_")

            row.append(
                (
                    label,
                    f"{prefix}_{encoded}"
                )
            )

        rows.append(row)

    rows.append([
        (
            TEXT[lang]["manual"],
            f"{prefix}_manual"
        )
    ])

    rows.append([
        (TEXT[lang]["cancel"], "cancel")
    ])

    return kb(rows)


DIMENSIONS_M = [
    1.0, 1.2, 1.5,
    1.8, 2.0, 2.2,
    2.5, 2.8, 3.0,
    3.2, 3.5, 4.0,
    4.5, 5.0, 6.0,
    7.0, 8.0, 10.0,
]

THICKNESS_M = [
    0.10, 0.12, 0.15,
    0.18, 0.20, 0.22,
    0.25, 0.30, 0.35,
    0.40, 0.45, 0.50,
    0.60, 0.70, 0.80,
]

DIMENSIONS_SMALL_M = [
    0.15, 0.20, 0.25,
    0.30, 0.35, 0.40,
    0.45, 0.50, 0.55,
    0.60, 0.70, 0.80,
    0.90, 1.00, 1.20,
]


# =========================================================
# PROMPTS
# =========================================================

def field_prompt(lang, label, idx, total):
    units = {
        "count": "عدد",
        "int": "انتخاب کنید",
        "float": "مقدار",
    }

    if lang == "fa":
        return (
            f"📐 <b>{escape(label)}</b>\n\n"
            "مقدار موردنظر را انتخاب کنید:"
            f"\n\n━━━━━━━━━━━━━━\n"
            f"📍 مرحله <b>{idx}</b> از <b>{total}</b>"
        )

    return (
        f"📐 <b>{escape(label)}</b>\n\n"
        "Choose a value:"
        f"\n\n━━━━━━━━━━━━━━\n"
        f"📍 <b>{idx}</b> / <b>{total}</b>"
    )


def manual_prompt(lang, label):
    if lang == "fa":
        return (
            f"✏️ <b>{escape(label)}</b>\n\n"
            "فقط عدد را وارد کن.\n"
            "واحد را ننویس."
        )

    return (
        f"✏️ <b>{escape(label)}</b>\n\n"
        "Enter the number only.\n"
        "Do not enter the unit."
    )


# =========================================================
# INPUT KEYBOARD SELECTOR
# =========================================================

def field_keyboard(lang, key):
    if key == "count":
        return count_kb(lang, "input")

    diameter_keys = {
        "bd", "td", "ld", "tld",
        "sd", "vd", "hd",
        "md", "dd", "dia",
    }

    spacing_keys = {
        "bs", "ts",
        "bxs", "bys",
        "txs", "tys",
        "ss", "vs", "hs",
        "ms", "ds",
        "tts",
        "spacing",
    }

    if key in diameter_keys:
        return diameter_kb(lang, "input")

    if key in spacing_keys:
        return spacing_kb(lang, "input")

    if key in {"L", "W", "D", "H", "leanL", "leanW", "pl", "pw"}:
        return dimension_kb(
            lang,
            "input",
            DIMENSIONS_M,
            "m",
        )

    if key in {"T", "leanT"}:
        return dimension_kb(
            lang,
            "input",
            THICKNESS_M,
            "m",
        )

    if key in {"ph", "riser", "tread"}:
        return dimension_kb(
            lang,
            "input",
            DIMENSIONS_SMALL_M,
            "m",
        )

    if key in {"lc", "bc", "tc", "tlc", "steps"}:
        return count_kb(lang, "input")

    return kb([
        [
            (
                TEXT[lang]["manual"],
                "input_manual"
            )
        ],
        [
            (
                TEXT[lang]["cancel"],
                "cancel"
            )
        ],
    ])


# =========================================================
# CALCULATION
# =========================================================

def calculate(kind, v, project=None):

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
            int(v["td"]) if v["td"] > 0 else None,
            v["ts"] if v["td"] > 0 and v["ts"] > 0 else None,
            50,
            0,
            v["pl"],
            v["pw"],
            v["ph"],
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
            int(v["tld"]) if v["tld"] > 0 else None,
            int(v["tlc"]) if v["tlc"] > 0 else None,
            int(v["ttd"]) if v["ttd"] > 0 else None,
            v["tts"] if v["ttd"] > 0 and v["tts"] > 0 else None,
            50,
            0,
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
            int(v["txd"]) if v["txd"] > 0 else None,
            v["txs"] if v["txd"] > 0 and v["txs"] > 0 else None,
            int(v["tyd"]) if v["tyd"] > 0 else None,
            v["tys"] if v["tyd"] > 0 and v["tys"] > 0 else None,
            50,
            0,
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
            40,
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
            40,
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
            40,
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
            40,
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
            40,
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
            v["tread"],
        )

    if kind == "roof":
        area = v["L"] * v["W"]

        return roof_slab(
            area,
            ROOF_COEFF.get(
                context_roof_type(v),
                0.20,
            ),
            int(v["dia"]),
            0,
        )

    raise ValueError(
        f"Unknown calculation type: {kind}"
    )


def context_roof_type(v):
    return v.get("_roof_type", "slab")


# =========================================================
# SUMMARY
# =========================================================

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
            result.get("concrete_m3", 0),
        ) or 0
    )

    rebar = float(
        result.get(
            "total_rebar_kg",
            0,
        ) or 0
    )

    lines = [
        "🏗️ <b>نتیجه محاسبه</b>",
        "",
        f"<b>{name}</b>",
        "",
        "<pre>",
        f"بتن کل:       {concrete:>10.2f} m³",
        f"میلگرد کل:    {rebar:>10.1f} kg",
    ]

    if kind == "iso":
        lean = float(
            result.get(
                "lean_concrete_m3",
                0,
            ) or 0
        )

        footing = float(
            result.get(
                "footing_concrete_m3",
                0,
            ) or 0
        )

        pedestal = float(
            result.get(
                "pedestal_concrete_m3",
                0,
            ) or 0
        )

        lines += [
            f"بتن مگر:      {lean:>10.2f} m³",
            f"بتن پی:       {footing:>10.2f} m³",
            f"پدستال:       {pedestal:>10.2f} m³",
        ]

    lines += [
        "</pre>",
        "",
        "🔎 جزئیات میلگرد و Cut List را از دکمه‌های زیر ببین.",
    ]

    return "\n".join(lines)


def rebar_text(details):
    if not details:
        return (
            "🔩 <b>جزئیات میلگرد</b>\n\n"
            "میلگردی ثبت نشده است."
        )

    chunks = [
        "🔩 <b>جزئیات میلگرد</b>",
        "",
    ]

    total_weight = 0.0
    total_bars = 0

    for x in details:
        dia = int(
            x.get(
                "diameter_mm",
                0,
            )
        )

        pieces = int(
            x.get(
                "piece_count",
                0,
            )
        )

        length = float(
            x.get(
                "length_m",
                0,
            ) or 0
        )

        weight = float(
            x.get(
                "weight_kg",
                0,
            ) or 0
        )

        bars = int(
            x.get(
                "bars_12m",
                0,
            )
        )

        desc = x.get(
            "description",
            "",
        )

        total_weight += weight
        total_bars += bars

        chunks += [
            "━━━━━━━━━━━━━━━━",
            f"میلگرد Φ{dia}",
            f"توضیح:          {desc}",
            f"تعداد قطعات:    {pieces} عدد",
            f"طول کل:         {length:.2f} m",
            f"وزن:            {weight:.1f} kg",
            f"شاخه ۱۲ متری:   {bars} عدد",
        ]

    chunks += [
        "━━━━━━━━━━━━━━━━",
        f"وزن کل:          {total_weight:.1f} kg",
        f"شاخه کل:         {total_bars} عدد",
    ]

    return "\n".join(chunks)


def cut_text(details):
    if not details:
        return (
            "✂️ <b>Cut List</b>\n\n"
            "موردی وجود ندارد."
        )

    chunks = [
        "✂️ <b>Cut List</b>",
        "",
    ]

    for x in details:
        dia = int(
            x.get(
                "diameter_mm",
                0,
            )
        )

        plans = x.get(
            "cut_plan",
            [],
        )

        bars = int(
            x.get(
                "bars_12m",
                len(plans),
            )
        )

        chunks += [
            "━━━━━━━━━━━━━━━━",
            f"🔩 Φ{dia}",
            f"شاخه ۱۲ متری: {bars} عدد",
        ]

        for i, p in enumerate(plans, 1):
            pieces = p.get(
                "pieces",
                [],
            )

            used = sum(
                float(v)
                for v in pieces
            )

            # پرت مستقیماً از شاخه 12 متری
            waste = 12.0 - used

            piece_text = " + ".join(
                f"{float(v):.2f}"
                for v in pieces
            )

            chunks += [
                "",
                f"قطعه {i}",
                f"برش:            {piece_text} m",
                f"مصرف:           {used:.2f} m",
                f"پرت:            {waste:.2f} m",
            ]

            if i >= 15:
                if len(plans) > 15:
                    chunks.append(
                        f"... و {len(plans) - 15} شاخه دیگر"
                    )
                break

    return "\n".join(chunks)


# =========================================================
# REVIEW
# =========================================================

def review_text(kind, values, lang):
    names = {
        "iso": "پی منفرد",
        "strip": "پی نواری",
        "raft": "رادیه",
        "column_rect": "ستون مستطیلی",
        "column_round": "ستون گرد",
        "beam": "تیر",
        "tie": "شناژ / کلاف",
        "wall": "دیوار",
        "stair": "راه‌پله",
        "roof": "سقف",
    }

    lines = [
        "📋 <b>اطلاعات واردشده</b>",
        "",
        f"عضو: <b>{names.get(kind, kind)}</b>",
        "",
    ]

    for key, value in values.items():
        if key.startswith("_"):
            continue

        label = key

        for k, l, _ in STEPS.get(kind, []):
            if k == key:
                label = l
                break

        if key in {
            "bd", "td", "ld",
            "tld", "sd", "vd",
            "hd", "md", "dd",
            "dia",
        }:
            value_text = f"Φ{int(value)}"

        elif key in {
            "bs", "ts",
            "bxs", "bys",
            "txs", "tys",
            "ss", "vs", "hs",
            "ms", "ds",
            "tts", "spacing",
        }:
            value_text = f"{value:g} cm"

        elif key in {
            "L", "W", "D", "H",
            "T", "leanL", "leanW",
            "leanT", "pl", "pw",
            "ph", "riser", "tread",
        }:
            value_text = f"{value:g} m"

        else:
            value_text = str(value)

        lines.append(
            f"{escape(label)}: {escape(value_text)}"
        )

    return "\n".join(lines)


def review_kb(lang):
    return kb([
        [
            (
                TEXT[lang]["calculate"],
                "do_calculate"
            ),
        ],
        [
            (
                TEXT[lang]["edit"],
                "edit_current"
            ),
        ],
        [
            (
                TEXT[lang]["cancel"],
                "cancel"
            ),
        ],
    ])


# =========================================================
# PROJECT
# =========================================================

def project_text(context, lang):
    project = context.user_data.get(
        "project",
        {}
    )

    concrete = project.get(
        "concrete",
        "—"
    )

    steel = project.get(
        "steel",
        "—"
    )

    standard = STANDARDS.get(
        context.user_data.get(
            "standard",
            "iran",
        ),
        STANDARDS["iran"],
    )[lang]

    if lang == "fa":
        return (
            "🏗️ <b>مشخصات پروژه</b>\n\n"
            f"استاندارد: {standard}\n"
            f"مقاومت بتن: {concrete}\n"
            f"نوع میلگرد: {steel}"
        )

    return (
        f"🏗️ <b>Project Information</b>\n\n"
        f"Standard: {standard}\n"
        f"Concrete: {concrete}\n"
        f"Rebar: {steel}"
    )


# =========================================================
# START / LANGUAGE / STANDARD
# =========================================================

async def start(update, context):
    context.user_data.clear()

    await update.message.reply_text(
        "🌐 زبان / Language / اللغة / 语言:",
        reply_markup=language_kb(),
    )


async def choose_language(update, context):
    q = update.callback_query
    await q.answer()

    lang = q.data.split(
        "_",
        1,
    )[1]

    old_standard = context.user_data.get(
        "standard",
        "iran",
    )

    context.user_data.clear()

    context.user_data["lang"] = lang
    context.user_data["standard"] = old_standard

    await q.edit_message_text(
        TEXT[lang]["standard"],
        reply_markup=standard_kb(lang),
    )


async def choose_standard(update, context):
    q = update.callback_query
    await q.answer()

    standard = q.data.split(
        "_",
        1,
    )[1]

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    context.user_data["standard"] = standard

    if "project" not in context.user_data:
        context.user_data["project"] = {}

    await q.edit_message_text(
        TEXT[lang]["project"]
        + "\n\n"
        + "مقاومت بتن را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=concrete_kb(lang),
    )


# =========================================================
# PROJECT SETTINGS
# =========================================================

def concrete_kb(lang):
    return kb([
        [
            ("C20", "concrete_C20"),
            ("C25", "concrete_C25"),
            ("C30", "concrete_C30"),
        ],
        [
            ("C35", "concrete_C35"),
            ("C40", "concrete_C40"),
            ("C45", "concrete_C45"),
        ],
        [
            (TEXT[lang]["manual"], "concrete_manual"),
        ],
        [
            (TEXT[lang]["cancel"], "cancel"),
        ],
    ])


def steel_kb(lang):
    return kb([
        [
            ("A2", "steel_A2"),
            ("A3", "steel_A3"),
            ("A4", "steel_A4"),
        ],
        [
            (TEXT[lang]["manual"], "steel_manual"),
        ],
        [
            (TEXT[lang]["cancel"], "cancel"),
        ],
    ])


async def project_setup(update, context):
    q = update.callback_query
    lang = context.user_data.get("lang", "fa")

    if q.data.startswith("concrete_"):
        value = q.data.split("_", 1)[1]

        if value == "manual":
            context.user_data["manual_target"] = "project_concrete"

            await q.edit_message_text(
                manual_prompt(
                    lang,
                    "مقاومت بتن"
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

            return True

        context.user_data.setdefault(
            "project",
            {}
        )["concrete"] = value

        await q.edit_message_text(
            TEXT[lang]["project"]
            + "\n\n"
            + "نوع میلگرد را انتخاب کنید:",
            parse_mode="HTML",
            reply_markup=steel_kb(lang),
        )

        return True

    if q.data.startswith("steel_"):
        value = q.data.split("_", 1)[1]

        if value == "manual":
            context.user_data["manual_target"] = "project_steel"

            await q.edit_message_text(
                manual_prompt(
                    lang,
                    "نوع میلگرد"
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

            return True

        context.user_data.setdefault(
            "project",
            {}
        )["steel"] = value

        await q.edit_message_text(
            project_text(
                context,
                lang,
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["calculate"],
                        "project_done"
                    )
                ],
                [
                    (
                        TEXT[lang]["home"],
                        "home"
                    )
                ],
            ]),
        )

        return True

    return False


# =========================================================
# WIZARD
# =========================================================

async def begin_wizard(
    update,
    context,
    kind,
):
    q = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    context.user_data["kind"] = kind
    context.user_data["step_index"] = 0
    context.user_data["values"] = {}
    context.user_data["history"] = []

    fields = STEPS[kind]

    key, label, typ = fields[0]

    await q.edit_message_text(
        field_prompt(
            lang,
            label,
            1,
            len(fields),
        ),
        parse_mode="HTML",
        reply_markup=field_keyboard(
            lang,
            key,
        ),
    )


async def next_field(update, context):
    kind = context.user_data.get("kind")
    idx = context.user_data.get("step_index")

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    if not kind or idx is None:
        return

    fields = STEPS[kind]

    next_idx = idx + 1

    if next_idx >= len(fields):
        return await show_review(
            update,
            context,
        )

    context.user_data["step_index"] = next_idx

    key, label, typ = fields[next_idx]

    await update.message.reply_text(
        field_prompt(
            lang,
            label,
            next_idx + 1,
            len(fields),
        ),
        parse_mode="HTML",
        reply_markup=field_keyboard(
            lang,
            key,
        ),
    )


async def show_review(update, context):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    kind = context.user_data.get(
        "kind"
    )

    values = context.user_data.get(
        "values",
        {}
    )

    text = review_text(
        kind,
        values,
        lang,
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=review_kb(lang),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=review_kb(lang),
        )


# =========================================================
# MANUAL INPUT
# =========================================================

def parse_number(raw):
    raw = (
        raw.strip()
        .replace(",", ".")
        .replace("٫", ".")
        .replace("٬", "")
    )

    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"

    for i, ch in enumerate(persian):
        raw = raw.replace(ch, str(i))

    for i, ch in enumerate(arabic):
        raw = raw.replace(ch, str(i))

    return float(raw)


async def receive_manual(update, context):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    target = context.user_data.get(
        "manual_target"
    )

    raw = update.message.text

    try:
        value = parse_number(raw)

        if value < 0:
            raise ValueError

    except Exception:
        await update.message.reply_text(
            TEXT[lang]["invalid"],
            reply_markup=step_kb(lang),
        )
        return

    if target == "project_concrete":
        context.user_data.setdefault(
            "project",
            {}
        )["concrete"] = str(value)

        context.user_data.pop(
            "manual_target",
            None,
        )

        await update.message.reply_text(
            TEXT[lang]["project"]
            + "\n\n"
            + "نوع میلگرد را انتخاب کنید:",
            parse_mode="HTML",
            reply_markup=steel_kb(lang),
        )

        return

    if target == "project_steel":
        context.user_data.setdefault(
            "project",
            {}
        )["steel"] = str(value)

        context.user_data.pop(
            "manual_target",
            None,
        )

        await update.message.reply_text(
            project_text(
                context,
                lang,
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["calculate"],
                        "project_done"
                    )
                ],
                [
                    (
                        TEXT[lang]["home"],
                        "home"
                    )
                ],
            ]),
        )

        return

    if target == "equiv_count":
        context.user_data[
            "equiv_count"
        ] = int(value)

        context.user_data.pop(
            "manual_target",
            None,
        )

        await update.message.reply_text(
            "🔩 قطر میلگرد فعلی:",
            reply_markup=diameter_kb(
                lang,
                "eq_current",
            ),
        )

        return

    if target == "eq_current":
        context.user_data[
            "eq_current_dia"
        ] = int(value)

        context.user_data.pop(
            "manual_target",
            None,
        )

        await update.message.reply_text(
            "🔄 قطر میلگرد جایگزین:",
            reply_markup=diameter_kb(
                lang,
                "eq_replace",
            ),
        )

        return

    if target == "eq_replace":
        context.user_data[
            "eq_replace_dia"
        ] = int(value)

        context.user_data.pop(
            "manual_target",
            None,
        )

        return await show_equivalency(
            update,
            context,
        )

    kind = context.user_data.get(
        "kind"
    )

    idx = context.user_data.get(
        "step_index"
    )

    if not kind or idx is None:
        return

    fields = STEPS[kind]

    key, label, typ = fields[idx]

    if typ == "int":
        if int(value) != value:
            await update.message.reply_text(
                TEXT[lang]["invalid"],
                reply_markup=step_kb(lang),
            )
            return

        value = int(value)

    context.user_data.setdefault(
        "values",
        {}
    )[key] = value

    context.user_data.setdefault(
        "history",
        []
    ).append(idx)

    await next_field(
        update,
        context,
    )


# =========================================================
# QUICK BUTTON INPUT
# =========================================================

async def quick_input(update, context):
    q = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    data = q.data

    if not data.startswith("input_"):
        return False

    await q.answer()

    token = data[len("input_"):]

    kind = context.user_data.get(
        "kind"
    )

    idx = context.user_data.get(
        "step_index"
    )

    if not kind or idx is None:
        return True

    fields = STEPS[kind]
    key, label, typ = fields[idx]

    if token == "manual":
        context.user_data[
            "manual_target"
        ] = "member"

        await q.edit_message_text(
            manual_prompt(
                lang,
                label,
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang),
        )

        return True

    try:
        value = float(
            token.replace("_", ".")
        )

        if typ == "int":
            value = int(value)

    except Exception:
        await q.answer(
            "Invalid value",
            show_alert=True,
        )
        return True

    context.user_data.setdefault(
        "values",
        {}
    )[key] = value

    context.user_data.setdefault(
        "history",
        []
    ).append(idx)

    next_idx = idx + 1

    if next_idx < len(fields):
        context.user_data[
            "step_index"
        ] = next_idx

        next_key, next_label, next_typ = fields[
            next_idx
        ]

        await q.edit_message_text(
            field_prompt(
                lang,
                next_label,
                next_idx + 1,
                len(fields),
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                next_key,
            ),
        )

    else:
        context.user_data[
            "step_index"
        ] = None

        await show_review(
            update,
            context,
        )

    return True


# =========================================================
# EQUIVALENCY
# =========================================================

async def start_equivalency(
    update,
    context,
):
    q = update.callback_query
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    context.user_data[
        "equiv_count"
    ] = None

    context.user_data[
        "eq_current_dia"
    ] = None

    context.user_data[
        "eq_replace_dia"
    ] = None

    await q.edit_message_text(
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "تعداد میلگرد فعلی را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=count_kb(
            lang,
            "eq_count",
        ),
    )


async def equivalency_input(
    update,
    context,
):
    q = update.callback_query
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    data = q.data

    if data.startswith("eq_count_"):
        value = data.split(
            "_",
            2,
        )[2]

        if value == "manual":
            context.user_data[
                "manual_target"
            ] = "equiv_count"

            await q.edit_message_text(
                manual_prompt(
                    lang,
                    "تعداد میلگرد فعلی",
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

            return True

        context.user_data[
            "equiv_count"
        ] = int(value)

        await q.edit_message_text(
            "🔩 قطر میلگرد فعلی را انتخاب کنید:",
            reply_markup=diameter_kb(
                lang,
                "eq_current",
            ),
        )

        return True

    if data.startswith("eq_current_"):
        value = data.split(
            "_",
            2,
        )[2]

        if value == "manual":
            context.user_data[
                "manual_target"
            ] = "eq_current"

            await q.edit_message_text(
                manual_prompt(
                    lang,
                    "قطر میلگرد فعلی",
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

            return True

        context.user_data[
            "eq_current_dia"
        ] = int(
            value.replace("_", ".")
        )

        await q.edit_message_text(
            "🔄 قطر میلگرد جایگزین را انتخاب کنید:",
            reply_markup=diameter_kb(
                lang,
                "eq_replace",
            ),
        )

        return True

    if data.startswith("eq_replace_"):
        value = data.split(
            "_",
            2,
        )[2]

        if value == "manual":
            context.user_data[
                "manual_target"
            ] = "eq_replace"

            await q.edit_message_text(
                manual_prompt(
                    lang,
                    "قطر میلگرد جایگزین",
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

            return True

        context.user_data[
            "eq_replace_dia"
        ] = int(
            value.replace("_", ".")
        )

        await show_equivalency(
            update,
            context,
        )

        return True

    return False


async def show_equivalency(
    update,
    context,
):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    count = context.user_data.get(
        "equiv_count"
    )

    current_dia = context.user_data.get(
        "eq_current_dia"
    )

    replace_dia = context.user_data.get(
        "eq_replace_dia"
    )

    if not count or not current_dia or not replace_dia:
        return

    result = equivalent_rebar_count(
        count,
        current_dia,
        replace_dia,
    )

    current_area = result[
        "current_area_mm2"
    ]

    replacement_area = result[
        "provided_area_mm2"
    ]

    required = result[
        "required_count"
    ]

    excess = result[
        "excess_percent"
    ]

    standard = STANDARDS[
        context.user_data.get(
            "standard",
            "iran",
        )
    ][lang]

    if replacement_area >= current_area:
        status = "🟢"
        conclusion = (
            "از نظر سطح مقطع فولاد، "
            "معادل یا بیشتر است."
        )
    else:
        status = "🔴"
        conclusion = (
            "از نظر سطح مقطع فولاد، "
            "معادل نیست."
        )

    text = (
        "🔄 <b>معادل‌سازی میلگرد</b>\n\n"
        "━━━━━━━━━━━━━━━━\n"
        f"استاندارد:      {escape(standard)}\n"
        f"میلگرد فعلی:    {count}Φ{current_dia}\n"
        f"میلگرد جایگزین: Φ{replace_dia}\n"
        "━━━━━━━━━━━━━━━━\n"
        f"سطح مقطع فعلی:  {current_area:.1f} mm²\n"
        f"تعداد لازم:      {required} عدد\n"
        f"سطح مقطع جدید:  {replacement_area:.1f} mm²\n"
        f"افزایش سطح:     {excess:.1f}%\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{status} {conclusion}\n\n"
        "⚠️ این کنترل، مقایسه سطح مقطع است؛ "
        "جایگزینی نهایی باید با کنترل‌های طراحی، "
        "فاصله میلگرد، مهاری و الزامات عضو سازه‌ای "
        "تأیید شود."
    )

    markup = kb([
        [
            (
                TEXT[lang]["equivalent"],
                "equivalent",
            )
        ],
        [
            (
                TEXT[lang]["home"],
                "home",
            )
        ],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup,
        )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def buttons(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    if data.startswith("lang_"):
        return await choose_language(
            update,
            context,
        )

    if data.startswith("standard_"):
        return await choose_standard(
            update,
            context,
        )

    if data.startswith("concrete_") or data.startswith("steel_"):
        await project_setup(
            update,
            context,
        )
        return

    if data == "project_done":
        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

    if data == "home":
        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        context.user_data[
            "standard"
        ] = "iran"

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

    if data == "cancel":
        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        context.user_data[
            "standard"
        ] = "iran"

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

    if data == "language":
        return await q.edit_message_text(
            TEXT[lang]["language"],
            reply_markup=language_kb(),
        )

    if data == "settings":
        return await q.edit_message_text(
            "⚙️ <b>تنظیمات</b>\n\n"
            "گزینه موردنظر را انتخاب کنید:",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["language"],
                        "language",
                    )
                ],
                [
                    (
                        "📚 استاندارد محاسبات",
                        "change_standard",
                    )
                ],
                [
                    (
                        "🏗️ مشخصات پروژه",
                        "project_settings",
                    )
                ],
                [
                    (
                        TEXT[lang]["home"],
                        "home",
                    )
                ],
            ]),
        )

    if data == "change_standard":
        return await q.edit_message_text(
            TEXT[lang]["standard"],
            reply_markup=standard_kb(lang),
        )

    if data == "project_settings":
        return await q.edit_message_text(
            project_text(
                context,
                lang,
            )
            + "\n\n"
            + "برای تغییر مقاومت بتن یا نوع میلگرد، "
            "مشخصات پروژه را دوباره وارد کنید.",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        "✏️ تغییر مشخصات",
                        "restart_project",
                    )
                ],
                [
                    (
                        TEXT[lang]["back"],
                        "settings",
                    )
                ],
            ]),
        )

    if data == "restart_project":
        return await q.edit_message_text(
            TEXT[lang]["project"]
            + "\n\n"
            + "مقاومت بتن را انتخاب کنید:",
            parse_mode="HTML",
            reply_markup=concrete_kb(lang),
        )

    if data == "help":
        return await q.edit_message_text(
            "ℹ️ <b>راهنما</b>\n\n"
            "1️⃣ زبان را انتخاب کن.\n"
            "2️⃣ استاندارد محاسبات را انتخاب کن.\n"
            "3️⃣ مشخصات پروژه را یک‌بار وارد کن.\n"
            "4️⃣ عضو سازه‌ای را انتخاب کن.\n"
            "5️⃣ تا حد امکان از دکمه‌ها استفاده کن.\n"
            "6️⃣ قبل از محاسبه اطلاعات را بررسی کن.\n"
            "7️⃣ نتیجه، جزئیات میلگرد و Cut List را ببین.\n\n"
            "⚠️ خروجی‌ها برای برآورد و کنترل اولیه هستند "
            "و جایگزین نقشه و طراحی مهندس محاسب نیستند.",
            parse_mode="HTML",
            reply_markup=back_kb(lang),
        )

    if data == "summary":
        return await q.edit_message_text(
            "📊 <b>خلاصه پروژه</b>\n\n"
            "فعلاً اطلاعات عضوهای محاسبه‌شده در همین نشست "
            "نگهداری می‌شود.\n\n"
            "در مرحله بعد جمع کل بتن و میلگرد "
            "تمام اعضای پروژه را به این بخش متصل می‌کنیم.",
            parse_mode="HTML",
            reply_markup=back_kb(lang),
        )

    if data == "equivalent":
        return await start_equivalency(
            update,
            context,
        )

    if (
        data.startswith("eq_count_")
        or data.startswith("eq_current_")
        or data.startswith("eq_replace_")
    ):
        await equivalency_input(
            update,
            context,
        )
        return

    if data.startswith("input_"):
        await quick_input(
            update,
            context,
        )
        return

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
                reply_markup=main_menu(lang),
            )

        if idx == 0:
            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(lang),
            )

        previous = idx - 1

        key = STEPS[kind][
            previous
        ][0]

        context.user_data[
            "values"
        ].pop(
            key,
            None,
        )

        context.user_data[
            "step_index"
        ] = previous

        context.user_data[
            "history"
        ] = context.user_data.get(
            "history",
            []
        )[:-1]

        label = STEPS[kind][
            previous
        ][1]

        return await q.edit_message_text(
            field_prompt(
                lang,
                label,
                previous + 1,
                len(STEPS[kind]),
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                key,
            ),
        )

    if data == "foundation":
        return await q.edit_message_text(
            "🧱 <b>فونداسیون</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("⬛ پی منفرد", "foundation_iso"),
                    ("▬ پی نواری", "foundation_strip"),
                    ("▰ پی گسترده / رادیه", "foundation_raft"),
                ],
            ),
        )

    if data == "columns":
        return await q.edit_message_text(
            "🏛️ <b>ستون‌ها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        "▯ ستون مربعی / مستطیلی",
                        "column_rect",
                    ),
                    (
                        "◯ ستون گرد",
                        "column_round",
                    ),
                ],
            ),
        )

    if data == "beams":
        return await q.edit_message_text(
            "📐 <b>تیرها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        "📐 تیر اصلی",
                        "beam_main",
                    ),
                    (
                        "📏 تیر فرعی",
                        "beam_secondary",
                    ),
                ],
            ),
        )

    if data == "roofs":
        return await q.edit_message_text(
            "🏠 <b>سقف‌ها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        ROOF_NAMES["foam"][lang],
                        "roof_foam",
                    ),
                    (
                        ROOF_NAMES["clay"][lang],
                        "roof_clay",
                    ),
                    (
                        ROOF_NAMES["double"][lang],
                        "roof_double",
                    ),
                    (
                        ROOF_NAMES["kromit"][lang],
                        "roof_kromit",
                    ),
                    (
                        ROOF_NAMES["composite"][lang],
                        "roof_composite",
                    ),
                    (
                        ROOF_NAMES["steeldeck"][lang],
                        "roof_steeldeck",
                    ),
                    (
                        ROOF_NAMES["slab"][lang],
                        "roof_slab",
                    ),
                    (
                        ROOF_NAMES["waffle"][lang],
                        "roof_waffle",
                    ),
                ],
            ),
        )

    if data == "ties":
        return await q.edit_message_text(
            "🔗 <b>شناژ و کلاف</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        "🔗 شناژ",
                        "tie_beam",
                    ),
                    (
                        "⛓️ کلاف",
                        "tie_cowl",
                    ),
                ],
            ),
        )

    if data == "walls":
        return await q.edit_message_text(
            "🧱 <b>دیوارها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        "🏢 دیوار برشی",
                        "wall_shear",
                    ),
                    (
                        "🧱 دیوار حائل",
                        "wall_retaining",
                    ),
                ],
            ),
        )

    if data == "stairs":
        return await begin_wizard(
            update,
            context,
            "stair",
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
            mapping[data],
        )

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
            "_roof_type": roof_type
        }

        context.user_data[
            "history"
        ] = []

        key, label, typ = STEPS[
            "roof"
        ][0]

        return await q.edit_message_text(
            f"🏠 <b>{ROOF_NAMES[roof_type][lang]}</b>\n\n"
            + field_prompt(
                lang,
                label,
                1,
                len(STEPS["roof"]),
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                key,
            ),
        )

    if data == "edit_current":
        kind = context.user_data.get(
            "kind"
        )

        if not kind:
            return

        context.user_data[
            "step_index"
        ] = 0

        return await q.edit_message_text(
            field_prompt(
                lang,
                STEPS[kind][0][1],
                1,
                len(STEPS[kind]),
            ),
            parse_mode="HTML",
            reply_markup=field_keyboard(
                lang,
                STEPS[kind][0][0],
            ),
        )

    if data == "do_calculate":
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
                values,
                context.user_data.get(
                    "project",
                    {},
                ),
            )

            context.user_data[
                "result"
            ] = result

            context.user_data[
                "step_index"
            ] = None

            await q.edit_message_text(
                summary_text(
                    kind,
                    result,
                    lang,
                ),
                parse_mode="HTML",
                reply_markup=result_kb(lang),
            )

        except Exception as exc:
            logger.exception(
                "Calculation failed"
            )

            await q.edit_message_text(
                TEXT[lang][
                    "calc_error"
                ].format(
                    escape(str(exc))
                ),
                parse_mode="HTML",
                reply_markup=step_kb(lang),
            )

        return

    if data == "show_rebar":
        return await q.edit_message_text(
            rebar_text(
                context.user_data.get(
                    "result",
                    {}
                ).get(
                    "rebar_details",
                    [],
                )
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["cut"],
                        "show_cut",
                    ),
                    (
                        "⬅️ نتیجه",
                        "back_result",
                    ),
                ],
                [
                    (
                        TEXT[lang]["home"],
                        "home",
                    )
                ],
            ]),
        )

    if data == "show_cut":
        return await q.edit_message_text(
            cut_text(
                context.user_data.get(
                    "result",
                    {}
                ).get(
                    "rebar_details",
                    [],
                )
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["rebar"],
                        "show_rebar",
                    ),
                    (
                        "⬅️ نتیجه",
                        "back_result",
                    ),
                ],
                [
                    (
                        TEXT[lang]["home"],
                        "home",
                    )
                ],
            ]),
        )

    if data == "back_result":
        return await q.edit_message_text(
            summary_text(
                context.user_data.get(
                    "kind",
                    "",
                ),
                context.user_data.get(
                    "result",
                    {},
                ),
                lang,
            ),
            parse_mode="HTML",
            reply_markup=result_kb(lang),
        )

    if data == "new_member":
        context.user_data[
            "kind"
        ] = None

        context.user_data[
            "values"
        ] = {}

        context.user_data[
            "result"
        ] = None

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

    await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang),
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def receive(update, context):
    if context.user_data.get(
        "manual_target"
    ):
        return await receive_manual(
            update,
            context,
        )

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    kind = context.user_data.get(
        "kind"
    )

    idx = context.user_data.get(
        "step_index"
    )

    if kind is None or idx is None:
        await update.message.reply_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

        return

    await update.message.reply_text(
        TEXT[lang]["invalid"],
        reply_markup=step_kb(lang),
    )


# =========================================================
# ERROR
# =========================================================

async def error_handler(
    update,
    context,
):
    logger.exception(
        "Unhandled bot error",
        exc_info=context.error,
    )


# =========================================================
# MAIN
# =========================================================

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
            start,
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
            receive,
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
