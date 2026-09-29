# bot.py - Version 2.0
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
    normalize_standard,
    project_settings,
    aggregate_project_results,
    equivalent_rebar_count,
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


# ============================================================
# Standards / Materials
# ============================================================

STANDARDS = {
    "iran": "🇮🇷 مبحث ۹ ایران",
    "aci318": "🇺🇸 ACI 318",
    "eurocode2": "🇪🇺 Eurocode 2",
    "china": "🇨🇳 China / GB",
}

EDITIONS = {
    key: "نسخه پروژه / نیازمند انتخاب دقیق"
    for key in STANDARDS
}

CONCRETE_OPTIONS = [
    25,
    30,
    35,
    40,
]

REBAR_OPTIONS = {
    "iran": [
        ("A2", 300),
        ("A3", 400),
        ("A4", 500),
    ],

    "aci318": [
        ("Grade 40", 280),
        ("Grade 60", 420),
    ],

    "eurocode2": [
        ("B400", 400),
        ("B500", 500),
    ],

    "china": [],
}


# ============================================================
# Roofs
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
# Text
# ============================================================

TEXT = {
    "fa": {
        "welcome":
            "🏗️ <b>Structural Quantity Engine</b>\n\n"
            "استاندارد، مصالح و سپس عضو سازه‌ای را انتخاب کنید.",

        "invalid":
            "❌ مقدار معتبر نیست. دوباره وارد کنید.",

        "back":
            "🔙 بازگشت",

        "home":
            "🏠 صفحه اصلی",

        "cancel":
            "❌ لغو",

        "standard":
            "📚 استاندارد",

        "concrete":
            "🧱 مقاومت بتن",

        "grade":
            "🔩 گرید میلگرد",

        "ready":
            "✅ پروژه آماده است.",

        "summary":
            "📊 خلاصه پروژه",

        "settings":
            "⚙️ تنظیمات",

        "help":
            "ℹ️ راهنما",

        "no_project":
            "هنوز پروژه‌ای تعریف نشده است.",
    },

    "en": {
        "welcome":
            "🏗️ <b>Structural Quantity Engine</b>\n\n"
            "Select standard, materials, then a structural member.",

        "invalid":
            "❌ Invalid value. Try again.",

        "back":
            "🔙 Back",

        "home":
            "🏠 Main Menu",

        "cancel":
            "❌ Cancel",

        "standard":
            "📚 Standard",

        "concrete":
            "🧱 Concrete",

        "grade":
            "🔩 Rebar Grade",

        "ready":
            "✅ Project is ready.",

        "summary":
            "📊 Project Summary",

        "settings":
            "⚙️ Settings",

        "help":
            "ℹ️ Help",

        "no_project":
            "No project is configured yet.",
    },
}


# ============================================================
# Wizard Steps
# ============================================================

STEPS = {

    "iso": [
        ("count", "تعداد پی", "int"),
        ("L", "طول پی (m)", "float"),
        ("W", "عرض پی (m)", "float"),
        ("T", "ضخامت پی (m)", "float"),

        ("leanL", "طول بتن مگر (m)", "float"),
        ("leanW", "عرض بتن مگر (m)", "float"),
        ("leanT", "ضخامت بتن مگر (m)", "float"),

        ("bd", "قطر میلگرد پایین (mm)", "int"),
        ("bs", "فاصله میلگرد پایین (mm)", "int"),

        ("td", "قطر میلگرد بالا؛ 0 اگر ندارد", "int"),
        ("ts", "فاصله میلگرد بالا؛ 0 اگر ندارد", "int"),

        ("cover", "کاور (mm)", "float"),
        ("lap", "درصد اورلپ", "float"),

        ("pl", "طول پدستال (m)", "float"),
        ("pw", "عرض پدستال (m)", "float"),
        ("ph", "ارتفاع پدستال (m)", "float"),
    ],

    "strip": [
        ("count", "تعداد نوار", "int"),
        ("L", "طول نوار (m)", "float"),
        ("W", "عرض پی (m)", "float"),
        ("T", "ضخامت پی (m)", "float"),

        ("leanL", "طول بتن مگر (m)", "float"),
        ("leanW", "عرض بتن مگر (m)", "float"),
        ("leanT", "ضخامت بتن مگر (m)", "float"),

        ("ld", "قطر طولی پایین (mm)", "int"),
        ("lc", "تعداد طولی پایین", "int"),

        ("td", "قطر عرضی پایین (mm)", "int"),
        ("ts", "فاصله عرضی پایین (mm)", "int"),

        ("tld", "قطر طولی بالا؛ 0 اگر ندارد", "int"),
        ("tlc", "تعداد طولی بالا؛ 0 اگر ندارد", "int"),

        ("ttd", "قطر عرضی بالا؛ 0 اگر ندارد", "int"),
        ("tts", "فاصله عرضی بالا؛ 0 اگر ندارد", "int"),

        ("cover", "کاور (mm)", "float"),
        ("lap", "درصد اورلپ", "float"),
    ],

    "raft": [
        ("L", "طول رادیه (m)", "float"),
        ("W", "عرض رادیه (m)", "float"),
        ("T", "ضخامت رادیه (m)", "float"),

        ("leanL", "طول بتن مگر (m)", "float"),
        ("leanW", "عرض بتن مگر (m)", "float"),
        ("leanT", "ضخامت بتن مگر (m)", "float"),

        ("bxd", "قطر X پایین (mm)", "int"),
        ("bxs", "فاصله X پایین (mm)", "int"),

        ("byd", "قطر Y پایین (mm)", "int"),
        ("bys", "فاصله Y پایین (mm)", "int"),

        ("txd", "قطر X بالا؛ 0 اگر ندارد", "int"),
        ("txs", "فاصله X بالا؛ 0 اگر ندارد", "int"),

        ("tyd", "قطر Y بالا؛ 0 اگر ندارد", "int"),
        ("tys", "فاصله Y بالا؛ 0 اگر ندارد", "int"),

        ("cover", "کاور (mm)", "float"),
        ("lap", "درصد اورلپ", "float"),
    ],

    "column_rect": [
        ("count", "تعداد ستون", "int"),
        ("W", "عرض ستون (m)", "float"),
        ("D", "عمق ستون (m)", "float"),
        ("H", "ارتفاع ستون (m)", "float"),

        ("ld", "قطر میلگرد طولی (mm)", "int"),
        ("lc", "تعداد میلگرد طولی هر ستون", "int"),

        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),

        ("cover", "کاور (mm)", "float"),
    ],

    "column_round": [
        ("count", "تعداد ستون گرد", "int"),
        ("D", "قطر ستون (m)", "float"),
        ("H", "ارتفاع ستون (m)", "float"),

        ("ld", "قطر میلگرد طولی (mm)", "int"),
        ("lc", "تعداد میلگرد طولی هر ستون", "int"),

        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),

        ("cover", "کاور (mm)", "float"),
    ],

    "beam": [
        ("count", "تعداد تیر", "int"),
        ("L", "طول تیر (m)", "float"),
        ("W", "عرض تیر (m)", "float"),
        ("H", "ارتفاع تیر (m)", "float"),

        ("bd", "قطر پایین (mm)", "int"),
        ("bc", "تعداد پایین", "int"),

        ("td", "قطر بالا (mm)", "int"),
        ("tc", "تعداد بالا", "int"),

        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),

        ("cover", "کاور (mm)", "float"),
    ],

    "tie": [
        ("count", "تعداد شناژ/کلاف", "int"),
        ("L", "طول (m)", "float"),
        ("W", "عرض (m)", "float"),
        ("H", "ارتفاع (m)", "float"),

        ("ld", "قطر طولی (mm)", "int"),
        ("lc", "تعداد طولی", "int"),

        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),

        ("cover", "کاور (mm)", "float"),
    ],

    "wall": [
        ("L", "طول دیوار (m)", "float"),
        ("H", "ارتفاع دیوار (m)", "float"),
        ("T", "ضخامت دیوار (m)", "float"),

        ("vd", "قطر قائم (mm)", "int"),
        ("vs", "فاصله قائم (mm)", "int"),

        ("hd", "قطر افقی (mm)", "int"),
        ("hs", "فاصله افقی (mm)", "int"),

        ("cover", "کاور (mm)", "float"),
    ],

    "stair": [
        ("L", "طول شیب/دال (m)", "float"),
        ("W", "عرض راه‌پله (m)", "float"),
        ("T", "ضخامت دال (m)", "float"),

        ("md", "قطر اصلی (mm)", "int"),
        ("ms", "فاصله اصلی (mm)", "int"),

        ("dd", "قطر توزیعی (mm)", "int"),
        ("ds", "فاصله توزیعی (mm)", "int"),

        ("steps", "تعداد پله", "int"),
        ("riser", "ارتفاع رایزر (m)", "float"),
        ("tread", "کف پله (m)", "float"),
    ],

    "roof": [
        ("area", "مساحت سقف (m²)", "float"),
        ("dia", "قطر میلگرد (mm)", "int"),
        ("kgm2", "مصرف میلگرد kg/m²؛ برای 0 وارد کن", "float"),
    ],
}


# ============================================================
# Keyboard Helpers
# ============================================================

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


def back_kb(lang, callback="home"):
    return kb([
        [
            (TEXT[lang]["back"], callback),
            (TEXT[lang]["home"], "home")
        ]
    ])


def step_kb(lang):
    return kb([
        [
            ("⬅️ مرحله قبل", "prev"),
            (TEXT[lang]["cancel"], "cancel")
        ],
        [
            (TEXT[lang]["home"], "home")
        ],
    ])


def result_kb(lang):
    return kb([
        [
            ("🔩 میلگرد", "show_rebar"),
            ("✂️ Cut List", "show_cut")
        ],
        [
            ("➕ عضو جدید", "new_member")
        ],
        [
            ("📊 خلاصه پروژه", "summary")
        ],
        [
            (TEXT[lang]["home"], "home")
        ],
    ])


def section_kb(lang, items, parent="home"):
    return kb(
        [
            [a, b]
            for a, b in items
        ]
        + [
            [
                TEXT[lang]["back"],
                parent
            ]
        ]
    )


def prompt_text(lang, label, i, total):

    if lang == "fa":
        return (
            f"📐 <b>{escape(label)}</b>\n\n"
            "مقدار را وارد کنید:\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 مرحله <b>{i}</b> از <b>{total}</b>"
        )

    return (
        f"📐 <b>{escape(label)}</b>\n\n"
        "Enter value:\n\n"
        "━━━━━━━━━━━━━━\n"
        f"📍 Step <b>{i}</b> of <b>{total}</b>"
    )


# ============================================================
# Project Helpers
# ============================================================

def project_ready(context):
    return all(
        context.get(k) is not None
        for k in (
            "standard",
            "fc",
            "grade",
            "fy",
        )
    )


def project_header(context):

    standard = STANDARDS.get(
        context.get("standard"),
        "-"
    )

    return (
        f"استاندارد: {standard}\n"
        f"ویرایش: {context.get('edition', '-')}\n"
        f"بتن: C{context.get('fc', '-')} MPa\n"
        f"میلگرد: {context.get('grade', '-')} "
        f"/ fy={context.get('fy', '-')} MPa"
    )


# ============================================================
# Main Menu
# ============================================================

def main_menu(lang):

    if lang == "fa":

        return kb([
            [
                ("🧱 فونداسیون", "foundation"),
                ("🏛️ ستون‌ها", "columns")
            ],
            [
                ("📐 تیرها", "beams"),
                ("🏠 سقف‌ها", "roofs")
            ],
            [
                ("🪜 راه‌پله", "stairs"),
                ("🔗 شناژ و کلاف", "ties")
            ],
            [
                ("🧱 دیوارها", "walls")
            ],
            [
                ("📊 خلاصه پروژه", "summary"),
                ("⚙️ تنظیمات", "settings")
            ],
            [
                ("🔁 معادل‌سازی میلگرد", "equiv")
            ],
            [
                ("ℹ️ راهنما", "help")
            ],
        ])

    return kb([
        [
            ("🧱 Foundation", "foundation"),
            ("🏛️ Columns", "columns")
        ],
        [
            ("📐 Beams", "beams"),
            ("🏠 Roofs", "roofs")
        ],
        [
            ("🪜 Stairs", "stairs"),
            ("🔗 Tie Beams", "ties")
        ],
        [
            ("🧱 Walls", "walls")
        ],
        [
            ("📊 Summary", "summary"),
            ("⚙️ Settings", "settings")
        ],
        [
            ("🔁 Rebar Equivalency", "equiv")
        ],
        [
            ("ℹ️ Help", "help")
        ],
    ])


# ============================================================
# Result Display
# ============================================================

def summary_text(kind, result, lang):

    names = {
        "iso": "⬛ پی منفرد",
        "strip": "▬ پی نواری",
        "raft": "▰ رادیه",
        "column_rect": "▯ ستون مستطیلی",
        "column_round": "◯ ستون گرد",
        "beam": "📐 تیر",
        "tie": "🔗 شناژ / کلاف",
        "wall": "🧱 دیوار",
        "stair": "🪜 راه‌پله",
        "roof": "🏠 سقف",
    }

    name = names.get(
        kind,
        kind
    )

    return (
        "🏗️ <b>نتیجه محاسبه</b>\n\n"
        f"<b>{name}</b>\n\n"
        "<pre>"
        f"بتن              "
        f"{float(result.get('total_concrete_m3', 0)):.2f} m³\n"

        f"میلگرد            "
        f"{float(result.get('total_rebar_kg', 0)):.1f} kg\n"

        f"طول میلگرد        "
        f"{float(result.get('total_rebar_length_m', 0)):.2f} m\n"

        f"شاخه ۱۲ متری      "
        f"{int(result.get('total_stock_bars_12m', 0))}\n"

        f"پرت میلگرد        "
        f"{float(result.get('total_rebar_waste_m', 0)):.2f} m\n"

        f"درصد پرت          "
        f"{float(result.get('rebar_waste_percent', 0)):.2f}%"
        "</pre>"
    )


def rebar_text(details):

    if not details:
        return (
            "🔩 <b>میلگرد</b>\n\n"
            "موردی ثبت نشده."
        )

    lines = [
        "🔩 <b>Rebar Schedule</b>",
        "",
        "<pre>",
        "قطر   قطعه   طول(m)   وزن(kg)   شاخه",
        "────────────────────────────────",
    ]

    for x in details:

        lines.append(
            f"Φ{x['diameter_mm']:<4} "
            f"{x['piece_count']:<6} "
            f"{x['length_m']:<9.2f} "
            f"{x['weight_kg']:<9.1f} "
            f"{x['bars_12m']}"
        )

    lines.append("</pre>")

    return "\n".join(lines)


def cut_text(details):

    if not details:
        return (
            "✂️ <b>Cut List</b>\n\n"
            "موردی ثبت نشده."
        )

    out = [
        "✂️ <b>Cut List</b>",
        ""
    ]

    for x in details:

        out.append(
            f"<b>Φ{x['diameter_mm']}</b> — "
            f"{x['bars_12m']} شاخه ۱۲ متری"
        )

        out.append("<pre>")

        plans = x.get(
            "cut_plan",
            []
        )

        for i, p in enumerate(
            plans,
            1
        ):

            if i > 15:

                out.append(
                    f"... "
                    f"{len(plans) - 15} "
                    f"شاخه دیگر"
                )

                break

            pieces = " + ".join(
                f"{v:.2f}"
                for v in p.get(
                    "pieces",
                    []
                )
            )

            out.append(
                f"{i:02d}) "
                f"{pieces} = "
                f"{p['used_m']:.2f} | "
                f"پرت {p['waste_m']:.2f}"
            )

        out.append("</pre>")

    return "\n".join(out)


# ============================================================
# Project Summary
# ============================================================

def project_summary(context):

    data = aggregate_project_results(
        context.get(
            "project_results",
            []
        )
    )

    lines = [
        "📊 <b>خلاصه پروژه</b>",
        "",
        "<pre>",
        project_header(context),
        "",
        f"اعضا              "
        f"{data['member_count']}",

        f"بتن کل            "
        f"{data['total_concrete_m3']:.2f} m³",

        f"میلگرد کل         "
        f"{data['total_rebar_kg']:.1f} kg",

        f"طول میلگرد        "
        f"{data['total_rebar_length_m']:.2f} m",

        f"شاخه ۱۲ متری      "
        f"{data['total_stock_bars_12m']}",

        f"پرت                "
        f"{data['total_rebar_waste_m']:.2f} m",

        f"درصد پرت           "
        f"{data['rebar_waste_percent']:.2f}%",

        "",
        "Breakdown قطر:",
    ]

    for dia, x in sorted(
        data["by_diameter"].items(),
        key=lambda z: int(z[0])
    ):

        lines.append(
            f"Φ{dia:<3} "
            f"{x['weight_kg']:>9.1f} kg | "
            f"{x['length_m']:>9.2f} m | "
            f"{x['bars_12m']:>4} شاخه"
        )

    lines.append("</pre>")

    return "\n".join(lines)


# ============================================================
# Calculation Router
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
            if v["td"] > 0
            else None,
            v["ts"]
            if (
                v["td"] > 0
                and v["ts"] > 0
            )
            else None,
            v["cover"],
            v["lap"],
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
            int(v["tld"])
            if v["tld"] > 0
            else None,
            int(v["tlc"])
            if v["tlc"] > 0
            else None,
            int(v["ttd"])
            if v["ttd"] > 0
            else None,
            v["tts"]
            if (
                v["ttd"] > 0
                and v["tts"] > 0
            )
            else None,
            v["cover"],
            v["lap"],
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
            if v["txd"] > 0
            else None,
            v["txs"]
            if (
                v["txd"] > 0
                and v["txs"] > 0
            )
            else None,
            int(v["tyd"])
            if v["tyd"] > 0
            else None,
            v["tys"]
            if (
                v["tyd"] > 0
                and v["tys"] > 0
            )
            else None,
            v["cover"],
            v["lap"],
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
            v["cover"],
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
            v["cover"],
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
            v["cover"],
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
            v["cover"],
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
            v["cover"],
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

        return roof_slab(
            v["area"],
            v["coeff"],
            int(v["dia"]),
            v["kgm2"],
        )

    raise ValueError(
        f"Unknown calculation type: {kind}"
    )


# ============================================================
# Project Setup
# ============================================================

async def start_project_setup(
    update,
    context
):

    context.user_data[
        "project_results"
    ] = []

    await update.message.reply_text(
        "📚 <b>انتخاب استاندارد</b>",
        parse_mode="HTML",
        reply_markup=kb([
            [
                (value, f"std_{key}")
                for key, value in STANDARDS.items()
            ]
        ]),
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data[
        "lang"
    ] = "fa"

    await start_project_setup(
        update,
        context
    )


# ============================================================
# Wizard
# ============================================================

async def begin_wizard(
    update,
    context,
    kind
):

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    if not project_ready(
        context.user_data
    ):

        return await (
            update.callback_query
            .edit_message_text(
                "⚠️ ابتدا استاندارد و "
                "مصالح پروژه را تنظیم کن.",
                reply_markup=back_kb(lang)
            )
        )

    context.user_data.update(
        kind=kind,
        step_index=0,
        values={},
        history=[],
    )

    fields = STEPS[kind]

    await update.callback_query.edit_message_text(
        prompt_text(
            lang,
            fields[0][1],
            1,
            len(fields)
        ),
        parse_mode="HTML",
        reply_markup=step_kb(lang),
    )


async def receive(
    update,
    context
):

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    kind = context.user_data.get(
        "kind"
    )

    idx = context.user_data.get(
        "step_index"
    )

    if kind is None or idx is None:

        return await update.message.reply_text(
            "ابتدا پروژه را تنظیم کن."
        )

    key, label, typ = STEPS[
        kind
    ][idx]

    raw = (
        update.message.text
        .strip()
        .replace(",", ".")
        .replace("٫", ".")
    )

    try:

        value = float(raw)

        if (
            typ == "int"
            and value.is_integer()
        ):
            value = int(value)

        if value < 0:
            raise ValueError

        if (
            typ == "int"
            and not isinstance(value, int)
        ):
            raise ValueError

    except Exception:

        return await update.message.reply_text(
            TEXT[lang]["invalid"],
            reply_markup=step_kb(lang)
        )

    context.user_data[
        "values"
    ][key] = value

    context.user_data[
        "history"
    ].append(idx)

    nxt = idx + 1

    if nxt < len(STEPS[kind]):

        context.user_data[
            "step_index"
        ] = nxt

        f = STEPS[kind][nxt]

        return await update.message.reply_text(
            prompt_text(
                lang,
                f[1],
                nxt + 1,
                len(STEPS[kind])
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang)
        )

    try:

        result = calculate(
            kind,
            context.user_data["values"]
        )

        context.user_data[
            "result"
        ] = result

        context.user_data[
            "step_index"
        ] = None

        context.user_data.setdefault(
            "project_results",
            []
        ).append(
            {
                "kind": kind,
                "result": result,
                "values":
                    dict(
                        context.user_data[
                            "values"
                        ]
                    ),
            }
        )

        await update.message.reply_text(
            summary_text(
                kind,
                result,
                lang
            ),
            parse_mode="HTML",
            reply_markup=result_kb(lang)
        )

    except Exception as exc:

        logger.exception(
            "Calculation failed"
        )

        await update.message.reply_text(
            "❌ خطا در محاسبه:\n"
            f"<code>{escape(str(exc))}</code>",
            parse_mode="HTML",
            reply_markup=step_kb(lang)
        )


# ============================================================
# Callback Buttons
# ============================================================

async def buttons(
    update,
    context
):

    q = update.callback_query

    await q.answer()

    data = q.data

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    # --------------------------------------------------------
    # Standard
    # --------------------------------------------------------

    if data.startswith("std_"):

        std = data[4:]

        context.user_data[
            "standard"
        ] = std

        context.user_data[
            "edition"
        ] = EDITIONS[std]

        return await q.edit_message_text(
            "🧱 <b>مقاومت بتن</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        f"C{x} MPa",
                        f"fc_{x}"
                    )
                    for x in CONCRETE_OPTIONS
                ]
            ])
        )

    # --------------------------------------------------------
    # Concrete
    # --------------------------------------------------------

    if data.startswith("fc_"):

        context.user_data[
            "fc"
        ] = int(data[3:])

        std = context.user_data[
            "standard"
        ]

        opts = REBAR_OPTIONS[
            std
        ]

        if not opts:

            return await q.edit_message_text(
                "🔩 <b>China / GB</b>\n\n"
                "برای این استاندارد فعلاً "
                "fy را عددی وارد کن (MPa).",
                parse_mode="HTML",
                reply_markup=kb([
                    [
                        ("✏️ ورود fy", "china_fy")
                    ],
                    [
                        ("🏠 صفحه اصلی", "home")
                    ]
                ])
            )

        return await q.edit_message_text(
            "🔩 <b>گرید میلگرد</b>",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        f"{g} ({fy} MPa)",
                        f"grade_{g}"
                    )
                    for g, fy in opts
                ]
            ])
        )

    # --------------------------------------------------------
    # Grade
    # --------------------------------------------------------

    if data.startswith("grade_"):

        grade = data[6:]

        std = context.user_data[
            "standard"
        ]

        fy = next(
            f
            for g, f in REBAR_OPTIONS[std]
            if g == grade
        )

        context.user_data.update(
            grade=grade,
            fy=fy,
        )

        return await q.edit_message_text(
            TEXT[lang]["welcome"]
            + "\n\n"
            + project_header(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # China fy
    # --------------------------------------------------------

    if data == "china_fy":

        context.user_data[
            "await_fy"
        ] = True

        return await q.edit_message_text(
            "عدد fy را بر حسب MPa وارد کن:",
            reply_markup=back_kb(lang)
        )

    # --------------------------------------------------------
    # Home
    # --------------------------------------------------------

    if data == "home":

        context.user_data.pop(
            "kind",
            None
        )

        context.user_data.pop(
            "values",
            None
        )

        context.user_data.pop(
            "result",
            None
        )

        return await q.edit_message_text(
            TEXT[lang]["welcome"]
            + "\n\n"
            + project_header(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # Cancel
    # --------------------------------------------------------

    if data == "cancel":

        context.user_data.pop(
            "kind",
            None
        )

        context.user_data.pop(
            "values",
            None
        )

        return await q.edit_message_text(
            TEXT[lang]["welcome"]
            + "\n\n"
            + project_header(
                context.user_data
            ),
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

        if not kind or idx in (
            None,
            0
        ):

            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(lang)
            )

        idx -= 1

        context.user_data[
            "step_index"
        ] = idx

        context.user_data[
            "values"
        ].pop(
            STEPS[kind][idx][0],
            None
        )

        return await q.edit_message_text(
            prompt_text(
                lang,
                STEPS[kind][idx][1],
                idx + 1,
                len(STEPS[kind])
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang)
        )

    # --------------------------------------------------------
    # Sections
    # --------------------------------------------------------

    if data == "foundation":

        return await q.edit_message_text(
            "🧱 <b>فونداسیون</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("⬛ پی منفرد", "foundation_iso"),
                    ("▬ پی نواری", "foundation_strip"),
                    ("▰ رادیه", "foundation_raft"),
                ]
            )
        )

    if data == "columns":

        return await q.edit_message_text(
            "🏛️ <b>ستون‌ها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("▯ مستطیلی", "column_rect"),
                    ("◯ گرد", "column_round"),
                ]
            )
        )

    if data == "beams":

        return await q.edit_message_text(
            "📐 <b>تیرها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("📐 تیر اصلی", "beam_main"),
                    ("📏 تیر فرعی", "beam_secondary"),
                ]
            )
        )

    if data == "ties":

        return await q.edit_message_text(
            "🔗 <b>شناژ و کلاف</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("🔗 شناژ", "tie_beam"),
                    ("⛓️ کلاف", "tie_cowl"),
                ]
            )
        )

    if data == "walls":

        return await q.edit_message_text(
            "🧱 <b>دیوارها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    ("🏢 دیوار برشی", "wall_shear"),
                    ("🧱 دیوار حائل", "wall_retaining"),
                ]
            )
        )

    if data == "stairs":

        return await begin_wizard(
            update,
            context,
            "stair"
        )

    if data == "roofs":

        return await q.edit_message_text(
            "🏠 <b>سقف‌ها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        ROOF_NAMES[k],
                        f"roof_{k}"
                    )
                    for k in ROOF_NAMES
                ]
            )
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

        rt = data[5:]

        context.user_data.update(
            kind="roof",
            step_index=0,
            values={
                "coeff":
                    ROOF_COEFF[rt]
            },
            history=[],
            roof_name=
                ROOF_NAMES[rt],
        )

        f = STEPS["roof"]

        return await q.edit_message_text(
            f"🏠 <b>{ROOF_NAMES[rt]}</b>\n\n"
            + prompt_text(
                lang,
                f[0][1],
                1,
                len(f)
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang)
        )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    if data == "show_rebar":

        return await q.edit_message_text(
            rebar_text(
                context.user_data.get(
                    "result",
                    {}
                ).get(
                    "rebar_details",
                    []
                )
            ),
            parse_mode="HTML",
            reply_markup=back_kb(
                lang,
                "back_result"
            )
        )

    if data == "show_cut":

        return await q.edit_message_text(
            cut_text(
                context.user_data.get(
                    "result",
                    {}
                ).get(
                    "rebar_details",
                    []
                )
            ),
            parse_mode="HTML",
            reply_markup=back_kb(
                lang,
                "back_result"
            )
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
            reply_markup=result_kb(lang)
        )

    # --------------------------------------------------------
    # New Member
    # --------------------------------------------------------

    if data == "new_member":

        return await q.edit_message_text(
            TEXT[lang]["welcome"]
            + "\n\n"
            + project_header(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=main_menu(lang)
        )

    # --------------------------------------------------------
    # Project Summary
    # --------------------------------------------------------

    if data == "summary":

        return await q.edit_message_text(
            project_summary(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=back_kb(lang)
        )

    # --------------------------------------------------------
    # Settings
    # --------------------------------------------------------

    if data == "settings":

        return await q.edit_message_text(
            "⚙️ <b>تنظیمات پروژه</b>\n\n"
            + project_header(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [
                    ("📚 تغییر استاندارد", "change_std")
                ],
                [
                    ("🧱 تغییر بتن", "change_fc")
                ],
                [
                    ("🔩 تغییر میلگرد", "change_grade")
                ],
                [
                    ("🏠 صفحه اصلی", "home")
                ],
            ])
        )

    if data == "change_std":

        return await q.edit_message_text(
            "📚 استاندارد جدید:",
            reply_markup=kb([
                [
                    (v, f"std_{k}")
                    for k, v in STANDARDS.items()
                ]
            ])
        )

    if data == "change_fc":

        return await q.edit_message_text(
            "🧱 بتن جدید:",
            reply_markup=kb([
                [
                    (
                        f"C{x}",
                        f"fc_{x}"
                    )
                    for x in CONCRETE_OPTIONS
                ]
            ])
        )

    if data == "change_grade":

        opts = REBAR_OPTIONS.get(
            context.user_data.get(
                "standard"
            ),
            []
        )

        return await q.edit_message_text(
            "🔩 گرید جدید:",
            reply_markup=kb(
                [
                    [
                        (
                            f"{g} ({fy})",
                            f"grade_{g}"
                        )
                        for g, fy in opts
                    ]
                ]
                or [
                    [
                        ("✏️ fy چین", "china_fy")
                    ]
                ]
            )
        )

    # --------------------------------------------------------
    # Equivalency
    # --------------------------------------------------------

    if data == "equiv":

        context.user_data[
            "equiv_step"
        ] = 0

        return await q.edit_message_text(
            "تعداد میلگرد فعلی را وارد کن:",
            reply_markup=back_kb(lang)
        )

    # --------------------------------------------------------
    # Help
    # --------------------------------------------------------

    if data == "help":

        return await q.edit_message_text(
            "ℹ️ <b>راهنما</b>\n\n"
            "این نسخه برای محاسبه مقادیر بتن و میلگرد، "
            "Rebar Schedule و Cut List است.\n\n"
            "کنترل کامل آیین‌نامه‌ای باید از لایه "
            "Code Checks انجام شود.",
            parse_mode="HTML",
            reply_markup=back_kb(lang)
        )

    return await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang)
    )


# ============================================================
# Text Router
# ============================================================

async def text_router(
    update,
    context
):

    if context.user_data.get(
        "await_fy"
    ):

        try:

            fy = float(
                update.message.text
                .strip()
                .replace(",", ".")
            )

            if fy <= 0:
                raise ValueError

        except Exception:

            return await update.message.reply_text(
                "❌ fy نامعتبر است."
            )

        context.user_data.update(
            fy=fy,
            grade="Custom",
            await_fy=False,
        )

        return await update.message.reply_text(
            TEXT["fa"]["welcome"]
            + "\n\n"
            + project_header(
                context.user_data
            ),
            parse_mode="HTML",
            reply_markup=main_menu("fa")
        )

    return await receive(
        update,
        context
    )


# ============================================================
# Error Handler
# ============================================================

async def error_handler(
    update,
    context
):

    logger.exception(
        "Unhandled bot error",
        exc_info=context.error
    )


# ============================================================
# Main
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
            text_router
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "Concrete Structure Bot v2.0"
    )

    print(
        f"Webhook: {webhook_url}"
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
