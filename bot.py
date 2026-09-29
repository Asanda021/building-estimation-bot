import os
import html
import traceback
from collections import Counter

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
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
    total_foundation_result,
    column_rectangular,
    column_round,
    beam,
    tie_beam,
    wall_concrete,
    stair_slab,
    roof_slab,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")


# =========================================================
# LANGUAGE
# =========================================================

LANGS = {
    "fa": "🇮🇷 فارسی",
    "ar": "🇸🇦 العربية",
    "en": "🇬🇧 English",
    "zh": "🇨🇳 中文",
}


T = {
    "fa": {
        "home_title": "🏗️ اسکلت بتنی",
        "foundation": "🧱 فونداسیون",
        "columns": "🏛️ ستون‌ها",
        "beams": "📐 تیرها",
        "roofs": "🏠 سقف‌ها",
        "stairs": "🪜 راه‌پله",
        "ties": "🔗 شناژ و کلاف",
        "walls": "🧱 دیوارها",
        "summary": "📊 خلاصه پروژه",
        "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما",
        "home": "🏠 خانه",
        "menu": "☰ منو",
        "back": "🔙 بازگشت",
        "cancel": "❌ لغو",
        "language": "🌐 زبان",
        "language_changed": "زبان با موفقیت تغییر کرد.",
        "choose_language": "زبان موردنظر را انتخاب کنید:",
        "start": "سلام 👋\nبه ربات برآورد اسکلت بتنی خوش آمدید.",
        "cancelled": "عملیات لغو شد.",
        "invalid_number": "❌ مقدار واردشده معتبر نیست.\nلطفاً فقط عدد وارد کنید.",
        "positive_number": "❌ مقدار باید بزرگ‌تر از صفر باشد.",
        "zero_allowed": "برای حذف این بخش عدد 0 وارد کنید.",
        "done": "✅ محاسبه با موفقیت انجام شد.",
        "no_summary": "هنوز محاسبه‌ای برای پروژه ثبت نشده است.",
        "project_summary": "📊 خلاصه پروژه",
        "rebar": "🔩 جزئیات میلگرد",
        "cutlist": "✂️ Cut List",
        "new_calc": "🔄 محاسبه جدید",
        "save_result": "نتیجه در خلاصه پروژه ثبت شد.",
        "help_text": (
            "ℹ️ راهنما\n\n"
            "این ربات برای برآورد مقادیر اسکلت بتنی طراحی شده است.\n\n"
            "مقادیر بتن، میلگرد، طول قطعات و Cut List بر اساس "
            "اطلاعات واردشده محاسبه می‌شوند.\n\n"
            "⚠️ این ابزار برای متره و برآورد است و جایگزین طراحی سازه، "
            "نقشه محاسباتی و کنترل مهندس محاسب نیست."
        ),

        "isolated": "پی منفرد",
        "strip": "پی نواری",
        "raft": "پی گسترده (رادیه)",

        "rect_column": "ستون مربعی/مستطیلی",
        "round_column": "ستون گرد",

        "main_beam": "تیر اصلی",
        "secondary_beam": "تیر فرعی",

        "tie_beam": "شناژ",
        "tie_collar": "کلاف",

        "shear_wall": "دیوار برشی",
        "retaining_wall": "دیوار حائل",

        "stair_slab": "راه‌پله",

        "roof_joist_foam": "تیرچه یونولیتی",
        "roof_joist_clay": "تیرچه سفالی",
        "roof_double_joist": "تیرچه دوبل",
        "roof_keromet": "کرومیت",
        "roof_composite": "کامپوزیت",
        "roof_deck": "عرشه فولادی",
        "roof_slab": "دال بتنی",
        "roof_waffle": "وافل",

        "count": "تعداد",
        "length": "طول",
        "width": "عرض",
        "height": "ارتفاع",
        "thickness": "ضخامت",
        "diameter": "قطر",
        "spacing": "فاصله",
        "cover": "کاور",
        "lap": "اورلپ",
        "lean_length": "طول بتن مگر",
        "lean_width": "عرض بتن مگر",
        "lean_thickness": "ضخامت بتن مگر",
        "pedestal_length": "طول پدستال",
        "pedestal_width": "عرض پدستال",
        "pedestal_height": "ارتفاع پدستال",

        "bottom_diameter": "قطر میلگرد پایین",
        "bottom_spacing": "فاصله میلگرد پایین",
        "top_diameter": "قطر میلگرد بالا",
        "top_spacing": "فاصله میلگرد بالا",

        "longitudinal_diameter": "قطر میلگرد طولی",
        "longitudinal_count": "تعداد میلگرد طولی",
        "transverse_diameter": "قطر میلگرد عرضی",
        "transverse_spacing": "فاصله میلگرد عرضی",

        "top_longitudinal_diameter": "قطر میلگرد طولی بالا",
        "top_longitudinal_count": "تعداد میلگرد طولی بالا",
        "top_transverse_diameter": "قطر میلگرد عرضی بالا",
        "top_transverse_spacing": "فاصله میلگرد عرضی بالا",

        "bottom_x_diameter": "قطر میلگرد پایین X",
        "bottom_x_spacing": "فاصله میلگرد پایین X",
        "bottom_y_diameter": "قطر میلگرد پایین Y",
        "bottom_y_spacing": "فاصله میلگرد پایین Y",
        "top_x_diameter": "قطر میلگرد بالا X",
        "top_x_spacing": "فاصله میلگرد بالا X",
        "top_y_diameter": "قطر میلگرد بالا Y",
        "top_y_spacing": "فاصله میلگرد بالا Y",

        "main_diameter": "قطر میلگرد اصلی",
        "main_count": "تعداد میلگرد اصلی",
        "main_top_count": "تعداد میلگرد بالایی",
        "main_bottom_count": "تعداد میلگرد پایینی",
        "stirrup_diameter": "قطر خاموت",
        "stirrup_spacing": "فاصله خاموت",

        "vertical_diameter": "قطر میلگرد قائم",
        "vertical_spacing": "فاصله میلگرد قائم",
        "horizontal_diameter": "قطر میلگرد افقی",
        "horizontal_spacing": "فاصله میلگرد افقی",

        "area": "مساحت سقف",
        "rebar_kg_m2": "میلگرد به ازای هر مترمربع",
        "steps": "تعداد پله",
        "riser": "ارتفاع کف تا کف پله",
        "tread": "عرض کف پله",

        "ask_count": "تعداد را وارد کنید:",
        "ask_length": "طول را وارد کنید (متر):",
        "ask_width": "عرض را وارد کنید (متر):",
        "ask_height": "ارتفاع را وارد کنید (متر):",
        "ask_thickness": "ضخامت را وارد کنید (متر):",
        "ask_diameter": "قطر میلگرد را وارد کنید (میلی‌متر):",
        "ask_spacing": "فاصله را وارد کنید (میلی‌متر):",
        "ask_cover": "کاور را وارد کنید (میلی‌متر):",
        "ask_lap": "اورلپ را به درصد وارد کنید:",
        "ask_zero": "برای حذف این بخش عدد 0 وارد کنید.",

        "result_title": "🏗️ نتیجه محاسبه",
        "concrete": "بتن",
        "lean_concrete": "بتن مگر",
        "pedestal": "بتن پدستال",
        "total_concrete": "کل بتن",
        "total_rebar": "کل میلگرد",

        "piece": "قطعه",
        "piece_count": "تعداد",
        "piece_length": "طول هر قطعه",
        "weight": "وزن",
        "bars12": "شاخه ۱۲ متری",
        "waste": "پرت",
        "diameter_label": "قطر",
        "bar": "میلگرد",
        "branch": "شاخه",
        "branch_length": "طول شاخه",
        "pieces": "قطعات",
        "description": "شرح",

        "no_data": "داده‌ای برای نمایش وجود ندارد.",
    },

    "ar": {
        "home_title": "🏗️ الهيكل الخرساني",
        "foundation": "🧱 الأساسات",
        "columns": "🏛️ الأعمدة",
        "beams": "📐 الكمرات",
        "roofs": "🏠 الأسقف",
        "stairs": "🪜 الدرج",
        "ties": "🔗 الميدات والرباط",
        "walls": "🧱 الجدران",
        "summary": "📊 ملخص المشروع",
        "settings": "⚙️ الإعدادات",
        "help": "ℹ️ المساعدة",
        "home": "🏠 الرئيسية",
        "menu": "☰ القائمة",
        "back": "🔙 رجوع",
        "cancel": "❌ إلغاء",
        "language": "🌐 اللغة",
        "language_changed": "تم تغيير اللغة بنجاح.",
        "choose_language": "اختر اللغة:",
        "start": "مرحباً 👋\nأهلاً بك في روبوت تقدير الهيكل الخرساني.",
        "cancelled": "تم إلغاء العملية.",
        "invalid_number": "❌ القيمة غير صحيحة. أدخل رقماً فقط.",
        "positive_number": "❌ يجب أن تكون القيمة أكبر من صفر.",
        "zero_allowed": "أدخل 0 لإلغاء هذا الجزء.",
        "done": "✅ تمت العملية بنجاح.",
        "no_summary": "لم يتم تسجيل أي حساب للمشروع بعد.",
        "project_summary": "📊 ملخص المشروع",
        "rebar": "🔩 تفاصيل حديد التسليح",
        "cutlist": "✂️ قائمة القص",
        "new_calc": "🔄 حساب جديد",
        "save_result": "تم حفظ النتيجة في ملخص المشروع.",
        "help_text": (
            "ℹ️ المساعدة\n\n"
            "هذا الروبوت مخصص لتقدير كميات الهيكل الخرساني.\n\n"
            "يحسب الخرسانة والتسليح وأطوال القطع وقائمة القص "
            "حسب البيانات المدخلة.\n\n"
            "⚠️ الأداة للمتر والحصر ولا تغني عن التصميم الإنشائي "
            "والمخططات ومراجعة المهندس."
        ),

        "isolated": "قاعدة منفردة",
        "strip": "قاعدة شريطية",
        "raft": "لبشة",

        "rect_column": "عمود مربع/مستطيل",
        "round_column": "عمود دائري",

        "main_beam": "كمرة رئيسية",
        "secondary_beam": "كمرة ثانوية",

        "tie_beam": "ميدة",
        "tie_collar": "رباط",

        "shear_wall": "جدار قص",
        "retaining_wall": "جدار ساند",
        "stair_slab": "درج",

        "roof_joist_foam": "بلوك فوم",
        "roof_joist_clay": "بلوك فخاري",
        "roof_double_joist": "جوائز مزدوجة",
        "roof_keromet": "كروميت",
        "roof_composite": "سقف مركب",
        "roof_deck": "عرشة فولاذية",
        "roof_slab": "بلاطة خرسانية",
        "roof_waffle": "وافل",

        "count": "العدد",
        "length": "الطول",
        "width": "العرض",
        "height": "الارتفاع",
        "thickness": "السماكة",
        "diameter": "القطر",
        "spacing": "المسافة",
        "cover": "الغطاء الخرساني",
        "lap": "التراكب",
        "lean_length": "طول خرسانة النظافة",
        "lean_width": "عرض خرسانة النظافة",
        "lean_thickness": "سماكة خرسانة النظافة",
        "pedestal_length": "طول البيدستال",
        "pedestal_width": "عرض البيدستال",
        "pedestal_height": "ارتفاع البيدستال",

        "bottom_diameter": "قطر الحديد السفلي",
        "bottom_spacing": "مسافة الحديد السفلي",
        "top_diameter": "قطر الحديد العلوي",
        "top_spacing": "مسافة الحديد العلوي",

        "longitudinal_diameter": "قطر الحديد الطولي",
        "longitudinal_count": "عدد الحديد الطولي",
        "transverse_diameter": "قطر الحديد العرضي",
        "transverse_spacing": "مسافة الحديد العرضي",

        "top_longitudinal_diameter": "قطر الحديد الطولي العلوي",
        "top_longitudinal_count": "عدد الحديد الطولي العلوي",
        "top_transverse_diameter": "قطر الحديد العرضي العلوي",
        "top_transverse_spacing": "مسافة الحديد العرضي العلوي",

        "bottom_x_diameter": "قطر الحديد السفلي X",
        "bottom_x_spacing": "مسافة الحديد السفلي X",
        "bottom_y_diameter": "قطر الحديد السفلي Y",
        "bottom_y_spacing": "مسافة الحديد السفلي Y",
        "top_x_diameter": "قطر الحديد العلوي X",
        "top_x_spacing": "مسافة الحديد العلوي X",
        "top_y_diameter": "قطر الحديد العلوي Y",
        "top_y_spacing": "مسافة الحديد العلوي Y",

        "main_diameter": "قطر الحديد الرئيسي",
        "main_count": "عدد الحديد الرئيسي",
        "main_top_count": "عدد الحديد العلوي",
        "main_bottom_count": "عدد الحديد السفلي",
        "stirrup_diameter": "قطر الكانة",
        "stirrup_spacing": "مسافة الكانات",

        "vertical_diameter": "قطر الحديد الرأسي",
        "vertical_spacing": "مسافة الحديد الرأسي",
        "horizontal_diameter": "قطر الحديد الأفقي",
        "horizontal_spacing": "مسافة الحديد الأفقي",

        "area": "مساحة السقف",
        "rebar_kg_m2": "حديد لكل متر مربع",
        "steps": "عدد الدرجات",
        "riser": "ارتفاع القائمة",
        "tread": "عرض النائمة",

        "ask_count": "أدخل العدد:",
        "ask_length": "أدخل الطول (متر):",
        "ask_width": "أدخل العرض (متر):",
        "ask_height": "أدخل الارتفاع (متر):",
        "ask_thickness": "أدخل السماكة (متر):",
        "ask_diameter": "أدخل قطر الحديد (ملم):",
        "ask_spacing": "أدخل المسافة (ملم):",
        "ask_cover": "أدخل الغطاء الخرساني (ملم):",
        "ask_lap": "أدخل نسبة التراكب:",
        "ask_zero": "أدخل 0 لإلغاء هذا الجزء.",

        "result_title": "🏗️ نتيجة الحساب",
        "concrete": "الخرسانة",
        "lean_concrete": "خرسانة النظافة",
        "pedestal": "خرسانة البيدستال",
        "total_concrete": "إجمالي الخرسانة",
        "total_rebar": "إجمالي الحديد",

        "piece": "قطعة",
        "piece_count": "العدد",
        "piece_length": "طول القطعة",
        "weight": "الوزن",
        "bars12": "أعواد 12 متر",
        "waste": "الهدر",
        "diameter_label": "القطر",
        "bar": "حديد",
        "branch": "عود",
        "branch_length": "طول العود",
        "pieces": "القطع",
        "description": "الوصف",

        "no_data": "لا توجد بيانات للعرض.",
    },

    "en": {
        "home_title": "🏗️ Concrete Structure",
        "foundation": "🧱 Foundations",
        "columns": "🏛️ Columns",
        "beams": "📐 Beams",
        "roofs": "🏠 Roofs",
        "stairs": "🪜 Stairs",
        "ties": "🔗 Tie Beams",
        "walls": "🧱 Walls",
        "summary": "📊 Project Summary",
        "settings": "⚙️ Settings",
        "help": "ℹ️ Help",
        "home": "🏠 Home",
        "menu": "☰ Menu",
        "back": "🔙 Back",
        "cancel": "❌ Cancel",
        "language": "🌐 Language",
        "language_changed": "Language changed successfully.",
        "choose_language": "Choose language:",
        "start": "Hello 👋\nWelcome to the Concrete Structure Quantity Bot.",
        "cancelled": "Operation cancelled.",
        "invalid_number": "❌ Invalid value. Please enter a number.",
        "positive_number": "❌ Value must be greater than zero.",
        "zero_allowed": "Enter 0 to remove this part.",
        "done": "✅ Calculation completed successfully.",
        "no_summary": "No calculation has been recorded yet.",
        "project_summary": "📊 Project Summary",
        "rebar": "🔩 Rebar Details",
        "cutlist": "✂️ Cut List",
        "new_calc": "🔄 New Calculation",
        "save_result": "Result saved to project summary.",
        "help_text": (
            "ℹ️ Help\n\n"
            "This bot estimates concrete structure quantities.\n\n"
            "It calculates concrete, reinforcement, piece lengths "
            "and cutting lists from the entered data.\n\n"
            "⚠️ This is a quantity takeoff tool and does not replace "
            "structural design, drawings or engineering review."
        ),

        "isolated": "Isolated Footing",
        "strip": "Strip Footing",
        "raft": "Raft Foundation",

        "rect_column": "Rectangular Column",
        "round_column": "Round Column",

        "main_beam": "Main Beam",
        "secondary_beam": "Secondary Beam",

        "tie_beam": "Tie Beam",
        "tie_collar": "Collar Beam",

        "shear_wall": "Shear Wall",
        "retaining_wall": "Retaining Wall",

        "stair_slab": "Stair",

        "roof_joist_foam": "Foam Joist",
        "roof_joist_clay": "Clay Joist",
        "roof_double_joist": "Double Joist",
        "roof_keromet": "Kromit",
        "roof_composite": "Composite",
        "roof_deck": "Steel Deck",
        "roof_slab": "Concrete Slab",
        "roof_waffle": "Waffle",

        "count": "Count",
        "length": "Length",
        "width": "Width",
        "height": "Height",
        "thickness": "Thickness",
        "diameter": "Diameter",
        "spacing": "Spacing",
        "cover": "Concrete Cover",
        "lap": "Lap",
        "lean_length": "Lean Concrete Length",
        "lean_width": "Lean Concrete Width",
        "lean_thickness": "Lean Concrete Thickness",
        "pedestal_length": "Pedestal Length",
        "pedestal_width": "Pedestal Width",
        "pedestal_height": "Pedestal Height",

        "bottom_diameter": "Bottom Rebar Diameter",
        "bottom_spacing": "Bottom Rebar Spacing",
        "top_diameter": "Top Rebar Diameter",
        "top_spacing": "Top Rebar Spacing",

        "longitudinal_diameter": "Longitudinal Rebar Diameter",
        "longitudinal_count": "Longitudinal Rebar Count",
        "transverse_diameter": "Transverse Rebar Diameter",
        "transverse_spacing": "Transverse Rebar Spacing",

        "top_longitudinal_diameter": "Top Longitudinal Diameter",
        "top_longitudinal_count": "Top Longitudinal Count",
        "top_transverse_diameter": "Top Transverse Diameter",
        "top_transverse_spacing": "Top Transverse Spacing",

        "bottom_x_diameter": "Bottom X Diameter",
        "bottom_x_spacing": "Bottom X Spacing",
        "bottom_y_diameter": "Bottom Y Diameter",
        "bottom_y_spacing": "Bottom Y Spacing",
        "top_x_diameter": "Top X Diameter",
        "top_x_spacing": "Top X Spacing",
        "top_y_diameter": "Top Y Diameter",
        "top_y_spacing": "Top Y Spacing",

        "main_diameter": "Main Rebar Diameter",
        "main_count": "Main Rebar Count",
        "main_top_count": "Top Rebar Count",
        "main_bottom_count": "Bottom Rebar Count",
        "stirrup_diameter": "Stirrup Diameter",
        "stirrup_spacing": "Stirrup Spacing",

        "vertical_diameter": "Vertical Rebar Diameter",
        "vertical_spacing": "Vertical Rebar Spacing",
        "horizontal_diameter": "Horizontal Rebar Diameter",
        "horizontal_spacing": "Horizontal Rebar Spacing",

        "area": "Roof Area",
        "rebar_kg_m2": "Rebar kg/m²",
        "steps": "Number of Steps",
        "riser": "Riser Height",
        "tread": "Tread Width",

        "ask_count": "Enter count:",
        "ask_length": "Enter length (m):",
        "ask_width": "Enter width (m):",
        "ask_height": "Enter height (m):",
        "ask_thickness": "Enter thickness (m):",
        "ask_diameter": "Enter rebar diameter (mm):",
        "ask_spacing": "Enter spacing (mm):",
        "ask_cover": "Enter concrete cover (mm):",
        "ask_lap": "Enter lap percentage:",
        "ask_zero": "Enter 0 to remove this part.",

        "result_title": "🏗️ Calculation Result",
        "concrete": "Concrete",
        "lean_concrete": "Lean Concrete",
        "pedestal": "Pedestal Concrete",
        "total_concrete": "Total Concrete",
        "total_rebar": "Total Rebar",

        "piece": "Piece",
        "piece_count": "Count",
        "piece_length": "Piece Length",
        "weight": "Weight",
        "bars12": "12 m Bars",
        "waste": "Waste",
        "diameter_label": "Diameter",
        "bar": "Rebar",
        "branch": "Bar",
        "branch_length": "Bar Length",
        "pieces": "Pieces",
        "description": "Description",

        "no_data": "No data available.",
    },

    "zh": {
        "home_title": "🏗️ 混凝土结构",
        "foundation": "🧱 基础",
        "columns": "🏛️ 柱",
        "beams": "📐 梁",
        "roofs": "🏠 楼板",
        "stairs": "🪜 楼梯",
        "ties": "🔗 系梁",
        "walls": "🧱 墙",
        "summary": "📊 项目汇总",
        "settings": "⚙️ 设置",
        "help": "ℹ️ 帮助",
        "home": "🏠 首页",
        "menu": "☰ 菜单",
        "back": "🔙 返回",
        "cancel": "❌ 取消",
        "language": "🌐 语言",
        "language_changed": "语言修改成功。",
        "choose_language": "请选择语言：",
        "start": "你好 👋\n欢迎使用混凝土结构工程量估算机器人。",
        "cancelled": "操作已取消。",
        "invalid_number": "❌ 输入值无效，请输入数字。",
        "positive_number": "❌ 数值必须大于零。",
        "zero_allowed": "输入 0 可取消此部分。",
        "done": "✅ 计算完成。",
        "no_summary": "项目中还没有计算记录。",
        "project_summary": "📊 项目汇总",
        "rebar": "🔩 钢筋明细",
        "cutlist": "✂️ 下料清单",
        "new_calc": "🔄 新计算",
        "save_result": "结果已保存到项目汇总。",
        "help_text": (
            "ℹ️ 帮助\n\n"
            "本机器人用于混凝土结构工程量估算。\n\n"
            "根据输入数据计算混凝土、钢筋、构件长度和下料清单。\n\n"
            "⚠️ 本工具用于工程量估算，不能替代结构设计、施工图纸 "
            "和工程师审核。"
        ),

        "isolated": "独立基础",
        "strip": "条形基础",
        "raft": "筏板基础",

        "rect_column": "矩形柱",
        "round_column": "圆柱",

        "main_beam": "主梁",
        "secondary_beam": "次梁",

        "tie_beam": "系梁",
        "tie_collar": "拉梁",

        "shear_wall": "剪力墙",
        "retaining_wall": "挡土墙",

        "stair_slab": "楼梯",

        "roof_joist_foam": "泡沫块楼板",
        "roof_joist_clay": "陶土块楼板",
        "roof_double_joist": "双梁",
        "roof_keromet": "Kromit楼板",
        "roof_composite": "组合楼板",
        "roof_deck": "钢承板楼板",
        "roof_slab": "混凝土板",
        "roof_waffle": "密肋/华夫板",

        "count": "数量",
        "length": "长度",
        "width": "宽度",
        "height": "高度",
        "thickness": "厚度",
        "diameter": "直径",
        "spacing": "间距",
        "cover": "保护层",
        "lap": "搭接",
        "lean_length": "素混凝土长度",
        "lean_width": "素混凝土宽度",
        "lean_thickness": "素混凝土厚度",
        "pedestal_length": "柱墩长度",
        "pedestal_width": "柱墩宽度",
        "pedestal_height": "柱墩高度",

        "bottom_diameter": "底部钢筋直径",
        "bottom_spacing": "底部钢筋间距",
        "top_diameter": "顶部钢筋直径",
        "top_spacing": "顶部钢筋间距",

        "longitudinal_diameter": "纵向钢筋直径",
        "longitudinal_count": "纵向钢筋数量",
        "transverse_diameter": "横向钢筋直径",
        "transverse_spacing": "横向钢筋间距",

        "top_longitudinal_diameter": "顶部纵向钢筋直径",
        "top_longitudinal_count": "顶部纵向钢筋数量",
        "top_transverse_diameter": "顶部横向钢筋直径",
        "top_transverse_spacing": "顶部横向钢筋间距",

        "bottom_x_diameter": "底部 X 钢筋直径",
        "bottom_x_spacing": "底部 X 钢筋间距",
        "bottom_y_diameter": "底部 Y 钢筋直径",
        "bottom_y_spacing": "底部 Y 钢筋间距",
        "top_x_diameter": "顶部 X 钢筋直径",
        "top_x_spacing": "顶部 X 钢筋间距",
        "top_y_diameter": "顶部 Y 钢筋直径",
        "top_y_spacing": "顶部 Y 钢筋间距",

        "main_diameter": "主筋直径",
        "main_count": "主筋数量",
        "main_top_count": "顶部钢筋数量",
        "main_bottom_count": "底部钢筋数量",
        "stirrup_diameter": "箍筋直径",
        "stirrup_spacing": "箍筋间距",

        "vertical_diameter": "竖向钢筋直径",
        "vertical_spacing": "竖向钢筋间距",
        "horizontal_diameter": "水平钢筋直径",
        "horizontal_spacing": "水平钢筋间距",

        "area": "楼板面积",
        "rebar_kg_m2": "每平方米钢筋",
        "steps": "台阶数量",
        "riser": "踏步高度",
        "tread": "踏步宽度",

        "ask_count": "请输入数量：",
        "ask_length": "请输入长度（米）：",
        "ask_width": "请输入宽度（米）：",
        "ask_height": "请输入高度（米）：",
        "ask_thickness": "请输入厚度（米）：",
        "ask_diameter": "请输入钢筋直径（毫米）：",
        "ask_spacing": "请输入间距（毫米）：",
        "ask_cover": "请输入保护层厚度（毫米）：",
        "ask_lap": "请输入搭接百分比：",
        "ask_zero": "输入 0 可取消此部分。",

        "result_title": "🏗️ 计算结果",
        "concrete": "混凝土",
        "lean_concrete": "素混凝土",
        "pedestal": "柱墩混凝土",
        "total_concrete": "混凝土总量",
        "total_rebar": "钢筋总量",

        "piece": "构件",
        "piece_count": "数量",
        "piece_length": "单件长度",
        "weight": "重量",
        "bars12": "12米钢筋",
        "waste": "损耗",
        "diameter_label": "直径",
        "bar": "钢筋",
        "branch": "钢筋",
        "branch_length": "钢筋长度",
        "pieces": "切割件",
        "description": "说明",

        "no_data": "没有可显示的数据。",
    },
}


def get_lang(context):
    return context.user_data.get("lang", "fa")


def tr(context, key):
    lang = get_lang(context)
    return T.get(lang, T["fa"]).get(key, T["fa"].get(key, key))


# =========================================================
# NUMBER PARSER
# =========================================================

def normalize_number(value):
    if value is None:
        return None

    s = str(value).strip()

    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"

    for i, ch in enumerate(persian):
        s = s.replace(ch, str(i))

    for i, ch in enumerate(arabic):
        s = s.replace(ch, str(i))

    s = s.replace("٫", ".")
    s = s.replace(",", ".")
    s = s.replace("٬", "")

    # common unit suffixes
    lower = s.lower()

    if lower.endswith("cm"):
        s = s[:-2].strip()
        try:
            return float(s) / 100.0
        except ValueError:
            return None

    if lower.endswith("mm"):
        s = s[:-2].strip()
        try:
            return float(s) / 1000.0
        except ValueError:
            return None

    try:
        return float(s)
    except ValueError:
        return None


def parse_value(text, integer=False):
    value = normalize_number(text)

    if value is None:
        return None

    if integer:
        if abs(value - round(value)) > 1e-9:
            return None
        return int(round(value))

    return value


# =========================================================
# UI
# =========================================================

def bottom_menu(context):
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(tr(context, "menu")),
                KeyboardButton(tr(context, "home")),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
    )


async def send_message(update, context, text, reply_markup=None):
    if update.callback_query:
        return await update.callback_query.message.reply_text(
            text,
            reply_markup=reply_markup,
        )

    return await update.message.reply_text(
        text,
        reply_markup=reply_markup,
    )


async def edit_message(update, text, reply_markup=None):
    query = update.callback_query

    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )
    except Exception:
        await query.message.reply_text(
            text,
            reply_markup=reply_markup,
        )


def button(text, callback):
    return InlineKeyboardButton(text, callback_data=callback)


# =========================================================
# HOME
# =========================================================

def home_keyboard(context):
    return InlineKeyboardMarkup(
        [
            [
                button(tr(context, "foundation"), "menu_foundation"),
                button(tr(context, "columns"), "menu_columns"),
            ],
            [
                button(tr(context, "beams"), "menu_beams"),
                button(tr(context, "roofs"), "menu_roofs"),
            ],
            [
                button(tr(context, "stairs"), "menu_stairs"),
                button(tr(context, "ties"), "menu_ties"),
            ],
            [
                button(tr(context, "walls"), "menu_walls"),
            ],
            [
                button(tr(context, "summary"), "summary"),
            ],
            [
                button(tr(context, "settings"), "settings"),
                button(tr(context, "help"), "help"),
            ],
        ]
    )


async def show_home(update, context):
    context.user_data.pop("wizard", None)

    text = tr(context, "home_title")

    if update.callback_query:
        await edit_message(
            update,
            text,
            home_keyboard(context),
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=home_keyboard(context),
        )

        await update.message.reply_text(
            tr(context, "menu"),
            reply_markup=bottom_menu(context),
        )


# =========================================================
# MENUS
# =========================================================

async def show_foundation_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "isolated"), "foundation_isolated")],
            [button(tr(context, "strip"), "foundation_strip")],
            [button(tr(context, "raft"), "foundation_raft")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "foundation"), keyboard)


async def show_columns_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "rect_column"), "column_rect")],
            [button(tr(context, "round_column"), "column_round")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "columns"), keyboard)


async def show_beams_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "main_beam"), "beam_main")],
            [button(tr(context, "secondary_beam"), "beam_secondary")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "beams"), keyboard)


async def show_roofs_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                button(
                    tr(context, "roof_joist_foam"),
                    "roof_joist_foam",
                )
            ],
            [
                button(
                    tr(context, "roof_joist_clay"),
                    "roof_joist_clay",
                )
            ],
            [
                button(
                    tr(context, "roof_double_joist"),
                    "roof_double_joist",
                )
            ],
            [
                button(
                    tr(context, "roof_keromet"),
                    "roof_keromet",
                )
            ],
            [
                button(
                    tr(context, "roof_composite"),
                    "roof_composite",
                )
            ],
            [
                button(
                    tr(context, "roof_deck"),
                    "roof_deck",
                )
            ],
            [
                button(
                    tr(context, "roof_slab"),
                    "roof_slab",
                )
            ],
            [
                button(
                    tr(context, "roof_waffle"),
                    "roof_waffle",
                )
            ],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "roofs"), keyboard)


async def show_stairs_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "stair_slab"), "stair_calc")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "stairs"), keyboard)


async def show_ties_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "tie_beam"), "tie_beam_calc")],
            [button(tr(context, "tie_collar"), "tie_collar_calc")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "ties"), keyboard)


async def show_walls_menu(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [button(tr(context, "shear_wall"), "wall_shear")],
            [button(tr(context, "retaining_wall"), "wall_retaining")],
            [button(tr(context, "back"), "home")],
        ]
    )

    await edit_message(update, tr(context, "walls"), keyboard)


# =========================================================
# WIZARD DEFINITIONS
# =========================================================

WIZARDS = {

    "isolated": {
        "title": "isolated",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("width_m", "float"),
            ("thickness_m", "float"),
            ("lean_concrete_length_m", "float"),
            ("lean_concrete_width_m", "float"),
            ("lean_concrete_thickness_m", "float"),
            ("bottom_diameter_mm", "float"),
            ("bottom_spacing_mm", "float"),
            ("top_diameter_mm", "float"),
            ("top_spacing_mm", "float"),
            ("cover_mm", "float"),
            ("lap_percent", "float"),
            ("pedestal_length_m", "float"),
            ("pedestal_width_m", "float"),
            ("pedestal_height_m", "float"),
        ],
    },

    "strip": {
        "title": "strip",
        "fields": [
            ("strip_count", "int"),
            ("strip_length_m", "float"),
            ("footing_width_m", "float"),
            ("footing_thickness_m", "float"),
            ("lean_length_m", "float"),
            ("lean_width_m", "float"),
            ("lean_thickness_m", "float"),
            ("longitudinal_diameter_mm", "float"),
            ("longitudinal_count", "int"),
            ("transverse_diameter_mm", "float"),
            ("transverse_spacing_mm", "float"),
            ("top_longitudinal_diameter_mm", "float"),
            ("top_longitudinal_count", "int"),
            ("top_transverse_diameter_mm", "float"),
            ("top_transverse_spacing_mm", "float"),
            ("cover_mm", "float"),
            ("lap_percent", "float"),
        ],
    },

    "raft": {
        "title": "raft",
        "fields": [
            ("length_m", "float"),
            ("width_m", "float"),
            ("thickness_m", "float"),
            ("lean_length_m", "float"),
            ("lean_width_m", "float"),
            ("lean_thickness_m", "float"),
            ("bottom_x_diameter_mm", "float"),
            ("bottom_x_spacing_mm", "float"),
            ("bottom_y_diameter_mm", "float"),
            ("bottom_y_spacing_mm", "float"),
            ("top_x_diameter_mm", "float"),
            ("top_x_spacing_mm", "float"),
            ("top_y_diameter_mm", "float"),
            ("top_y_spacing_mm", "float"),
            ("cover_mm", "float"),
            ("lap_percent", "float"),
        ],
    },

    "column_rect": {
        "title": "rect_column",
        "fields": [
            ("count", "int"),
            ("width_m", "float"),
            ("depth_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "column_round": {
        "title": "round_column",
        "fields": [
            ("count", "int"),
            ("diameter_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "beam_main": {
        "title": "main_beam",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("width_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_top_count", "int"),
            ("main_bottom_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "beam_secondary": {
        "title": "secondary_beam",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("width_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_top_count", "int"),
            ("main_bottom_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "tie_beam_calc": {
        "title": "tie_beam",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("width_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "tie_collar_calc": {
        "title": "tie_collar",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("width_m", "float"),
            ("height_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_count", "int"),
            ("stirrup_diameter_mm", "float"),
            ("stirrup_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "wall_shear": {
        "title": "shear_wall",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("height_m", "float"),
            ("thickness_m", "float"),
            ("vertical_diameter_mm", "float"),
            ("vertical_spacing_mm", "float"),
            ("horizontal_diameter_mm", "float"),
            ("horizontal_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "wall_retaining": {
        "title": "retaining_wall",
        "fields": [
            ("count", "int"),
            ("length_m", "float"),
            ("height_m", "float"),
            ("thickness_m", "float"),
            ("vertical_diameter_mm", "float"),
            ("vertical_spacing_mm", "float"),
            ("horizontal_diameter_mm", "float"),
            ("horizontal_spacing_mm", "float"),
            ("cover_mm", "float"),
        ],
    },

    "stair_calc": {
        "title": "stair_slab",
        "fields": [
            ("length_m", "float"),
            ("width_m", "float"),
            ("thickness_m", "float"),
            ("main_diameter_mm", "float"),
            ("main_spacing_mm", "float"),
            ("distribution_diameter_mm", "float"),
            ("distribution_spacing_mm", "float"),
            ("steps", "int"),
            ("step_riser", "float"),
            ("step_tread", "float"),
        ],
    },

    "roof": {
        "title": "roof_slab",
        "fields": [
            ("area_m2", "float"),
            ("rebar_kg_m2", "float"),
        ],
    },
}


def field_label(context, field):
    key = field[0]

    special = {
        "length_m": "length",
        "width_m": "width",
        "height_m": "height",
        "thickness_m": "thickness",

        "lean_concrete_length_m": "lean_length",
        "lean_concrete_width_m": "lean_width",
        "lean_concrete_thickness_m": "lean_thickness",

        "lean_length_m": "lean_length",
        "lean_width_m": "lean_width",
        "lean_thickness_m": "lean_thickness",

        "pedestal_length_m": "pedestal_length",
        "pedestal_width_m": "pedestal_width",
        "pedestal_height_m": "pedestal_height",

        "bottom_diameter_mm": "bottom_diameter",
        "bottom_spacing_mm": "bottom_spacing",
        "top_diameter_mm": "top_diameter",
        "top_spacing_mm": "top_spacing",

        "longitudinal_diameter_mm": "longitudinal_diameter",
        "longitudinal_count": "longitudinal_count",
        "transverse_diameter_mm": "transverse_diameter",
        "transverse_spacing_mm": "transverse_spacing",

        "top_longitudinal_diameter_mm": "top_longitudinal_diameter",
        "top_longitudinal_count": "top_longitudinal_count",
        "top_transverse_diameter_mm": "top_transverse_diameter",
        "top_transverse_spacing_mm": "top_transverse_spacing",

        "bottom_x_diameter_mm": "bottom_x_diameter",
        "bottom_x_spacing_mm": "bottom_x_spacing",
        "bottom_y_diameter_mm": "bottom_y_diameter",
        "bottom_y_spacing_mm": "bottom_y_spacing",
        "top_x_diameter_mm": "top_x_diameter",
        "top_x_spacing_mm": "top_x_spacing",
        "top_y_diameter_mm": "top_y_diameter",
        "top_y_spacing_mm": "top_y_spacing",

        "main_diameter_mm": "main_diameter",
        "main_count": "main_count",
        "main_top_count": "main_top_count",
        "main_bottom_count": "main_bottom_count",

        "stirrup_diameter_mm": "stirrup_diameter",
        "stirrup_spacing_mm": "stirrup_spacing",

        "vertical_diameter_mm": "vertical_diameter",
        "vertical_spacing_mm": "vertical_spacing",
        "horizontal_diameter_mm": "horizontal_diameter",
        "horizontal_spacing_mm": "horizontal_spacing",

        "area_m2": "area",
        "rebar_kg_m2": "rebar_kg_m2",

        "step_riser": "riser",
        "step_tread": "tread",
    }

    return tr(context, special.get(key, key))


def build_prompt(context, field):
    key, typ = field

    label = field_label(context, field)

    if key == "count" or key == "strip_count":
        return f"🔢 {label}\n\n{tr(context, 'ask_count')}"

    if key.endswith("_diameter_mm"):
        return (
            f"🔩 {label}\n\n"
            f"{tr(context, 'ask_diameter')}\n"
            f"{tr(context, 'ask_zero')}"
        )

    if key.endswith("_spacing_mm"):
        return (
            f"📏 {label}\n\n"
            f"{tr(context, 'ask_spacing')}\n"
            f"{tr(context, 'ask_zero')}"
        )

    if key == "cover_mm":
        return f"📏 {label}\n\n{tr(context, 'ask_cover')}"

    if key == "lap_percent":
        return f"🔗 {label}\n\n{tr(context, 'ask_lap')}"

    if key.endswith("_m"):
        if "length" in key:
            return f"📐 {label}\n\n{tr(context, 'ask_length')}"
        if "width" in key:
            return f"📐 {label}\n\n{tr(context, 'ask_width')}"
        if "height" in key:
            return f"📐 {label}\n\n{tr(context, 'ask_height')}"
        if "thickness" in key:
            return f"📐 {label}\n\n{tr(context, 'ask_thickness')}"

    if key == "area_m2":
        return f"📐 {label}\n\n{tr(context, 'ask_length')}"

    if key in ("steps",):
        return f"🔢 {label}\n\n{tr(context, 'ask_count')}"

    return f"📌 {label}\n\n"


# =========================================================
# WIZARD START
# =========================================================

async def start_wizard(update, context, wizard_name):
    context.user_data["wizard"] = {
        "name": wizard_name,
        "index": 0,
        "data": {},
    }

    wizard = WIZARDS[wizard_name]
    first_field = wizard["fields"][0]

    text = (
        f"🏗️ {tr(context, wizard['title'])}\n\n"
        f"{build_prompt(context, first_field)}"
    )

    keyboard = InlineKeyboardMarkup(
        [[button(tr(context, "cancel"), "cancel_wizard")]]
    )

    if update.callback_query:
        await edit_message(update, text, keyboard)
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
        )


# =========================================================
# WIZARD PROCESS
# =========================================================

async def handle_wizard_text(update, context):
    wizard_state = context.user_data.get("wizard")

    if not wizard_state:
        return False

    wizard_name = wizard_state["name"]
    wizard = WIZARDS[wizard_name]

    index = wizard_state["index"]

    if index >= len(wizard["fields"]):
        return False

    field = wizard["fields"][index]
    key, typ = field

    value = parse_value(
        update.message.text,
        integer=(typ == "int"),
    )

    if value is None:
        await update.message.reply_text(
            tr(context, "invalid_number")
        )
        return True

    # allow zero for optional rebar sections
    if value == 0:
        optional_keys = {
            "top_diameter_mm",
            "top_spacing_mm",
            "top_longitudinal_diameter_mm",
            "top_longitudinal_count",
            "top_transverse_diameter_mm",
            "top_transverse_spacing_mm",
            "top_x_diameter_mm",
            "top_x_spacing_mm",
            "top_y_diameter_mm",
            "top_y_spacing_mm",
        }

        if key not in optional_keys and key not in {
            "pedestal_length_m",
            "pedestal_width_m",
            "pedestal_height_m",
        }:
            await update.message.reply_text(
                tr(context, "positive_number")
            )
            return True

    wizard_state["data"][key] = value
    wizard_state["index"] += 1

    if wizard_state["index"] >= len(wizard["fields"]):
        await finish_wizard(update, context)
        return True

    next_field = wizard["fields"][wizard_state["index"]]

    await update.message.reply_text(
        build_prompt(context, next_field),
        reply_markup=InlineKeyboardMarkup(
            [[button(tr(context, "cancel"), "cancel_wizard")]]
        ),
    )

    return True


# =========================================================
# CALCULATIONS
# =========================================================

def execute_calculation(name, data):
    if name == "isolated":
        return isolated_footing(
            count=data["count"],
            length_m=data["length_m"],
            width_m=data["width_m"],
            thickness_m=data["thickness_m"],
            lean_concrete_length_m=data["lean_concrete_length_m"],
            lean_concrete_width_m=data["lean_concrete_width_m"],
            lean_concrete_thickness_m=data["lean_concrete_thickness_m"],
            bottom_diameter_mm=data["bottom_diameter_mm"],
            bottom_spacing_mm=data["bottom_spacing_mm"],
            top_diameter_mm=data["top_diameter_mm"] or None,
            top_spacing_mm=data["top_spacing_mm"] or None,
            cover_mm=data["cover_mm"],
            lap_percent=data["lap_percent"],
            pedestal_length_m=data["pedestal_length_m"],
            pedestal_width_m=data["pedestal_width_m"],
            pedestal_height_m=data["pedestal_height_m"],
        )

    if name == "strip":
        return strip_footing(
            strip_count=data["strip_count"],
            strip_length_m=data["strip_length_m"],
            footing_width_m=data["footing_width_m"],
            footing_thickness_m=data["footing_thickness_m"],
            lean_length_m=data["lean_length_m"],
            lean_width_m=data["lean_width_m"],
            lean_thickness_m=data["lean_thickness_m"],
            longitudinal_diameter_mm=data["longitudinal_diameter_mm"],
            longitudinal_count=data["longitudinal_count"],
            transverse_diameter_mm=data["transverse_diameter_mm"],
            transverse_spacing_mm=data["transverse_spacing_mm"],
            top_longitudinal_diameter_mm=(
                data["top_longitudinal_diameter_mm"] or None
            ),
            top_longitudinal_count=(
                data["top_longitudinal_count"] or None
            ),
            top_transverse_diameter_mm=(
                data["top_transverse_diameter_mm"] or None
            ),
            top_transverse_spacing_mm=(
                data["top_transverse_spacing_mm"] or None
            ),
            cover_mm=data["cover_mm"],
            lap_percent=data["lap_percent"],
        )

    if name == "raft":
        return raft_foundation(
            length_m=data["length_m"],
            width_m=data["width_m"],
            thickness_m=data["thickness_m"],
            lean_length_m=data["lean_length_m"],
            lean_width_m=data["lean_width_m"],
            lean_thickness_m=data["lean_thickness_m"],
            bottom_x_diameter_mm=data["bottom_x_diameter_mm"],
            bottom_x_spacing_mm=data["bottom_x_spacing_mm"],
            bottom_y_diameter_mm=data["bottom_y_diameter_mm"],
            bottom_y_spacing_mm=data["bottom_y_spacing_mm"],
            top_x_diameter_mm=data["top_x_diameter_mm"] or None,
            top_x_spacing_mm=data["top_x_spacing_mm"] or None,
            top_y_diameter_mm=data["top_y_diameter_mm"] or None,
            top_y_spacing_mm=data["top_y_spacing_mm"] or None,
            cover_mm=data["cover_mm"],
            lap_percent=data["lap_percent"],
        )

    if name == "column_rect":
        return column_rectangular(
            count=data["count"],
            width_m=data["width_m"],
            depth_m=data["depth_m"],
            height_m=data["height_m"],
            main_diameter_mm=data["main_diameter_mm"],
            main_count=data["main_count"],
            stirrup_diameter_mm=data["stirrup_diameter_mm"],
            stirrup_spacing_mm=data["stirrup_spacing_mm"],
            cover_mm=data["cover_mm"],
        )

    if name == "column_round":
        return column_round(
            count=data["count"],
            diameter_m=data["diameter_m"],
            height_m=data["height_m"],
            main_diameter_mm=data["main_diameter_mm"],
            main_count=data["main_count"],
            stirrup_diameter_mm=data["stirrup_diameter_mm"],
            stirrup_spacing_mm=data["stirrup_spacing_mm"],
            cover_mm=data["cover_mm"],
        )

    if name in ("beam_main", "beam_secondary"):
        return beam(
            count=data["count"],
            length_m=data["length_m"],
            width_m=data["width_m"],
            height_m=data["height_m"],
            main_diameter_mm=data["main_diameter_mm"],
            main_top_count=data["main_top_count"],
            main_bottom_count=data["main_bottom_count"],
            stirrup_diameter_mm=data["stirrup_diameter_mm"],
            stirrup_spacing_mm=data["stirrup_spacing_mm"],
            cover_mm=data["cover_mm"],
        )

    if name in ("tie_beam_calc", "tie_collar_calc"):
        return tie_beam(
            count=data["count"],
            length_m=data["length_m"],
            width_m=data["width_m"],
            height_m=data["height_m"],
            main_diameter_mm=data["main_diameter_mm"],
            main_count=data["main_count"],
            stirrup_diameter_mm=data["stirrup_diameter_mm"],
            stirrup_spacing_mm=data["stirrup_spacing_mm"],
            cover_mm=data["cover_mm"],
        )

    if name in ("wall_shear", "wall_retaining"):
        one = wall_concrete(
            length_m=data["length_m"],
            height_m=data["height_m"],
            thickness_m=data["thickness_m"],
            vertical_diameter_mm=data["vertical_diameter_mm"],
            vertical_spacing_mm=data["vertical_spacing_mm"],
            horizontal_diameter_mm=data["horizontal_diameter_mm"],
            horizontal_spacing_mm=data["horizontal_spacing_mm"],
            cover_mm=data["cover_mm"],
        )

        count = data["count"]

        if count != 1:
            one["concrete_m3"] *= count
            one["total_rebar_kg"] *= count

            if "rebar_details" in one:
                for item in one["rebar_details"]:
                    item["weight_kg"] *= count
                    item["piece_count"] *= count

        return one

    if name == "stair_calc":
        return stair_slab(
            length_m=data["length_m"],
            width_m=data["width_m"],
            thickness_m=data["thickness_m"],
            main_diameter_mm=data["main_diameter_mm"],
            main_spacing_mm=data["main_spacing_mm"],
            distribution_diameter_mm=data["distribution_diameter_mm"],
            distribution_spacing_mm=data["distribution_spacing_mm"],
            steps=data["steps"],
            step_riser=data["step_riser"],
            step_tread=data["step_tread"],
        )

    if name == "roof":
        return roof_slab(
            area_m2=data["area_m2"],
            concrete_coefficient=data.get("concrete_coefficient", 0.20),
            rebar_kg_m2=data["rebar_kg_m2"],
        )

    raise ValueError(f"Unknown wizard: {name}")


# =========================================================
# FORMAT RESULT
# =========================================================

def fmt(value, digits=2):
    if value is None:
        return "0"

    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def safe_num(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def make_block(lines):
    content = "\n".join(lines)
    return f"<pre>{html.escape(content)}</pre>"


def format_rebar(context, result):
    details = result.get("rebar_details") or []

    if not details:
        return make_block([
            tr(context, "rebar"),
            "────────────────────",
            tr(context, "no_data"),
        ])

    lines = [
        "🔩 " + tr(context, "rebar"),
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, item in enumerate(details, 1):
        diameter = item.get("diameter_mm", 0)
        count = item.get("piece_count", 0)
        length = item.get("length_m", 0)
        weight = item.get("weight_kg", 0)
        bars = item.get("bars_12m", 0)
        waste = item.get("waste_m", 0)

        piece_lengths = item.get("piece_lengths_m") or []

        unique_lengths = Counter(
            round(float(x), 3)
            for x in piece_lengths
        )

        if len(unique_lengths) == 1:
            length_text = fmt(next(iter(unique_lengths.keys())), 3) + " m"
        else:
            length_text = ", ".join(
                f"{x:.3f} m × {n}"
                for x, n in unique_lengths.items()
            )

        lines.extend(
            [
                "",
                f"{tr(context, 'bar')} {i}",
                f"{tr(context, 'diameter_label')}:      Φ{fmt(diameter, 0)}",
                f"{tr(context, 'piece_count')}:        {int(count)}",
                f"{tr(context, 'piece_length')}:   {length_text}",
                f"{tr(context, 'weight')}:           {fmt(weight, 1)} kg",
                f"{tr(context, 'bars12')}:      {int(bars)}",
                f"{tr(context, 'waste')}:           {fmt(waste, 2)} m",
                "━━━━━━━━━━━━━━━━━━━━",
            ]
        )

    lines.extend(
        [
            f"{tr(context, 'total_rebar')}: "
            f"{fmt(result.get('total_rebar_kg', 0), 1)} kg"
        ]
    )

    return make_block(lines)


def format_cutlist(context, result):
    details = result.get("rebar_details") or []

    if not details:
        return make_block([
            "✂️ " + tr(context, "cutlist"),
            "━━━━━━━━━━━━━━━━━━━━",
            tr(context, "no_data"),
        ])

    lines = [
        "✂️ " + tr(context, "cutlist"),
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    branch_no = 1

    for item in details:
        cut_plan = item.get("cut_plan") or []

        if not cut_plan:
            continue

        diameter = item.get("diameter_mm", 0)

        for plan in cut_plan:
            if isinstance(plan, dict):
                cuts = (
                    plan.get("cuts")
                    or plan.get("pieces")
                    or plan.get("lengths")
                    or []
                )

                waste = plan.get("waste_m", 0)

                lines.extend(
                    [
                        "",
                        f"{tr(context, 'branch')} {branch_no}",
                        f"{tr(context, 'diameter_label')}: Φ{fmt(diameter, 0)}",
                        f"{tr(context, 'branch_length')}: 12.00 m",
                        f"{tr(context, 'pieces')}: "
                        + (
                            " + ".join(
                                f"{safe_num(x):.3f}"
                                for x in cuts
                            )
                            if cuts
                            else "-"
                        ),
                        f"{tr(context, 'waste')}: {safe_num(waste):.3f} m",
                        "━━━━━━━━━━━━━━━━━━━━",
                    ]
                )

                branch_no += 1

    if branch_no == 1:
        return make_block([
            "✂️ " + tr(context, "cutlist"),
            "━━━━━━━━━━━━━━━━━━━━",
            tr(context, "no_data"),
        ])

    return make_block(lines)


def format_result(context, name, result):
    lines = [
        "🏗️ " + tr(context, WIZARDS[name]["title"]),
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    # Generic concrete values
    if "concrete_m3" in result:
        lines.append(
            f"{tr(context, 'concrete')}: "
            f"{fmt(result.get('concrete_m3', 0))} m³"
        )

    if "footing_concrete_m3" in result:
        lines.append(
            f"{tr(context, 'concrete')}: "
            f"{fmt(result.get('footing_concrete_m3', 0))} m³"
        )

    if "lean_concrete_m3" in result:
        lines.append(
            f"{tr(context, 'lean_concrete')}: "
            f"{fmt(result.get('lean_concrete_m3', 0))} m³"
        )

    if "pedestal_concrete_m3" in result:
        lines.append(
            f"{tr(context, 'pedestal')}: "
            f"{fmt(result.get('pedestal_concrete_m3', 0))} m³"
        )

    if "total_concrete_m3" in result:
        lines.append(
            f"{tr(context, 'total_concrete')}: "
            f"{fmt(result.get('total_concrete_m3', 0))} m³"
        )

    if "total_rebar_kg" in result:
        lines.append(
            f"{tr(context, 'total_rebar')}: "
            f"{fmt(result.get('total_rebar_kg', 0), 1)} kg"
        )

    lines.append("━━━━━━━━━━━━━━━━━━━━")

    return make_block(lines)


# =========================================================
# SEND LONG MESSAGE IN PARTS
# =========================================================

async def send_long(update, text):
    MAX = 3800

    if len(text) <= MAX:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=bottom_menu_from_update(update),
        )
        return

    chunks = []

    while len(text) > MAX:
        cut = text.rfind("\n", 0, MAX)

        if cut < 500:
            cut = MAX

        chunks.append(text[:cut])
        text = text[cut:]

    chunks.append(text)

    for chunk in chunks:
        await update.message.reply_text(
            chunk,
            parse_mode="HTML",
        )


def bottom_menu_from_update(update):
    # context is unavailable here, so fallback is intentionally not used
    return None


# =========================================================
# FINISH WIZARD
# =========================================================

async def finish_wizard(update, context):
    wizard_state = context.user_data.get("wizard")

    if not wizard_state:
        return

    name = wizard_state["name"]
    data = wizard_state["data"]

    try:
        result = execute_calculation(name, data)

    except Exception as exc:
        traceback.print_exc()

        context.user_data.pop("wizard", None)

        await update.message.reply_text(
            f"❌ {html.escape(str(exc))}",
            reply_markup=bottom_menu(context),
        )
        return

    # Store project result
    project_results = context.user_data.setdefault(
        "project_results",
        [],
    )

    project_results.append(
        {
            "name": name,
            "result": result,
        }
    )

    context.user_data["last_result"] = result
    context.user_data["last_result_name"] = name

    context.user_data.pop("wizard", None)

    await update.message.reply_text(
        format_result(context, name, result),
        parse_mode="HTML",
        reply_markup=bottom_menu(context),
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                button(tr(context, "rebar"), "result_rebar"),
                button(tr(context, "cutlist"), "result_cut"),
            ],
            [
                button(tr(context, "new_calc"), "home"),
            ],
        ]
    )

    await update.message.reply_text(
        tr(context, "done"),
        reply_markup=keyboard,
    )


# =========================================================
# SUMMARY
# =========================================================

async def show_summary(update, context):
    results = context.user_data.get("project_results") or []

    if not results:
        await edit_message(
            update,
            tr(context, "no_summary"),
            InlineKeyboardMarkup(
                [[button(tr(context, "back"), "home")]]
            ),
        )
        return

    total_concrete = 0.0
    total_rebar = 0.0

    for item in results:
        result = item["result"]

        total_concrete += safe_num(
            result.get("total_concrete_m3", 0)
        )

        if not result.get("total_concrete_m3"):
            total_concrete += safe_num(
                result.get("concrete_m3", 0)
            )
            total_concrete += safe_num(
                result.get("lean_concrete_m3", 0)
            )

        total_rebar += safe_num(
            result.get("total_rebar_kg", 0)
        )

    lines = [
        "📊 " + tr(context, "project_summary"),
        "━━━━━━━━━━━━━━━━━━━━",
        f"{tr(context, 'concrete')}: {total_concrete:.2f} m³",
        f"{tr(context, 'total_rebar')}: {total_rebar:.1f} kg",
        "━━━━━━━━━━━━━━━━━━━━",
        f"تعداد آیتم‌ها: {len(results)}",
    ]

    await edit_message(
        update,
        make_block(lines),
        InlineKeyboardMarkup(
            [[button(tr(context, "back"), "home")]]
        ),
    )


# =========================================================
# SETTINGS
# =========================================================

async def show_settings(update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                button("🇮🇷 فارسی", "lang_fa"),
                button("🇸🇦 العربية", "lang_ar"),
            ],
            [
                button("🇬🇧 English", "lang_en"),
                button("🇨🇳 中文", "lang_zh"),
            ],
            [
                button(tr(context, "back"), "home"),
            ],
        ]
    )

    await edit_message(
        update,
        tr(context, "choose_language"),
        keyboard,
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":
        await show_home(update, context)
        return

    if data == "menu_foundation":
        await show_foundation_menu(update, context)
        return

    if data == "menu_columns":
        await show_columns_menu(update, context)
        return

    if data == "menu_beams":
        await show_beams_menu(update, context)
        return

    if data == "menu_roofs":
        await show_roofs_menu(update, context)
        return

    if data == "menu_stairs":
        await show_stairs_menu(update, context)
        return

    if data == "menu_ties":
        await show_ties_menu(update, context)
        return

    if data == "menu_walls":
        await show_walls_menu(update, context)
        return

    if data == "settings":
        await show_settings(update, context)
        return

    if data == "help":
        await edit_message(
            update,
            tr(context, "help_text"),
            InlineKeyboardMarkup(
                [[button(tr(context, "back"), "home")]]
            ),
        )
        return

    if data == "summary":
        await show_summary(update, context)
        return

    if data == "cancel_wizard":
        context.user_data.pop("wizard", None)

        await edit_message(
            update,
            tr(context, "cancelled"),
            InlineKeyboardMarkup(
                [[button(tr(context, "back"), "home")]]
            ),
        )
        return

    if data.startswith("lang_"):
        lang = data.replace("lang_", "")

        if lang in LANGS:
            context.user_data["lang"] = lang

        await query.answer(
            tr(context, "language_changed")
        )

        await show_home(update, context)
        return

    wizard_map = {
        "foundation_isolated": "isolated",
        "foundation_strip": "strip",
        "foundation_raft": "raft",

        "column_rect": "column_rect",
        "column_round": "column_round",

        "beam_main": "beam_main",
        "beam_secondary": "beam_secondary",

        "tie_beam_calc": "tie_beam_calc",
        "tie_collar_calc": "tie_collar_calc",

        "wall_shear": "wall_shear",
        "wall_retaining": "wall_retaining",

        "stair_calc": "stair_calc",

        "roof_joist_foam": "roof",
        "roof_joist_clay": "roof",
        "roof_double_joist": "roof",
        "roof_keromet": "roof",
        "roof_composite": "roof",
        "roof_deck": "roof",
        "roof_slab": "roof",
        "roof_waffle": "roof",
    }

    if data in wizard_map:
        wizard_name = wizard_map[data]

        # Roof coefficient based on selected type
        if wizard_name == "roof":
            coefficients = {
                "roof_joist_foam": 0.18,
                "roof_joist_clay": 0.20,
                "roof_double_joist": 0.23,
                "roof_keromet": 0.18,
                "roof_composite": 0.15,
                "roof_deck": 0.15,
                "roof_slab": 0.20,
                "roof_waffle": 0.20,
            }

            context.user_data["roof_type"] = data
            context.user_data["roof_coefficient"] = coefficients[data]

        await start_wizard(update, context, wizard_name)
        return

    if data == "result_rebar":
        result = context.user_data.get("last_result")

        if not result:
            await query.message.reply_text(
                tr(context, "no_data")
            )
            return

        await query.message.reply_text(
            format_rebar(context, result),
            parse_mode="HTML",
        )
        return

    if data == "result_cut":
        result = context.user_data.get("last_result")

        if not result:
            await query.message.reply_text(
                tr(context, "no_data")
            )
            return

        await query.message.reply_text(
            format_cutlist(context, result),
            parse_mode="HTML",
        )
        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(update, context):
    text = update.message.text.strip()

    # Home / menu
    if text in {
        tr(context, "home"),
        "🏠 خانه",
        "🏠 Home",
        "🏠 الرئيسية",
        "🏠 首页",
    }:
        await show_home(update, context)
        return

    if text in {
        tr(context, "menu"),
        "☰ منو",
        "☰ Menu",
        "☰ القائمة",
        "☰ 菜单",
    }:
        await update.message.reply_text(
            tr(context, "home_title"),
            reply_markup=home_keyboard(context),
        )
        return

    # Cancel wizard
    if text in {
        tr(context, "cancel"),
        "❌ لغو",
        "❌ إلغاء",
        "❌ Cancel",
        "❌ 取消",
    }:
        context.user_data.pop("wizard", None)

        await update.message.reply_text(
            tr(context, "cancelled"),
            reply_markup=bottom_menu(context),
        )
        return

    handled = await handle_wizard_text(update, context)

    if handled:
        return

    await update.message.reply_text(
        tr(context, "home_title"),
        reply_markup=home_keyboard(context),
    )


# =========================================================
# COMMANDS
# =========================================================

async def start_command(update, context):
    context.user_data.setdefault("lang", "fa")
    context.user_data.pop("wizard", None)

    await update.message.reply_text(
        tr(context, "start"),
        reply_markup=bottom_menu(context),
    )

    await update.message.reply_text(
        tr(context, "home_title"),
        reply_markup=home_keyboard(context),
    )


async def cancel_command(update, context):
    context.user_data.pop("wizard", None)

    await update.message.reply_text(
        tr(context, "cancelled"),
        reply_markup=bottom_menu(context),
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):
    print("BOT ERROR:")
    traceback.print_exception(
        type(context.error),
        context.error,
        context.error.__traceback__,
    )

    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ خطایی در پردازش درخواست رخ داد."
            )
    except Exception:
        pass


# =========================================================
# MAIN
# =========================================================

def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        CommandHandler("cancel", cancel_command)
    )

    application.add_handler(
        CallbackQueryHandler(callback_router)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler,
        )
    )

    application.add_error_handler(error_handler)

    port = int(os.getenv("PORT", "10000"))

    base_url = (
        os.getenv("WEBHOOK_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
    )

    if not base_url:
        raise RuntimeError(
            "WEBHOOK_URL or RENDER_EXTERNAL_URL is required"
        )

    base_url = base_url.rstrip("/")

    webhook_url = f"{base_url}/telegram"

    print("Starting Telegram bot...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Port: {port}")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
