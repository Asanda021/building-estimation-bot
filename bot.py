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
    roof_mesh,
    roof_slab,
    optimize_12m_bars,
    equivalent_rebar_count,
    normalize_standard,
    rebar_grade_yield_mpa,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# ENVIRONMENT
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get(
    "RENDER_EXTERNAL_URL", ""
).rstrip("/")


# =========================================================
# STANDARDS
# =========================================================

STANDARDS = {
    "iran": {
        "fa": "🇮🇷 مبحث ۹ ایران",
        "ar": "🇮🇷 الكود الإيراني - الفصل 9",
        "en": "🇮🇷 Iran - Chapter 9",
        "zh": "🇮🇷 伊朗规范 - 第9章",
    },
    "aci318": {
        "fa": "🇺🇸 ACI 318",
        "ar": "🇺🇸 ACI 318",
        "en": "🇺🇸 ACI 318",
        "zh": "🇺🇸 ACI 318",
    },
    "eurocode2": {
        "fa": "🇪🇺 Eurocode 2",
        "ar": "🇪🇺 Eurocode 2",
        "en": "🇪🇺 Eurocode 2",
        "zh": "🇪🇺 Eurocode 2",
    },
}


CONCRETE_OPTIONS = [
    25,
    30,
    35,
    40,
]


REBAR_OPTIONS_IRAN = [
    ("A2", 300),
    ("A3", 400),
    ("A4", 500),
]

REBAR_OPTIONS_ACI = [
    ("Grade 40", 280),
    ("Grade 60", 420),
]

REBAR_OPTIONS_EC2 = [
    ("B400", 400),
    ("B500", 500),
]


# =========================================================
# TRANSLATIONS
# =========================================================

TEXT = {

    "fa": {
        "language": "🌐 زبان را انتخاب کنید:",
        "welcome": "🏗️ <b>اسکلت بتنی</b>\n\nعضو موردنظر را انتخاب کنید:",
        "standard": "📚 <b>استاندارد محاسباتی</b>\n\nاستاندارد پروژه را انتخاب کنید:",
        "concrete": "🧱 <b>مقاومت بتن</b>\n\nمقاومت فشاری بتن پروژه را انتخاب کنید:",
        "rebar_grade": "🔩 <b>گرید میلگرد</b>\n\nگرید میلگرد پروژه را انتخاب کنید:",
        "project_ready": "✅ مشخصات پروژه ثبت شد.",
        "invalid": "❌ مقدار واردشده معتبر نیست.\n\nدوباره وارد کنید.",
        "calc_error": "❌ خطا در محاسبه:\n<code>{}</code>",
        "back": "🔙 بازگشت",
        "home": "🏠 صفحه اصلی",
        "cancel": "❌ لغو",
        "previous": "⬅️ مرحله قبل",
        "calculate": "✅ محاسبه",
        "edit": "✏️ ویرایش",
        "new_member": "➕ عضو جدید",
        "show_rebar": "🔩 جزئیات میلگرد",
        "show_cut": "✂️ Cut List",
        "result": "🏗️ نتیجه محاسبه",
        "review": "📋 <b>اطلاعات واردشده</b>",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "summary": "📊 خلاصه پروژه",
        "language": "🌐 زبان",
        "standard_setting": "📚 استاندارد محاسباتی",
        "materials": "🧱 مشخصات مصالح",
        "equivalency": "🔄 معادل‌سازی میلگرد",
        "enter_value": "مقدار را وارد کنید:",
        "step": "مرحله",
        "of": "از",
        "no_project": "هنوز عضوی برای پروژه ثبت نشده است.",
        "project_cleared": "پروژه جدید آماده شد.",
        "area_equivalent": "از نظر سطح مقطع",
        "equivalent": "معادل است",
        "not_equivalent": "معادل نیست",
        "engineering_warning": (
            "⚠️ این کنترل فقط معادل‌سازی سطح مقطع است؛ "
            "کنترل کامل طراحی، فاصله، حداقل/حداکثر آرماتور، "
            "طول مهاری و جزئیات لرزه‌ای باید جداگانه انجام شود."
        ),
        "current_count": "تعداد میلگرد فعلی",
        "current_dia": "قطر میلگرد فعلی (mm)",
        "replacement_dia": "قطر میلگرد جایگزین (mm)",
        "project_standard": "استاندارد",
        "project_concrete": "بتن",
        "project_rebar": "میلگرد",
        "member_saved": "عضو به پروژه اضافه شد.",
    },

    "ar": {
        "language": "🌐 اختر اللغة:",
        "welcome": "🏗️ <b>الهيكل الخرساني</b>\n\nاختر العنصر الإنشائي:",
        "standard": "📚 <b>الكود الحسابي</b>\n\nاختر الكود:",
        "concrete": "🧱 <b>مقاومة الخرسانة</b>\n\nاختر مقاومة ضغط الخرسانة:",
        "rebar_grade": "🔩 <b>درجة حديد التسليح</b>\n\nاختر درجة الحديد:",
        "project_ready": "✅ تم حفظ مواصفات المشروع.",
        "invalid": "❌ القيمة غير صحيحة.\n\nحاول مرة أخرى.",
        "calc_error": "❌ خطأ في الحساب:\n<code>{}</code>",
        "back": "🔙 رجوع",
        "home": "🏠 الرئيسية",
        "cancel": "❌ إلغاء",
        "previous": "⬅️ السابق",
        "calculate": "✅ حساب",
        "edit": "✏️ تعديل",
        "new_member": "➕ عنصر جديد",
        "show_rebar": "🔩 تفاصيل التسليح",
        "show_cut": "✂️ Cut List",
        "result": "🏗️ نتيجة الحساب",
        "review": "📋 <b>البيانات المدخلة</b>",
        "settings": "⚙️ الإعدادات",
        "help": "ℹ️ المساعدة",
        "summary": "📊 ملخص المشروع",
        "language": "🌐 اللغة",
        "standard_setting": "📚 الكود الحسابي",
        "materials": "🧱 مواد المشروع",
        "equivalency": "🔄 معادلة حديد التسليح",
        "enter_value": "أدخل القيمة:",
        "step": "الخطوة",
        "of": "من",
        "no_project": "لا توجد عناصر مسجلة في المشروع.",
        "project_cleared": "تم تجهيز مشروع جديد.",
        "area_equivalent": "من ناحية مساحة المقطع",
        "equivalent": "مكافئ",
        "not_equivalent": "غير مكافئ",
        "engineering_warning": (
            "⚠️ هذه المقارنة لمساحة التسليح فقط؛ "
            "ويجب فحص التباعد والحد الأدنى والأقصى وطول التثبيت "
            "والتفاصيل الزلزالية بشكل منفصل."
        ),
        "current_count": "عدد القضبان الحالية",
        "current_dia": "قطر القضيب الحالي (mm)",
        "replacement_dia": "قطر القضيب البديل (mm)",
        "project_standard": "الكود",
        "project_concrete": "الخرسانة",
        "project_rebar": "التسليح",
        "member_saved": "تمت إضافة العنصر إلى المشروع.",
    },

    "en": {
        "language": "🌐 Choose language:",
        "welcome": "🏗️ <b>Concrete Frame</b>\n\nChoose a structural member:",
        "standard": "📚 <b>Design Standard</b>\n\nChoose the project standard:",
        "concrete": "🧱 <b>Concrete Strength</b>\n\nChoose concrete compressive strength:",
        "rebar_grade": "🔩 <b>Rebar Grade</b>\n\nChoose the project rebar grade:",
        "project_ready": "✅ Project specifications saved.",
        "invalid": "❌ Invalid value.\n\nPlease try again.",
        "calc_error": "❌ Calculation error:\n<code>{}</code>",
        "back": "🔙 Back",
        "home": "🏠 Main Menu",
        "cancel": "❌ Cancel",
        "previous": "⬅️ Previous",
        "calculate": "✅ Calculate",
        "edit": "✏️ Edit",
        "new_member": "➕ New Member",
        "show_rebar": "🔩 Rebar Details",
        "show_cut": "✂️ Cut List",
        "result": "🏗️ Calculation Result",
        "review": "📋 <b>Entered Data</b>",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "summary": "📊 Project Summary",
        "language": "🌐 Language",
        "standard_setting": "📚 Design Standard",
        "materials": "🧱 Project Materials",
        "equivalency": "🔄 Rebar Equivalency",
        "enter_value": "Enter value:",
        "step": "Step",
        "of": "of",
        "no_project": "No members have been added to the project.",
        "project_cleared": "New project is ready.",
        "area_equivalent": "By cross-sectional area",
        "equivalent": "Equivalent",
        "not_equivalent": "Not equivalent",
        "engineering_warning": (
            "⚠️ This is an area-only equivalency check. "
            "Spacing, minimum/maximum reinforcement, development length "
            "and seismic detailing must be checked separately."
        ),
        "current_count": "Current bar count",
        "current_dia": "Current bar diameter (mm)",
        "replacement_dia": "Replacement bar diameter (mm)",
        "project_standard": "Standard",
        "project_concrete": "Concrete",
        "project_rebar": "Rebar",
        "member_saved": "Member added to project.",
    },

    "zh": {
        "language": "🌐 选择语言：",
        "welcome": "🏗️ <b>混凝土结构</b>\n\n请选择结构构件：",
        "standard": "📚 <b>计算规范</b>\n\n请选择项目规范：",
        "concrete": "🧱 <b>混凝土强度</b>\n\n请选择项目混凝土强度：",
        "rebar_grade": "🔩 <b>钢筋等级</b>\n\n请选择项目钢筋等级：",
        "project_ready": "✅ 项目参数已保存。",
        "invalid": "❌ 输入值无效。\n\n请重新输入。",
        "calc_error": "❌ 计算错误：\n<code>{}</code>",
        "back": "🔙 返回",
        "home": "🏠 主菜单",
        "cancel": "❌ 取消",
        "previous": "⬅️ 上一步",
        "calculate": "✅ 计算",
        "edit": "✏️ 编辑",
        "new_member": "➕ 新构件",
        "show_rebar": "🔩 钢筋明细",
        "show_cut": "✂️ Cut List",
        "result": "🏗️ 计算结果",
        "review": "📋 <b>输入数据</b>",
        "settings": "⚙️ 设置",
        "help": "ℹ️ 帮助",
        "summary": "📊 项目汇总",
        "language": "🌐 语言",
        "standard_setting": "📚 计算规范",
        "materials": "🧱 项目材料",
        "equivalency": "🔄 钢筋等效",
        "enter_value": "请输入数值：",
        "step": "步骤",
        "of": "/",
        "no_project": "项目中还没有构件。",
        "project_cleared": "新项目已准备好。",
        "area_equivalent": "按截面积",
        "equivalent": "等效",
        "not_equivalent": "不等效",
        "engineering_warning": (
            "⚠️ 此结果仅检查钢筋截面积等效；"
            "间距、最小/最大配筋、锚固长度和抗震构造需另行检查。"
        ),
        "current_count": "现有钢筋数量",
        "current_dia": "现有钢筋直径 (mm)",
        "replacement_dia": "替换钢筋直径 (mm)",
        "project_standard": "规范",
        "project_concrete": "混凝土",
        "project_rebar": "钢筋",
        "member_saved": "构件已加入项目。",
    },
}


# =========================================================
# MEMBER NAMES
# =========================================================

MEMBER_NAMES = {
    "iso": {
        "fa": "⬛ پی منفرد",
        "ar": "⬛ قاعدة منفردة",
        "en": "⬛ Isolated Footing",
        "zh": "⬛ 独立基础",
    },
    "strip": {
        "fa": "▬ پی نواری",
        "ar": "▬ قاعدة شريطية",
        "en": "▬ Strip Footing",
        "zh": "▬ 条形基础",
    },
    "raft": {
        "fa": "▰ پی گسترده / رادیه",
        "ar": "▰ اللبشة",
        "en": "▰ Raft Foundation",
        "zh": "▰ 筏板基础",
    },
    "column_rect": {
        "fa": "▯ ستون مربعی / مستطیلی",
        "ar": "▯ عمود مستطيل",
        "en": "▯ Rectangular Column",
        "zh": "▯ 矩形柱",
    },
    "column_round": {
        "fa": "◯ ستون گرد",
        "ar": "◯ عمود دائري",
        "en": "◯ Circular Column",
        "zh": "◯ 圆柱",
    },
    "beam": {
        "fa": "📐 تیر",
        "ar": "📐 كمرة",
        "en": "📐 Beam",
        "zh": "📐 梁",
    },
    "tie": {
        "fa": "🔗 شناژ / کلاف",
        "ar": "🔗 ميدة / رابط",
        "en": "🔗 Tie Beam",
        "zh": "🔗 系梁",
    },
    "wall": {
        "fa": "🧱 دیوار",
        "ar": "🧱 جدار",
        "en": "🧱 Wall",
        "zh": "🧱 墙",
    },
    "stair": {
        "fa": "🪜 راه‌پله",
        "ar": "🪜 درج",
        "en": "🪜 Stair",
        "zh": "🪜 楼梯",
    },
    "roof": {
        "fa": "🏠 سقف",
        "ar": "🏠 سقف",
        "en": "🏠 Roof",
        "zh": "🏠 楼板",
    },
}


# =========================================================
# ROOF TYPES
# =========================================================

ROOF_TYPES = {
    "foam": {
        "name": {
            "fa": "🟦 تیرچه یونولیتی",
            "ar": "🟦 بلوك فلين",
            "en": "🟦 EPS Joist",
            "zh": "🟦 EPS 板",
        },
        "coeff": 0.18,
    },
    "clay": {
        "name": {
            "fa": "🟫 تیرچه سفالی",
            "ar": "🟫 بلوك فخاري",
            "en": "🟫 Clay Joist",
            "zh": "🟫 陶土块楼板",
        },
        "coeff": 0.20,
    },
    "double": {
        "name": {
            "fa": "🟪 تیرچه دوبل",
            "ar": "🟪 جوائز مزدوجة",
            "en": "🟪 Double Joist",
            "zh": "🟪 双梁板",
        },
        "coeff": 0.23,
    },
    "kromit": {
        "name": {
            "fa": "🔩 کرومیت",
            "ar": "🔩 كروميت",
            "en": "🔩 Kromit",
            "zh": "🔩 Kromit",
        },
        "coeff": 0.18,
    },
    "composite": {
        "name": {
            "fa": "🏗️ کامپوزیت",
            "ar": "🏗️ مركب",
            "en": "🏗️ Composite",
            "zh": "🏗️ 组合楼板",
        },
        "coeff": 0.15,
    },
    "steeldeck": {
        "name": {
            "fa": "🔩 عرشه فولادی",
            "ar": "🔩 سطح فولاذي",
            "en": "🔩 Steel Deck",
            "zh": "🔩 钢承板",
        },
        "coeff": 0.15,
    },
    "slab": {
        "name": {
            "fa": "⬜ دال بتنی",
            "ar": "⬜ بلاطة خرسانية",
            "en": "⬜ Concrete Slab",
            "zh": "⬜ 混凝土板",
        },
        "coeff": 0.20,
    },
    "waffle": {
        "name": {
            "fa": "🔳 وافل",
            "ar": "🔳 وافل",
            "en": "🔳 Waffle",
            "zh": "🔳 华夫板",
        },
        "coeff": 0.20,
    },
}


# =========================================================
# REBAR DIAMETERS
# =========================================================

DIAMETERS = [
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    25,
    28,
    32,
]


def diameter_buttons(prefix):
    rows = []

    row = []

    for dia in DIAMETERS:
        row.append(
            (
                f"Φ{dia}",
                f"{prefix}{dia}",
            )
        )

        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return rows


# =========================================================
# KEYBOARD
# =========================================================

def kb(rows):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text,
                    callback_data=data,
                )
                for text, data in row
            ]
            for row in rows
        ]
    )


def language_keyboard():
    return kb(
        [
            [
                ("🇮🇷 فارسی", "lang_fa"),
                ("🇸🇦 العربية", "lang_ar"),
            ],
            [
                ("🇬🇧 English", "lang_en"),
                ("🇨🇳 中文", "lang_zh"),
            ],
        ]
    )


def standard_keyboard(lang):
    return kb(
        [
            [
                (
                    STANDARDS["iran"][lang],
                    "std_iran",
                )
            ],
            [
                (
                    STANDARDS["aci318"][lang],
                    "std_aci",
                ),
            ],
            [
                (
                    STANDARDS["eurocode2"][lang],
                    "std_ec2",
                )
            ],
        ]
    )


def concrete_keyboard(lang):
    return kb(
        [
            [
                (f"C{v}", f"fc_{v}")
                for v in CONCRETE_OPTIONS
            ],
            [
                (
                    TEXT[lang]["back"],
                    "setup_back_standard",
                )
            ],
        ]
    )


def rebar_grade_keyboard(lang, standard):
    if standard == "aci318":
        options = REBAR_OPTIONS_ACI
    elif standard == "eurocode2":
        options = REBAR_OPTIONS_EC2
    else:
        options = REBAR_OPTIONS_IRAN

    rows = []

    row = []

    for grade, fy in options:
        row.append(
            (
                f"🔩 {grade} ({fy} MPa)",
                f"grade_{grade.replace(' ', '_')}",
            )
        )

        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return kb(rows)


def main_menu(lang):
    if lang == "fa":
        return kb(
            [
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
                    ("🔄 معادل‌سازی میلگرد", "equiv"),
                ],
                [
                    ("🌐 زبان", "language"),
                    ("⚙️ تنظیمات", "settings"),
                ],
                [
                    ("ℹ️ راهنما", "help"),
                ],
            ]
        )

    if lang == "ar":
        return kb(
            [
                [
                    ("🧱 الأساسات", "foundation"),
                    ("🏛️ الأعمدة", "columns"),
                ],
                [
                    ("📐 الكمرات", "beams"),
                    ("🏠 الأسقف", "roofs"),
                ],
                [
                    ("🪜 الدرج", "stairs"),
                    ("🔗 الميدات", "ties"),
                ],
                [
                    ("🧱 الجدران", "walls"),
                ],
                [
                    ("📊 ملخص المشروع", "summary"),
                ],
                [
                    ("🔄 معادلة التسليح", "equiv"),
                ],
                [
                    ("🌐 اللغة", "language"),
                    ("⚙️ الإعدادات", "settings"),
                ],
                [
                    ("ℹ️ المساعدة", "help"),
                ],
            ]
        )

    if lang == "zh":
        return kb(
            [
                [
                    ("🧱 基础", "foundation"),
                    ("🏛️ 柱", "columns"),
                ],
                [
                    ("📐 梁", "beams"),
                    ("🏠 楼板", "roofs"),
                ],
                [
                    ("🪜 楼梯", "stairs"),
                    ("🔗 系梁", "ties"),
                ],
                [
                    ("🧱 墙", "walls"),
                ],
                [
                    ("📊 项目汇总", "summary"),
                ],
                [
                    ("🔄 钢筋等效", "equiv"),
                ],
                [
                    ("🌐 语言", "language"),
                    ("⚙️ 设置", "settings"),
                ],
                [
                    ("ℹ️ 帮助", "help"),
                ],
            ]
        )

    return kb(
        [
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
                ("📊 Project Summary", "summary"),
            ],
            [
                ("🔄 Rebar Equivalency", "equiv"),
            ],
            [
                ("🌐 Language", "language"),
                ("⚙️ Settings", "settings"),
            ],
            [
                ("ℹ️ Help", "help"),
            ],
        ]
    )


def back_kb(lang, callback="home"):
    return kb(
        [
            [
                (TEXT[lang]["back"], callback),
                (TEXT[lang]["home"], "home"),
            ]
        ]
    )


def step_kb(lang):
    return kb(
        [
            [
                (
                    TEXT[lang]["previous"],
                    "prev",
                ),
                (
                    TEXT[lang]["cancel"],
                    "cancel",
                ),
            ],
            [
                (
                    TEXT[lang]["home"],
                    "home",
                )
            ],
        ]
    )


def review_kb(lang):
    return kb(
        [
            [
                (
                    TEXT[lang]["calculate"],
                    "do_calculate",
                )
            ],
            [
                (
                    TEXT[lang]["edit"],
                    "edit_member",
                ),
                (
                    TEXT[lang]["cancel"],
                    "cancel",
                ),
            ],
        ]
    )


def result_kb(lang):
    return kb(
        [
            [
                (
                    TEXT[lang]["show_rebar"],
                    "show_rebar",
                ),
                (
                    TEXT[lang]["show_cut"],
                    "show_cut",
                ),
            ],
            [
                (
                    TEXT[lang]["new_member"],
                    "new_member",
                )
            ],
            [
                (
                    TEXT[lang]["summary"],
                    "summary",
                ),
            ],
            [
                (
                    TEXT[lang]["home"],
                    "home",
                )
            ],
        ]
    )


def section_kb(
    lang,
    items,
    parent="home",
):
    rows = [
        [
            (
                text,
                data,
            )
        ]
        for text, data in items
    ]

    rows.append(
        [
            (
                TEXT[lang]["back"],
                parent,
            )
        ]
    )

    return kb(rows)


# =========================================================
# NUMBER PARSER
# =========================================================

def normalize_number(text):
    value = str(text).strip()

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )

    value = value.translate(
        translation
    )

    value = value.replace(
        ",",
        ".",
    )

    # Persian-style decimal slash
    if value.count("/") == 1 and "." not in value:
        value = value.replace(
            "/",
            ".",
        )

    return value


def parse_number(text, integer=False):
    value = normalize_number(text)

    number = float(value)

    if number < 0:
        raise ValueError(
            "Negative values are not allowed."
        )

    if integer:
        if number != int(number):
            raise ValueError(
                "Integer required."
            )

        return int(number)

    return number


# =========================================================
# PROJECT DATA
# =========================================================

def project_standard(context):
    return context.user_data.get(
        "standard",
        "iran",
    )


def project_fc(context):
    return float(
        context.user_data.get(
            "fc",
            25,
        )
    )


def project_fy(context):
    return float(
        context.user_data.get(
            "fy",
            400,
        )
    )


def project_grade(context):
    return context.user_data.get(
        "rebar_grade",
        "A3",
    )


def project_ready(context):
    return (
        context.user_data.get(
            "standard"
        )
        is not None
        and context.user_data.get(
            "fc"
        )
        is not None
        and context.user_data.get(
            "rebar_grade"
        )
        is not None
    )


# =========================================================
# PROMPTS
# =========================================================

def prompt_text(
    lang,
    label,
    index,
    total,
):
    return (
        f"📐 <b>{escape(label)}</b>\n\n"
        f"{TEXT[lang]['enter_value']}\n\n"
        "━━━━━━━━━━━━━━\n"
        f"📍 {TEXT[lang]['step']} "
        f"<b>{index}</b> "
        f"{TEXT[lang]['of']} "
        f"<b>{total}</b>"
    )


# =========================================================
# FIELD DEFINITIONS
# =========================================================

STEPS = {

    "iso": [
        (
            "count",
            {
                "fa": "تعداد پی",
                "ar": "عدد القواعد",
                "en": "Footing count",
                "zh": "基础数量",
            },
            "int",
        ),
        (
            "L",
            {
                "fa": "طول پی (m)",
                "ar": "طول القاعدة (m)",
                "en": "Footing length (m)",
                "zh": "基础长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض پی (m)",
                "ar": "عرض القاعدة (m)",
                "en": "Footing width (m)",
                "zh": "基础宽度 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت پی (m)",
                "ar": "سماكة القاعدة (m)",
                "en": "Footing thickness (m)",
                "zh": "基础厚度 (m)",
            },
            "float",
        ),
        (
            "leanL",
            {
                "fa": "طول بتن مگر (m)",
                "ar": "طول الخرسانة النظافة (m)",
                "en": "Lean concrete length (m)",
                "zh": "垫层长度 (m)",
            },
            "float",
        ),
        (
            "leanW",
            {
                "fa": "عرض بتن مگر (m)",
                "ar": "عرض الخرسانة النظافة (m)",
                "en": "Lean concrete width (m)",
                "zh": "垫层宽度 (m)",
            },
            "float",
        ),
        (
            "leanT",
            {
                "fa": "ضخامت بتن مگر (m)",
                "ar": "سماكة الخرسانة النظافة (m)",
                "en": "Lean concrete thickness (m)",
                "zh": "垫层厚度 (m)",
            },
            "float",
        ),
        (
            "bd",
            {
                "fa": "قطر میلگرد پایین (mm)",
                "ar": "قطر التسليح السفلي (mm)",
                "en": "Bottom rebar diameter (mm)",
                "zh": "底部钢筋直径 (mm)",
            },
            "diameter",
        ),
        (
            "bs",
            {
                "fa": "فاصله میلگرد پایین (mm)",
                "ar": "تباعد التسليح السفلي (mm)",
                "en": "Bottom rebar spacing (mm)",
                "zh": "底部钢筋间距 (mm)",
            },
            "spacing",
        ),
        (
            "td",
            {
                "fa": "قطر میلگرد بالا؛ اگر ندارد 0",
                "ar": "قطر التسليح العلوي؛ 0 إذا لا يوجد",
                "en": "Top rebar diameter; 0 if none",
                "zh": "顶部钢筋直径；无则输入0",
            },
            "diameter_optional",
        ),
        (
            "ts",
            {
                "fa": "فاصله میلگرد بالا؛ اگر ندارد 0",
                "ar": "تباعد التسليح العلوي؛ 0 إذا لا يوجد",
                "en": "Top rebar spacing; 0 if none",
                "zh": "顶部钢筋间距；无则输入0",
            },
            "spacing_optional",
        ),
        (
            "pl",
            {
                "fa": "طول پدستال (m)؛ اگر ندارد 0",
                "ar": "طول القاعدة الرأسية (m)؛ 0 إذا لا يوجد",
                "en": "Pedestal length (m); 0 if none",
                "zh": "柱墩长度 (m)；无则0",
            },
            "float",
        ),
        (
            "pw",
            {
                "fa": "عرض پدستال (m)؛ اگر ندارد 0",
                "ar": "عرض القاعدة الرأسية (m)؛ 0 إذا لا يوجد",
                "en": "Pedestal width (m); 0 if none",
                "zh": "柱墩宽度 (m)；无则0",
            },
            "float",
        ),
        (
            "ph",
            {
                "fa": "ارتفاع پدستال (m)؛ اگر ندارد 0",
                "ar": "ارتفاع القاعدة الرأسية (m)؛ 0 إذا لا يوجد",
                "en": "Pedestal height (m); 0 if none",
                "zh": "柱墩高度 (m)；无则0",
            },
            "float",
        ),
    ],

    "strip": [
        (
            "count",
            {
                "fa": "تعداد نوار",
                "ar": "عدد الشرائح",
                "en": "Strip count",
                "zh": "条形基础数量",
            },
            "int",
        ),
        (
            "L",
            {
                "fa": "طول نوار (m)",
                "ar": "طول الشريط (m)",
                "en": "Strip length (m)",
                "zh": "长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض پی (m)",
                "ar": "عرض القاعدة (m)",
                "en": "Footing width (m)",
                "zh": "基础宽度 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت پی (m)",
                "ar": "السماكة (m)",
                "en": "Thickness (m)",
                "zh": "厚度 (m)",
            },
            "float",
        ),
        (
            "leanL",
            {
                "fa": "طول مگر (m)",
                "ar": "طول النظافة (m)",
                "en": "Lean concrete length (m)",
                "zh": "垫层长度 (m)",
            },
            "float",
        ),
        (
            "leanW",
            {
                "fa": "عرض مگر (m)",
                "ar": "عرض النظافة (m)",
                "en": "Lean concrete width (m)",
                "zh": "垫层宽度 (m)",
            },
            "float",
        ),
        (
            "leanT",
            {
                "fa": "ضخامت مگر (m)",
                "ar": "سماكة النظافة (m)",
                "en": "Lean concrete thickness (m)",
                "zh": "垫层厚度 (m)",
            },
            "float",
        ),
        (
            "ld",
            {
                "fa": "قطر طولی پایین (mm)",
                "ar": "قطر التسليح الطولي السفلي",
                "en": "Bottom longitudinal diameter",
                "zh": "底部纵筋直径",
            },
            "diameter",
        ),
        (
            "lc",
            {
                "fa": "تعداد طولی پایین",
                "ar": "عدد التسليح الطولي السفلي",
                "en": "Bottom longitudinal count",
                "zh": "底部纵筋数量",
            },
            "int",
        ),
        (
            "td",
            {
                "fa": "قطر عرضی پایین (mm)",
                "ar": "قطر التسليح العرضي السفلي",
                "en": "Bottom transverse diameter",
                "zh": "底部横筋直径",
            },
            "diameter",
        ),
        (
            "ts",
            {
                "fa": "فاصله عرضی پایین (mm)",
                "ar": "تباعد التسليح العرضي السفلي",
                "en": "Bottom transverse spacing",
                "zh": "底部横筋间距",
            },
            "spacing",
        ),
        (
            "tld",
            {
                "fa": "قطر طولی بالا؛ اگر ندارد 0",
                "ar": "قطر الطولي العلوي؛ 0 إذا لا يوجد",
                "en": "Top longitudinal diameter; 0 if none",
                "zh": "顶部纵筋直径；无则0",
            },
            "diameter_optional",
        ),
        (
            "tlc",
            {
                "fa": "تعداد طولی بالا؛ اگر ندارد 0",
                "ar": "عدد الطولي العلوي؛ 0 إذا لا يوجد",
                "en": "Top longitudinal count; 0 if none",
                "zh": "顶部纵筋数量；无则0",
            },
            "int",
        ),
        (
            "ttd",
            {
                "fa": "قطر عرضی بالا؛ اگر ندارد 0",
                "ar": "قطر العرضي العلوي؛ 0 إذا لا يوجد",
                "en": "Top transverse diameter; 0 if none",
                "zh": "顶部横筋直径；无则0",
            },
            "diameter_optional",
        ),
        (
            "tts",
            {
                "fa": "فاصله عرضی بالا؛ اگر ندارد 0",
                "ar": "تباعد العرضي العلوي؛ 0 إذا لا يوجد",
                "en": "Top transverse spacing; 0 if none",
                "zh": "顶部横筋间距；无则0",
            },
            "spacing_optional",
        ),
    ],

    "raft": [
        (
            "L",
            {
                "fa": "طول رادیه (m)",
                "ar": "طول اللبشة (m)",
                "en": "Raft length (m)",
                "zh": "筏板长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض رادیه (m)",
                "ar": "عرض اللبشة (m)",
                "en": "Raft width (m)",
                "zh": "筏板宽度 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت رادیه (m)",
                "ar": "سماكة اللبشة (m)",
                "en": "Raft thickness (m)",
                "zh": "筏板厚度 (m)",
            },
            "float",
        ),
        (
            "leanL",
            {
                "fa": "طول مگر (m)",
                "ar": "طول النظافة (m)",
                "en": "Lean concrete length (m)",
                "zh": "垫层长度 (m)",
            },
            "float",
        ),
        (
            "leanW",
            {
                "fa": "عرض مگر (m)",
                "ar": "عرض النظافة (m)",
                "en": "Lean concrete width (m)",
                "zh": "垫层宽度 (m)",
            },
            "float",
        ),
        (
            "leanT",
            {
                "fa": "ضخامت مگر (m)",
                "ar": "سماكة النظافة (m)",
                "en": "Lean concrete thickness (m)",
                "zh": "垫层厚度 (m)",
            },
            "float",
        ),
        (
            "bxd",
            {
                "fa": "قطر X پایین (mm)",
                "ar": "قطر X السفلي",
                "en": "Bottom X diameter",
                "zh": "底部X钢筋直径",
            },
            "diameter",
        ),
        (
            "bxs",
            {
                "fa": "فاصله X پایین (mm)",
                "ar": "تباعد X السفلي",
                "en": "Bottom X spacing",
                "zh": "底部X间距",
            },
            "spacing",
        ),
        (
            "byd",
            {
                "fa": "قطر Y پایین (mm)",
                "ar": "قطر Y السفلي",
                "en": "Bottom Y diameter",
                "zh": "底部Y钢筋直径",
            },
            "diameter",
        ),
        (
            "bys",
            {
                "fa": "فاصله Y پایین (mm)",
                "ar": "تباعد Y السفلي",
                "en": "Bottom Y spacing",
                "zh": "底部Y间距",
            },
            "spacing",
        ),
        (
            "txd",
            {
                "fa": "قطر X بالا؛ اگر ندارد 0",
                "ar": "قطر X العلوي؛ 0 إذا لا يوجد",
                "en": "Top X diameter; 0 if none",
                "zh": "顶部X直径；无则0",
            },
            "diameter_optional",
        ),
        (
            "txs",
            {
                "fa": "فاصله X بالا",
                "ar": "تباعد X العلوي",
                "en": "Top X spacing",
                "zh": "顶部X间距",
            },
            "spacing_optional",
        ),
        (
            "tyd",
            {
                "fa": "قطر Y بالا؛ اگر ندارد 0",
                "ar": "قطر Y العلوي؛ 0 إذا لا يوجد",
                "en": "Top Y diameter; 0 if none",
                "zh": "顶部Y直径；无则0",
            },
            "diameter_optional",
        ),
        (
            "tys",
            {
                "fa": "فاصله Y بالا",
                "ar": "تباعد Y العلوي",
                "en": "Top Y spacing",
                "zh": "顶部Y间距",
            },
            "spacing_optional",
        ),
    ],

    "column_rect": [
        (
            "count",
            {
                "fa": "تعداد ستون",
                "ar": "عدد الأعمدة",
                "en": "Column count",
                "zh": "柱数量",
            },
            "int",
        ),
        (
            "W",
            {
                "fa": "عرض ستون (m)",
                "ar": "عرض العمود (m)",
                "en": "Column width (m)",
                "zh": "柱宽 (m)",
            },
            "float",
        ),
        (
            "D",
            {
                "fa": "عمق ستون (m)",
                "ar": "عمق العمود (m)",
                "en": "Column depth (m)",
                "zh": "柱深 (m)",
            },
            "float",
        ),
        (
            "H",
            {
                "fa": "ارتفاع ستون (m)",
                "ar": "ارتفاع العمود (m)",
                "en": "Column height (m)",
                "zh": "柱高 (m)",
            },
            "float",
        ),
        (
            "ld",
            {
                "fa": "قطر میلگرد طولی (mm)",
                "ar": "قطر التسليح الطولي",
                "en": "Longitudinal diameter",
                "zh": "纵筋直径",
            },
            "diameter",
        ),
        (
            "lc",
            {
                "fa": "تعداد میلگرد طولی هر ستون",
                "ar": "عدد التسليح الطولي لكل عمود",
                "en": "Longitudinal bars per column",
                "zh": "每柱纵筋数量",
            },
            "int",
        ),
        (
            "sd",
            {
                "fa": "قطر خاموت (mm)",
                "ar": "قطر الكانات",
                "en": "Stirrup diameter",
                "zh": "箍筋直径",
            },
            "diameter",
        ),
        (
            "ss",
            {
                "fa": "فاصله خاموت (mm)",
                "ar": "تباعد الكانات",
                "en": "Stirrup spacing",
                "zh": "箍筋间距",
            },
            "spacing",
        ),
    ],

    "column_round": [
        (
            "count",
            {
                "fa": "تعداد ستون گرد",
                "ar": "عدد الأعمدة الدائرية",
                "en": "Circular column count",
                "zh": "圆柱数量",
            },
            "int",
        ),
        (
            "D",
            {
                "fa": "قطر ستون (m)",
                "ar": "قطر العمود (m)",
                "en": "Column diameter (m)",
                "zh": "柱直径 (m)",
            },
            "float",
        ),
        (
            "H",
            {
                "fa": "ارتفاع ستون (m)",
                "ar": "ارتفاع العمود (m)",
                "en": "Column height (m)",
                "zh": "柱高 (m)",
            },
            "float",
        ),
        (
            "ld",
            {
                "fa": "قطر میلگرد طولی (mm)",
                "ar": "قطر التسليح الطولي",
                "en": "Longitudinal diameter",
                "zh": "纵筋直径",
            },
            "diameter",
        ),
        (
            "lc",
            {
                "fa": "تعداد میلگرد طولی هر ستون",
                "ar": "عدد التسليح الطولي",
                "en": "Longitudinal bar count",
                "zh": "纵筋数量",
            },
            "int",
        ),
        (
            "sd",
            {
                "fa": "قطر خاموت (mm)",
                "ar": "قطر الكانات",
                "en": "Stirrup diameter",
                "zh": "箍筋直径",
            },
            "diameter",
        ),
        (
            "ss",
            {
                "fa": "فاصله خاموت (mm)",
                "ar": "تباعد الكانات",
                "en": "Stirrup spacing",
                "zh": "箍筋间距",
            },
            "spacing",
        ),
    ],

    "beam": [
        (
            "count",
            {
                "fa": "تعداد تیر",
                "ar": "عدد الكمرات",
                "en": "Beam count",
                "zh": "梁数量",
            },
            "int",
        ),
        (
            "L",
            {
                "fa": "طول تیر (m)",
                "ar": "طول الكمرة (m)",
                "en": "Beam length (m)",
                "zh": "梁长 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض تیر (m)",
                "ar": "عرض الكمرة (m)",
                "en": "Beam width (m)",
                "zh": "梁宽 (m)",
            },
            "float",
        ),
        (
            "H",
            {
                "fa": "ارتفاع تیر (m)",
                "ar": "ارتفاع الكمرة (m)",
                "en": "Beam height (m)",
                "zh": "梁高 (m)",
            },
            "float",
        ),
        (
            "bd",
            {
                "fa": "قطر میلگرد پایین (mm)",
                "ar": "قطر التسليح السفلي",
                "en": "Bottom rebar diameter",
                "zh": "底部钢筋直径",
            },
            "diameter",
        ),
        (
            "bc",
            {
                "fa": "تعداد میلگرد پایین",
                "ar": "عدد التسليح السفلي",
                "en": "Bottom rebar count",
                "zh": "底部钢筋数量",
            },
            "int",
        ),
        (
            "td",
            {
                "fa": "قطر میلگرد بالا (mm)",
                "ar": "قطر التسليح العلوي",
                "en": "Top rebar diameter",
                "zh": "顶部钢筋直径",
            },
            "diameter",
        ),
        (
            "tc",
            {
                "fa": "تعداد میلگرد بالا",
                "ar": "عدد التسليح العلوي",
                "en": "Top rebar count",
                "zh": "顶部钢筋数量",
            },
            "int",
        ),
        (
            "sd",
            {
                "fa": "قطر خاموت (mm)",
                "ar": "قطر الكانات",
                "en": "Stirrup diameter",
                "zh": "箍筋直径",
            },
            "diameter",
        ),
        (
            "ss",
            {
                "fa": "فاصله خاموت (mm)",
                "ar": "تباعد الكانات",
                "en": "Stirrup spacing",
                "zh": "箍筋间距",
            },
            "spacing",
        ),
    ],

    "tie": [
        (
            "count",
            {
                "fa": "تعداد شناژ/کلاف",
                "ar": "عدد الميدات",
                "en": "Tie beam count",
                "zh": "系梁数量",
            },
            "int",
        ),
        (
            "L",
            {
                "fa": "طول (m)",
                "ar": "الطول (m)",
                "en": "Length (m)",
                "zh": "长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض (m)",
                "ar": "العرض (m)",
                "en": "Width (m)",
                "zh": "宽度 (m)",
            },
            "float",
        ),
        (
            "H",
            {
                "fa": "ارتفاع (m)",
                "ar": "الارتفاع (m)",
                "en": "Height (m)",
                "zh": "高度 (m)",
            },
            "float",
        ),
        (
            "ld",
            {
                "fa": "قطر میلگرد طولی (mm)",
                "ar": "قطر التسليح الطولي",
                "en": "Longitudinal diameter",
                "zh": "纵筋直径",
            },
            "diameter",
        ),
        (
            "lc",
            {
                "fa": "تعداد میلگرد طولی",
                "ar": "عدد التسليح الطولي",
                "en": "Longitudinal count",
                "zh": "纵筋数量",
            },
            "int",
        ),
        (
            "sd",
            {
                "fa": "قطر خاموت (mm)",
                "ar": "قطر الكانات",
                "en": "Stirrup diameter",
                "zh": "箍筋直径",
            },
            "diameter",
        ),
        (
            "ss",
            {
                "fa": "فاصله خاموت (mm)",
                "ar": "تباعد الكانات",
                "en": "Stirrup spacing",
                "zh": "箍筋间距",
            },
            "spacing",
        ),
    ],

    "wall": [
        (
            "L",
            {
                "fa": "طول دیوار (m)",
                "ar": "طول الجدار (m)",
                "en": "Wall length (m)",
                "zh": "墙长 (m)",
            },
            "float",
        ),
        (
            "H",
            {
                "fa": "ارتفاع دیوار (m)",
                "ar": "ارتفاع الجدار (m)",
                "en": "Wall height (m)",
                "zh": "墙高 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت دیوار (m)",
                "ar": "سماكة الجدار (m)",
                "en": "Wall thickness (m)",
                "zh": "墙厚 (m)",
            },
            "float",
        ),
        (
            "vd",
            {
                "fa": "قطر میلگرد قائم (mm)",
                "ar": "قطر التسليح الرأسي",
                "en": "Vertical rebar diameter",
                "zh": "竖向钢筋直径",
            },
            "diameter",
        ),
        (
            "vs",
            {
                "fa": "فاصله میلگرد قائم (mm)",
                "ar": "تباعد التسليح الرأسي",
                "en": "Vertical rebar spacing",
                "zh": "竖向钢筋间距",
            },
            "spacing",
        ),
        (
            "hd",
            {
                "fa": "قطر میلگرد افقی (mm)",
                "ar": "قطر التسليح الأفقي",
                "en": "Horizontal rebar diameter",
                "zh": "水平钢筋直径",
            },
            "diameter",
        ),
        (
            "hs",
            {
                "fa": "فاصله میلگرد افقی (mm)",
                "ar": "تباعد التسليح الأفقي",
                "en": "Horizontal rebar spacing",
                "zh": "水平钢筋间距",
            },
            "spacing",
        ),
    ],

    "stair": [
        (
            "L",
            {
                "fa": "طول شیب/دال (m)",
                "ar": "طول البلاطة (m)",
                "en": "Slab/slope length (m)",
                "zh": "楼梯板长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض راه‌پله (m)",
                "ar": "عرض الدرج (m)",
                "en": "Stair width (m)",
                "zh": "楼梯宽度 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت دال (m)",
                "ar": "سماكة البلاطة (m)",
                "en": "Slab thickness (m)",
                "zh": "板厚 (m)",
            },
            "float",
        ),
        (
            "md",
            {
                "fa": "قطر میلگرد اصلی (mm)",
                "ar": "قطر التسليح الرئيسي",
                "en": "Main rebar diameter",
                "zh": "主筋直径",
            },
            "diameter",
        ),
        (
            "ms",
            {
                "fa": "فاصله میلگرد اصلی (mm)",
                "ar": "تباعد التسليح الرئيسي",
                "en": "Main rebar spacing",
                "zh": "主筋间距",
            },
            "spacing",
        ),
        (
            "dd",
            {
                "fa": "قطر میلگرد توزیعی (mm)",
                "ar": "قطر التسليح التوزيعي",
                "en": "Distribution rebar diameter",
                "zh": "分布筋直径",
            },
            "diameter",
        ),
        (
            "ds",
            {
                "fa": "فاصله میلگرد توزیعی (mm)",
                "ar": "تباعد التسليح التوزيعي",
                "en": "Distribution rebar spacing",
                "zh": "分布筋间距",
            },
            "spacing",
        ),
        (
            "steps",
            {
                "fa": "تعداد پله",
                "ar": "عدد الدرجات",
                "en": "Step count",
                "zh": "踏步数量",
            },
            "int",
        ),
        (
            "riser",
            {
                "fa": "ارتفاع رایزر (m)",
                "ar": "ارتفاع القائمة (m)",
                "en": "Riser height (m)",
                "zh": "踢面高度 (m)",
            },
            "float",
        ),
        (
            "tread",
            {
                "fa": "کف پله (m)",
                "ar": "عرض النائمة (m)",
                "en": "Tread (m)",
                "zh": "踏步宽度 (m)",
            },
            "float",
        ),
    ],

    "roof": [
        (
            "L",
            {
                "fa": "طول سقف (m)",
                "ar": "طول السقف (m)",
                "en": "Roof length (m)",
                "zh": "楼板长度 (m)",
            },
            "float",
        ),
        (
            "W",
            {
                "fa": "عرض سقف (m)",
                "ar": "عرض السقف (m)",
                "en": "Roof width (m)",
                "zh": "楼板宽度 (m)",
            },
            "float",
        ),
        (
            "T",
            {
                "fa": "ضخامت سقف (m)",
                "ar": "سماكة السقف (m)",
                "en": "Roof thickness (m)",
                "zh": "楼板厚度 (m)",
            },
            "float",
        ),
        (
            "dia",
            {
                "fa": "قطر شبکه حرارتی (mm)",
                "ar": "قطر شبكة التسليح (mm)",
                "en": "Thermal mesh diameter (mm)",
                "zh": "温度筋直径 (mm)",
            },
            "diameter",
        ),
        (
            "spacing",
            {
                "fa": "فاصله شبکه حرارتی (mm)",
                "ar": "تباعد الشبكة (mm)",
                "en": "Thermal mesh spacing (mm)",
                "zh": "温度筋间距 (mm)",
            },
            "spacing",
        ),
    ],
}


# =========================================================
# FIELD LABEL
# =========================================================

def field_label(
    field,
    lang,
):
    return field[1][lang]


# =========================================================
# REVIEW
# =========================================================

def format_value(value):
    if isinstance(value, float):
        return f"{value:g}"

    return str(value)


def review_text(
    kind,
    values,
    lang,
    roof_name=None,
):
    lines = [
        TEXT[lang]["review"],
        "",
    ]

    if kind == "roof" and roof_name:
        lines.append(
            f"🏠 <b>{escape(roof_name)}</b>"
        )
        lines.append("")

    for key, label, typ in STEPS[kind]:

        if key not in values:
            continue

        value = values[key]

        if typ.startswith("diameter"):
            display = f"Φ{int(value)}"

        elif typ.startswith("spacing"):
            display = f"{value:g} mm"

        elif key in {
            "L",
            "W",
            "H",
            "T",
            "leanL",
            "leanW",
            "leanT",
            "pl",
            "pw",
            "ph",
            "riser",
            "tread",
        }:
            display = f"{value:g} m"

        else:
            display = format_value(
                value
            )

        lines.append(
            f"• {escape(label[lang])}: "
            f"<b>{escape(display)}</b>"
        )

    lines += [
        "",
        "━━━━━━━━━━━━━━━━",
        f"📚 {TEXT[lang]['project_standard']}: "
        f"{escape(STANDARDS[project_standard_dummy()][lang])}",
        f"🧱 {TEXT[lang]['project_concrete']}: "
        f"C{project_fc_dummy()}",
        f"🔩 {TEXT[lang]['project_rebar']}: "
        f"{escape(project_grade_dummy())}",
    ]

    return "\n".join(lines)


# Dummy helpers used only before actual context injection.
# They are replaced immediately by review_text_with_context.

def project_standard_dummy():
    return "iran"


def project_fc_dummy():
    return 25


def project_grade_dummy():
    return "A3"


def review_text_with_context(
    context,
    kind,
    values,
    lang,
):
    roof_name = context.user_data.get(
        "roof_name"
    )

    lines = [
        TEXT[lang]["review"],
        "",
    ]

    if kind == "roof" and roof_name:
        lines.append(
            f"🏠 <b>{escape(roof_name)}</b>"
        )
        lines.append("")

    for key, label, typ in STEPS[kind]:

        if key not in values:
            continue

        value = values[key]

        if typ.startswith("diameter"):
            display = f"Φ{int(value)}"

        elif typ.startswith("spacing"):
            display = f"{value:g} mm"

        elif key in {
            "L",
            "W",
            "H",
            "T",
            "leanL",
            "leanW",
            "leanT",
            "pl",
            "pw",
            "ph",
            "riser",
            "tread",
        }:
            display = f"{value:g} m"

        else:
            display = format_value(
                value
            )

        lines.append(
            f"• {escape(label[lang])}: "
            f"<b>{escape(display)}</b>"
        )

    standard = project_standard(
        context
    )

    lines += [
        "",
        "━━━━━━━━━━━━━━━━",
        f"📚 {TEXT[lang]['project_standard']}: "
        f"{escape(STANDARDS[standard][lang])}",
        f"🧱 {TEXT[lang]['project_concrete']}: "
        f"C{project_fc(context):g}",
        f"🔩 {TEXT[lang]['project_rebar']}: "
        f"{escape(project_grade(context))}",
    ]

    return "\n".join(lines)


# =========================================================
# CALCULATION ENGINE CONNECTION
# =========================================================

def calculate(
    context,
    kind,
    values,
):
    standard = project_standard(
        context
    )

    fc = project_fc(
        context
    )

    fy = project_fy(
        context
    )

    if kind == "iso":

        return isolated_footing(
            int(values["count"]),
            values["L"],
            values["W"],
            values["T"],
            values["leanL"],
            values["leanW"],
            values["leanT"],
            int(values["bd"]),
            values["bs"],
            int(values["td"])
            if values["td"] > 0
            else None,
            values["ts"]
            if values["td"] > 0
            and values["ts"] > 0
            else None,

            # Internal cover
            None,

            # Legacy lap_percent is intentionally unused
            0,

            values["pl"],
            values["pw"],
            values["ph"],

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "strip":

        return strip_footing(
            int(values["count"]),
            values["L"],
            values["W"],
            values["T"],
            values["leanL"],
            values["leanW"],
            values["leanT"],
            int(values["ld"]),
            int(values["lc"]),
            int(values["td"]),
            values["ts"],
            int(values["tld"])
            if values["tld"] > 0
            else None,
            int(values["tlc"])
            if values["tlc"] > 0
            else None,
            int(values["ttd"])
            if values["ttd"] > 0
            else None,
            values["tts"]
            if values["ttd"] > 0
            and values["tts"] > 0
            else None,

            None,
            0,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "raft":

        return raft_foundation(
            values["L"],
            values["W"],
            values["T"],
            values["leanL"],
            values["leanW"],
            values["leanT"],
            int(values["bxd"]),
            values["bxs"],
            int(values["byd"]),
            values["bys"],
            int(values["txd"])
            if values["txd"] > 0
            else None,
            values["txs"]
            if values["txd"] > 0
            and values["txs"] > 0
            else None,
            int(values["tyd"])
            if values["tyd"] > 0
            else None,
            values["tys"]
            if values["tyd"] > 0
            and values["tys"] > 0
            else None,

            None,
            0,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "column_rect":

        return column_rectangular(
            int(values["count"]),
            values["W"],
            values["D"],
            values["H"],
            int(values["ld"]),
            int(values["lc"]),
            int(values["sd"]),
            values["ss"],
            None,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "column_round":

        return column_round(
            int(values["count"]),
            values["D"],
            values["H"],
            int(values["ld"]),
            int(values["lc"]),
            int(values["sd"]),
            values["ss"],
            None,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "beam":

        return beam(
            int(values["count"]),
            values["L"],
            values["W"],
            values["H"],
            int(values["bd"]),
            int(values["bc"]),
            int(values["td"]),
            int(values["tc"]),
            int(values["sd"]),
            values["ss"],
            None,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "tie":

        return tie_beam(
            int(values["count"]),
            values["L"],
            values["W"],
            values["H"],
            int(values["ld"]),
            int(values["lc"]),
            int(values["sd"]),
            values["ss"],
            None,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "wall":

        return wall_concrete(
            values["L"],
            values["H"],
            values["T"],
            int(values["vd"]),
            values["vs"],
            int(values["hd"]),
            values["hs"],
            None,

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "stair":

        return stair_slab(
            values["L"],
            values["W"],
            values["T"],
            int(values["md"]),
            values["ms"],
            int(values["dd"]),
            values["ds"],
            int(values["steps"]),
            values["riser"],
            values["tread"],

            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    if kind == "roof":

        roof_type = context.user_data.get(
            "roof_type",
            "slab",
        )

        coeff = ROOF_TYPES[
            roof_type
        ]["coeff"]

        return roof_mesh(
            values["L"],
            values["W"],
            values["T"],
            int(values["dia"]),
            values["spacing"],
            concrete_coeff=coeff,
            cover_mm=None,
            standard=standard,
            concrete_strength_mpa=fc,
            rebar_yield_mpa=fy,
        )

    raise ValueError(
        f"Unknown calculation type: {kind}"
    )


# =========================================================
# RESULT TEXT
# =========================================================

def summary_text(
    kind,
    result,
    lang,
):
    name = MEMBER_NAMES.get(
        kind,
        {},
    ).get(
        lang,
        kind,
    )

    concrete = float(
        result.get(
            "total_concrete_m3",
            result.get(
                "concrete_m3",
                0,
            ),
        )
        or 0
    )

    rebar = float(
        result.get(
            "total_rebar_kg",
            0,
        )
        or 0
    )

    lines = [
        f"🏗️ <b>{TEXT[lang]['result']}</b>",
        "",
        f"<b>{escape(name)}</b>",
        "",
        "<pre>",
        f"بتن کل:       {concrete:.2f} m³",
        f"میلگرد کل:    {rebar:.1f} kg",
    ]

    if kind == "iso":

        lean = float(
            result.get(
                "lean_concrete_m3",
                0,
            )
            or 0
        )

        footing = float(
            result.get(
                "footing_concrete_m3",
                0,
            )
            or 0
        )

        pedestal = float(
            result.get(
                "pedestal_concrete_m3",
                0,
            )
            or 0
        )

        lines += [
            f"بتن مگر:      {lean:.2f} m³",
            f"بتن پی:       {footing:.2f} m³",
            f"پدستال:       {pedestal:.2f} m³",
        ]

    if kind == "roof":

        area = float(
            result.get(
                "area_m2",
                0,
            )
            or 0
        )

        lines.append(
            f"مساحت:        {area:.2f} m²"
        )

    lines += [
        "</pre>",
        "",
        "🔎 جزئیات میلگرد و Cut List را از دکمه‌های زیر ببین.",
    ]

    return "\n".join(
        lines
    )


def rebar_text(
    details,
    lang,
):
    if not details:
        return (
            f"🔩 <b>{TEXT[lang]['show_rebar']}</b>\n\n"
            "میلگردی ثبت نشده است."
        )

    chunks = [
        f"🔩 <b>{TEXT[lang]['show_rebar']}</b>",
        "",
    ]

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
            )
            or 0
        )

        weight = float(
            x.get(
                "weight_kg",
                0,
            )
            or 0
        )

        bars = int(
            x.get(
                "bars_12m",
                0,
            )
        )

        description = escape(
            str(
                x.get(
                    "description",
                    "",
                )
            )
        )

        chunks += [
            "<pre>",
            f"قطر:          Φ{dia}",
            f"تعداد قطعات:  {pieces}",
            f"طول کل:       {length:.2f} m",
            f"وزن:          {weight:.1f} kg",
            f"شاخه ۱۲ متری: {bars}",
            "</pre>",
        ]

        if description:
            chunks.append(
                f"📌 {description}"
            )

        chunks.append(
            "━━━━━━━━━━━━━━━━"
        )

    return "\n".join(
        chunks
    )


def cut_text(
    details,
    lang,
):
    if not details:
        return (
            f"✂️ <b>{TEXT[lang]['show_cut']}</b>\n\n"
            "موردی وجود ندارد."
        )

    chunks = [
        f"✂️ <b>{TEXT[lang]['show_cut']}</b>",
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

        chunks.append(
            f"<b>Φ{dia}</b> — {len(plans)} شاخه ۱۲ متری"
        )

        chunks.append(
            "<pre>"
        )

        for index, plan in enumerate(
            plans,
            1,
        ):

            pieces = plan.get(
                "pieces",
                [],
            )

            used = sum(
                float(v)
                for v in pieces
            )

            # IMPORTANT:
            # Waste is recalculated directly from 12m.
            waste = (
                12.0
                - used
            )

            piece_text = " + ".join(
                f"{float(v):.2f}"
                for v in pieces
            )

            chunks.append(
                f"{index:02d}) "
                f"{piece_text} = "
                f"{used:.2f} m | "
                f"پرت {waste:.2f} m"
            )

        chunks.append(
            "</pre>"
        )

        chunks.append(
            "━━━━━━━━━━━━━━━━"
        )

    return "\n".join(
        chunks
    )


# =========================================================
# PROJECT SUMMARY
# =========================================================

def project_summary_text(
    context,
    lang,
):
    results = context.user_data.get(
        "project_results",
        [],
    )

    if not results:
        return (
            f"📊 <b>{TEXT[lang]['summary']}</b>\n\n"
            f"{TEXT[lang]['no_project']}"
        )

    total_concrete = sum(
        float(
            r.get(
                "total_concrete_m3",
                r.get(
                    "concrete_m3",
                    0,
                ),
            )
            or 0
        )
        for r in results
    )

    total_rebar = sum(
        float(
            r.get(
                "total_rebar_kg",
                0,
            )
            or 0
        )
        for r in results
    )

    lines = [
        f"📊 <b>{TEXT[lang]['summary']}</b>",
        "",
        "<pre>",
        f"تعداد اعضا:    {len(results)}",
        f"بتن کل:        {total_concrete:.2f} m³",
        f"میلگرد کل:     {total_rebar:.1f} kg",
        "</pre>",
        "",
        "━━━━━━━━━━━━━━━━",
    ]

    for index, item in enumerate(
        results,
        1,
    ):

        kind = item.get(
            "kind",
            "",
        )

        result = item.get(
            "result",
            {},
        )

        name = MEMBER_NAMES.get(
            kind,
            {},
        ).get(
            lang,
            kind,
        )

        concrete = float(
            result.get(
                "total_concrete_m3",
                result.get(
                    "concrete_m3",
                    0,
                ),
            )
            or 0
        )

        rebar = float(
            result.get(
                "total_rebar_kg",
                0,
            )
            or 0
        )

        lines += [
            f"{index}. {escape(name)}",
            f"   بتن: {concrete:.2f} m³",
            f"   میلگرد: {rebar:.1f} kg",
            "",
        ]

    return "\n".join(
        lines
    )


# =========================================================
# SETUP FLOW
# =========================================================

async def start_project_setup(
    q,
    context,
):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    await q.edit_message_text(
        TEXT[lang]["standard"],
        parse_mode="HTML",
        reply_markup=standard_keyboard(
            lang
        ),
    )


async def choose_standard(
    update,
    context,
):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    code = q.data

    mapping = {
        "std_iran": "iran",
        "std_aci": "aci318",
        "std_ec2": "eurocode2",
    }

    standard = mapping.get(
        code
    )

    if not standard:
        return

    context.user_data[
        "standard"
    ] = standard

    await q.edit_message_text(
        TEXT[lang]["concrete"],
        parse_mode="HTML",
        reply_markup=concrete_keyboard(
            lang
        ),
    )


async def choose_concrete(
    update,
    context,
):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    fc = int(
        q.data.split(
            "_",
            1,
        )[1]
    )

    context.user_data[
        "fc"
    ] = fc

    standard = project_standard(
        context
    )

    await q.edit_message_text(
        TEXT[lang]["rebar_grade"],
        parse_mode="HTML",
        reply_markup=rebar_grade_keyboard(
            lang,
            standard,
        ),
    )


async def choose_grade(
    update,
    context,
):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    grade = q.data.split(
        "_",
        1,
    )[1].replace(
        "_",
        " ",
    )

    standard = project_standard(
        context
    )

    fy = rebar_grade_yield_mpa(
        grade,
        standard,
    )

    context.user_data[
        "rebar_grade"
    ] = grade

    context.user_data[
        "fy"
    ] = fy

    if "project_results" not in context.user_data:
        context.user_data[
            "project_results"
        ] = []

    await q.edit_message_text(
        (
            f"{TEXT[lang]['project_ready']}\n\n"
            f"📚 {escape(STANDARDS[standard][lang])}\n"
            f"🧱 C{project_fc(context):g}\n"
            f"🔩 {escape(grade)} — {fy:g} MPa"
        ),
        parse_mode="HTML",
        reply_markup=main_menu(
            lang
        ),
    )


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

    if not project_ready(
        context
    ):
        await start_project_setup(
            q,
            context,
        )
        return

    context.user_data[
        "kind"
    ] = kind

    context.user_data[
        "step_index"
    ] = 0

    context.user_data[
        "values"
    ] = {}

    context.user_data[
        "history"
    ] = []

    fields = STEPS[
        kind
    ]

    key, label, typ = fields[0]

    await q.edit_message_text(
        prompt_text(
            lang,
            label[lang],
            1,
            len(fields),
        ),
        parse_mode="HTML",
        reply_markup=step_kb(
            lang
        ),
    )


async def receive(
    update,
    context,
):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    kind = context.user_data.get(
        "kind"
    )

    index = context.user_data.get(
        "step_index"
    )

    if (
        kind is None
        or index is None
    ):
        await update.message.reply_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(
                lang
            ),
        )
        return

    fields = STEPS[
        kind
    ]

    key, label, typ = fields[
        index
    ]

    try:

        if typ == "int":
            value = parse_number(
                update.message.text,
                integer=True,
            )

        elif typ in {
            "diameter",
            "diameter_optional",
            "spacing",
            "spacing_optional",
        }:
            value = parse_number(
                update.message.text,
                integer=True,
            )

        else:
            value = parse_number(
                update.message.text
            )

    except Exception:

        await update.message.reply_text(
            TEXT[lang]["invalid"],
            reply_markup=step_kb(
                lang
            ),
        )

        return

    context.user_data[
        "values"
    ][key] = value

    context.user_data[
        "history"
    ].append(index)

    next_index = index + 1

    if next_index < len(fields):

        context.user_data[
            "step_index"
        ] = next_index

        _, next_label, _ = fields[
            next_index
        ]

        await update.message.reply_text(
            prompt_text(
                lang,
                next_label[lang],
                next_index + 1,
                len(fields),
            ),
            parse_mode="HTML",
            reply_markup=step_kb(
                lang
            ),
        )

        return

    # Review instead of immediate calculation.
    context.user_data[
        "step_index"
    ] = None

    await update.message.reply_text(
        review_text_with_context(
            context,
            kind,
            context.user_data[
                "values"
            ],
            lang,
        ),
        parse_mode="HTML",
        reply_markup=review_kb(
            lang
        ),
    )


# =========================================================
# CALCULATE AFTER REVIEW
# =========================================================

async def do_calculate(
    update,
    context,
):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    kind = context.user_data.get(
        "kind"
    )

    values = context.user_data.get(
        "values",
        {},
    )

    try:

        result = calculate(
            context,
            kind,
            values,
        )

        context.user_data[
            "result"
        ] = result

        project_results = context.user_data.setdefault(
            "project_results",
            [],
        )

        project_results.append(
            {
                "kind": kind,
                "result": result,
            }
        )

        await q.edit_message_text(
            summary_text(
                kind,
                result,
                lang,
            ),
            parse_mode="HTML",
            reply_markup=result_kb(
                lang
            ),
        )

    except Exception as exc:

        logger.exception(
            "Calculation failed"
        )

        await q.edit_message_text(
            TEXT[lang][
                "calc_error"
            ].format(
                escape(
                    str(exc)
                )
            ),
            parse_mode="HTML",
            reply_markup=step_kb(
                lang
            ),
        )


# =========================================================
# EQUIVALENCY
# =========================================================

async def begin_equivalency(
    update,
    context,
):
    q = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    context.user_data[
        "equiv"
    ] = {}

    await q.edit_message_text(
        f"🔄 <b>{TEXT[lang]['equivalency']}</b>\n\n"
        f"1️⃣ {TEXT[lang]['current_count']}\n\n"
        f"{TEXT[lang]['enter_value']}",
        parse_mode="HTML",
        reply_markup=back_kb(
            lang
        ),
    )

    context.user_data[
        "equiv_step"
    ] = 0


async def receive_equivalency(
    update,
    context,
):
    lang = context.user_data.get(
        "lang",
        "fa",
    )

    step = context.user_data.get(
        "equiv_step"
    )

    if step is None:
        return False

    try:

        value = parse_number(
            update.message.text,
            integer=True,
        )

    except Exception:

        await update.message.reply_text(
            TEXT[lang]["invalid"]
        )

        return True

    equiv = context.user_data.setdefault(
        "equiv",
        {},
    )

    if step == 0:

        equiv[
            "count"
        ] = value

        context.user_data[
            "equiv_step"
        ] = 1

        await update.message.reply_text(
            f"2️⃣ {TEXT[lang]['current_dia']}\n\n"
            f"{TEXT[lang]['enter_value']}",
            reply_markup=kb(
                diameter_buttons(
                    "equiv_current_"
                )
                + [
                    [
                        (
                            TEXT[lang]["back"],
                            "home",
                        )
                    ]
                ]
            ),
        )

        return True

    if step == 1:

        equiv[
            "current_dia"
        ] = value

        context.user_data[
            "equiv_step"
        ] = 2

        await update.message.reply_text(
            f"3️⃣ {TEXT[lang]['replacement_dia']}\n\n"
            f"{TEXT[lang]['enter_value']}",
            reply_markup=kb(
                diameter_buttons(
                    "equiv_replace_"
                )
                + [
                    [
                        (
                            TEXT[lang]["back"],
                            "home",
                        )
                    ]
                ]
            ),
        )

        return True

    if step == 2:

        equiv[
            "replacement_dia"
        ] = value

        try:

            result = equivalent_rebar_count(
                equiv["count"],
                equiv["current_dia"],
                equiv["replacement_dia"],
                project_standard(
                    context
                ),
            )

            current_area = result[
                "current_area_mm2"
            ]

            replacement_area = result[
                "replacement_area_mm2"
            ]

            required_count = result[
                "required_count"
            ]

            if result[
                "area_equivalent"
            ]:

                status = "🟢"

                status_text = (
                    TEXT[lang][
                        "equivalent"
                    ]
                )

            else:

                status = "🔴"

                status_text = (
                    TEXT[lang][
                        "not_equivalent"
                    ]
                )

            message = (
                f"🔄 <b>{TEXT[lang]['equivalency']}</b>\n\n"
                "<pre>"
                f"میلگرد فعلی:\n"
                f"تعداد:       {equiv['count']}\n"
                f"قطر:         Φ{int(equiv['current_dia'])}\n"
                f"سطح مقطع:    {current_area:.0f} mm²\n\n"
                f"جایگزین:\n"
                f"قطر:         Φ{int(equiv['replacement_dia'])}\n"
                f"تعداد لازم:   {required_count}\n"
                f"سطح مقطع:    {replacement_area:.0f} mm²\n"
                "</pre>\n"
                f"{status} {status_text}\n\n"
                f"{TEXT[lang]['engineering_warning']}"
            )

            context.user_data[
                "equiv_step"
            ] = None

            await update.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=back_kb(
                    lang
                ),
            )

        except Exception as exc:

            await update.message.reply_text(
                TEXT[lang][
                    "calc_error"
                ].format(
                    escape(
                        str(exc)
                    )
                ),
                parse_mode="HTML",
                reply_markup=back_kb(
                    lang
                ),
            )

        return True

    return False


# =========================================================
# BUTTONS
# =========================================================

async def buttons(
    update,
    context,
):
    q = update.callback_query
    await q.answer()

    data = q.data

    lang = context.user_data.get(
        "lang",
        "fa",
    )

    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    if data == "language":

        return await q.edit_message_text(
            TEXT[lang]["language"],
            reply_markup=language_keyboard(),
        )

    if data.startswith(
        "lang_"
    ):

        new_lang = data.split(
            "_",
            1,
        )[1]

        context.user_data[
            "lang"
        ] = new_lang

        if project_ready(
            context
        ):

            await q.edit_message_text(
                TEXT[new_lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(
                    new_lang
                ),
            )

        else:

            await q.edit_message_text(
                TEXT[new_lang]["standard"],
                parse_mode="HTML",
                reply_markup=standard_keyboard(
                    new_lang
                ),
            )

        return

    # -----------------------------------------------------
    # STANDARD
    # -----------------------------------------------------

    if data in {
        "std_iran",
        "std_aci",
        "std_ec2",
    }:

        return await choose_standard(
            update,
            context,
        )

    # -----------------------------------------------------
    # CONCRETE
    # -----------------------------------------------------

    if data.startswith(
        "fc_"
    ):

        return await choose_concrete(
            update,
            context,
        )

    # -----------------------------------------------------
    # REBAR GRADE
    # -----------------------------------------------------

    if data.startswith(
        "grade_"
    ):

        return await choose_grade(
            update,
            context,
        )

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":

        # Keep project settings.
        saved_lang = lang
        project_results = context.user_data.get(
            "project_results",
            [],
        )

        standard = context.user_data.get(
            "standard"
        )

        fc = context.user_data.get(
            "fc"
        )

        grade = context.user_data.get(
            "rebar_grade"
        )

        fy = context.user_data.get(
            "fy"
        )

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = saved_lang

        if standard:
            context.user_data[
                "standard"
            ] = standard

        if fc is not None:
            context.user_data[
                "fc"
            ] = fc

        if grade:
            context.user_data[
                "rebar_grade"
            ] = grade

        if fy is not None:
            context.user_data[
                "fy"
            ] = fy

        context.user_data[
            "project_results"
        ] = project_results

        return await q.edit_message_text(
            TEXT[saved_lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(
                saved_lang
            ),
        )

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    if data == "cancel":

        saved_lang = lang

        context.user_data.pop(
            "kind",
            None,
        )

        context.user_data.pop(
            "step_index",
            None,
        )

        context.user_data.pop(
            "values",
            None,
        )

        context.user_data.pop(
            "history",
            None,
        )

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(
                saved_lang
            ),
        )

    # -----------------------------------------------------
    # PREVIOUS
    # -----------------------------------------------------

    if data == "prev":

        kind = context.user_data.get(
            "kind"
        )

        index = context.user_data.get(
            "step_index"
        )

        if (
            kind is None
            or index is None
        ):

            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(
                    lang
                ),
            )

        if index == 0:

            return await q.edit_message_text(
                TEXT[lang]["welcome"],
                parse_mode="HTML",
                reply_markup=main_menu(
                    lang
                ),
            )

        previous = index - 1

        key, label, typ = STEPS[
            kind
        ][previous]

        context.user_data[
            "values"
        ].pop(
            key,
            None,
        )

        context.user_data[
            "step_index"
        ] = previous

        await q.edit_message_text(
            prompt_text(
                lang,
                label[lang],
                previous + 1,
                len(
                    STEPS[kind]
                ),
            ),
            parse_mode="HTML",
            reply_markup=step_kb(
                lang
            ),
        )

        return

    # -----------------------------------------------------
    # REVIEW -> CALCULATE
    # -----------------------------------------------------

    if data == "do_calculate":

        return await do_calculate(
            update,
            context,
        )

    # -----------------------------------------------------
    # REVIEW -> EDIT
    # -----------------------------------------------------

    if data == "edit_member":

        kind = context.user_data.get(
            "kind"
        )

        if not kind:
            return

        context.user_data[
            "step_index"
        ] = 0

        context.user_data[
            "values"
        ] = {}

        key, label, typ = STEPS[
            kind
        ][0]

        return await q.edit_message_text(
            prompt_text(
                lang,
                label[lang],
                1,
                len(
                    STEPS[kind]
                ),
            ),
            parse_mode="HTML",
            reply_markup=step_kb(
                lang
            ),
        )

    # -----------------------------------------------------
    # FOUNDATION
    # -----------------------------------------------------

    if data == "foundation":

        return await q.edit_message_text(
            "🧱 <b>فونداسیون</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        "⬛ پی منفرد",
                        "foundation_iso",
                    ),
                    (
                        "▬ پی نواری",
                        "foundation_strip",
                    ),
                    (
                        "▰ پی گسترده / رادیه",
                        "foundation_raft",
                    ),
                ],
            ),
        )

    # -----------------------------------------------------
    # COLUMNS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # BEAMS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ROOFS
    # -----------------------------------------------------

    if data == "roofs":

        rows = []

        for key, info in ROOF_TYPES.items():

            rows.append(
                [
                    (
                        info["name"][lang],
                        f"roof_{key}",
                    )
                ]
            )

        return await q.edit_message_text(
            "🏠 <b>سقف‌ها</b>",
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                [
                    (
                        text,
                        data,
                    )
                    for row in rows
                    for text, data in row
                ],
            ),
        )

    # -----------------------------------------------------
    # TIES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # WALLS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # STAIRS
    # -----------------------------------------------------

    if data == "stairs":

        return await begin_wizard(
            update,
            context,
            "stair",
        )

    # -----------------------------------------------------
    # MEMBER MAPPING
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ROOF TYPE
    # -----------------------------------------------------

    if data.startswith(
        "roof_"
    ):

        roof_type = data[
            5:
        ]

        if roof_type not in ROOF_TYPES:
            return

        context.user_data[
            "kind"
        ] = "roof"

        context.user_data[
            "roof_type"
        ] = roof_type

        context.user_data[
            "roof_name"
        ] = ROOF_TYPES[
            roof_type
        ]["name"][lang]

        context.user_data[
            "step_index"
        ] = 0

        context.user_data[
            "values"
        ] = {}

        context.user_data[
            "history"
        ] = []

        fields = STEPS[
            "roof"
        ]

        _, label, typ = fields[
            0
        ]

        return await q.edit_message_text(
            (
                f"🏠 <b>"
                f"{escape(context.user_data['roof_name'])}"
                f"</b>\n\n"
                +
                prompt_text(
                    lang,
                    label[lang],
                    1,
                    len(fields),
                )
            ),
            parse_mode="HTML",
            reply_markup=step_kb(
                lang
            ),
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    if data == "show_rebar":

        result = context.user_data.get(
            "result",
            {},
        )

        return await q.edit_message_text(
            rebar_text(
                result.get(
                    "rebar_details",
                    [],
                ),
                lang,
            ),
            parse_mode="HTML",
            reply_markup=kb(
                [
                    [
                        (
                            TEXT[lang]["show_cut"],
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
                ]
            ),
        )

    if data == "show_cut":

        result = context.user_data.get(
            "result",
            {},
        )

        return await q.edit_message_text(
            cut_text(
                result.get(
                    "rebar_details",
                    [],
                ),
                lang,
            ),
            parse_mode="HTML",
            reply_markup=kb(
                [
                    [
                        (
                            TEXT[lang]["show_rebar"],
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
                ]
            ),
        )

    if data == "back_result":

        kind = context.user_data.get(
            "kind",
            "",
        )

        result = context.user_data.get(
            "result",
            {},
        )

        return await q.edit_message_text(
            summary_text(
                kind,
                result,
                lang,
            ),
            parse_mode="HTML",
            reply_markup=result_kb(
                lang
            ),
        )

    # -----------------------------------------------------
    # NEW MEMBER
    # -----------------------------------------------------

    if data == "new_member":

        context.user_data.pop(
            "kind",
            None,
        )

        context.user_data.pop(
            "step_index",
            None,
        )

        context.user_data.pop(
            "values",
            None,
        )

        context.user_data.pop(
            "history",
            None,
        )

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(
                lang
            ),
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    if data == "summary":

        return await q.edit_message_text(
            project_summary_text(
                context,
                lang,
            ),
            parse_mode="HTML",
            reply_markup=back_kb(
                lang
            ),
        )

    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    if data == "settings":

        standard = project_standard(
            context
        )

        message = (
            f"⚙️ <b>{TEXT[lang]['settings']}</b>\n\n"
            f"📚 {STANDARDS[standard][lang]}\n"
            f"🧱 C{project_fc(context):g}\n"
            f"🔩 {escape(project_grade(context))}"
        )

        return await q.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=kb(
                [
                    [
                        (
                            TEXT[lang]["standard_setting"],
                            "settings_standard",
                        )
                    ],
                    [
                        (
                            TEXT[lang]["materials"],
                            "settings_materials",
                        )
                    ],
                    [
                        (
                            TEXT[lang]["language"],
                            "language",
                        )
                    ],
                    [
                        (
                            TEXT[lang]["home"],
                            "home",
                        )
                    ],
                ]
            ),
        )

    if data == "settings_standard":

        return await q.edit_message_text(
            TEXT[lang]["standard"],
            parse_mode="HTML",
            reply_markup=standard_keyboard(
                lang
            ),
        )

    if data == "settings_materials":

        return await q.edit_message_text(
            TEXT[lang]["concrete"],
            parse_mode="HTML",
            reply_markup=concrete_keyboard(
                lang
            ),
        )

    # -----------------------------------------------------
    # EQUIVALENCY
    # -----------------------------------------------------

    if data == "equiv":

        return await begin_equivalency(
            update,
            context,
        )

    # Quick diameter buttons
    if data.startswith(
        "equiv_current_"
    ):

        dia = int(
            data.split(
                "_"
            )[-1]
        )

        context.user_data[
            "equiv"
        ]["current_dia"] = dia

        context.user_data[
            "equiv_step"
        ] = 2

        return await q.edit_message_text(
            f"3️⃣ {TEXT[lang]['replacement_dia']}",
            reply_markup=kb(
                diameter_buttons(
                    "equiv_replace_"
                )
            ),
        )

    if data.startswith(
        "equiv_replace_"
    ):

        dia = int(
            data.split(
                "_"
            )[-1]
        )

        equiv = context.user_data.get(
            "equiv",
            {},
        )

        equiv[
            "replacement_dia"
        ] = dia

        try:

            result = equivalent_rebar_count(
                equiv["count"],
                equiv["current_dia"],
                equiv["replacement_dia"],
                project_standard(
                    context
                ),
            )

            current_area = result[
                "current_area_mm2"
            ]

            replacement_area = result[
                "replacement_area_mm2"
            ]

            required_count = result[
                "required_count"
            ]

            if result[
                "area_equivalent"
            ]:

                status = "🟢"
                status_text = TEXT[
                    lang
                ]["equivalent"]

            else:

                status = "🔴"
                status_text = TEXT[
                    lang
                ]["not_equivalent"]

            message = (
                f"🔄 <b>{TEXT[lang]['equivalency']}</b>\n\n"
                "<pre>"
                f"فعلی:\n"
                f"تعداد:       {equiv['count']}\n"
                f"قطر:         Φ{equiv['current_dia']}\n"
                f"سطح مقطع:    {current_area:.0f} mm²\n\n"
                f"جایگزین:\n"
                f"قطر:         Φ{equiv['replacement_dia']}\n"
                f"تعداد لازم:   {required_count}\n"
                f"سطح مقطع:    {replacement_area:.0f} mm²\n"
                "</pre>\n"
                f"{status} {status_text}\n\n"
                f"{TEXT[lang]['engineering_warning']}"
            )

            context.user_data[
                "equiv_step"
            ] = None

            return await q.edit_message_text(
                message,
                parse_mode="HTML",
                reply_markup=back_kb(
                    lang
                ),
            )

        except Exception as exc:

            return await q.edit_message_text(
                TEXT[lang][
                    "calc_error"
                ].format(
                    escape(
                        str(exc)
                    )
                ),
                parse_mode="HTML",
                reply_markup=back_kb(
                    lang
                ),
            )

    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    if data == "help":

        message = (
            f"ℹ️ <b>{TEXT[lang]['help']}</b>\n\n"
            "🏗️ این ابزار برای برآورد مقادیر بتن و میلگرد "
            "اعضای سازه بتنی طراحی شده است.\n\n"
            "📚 استاندارد انتخابی در موتور محاسبات ذخیره می‌شود.\n"
            "🧱 مقاومت بتن و 🔩 گرید میلگرد یک‌بار برای پروژه ثبت می‌شوند.\n"
            "✂️ Cut List بر اساس شاخه ۱۲ متری محاسبه می‌شود.\n\n"
            "⚠️ خروجی ابزار جایگزین نقشه و محاسبات نهایی مهندس محاسب نیست."
        )

        return await q.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=back_kb(
                lang
            ),
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(
            lang
        ),
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        TEXT["fa"]["language"],
        reply_markup=language_keyboard(),
    )


# =========================================================
# LANGUAGE CALLBACK
# =========================================================

async def choose_language(
    update,
    context,
):
    q = update.callback_query

    await q.answer()

    lang = q.data.split(
        "_",
        1,
    )[1]

    context.user_data.clear()

    context.user_data[
        "lang"
    ] = lang

    await q.edit_message_text(
        TEXT[lang]["standard"],
        parse_mode="HTML",
        reply_markup=standard_keyboard(
            lang
        ),
    )


# =========================================================
# MESSAGE ROUTER
# =========================================================

async def receive_router(
    update,
    context,
):
    # Equivalency has its own input flow.
    if context.user_data.get(
        "equiv_step"
    ) is not None:

        handled = await receive_equivalency(
            update,
            context,
        )

        if handled:
            return

    await receive(
        update,
        context,
    )


# =========================================================
# ERROR HANDLER
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
            filters.TEXT
            & ~filters.COMMAND,
            receive_router,
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
