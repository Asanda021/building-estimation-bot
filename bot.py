# -*- coding: utf-8 -*-
"""Concrete Structure Quantity Bot - sellable rebuild v3.0.

Base architecture follows the five-part BOT flow supplied by the user:
project setup -> member wizard -> review -> calculation -> result/Cut List.
The calculation engine is kept separate in calculations.py.
"""
import os
import logging
import math
from html import escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from calculations import (
    isolated_footing, strip_footing, raft_foundation,
    column_rectangular, column_round, beam, tie_beam,
    wall_concrete, stair_slab,
    joist_eps_roof_detail, joist_clay_roof_detail,
    waffle_roof_detail, solid_slab_roof_detail,
    aggregate_project_results, equivalent_rebar_count,
    normalize_standard, rebar_grade_yield_mpa,
    parse_natural_input, natural_stirrup_quantity,
    column_multistory_plan, verified_splice_length,
    iran_column_lap_rule, multistory_column_splice_schedule,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

STANDARDS = {
    "iran": {"fa": "🇮🇷 مبحث ۹ ایران", "en": "🇮🇷 Iran - Chapter 9", "ar": "🇮🇷 مبحث 9 إيران", "zh": "🇮🇷 伊朗第9章"},
    "aci318": {"fa": "🇺🇸 ACI 318", "en": "🇺🇸 ACI 318", "ar": "🇺🇸 ACI 318", "zh": "🇺🇸 ACI 318"},
    "eurocode2": {"fa": "🇪🇺 Eurocode 2", "en": "🇪🇺 Eurocode 2", "ar": "🇪🇺 Eurocode 2", "zh": "🇪🇺 Eurocode 2"},
    "china": {"fa": "🇨🇳 China / GB", "en": "🇨🇳 China / GB", "ar": "🇨🇳 China / GB", "zh": "🇨🇳 中国 / GB"},
}

CONCRETE_OPTIONS = [25, 30, 35, 40, 45, 50]
REBAR_OPTIONS = {
    "iran": [("A2", 300), ("A3", 400), ("A4", 500)],
    "aci318": [("Grade 40", 280), ("Grade 60", 420)],
    "eurocode2": [("B400", 400), ("B500", 500)],
    "china": [],  # China requires explicit verified fy.
}

TEXT = {
    "fa": {
        "language": "🌐 <b>زبان / Language</b>",
        "welcome": "🏗️ <b>Structural Quantity Engine</b>\n\nاستاندارد، مصالح و سپس عضو سازه‌ای را انتخاب کنید.",
        "standard": "📚 <b>استاندارد پروژه</b>\nاستاندارد مبنا را انتخاب کنید:",
        "concrete": "🧱 <b>مقاومت بتن</b>\nمقاومت فشاری مشخصه بتن را انتخاب کنید:",
        "grade": "🔩 <b>گرید میلگرد</b>\nگرید میلگرد پروژه را انتخاب کنید:",
        "china_fy": "🔩 <b>fy میلگرد چین</b>\nبرای China / GB مقدار fy را به MPa وارد کنید. هیچ مقدار پیش‌فرضی اعمال نمی‌شود.",
        "project_ready": "✅ <b>پروژه آماده است</b>",
        "invalid": "❌ مقدار معتبر نیست. دوباره وارد کنید.",
        "calc_error": "❌ خطا در محاسبه:\n<code>{}</code>",
        "back": "🔙 بازگشت", "home": "🏠 صفحه اصلی", "cancel": "❌ لغو",
        "prev": "⬅️ مرحله قبل", "review": "📋 بررسی نهایی", "calculate": "🧮 محاسبه",
        "edit": "✏️ ویرایش", "show_rebar": "🔩 جزئیات میلگرد", "show_cut": "✂️ Cut List",
        "new_member": "➕ عضو جدید", "summary": "📊 خلاصه پروژه", "settings": "⚙️ تنظیمات",
        "help": "ℹ️ راهنما", "equivalency": "🔄 معادل‌سازی میلگرد", "current_count": "تعداد میلگرد فعلی",
        "current_dia": "قطر میلگرد فعلی", "replacement_dia": "قطر میلگرد جایگزین", "enter_value": "مقدار را وارد کنید:",
        "equivalent": "سطح مقطع معادل است.", "not_equivalent": "جایگزین انتخاب‌شده از نظر سطح مقطع کافی نیست.",
        "engineering_warning": "⚠️ این فقط کنترل سطح مقطع است؛ فاصله‌گذاری، حداقل/حداکثر آرماتور، مهاری، وصله و دیتیلینگ باید جداگانه کنترل شود.",
        "language": "🌐 تغییر زبان", "materials": "🧱 مصالح", "standard_setting": "📚 تغییر استاندارد",
        "natural": "✍️ ورود طبیعی / هوشمند", "multi_column": "🏢 ستون چندطبقه", "result": "📌 نتیجه",
    },
    "en": {
        "language": "🌐 <b>Language</b>", "welcome": "🏗️ <b>Structural Quantity Engine</b>\n\nChoose project standard, materials, then a structural member.",
        "standard": "📚 <b>Project Standard</b>\nChoose the governing standard:", "concrete": "🧱 <b>Concrete</b>\nChoose characteristic concrete strength:",
        "grade": "🔩 <b>Rebar Grade</b>\nChoose the project rebar grade:", "china_fy": "🔩 <b>China rebar fy</b>\nEnter verified fy in MPa. No default is assumed.",
        "project_ready": "✅ <b>Project is ready</b>", "invalid": "❌ Invalid value. Try again.", "calc_error": "❌ Calculation error:\n<code>{}</code>",
        "back": "🔙 Back", "home": "🏠 Home", "cancel": "❌ Cancel", "prev": "⬅️ Previous", "review": "📋 Review", "calculate": "🧮 Calculate",
        "edit": "✏️ Edit", "show_rebar": "🔩 Rebar details", "show_cut": "✂️ Cut List", "new_member": "➕ New member", "summary": "📊 Project summary",
        "settings": "⚙️ Settings", "help": "ℹ️ Help", "equivalency": "🔄 Rebar equivalency", "current_count": "Current bar count", "current_dia": "Current diameter",
        "replacement_dia": "Replacement diameter", "enter_value": "Enter value:", "equivalent": "Area is equivalent.", "not_equivalent": "Replacement area is insufficient.",
        "engineering_warning": "⚠️ Area equivalency only; spacing, minimum/maximum reinforcement, development, splice and detailing require separate checks.",
        "language": "🌐 Language", "materials": "🧱 Materials", "standard_setting": "📚 Standard", "natural": "✍️ Natural input", "multi_column": "🏢 Multi-story column", "result": "📌 Result",
    },
    "ar": {
        "language": "🌐 <b>اللغة</b>", "welcome": "🏗️ <b>محرك الكميات الإنشائية</b>\n\nاختر المعيار والمواد ثم العنصر الإنشائي.",
        "standard": "📚 <b>معيار المشروع</b>", "concrete": "🧱 <b>الخرسانة</b>", "grade": "🔩 <b>حديد التسليح</b>", "china_fy": "🔩 أدخل fy الموثق بوحدة MPa.",
        "project_ready": "✅ <b>المشروع جاهز</b>", "invalid": "❌ قيمة غير صالحة.", "calc_error": "❌ خطأ في الحساب:\n<code>{}</code>",
        "back": "🔙 رجوع", "home": "🏠 الرئيسية", "cancel": "❌ إلغاء", "prev": "⬅️ السابق", "review": "📋 مراجعة", "calculate": "🧮 حساب",
        "edit": "✏️ تعديل", "show_rebar": "🔩 تفاصيل التسليح", "show_cut": "✂️ Cut List", "new_member": "➕ عنصر جديد", "summary": "📊 ملخص المشروع",
        "settings": "⚙️ الإعدادات", "help": "ℹ️ المساعدة", "equivalency": "🔄 معادلة التسليح", "current_count": "العدد الحالي", "current_dia": "القطر الحالي",
        "replacement_dia": "قطر البديل", "enter_value": "أدخل القيمة:", "equivalent": "المساحة مكافئة.", "not_equivalent": "المساحة غير كافية.",
        "engineering_warning": "⚠️ هذه معادلة مساحة فقط؛ يجب فحص التباعد والتفاصيل والوصلة والتثبيت منفصلاً.", "language": "🌐 اللغة", "materials": "🧱 المواد", "standard_setting": "📚 المعيار", "natural": "✍️ إدخال طبيعي", "multi_column": "🏢 عمود متعدد الطوابق", "result": "📌 النتيجة",
    },
    "zh": {
        "language": "🌐 <b>语言</b>", "welcome": "🏗️ <b>结构工程量引擎</b>\n\n选择标准、材料和结构构件。", "standard": "📚 <b>项目标准</b>", "concrete": "🧱 <b>混凝土</b>", "grade": "🔩 <b>钢筋等级</b>", "china_fy": "🔩 <b>钢筋 fy</b>\n请输入经验证的 MPa 值，不使用默认值。", "project_ready": "✅ <b>项目已准备</b>", "invalid": "❌ 输入无效。", "calc_error": "❌ 计算错误：\n<code>{}</code>", "back": "🔙 返回", "home": "🏠 首页", "cancel": "❌ 取消", "prev": "⬅️ 上一步", "review": "📋 检查", "calculate": "🧮 计算", "edit": "✏️ 编辑", "show_rebar": "🔩 钢筋明细", "show_cut": "✂️ Cut List", "new_member": "➕ 新构件", "summary": "📊 项目汇总", "settings": "⚙️ 设置", "help": "ℹ️ 帮助", "equivalency": "🔄 钢筋等效", "current_count": "当前数量", "current_dia": "当前直径", "replacement_dia": "替换直径", "enter_value": "请输入：", "equivalent": "面积满足等效条件。", "not_equivalent": "替换面积不足。", "engineering_warning": "⚠️ 仅检查面积等效；间距、锚固、搭接和构造必须单独检查。", "language": "🌐 语言", "materials": "🧱 材料", "standard_setting": "📚 标准", "natural": "✍️ 自然输入", "multi_column": "🏢 多层柱", "result": "📌 结果",
    },
}

MEMBER_NAMES = {
    "iso": "⬛ پی منفرد", "strip": "▬ پی نواری", "raft": "▰ پی گسترده / رادیه",
    "column_rect": "▯ ستون مستطیلی", "column_round": "◯ ستون گرد", "beam": "📐 تیر", "tie": "🔗 شناژ / کلاف",
    "wall": "🧱 دیوار", "stair": "🪜 راه‌پله", "roof": "🏠 سقف",
}

ROOF_TYPES = {
    "eps": {"name": {"fa": "🟦 سقف تیرچه یونولیتی", "en": "🟦 EPS joist roof", "ar": "🟦 سقف بلوك EPS", "zh": "🟦 EPS 肋梁楼板"}},
    "clay": {"name": {"fa": "🟫 سقف تیرچه سفالی", "en": "🟫 Clay-block joist roof", "ar": "🟫 سقف بلوك طيني", "zh": "🟫 陶土块肋梁楼板"}},
    "waffle": {"name": {"fa": "🔳 سقف وافل", "en": "🔳 Waffle slab", "ar": "🔳 سقف وافل", "zh": "🔳 密肋/华夫楼板"}},
    "slab": {"name": {"fa": "⬜ دال بتنی توپر", "en": "⬜ Solid slab", "ar": "⬜ بلاطة مصمتة", "zh": "⬜ 实心板"}},
}

# Main wizard fields retained for the original member flow.
STEPS = {
    "iso": [("count", {"fa":"تعداد پی","en":"Footing count","ar":"عدد القواعد","zh":"基础数量"}, "int"), ("L", {"fa":"طول پی (m)","en":"Length (m)","ar":"الطول (m)","zh":"长度(m)"}, "float"), ("W", {"fa":"عرض پی (m)","en":"Width (m)","ar":"العرض (m)","zh":"宽度(m)"}, "float"), ("T", {"fa":"ضخامت پی (m)","en":"Thickness (m)","ar":"السماكة (m)","zh":"厚度(m)"}, "float"), ("leanL", {"fa":"طول بتن مگر (m)","en":"Lean length (m)","ar":"طول الخرسانة النظافة","zh":"垫层长度"}, "float"), ("leanW", {"fa":"عرض بتن مگر (m)","en":"Lean width (m)","ar":"عرض خرسانة النظافة","zh":"垫层宽度"}, "float"), ("leanT", {"fa":"ضخامت بتن مگر (m)","en":"Lean thickness (m)","ar":"سماكة خرسانة النظافة","zh":"垫层厚度"}, "float"), ("bd", {"fa":"قطر میلگرد پایین (mm)","en":"Bottom bar diameter (mm)","ar":"قطر التسليح السفلي","zh":"底筋直径"}, "diameter"), ("bs", {"fa":"فاصله میلگرد پایین (mm)","en":"Bottom spacing (mm)","ar":"تباعد التسليح السفلي","zh":"底筋间距"}, "spacing"), ("td", {"fa":"قطر میلگرد بالا (mm)؛ اگر ندارد 0","en":"Top diameter (mm); 0 if none","ar":"قطر علوي؛ 0 عند عدم وجوده","zh":"顶筋直径；无则0"}, "diameter_optional"), ("ts", {"fa":"فاصله میلگرد بالا (mm)؛ اگر ندارد 0","en":"Top spacing (mm); 0 if none","ar":"تباعد علوي؛ 0 عند عدم وجوده","zh":"顶筋间距；无则0"}, "spacing_optional"), ("pl", {"fa":"طول پدستال (m)؛ اگر ندارد 0","en":"Pedestal length (m); 0 if none","ar":"طول البيدستال","zh":"柱墩长度"}, "float"), ("pw", {"fa":"عرض پدستال (m)؛ اگر ندارد 0","en":"Pedestal width (m); 0 if none","ar":"عرض البيدستال","zh":"柱墩宽度"}, "float"), ("ph", {"fa":"ارتفاع پدستال (m)؛ اگر ندارد 0","en":"Pedestal height (m); 0 if none","ar":"ارتفاع البيدستال","zh":"柱墩高度"}, "float")],
    "strip": [("count", {"fa":"تعداد نوار","en":"Strip count","ar":"عدد الشرائط","zh":"条基数量"}, "int"), ("L", {"fa":"طول نوار (m)","en":"Strip length (m)","ar":"طول الشريط","zh":"长度"}, "float"), ("W", {"fa":"عرض پی (m)","en":"Footing width (m)","ar":"عرض القاعدة","zh":"宽度"}, "float"), ("T", {"fa":"ضخامت پی (m)","en":"Thickness (m)","ar":"السماكة","zh":"厚度"}, "float"), ("leanL", {"fa":"طول بتن مگر (m)","en":"Lean length (m)","ar":"طول النظافة","zh":"垫层长度"}, "float"), ("leanW", {"fa":"عرض بتن مگر (m)","en":"Lean width (m)","ar":"عرض النظافة","zh":"垫层宽度"}, "float"), ("leanT", {"fa":"ضخامت بتن مگر (m)","en":"Lean thickness (m)","ar":"سماكة النظافة","zh":"垫层厚度"}, "float"), ("ld", {"fa":"قطر طولی پایین (mm)","en":"Bottom longitudinal diameter","ar":"قطر التسليح الطولي","zh":"底部纵筋直径"}, "diameter"), ("lc", {"fa":"تعداد طولی پایین","en":"Bottom longitudinal count","ar":"عدد التسليح الطولي","zh":"底部纵筋数量"}, "int"), ("td", {"fa":"قطر عرضی پایین (mm)","en":"Bottom transverse diameter","ar":"قطر التسليح العرضي","zh":"底部横筋直径"}, "diameter"), ("ts", {"fa":"فاصله عرضی پایین (mm)","en":"Bottom transverse spacing","ar":"تباعد العرضي","zh":"底部横筋间距"}, "spacing"), ("tld", {"fa":"قطر طولی بالا (mm)؛ اگر ندارد 0","en":"Top longitudinal diameter; 0 if none","ar":"قطر علوي؛ 0","zh":"顶部纵筋直径；无则0"}, "diameter_optional"), ("tlc", {"fa":"تعداد طولی بالا؛ اگر ندارد 0","en":"Top longitudinal count; 0 if none","ar":"عدد علوي؛ 0","zh":"顶部纵筋数量；无则0"}, "int"), ("ttd", {"fa":"قطر عرضی بالا (mm)؛ اگر ندارد 0","en":"Top transverse diameter; 0 if none","ar":"قطر عرضي علوي؛ 0","zh":"顶部横筋直径；无则0"}, "diameter_optional"), ("tts", {"fa":"فاصله عرضی بالا (mm)؛ اگر ندارد 0","en":"Top transverse spacing; 0 if none","ar":"تباعد عرضي علوي؛ 0","zh":"顶部横筋间距；无则0"}, "spacing_optional")],
    "raft": [("L", {"fa":"طول رادیه (m)","en":"Raft length (m)","ar":"طول اللبشة","zh":"筏板长度"}, "float"), ("W", {"fa":"عرض رادیه (m)","en":"Raft width (m)","ar":"عرض اللبشة","zh":"筏板宽度"}, "float"), ("T", {"fa":"ضخامت رادیه (m)","en":"Raft thickness (m)","ar":"سماكة اللبشة","zh":"筏板厚度"}, "float"), ("leanL", {"fa":"طول بتن مگر (m)","en":"Lean length","ar":"طول النظافة","zh":"垫层长度"}, "float"), ("leanW", {"fa":"عرض بتن مگر (m)","en":"Lean width","ar":"عرض النظافة","zh":"垫层宽度"}, "float"), ("leanT", {"fa":"ضخامت بتن مگر (m)","en":"Lean thickness","ar":"سماكة النظافة","zh":"垫层厚度"}, "float"), ("bxd", {"fa":"قطر X پایین (mm)","en":"Bottom X diameter","ar":"قطر X السفلي","zh":"底部X直径"}, "diameter"), ("bxs", {"fa":"فاصله X پایین (mm)","en":"Bottom X spacing","ar":"تباعد X السفلي","zh":"底部X间距"}, "spacing"), ("byd", {"fa":"قطر Y پایین (mm)","en":"Bottom Y diameter","ar":"قطر Y السفلي","zh":"底部Y直径"}, "diameter"), ("bys", {"fa":"فاصله Y پایین (mm)","en":"Bottom Y spacing","ar":"تباعد Y السفلي","zh":"底部Y间距"}, "spacing"), ("txd", {"fa":"قطر X بالا (mm)؛ اگر ندارد 0","en":"Top X diameter; 0 if none","ar":"قطر X العلوي؛ 0","zh":"顶部X直径；无则0"}, "diameter_optional"), ("txs", {"fa":"فاصله X بالا (mm)","en":"Top X spacing","ar":"تباعد X العلوي","zh":"顶部X间距"}, "spacing_optional"), ("tyd", {"fa":"قطر Y بالا (mm)؛ اگر ندارد 0","en":"Top Y diameter; 0 if none","ar":"قطر Y العلوي؛ 0","zh":"顶部Y直径；无则0"}, "diameter_optional"), ("tys", {"fa":"فاصله Y بالا (mm)","en":"Top Y spacing","ar":"تباعد Y العلوي","zh":"顶部Y间距"}, "spacing_optional")],
    "column_rect": [("count", {"fa":"تعداد ستون","en":"Column count","ar":"عدد الأعمدة","zh":"柱数量"}, "int"), ("W", {"fa":"عرض ستون (m)","en":"Width (m)","ar":"العرض","zh":"宽度"}, "float"), ("D", {"fa":"عمق ستون (m)","en":"Depth (m)","ar":"العمق","zh":"深度"}, "float"), ("H", {"fa":"ارتفاع ستون (m)","en":"Height (m)","ar":"الارتفاع","zh":"高度"}, "float"), ("ld", {"fa":"قطر میلگرد طولی (mm)","en":"Longitudinal diameter","ar":"قطر طولي","zh":"纵筋直径"}, "diameter"), ("lc", {"fa":"تعداد میلگرد طولی هر ستون","en":"Longitudinal bars/column","ar":"عدد التسليح الطولي","zh":"每柱纵筋数量"}, "int"), ("sd", {"fa":"قطر خاموت (mm)","en":"Stirrup diameter","ar":"قطر الكانة","zh":"箍筋直径"}, "diameter"), ("ss", {"fa":"فاصله خاموت (mm)","en":"Stirrup spacing","ar":"تباعد الكانات","zh":"箍筋间距"}, "spacing")],
    "column_round": [("count", {"fa":"تعداد ستون گرد","en":"Round column count","ar":"عدد الأعمدة الدائرية","zh":"圆柱数量"}, "int"), ("D", {"fa":"قطر ستون (m)","en":"Diameter (m)","ar":"القطر","zh":"直径"}, "float"), ("H", {"fa":"ارتفاع ستون (m)","en":"Height (m)","ar":"الارتفاع","zh":"高度"}, "float"), ("ld", {"fa":"قطر میلگرد طولی (mm)","en":"Longitudinal diameter","ar":"قطر طولي","zh":"纵筋直径"}, "diameter"), ("lc", {"fa":"تعداد میلگرد طولی هر ستون","en":"Longitudinal bars/column","ar":"عدد التسليح","zh":"每柱纵筋数量"}, "int"), ("sd", {"fa":"قطر خاموت (mm)","en":"Stirrup diameter","ar":"قطر الكانة","zh":"箍筋直径"}, "diameter"), ("ss", {"fa":"فاصله خاموت (mm)","en":"Stirrup spacing","ar":"تباعد الكانات","zh":"箍筋间距"}, "spacing")],
    "beam": [("count", {"fa":"تعداد تیر","en":"Beam count","ar":"عدد الجسور","zh":"梁数量"}, "int"), ("L", {"fa":"طول تیر (m)","en":"Length (m)","ar":"الطول","zh":"长度"}, "float"), ("W", {"fa":"عرض تیر (m)","en":"Width (m)","ar":"العرض","zh":"宽度"}, "float"), ("H", {"fa":"ارتفاع تیر (m)","en":"Height (m)","ar":"الارتفاع","zh":"高度"}, "float"), ("bd", {"fa":"قطر میلگرد پایین (mm)","en":"Bottom diameter","ar":"قطر سفلي","zh":"底筋直径"}, "diameter"), ("bc", {"fa":"تعداد میلگرد پایین","en":"Bottom bar count","ar":"عدد سفلي","zh":"底筋数量"}, "int"), ("td", {"fa":"قطر میلگرد بالا (mm)","en":"Top diameter","ar":"قطر علوي","zh":"顶筋直径"}, "diameter"), ("tc", {"fa":"تعداد میلگرد بالا","en":"Top bar count","ar":"عدد علوي","zh":"顶筋数量"}, "int"), ("sd", {"fa":"قطر خاموت (mm)","en":"Stirrup diameter","ar":"قطر الكانة","zh":"箍筋直径"}, "diameter"), ("ss", {"fa":"فاصله خاموت (mm)","en":"Stirrup spacing","ar":"تباعد الكانات","zh":"箍筋间距"}, "spacing")],
    "tie": [("count", {"fa":"تعداد شناژ/کلاف","en":"Tie count","ar":"عدد الكمرات الرابطة","zh":"系梁数量"}, "int"), ("L", {"fa":"طول (m)","en":"Length (m)","ar":"الطول","zh":"长度"}, "float"), ("W", {"fa":"عرض (m)","en":"Width (m)","ar":"العرض","zh":"宽度"}, "float"), ("H", {"fa":"ارتفاع (m)","en":"Height (m)","ar":"الارتفاع","zh":"高度"}, "float"), ("ld", {"fa":"قطر میلگرد طولی (mm)","en":"Longitudinal diameter","ar":"قطر طولي","zh":"纵筋直径"}, "diameter"), ("lc", {"fa":"تعداد میلگرد طولی","en":"Longitudinal count","ar":"عدد طولي","zh":"纵筋数量"}, "int"), ("sd", {"fa":"قطر خاموت (mm)","en":"Stirrup diameter","ar":"قطر الكانة","zh":"箍筋直径"}, "diameter"), ("ss", {"fa":"فاصله خاموت (mm)","en":"Stirrup spacing","ar":"تباعد الكانات","zh":"箍筋间距"}, "spacing")],
    "wall": [("L", {"fa":"طول دیوار (m)","en":"Wall length","ar":"طول الجدار","zh":"墙长"}, "float"), ("H", {"fa":"ارتفاع دیوار (m)","en":"Wall height","ar":"ارتفاع الجدار","zh":"墙高"}, "float"), ("T", {"fa":"ضخامت دیوار (m)","en":"Wall thickness","ar":"سماكة الجدار","zh":"墙厚"}, "float"), ("vd", {"fa":"قطر میلگرد قائم (mm)","en":"Vertical diameter","ar":"قطر رأسي","zh":"竖筋直径"}, "diameter"), ("vs", {"fa":"فاصله میلگرد قائم (mm)","en":"Vertical spacing","ar":"تباعد رأسي","zh":"竖筋间距"}, "spacing"), ("hd", {"fa":"قطر میلگرد افقی (mm)","en":"Horizontal diameter","ar":"قطر أفقي","zh":"水平筋直径"}, "diameter"), ("hs", {"fa":"فاصله میلگرد افقی (mm)","en":"Horizontal spacing","ar":"تباعد أفقي","zh":"水平筋间距"}, "spacing")],
    "stair": [("L", {"fa":"طول شیب/دال (m)","en":"Slab/sloping length","ar":"طول الدرج","zh":"斜板长度"}, "float"), ("W", {"fa":"عرض راه‌پله (m)","en":"Stair width","ar":"عرض الدرج","zh":"楼梯宽度"}, "float"), ("T", {"fa":"ضخامت دال (m)","en":"Slab thickness","ar":"سماكة الدرج","zh":"板厚"}, "float"), ("md", {"fa":"قطر میلگرد اصلی (mm)","en":"Main diameter","ar":"قطر رئيسي","zh":"主筋直径"}, "diameter"), ("ms", {"fa":"فاصله میلگرد اصلی (mm)","en":"Main spacing","ar":"تباعد رئيسي","zh":"主筋间距"}, "spacing"), ("dd", {"fa":"قطر میلگرد توزیعی (mm)","en":"Distribution diameter","ar":"قطر توزيع","zh":"分布筋直径"}, "diameter"), ("ds", {"fa":"فاصله میلگرد توزیعی (mm)","en":"Distribution spacing","ar":"تباعد توزيع","zh":"分布筋间距"}, "spacing"), ("steps", {"fa":"تعداد پله","en":"Steps","ar":"عدد الدرجات","zh":"踏步数"}, "int"), ("riser", {"fa":"ارتفاع رایزر (m)","en":"Riser (m)","ar":"ارتفاع القائمة","zh":"踢面高"}, "float"), ("tread", {"fa":"کف پله (m)","en":"Tread (m)","ar":"عرض النائمة","zh":"踏面宽"}, "float")],
}

ROOF_STEPS = {
    "eps": [
        ("span_m", "دهانه سقف (m)", "float"), ("width_m", "عرض سقف (m)", "float"), ("joist_spacing_mm", "فاصله تیرچه (mm)", "spacing"),
        ("eps_length_m", "طول بلوک یونولیت (m)", "float"), ("eps_width_m", "عرض بلوک یونولیت (m)", "float"), ("eps_height_m", "ارتفاع بلوک (m)", "float"),
        ("joist_length_m", "طول تیرچه (m)؛ 0 برای برابر دهانه", "float0"), ("joist_count", "تعداد تیرچه؛ 0 برای محاسبه هندسی", "int0"),
        ("thermal_dia_mm", "قطر میلگرد حرارتی (mm)؛ 0 برای عدم ورود", "diameter_optional"), ("thermal_spacing_mm", "فاصله حرارتی (mm)", "spacing_optional"),
        ("transverse_dia_mm", "قطر کلاف عرضی (mm)؛ 0 برای عدم ورود", "diameter_optional"), ("transverse_count", "تعداد کلاف عرضی؛ 0 برای عدم ورود", "int0"),
        ("concrete_topping_thickness_m", "ضخامت بتن رویه (m)", "float"), ("block_count", "تعداد بلوک؛ 0 برای محاسبه هندسی", "int0"),
    ],
    "clay": [
        ("span_m", "دهانه سقف (m)", "float"), ("width_m", "عرض سقف (m)", "float"), ("joist_spacing_mm", "فاصله تیرچه (mm)", "spacing"),
        ("block_length_m", "طول بلوک سفالی (m)", "float"), ("block_width_m", "عرض بلوک سفالی (m)", "float"), ("block_height_m", "ارتفاع بلوک (m)", "float"),
        ("joist_length_m", "طول تیرچه (m)؛ 0 برای برابر دهانه", "float0"), ("joist_count", "تعداد تیرچه؛ 0 برای محاسبه هندسی", "int0"),
        ("thermal_dia_mm", "قطر میلگرد حرارتی (mm)؛ 0 برای عدم ورود", "diameter_optional"), ("thermal_spacing_mm", "فاصله حرارتی (mm)", "spacing_optional"),
        ("transverse_dia_mm", "قطر کلاف عرضی (mm)؛ 0 برای عدم ورود", "diameter_optional"), ("transverse_count", "تعداد کلاف عرضی؛ 0 برای عدم ورود", "int0"),
        ("concrete_topping_thickness_m", "ضخامت بتن رویه (m)", "float"), ("block_count", "تعداد بلوک؛ 0 برای محاسبه هندسی", "int0"),
    ],
    "waffle": [("length_m","طول سقف (m)","float"),("width_m","عرض سقف (m)","float"),("module_length_m","طول مدول وافل (m)","float"),("module_width_m","عرض مدول وافل (m)","float"),("depth_m","عمق وافل (m)","float"),("top_slab_thickness_m","ضخامت دال رویه (m)","float"),("main_dia_mm","قطر میلگرد اصلی (mm)","diameter"),("main_spacing_mm","فاصله میلگرد اصلی (mm)","spacing"),("dist_dia_mm","قطر میلگرد توزیعی (mm)","diameter"),("dist_spacing_mm","فاصله میلگرد توزیعی (mm)","spacing")],
    "slab": [("length_m","طول دال (m)","float"),("width_m","عرض دال (m)","float"),("thickness_m","ضخامت دال (m)","float"),("main_dia_mm","قطر میلگرد اصلی (mm)","diameter"),("main_spacing_mm","فاصله میلگرد اصلی (mm)","spacing"),("dist_dia_mm","قطر میلگرد توزیعی (mm)","diameter"),("dist_spacing_mm","فاصله میلگرد توزیعی (mm)","spacing")],
}


def kb(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(str(t), callback_data=str(d)) for t, d in row] for row in rows])


def language_keyboard():
    return kb([[('🇮🇷 فارسی','lang_fa'),('🇬🇧 English','lang_en')],[('🇸🇦 العربية','lang_ar'),('🇨🇳 中文','lang_zh')]])


def standard_keyboard(lang):
    return kb([[(info[lang], f'std_{key}')] for key, info in STANDARDS.items()])


def concrete_keyboard(lang):
    return kb([[('C'+str(v), f'fc_{v}') for v in CONCRETE_OPTIONS]])


def rebar_grade_keyboard(lang):
    std = contextless_standard = None
    return kb([])  # replaced by choose_grade_screen()


def grade_keyboard(lang, standard):
    opts = REBAR_OPTIONS.get(standard, [])
    rows = [[(name, f'grade_{name.replace(" ", "")}') for name, _ in opts]]
    if standard == 'china':
        rows = [[('✍️ fy (MPa)', 'grade_china_custom')]]
    return kb(rows + [[(TEXT[lang]['back'], 'home')]])


def main_menu(lang):
    t = TEXT[lang]
    return kb([
        [('🧱 فونداسیون','foundation'),('🏛️ ستون‌ها','columns')],
        [('📐 تیرها','beams'),('🏠 سقف‌ها','roofs')],
        [('🔗 شناژ/کلاف','ties'),('🧱 دیوارها','walls')],
        [('🪜 راه‌پله','stairs'),('🔄 معادل‌سازی','equiv')],
        [(t['natural'],'natural_input'),(t['multi_column'],'multi_column')],
        [(t['summary'],'summary'),(t['settings'],'settings')],
        [(t['help'],'help'),(t['language'],'language')],
    ])


def back_kb(lang, callback='home'):
    return kb([[(TEXT[lang]['back'], callback)]])


def step_kb(lang):
    return kb([[(TEXT[lang]['prev'],'prev'),(TEXT[lang]['cancel'],'cancel')]])


def review_kb(lang):
    return kb([[(TEXT[lang]['calculate'],'do_calculate'),(TEXT[lang]['edit'],'edit_member')],[(TEXT[lang]['cancel'],'cancel')]])


def result_kb(lang):
    return kb([[(TEXT[lang]['show_rebar'],'show_rebar'),(TEXT[lang]['show_cut'],'show_cut')],[(TEXT[lang]['new_member'],'new_member'),(TEXT[lang]['summary'],'summary')],[(TEXT[lang]['home'],'home')]])


def section_kb(lang, items):
    """Build section keyboards safely.

    Accepts either:
      [(text, callback), ...]                  # one row
    or
      [[(text, callback), ...], [...]]        # multiple rows

    The previous build wrapped an already-rowed list one level too deep,
    producing tuple/list callback_data and making Telegram buttons appear dead.
    """
    if not items:
        return kb([])
    if isinstance(items[0], tuple):
        rows = [items]
    else:
        rows = items
    normalized = []
    for row in rows:
        clean_row = []
        for item in row:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError(f"Invalid keyboard item: {item!r}")
            text, data = item
            clean_row.append((str(text), str(data)))
        if clean_row:
            normalized.append(clean_row)
    return kb(normalized)


def normalize_number(text):
    s = str(text).strip()
    trans = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    s = s.translate(trans).replace(',', '.').replace('٫', '.')
    if s.count('/') == 1:
        s = s.replace('/', '.')
    return s


def parse_number(text, integer=False):
    s = normalize_number(text)
    x = float(s)
    if not math.isfinite(x):
        raise ValueError('Non-finite number is not allowed.')
    if x < 0:
        raise ValueError('Negative value is not allowed.')
    if integer:
        if not x.is_integer():
            raise ValueError('Integer required.')
        return int(x)
    return x


def project_standard(context):
    return context.user_data.get('standard')


def project_fc(context):
    return float(context.user_data.get('fc', 25))


def project_fy(context):
    return float(context.user_data.get('fy'))


def project_grade(context):
    return str(context.user_data.get('rebar_grade', ''))


def project_ready(context):
    return bool(context.user_data.get('standard') and context.user_data.get('fc') and context.user_data.get('fy'))


def prompt_text(lang, label, i, total):
    return f"📐 <b>{escape(label)}</b>\n\n{TEXT[lang]['enter_value']}\n\n📍 <b>{i}</b> / <b>{total}</b>"


def field_label(field, lang):
    return field[1].get(lang, field[1].get('en', field[0])) if isinstance(field[1], dict) else str(field[1])


def format_value(v):
    return f'{v:g}' if isinstance(v, float) else str(v)


def review_text_with_context(context, kind, values, lang):
    lines = [f"📋 <b>{escape(MEMBER_NAMES.get(kind, kind))}</b>", '', '<pre>']
    for key, label, typ in STEPS.get(kind, []):
        if key in values:
            lines.append(f'{field_label((key,label,typ),lang):<28} {format_value(values[key])}')
    lines += ['</pre>', '', f"📚 {escape(STANDARDS[project_standard(context)][lang])}", f"🧱 C{project_fc(context):g}", f"🔩 {escape(project_grade(context))}"]
    return '\n'.join(lines)


def review_roof(context, roof_type, values, lang):
    lines = [f"📋 <b>{escape(ROOF_TYPES[roof_type]['name'][lang])}</b>", '', '<pre>']
    for key, label, typ in ROOF_STEPS[roof_type]:
        if key in values:
            lines.append(f'{label:<36} {format_value(values[key])}')
    lines += ['</pre>', '', f"📚 {escape(STANDARDS[project_standard(context)][lang])}", f"🧱 C{project_fc(context):g}", f"🔩 {escape(project_grade(context))}"]
    return '\n'.join(lines)


def summary_text(kind, result, lang):
    name = MEMBER_NAMES.get(kind, kind)
    concrete = float(result.get('total_concrete_m3', result.get('concrete_m3', 0)) or 0)
    rebar = float(result.get('total_rebar_kg', 0) or 0)
    waste = float(result.get('total_rebar_waste_m', 0) or 0)
    lines = [f"📌 <b>{TEXT[lang]['result']}</b>", '', f'<b>{escape(name)}</b>', '', '<pre>', f'Concrete      {concrete:>10.3f} m³', f'Rebar         {rebar:>10.1f} kg', f'12m stock     {int(result.get("total_stock_bars_12m",0) or 0):>10d}', f'Offcut waste   {waste:>10.2f} m']
    if kind == 'iso':
        lines += [f'Lean concrete {float(result.get("lean_concrete_m3",0) or 0):>10.3f} m³', f'Footing        {float(result.get("footing_concrete_m3",0) or 0):>10.3f} m³', f'Pedestal       {float(result.get("pedestal_concrete_m3",0) or 0):>10.3f} m³']
    lines += ['</pre>', '', '⚠️ Quantity output is not a substitute for final structural design/detailing.']
    return '\n'.join(lines)


def rebar_text(details, lang='fa'):
    if not details:
        return f"🔩 <b>{TEXT[lang]['show_rebar']}</b>\n\nNo rebar detail."
    lines = [f"🔩 <b>{TEXT[lang]['show_rebar']}</b>", '', '<pre>', 'Dia  Pieces   Length(m)   Weight(kg)  12m', '--------------------------------------------']
    for x in details:
        lines.append(f"Φ{int(x.get('diameter_mm',0)):<3} {int(x.get('piece_count',0)):>6} {float(x.get('length_m',0)):>12.2f} {float(x.get('weight_kg',0)):>11.1f} {int(x.get('bars_12m',0)):>5}")
    lines += ['</pre>']
    return '\n'.join(lines)


def cut_text(details, lang='fa'):
    if not details:
        return f"✂️ <b>{TEXT[lang]['show_cut']}</b>\n\nNo cut plan."
    chunks = [f"✂️ <b>{TEXT[lang]['show_cut']}</b>", '']
    for x in details:
        dia = int(x.get('diameter_mm',0)); plans = x.get('cut_plan', [])
        chunks.append(f'<b>Φ{dia}</b> — {int(x.get("bars_12m",len(plans)))} × 12m')
        chunks.append('<pre>')
        for i, p in enumerate(plans[:30], 1):
            pieces = ' + '.join(f'{float(v):.2f}' for v in p.get('pieces', []))
            chunks.append(f'{i:02d}) {pieces} = {float(p.get("used_m",0)):.2f} | waste {float(p.get("waste_m",0)):.2f}')
        if len(plans) > 30: chunks.append(f'... {len(plans)-30} more')
        chunks.append('</pre>')
    return '\n'.join(chunks)


def project_summary_text(context, lang):
    items = context.user_data.get('project_results', [])
    agg = aggregate_project_results([x.get('result',{}) for x in items if isinstance(x,dict)])
    return (f"📊 <b>{TEXT[lang]['summary']}</b>\n\n<pre>"
            f"Members       {agg.get('member_count',0):>8d}\n"
            f"Concrete      {agg.get('total_concrete_m3',0):>8.3f} m³\n"
            f"Rebar         {agg.get('total_rebar_kg',0):>8.1f} kg\n"
            f"12m stock     {agg.get('total_stock_bars_12m',0):>8d}\n"
            f"Offcut waste  {agg.get('total_rebar_waste_m',0):>8.2f} m"
            f"</pre>")


def calculate(context, kind, v):
    if kind == 'iso':
        return isolated_footing(int(v['count']),v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['bd']),v['bs'],int(v['td']) if v['td']>0 else None,v['ts'] if v['td']>0 and v['ts']>0 else None,40,0,v['pl'],v['pw'],v['ph'])
    if kind == 'strip':
        return strip_footing(int(v['count']),v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['ld']),int(v['lc']),int(v['td']),v['ts'],int(v['tld']) if v['tld']>0 else None,int(v['tlc']) if v['tlc']>0 else None,int(v['ttd']) if v['ttd']>0 else None,v['tts'] if v['ttd']>0 and v['tts']>0 else None,40,0)
    if kind == 'raft':
        return raft_foundation(v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['bxd']),v['bxs'],int(v['byd']),v['bys'],int(v['txd']) if v['txd']>0 else None,v['txs'] if v['txd']>0 and v['txs']>0 else None,int(v['tyd']) if v['tyd']>0 else None,v['tys'] if v['tyd']>0 and v['tys']>0 else None,40,0)
    if kind == 'column_rect': return column_rectangular(int(v['count']),v['W'],v['D'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],40)
    if kind == 'column_round': return column_round(int(v['count']),v['D'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],40)
    if kind == 'beam': return beam(int(v['count']),v['L'],v['W'],v['H'],int(v['bd']),int(v['bc']),int(v['td']),int(v['tc']),int(v['sd']),v['ss'],40)
    if kind == 'tie': return tie_beam(int(v['count']),v['L'],v['W'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],40)
    if kind == 'wall': return wall_concrete(v['L'],v['H'],v['T'],int(v['vd']),v['vs'],int(v['hd']),v['hs'],40)
    if kind == 'stair': return stair_slab(v['L'],v['W'],v['T'],int(v['md']),v['ms'],int(v['dd']),v['ds'],int(v['steps']),v['riser'],v['tread'])
    raise ValueError(f'Unknown member kind: {kind}')


def roof_calculate(context, roof_type, v):
    if roof_type == 'eps':
        kw = dict(span_m=v['span_m'],width_m=v['width_m'],joist_spacing_mm=v['joist_spacing_mm'],eps_length_m=v['eps_length_m'],eps_width_m=v['eps_width_m'],eps_height_m=v['eps_height_m'],joist_length_m=(v['joist_length_m'] or None),joist_count=(v['joist_count'] or None),thermal_dia_mm=(v['thermal_dia_mm'] or None),thermal_spacing_mm=(v['thermal_spacing_mm'] or None),transverse_dia_mm=(v['transverse_dia_mm'] or None),transverse_count=(v['transverse_count'] or None),concrete_topping_thickness_m=v['concrete_topping_thickness_m'],block_count=(v['block_count'] or None))
        return joist_eps_roof_detail(**kw)
    if roof_type == 'clay':
        kw = dict(span_m=v['span_m'],width_m=v['width_m'],joist_spacing_mm=v['joist_spacing_mm'],block_length_m=v['block_length_m'],block_width_m=v['block_width_m'],block_height_m=v['block_height_m'],joist_length_m=(v['joist_length_m'] or None),joist_count=(v['joist_count'] or None),thermal_dia_mm=(v['thermal_dia_mm'] or None),thermal_spacing_mm=(v['thermal_spacing_mm'] or None),transverse_dia_mm=(v['transverse_dia_mm'] or None),transverse_count=(v['transverse_count'] or None),concrete_topping_thickness_m=v['concrete_topping_thickness_m'],block_count=(v['block_count'] or None))
        return joist_clay_roof_detail(**kw)
    if roof_type == 'waffle':
        return waffle_roof_detail(length_m=v['length_m'],width_m=v['width_m'],module_length_m=v['module_length_m'],module_width_m=v['module_width_m'],depth_m=v['depth_m'],top_slab_thickness_m=v['top_slab_thickness_m'],main_dia_mm=int(v['main_dia_mm']),main_spacing_mm=v['main_spacing_mm'],dist_dia_mm=int(v['dist_dia_mm']),dist_spacing_mm=v['dist_spacing_mm'])
    if roof_type == 'slab':
        return solid_slab_roof_detail(length_m=v['length_m'],width_m=v['width_m'],thickness_m=v['thickness_m'],main_dia_mm=int(v['main_dia_mm']),main_spacing_mm=v['main_spacing_mm'],dist_dia_mm=int(v['dist_dia_mm']),dist_spacing_mm=v['dist_spacing_mm'])
    raise ValueError('Unsupported roof system.')


async def start_project_setup(q, context):
    context.user_data.setdefault('project_results', [])
    await q.edit_message_text(TEXT[context.user_data.get('lang','fa')]['standard'],parse_mode='HTML',reply_markup=standard_keyboard(context.user_data.get('lang','fa')))


async def choose_standard(update, context):
    q=update.callback_query; data=q.data; lang=context.user_data.get('lang','fa')
    std=data[4:]
    if std not in STANDARDS: raise ValueError('Unsupported standard.')
    context.user_data['standard']=normalize_standard(std)
    await q.edit_message_text(TEXT[lang]['concrete'],parse_mode='HTML',reply_markup=concrete_keyboard(lang))


async def choose_concrete(update, context):
    q=update.callback_query; lang=context.user_data.get('lang','fa')
    fc=parse_number(q.data[3:], integer=False)
    context.user_data['fc']=fc
    std=project_standard(context)
    await q.edit_message_text(TEXT[lang]['grade'],parse_mode='HTML',reply_markup=grade_keyboard(lang,std))


async def choose_grade(update, context):
    q=update.callback_query; lang=context.user_data.get('lang','fa'); raw=q.data[6:]
    std=project_standard(context)
    if raw == 'china_custom':
        context.user_data['awaiting_fy']=True
        return await q.edit_message_text(TEXT[lang]['china_fy'],parse_mode='HTML',reply_markup=back_kb(lang))
    grade=raw.replace('Grade','Grade ').replace('B400','B400').replace('B500','B500')
    # Restore display names for A2/A3/A4 and Grade40/Grade60.
    if std == 'aci318' and raw in ('Grade40','Grade60'): grade=raw[:5]+' '+raw[5:]
    try: fy=rebar_grade_yield_mpa(std,grade)
    except Exception as exc: return await q.edit_message_text(TEXT[lang]['calc_error'].format(escape(str(exc))),parse_mode='HTML',reply_markup=back_kb(lang))
    context.user_data.update(rebar_grade=grade,fy=float(fy),project_results=[])
    await q.edit_message_text(TEXT[lang]['project_ready']+f"\n\n📚 {escape(STANDARDS[std][lang])}\n🧱 C{project_fc(context):g}\n🔩 {escape(grade)} / fy={fy:g} MPa",parse_mode='HTML',reply_markup=main_menu(lang))


async def begin_wizard(update, context, kind):
    q=update.callback_query; lang=context.user_data.get('lang','fa')
    if not project_ready(context): return await start_project_setup(q,context)
    context.user_data.update(kind=kind,step_index=0,values={},history=[])
    fields=STEPS[kind]; _,label,typ=fields[0]
    await q.edit_message_text(prompt_text(lang,field_label(fields[0],lang),1,len(fields)),parse_mode='HTML',reply_markup=step_kb(lang))


async def receive(update, context):
    lang=context.user_data.get('lang','fa'); kind=context.user_data.get('kind'); index=context.user_data.get('step_index')
    if kind is None or index is None:
        await update.message.reply_text(TEXT[lang]['welcome'],parse_mode='HTML',reply_markup=main_menu(lang)); return
    fields=STEPS[kind]; key,label,typ=fields[index]
    try:
        integer=typ in ('int','diameter','diameter_optional','spacing','spacing_optional','int0')
        value=parse_number(update.message.text,integer=integer)
        if typ=='diameter' and value==0: raise ValueError('Diameter must be positive.')
        if typ=='spacing' and value==0: raise ValueError('Spacing must be positive.')
    except Exception:
        await update.message.reply_text(TEXT[lang]['invalid'],reply_markup=step_kb(lang)); return
    context.user_data['values'][key]=value; context.user_data['history'].append(index)
    nxt=index+1
    if nxt<len(fields):
        context.user_data['step_index']=nxt
        await update.message.reply_text(prompt_text(lang,field_label(fields[nxt],lang),nxt+1,len(fields)),parse_mode='HTML',reply_markup=step_kb(lang)); return
    context.user_data['step_index']=None
    await update.message.reply_text(review_text_with_context(context,kind,context.user_data['values'],lang),parse_mode='HTML',reply_markup=review_kb(lang))


async def begin_roof(update, context, roof_type):
    q=update.callback_query; lang=context.user_data.get('lang','fa')
    if not project_ready(context): return await start_project_setup(q,context)
    context.user_data.update(kind='roof',roof_type=roof_type,roof_name=ROOF_TYPES[roof_type]['name'][lang],roof_step_index=0,roof_values={})
    f=ROOF_STEPS[roof_type][0]
    await q.edit_message_text(f"🏠 <b>{escape(context.user_data['roof_name'])}</b>\n\n{prompt_text(lang,f[1],1,len(ROOF_STEPS[roof_type]))}",parse_mode='HTML',reply_markup=step_kb(lang))


async def receive_roof(update, context):
    lang=context.user_data.get('lang','fa'); rt=context.user_data.get('roof_type'); idx=context.user_data.get('roof_step_index')
    fields=ROOF_STEPS.get(rt,[])
    if rt is None or idx is None: return False
    key,label,typ=fields[idx]
    try:
        integer=typ in ('diameter','diameter_optional','spacing','spacing_optional','int0')
        value=parse_number(update.message.text,integer=integer)
    except Exception:
        await update.message.reply_text(TEXT[lang]['invalid'],reply_markup=step_kb(lang)); return True
    context.user_data['roof_values'][key]=value
    nxt=idx+1
    if nxt<len(fields):
        context.user_data['roof_step_index']=nxt
        f=fields[nxt]
        await update.message.reply_text(prompt_text(lang,f[1],nxt+1,len(fields)),parse_mode='HTML',reply_markup=step_kb(lang)); return True
    context.user_data['roof_step_index']=None
    await update.message.reply_text(review_roof(context,rt,context.user_data['roof_values'],lang),parse_mode='HTML',reply_markup=review_kb(lang)); return True


async def do_calculate(update, context):
    q=update.callback_query; await q.answer(); lang=context.user_data.get('lang','fa')
    try:
        if context.user_data.get('kind')=='roof':
            rt=context.user_data['roof_type']; result=roof_calculate(context,rt,context.user_data['roof_values']); kind='roof'
            values=dict(context.user_data['roof_values']); values['roof_type']=rt
        else:
            kind=context.user_data['kind']; values=dict(context.user_data.get('values',{})); result=calculate(context,kind,values)
        context.user_data['result']=result
        context.user_data.setdefault('project_results',[]).append({'kind':kind,'values':values,'roof_type':context.user_data.get('roof_type'),'result':result})
        await q.edit_message_text(summary_text(kind,result,lang),parse_mode='HTML',reply_markup=result_kb(lang))
    except Exception as exc:
        logger.exception('Calculation failed')
        await q.edit_message_text(TEXT[lang]['calc_error'].format(escape(str(exc))),parse_mode='HTML',reply_markup=back_kb(lang))


async def begin_equivalency(update, context):
    q=update.callback_query; lang=context.user_data.get('lang','fa')
    context.user_data['equiv']={}; context.user_data['equiv_step']=0
    await q.edit_message_text(f"🔄 <b>{TEXT[lang]['equivalency']}</b>\n\n1️⃣ {TEXT[lang]['current_count']}\n\n{TEXT[lang]['enter_value']}",parse_mode='HTML',reply_markup=back_kb(lang))


async def receive_equivalency(update, context):
    lang=context.user_data.get('lang','fa'); step=context.user_data.get('equiv_step')
    if step is None: return False
    try: value=parse_number(update.message.text,integer=True)
    except Exception:
        await update.message.reply_text(TEXT[lang]['invalid']); return True
    eq=context.user_data.setdefault('equiv',{})
    if step==0:
        eq['count']=value; context.user_data['equiv_step']=1
        await update.message.reply_text(f"2️⃣ {TEXT[lang]['current_dia']}\n\n{TEXT[lang]['enter_value']}",reply_markup=kb([[('Φ'+str(d),f'equiv_current_{d}') for d in (8,10,12,14,16,18,20,22,25,28,32)],[('0','home')]])); return True
    if step==1:
        eq['current_dia']=value; context.user_data['equiv_step']=2
        await update.message.reply_text(f"3️⃣ {TEXT[lang]['replacement_dia']}\n\n{TEXT[lang]['enter_value']}",reply_markup=kb([[('Φ'+str(d),f'equiv_replace_{d}') for d in (8,10,12,14,16,18,20,22,25,28,32)],[('0','home')]])); return True
    return False


async def show_equiv_result(update, context, replacement_dia):
    q=update.callback_query; lang=context.user_data.get('lang','fa'); eq=context.user_data.get('equiv',{}); eq['replacement_dia']=replacement_dia
    try:
        r=equivalent_rebar_count(eq['count'],eq['current_dia'],replacement_dia)
        status='🟢' if r['area_equivalent'] else '🔴'; status_text=TEXT[lang]['equivalent'] if r['area_equivalent'] else TEXT[lang]['not_equivalent']
        msg=(f"🔄 <b>{TEXT[lang]['equivalency']}</b>\n\n<pre>Current: {eq['count']} Φ{eq['current_dia']}\nArea: {r['current_area_mm2']:.0f} mm²\n\nReplacement: Φ{replacement_dia}\nRequired count: {r['required_count']}\nArea/bar: {r['replacement_bar_area_mm2']:.0f} mm²</pre>\n{status} {status_text}\n\n{TEXT[lang]['engineering_warning']}")
        context.user_data['equiv_step']=None
        await q.edit_message_text(msg,parse_mode='HTML',reply_markup=back_kb(lang))
    except Exception as exc:
        await q.edit_message_text(TEXT[lang]['calc_error'].format(escape(str(exc))),parse_mode='HTML',reply_markup=back_kb(lang))


async def buttons(update, context):
    """Single, deterministic callback dispatcher.

    Every inline keyboard callback must pass through this function (except the
    optional language handler removed from main below).  Unknown callbacks are
    surfaced to the user instead of silently falling back to Home.
    """
    q = update.callback_query
    if q is None:
        return
    data = str(q.data or '')
    lang = context.user_data.get('lang', 'fa')
    try:
        await q.answer()

        if data == 'language':
            return await q.edit_message_text(TEXT[lang]['language'], reply_markup=language_keyboard())
        if data.startswith('lang_'):
            new_lang = data.split('_', 1)[1]
            if new_lang not in TEXT:
                raise ValueError('Unsupported language.')
            # Preserve project data when changing language.
            context.user_data['lang'] = new_lang
            lang = new_lang
            ready = project_ready(context)
            return await q.edit_message_text(
                TEXT[lang]['welcome'] if ready else TEXT[lang]['standard'],
                parse_mode='HTML',
                reply_markup=main_menu(lang) if ready else standard_keyboard(lang),
            )

        if data.startswith('std_'):
            return await choose_standard(update, context)
        if data.startswith('fc_'):
            return await choose_concrete(update, context)
        if data.startswith('grade_'):
            return await choose_grade(update, context)

        if data == 'home':
            saved = {k: context.user_data.get(k) for k in ('lang', 'standard', 'fc', 'rebar_grade', 'fy')}
            results = context.user_data.get('project_results', [])
            context.user_data.clear()
            context.user_data.update({k: v for k, v in saved.items() if v is not None})
            context.user_data['project_results'] = results
            lang = context.user_data.get('lang', 'fa')
            return await q.edit_message_text(
                TEXT[lang]['welcome'], parse_mode='HTML',
                reply_markup=main_menu(lang) if project_ready(context) else standard_keyboard(lang)
            )

        if data == 'cancel':
            for k in ('kind', 'step_index', 'values', 'history', 'roof_type', 'roof_name',
                      'roof_step_index', 'roof_values', 'result', 'natural_mode',
                      'multi_mode', 'equiv', 'equiv_step', 'awaiting_fy'):
                context.user_data.pop(k, None)
            return await q.edit_message_text(TEXT[lang]['welcome'], parse_mode='HTML', reply_markup=main_menu(lang))

        if data == 'prev':
            if context.user_data.get('kind') == 'roof':
                idx = context.user_data.get('roof_step_index')
                rt = context.user_data.get('roof_type')
                if rt not in ROOF_STEPS or idx in (None, 0):
                    return await q.edit_message_text(TEXT[lang]['welcome'], parse_mode='HTML', reply_markup=main_menu(lang))
                idx -= 1
                context.user_data['roof_step_index'] = idx
                key = ROOF_STEPS[rt][idx][0]
                context.user_data['roof_values'].pop(key, None)
                f = ROOF_STEPS[rt][idx]
                return await q.edit_message_text(prompt_text(lang, f[1], idx + 1, len(ROOF_STEPS[rt])),
                                                 parse_mode='HTML', reply_markup=step_kb(lang))
            kind = context.user_data.get('kind')
            idx = context.user_data.get('step_index')
            if not kind or kind not in STEPS or idx in (None, 0):
                return await q.edit_message_text(TEXT[lang]['welcome'], parse_mode='HTML', reply_markup=main_menu(lang))
            idx -= 1
            context.user_data['step_index'] = idx
            context.user_data['values'].pop(STEPS[kind][idx][0], None)
            f = STEPS[kind][idx]
            return await q.edit_message_text(prompt_text(lang, field_label(f, lang), idx + 1, len(STEPS[kind])),
                                             parse_mode='HTML', reply_markup=step_kb(lang))

        if data == 'do_calculate':
            return await do_calculate(update, context)

        if data == 'edit_member':
            if context.user_data.get('kind') == 'roof':
                return await begin_roof(update, context, context.user_data['roof_type'])
            return await begin_wizard(update, context, context.user_data['kind'])

        # Main sections.
        section_routes = {
            'foundation': ('🧱 <b>فونداسیون</b>', [[('⬛ پی منفرد', 'foundation_iso'), ('▬ پی نواری', 'foundation_strip')],
                                                   [('▰ پی گسترده / رادیه', 'foundation_raft')]]),
            'columns': ('🏛️ <b>ستون‌ها</b>', [[('▯ ستون مستطیلی', 'column_rect'), ('◯ ستون گرد', 'column_round')]]),
            'beams': ('📐 <b>تیرها</b>', [[('📐 تیر اصلی', 'beam_main'), ('📏 تیر فرعی', 'beam_secondary')]]),
            'ties': ('🔗 <b>شناژ و کلاف</b>', [[('🔗 شناژ', 'tie_beam'), ('⛓️ کلاف', 'tie_cowl')]]),
            'walls': ('🧱 <b>دیوارها</b>', [[('🏢 دیوار برشی', 'wall_shear'), ('🧱 دیوار حائل', 'wall_retaining')]]),
        }
        if data in section_routes:
            title, rows = section_routes[data]
            return await q.edit_message_text(title, parse_mode='HTML', reply_markup=section_kb(lang, rows))

        if data == 'roofs':
            rows = [
                [(ROOF_TYPES['eps']['name'][lang], 'roof_eps')],
                [(ROOF_TYPES['clay']['name'][lang], 'roof_clay')],
                [(ROOF_TYPES['waffle']['name'][lang], 'roof_waffle')],
                [(ROOF_TYPES['slab']['name'][lang], 'roof_slab')],
            ]
            return await q.edit_message_text(
                '🏠 <b>سیستم سقف</b>\n\nبرای هر سیستم، ورودی‌های اختصاصی استفاده می‌شود؛ ضریب تجربی مخفی وجود ندارد.',
                parse_mode='HTML', reply_markup=section_kb(lang, rows)
            )

        mapping = {
            'foundation_iso': 'iso', 'foundation_strip': 'strip', 'foundation_raft': 'raft',
            'column_rect': 'column_rect', 'column_round': 'column_round',
            'beam_main': 'beam', 'beam_secondary': 'beam',
            'tie_beam': 'tie', 'tie_cowl': 'tie',
            'wall_shear': 'wall', 'wall_retaining': 'wall',
        }
        if data in mapping:
            return await begin_wizard(update, context, mapping[data])

        if data.startswith('roof_'):
            rt = data[5:]
            if rt in ROOF_TYPES:
                return await begin_roof(update, context, rt)

        if data == 'stairs':
            return await begin_wizard(update, context, 'stair')

        if data == 'show_rebar':
            result = context.user_data.get('result') or {}
            return await q.edit_message_text(
                rebar_text(result.get('rebar_details', []), lang), parse_mode='HTML',
                reply_markup=kb([[(TEXT[lang]['show_cut'], 'show_cut'), (TEXT[lang]['result'], 'back_result')],
                                 [(TEXT[lang]['home'], 'home')]])
            )
        if data == 'show_cut':
            result = context.user_data.get('result') or {}
            return await q.edit_message_text(
                cut_text(result.get('rebar_details', []), lang), parse_mode='HTML',
                reply_markup=kb([[(TEXT[lang]['show_rebar'], 'show_rebar'), (TEXT[lang]['result'], 'back_result')],
                                 [(TEXT[lang]['home'], 'home')]])
            )
        if data == 'back_result':
            return await q.edit_message_text(
                summary_text(context.user_data.get('kind', ''), context.user_data.get('result', {}), lang),
                parse_mode='HTML', reply_markup=result_kb(lang)
            )
        if data == 'new_member':
            for k in ('kind', 'step_index', 'values', 'history', 'roof_type', 'roof_name',
                      'roof_step_index', 'roof_values', 'result', 'natural_mode', 'multi_mode'):
                context.user_data.pop(k, None)
            return await q.edit_message_text(TEXT[lang]['welcome'], parse_mode='HTML', reply_markup=main_menu(lang))
        if data == 'summary':
            return await q.edit_message_text(project_summary_text(context, lang), parse_mode='HTML', reply_markup=back_kb(lang))
        if data == 'settings':
            if not project_ready(context):
                return await q.edit_message_text(TEXT[lang]['standard'], parse_mode='HTML', reply_markup=standard_keyboard(lang))
            std = project_standard(context)
            return await q.edit_message_text(
                f"⚙️ <b>{TEXT[lang]['settings']}</b>\n\n📚 {escape(STANDARDS[std][lang])}\n"
                f"🧱 C{project_fc(context):g}\n🔩 {escape(project_grade(context))}\nfy={project_fy(context):g} MPa",
                parse_mode='HTML',
                reply_markup=kb([[(TEXT[lang]['standard_setting'], 'settings_standard')],
                                 [(TEXT[lang]['materials'], 'settings_materials')],
                                 [(TEXT[lang]['language'], 'language')],
                                 [(TEXT[lang]['home'], 'home')]])
            )
        if data == 'settings_standard':
            return await q.edit_message_text(TEXT[lang]['standard'], parse_mode='HTML', reply_markup=standard_keyboard(lang))
        if data == 'settings_materials':
            return await q.edit_message_text(TEXT[lang]['concrete'], reply_markup=concrete_keyboard(lang))

        if data == 'equiv':
            return await begin_equivalency(update, context)
        if data.startswith('equiv_current_'):
            d = int(data.rsplit('_', 1)[1])
            context.user_data.setdefault('equiv', {})['current_dia'] = d
            context.user_data['equiv_step'] = 2
            return await q.edit_message_text(
                f"3️⃣ {TEXT[lang]['replacement_dia']}",
                reply_markup=kb([[('Φ' + str(x), f'equiv_replace_{x}') for x in (8,10,12,14,16,18,20,22,25,28,32)],
                                 [(TEXT[lang]['home'], 'home')]])
            )
        if data.startswith('equiv_replace_'):
            return await show_equiv_result(update, context, int(data.rsplit('_', 1)[1]))

        if data == 'natural_input':
            context.user_data['natural_mode'] = True
            return await q.edit_message_text(
                f"✍️ <b>{TEXT[lang]['natural']}</b>\n\nمثال: <code>stirrups 8 spacing 20 length 7</code>",
                parse_mode='HTML', reply_markup=back_kb(lang)
            )
        if data == 'multi_column':
            context.user_data['multi_mode'] = 'input'
            return await q.edit_message_text(
                f"🏢 <b>{TEXT[lang]['multi_column']}</b>\n\nمثال: <code>۱۰ طبقه، ارتفاع هر طبقه ۳.۲، ۱۶ میلگرد ۲۰</code>",
                parse_mode='HTML', reply_markup=back_kb(lang)
            )
        if data == 'help':
            return await q.edit_message_text(
                f"ℹ️ <b>{TEXT[lang]['help']}</b>\n\nاین ابزار برای برآورد کمی بتن و میلگرد است. "
                f"Cut List بر مبنای شاخه ۱۲ متری گزارش می‌شود. خروجی جایگزین نقشه و محاسبات نهایی مهندس محاسب نیست. "
                f"استاندارد China بدون fy صریح پذیرفته نمی‌شود.",
                parse_mode='HTML', reply_markup=back_kb(lang)
            )

        logger.warning('Unknown callback_data=%r user=%s', data, getattr(update.effective_user, 'id', None))
        return await q.edit_message_text(
            f"⚠️ <b>دکمه ناشناخته</b>\n\n<code>{escape(data)}</code>\n\nمنوی اصلی:",
            parse_mode='HTML', reply_markup=main_menu(lang)
        )
    except Exception as exc:
        logger.exception('Callback failed: %r', data)
        try:
            await q.edit_message_text(TEXT[lang]['calc_error'].format(escape(str(exc))),
                                      parse_mode='HTML', reply_markup=main_menu(lang))
        except Exception:
            logger.exception('Could not send callback error message')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear(); context.user_data['lang']='fa'
    await update.message.reply_text(TEXT['fa']['language'],parse_mode='HTML',reply_markup=language_keyboard())


async def choose_language(update, context):
    q=update.callback_query; await q.answer(); lang=q.data.split('_',1)[1]; context.user_data.clear(); context.user_data['lang']=lang
    await q.edit_message_text(TEXT[lang]['standard'],parse_mode='HTML',reply_markup=standard_keyboard(lang))


async def receive_router(update, context):
    if context.user_data.get('awaiting_fy'):
        lang=context.user_data.get('lang','fa')
        try:
            fy=parse_number(update.message.text)
            if fy <= 0: raise ValueError
            context.user_data.update(fy=fy,rebar_grade=f'fy={fy:g} MPa',awaiting_fy=False,project_results=[])
            await update.message.reply_text(TEXT[lang]['project_ready']+f"\n\n📚 {escape(STANDARDS['china'][lang])}\n🧱 C{project_fc(context):g}\n🔩 fy={fy:g} MPa",parse_mode='HTML',reply_markup=main_menu(lang)); return
        except Exception:
            await update.message.reply_text(TEXT[lang]['invalid']); return
    if context.user_data.get('natural_mode'):
        lang=context.user_data.get('lang','fa')
        try:
            parsed=parse_natural_input(update.message.text)
            context.user_data['natural_mode']=False
            f=parsed.get('fields',{})
            if not f: raise ValueError('No structured fields detected.')
            msg='✍️ <b>Parsed input</b>\n\n<pre>'+escape(str(f))+'</pre>\n\n⚠️ Before using it in a calculation, verify the interpreted fields.'
            await update.message.reply_text(msg,parse_mode='HTML',reply_markup=back_kb(lang)); return
        except Exception as exc:
            await update.message.reply_text(TEXT[lang]['calc_error'].format(escape(str(exc))),parse_mode='HTML'); return
    if context.user_data.get('multi_mode')=='input':
        lang=context.user_data.get('lang','fa')
        try:
            f=parse_natural_input(update.message.text).get('fields',{})
            required=('floors','story_height_m','count','diameter_mm')
            if not all(k in f for k in required): raise ValueError('floors, story_height_m, count and diameter_mm are required.')
            if 'ld_m' in f:
                lap=iran_column_lap_rule(f['ld_m'],splice_class=f.get('splice_class','B'),special_moment_frame=True)
                plan=multistory_column_splice_schedule(int(f['floors']),f['story_height_m'],int(f['count']),int(f['diameter_mm']),lap,coupler=bool(f.get('coupler_requested')),special_moment_frame=True)
                context.user_data['multi_mode']=None
                rows='\n'.join(f"{r['connection_between_floors']}: {r['splice_start_from_lower_story_base_m']:.2f}-{r['splice_end_from_lower_story_base_m']:.2f} m" for r in plan['schedule'][:10])
                await update.message.reply_text(f"🏢 <b>برنامه وصله ستون</b>\n\nطبقات: {plan['floors']}\nمیلگرد: {plan['bar_count']}Φ{plan['diameter_mm']}\nوصله: {lap['lap_length_m']:.3f} m\n\n{rows}\n\n⚠️ کنترل نهایی بر اساس نقشه و سیستم سازه‌ای الزامی است.",parse_mode='HTML',reply_markup=back_kb(lang)); return
            plan=column_multistory_plan(int(f['floors']),f['story_height_m'],int(f['count']),int(f['diameter_mm']))
            context.user_data['multi_mode']=None
            await update.message.reply_text(f"🏢 <b>برنامه اولیه ستون چندطبقه</b>\n\nطبقات: {plan['floors']}\nارتفاع: {plan['story_height_m']:.2f} m\nمیلگرد: {plan['longitudinal_bars']}Φ{plan['diameter_mm']}\nاتصالات: {plan['connections']}",parse_mode='HTML',reply_markup=back_kb(lang)); return
        except Exception as exc:
            await update.message.reply_text(TEXT[lang]['calc_error'].format(escape(str(exc))),parse_mode='HTML'); return
    if context.user_data.get('roof_type') and context.user_data.get('roof_step_index') is not None:
        if await receive_roof(update,context): return
    if context.user_data.get('equiv_step') is not None:
        if await receive_equivalency(update,context): return
    await receive(update,context)


async def error_handler(update, context):
    logger.exception('Unhandled bot error',exc_info=context.error)


def main():
    if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN environment variable is not set')
    if not RENDER_EXTERNAL_URL: raise RuntimeError('RENDER_EXTERNAL_URL environment variable is not set')
    webhook_url=f'{RENDER_EXTERNAL_URL}/telegram'
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start',start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,receive_router))
    app.add_error_handler(error_handler)
    print('Concrete Structure Quantity Bot - professional build')
    print(f'Port: {PORT}')
    print(f'Webhook: {webhook_url}')
    app.run_webhook(listen='0.0.0.0',port=PORT,url_path='telegram',webhook_url=webhook_url,allowed_updates=Update.ALL_TYPES,drop_pending_updates=True)


if __name__=='__main__':
    main()
