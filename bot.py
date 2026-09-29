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
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get(
    "RENDER_EXTERNAL_URL",
    ""
).rstrip("/")


# =========================================================
# TEXT / LANGUAGES
# =========================================================

TEXT = {
    "fa": {
        "language": "🌐 زبان",
        "welcome": "🏗️ <b>اسکلت بتنی</b>\n\nعضو موردنظر را انتخاب کنید:",
        "invalid": "❌ مقدار واردشده معتبر نیست. دوباره وارد کنید.",
        "calc_error": "❌ خطا در محاسبه:\n<code>{}</code>",
        "back": "🔙 بازگشت",
        "home": "🏠 صفحه اصلی",
        "cancel": "❌ لغو",
        "prev": "⬅️ مرحله قبل",
        "rebar": "🔩 جزئیات میلگرد",
        "cut": "✂️ Cut List",
        "result": "⬅️ نتیجه",
        "new": "➕ محاسبه جدید",
        "summary": "📊 خلاصه پروژه",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "change_language": "🌐 تغییر زبان",
        "language_changed": "زبان با موفقیت تغییر کرد.",
        "choose_language": "زبان موردنظر را انتخاب کنید:",
    },

    "ar": {
        "language": "🌐 اللغة",
        "welcome": "🏗️ <b>الهيكل الخرساني</b>\n\nاختر العنصر المطلوب:",
        "invalid": "❌ القيمة غير صالحة. حاول مرة أخرى.",
        "calc_error": "❌ خطأ في الحساب:\n<code>{}</code>",
        "back": "🔙 رجوع",
        "home": "🏠 الرئيسية",
        "cancel": "❌ إلغاء",
        "prev": "⬅️ الخطوة السابقة",
        "rebar": "🔩 تفاصيل التسليح",
        "cut": "✂️ Cut List",
        "result": "⬅️ النتيجة",
        "new": "➕ حساب جديد",
        "summary": "📊 ملخص المشروع",
        "settings": "⚙️ الإعدادات",
        "help": "ℹ️ المساعدة",
        "change_language": "🌐 تغيير اللغة",
        "language_changed": "تم تغيير اللغة بنجاح.",
        "choose_language": "اختر اللغة:",
    },

    "en": {
        "language": "🌐 Language",
        "welcome": "🏗️ <b>Concrete Frame</b>\n\nChoose the required member:",
        "invalid": "❌ Invalid value. Please try again.",
        "calc_error": "❌ Calculation error:\n<code>{}</code>",
        "back": "🔙 Back",
        "home": "🏠 Main Menu",
        "cancel": "❌ Cancel",
        "prev": "⬅️ Previous",
        "rebar": "🔩 Rebar Details",
        "cut": "✂️ Cut List",
        "result": "⬅️ Result",
        "new": "➕ New Calculation",
        "summary": "📊 Project Summary",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "change_language": "🌐 Change Language",
        "language_changed": "Language changed successfully.",
        "choose_language": "Choose your language:",
    },

    "zh": {
        "language": "🌐 语言",
        "welcome": "🏗️ <b>混凝土结构</b>\n\n请选择构件：",
        "invalid": "❌ 输入值无效，请重新输入。",
        "calc_error": "❌ 计算错误：\n<code>{}</code>",
        "back": "🔙 返回",
        "home": "🏠 主菜单",
        "cancel": "❌ 取消",
        "prev": "⬅️ 上一步",
        "rebar": "🔩 钢筋详情",
        "cut": "✂️ Cut List",
        "result": "⬅️ 结果",
        "new": "➕ 新计算",
        "summary": "📊 项目汇总",
        "settings": "⚙️ 设置",
        "help": "ℹ️ 帮助",
        "change_language": "🌐 更改语言",
        "language_changed": "语言已成功更改。",
        "choose_language": "请选择语言：",
    },
}


# =========================================================
# ROOF COEFFICIENTS
# =========================================================

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
    "fa": {
        "foam": "🟦 تیرچه یونولیتی",
        "clay": "🟫 تیرچه سفالی",
        "double": "🟪 تیرچه دوبل",
        "kromit": "🔩 کرومیت",
        "composite": "🏗️ کامپوزیت",
        "steeldeck": "🔩 عرشه فولادی",
        "slab": "⬜ دال بتنی",
        "waffle": "🔳 وافل",
    },

    "ar": {
        "foam": "🟦 بلوك فوم",
        "clay": "🟫 بلوك فخاري",
        "double": "🟪 الجسر المزدوج",
        "kromit": "🔩 كروميت",
        "composite": "🏗️ مركب",
        "steeldeck": "🔩 سطح فولاذي",
        "slab": "⬜ بلاطة خرسانية",
        "waffle": "🔳 وافل",
    },

    "en": {
        "foam": "🟦 Foam Joist",
        "clay": "🟫 Clay Joist",
        "double": "🟪 Double Joist",
        "kromit": "🔩 Kromit",
        "composite": "🏗️ Composite",
        "steeldeck": "🔩 Steel Deck",
        "slab": "⬜ Concrete Slab",
        "waffle": "🔳 Waffle",
    },

    "zh": {
        "foam": "🟦 泡沫块楼板",
        "clay": "🟫 陶土块楼板",
        "double": "🟪 双梁楼板",
        "kromit": "🔩 Kromit",
        "composite": "🏗️ 组合楼板",
        "steeldeck": "🔩 压型钢板",
        "slab": "⬜ 混凝土板",
        "waffle": "🔳 井字梁楼板",
    },
}


# =========================================================
# STEP DEFINITIONS
# =========================================================

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
        ("td", "قطر میلگرد بالا (mm)؛ اگر ندارد 0", "int"),
        ("ts", "فاصله میلگرد بالا (mm)؛ اگر ندارد 0", "int"),
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
        ("tld", "قطر طولی بالا (mm)؛ اگر ندارد 0", "int"),
        ("tlc", "تعداد طولی بالا؛ اگر ندارد 0", "int"),
        ("ttd", "قطر عرضی بالا (mm)؛ اگر ندارد 0", "int"),
        ("tts", "فاصله عرضی بالا (mm)؛ اگر ندارد 0", "int"),
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
        ("txd", "قطر X بالا (mm)؛ اگر ندارد 0", "int"),
        ("txs", "فاصله X بالا (mm)", "int"),
        ("tyd", "قطر Y بالا (mm)؛ اگر ندارد 0", "int"),
        ("tys", "فاصله Y بالا (mm)", "int"),
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
        ("bd", "قطر میلگرد پایین (mm)", "int"),
        ("bc", "تعداد میلگرد پایین", "int"),
        ("td", "قطر میلگرد بالا (mm)", "int"),
        ("tc", "تعداد میلگرد بالا", "int"),
        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),
        ("cover", "کاور (mm)", "float"),
    ],

    "tie": [
        ("count", "تعداد شناژ/کلاف", "int"),
        ("L", "طول (m)", "float"),
        ("W", "عرض (m)", "float"),
        ("H", "ارتفاع (m)", "float"),
        ("ld", "قطر میلگرد طولی (mm)", "int"),
        ("lc", "تعداد میلگرد طولی", "int"),
        ("sd", "قطر خاموت (mm)", "int"),
        ("ss", "فاصله خاموت (mm)", "int"),
        ("cover", "کاور (mm)", "float"),
    ],

    "wall": [
        ("L", "طول دیوار (m)", "float"),
        ("H", "ارتفاع دیوار (m)", "float"),
        ("T", "ضخامت دیوار (m)", "float"),
        ("vd", "قطر میلگرد قائم (mm)", "int"),
        ("vs", "فاصله میلگرد قائم (mm)", "int"),
        ("hd", "قطر میلگرد افقی (mm)", "int"),
        ("hs", "فاصله میلگرد افقی (mm)", "int"),
        ("cover", "کاور (mm)", "float"),
    ],

    "stair": [
        ("L", "طول شیب/دال (m)", "float"),
        ("W", "عرض راه‌پله (m)", "float"),
        ("T", "ضخامت دال (m)", "float"),
        ("md", "قطر میلگرد اصلی (mm)", "int"),
        ("ms", "فاصله میلگرد اصلی (mm)", "int"),
        ("dd", "قطر میلگرد توزیعی (mm)", "int"),
        ("ds", "فاصله میلگرد توزیعی (mm)", "int"),
        ("steps", "تعداد پله", "int"),
        ("riser", "ارتفاع رایزر (m)", "float"),
        ("tread", "کف پله (m)", "float"),
    ],

    "roof": [
        ("area", "مساحت سقف (m²)", "float"),
        ("dia", "قطر میلگرد (mm)", "int"),
        ("kgm2", "مصرف میلگرد (kg/m²)؛ برای فقط بتن 0", "float"),
    ],
}


# =========================================================
# TRANSLATION OF STEP LABELS
# =========================================================

STEP_TRANSLATIONS = {

    "ar": {
        "تعداد پی": "عدد القواعد",
        "طول پی (m)": "طول القاعدة (m)",
        "عرض پی (m)": "عرض القاعدة (m)",
        "ضخامت پی (m)": "سماكة القاعدة (m)",
        "طول بتن مگر (m)": "طول الخرسانة النظافة (m)",
        "عرض بتن مگر (m)": "عرض الخرسانة النظافة (m)",
        "ضخامت بتن مگر (m)": "سماكة الخرسانة النظافة (m)",
        "قطر میلگرد پایین (mm)": "قطر التسليح السفلي (mm)",
        "فاصله میلگرد پایین (mm)": "تباعد التسليح السفلي (mm)",
        "قطر میلگرد بالا (mm)؛ اگر ندارد 0": "قطر التسليح العلوي (mm)؛ إذا لا يوجد 0",
        "فاصله میلگرد بالا (mm)؛ اگر ندارد 0": "تباعد التسليح العلوي (mm)؛ إذا لا يوجد 0",
        "کاور (mm)": "الغطاء الخرساني (mm)",
        "درصد اورلپ": "نسبة التراكب",
        "طول پدستال (m)": "طول البيدستال (m)",
        "عرض پدستال (m)": "عرض البيدستال (m)",
        "ارتفاع پدستال (m)": "ارتفاع البيدستال (m)",
    },

    "en": {
        "تعداد پی": "Number of footings",
        "طول پی (m)": "Footing length (m)",
        "عرض پی (m)": "Footing width (m)",
        "ضخامت پی (m)": "Footing thickness (m)",
        "طول بتن مگر (m)": "Lean concrete length (m)",
        "عرض بتن مگر (m)": "Lean concrete width (m)",
        "ضخامت بتن مگر (m)": "Lean concrete thickness (m)",
        "قطر میلگرد پایین (mm)": "Bottom rebar diameter (mm)",
        "فاصله میلگرد پایین (mm)": "Bottom rebar spacing (mm)",
        "قطر میلگرد بالا (mm)؛ اگر ندارد 0": "Top rebar diameter (mm); 0 if none",
        "فاصله میلگرد بالا (mm)؛ اگر ندارد 0": "Top rebar spacing (mm); 0 if none",
        "کاور (mm)": "Concrete cover (mm)",
        "درصد اورلپ": "Lap percentage",
        "طول پدستال (m)": "Pedestal length (m)",
        "عرض پدستال (m)": "Pedestal width (m)",
        "ارتفاع پدستال (m)": "Pedestal height (m)",
    },

    "zh": {
        "تعداد پی": "基础数量",
        "طول پی (m)": "基础长度 (m)",
        "عرض پی (m)": "基础宽度 (m)",
        "ضخامت پی (m)": "基础厚度 (m)",
        "طول بتن مگر (m)": "垫层长度 (m)",
        "عرض بتن مگر (m)": "垫层宽度 (m)",
        "ضخامت بتن مگر (m)": "垫层厚度 (m)",
        "قطر میلگرد پایین (mm)": "底部钢筋直径 (mm)",
        "فاصله میلگرد پایین (mm)": "底部钢筋间距 (mm)",
        "قطر میلگرد بالا (mm)؛ اگر ندارد 0": "顶部钢筋直径 (mm)，无则输入0",
        "فاصله میلگرد بالا (mm)؛ اگر ندارد 0": "顶部钢筋间距 (mm)，无则输入0",
        "کاور (mm)": "保护层厚度 (mm)",
        "درصد اورلپ": "搭接百分比",
        "طول پدستال (m)": "柱墩长度 (m)",
        "عرض پدستال (m)": "柱墩宽度 (m)",
        "ارتفاع پدستال (m)": "柱墩高度 (m)",
    },
}


def label_for(lang, label):
    if lang == "fa":
        return label

    return STEP_TRANSLATIONS.get(
        lang,
        {}
    ).get(
        label,
        label
    )


# =========================================================
# KEYBOARD HELPERS
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


def language_keyboard():
    return kb([
        [("🇮🇷 فارسی", "lang_fa")],
        [("🇸🇦 العربية", "lang_ar")],
        [("🇬🇧 English", "lang_en")],
        [("🇨🇳 中文", "lang_zh")],
    ])


def main_menu(lang):

    if lang == "fa":
        return kb([
            [("🧱 فونداسیون", "foundation")],
            [("🏛️ ستون‌ها", "columns")],
            [("📐 تیرها", "beams")],
            [("🏠 سقف‌ها", "roofs")],
            [("🪜 راه‌پله", "stairs")],
            [("🔗 شناژ و کلاف", "ties")],
            [("🧱 دیوارها", "walls")],
            [("📊 خلاصه پروژه", "summary")],
            [("⚙️ تنظیمات", "settings")],
            [("ℹ️ راهنما", "help")],
        ])

    if lang == "ar":
        return kb([
            [("🧱 الأساسات", "foundation")],
            [("🏛️ الأعمدة", "columns")],
            [("📐 الكمرات", "beams")],
            [("🏠 الأسقف", "roofs")],
            [("🪜 السلالم", "stairs")],
            [("🔗 الجسور والرباطات", "ties")],
            [("🧱 الجدران", "walls")],
            [("📊 ملخص المشروع", "summary")],
            [("⚙️ الإعدادات", "settings")],
            [("ℹ️ المساعدة", "help")],
        ])

    if lang == "en":
        return kb([
            [("🧱 Foundations", "foundation")],
            [("🏛️ Columns", "columns")],
            [("📐 Beams", "beams")],
            [("🏠 Roofs", "roofs")],
            [("🪜 Stairs", "stairs")],
            [("🔗 Tie Beams", "ties")],
            [("🧱 Walls", "walls")],
            [("📊 Project Summary", "summary")],
            [("⚙️ Settings", "settings")],
            [("ℹ️ Help", "help")],
        ])

    return kb([
        [("🧱 基础", "foundation")],
        [("🏛️ 柱", "columns")],
        [("📐 梁", "beams")],
        [("🏠 楼板", "roofs")],
        [("🪜 楼梯", "stairs")],
        [("🔗 系梁", "ties")],
        [("🧱 墙体", "walls")],
        [("📊 项目汇总", "summary")],
        [("⚙️ 设置", "settings")],
        [("ℹ️ 帮助", "help")],
    ])


def back_kb(lang, callback="home"):
    return kb([
        [(TEXT[lang]["back"], callback)],
        [(TEXT[lang]["home"], "home")],
    ])


def step_kb(lang):
    return kb([
        [(TEXT[lang]["prev"], "prev")],
        [(TEXT[lang]["cancel"], "cancel")],
        [(TEXT[lang]["home"], "home")],
    ])


def result_kb(lang):
    return kb([
        [(TEXT[lang]["rebar"], "show_rebar")],
        [(TEXT[lang]["cut"], "show_cut")],
        [(TEXT[lang]["new"], "new_member")],
        [(TEXT[lang]["home"], "home")],
    ])


def section_kb(lang, items, parent="home"):
    rows = [[(text, data)] for text, data in items]
    rows.append([(TEXT[lang]["back"], parent)])
    return kb(rows)


# =========================================================
# PROMPTS
# =========================================================

def prompt_text(lang, label, i, total):

    label = label_for(lang, label)

    if lang == "fa":
        return (
            f"📐 <b>{escape(label)}</b>\n\n"
            "مقدار را وارد کنید:\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 مرحله <b>{i}</b> از <b>{total}</b>"
        )

    if lang == "ar":
        return (
            f"📐 <b>{escape(label)}</b>\n\n"
            "أدخل القيمة:\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 الخطوة <b>{i}</b> من <b>{total}</b>"
        )

    if lang == "en":
        return (
            f"📐 <b>{escape(label)}</b>\n\n"
            "Enter the value:\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 Step <b>{i}</b> of <b>{total}</b>"
        )

    return (
        f"📐 <b>{escape(label)}</b>\n\n"
        "请输入数值：\n\n"
        "━━━━━━━━━━━━━━\n"
        f"📍 第 <b>{i}</b> 步，共 <b>{total}</b> 步"
    )


# =========================================================
# RESULT TEXT
# =========================================================

def member_name(kind, lang):

    names = {
        "fa": {
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
        },

        "ar": {
            "iso": "⬛ قاعدة منفردة",
            "strip": "▬ قاعدة شريطية",
            "raft": "▰ لبشة",
            "column_rect": "▯ عمود مستطيل",
            "column_round": "◯ عمود دائري",
            "beam": "📐 كمرة",
            "tie": "🔗 جسر ربط",
            "wall": "🧱 جدار",
            "stair": "🪜 درج",
            "roof": "🏠 سقف",
        },

        "en": {
            "iso": "⬛ Isolated Footing",
            "strip": "▬ Strip Footing",
            "raft": "▰ Raft Foundation",
            "column_rect": "▯ Rectangular Column",
            "column_round": "◯ Round Column",
            "beam": "📐 Beam",
            "tie": "🔗 Tie Beam",
            "wall": "🧱 Wall",
            "stair": "🪜 Stair",
            "roof": "🏠 Roof",
        },

        "zh": {
            "iso": "⬛ 独立基础",
            "strip": "▬ 条形基础",
            "raft": "▰ 筏板基础",
            "column_rect": "▯ 矩形柱",
            "column_round": "◯ 圆柱",
            "beam": "📐 梁",
            "tie": "🔗 系梁",
            "wall": "🧱 墙",
            "stair": "🪜 楼梯",
            "roof": "🏠 楼板",
        },
    }

    return names.get(lang, names["fa"]).get(
        kind,
        kind
    )


def summary_text(kind, result, lang):

    name = member_name(
        kind,
        lang
    )

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
        f"<b>{name}</b>",
        "",
        "<pre>",
        "━━━━━━━━━━━━━━━━",
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

        lines.append(
            f"بتن پی:         {footing:.2f} m³"
        )

        lines.append(
            f"بتن مگر:        {lean:.2f} m³"
        )

        lines.append(
            f"بتن پدستال:     {pedestal:.2f} m³"
        )

        lines.append(
            "━━━━━━━━━━━━━━━━"
        )

    lines.append(
        f"کل بتن:         {concrete:.2f} m³"
    )

    lines.append(
        f"کل میلگرد:      {rebar:.1f} kg"
    )

    lines.extend([
        "━━━━━━━━━━━━━━━━",
        "</pre>",
        "",
        "🔎 جزئیات میلگرد و Cut List را از دکمه‌های زیر ببین.",
    ])

    return "\n".join(lines)


# =========================================================
# REBAR DETAILS - VERTICAL / COPYABLE
# =========================================================

def rebar_text(details, lang="fa"):

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

    for index, item in enumerate(details, 1):

        dia = int(
            item.get(
                "diameter_mm",
                0
            )
        )

        pieces = int(
            item.get(
                "piece_count",
                0
            )
        )

        length = float(
            item.get(
                "length_m",
                0
            ) or 0
        )

        weight = float(
            item.get(
                "weight_kg",
                0
            ) or 0
        )

        bars = int(
            item.get(
                "bars_12m",
                0
            )
        )

        waste = float(
            item.get(
                "waste_m",
                0
            ) or 0
        )

        description = item.get(
            "description",
            ""
        )

        total_weight += weight
        total_bars += bars

        chunks.append("<pre>")
        chunks.append(
            "━━━━━━━━━━━━━━━━"
        )

        chunks.append(
            f"میلگرد {index}"
        )

        if description:
            chunks.append(
                f"نوع:            {description}"
            )

        chunks.append(
            f"قطر:            Φ{dia}"
        )

        chunks.append(
            f"تعداد قطعات:    {pieces} عدد"
        )

        chunks.append(
            f"طول کل:         {length:.2f} m"
        )

        chunks.append(
            f"وزن:            {weight:.1f} kg"
        )

        chunks.append(
            f"شاخه ۱۲ متری:   {bars} شاخه"
        )

        chunks.append(
            f"پرت:            {waste:.2f} m"
        )

        chunks.append(
            "━━━━━━━━━━━━━━━━"
        )

        chunks.append("</pre>")
        chunks.append("")

    chunks.append("<pre>")
    chunks.append(
        "━━━━━━━━━━━━━━━━"
    )
    chunks.append(
        "جمع کل"
    )
    chunks.append(
        f"وزن کل:         {total_weight:.1f} kg"
    )
    chunks.append(
        f"شاخه ۱۲ متری:   {total_bars} شاخه"
    )
    chunks.append(
        "━━━━━━━━━━━━━━━━"
    )
    chunks.append("</pre>")

    return "\n".join(chunks)


# =========================================================
# CUT LIST - VERTICAL / COPYABLE
# =========================================================

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

    total_bars_all = 0
    total_waste_all = 0.0

    for detail in details:

        dia = int(
            detail.get(
                "diameter_mm",
                0
            )
        )

        plans = detail.get(
            "cut_plan",
            []
        )

        bars = int(
            detail.get(
                "bars_12m",
                len(plans)
            )
        )

        total_bars_all += bars

        chunks.append(
            f"🔩 <b>Φ{dia}</b>"
        )

        chunks.append("")

        for i, plan in enumerate(
            plans,
            1
        ):

            pieces_list = plan.get(
                "pieces",
                []
            )

            pieces = " + ".join(
                f"{float(v):.2f}"
                for v in pieces_list
            )

            used = float(
                plan.get(
                    "used_m",
                    sum(
                        float(v)
                        for v in pieces_list
                    )
                )
            )

            # Always recalculate the waste from the
            # actual 12 m stock bar.
            waste = max(
                0.0,
                12.0 - used
            )

            total_waste_all += waste

            chunks.append("<pre>")
            chunks.append(
                "━━━━━━━━━━━━━━━━"
            )

            chunks.append(
                f"شاخه {i:02d}"
            )

            chunks.append(
                f"قطر:            Φ{dia}"
            )

            chunks.append(
                f"قطعه‌ها:        {pieces} m"
            )

            chunks.append(
                f"مصرف:           {used:.2f} m"
            )

            chunks.append(
                f"پرت:            {waste:.2f} m"
            )

            chunks.append(
                "━━━━━━━━━━━━━━━━"
            )

            chunks.append("</pre>")
            chunks.append("")

        chunks.append("<pre>")
        chunks.append(
            f"تعداد شاخه:     {bars} شاخه"
        )
        chunks.append("</pre>")
        chunks.append("")

    chunks.append("<pre>")
    chunks.append(
        "━━━━━━━━━━━━━━━━"
    )
    chunks.append(
        "جمع کل Cut List"
    )
    chunks.append(
        f"تعداد شاخه:     {total_bars_all} شاخه"
    )
    chunks.append(
        f"پرت کل:         {total_waste_all:.2f} m"
    )
    chunks.append(
        "━━━━━━━━━━━━━━━━"
    )
    chunks.append("</pre>")

    return "\n".join(chunks)


# =========================================================
# CALCULATIONS
# =========================================================

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
            if v["td"] > 0
            and v["ts"] > 0
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
            if v["ttd"] > 0
            and v["tts"] > 0
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
            if v["txd"] > 0
            and v["txs"] > 0
            else None,
            int(v["tyd"])
            if v["tyd"] > 0
            else None,
            v["tys"]
            if v["tyd"] > 0
            and v["tys"] > 0
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


# =========================================================
# START / LANGUAGE
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "🌐 زبان / اللغة / Language / 语言",
        reply_markup=language_keyboard(),
    )


async def choose_language(
    update,
    context
):

    q = update.callback_query
    await q.answer()

    lang = q.data.split(
        "_",
        1
    )[1]

    context.user_data.clear()
    context.user_data["lang"] = lang

    await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang),
    )


# =========================================================
# WIZARD
# =========================================================

async def begin_wizard(
    update,
    context,
    kind
):

    q = update.callback_query

    lang = context.user_data.get(
        "lang",
        "fa"
    )

    context.user_data["kind"] = kind
    context.user_data["step_index"] = 0
    context.user_data["values"] = {}
    context.user_data["history"] = []

    fields = STEPS[kind]

    await q.edit_message_text(
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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
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

        await update.message.reply_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )

        return

    fields = STEPS[kind]

    key, label, typ = fields[idx]

    raw = (
        update.message.text
        .strip()
        .replace(",", ".")
    )

    try:

        value = (
            int(float(raw))
            if typ == "int"
            else float(raw)
        )

        if value < 0:
            raise ValueError

        if (
            typ == "int"
            and value != int(value)
        ):
            raise ValueError

    except Exception:

        await update.message.reply_text(
            TEXT[lang]["invalid"],
            reply_markup=step_kb(lang),
        )

        return

    context.user_data["values"][key] = value

    context.user_data["history"].append(
        idx
    )

    next_idx = idx + 1

    if next_idx < len(fields):

        context.user_data[
            "step_index"
        ] = next_idx

        next_label = fields[next_idx][1]

        await update.message.reply_text(
            prompt_text(
                lang,
                next_label,
                next_idx + 1,
                len(fields)
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang),
        )

        return

    try:

        result = calculate(
            kind,
            context.user_data["values"]
        )

        context.user_data["result"] = result

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
            reply_markup=result_kb(lang),
        )

    except Exception as exc:

        logger.exception(
            "Calculation failed"
        )

        await update.message.reply_text(
            TEXT[lang]["calc_error"].format(
                escape(str(exc))
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang),
        )


# =========================================================
# BUTTONS
# =========================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    q = update.callback_query

    await q.answer()

    data = q.data

    lang = context.user_data.get(
        "lang",
        "fa"
    )


    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    if data.startswith("lang_"):

        return await choose_language(
            update,
            context
        )


    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )


    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    if data == "cancel":

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )


    # -----------------------------------------------------
    # PREVIOUS STEP
    # -----------------------------------------------------

    if data == "prev":

        kind = context.user_data.get(
            "kind"
        )

        idx = context.user_data.get(
            "step_index"
        )

        if (
            not kind
            or idx is None
        ):

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

        key = STEPS[kind][previous][0]

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
            ] = context.user_data[
                "history"
            ][:-1]

        label = STEPS[kind][previous][1]

        return await q.edit_message_text(
            prompt_text(
                lang,
                label,
                previous + 1,
                len(STEPS[kind])
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang),
        )


    # -----------------------------------------------------
    # FOUNDATION
    # -----------------------------------------------------

    if data == "foundation":

        if lang == "fa":

            title = "🧱 <b>فونداسیون</b>"

            items = [
                ("⬛ پی منفرد", "foundation_iso"),
                ("▬ پی نواری", "foundation_strip"),
                ("▰ پی گسترده / رادیه", "foundation_raft"),
            ]

        elif lang == "ar":

            title = "🧱 <b>الأساسات</b>"

            items = [
                ("⬛ قاعدة منفردة", "foundation_iso"),
                ("▬ قاعدة شريطية", "foundation_strip"),
                ("▰ لبشة", "foundation_raft"),
            ]

        elif lang == "en":

            title = "🧱 <b>Foundations</b>"

            items = [
                ("⬛ Isolated Footing", "foundation_iso"),
                ("▬ Strip Footing", "foundation_strip"),
                ("▰ Raft Foundation", "foundation_raft"),
            ]

        else:

            title = "🧱 <b>基础</b>"

            items = [
                ("⬛ 独立基础", "foundation_iso"),
                ("▬ 条形基础", "foundation_strip"),
                ("▰ 筏板基础", "foundation_raft"),
            ]

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # COLUMNS
    # -----------------------------------------------------

    if data == "columns":

        if lang == "fa":

            title = "🏛️ <b>ستون‌ها</b>"

            items = [
                ("▯ ستون مربعی / مستطیلی", "column_rect"),
                ("◯ ستون گرد", "column_round"),
            ]

        elif lang == "ar":

            title = "🏛️ <b>الأعمدة</b>"

            items = [
                ("▯ عمود مربع / مستطيل", "column_rect"),
                ("◯ عمود دائري", "column_round"),
            ]

        elif lang == "en":

            title = "🏛️ <b>Columns</b>"

            items = [
                ("▯ Rectangular Column", "column_rect"),
                ("◯ Round Column", "column_round"),
            ]

        else:

            title = "🏛️ <b>柱</b>"

            items = [
                ("▯ 矩形柱", "column_rect"),
                ("◯ 圆柱", "column_round"),
            ]

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # BEAMS
    # -----------------------------------------------------

    if data == "beams":

        if lang == "fa":

            title = "📐 <b>تیرها</b>"

            items = [
                ("📐 تیر اصلی", "beam_main"),
                ("📏 تیر فرعی", "beam_secondary"),
            ]

        elif lang == "ar":

            title = "📐 <b>الكمرات</b>"

            items = [
                ("📐 كمرة رئيسية", "beam_main"),
                ("📏 كمرة ثانوية", "beam_secondary"),
            ]

        elif lang == "en":

            title = "📐 <b>Beams</b>"

            items = [
                ("📐 Main Beam", "beam_main"),
                ("📏 Secondary Beam", "beam_secondary"),
            ]

        else:

            title = "📐 <b>梁</b>"

            items = [
                ("📐 主梁", "beam_main"),
                ("📏 次梁", "beam_secondary"),
            ]

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # ROOFS
    # -----------------------------------------------------

    if data == "roofs":

        items = []

        for roof_key in [
            "foam",
            "clay",
            "double",
            "kromit",
            "composite",
            "steeldeck",
            "slab",
            "waffle",
        ]:

            items.append(
                (
                    ROOF_NAMES[lang][roof_key],
                    f"roof_{roof_key}"
                )
            )

        if lang == "fa":
            title = "🏠 <b>سقف‌ها</b>"

        elif lang == "ar":
            title = "🏠 <b>الأسقف</b>"

        elif lang == "en":
            title = "🏠 <b>Roofs</b>"

        else:
            title = "🏠 <b>楼板</b>"

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # TIES
    # -----------------------------------------------------

    if data == "ties":

        if lang == "fa":

            title = "🔗 <b>شناژ و کلاف</b>"

            items = [
                ("🔗 شناژ", "tie_beam"),
                ("⛓️ کلاف", "tie_cowl"),
            ]

        elif lang == "ar":

            title = "🔗 <b>الجسور والرباطات</b>"

            items = [
                ("🔗 جسر ربط", "tie_beam"),
                ("⛓️ رباط", "tie_cowl"),
            ]

        elif lang == "en":

            title = "🔗 <b>Tie Beams</b>"

            items = [
                ("🔗 Tie Beam", "tie_beam"),
                ("⛓️ Tie", "tie_cowl"),
            ]

        else:

            title = "🔗 <b>系梁</b>"

            items = [
                ("🔗 系梁", "tie_beam"),
                ("⛓️ 拉梁", "tie_cowl"),
            ]

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # WALLS
    # -----------------------------------------------------

    if data == "walls":

        if lang == "fa":

            title = "🧱 <b>دیوارها</b>"

            items = [
                ("🏢 دیوار برشی", "wall_shear"),
                ("🧱 دیوار حائل", "wall_retaining"),
            ]

        elif lang == "ar":

            title = "🧱 <b>الجدران</b>"

            items = [
                ("🏢 جدار قص", "wall_shear"),
                ("🧱 جدار ساند", "wall_retaining"),
            ]

        elif lang == "en":

            title = "🧱 <b>Walls</b>"

            items = [
                ("🏢 Shear Wall", "wall_shear"),
                ("🧱 Retaining Wall", "wall_retaining"),
            ]

        else:

            title = "🧱 <b>墙体</b>"

            items = [
                ("🏢 剪力墙", "wall_shear"),
                ("🧱 挡土墙", "wall_retaining"),
            ]

        return await q.edit_message_text(
            title,
            parse_mode="HTML",
            reply_markup=section_kb(
                lang,
                items
            ),
        )


    # -----------------------------------------------------
    # STAIRS
    # -----------------------------------------------------

    if data == "stairs":

        return await begin_wizard(
            update,
            context,
            "stair"
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
            mapping[data]
        )


    # -----------------------------------------------------
    # ROOF WIZARD
    # -----------------------------------------------------

    if data.startswith("roof_"):

        roof_type = data[5:]

        context.user_data["kind"] = "roof"

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
            lang
        ][
            roof_type
        ]

        fields = STEPS["roof"]

        return await q.edit_message_text(
            f"{ROOF_NAMES[lang][roof_type]}\n\n"
            + prompt_text(
                lang,
                fields[0][1],
                1,
                len(fields)
            ),
            parse_mode="HTML",
            reply_markup=step_kb(lang),
        )


    # -----------------------------------------------------
    # REBAR
    # -----------------------------------------------------

    if data == "show_rebar":

        return await q.edit_message_text(
            rebar_text(
                context.user_data.get(
                    "result",
                    {}
                ).get(
                    "rebar_details",
                    []
                ),
                lang
            ),
            parse_mode="HTML",
            reply_markup=kb([
                [(TEXT[lang]["cut"], "show_cut")],
                [(TEXT[lang]["result"], "back_result")],
                [(TEXT[lang]["home"], "home")],
            ]),
        )


    # -----------------------------------------------------
    # CUT LIST
    # -----------------------------------------------------

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
            reply_markup=kb([
                [(TEXT[lang]["rebar"], "show_rebar")],
                [(TEXT[lang]["result"], "back_result")],
                [(TEXT[lang]["home"], "home")],
            ]),
        )


    # -----------------------------------------------------
    # BACK TO RESULT
    # -----------------------------------------------------

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
            reply_markup=result_kb(lang),
        )


    # -----------------------------------------------------
    # NEW MEMBER
    # -----------------------------------------------------

    if data == "new_member":

        context.user_data.clear()

        context.user_data[
            "lang"
        ] = lang

        return await q.edit_message_text(
            TEXT[lang]["welcome"],
            parse_mode="HTML",
            reply_markup=main_menu(lang),
        )


    # -----------------------------------------------------
    # PROJECT SUMMARY
    # -----------------------------------------------------

    if data == "summary":

        if lang == "fa":

            text = (
                "📊 <b>خلاصه پروژه</b>\n\n"
                "فعلاً محاسبات به‌صورت عضو‌به‌عضو انجام می‌شوند.\n\n"
                "🔜 اتصال جمع کل پروژه در مرحله بعد تکمیل می‌شود."
            )

        elif lang == "ar":

            text = (
                "📊 <b>ملخص المشروع</b>\n\n"
                "حالياً يتم الحساب لكل عنصر بشكل مستقل.\n\n"
                "🔜 سيتم إضافة إجمالي المشروع في المرحلة التالية."
            )

        elif lang == "en":

            text = (
                "📊 <b>Project Summary</b>\n\n"
                "Calculations are currently performed member by member.\n\n"
                "🔜 Full project aggregation will be added in the next stage."
            )

        else:

            text = (
                "📊 <b>项目汇总</b>\n\n"
                "目前按构件分别进行计算。\n\n"
                "🔜 下一阶段将加入整个项目的汇总。"
            )

        return await q.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_kb(
                lang
            ),
        )


    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    if data == "settings":

        return await q.edit_message_text(
            f"⚙️ <b>{TEXT[lang]['settings']}</b>\n\n"
            f"{TEXT[lang]['change_language']}",
            parse_mode="HTML",
            reply_markup=kb([
                [
                    (
                        TEXT[lang]["change_language"],
                        "change_language"
                    )
                ],
                [
                    (
                        TEXT[lang]["back"],
                        "home"
                    )
                ],
            ]),
        )


    # -----------------------------------------------------
    # CHANGE LANGUAGE
    # -----------------------------------------------------

    if data == "change_language":

        return await q.edit_message_text(
            TEXT[lang]["choose_language"],
            reply_markup=language_keyboard(),
        )


    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    if data == "help":

        if lang == "fa":

            text = (
                "ℹ️ <b>راهنما</b>\n\n"
                "مقادیر واقعی عضو سازه‌ای را وارد کنید.\n\n"
                "ربات حجم بتن و مقدار میلگرد را بر اساس "
                "اطلاعات واردشده محاسبه می‌کند.\n\n"
                "⚠️ نتایج برآوردی هستند و جایگزین نقشه، "
                "دفترچه محاسبات و نظر مهندس محاسب نیستند."
            )

        elif lang == "ar":

            text = (
                "ℹ️ <b>المساعدة</b>\n\n"
                "أدخل الأبعاد والبيانات الفعلية للعناصر.\n\n"
                "يقوم البوت بحساب كمية الخرسانة والتسليح "
                "وفقاً للبيانات المدخلة.\n\n"
                "⚠️ النتائج تقديرية ولا تحل محل المخططات "
                "والحسابات الإنشائية."
            )

        elif lang == "en":

            text = (
                "ℹ️ <b>Help</b>\n\n"
                "Enter the actual dimensions and reinforcement data.\n\n"
                "The bot calculates concrete volume and rebar quantities "
                "from the entered information.\n\n"
                "⚠️ Results are estimates and do not replace structural "
                "drawings or engineering calculations."
            )

        else:

            text = (
                "ℹ️ <b>帮助</b>\n\n"
                "请输入构件的实际尺寸和钢筋信息。\n\n"
                "机器人根据输入数据计算混凝土和钢筋数量。\n\n"
                "⚠️ 结果为估算值，不能替代结构图纸和工程计算。"
            )

        return await q.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_kb(
                lang
            ),
        )


    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    await q.edit_message_text(
        TEXT[lang]["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu(lang),
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update,
    context
):

    logger.exception(
        "Unhandled bot error",
        exc_info=context.error
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
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            choose_language,
            pattern=r"^lang_(fa|ar|en|zh)$"
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
