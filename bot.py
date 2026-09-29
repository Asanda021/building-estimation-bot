# bot.py
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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
    column_rectangular,
    column_round,
    beam,
    tie_beam,
    wall_concrete,
    stair_slab,
    roof_slab,
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
# ENV
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است.")


# =========================================================
# LANGUAGES
# =========================================================

LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 English",
    "zh": "🇨🇳 中文",
}


TEXT = {

    # -----------------------------------------------------
    # MAIN
    # -----------------------------------------------------

    "title": {
        "fa": "🏗️ اسکلت بتنی",
        "ar": "🏗️ الهيكل الخرساني",
        "en": "🏗️ Concrete Structure",
        "zh": "🏗️ 混凝土结构",
    },

    "foundation": {
        "fa": "🧱 فونداسیون",
        "ar": "🧱 الأساسات",
        "en": "🧱 Foundation",
        "zh": "🧱 基础",
    },

    "columns": {
        "fa": "🏛️ ستون‌ها",
        "ar": "🏛️ الأعمدة",
        "en": "🏛️ Columns",
        "zh": "🏛️ 柱",
    },

    "beams": {
        "fa": "📐 تیرها",
        "ar": "📐 الكمرات",
        "en": "📐 Beams",
        "zh": "📐 梁",
    },

    "roofs": {
        "fa": "🏠 سقف‌ها",
        "ar": "🏠 الأسقف",
        "en": "🏠 Roofs",
        "zh": "🏠 楼板",
    },

    "stairs": {
        "fa": "🪜 راه‌پله",
        "ar": "🪜 السلالم",
        "en": "🪜 Stairs",
        "zh": "🪜 Stairs",
    },

    "ties": {
        "fa": "🔗 شناژ و کلاف",
        "ar": "🔗 الميدات والربط",
        "en": "🔗 Tie Beams",
        "zh": "🔗 系梁",
    },

    "walls": {
        "fa": "🧱 دیوارها",
        "ar": "🧱 الجدران",
        "en": "🧱 Walls",
        "zh": "🧱 墙体",
    },

    "summary": {
        "fa": "📊 خلاصه پروژه",
        "ar": "📊 ملخص المشروع",
        "en": "📊 Project Summary",
        "zh": "📊 项目汇总",
    },

    "settings": {
        "fa": "⚙️ تنظیمات",
        "ar": "⚙️ الإعدادات",
        "en": "⚙️ Settings",
        "zh": "⚙️ 设置",
    },

    "language": {
        "fa": "🌐 زبان",
        "ar": "🌐 اللغة",
        "en": "🌐 Language",
        "zh": "🌐 语言",
    },

    "help": {
        "fa": "ℹ️ راهنما",
        "ar": "ℹ️ المساعدة",
        "en": "ℹ️ Help",
        "zh": "ℹ️ 帮助",
    },

    "back": {
        "fa": "🔙 بازگشت",
        "ar": "🔙 رجوع",
        "en": "🔙 Back",
        "zh": "🔙 返回",
    },

    "home": {
        "fa": "🏠 منوی اصلی",
        "ar": "🏠 القائمة الرئيسية",
        "en": "🏠 Main Menu",
        "zh": "🏠 主菜单",
    },

    "select_language": {
        "fa": "🌐 زبان موردنظر را انتخاب کنید:",
        "ar": "🌐 اختر اللغة:",
        "en": "🌐 Select your language:",
        "zh": "🌐 请选择语言：",
    },

    "language_changed": {
        "fa": "✅ زبان با موفقیت تغییر کرد.",
        "ar": "✅ تم تغيير اللغة بنجاح.",
        "en": "✅ Language changed successfully.",
        "zh": "✅ 语言已成功更改。",
    },

    # -----------------------------------------------------
    # FOUNDATION
    # -----------------------------------------------------

    "isolated": {
        "fa": "پی منفرد",
        "ar": "قاعدة منفردة",
        "en": "Isolated Footing",
        "zh": "独立基础",
    },

    "strip": {
        "fa": "پی نواری",
        "ar": "قاعدة شريطية",
        "en": "Strip Footing",
        "zh": "条形基础",
    },

    "raft": {
        "fa": "پی گسترده (رادیه)",
        "ar": "لبشة",
        "en": "Raft Foundation",
        "zh": "筏板基础",
    },

    # -----------------------------------------------------
    # COLUMNS
    # -----------------------------------------------------

    "rect_column": {
        "fa": "ستون مربعی / مستطیلی",
        "ar": "عمود مربع / مستطيل",
        "en": "Rectangular Column",
        "zh": "矩形柱",
    },

    "round_column": {
        "fa": "ستون گرد",
        "ar": "عمود دائري",
        "en": "Round Column",
        "zh": "圆柱",
    },

    # -----------------------------------------------------
    # BEAMS
    # -----------------------------------------------------

    "main_beam": {
        "fa": "تیر اصلی",
        "ar": "كمرة رئيسية",
        "en": "Main Beam",
        "zh": "主梁",
    },

    "secondary_beam": {
        "fa": "تیر فرعی",
        "ar": "كمرة ثانوية",
        "en": "Secondary Beam",
        "zh": "次梁",
    },

    # -----------------------------------------------------
    # TIES
    # -----------------------------------------------------

    "tie_beam": {
        "fa": "شناژ",
        "ar": "ميدة",
        "en": "Tie Beam",
        "zh": "系梁",
    },

    "tie": {
        "fa": "کلاف",
        "ar": "رباط",
        "en": "Tie",
        "zh": "拉梁",
    },

    # -----------------------------------------------------
    # ROOFS
    # -----------------------------------------------------

    "joist_eps": {
        "fa": "تیرچه یونولیتی",
        "ar": "جوائز بلوك بوليسترين",
        "en": "EPS Joist Slab",
        "zh": "EPS 模块楼板",
    },

    "joist_clay": {
        "fa": "تیرچه سفالی",
        "ar": "جوائز بلوك فخاري",
        "en": "Clay Block Joist Slab",
        "zh": "陶土块楼板",
    },

    "double_joist": {
        "fa": "تیرچه دوبل",
        "ar": "جوائز مزدوجة",
        "en": "Double Joist",
        "zh": "双肋楼板",
    },

    "keromیت": {
        "fa": "کرومیت",
        "ar": "كروميت",
        "en": "Keramite",
        "zh": "克罗米特楼板",
    },

    "composite": {
        "fa": "کامپوزیت",
        "ar": "مركب",
        "en": "Composite",
        "zh": "组合楼板",
    },

    "steel_deck": {
        "fa": "عرشه فولادی",
        "ar": "سطح فولاذي",
        "en": "Steel Deck",
        "zh": "钢承板",
    },

    "concrete_slab": {
        "fa": "دال بتنی",
        "ar": "بلاطة خرسانية",
        "en": "Concrete Slab",
        "zh": "混凝土板",
    },

    "waffle": {
        "fa": "وافل",
        "ar": "وافل",
        "en": "Waffle Slab",
        "zh": "密肋楼板",
    },

    # -----------------------------------------------------
    # WALLS
    # -----------------------------------------------------

    "shear_wall": {
        "fa": "دیوار برشی",
        "ar": "جدار قص",
        "en": "Shear Wall",
        "zh": "剪力墙",
    },

    "retaining_wall": {
        "fa": "دیوار حائل",
        "ar": "جدار استنادي",
        "en": "Retaining Wall",
        "zh": "挡土墙",
    },

    # -----------------------------------------------------
    # COMMON
    # -----------------------------------------------------

    "enter": {
        "fa": "لطفاً مقدار را وارد کنید:",
        "ar": "يرجى إدخال القيمة:",
        "en": "Please enter the value:",
        "zh": "请输入数值：",
    },

    "cancel": {
        "fa": "❌ لغو",
        "ar": "❌ إلغاء",
        "en": "❌ Cancel",
        "zh": "❌ 取消",
    },

    "new_calculation": {
        "fa": "➕ محاسبه جدید",
        "ar": "➕ حساب جديد",
        "en": "➕ New Calculation",
        "zh": "➕ 新计算",
    },

    "invalid": {
        "fa": "⚠️ مقدار واردشده صحیح نیست. دوباره تلاش کنید.",
        "ar": "⚠️ القيمة المدخلة غير صحيحة. حاول مرة أخرى.",
        "en": "⚠️ Invalid value. Please try again.",
        "zh": "⚠️ 输入值无效，请重试。",
    },

    "help_text": {
        "fa": (
            "ℹ️ راهنمای ربات\n\n"
            "این ربات برای برآورد اولیه مقادیر بتن و میلگرد "
            "اجزای سازه بتنی طراحی شده است.\n\n"
            "از منوی اصلی عضو موردنظر را انتخاب کنید، "
            "ابعاد و مشخصات میلگرد را وارد کنید و نتیجه را دریافت کنید."
        ),
        "ar": (
            "ℹ️ دليل الاستخدام\n\n"
            "هذا البوت مخصص للتقدير الأولي لكميات الخرسانة "
            "والحديد في العناصر الخرسانية.\n\n"
            "اختر العنصر من القائمة الرئيسية ثم أدخل الأبعاد والتسليح."
        ),
        "en": (
            "ℹ️ Bot Guide\n\n"
            "This bot provides preliminary quantity estimation "
            "for concrete structural elements.\n\n"
            "Select an element, enter its dimensions and reinforcement "
            "data, and receive the calculated result."
        ),
        "zh": (
            "ℹ️ 使用说明\n\n"
            "本机器人用于混凝土结构构件的初步工程量估算。\n\n"
            "选择构件，输入尺寸和钢筋参数，即可获得计算结果。"
        ),
    },
}


# =========================================================
# ROOF COEFFICIENTS
# =========================================================

ROOF_TYPES = {
    "eps": 0.18,
    "clay": 0.20,
    "double": 0.23,
    "keromit": 0.18,
    "composite": 0.15,
    "steel_deck": 0.15,
    "concrete": 0.20,
    "waffle": 0.20,
}


# =========================================================
# HELPERS
# =========================================================

def lang_of(context):
    return context.user_data.get("lang", "fa")


def t(key, lang):
    return TEXT.get(key, {}).get(
        lang,
        TEXT.get(key, {}).get("fa", key)
    )


def main_menu_keyboard(lang):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t("foundation", lang),
                callback_data="menu_foundation"
            ),
            InlineKeyboardButton(
                t("columns", lang),
                callback_data="menu_columns"
            ),
        ],
        [
            InlineKeyboardButton(
                t("beams", lang),
                callback_data="menu_beams"
            ),
            InlineKeyboardButton(
                t("roofs", lang),
                callback_data="menu_roofs"
            ),
        ],
        [
            InlineKeyboardButton(
                t("stairs", lang),
                callback_data="menu_stairs"
            ),
            InlineKeyboardButton(
                t("ties", lang),
                callback_data="menu_ties"
            ),
        ],
        [
            InlineKeyboardButton(
                t("walls", lang),
                callback_data="menu_walls"
            ),
        ],
        [
            InlineKeyboardButton(
                t("summary", lang),
                callback_data="menu_summary"
            ),
        ],
        [
            InlineKeyboardButton(
                t("language", lang),
                callback_data="menu_language"
            ),
            InlineKeyboardButton(
                t("settings", lang),
                callback_data="menu_settings"
            ),
        ],
        [
            InlineKeyboardButton(
                t("help", lang),
                callback_data="menu_help"
            ),
        ],
    ])


def back_home_keyboard(lang, back_callback=None):
    buttons = []

    if back_callback:
        buttons.append(
            InlineKeyboardButton(
                t("back", lang),
                callback_data=back_callback
            )
        )

    buttons.append(
        InlineKeyboardButton(
            t("home", lang),
            callback_data="home"
        )
    )

    return InlineKeyboardMarkup([buttons])


def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🇮🇷 فارسی",
                callback_data="lang_fa"
            ),
            InlineKeyboardButton(
                "🇸🇦 العربية",
                callback_data="lang_ar"
            ),
        ],
        [
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_en"
            ),
            InlineKeyboardButton(
                "🇨🇳 中文",
                callback_data="lang_zh"
            ),
        ],
    ])


def save_result(context, title, result):
    """
    ذخیره نتیجه محاسبه در تاریخچه پروژه.
    """
    history = context.user_data.setdefault(
        "history",
        []
    )

    history.append({
        "title": title,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "result": result,
    })


def format_rebar(result, lang):
    details = result.get("rebar_details", [])

    if not details:
        return ""

    lines = [
        "",
        "🔩 میلگرد",
        "━━━━━━━━━━━━━━━━",
    ]

    for i, item in enumerate(details, 1):

        dia = item.get("diameter_mm", 0)
        count = item.get("piece_count", 0)
        length = item.get("length_m", 0)
        weight = item.get("weight_kg", 0)
        waste = item.get("waste_m", 0)

        lines.extend([
            f"میلگرد {i}",
            f"قطر:            Φ{dia}",
            f"تعداد:          {count} عدد",
            f"طول هر قطعه:    {length:.2f} m",
            f"وزن:            {weight:.1f} kg",
            f"پرت:            {waste:.2f} m",
            "━━━━━━━━━━━━━━━━",
        ])

    return "\n".join(lines)


def format_cut_list(result):
    details = result.get("rebar_details", [])

    if not details:
        return ""

    lines = [
        "",
        "✂️ Cut List",
        "━━━━━━━━━━━━━━━━",
    ]

    part = 1

    for item in details:

        diameter = item.get("diameter_mm", 0)
        piece_count = item.get("piece_count", 0)
        length = item.get("length_m", 0)

        cut_plan = item.get("cut_plan", [])

        if cut_plan:

            for plan in cut_plan:

                pieces = len(
                    plan.get("pieces", [])
                )

                used = sum(
                    float(x)
                    for x in plan.get("pieces", [])
                )

                waste = max(
                    0.0,
                    12.0 - used
                )

                lines.extend([
                    f"قطعه {part}",
                    f"قطر:            Φ{diameter}",
                    f"طول:            {length:.2f} m",
                    f"تعداد:          {pieces} عدد",
                    f"مصرف شاخه:      {used:.2f} m",
                    f"پرت شاخه:       {waste:.2f} m",
                    "━━━━━━━━━━━━━━━━",
                ])

                part += 1

        else:

            lines.extend([
                f"قطعه {part}",
                f"قطر:            Φ{diameter}",
                f"طول:            {length:.2f} m",
                f"تعداد:          {piece_count} عدد",
                "━━━━━━━━━━━━━━━━",
            ])

            part += 1

    return "\n".join(lines)


def result_text(title, result):
    concrete = result.get(
        "total_concrete_m3",
        result.get("concrete_m3", 0)
    )

    rebar = result.get(
        "total_rebar_kg",
        0
    )

    lines = [
        f"🏗️ {title}",
        "",
        "━━━━━━━━━━━━━━━━",
        f"بتن:            {concrete:.2f} m³",
        f"کل میلگرد:      {rebar:.1f} kg",
        "━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


def parse_float(text):
    text = text.strip().replace(",", ".")
    return float(text)


def parse_int(text):
    text = text.strip()
    return int(float(text))


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.setdefault(
        "lang",
        None
    )

    if not context.user_data.get("lang"):
        await update.message.reply_text(
            "🌐 زبان را انتخاب کنید / اختر اللغة / Select language / 选择语言",
            reply_markup=language_keyboard()
        )
        return

    lang = lang_of(context)

    await update.message.reply_text(
        t("title", lang),
        reply_markup=main_menu_keyboard(lang)
    )


# =========================================================
# HOME
# =========================================================

async def show_home(update, context):

    lang = lang_of(context)

    query = update.callback_query

    if query:
        await query.answer()
        await query.edit_message_text(
            t("title", lang),
            reply_markup=main_menu_keyboard(lang)
        )
    else:
        await update.message.reply_text(
            t("title", lang),
            reply_markup=main_menu_keyboard(lang)
        )


# =========================================================
# LANGUAGE
# =========================================================

async def show_language(update, context):

    query = update.callback_query

    await query.answer()

    lang = lang_of(context)

    await query.edit_message_text(
        t("select_language", lang),
        reply_markup=language_keyboard()
    )


async def select_language(update, context):

    query = update.callback_query

    await query.answer()

    new_lang = query.data.replace(
        "lang_",
        ""
    )

    if new_lang not in LANGUAGES:
        return

    context.user_data["lang"] = new_lang

    await query.edit_message_text(
        t("language_changed", new_lang),
        reply_markup=main_menu_keyboard(new_lang)
    )


# =========================================================
# FOUNDATION MENU
# =========================================================

async def foundation_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🧱 {t('isolated', lang)}",
                callback_data="calc_isolated"
            )
        ],
        [
            InlineKeyboardButton(
                f"🧱 {t('strip', lang)}",
                callback_data="calc_strip"
            )
        ],
        [
            InlineKeyboardButton(
                f"🧱 {t('raft', lang)}",
                callback_data="calc_raft"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            ),
        ],
    ])

    await query.edit_message_text(
        t("foundation", lang),
        reply_markup=keyboard
    )


# =========================================================
# COLUMN MENU
# =========================================================

async def column_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🏛️ {t('rect_column', lang)}",
                callback_data="calc_column_rect"
            )
        ],
        [
            InlineKeyboardButton(
                f"🏛️ {t('round_column', lang)}",
                callback_data="calc_column_round"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            ),
        ],
    ])

    await query.edit_message_text(
        t("columns", lang),
        reply_markup=keyboard
    )


# =========================================================
# BEAM MENU
# =========================================================

async def beam_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📐 {t('main_beam', lang)}",
                callback_data="calc_main_beam"
            )
        ],
        [
            InlineKeyboardButton(
                f"📐 {t('secondary_beam', lang)}",
                callback_data="calc_secondary_beam"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            ),
        ],
    ])

    await query.edit_message_text(
        t("beams", lang),
        reply_markup=keyboard
    )


# =========================================================
# TIE MENU
# =========================================================

async def tie_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🔗 {t('tie_beam', lang)}",
                callback_data="calc_tie_beam"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔗 {t('tie', lang)}",
                callback_data="calc_tie"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            ),
        ],
    ])

    await query.edit_message_text(
        t("ties", lang),
        reply_markup=keyboard
    )


# =========================================================
# WALL MENU
# =========================================================

async def wall_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🧱 {t('shear_wall', lang)}",
                callback_data="calc_shear_wall"
            )
        ],
        [
            InlineKeyboardButton(
                f"🧱 {t('retaining_wall', lang)}",
                callback_data="calc_retaining_wall"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            ),
        ],
    ])

    await query.edit_message_text(
        t("walls", lang),
        reply_markup=keyboard
    )


# =========================================================
# ROOF MENU
# =========================================================

async def roof_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    roof_buttons = [
        ("eps", "joist_eps"),
        ("clay", "joist_clay"),
        ("double", "double_joist"),
        ("keromit", "keromیت"),
        ("composite", "composite"),
        ("steel_deck", "steel_deck"),
        ("concrete", "concrete_slab"),
        ("waffle", "waffle"),
    ]

    rows = []

    for key, text_key in roof_buttons:

        rows.append([
            InlineKeyboardButton(
                f"🏠 {t(text_key, lang)}",
                callback_data=f"roof_{key}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            t("home", lang),
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        t("roofs", lang),
        reply_markup=InlineKeyboardMarkup(rows)
    )


# =========================================================
# SETTINGS
# =========================================================

async def settings_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t("language", lang),
                callback_data="menu_language"
            )
        ],
        [
            InlineKeyboardButton(
                t("home", lang),
                callback_data="home"
            )
        ],
    ])

    await query.edit_message_text(
        t("settings", lang),
        reply_markup=keyboard
    )


# =========================================================
# HELP
# =========================================================

async def help_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    await query.edit_message_text(
        t("help_text", lang),
        reply_markup=back_home_keyboard(lang)
    )


# =========================================================
# SUMMARY
# =========================================================

async def summary_menu(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    history = context.user_data.get(
        "history",
        []
    )

    if not history:

        text = (
            "📊 خلاصه پروژه\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "هنوز محاسبه‌ای در این پروژه ثبت نشده است."
        )

    else:

        total_concrete = 0.0
        total_rebar = 0.0

        for item in history:

            result = item.get(
                "result",
                {}
            )

            total_concrete += float(
                result.get(
                    "total_concrete_m3",
                    result.get(
                        "concrete_m3",
                        0
                    )
                )
                or 0
            )

            total_rebar += float(
                result.get(
                    "total_rebar_kg",
                    0
                )
                or 0
            )

        lines = [
            "📊 خلاصه پروژه",
            "",
            "━━━━━━━━━━━━━━━━",
            f"تعداد مراحل:      {len(history)}",
            f"کل بتن:           {total_concrete:.2f} m³",
            f"کل میلگرد:        {total_rebar:.1f} kg",
            "━━━━━━━━━━━━━━━━",
        ]

        text = "\n".join(lines)

    await query.edit_message_text(
        f"```text\n{text}\n```",
        parse_mode="Markdown",
        reply_markup=back_home_keyboard(lang)
    )


# =========================================================
# SIMPLE CALCULATION DISPATCH
# =========================================================

async def calculation_start(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    calc = query.data

    context.user_data["calc"] = calc
    context.user_data["step"] = 0
    context.user_data["inputs"] = []

    prompts = {

        "calc_isolated": [
            "تعداد پی",
            "طول پی (m)",
            "عرض پی (m)",
            "ضخامت پی (m)",
            "طول مگر (m)",
            "عرض مگر (m)",
            "ضخامت مگر (m)",
            "قطر میلگرد پایین",
            "فاصله میلگرد پایین (mm)",
            "قطر میلگرد بالا",
            "فاصله میلگرد بالا (mm)",
            "کاور (mm)",
            "اورلپ (%)",
            "طول پدستال (m)",
            "عرض پدستال (m)",
            "ارتفاع پدستال (m)",
        ],

        "calc_strip": [
            "تعداد پی نواری",
            "طول (m)",
            "عرض (m)",
            "ضخامت (m)",
            "طول مگر (m)",
            "عرض مگر (m)",
            "ضخامت مگر (m)",
            "قطر میلگرد طولی پایین",
            "تعداد میلگرد طولی پایین",
            "قطر میلگرد عرضی پایین",
            "فاصله میلگرد عرضی پایین (mm)",
            "قطر میلگرد طولی بالا",
            "تعداد میلگرد طولی بالا",
            "قطر میلگرد عرضی بالا",
            "فاصله میلگرد عرضی بالا (mm)",
            "کاور (mm)",
            "اورلپ (%)",
        ],

        "calc_raft": [
            "طول رادیه (m)",
            "عرض رادیه (m)",
            "ضخامت (m)",
            "طول مگر (m)",
            "عرض مگر (m)",
            "ضخامت مگر (m)",
            "قطر پایین X",
            "فاصله پایین X (mm)",
            "قطر پایین Y",
            "فاصله پایین Y (mm)",
            "قطر بالا X",
            "فاصله بالا X (mm)",
            "قطر بالا Y",
            "فاصله بالا Y (mm)",
            "کاور (mm)",
            "اورلپ (%)",
        ],

        "calc_column_rect": [
            "تعداد ستون",
            "عرض ستون (m)",
            "عمق ستون (m)",
            "ارتفاع ستون (m)",
            "قطر میلگرد طولی",
            "تعداد میلگرد طولی",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_column_round": [
            "تعداد ستون",
            "قطر ستون (m)",
            "ارتفاع ستون (m)",
            "قطر میلگرد طولی",
            "تعداد میلگرد طولی",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_main_beam": [
            "تعداد تیر",
            "طول تیر (m)",
            "عرض تیر (m)",
            "ارتفاع تیر (m)",
            "قطر میلگرد پایین",
            "تعداد میلگرد پایین",
            "قطر میلگرد بالا",
            "تعداد میلگرد بالا",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_secondary_beam": [
            "تعداد تیر",
            "طول تیر (m)",
            "عرض تیر (m)",
            "ارتفاع تیر (m)",
            "قطر میلگرد پایین",
            "تعداد میلگرد پایین",
            "قطر میلگرد بالا",
            "تعداد میلگرد بالا",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_tie_beam": [
            "تعداد شناژ",
            "طول (m)",
            "عرض (m)",
            "ارتفاع (m)",
            "قطر میلگرد طولی",
            "تعداد میلگرد طولی",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_tie": [
            "تعداد کلاف",
            "طول (m)",
            "عرض (m)",
            "ارتفاع (m)",
            "قطر میلگرد طولی",
            "تعداد میلگرد طولی",
            "قطر خاموت",
            "فاصله خاموت (mm)",
            "کاور (mm)",
        ],

        "calc_shear_wall": [
            "طول دیوار (m)",
            "ارتفاع دیوار (m)",
            "ضخامت دیوار (m)",
            "قطر میلگرد قائم",
            "فاصله قائم (mm)",
            "قطر میلگرد افقی",
            "فاصله افقی (mm)",
            "کاور (mm)",
        ],

        "calc_retaining_wall": [
            "طول دیوار (m)",
            "ارتفاع دیوار (m)",
            "ضخامت دیوار (m)",
            "قطر میلگرد قائم",
            "فاصله قائم (mm)",
            "قطر میلگرد افقی",
            "فاصله افقی (mm)",
            "کاور (mm)",
        ],
    }

    if calc not in prompts:
        return

    context.user_data["prompts"] = prompts[calc]

    await query.edit_message_text(
        f"🏗️ {prompts[calc][0]}\n\n{t('enter', lang)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t("cancel", lang),
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# MESSAGE INPUT
# =========================================================

async def handle_input(update, context):

    if "calc" not in context.user_data:
        return

    calc = context.user_data["calc"]

    prompts = context.user_data.get(
        "prompts",
        []
    )

    step = context.user_data.get(
        "step",
        0
    )

    try:
        value = parse_float(
            update.message.text
        )
    except Exception:

        lang = lang_of(context)

        await update.message.reply_text(
            t("invalid", lang)
        )

        return

    context.user_data["inputs"].append(
        value
    )

    step += 1
    context.user_data["step"] = step

    lang = lang_of(context)

    if step < len(prompts):

        await update.message.reply_text(
            f"🏗️ {prompts[step]}\n\n{t('enter', lang)}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        t("cancel", lang),
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    try:

        result = execute_calculation(
            calc,
            context.user_data["inputs"]
        )

        title = calc_title(
            calc,
            lang
        )

        save_result(
            context,
            title,
            result
        )

        text = (
            "```text\n"
            + result_text(
                title,
                result
            )
            + format_rebar(result, lang)
            + format_cut_list(result)
            + "\n```"
        )

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        t("new_calculation", lang),
                        callback_data="home"
                    )
                ],
                [
                    InlineKeyboardButton(
                        t("summary", lang),
                        callback_data="menu_summary"
                    )
                ],
            ])
        )

    except Exception as e:

        logger.exception(
            "Calculation error"
        )

        await update.message.reply_text(
            f"⚠️ خطا در محاسبه:\n{e}"
        )

    finally:

        context.user_data.pop(
            "calc",
            None
        )

        context.user_data.pop(
            "step",
            None
        )

        context.user_data.pop(
            "inputs",
            None
        )

        context.user_data.pop(
            "prompts",
            None
        )


# =========================================================
# CALCULATION EXECUTION
# =========================================================

def execute_calculation(calc, x):

    if calc == "calc_isolated":

        return isolated_footing(
            count=int(x[0]),
            L=x[1],
            W=x[2],
            T=x[3],
            leanL=x[4],
            leanW=x[5],
            leanT=x[6],
            bd=int(x[7]),
            bs=x[8],
            td=int(x[9]),
            ts=x[10],
            cover=x[11],
            lap=x[12],
            pl=x[13],
            pw=x[14],
            ph=x[15],
        )

    if calc == "calc_strip":

        return strip_footing(
            count=int(x[0]),
            L=x[1],
            W=x[2],
            T=x[3],
            leanL=x[4],
            leanW=x[5],
            leanT=x[6],
            ld=int(x[7]),
            lc=int(x[8]),
            td=int(x[9]),
            ts=x[10],
            tld=int(x[11]),
            tlc=int(x[12]),
            ttd=int(x[13]),
            tts=x[14],
            cover=x[15],
            lap=x[16],
        )

    if calc == "calc_raft":

        return raft_foundation(
            L=x[0],
            W=x[1],
            T=x[2],
            leanL=x[3],
            leanW=x[4],
            leanT=x[5],
            bxd=int(x[6]),
            bxs=x[7],
            byd=int(x[8]),
            bys=x[9],
            txd=int(x[10]),
            txs=x[11],
            tyd=int(x[12]),
            tys=x[13],
            cover=x[14],
            lap=x[15],
        )

    if calc == "calc_column_rect":

        return column_rectangular(
            count=int(x[0]),
            W=x[1],
            D=x[2],
            H=x[3],
            ld=int(x[4]),
            lc=int(x[5]),
            sd=int(x[6]),
            ss=x[7],
            cover=x[8],
        )

    if calc == "calc_column_round":

        return column_round(
            count=int(x[0]),
            D=x[1],
            H=x[2],
            ld=int(x[3]),
            lc=int(x[4]),
            sd=int(x[5]),
            ss=x[6],
            cover=x[7],
        )

    if calc in (
        "calc_main_beam",
        "calc_secondary_beam",
    ):

        return beam(
            count=int(x[0]),
            L=x[1],
            W=x[2],
            H=x[3],
            bd=int(x[4]),
            bc=int(x[5]),
            td=int(x[6]),
            tc=int(x[7]),
            sd=int(x[8]),
            ss=x[9],
            cover=x[10],
        )

    if calc in (
        "calc_tie_beam",
        "calc_tie",
    ):

        return tie_beam(
            count=int(x[0]),
            L=x[1],
            W=x[2],
            H=x[3],
            ld=int(x[4]),
            lc=int(x[5]),
            sd=int(x[6]),
            ss=x[7],
            cover=x[8],
        )

    if calc in (
        "calc_shear_wall",
        "calc_retaining_wall",
    ):

        return wall_concrete(
            L=x[0],
            H=x[1],
            T=x[2],
            vd=int(x[3]),
            vs=x[4],
            hd=int(x[5]),
            hs=x[6],
            cover=x[7],
        )

    raise ValueError(
        "محاسبه موردنظر پیدا نشد."
    )


# =========================================================
# CALC TITLES
# =========================================================

def calc_title(calc, lang):

    mapping = {

        "calc_isolated": "isolated",
        "calc_strip": "strip",
        "calc_raft": "raft",

        "calc_column_rect": "rect_column",
        "calc_column_round": "round_column",

        "calc_main_beam": "main_beam",
        "calc_secondary_beam": "secondary_beam",

        "calc_tie_beam": "tie_beam",
        "calc_tie": "tie",

        "calc_shear_wall": "shear_wall",
        "calc_retaining_wall": "retaining_wall",
    }

    key = mapping.get(
        calc,
        "title"
    )

    return t(
        key,
        lang
    )


# =========================================================
# ROOF CALCULATION
# =========================================================

async def roof_start(update, context):

    query = update.callback_query
    await query.answer()

    lang = lang_of(context)

    roof_key = query.data.replace(
        "roof_",
        ""
    )

    if roof_key not in ROOF_TYPES:
        return

    context.user_data["roof_key"] = roof_key
    context.user_data["calc"] = "roof"
    context.user_data["roof_step"] = 0
    context.user_data["roof_inputs"] = []

    prompts = [
        "مساحت سقف (m²)",
        "قطر میلگرد مصرفی",
        "مقدار میلگرد (kg/m²)",
    ]

    context.user_data["roof_prompts"] = prompts

    await query.edit_message_text(
        f"🏠 {t('roofs', lang)}\n\n"
        f"{prompts[0]}\n\n"
        f"{t('enter', lang)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t("cancel", lang),
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# ROOF INPUT
# =========================================================

async def handle_roof_input(update, context):

    if context.user_data.get("calc") != "roof":
        return

    lang = lang_of(context)

    try:
        value = parse_float(
            update.message.text
        )
    except Exception:

        await update.message.reply_text(
            t("invalid", lang)
        )

        return

    context.user_data["roof_inputs"].append(
        value
    )

    step = context.user_data.get(
        "roof_step",
        0
    ) + 1

    context.user_data["roof_step"] = step

    prompts = context.user_data[
        "roof_prompts"
    ]

    if step < len(prompts):

        await update.message.reply_text(
            f"{prompts[step]}\n\n{t('enter', lang)}"
        )

        return

    roof_key = context.user_data[
        "roof_key"
    ]

    area = context.user_data[
        "roof_inputs"
    ][0]

    dia = int(
        context.user_data[
            "roof_inputs"
        ][1]
    )

    kgm2 = context.user_data[
        "roof_inputs"
    ][2]

    coeff = ROOF_TYPES[
        roof_key
    ]

    result = roof_slab(
        area=area,
        coeff=coeff,
        dia=dia,
        kgm2=kgm2,
    )

    title_keys = {
        "eps": "joist_eps",
        "clay": "joist_clay",
        "double": "double_joist",
        "keromit": "keromیت",
        "composite": "composite",
        "steel_deck": "steel_deck",
        "concrete": "concrete_slab",
        "waffle": "waffle",
    }

    title = t(
        title_keys[roof_key],
        lang
    )

    save_result(
        context,
        title,
        result
    )

    text = (
        "```text\n"
        + result_text(
            title,
            result
        )
        + format_rebar(result, lang)
        + format_cut_list(result)
        + "\n```"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t("new_calculation", lang),
                    callback_data="home"
                )
            ],
            [
                InlineKeyboardButton(
                    t("summary", lang),
                    callback_data="menu_summary"
                )
            ],
        ])
    )

    context.user_data.pop(
        "calc",
        None
    )

    context.user_data.pop(
        "roof_key",
        None
    )

    context.user_data.pop(
        "roof_step",
        None
    )

    context.user_data.pop(
        "roof_inputs",
        None
    )

    context.user_data.pop(
        "roof_prompts",
        None
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(update, context):

    query = update.callback_query

    data = query.data

    # -------------------------
    # HOME
    # -------------------------

    if data == "home":
        await show_home(
            update,
            context
        )
        return

    # -------------------------
    # LANGUAGE
    # -------------------------

    if data == "menu_language":
        await show_language(
            update,
            context
        )
        return

    if data.startswith("lang_"):
        await select_language(
            update,
            context
        )
        return

    # -------------------------
    # MENUS
    # -------------------------

    if data == "menu_foundation":
        await foundation_menu(
            update,
            context
        )
        return

    if data == "menu_columns":
        await column_menu(
            update,
            context
        )
        return

    if data == "menu_beams":
        await beam_menu(
            update,
            context
        )
        return

    if data == "menu_roofs":
        await roof_menu(
            update,
            context
        )
        return

    if data == "menu_ties":
        await tie_menu(
            update,
            context
        )
        return

    if data == "menu_walls":
        await wall_menu(
            update,
            context
        )
        return

    if data == "menu_stairs":

        lang = lang_of(context)

        await query.answer()

        await query.edit_message_text(
            t("stairs", lang),
            reply_markup=back_home_keyboard(
                lang
            )
        )

        return

    if data == "menu_settings":
        await settings_menu(
            update,
            context
        )
        return

    if data == "menu_help":
        await help_menu(
            update,
            context
        )
        return

    if data == "menu_summary":
        await summary_menu(
            update,
            context
        )
        return

    # -------------------------
    # CALCULATIONS
    # -------------------------

    if data.startswith("calc_"):

        await calculation_start(
            update,
            context
        )

        return

    # -------------------------
    # ROOF
    # -------------------------

    if data.startswith("roof_"):

        await roof_start(
            update,
            context
        )

        return


# =========================================================
# TEXT ROUTER
# =========================================================

async def text_router(update, context):

    if context.user_data.get(
        "calc"
    ) == "roof":

        await handle_roof_input(
            update,
            context
        )

        return

    if context.user_data.get(
        "calc"
    ):

        await handle_input(
            update,
            context
        )

        return


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    logger.exception(
        "Unhandled exception:",
        exc_info=context.error
    )


# =========================================================
# APPLICATION
# =========================================================

def build_application():

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
            callback_router
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_router
        )
    )

    application.add_error_handler(
        error_handler
    )

    return application


# =========================================================
# RENDER / WEBHOOK
# =========================================================

def main():

    application = build_application()

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    render_url = os.getenv(
        "RENDER_EXTERNAL_URL"
    )

    webhook_url = os.getenv(
        "WEBHOOK_URL"
    )

    if not webhook_url and render_url:
        webhook_url = render_url

    if webhook_url:

        webhook_url = webhook_url.rstrip(
            "/"
        )

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}",
        )

    else:

        application.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
