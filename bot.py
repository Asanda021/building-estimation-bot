import os
import threading
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
    column_rectangular,
    column_round,
    beam,
    tie_beam,
    wall_concrete,
    stair_slab,
    roof_slab,
)


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


TEXTS = {
    "fa": {
        "welcome": (
            "🏗️ <b>اسکلت بتنی</b>\n\n"
            "عضو موردنظر را انتخاب کنید:"
        ),
        "home": "🏠 صفحه اصلی",
        "back": "⬅️ بازگشت",
        "cancel": "❌ لغو",
        "help": "ℹ️ راهنما",
        "settings": "⚙️ تنظیمات",
        "summary": "📊 خلاصه پروژه",
        "rebar": "🔩 آرماتور",
        "cut": "✂️ Cut List",
        "new": "➕ عضو جدید",
        "invalid": (
            "❌ مقدار واردشده صحیح نیست.\n"
            "دوباره وارد کنید."
        ),
        "guide": (
            "ℹ️ <b>راهنما</b>\n\n"
            "این ربات برای برآورد مقادیر "
            "اسکلت بتنی ساخته شده است.\n\n"
            "ابعاد و آرماتورها بر اساس "
            "اطلاعات واردشده محاسبه می‌شوند.\n\n"
            "⚠️ نتایج جایگزین نقشه و محاسبات "
            "سازه‌ای مهندس محاسب نیستند."
        ),
        "lang": "🌐 زبان ربات را انتخاب کنید:",
    },

    "en": {
        "welcome": (
            "🏗️ <b>Concrete Frame</b>\n\n"
            "Choose a member:"
        ),
        "home": "🏠 Main Menu",
        "back": "⬅️ Back",
        "cancel": "❌ Cancel",
        "help": "ℹ️ Help",
        "settings": "⚙️ Settings",
        "summary": "📊 Project Summary",
        "rebar": "🔩 Rebar",
        "cut": "✂️ Cut List",
        "new": "➕ New Member",
        "invalid": (
            "❌ Invalid value.\n"
            "Please try again."
        ),
        "guide": (
            "ℹ️ <b>Guide</b>\n\n"
            "This bot estimates concrete-frame "
            "quantities from entered dimensions "
            "and reinforcement.\n\n"
            "⚠️ Results do not replace structural "
            "drawings or engineer calculations."
        ),
        "lang": "🌐 Choose bot language:",
    },
}


ROOF_COEFF = {
    "foam": 0.18,
    "clay": 0.20,
    "double": 0.23,
    "kromit": 0.18,
    "kompozit": 0.15,
    "steeldeck": 0.15,
    "slab": 0.20,
    "waffle": 0.20,
}


STEPS = {

    "iso": [
        ("count", "تعداد پی‌ها", "int"),
        ("L", "طول پی (m)", "float"),
        ("W", "عرض پی (m)", "float"),
        ("T", "ضخامت پی (m)", "float"),
        ("bd", "قطر میلگرد پایین (mm)", "int"),
        ("bs", "فاصله میلگرد پایین (mm)", "int"),
        ("td", "قطر میلگرد بالا (mm)", "int"),
        ("ts", "فاصله میلگرد بالا (mm)", "int"),
        ("pl", "طول پدستال (m)", "float"),
        ("pw", "عرض پدستال (m)", "float"),
        ("ph", "ارتفاع پدستال (m)", "float"),
        ("sd", "قطر میلگرد انتظار (mm)", "int"),
        ("sc", "تعداد انتظار هر پی", "int"),
        ("sl", "طول هر انتظار (m)", "float"),
    ],

    "strip": [
        ("count", "تعداد نوار", "int"),
        ("L", "طول نوار (m)", "float"),
        ("W", "عرض پی (m)", "float"),
        ("T", "ضخامت پی (m)", "float"),
        ("ld", "قطر طولی پایین (mm)", "int"),
        ("lc", "تعداد طولی پایین", "int"),
        ("td", "قطر عرضی پایین (mm)", "int"),
        ("ts", "فاصله عرضی پایین (mm)", "int"),
        ("tld", "قطر طولی بالا (mm)", "int"),
        ("tlc", "تعداد طولی بالا", "int"),
        ("ttd", "قطر عرضی بالا (mm)", "int"),
        ("tts", "فاصله عرضی بالا (mm)", "int"),
    ],

    "raft": [
        ("L", "طول رادیه (m)", "float"),
        ("W", "عرض رادیه (m)", "float"),
        ("T", "ضخامت رادیه (m)", "float"),
        ("bxd", "قطر X پایین (mm)", "int"),
        ("bxs", "فاصله X پایین (mm)", "int"),
        ("byd", "قطر Y پایین (mm)", "int"),
        ("bys", "فاصله Y پایین (mm)", "int"),
        ("txd", "قطر X بالا (mm)", "int"),
        ("txs", "فاصله X بالا (mm)", "int"),
        ("tyd", "قطر Y بالا (mm)", "int"),
        ("tys", "فاصله Y بالا (mm)", "int"),
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
    ],

    "column_round": [
        ("count", "تعداد ستون گرد", "int"),
        ("D", "قطر ستون (m)", "float"),
        ("H", "ارتفاع ستون (m)", "float"),
        ("ld", "قطر میلگرد طولی (mm)", "int"),
        ("lc", "تعداد طولی هر ستون", "int"),
        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),
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
    ],

    "wall": [
        ("L", "طول دیوار (m)", "float"),
        ("H", "ارتفاع دیوار (m)", "float"),
        ("T", "ضخامت دیوار (m)", "float"),
        ("vd", "قطر قائم (mm)", "int"),
        ("vs", "فاصله قائم (mm)", "int"),
        ("hd", "قطر افقی (mm)", "int"),
        ("hs", "فاصله افقی (mm)", "int"),
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
        ("riser", "ارتفاع کف‌پله (m)", "float"),
        ("tread", "کف‌پله (m)", "float"),
    ],

    "roof": [
        ("area", "مساحت سقف (m²)", "float"),
        (
            "dia",
            "قطر میلگرد حرارتی (mm)",
            "int"
        ),
        (
            "kgm2",
            "مصرف میلگرد (kg/m²)\n"
            "برای صفر فقط بتن محاسبه می‌شود",
            "float"
        ),
    ],
}


MENU = {

    "fa": [
        [
            ("🧱 فونداسیون", "foundation_menu"),
            ("🔗 شناژ و کلاف", "tie_menu"),
        ],
        [
            ("🏛️ ستون‌ها", "column_menu"),
            ("📐 تیرها", "beam_menu"),
        ],
        [
            ("🏠 سقف‌ها", "roof_menu"),
            ("🪜 راه‌پله", "stair_menu"),
        ],
        [
            ("🧱 دیوارها", "wall_menu"),
        ],
        [
            ("📊 خلاصه پروژه", "summary"),
            ("⚙️ تنظیمات", "settings"),
        ],
        [
            ("ℹ️ راهنما", "help"),
        ],
    ],

    "en": [
        [
            ("🧱 Foundation", "foundation_menu"),
            ("🔗 Tie Beams", "tie_menu"),
        ],
        [
            ("🏛️ Columns", "column_menu"),
            ("📐 Beams", "beam_menu"),
        ],
        [
            ("🏠 Roofs", "roof_menu"),
            ("🪜 Stairs", "stair_menu"),
        ],
        [
            ("🧱 Walls", "wall_menu"),
        ],
        [
            ("📊 Project Summary", "summary"),
            ("⚙️ Settings", "settings"),
        ],
        [
            ("ℹ️ Help", "help"),
        ],
    ],
}


def make_keyboard(rows):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text,
                    callback_data=data
                )
                for text, data in row
            ]
            for row in rows
        ]
    )


def main_menu(lang):
    return make_keyboard(MENU[lang])


def language_menu():
    return make_keyboard(
        [
            [
                ("🇮🇷 فارسی", "lang_fa"),
                ("🇬🇧 English", "lang_en"),
            ]
        ]
    )


def foundation_menu(lang):
    return make_keyboard(
        [
            [
                ("⬛ پی منفرد", "foundation_iso"),
                ("▬ پی نواری", "foundation_strip"),
            ],
            [
                ("▰ پی گسترده (رادیه)", "foundation_raft"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def column_menu(lang):
    return make_keyboard(
        [
            [
                ("▯ ستون مستطیلی", "column_rect"),
                ("◯ ستون گرد", "column_round"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def beam_menu(lang):
    return make_keyboard(
        [
            [
                ("📐 تیر اصلی", "beam_main"),
                ("📏 تیر فرعی", "beam_secondary"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def tie_menu(lang):
    return make_keyboard(
        [
            [
                ("🔗 شناژ", "tie_beam"),
                ("⛓️ کلاف", "tie_beam"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def roof_menu(lang):
    return make_keyboard(
        [
            [
                ("🟦 تیرچه یونولیتی", "roof_foam"),
                ("🟫 تیرچه سفالی", "roof_clay"),
            ],
            [
                ("🟪 تیرچه دوبل", "roof_double"),
                ("🔩 کرومیت", "roof_kromit"),
            ],
            [
                ("🏗️ کامپوزیت", "roof_kompozit"),
                ("🔩 عرشه فولادی", "roof_steeldeck"),
            ],
            [
                ("⬜ دال بتنی", "roof_slab"),
                ("🔳 وافل", "roof_waffle"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def wall_menu(lang):
    return make_keyboard(
        [
            [
                ("🏢 دیوار برشی", "wall_shear"),
            ],
            [
                ("🧱 دیوار حائل", "wall_retaining"),
            ],
            [
                ("⬅️ بازگشت", "home"),
            ],
        ]
    )


def step_keyboard(lang):
    return make_keyboard(
        [
            [
                ("⬅️ مرحله قبل", "prev"),
                ("❌ لغو", "cancel"),
            ],
            [
                (
                    "🏠 صفحه اصلی"
                    if lang == "fa"
                    else "🏠 Main Menu",
                    "home"
                ),
            ],
        ]
    )


def result_keyboard(lang):
    return make_keyboard(
        [
            [
                ("🔩 آرماتور", "show_rebar"),
                ("✂️ Cut List", "show_cut"),
            ],
            [
                ("➕ عضو جدید", "new_member"),
            ],
            [
                (
                    "🏠 صفحه اصلی"
                    if lang == "fa"
                    else "🏠 Main Menu",
                    "home"
                ),
            ],
        ]
    )


def prompt_text(
    lang,
    label,
    step_number,
    total_steps
):
    if lang == "fa":
        return (
            f"📐 <b>{label}</b>\n\n"
            "مقدار را وارد کنید:\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 مرحله <b>{step_number}</b> "
            f"از <b>{total_steps}</b>"
        )

    return (
        f"📐 <b>{label}</b>\n\n"
        "Enter value:\n\n"
        "━━━━━━━━━━━━━━\n"
        f"📍 <b>Stage {step_number}</b> "
        f"of <b>{total_steps}</b>"
    )


def summary_text(
    kind,
    result,
    lang
):
    names = {
        "iso": "⬛ پی منفرد",
        "strip": "▬ پی نواری",
        "raft": "▰ پی گسترده (رادیه)",
        "column_rect": "▯ ستون مستطیلی",
        "column_round": "◯ ستون گرد",
        "beam": "📐 تیر",
        "tie": "🔗 شناژ / کلاف",
        "wall": "🧱 دیوار",
        "stair": "🪜 راه‌پله",
        "roof": "🏠 سقف",
    }

    concrete = result.get(
        "total_concrete_m3",
        result.get("concrete_m3", 0)
    )

    rebar = result.get(
        "total_rebar_kg",
        0
    )

    if lang == "fa":
        return (
            "✅ <b>محاسبه انجام شد</b>\n\n"
            f"<b>{names.get(kind, kind)}</b>\n\n"
            "┌────────────────────┐\n"
            f"│ 🧱 بتن : {concrete:>9.2f} m³ │\n"
            f"│ ⚖️ میلگرد: {rebar:>7.1f} kg │\n"
            "└────────────────────┘\n\n"
            "🔎 جزئیات آرماتور و Cut List "
            "با دکمه‌های زیر در دسترس است."
        )

    return (
        "✅ <b>Calculation completed</b>\n\n"
        f"<b>{names.get(kind, kind)}</b>\n\n"
        "┌────────────────────┐\n"
        f"│ 🧱 Concrete : {concrete:>7.2f} m³ │\n"
        f"│ ⚖️ Rebar : {rebar:>9.1f} kg │\n"
        "└────────────────────┘"
    )


def rebar_text(
    details,
    lang
):
    if not details:
        return (
            "🔩 <b>آرماتور</b>\n\n"
            "میلگردی برای این عضو ثبت نشده است."
        )

    text = "🔩 <b>تفکیک آرماتور</b>\n\n"
    text += (
        "```\n"
        "Φ قطر   قطعه   طول(m)   وزن(kg)   شاخه\n"
    )

    for item in details:
        text += (
            f"Φ{item['diameter_mm']:<5}"
            f"{item['piece_count']:<8}"
            f"{item['length_m']:<10.2f}"
            f"{item['weight_kg']:<11.1f}"
            f"{item['bars_12m']}\n"
        )

    text += "```"

    return text


def cut_text(
    details,
    lang
):
    if not details:
        return (
            "✂️ <b>Cut List</b>\n\n"
            "موردی وجود ندارد."
        )

    text = "✂️ <b>Cut List</b>\n\n"

    for item in details:

        text += (
            f"<b>Φ{item['diameter_mm']}</b> — "
            f"{item['bars_12m']} شاخه ۱۲ متری\n"
        )

        plans = item.get(
            "cut_plan",
            []
        )

        for index, plan in enumerate(
            plans[:12],
            1
        ):
            pieces = " + ".join(
                f"{value:.2f}"
                for value in plan["pieces"]
            )

            text += (
                f"{index:02d}) "
                f"{pieces} = "
                f"{plan['used_m']:.2f} m"
                f" | پرت "
                f"{plan['waste_m']:.2f}\n"
            )

        if len(plans) > 12:
            text += (
                f"... و {len(plans)-12} "
                "شاخه دیگر\n"
            )

        text += "\n"

    return text


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        TEXTS["fa"]["lang"],
        parse_mode="HTML",
        reply_markup=language_menu()
    )


async def change_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    lang = query.data[-2:]

    context.user_data.clear()
    context.user_data["lang"] = lang

    await query.edit_message_text(
        TEXTS[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang)
    )


async def show_page(
    query,
    text,
    keyboard
):
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def begin_wizard(
    update,
    context,
    kind
):
    query = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    context.user_data["kind"] = kind
    context.user_data["step_index"] = 0
    context.user_data["values"] = {}
    context.user_data["history"] = []

    steps = STEPS[kind]

    await show_page(
        query,
        prompt_text(
            lang,
            steps[0][1],
            1,
            len(steps)
        ),
        step_keyboard(lang)
    )


def calculate(
    kind,
    values
):

    if kind == "iso":

        result = isolated_footing(
            values["count"],
            values["L"],
            values["W"],
            values["T"],
            0,
            0,
            0,
            values["bd"],
            values["bs"],
            values["td"],
            values["ts"],
            50,
            0,
            values["pl"],
            values["pw"],
            values["ph"],
        )

        starter_dia = values["sd"]

        pieces = (
            [values["sl"]]
            *
            (
                int(values["count"])
                *
                int(values["sc"])
            )
        )

        optimize = optimize_12m_bars(
            pieces
        )

        existing = next(
            (
                item
                for item in result[
                    "rebar_details"
                ]
                if item[
                    "diameter_mm"
                ] == starter_dia
            ),
            None
        )

        if existing:

            all_pieces = (
                existing[
                    "piece_lengths_m"
                ]
                + pieces
            )

            optimize = optimize_12m_bars(
                all_pieces
            )

            existing[
                "piece_lengths_m"
            ] = all_pieces

            existing[
                "piece_count"
            ] = len(all_pieces)

            existing[
                "length_m"
            ] = sum(all_pieces)

            existing[
                "weight_kg"
            ] = (
                sum(all_pieces)
                * starter_dia
                * starter_dia
                / 162
            )

            existing[
                "bars_12m"
            ] = optimize[
                "stock_bars"
            ]

            existing[
                "waste_m"
            ] = optimize[
                "waste_m"
            ]

            existing[
                "cut_plan"
            ] = optimize[
                "plans"
            ]

        else:

            result[
                "rebar_details"
            ].append(
                {
                    "diameter_mm":
                        starter_dia,
                    "piece_lengths_m":
                        pieces,
                    "piece_count":
                        len(pieces),
                    "length_m":
                        sum(pieces),
                    "weight_kg":
                        (
                            sum(pieces)
                            * starter_dia
                            * starter_dia
                            / 162
                        ),
                    "bars_12m":
                        optimize[
                            "stock_bars"
                        ],
                    "waste_m":
                        optimize[
                            "waste_m"
                        ],
                    "cut_plan":
                        optimize[
                            "plans"
                        ],
                    "description":
                        "میلگرد انتظار",
                }
            )

        result[
            "total_rebar_kg"
        ] = sum(
            item["weight_kg"]
            for item in result[
                "rebar_details"
            ]
        )

        return result

    if kind == "strip":

        return strip_footing(
            values["count"],
            values["L"],
            values["W"],
            values["T"],
            0,
            0,
            0,
            values["ld"],
            values["lc"],
            values["td"],
            values["ts"],
            values["tld"],
            values["tlc"],
            values["ttd"],
            values["tts"],
        )

    if kind == "raft":

        return raft_foundation(
            values["L"],
            values["W"],
            values["T"],
            0,
            0,
            0,
            values["bxd"],
            values["bxs"],
            values["byd"],
            values["bys"],
            values["txd"],
            values["txs"],
            values["tyd"],
            values["tys"],
        )

    if kind == "column_rect":

        return column_rectangular(
            values["count"],
            values["W"],
            values["D"],
            values["H"],
            values["ld"],
            values["lc"],
            values["sd"],
            values["ss"],
        )

    if kind == "column_round":

        return column_round(
            values["count"],
            values["D"],
            values["H"],
            values["ld"],
            values["lc"],
            values["sd"],
            values["ss"],
        )

    if kind == "beam":

        return beam(
            values["count"],
            values["L"],
            values["W"],
            values["H"],
            values["bd"],
            values["bc"],
            values["td"],
            values["tc"],
            values["sd"],
            values["ss"],
        )

    if kind == "tie":

        return tie_beam(
            values["count"],
            values["L"],
            values["W"],
            values["H"],
            values["ld"],
            values["lc"],
            values["sd"],
            values["ss"],
        )

    if kind == "wall":

        return wall_concrete(
            values["L"],
            values["H"],
            values["T"],
            values["vd"],
            values["vs"],
            values["hd"],
            values["hs"],
        )

    if kind == "stair":

        return stair_slab(
            values["L"],
            values["W"],
            values["T"],
            values["md"],
            values["ms"],
            values["dd"],
            values["ds"],
            values["steps"],
            values["riser"],
            values["tread"],
        )

    if kind == "roof":

        return roof_slab(
            values["area"],
            values["coeff"],
            values["dia"],
            values["kgm2"],
        )

    raise ValueError(
        "Unknown member type"
    )


async def receive_message(
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

    index = context.user_data.get(
        "step_index"
    )

    if kind is None or index is None:
        return

    raw = update.message.text.strip()

    try:

        data_type = STEPS[
            kind
        ][index][2]

        if data_type == "int":

            value = int(
                float(
                    raw.replace(",", ".")
                )
            )

        else:

            value = float(
                raw.replace(",", ".")
            )

        if value < 0:
            raise ValueError

    except Exception:

        await update.message.reply_text(
            TEXTS[lang]["invalid"],
            reply_markup=step_keyboard(lang)
        )

        return

    key = STEPS[
        kind
    ][index][0]

    context.user_data[
        "values"
    ][key] = value

    context.user_data[
        "history"
    ].append(index)

    index += 1

    if index < len(STEPS[kind]):

        context.user_data[
            "step_index"
        ] = index

        await update.message.reply_text(
            prompt_text(
                lang,
                STEPS[kind][index][1],
                index + 1,
                len(STEPS[kind])
            ),
            parse_mode="HTML",
            reply_markup=step_keyboard(lang)
        )

        return

    try:

        result = calculate(
            kind,
            context.user_data[
                "values"
            ]
        )

        context.user_data[
            "result"
        ] = result

        context.user_data[
            "step_index"
        ] = None

        await update.message.reply_text(
            summary_text(
                kind,
                result,
                lang
            ),
            parse_mode="HTML",
            reply_markup=result_keyboard(lang)
        )

    except Exception as error:

        await update.message.reply_text(
            f"❌ خطا در محاسبه:\n{error}",
            reply_markup=step_keyboard(lang)
        )


async def button_handler(
    update,
    context
):
    query = update.callback_query

    await query.answer()

    data = query.data

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    if data.startswith("lang_"):
        return await change_language(
            update,
            context
        )

    if data == "home":

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        return await show_page(
            query,
            TEXTS[lang]["welcome"],
            main_menu(lang)
        )

    if data == "help":

        return await show_page(
            query,
            TEXTS[lang]["guide"],
            make_keyboard(
                [
                    [
                        (
                            "⬅️ بازگشت",
                            "home"
                        )
                    ]
                ]
            )
        )

    if data == "settings":

        return await show_page(
            query,
            (
                "⚙️ <b>تنظیمات</b>\n\n"
                "🌐 برای تغییر زبان "
                "از /start استفاده کنید."
            ),
            make_keyboard(
                [
                    [
                        (
                            "⬅️ بازگشت",
                            "home"
                        )
                    ]
                ]
            )
        )

    if data == "summary":

        return await show_page(
            query,
            (
                "📊 <b>خلاصه پروژه</b>\n\n"
                "جمع‌بندی خودکار کل پروژه "
                "در نسخه بعدی تکمیل می‌شود."
            ),
            make_keyboard(
                [
                    [
                        (
                            "⬅️ بازگشت",
                            "home"
                        )
                    ]
                ]
            )
        )

    if data == "foundation_menu":

        return await show_page(
            query,
            "🧱 <b>فونداسیون</b>",
            foundation_menu(lang)
        )

    if data == "column_menu":

        return await show_page(
            query,
            "🏛️ <b>ستون‌ها</b>",
            column_menu(lang)
        )

    if data == "beam_menu":

        return await show_page(
            query,
            "📐 <b>تیرها</b>",
            beam_menu(lang)
        )

    if data == "tie_menu":

        return await show_page(
            query,
            "🔗 <b>شناژ و کلاف</b>",
            tie_menu(lang)
        )

    if data == "roof_menu":

        return await show_page(
            query,
            "🏠 <b>سقف‌ها</b>",
            roof_menu(lang)
        )

    if data == "wall_menu":

        return await show_page(
            query,
            "🧱 <b>دیوارها</b>",
            wall_menu(lang)
        )

    if data == "stair_menu":

        return await begin_wizard(
            update,
            context,
            "stair"
        )

    mapping = {

        "foundation_iso":
            "iso",

        "foundation_strip":
            "strip",

        "foundation_raft":
            "raft",

        "column_rect":
            "column_rect",

        "column_round":
            "column_round",

        "beam_main":
            "beam",

        "beam_secondary":
            "beam",

        "tie_beam":
            "tie",

        "wall_shear":
            "wall",

        "wall_retaining":
            "wall",
    }

    if data in mapping:

        return await begin_wizard(
            update,
            context,
            mapping[data]
        )

    if data.startswith("roof_"):

        roof_type = data.replace(
            "roof_",
            ""
        )

        context.user_data[
            "roof_kind"
        ] = roof_type

        context.user_data[
            "kind"
        ] = "roof"

        context.user_data[
            "step_index"
        ] = 0

        context.user_data[
            "values"
        ] = {
            "coeff":
                ROOF_COEFF[roof_type]
        }

        context.user_data[
            "history"
        ] = []

        return await show_page(
            query,
            prompt_text(
                lang,
                "مساحت سقف (m²)",
                1,
                3
            ),
            step_keyboard(lang)
        )

    if data == "prev":

        kind = context.user_data.get(
            "kind"
        )

        index = context.user_data.get(
            "step_index"
        )

        if (
            kind
            and index is not None
            and index > 0
        ):

            index -= 1

            context.user_data[
                "step_index"
            ] = index

            key = STEPS[
                kind
            ][index][0]

            context.user_data[
                "values"
            ].pop(
                key,
                None
            )

            if context.user_data.get(
                "history"
            ):
                context.user_data[
                    "history"
                ].pop()

            return await show_page(
                query,
                prompt_text(
                    lang,
                    STEPS[kind][index][1],
                    index + 1,
                    len(STEPS[kind])
                ),
                step_keyboard(lang)
            )

        return await show_page(
            query,
            TEXTS[lang]["welcome"],
            main_menu(lang)
        )

    if data == "cancel":

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        return await show_page(
            query,
            TEXTS[lang]["welcome"],
            main_menu(lang)
        )

    if data == "new_member":

        return await show_page(
            query,
            TEXTS[lang]["welcome"],
            main_menu(lang)
        )

    if data == "show_rebar":

        result = context.user_data.get(
            "result",
            {}
        )

        return await show_page(
            query,
            rebar_text(
                result.get(
                    "rebar_details",
                    []
                ),
                lang
            ),
            make_keyboard(
                [
                    [
                        (
                            "✂️ Cut List",
                            "show_cut"
                        ),
                        (
                            "⬅️ نتیجه",
                            "back_result"
                        ),
                    ],
                    [
                        (
                            "🏠 صفحه اصلی",
                            "home"
                        )
                    ],
                ]
            )
        )

    if data == "show_cut":

        result = context.user_data.get(
            "result",
            {}
        )

        return await show_page(
            query,
            cut_text(
                result.get(
                    "rebar_details",
                    []
                ),
                lang
            ),
            make_keyboard(
                [
                    [
                        (
                            "🔩 آرماتور",
                            "show_rebar"
                        ),
                        (
                            "⬅️ نتیجه",
                            "back_result"
                        ),
                    ],
                    [
                        (
                            "🏠 صفحه اصلی",
                            "home"
                        )
                    ],
                ]
            )
        )

    if data == "back_result":

        return await show_page(
            query,
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
            result_keyboard(lang)
        )


def main():

    token = os.environ.get(
        "BOT_TOKEN"
    )

    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

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
            change_language,
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
            filters.TEXT
            & ~filters.COMMAND,
            receive_message
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
