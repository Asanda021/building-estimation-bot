# bot.py - Version 2.6
# -*- coding: utf-8 -*-

import os
import logging
from html import escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from calculations_v2_6 import (
    isolated_footing, strip_footing, raft_foundation,
    column_rectangular, column_round, beam, tie_beam,
    wall_concrete, stair_slab, roof_slab,
    joist_eps_roof_detail, joist_clay_roof_detail, waffle_roof_detail, solid_slab_roof_detail, material_waste,
    normalize_standard, project_settings,
    aggregate_project_results, equivalent_rebar_count,
    parse_natural_input, natural_stirrup_quantity, column_multistory_plan,
    verified_splice_length, iran_column_lap_rule, multistory_column_splice_schedule,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

STANDARDS = {
    "iran": "🇮🇷 مبحث ۹ ایران",
    "aci318": "🇺🇸 ACI 318",
    "eurocode2": "🇪🇺 Eurocode 2",
    "china": "🇨🇳 China / GB",
}
EDITIONS = {k: "نسخه پروژه / نیازمند انتخاب دقیق" for k in STANDARDS}
CONCRETE_OPTIONS = [25, 30, 35, 40]
REBAR_OPTIONS = {
    "iran": [("A2", 300), ("A3", 400), ("A4", 500)],
    "aci318": [("Grade 40", 280), ("Grade 60", 420)],
    "eurocode2": [("B400", 400), ("B500", 500)],
    "china": [],
}
ROOF_NAMES = {"eps": "تیرچه یونولیت", "clay": "تیرچه‌بلوک سفالی", "waffle": "وافل", "slab": "دال بتنی"}

TEXT = {
    "fa": {
        "welcome": "🏗️ <b>Structural Quantity Engine</b>\n\nاستاندارد، مصالح و سپس عضو سازه‌ای را انتخاب کنید.",
        "invalid": "❌ مقدار معتبر نیست. دوباره وارد کنید.", "back": "🔙 بازگشت", "home": "🏠 صفحه اصلی", "cancel": "❌ لغو",
        "standard": "📚 استاندارد", "concrete": "🧱 مقاومت بتن", "grade": "🔩 گرید میلگرد", "ready": "✅ پروژه آماده است.",
        "summary": "📊 خلاصه پروژه", "settings": "⚙️ تنظیمات", "help": "ℹ️ راهنما", "no_project": "هنوز پروژه‌ای تعریف نشده است.",
    },
    "en": {
        "welcome": "🏗️ <b>Structural Quantity Engine</b>\n\nSelect standard, materials, then a structural member.",
        "invalid": "❌ Invalid value. Try again.", "back": "🔙 Back", "home": "🏠 Main Menu", "cancel": "❌ Cancel",
        "standard": "📚 Standard", "concrete": "🧱 Concrete", "grade": "🔩 Rebar Grade", "ready": "✅ Project is ready.",
        "summary": "📊 Project Summary", "settings": "⚙️ Settings", "help": "ℹ️ Help", "no_project": "No project is configured yet.",
    },
}

STEPS = {
    "iso": [("count","تعداد پی","int"),("L","طول پی (m)","float"),("W","عرض پی (m)","float"),("T","ضخامت پی (m)","float"),("leanL","طول بتن مگر (m)","float"),("leanW","عرض بتن مگر (m)","float"),("leanT","ضخامت بتن مگر (m)","float"),("bd","قطر میلگرد پایین (mm)","int"),("bs","فاصله میلگرد پایین (mm)","int"),("td","قطر میلگرد بالا؛ 0 اگر ندارد","int"),("ts","فاصله میلگرد بالا؛ 0 اگر ندارد","int"),("cover","کاور (mm)","float"),("lap","درصد اورلپ","float"),("pl","طول پدستال (m)","float"),("pw","عرض پدستال (m)","float"),("ph","ارتفاع پدستال (m)","float")],
    "strip": [("count","تعداد نوار","int"),("L","طول نوار (m)","float"),("W","عرض پی (m)","float"),("T","ضخامت پی (m)","float"),("leanL","طول بتن مگر (m)","float"),("leanW","عرض بتن مگر (m)","float"),("leanT","ضخامت بتن مگر (m)","float"),("ld","قطر طولی پایین (mm)","int"),("lc","تعداد طولی پایین","int"),("td","قطر عرضی پایین (mm)","int"),("ts","فاصله عرضی پایین (mm)","int"),("tld","قطر طولی بالا؛ 0 اگر ندارد","int"),("tlc","تعداد طولی بالا؛ 0 اگر ندارد","int"),("ttd","قطر عرضی بالا؛ 0 اگر ندارد","int"),("tts","فاصله عرضی بالا؛ 0 اگر ندارد","int"),("cover","کاور (mm)","float"),("lap","درصد اورلپ","float")],
    "raft": [("L","طول رادیه (m)","float"),("W","عرض رادیه (m)","float"),("T","ضخامت رادیه (m)","float"),("leanL","طول بتن مگر (m)","float"),("leanW","عرض بتن مگر (m)","float"),("leanT","ضخامت بتن مگر (m)","float"),("bxd","قطر X پایین (mm)","int"),("bxs","فاصله X پایین (mm)","int"),("byd","قطر Y پایین (mm)","int"),("bys","فاصله Y پایین (mm)","int"),("txd","قطر X بالا؛ 0 اگر ندارد","int"),("txs","فاصله X بالا؛ 0 اگر ندارد","int"),("tyd","قطر Y بالا؛ 0 اگر ندارد","int"),("tys","فاصله Y بالا؛ 0 اگر ندارد","int"),("cover","کاور (mm)","float"),("lap","درصد اورلپ","float")],
    "column_rect": [("count","تعداد ستون","int"),("W","عرض ستون (m)","float"),("D","عمق ستون (m)","float"),("H","ارتفاع ستون (m)","float"),("ld","قطر میلگرد طولی (mm)","int"),("lc","تعداد میلگرد طولی هر ستون","int"),("sd","قطر خاموت (mm)","int"),("ss","فاصله خاموت (mm)","int"),("cover","کاور (mm)","float")],
    "column_round": [("count","تعداد ستون گرد","int"),("D","قطر ستون (m)","float"),("H","ارتفاع ستون (m)","float"),("ld","قطر میلگرد طولی (mm)","int"),("lc","تعداد میلگرد طولی هر ستون","int"),("sd","قطر خاموت (mm)","int"),("ss","فاصله خاموت (mm)","int"),("cover","کاور (mm)","float")],
    "beam": [("count","تعداد تیر","int"),("L","طول تیر (m)","float"),("W","عرض تیر (m)","float"),("H","ارتفاع تیر (m)","float"),("bd","قطر پایین (mm)","int"),("bc","تعداد پایین","int"),("td","قطر بالا (mm)","int"),("tc","تعداد بالا","int"),("sd","قطر خاموت (mm)","int"),("ss","فاصله خاموت (mm)","int"),("cover","کاور (mm)","float")],
    "tie": [("count","تعداد شناژ/کلاف","int"),("L","طول (m)","float"),("W","عرض (m)","float"),("H","ارتفاع (m)","float"),("ld","قطر طولی (mm)","int"),("lc","تعداد طولی","int"),("sd","قطر خاموت (mm)","int"),("ss","فاصله خاموت (mm)","int"),("cover","کاور (mm)","float")],
    "wall": [("L","طول دیوار (m)","float"),("H","ارتفاع دیوار (m)","float"),("T","ضخامت دیوار (m)","float"),("vd","قطر قائم (mm)","int"),("vs","فاصله قائم (mm)","int"),("hd","قطر افقی (mm)","int"),("hs","فاصله افقی (mm)","int"),("cover","کاور (mm)","float")],
    "stair": [("L","طول شیب/دال (m)","float"),("W","عرض راه‌پله (m)","float"),("T","ضخامت دال (m)","float"),("md","قطر اصلی (mm)","int"),("ms","فاصله اصلی (mm)","int"),("dd","قطر توزیعی (mm)","int"),("ds","فاصله توزیعی (mm)","int"),("steps","تعداد پله","int"),("riser","ارتفاع رایزر (m)","float"),("tread","کف پله (m)","float")],
    "roof": [("area","مساحت سقف (m²)","float"),("dia","قطر میلگرد (mm)","int"),("kgm2","مصرف میلگرد kg/m²؛ برای 0 وارد کن","float")],
}


def kb(rows): return InlineKeyboardMarkup([[InlineKeyboardButton(a, callback_data=b) for a,b in row] for row in rows])
def back_kb(lang, callback="home"): return kb([[(TEXT[lang]["back"],callback),(TEXT[lang]["home"],"home")]])
def step_kb(lang): return kb([[('⬅️ مرحله قبل','prev'),(TEXT[lang]['cancel'],'cancel')],[(TEXT[lang]['home'],'home')]])
def result_kb(lang): return kb([[('🔩 میلگرد','show_rebar'),('✂️ Cut List','show_cut')],[('➕ عضو جدید','new_member')],[('📊 خلاصه پروژه','summary')],[(TEXT[lang]['home'],'home')]])
def review_kb(lang): return kb([[('✅ محاسبه','confirm_calc'),('✏️ ویرایش آخر','edit_last')],[('❌ لغو','cancel'),(TEXT[lang]['home'],'home')]])
def section_kb(lang, items, parent="home"):
    return kb([[a,b] for a,b in items]+[[(TEXT[lang]['back'],parent)]])

def prompt_text(lang,label,i,total):
    if lang == 'fa': return f"📐 <b>{escape(label)}</b>\n\nانتخاب کنید یا در صورت نیاز مقدار سفارشی را وارد کنید:\n\n━━━━━━━━━━━━━━\n📍 مرحله <b>{i}</b> از <b>{total}</b>"
    return f"📐 <b>{escape(label)}</b>\n\nEnter value:\n\n━━━━━━━━━━━━━━\n📍 Step <b>{i}</b> of <b>{total}</b>"


def project_ready(c): return all(c.get(k) is not None for k in ('standard','fc','grade','fy'))
def project_header(c):
    std=STANDARDS.get(c.get('standard'),'-'); return f"استاندارد: {std}\nویرایش: {c.get('edition','-')}\nبتن: C{c.get('fc','-')} MPa\nمیلگرد: {c.get('grade','-')} / fy={c.get('fy','-')} MPa"



LANG_META = {
    'fa': {'name':'فارسی','flag':'🇮🇷'}, 'en': {'name':'English','flag':'🇬🇧'},
    'ar': {'name':'العربية','flag':'🇸🇦'}, 'zh': {'name':'中文','flag':'🇨🇳'},
}
UI = {
 'fa': {'title':'ماشین حساب میلگرد و بتن','foundation':'فونداسیون','columns':'ستون‌ها','beams':'تیرها','roofs':'سقف‌ها','stairs':'راه‌پله','ties':'شناژ و کلاف','walls':'دیوارها','quick':'محاسبه سریع','summary':'خلاصه پروژه','settings':'تنظیمات','equiv':'معادل‌سازی میلگرد','help':'راهنما','natural':'✍️ ورود آزاد','multi':'🏢 ستون چندطبقه','lang':'🌐 زبان','cut':'فهرست برش','schedule':'جدول میلگرد','back':'بازگشت','home':'صفحه اصلی'},
 'en': {'title':'Rebar & Concrete Calculator','foundation':'Foundations','columns':'Columns','beams':'Beams','roofs':'Roofs','stairs':'Stairs','ties':'Tie Beams','walls':'Walls','quick':'Quick Calculation','summary':'Project Summary','settings':'Settings','equiv':'Rebar Equivalency','help':'Help','natural':'✍️ Natural Input','multi':'🏢 Multi-Story Column','lang':'🌐 Language','cut':'Cut List','schedule':'Rebar Schedule','back':'Back','home':'Home'},
 'ar': {'title':'حاسبة حديد التسليح والخرسانة','foundation':'الأساسات','columns':'الأعمدة','beams':'الكمرات','roofs':'الأسقف','stairs':'السلالم','ties':'الميدات والروابط','walls':'الجدران','quick':'حساب سريع','summary':'ملخص المشروع','settings':'الإعدادات','equiv':'معادلة أقطار التسليح','help':'المساعدة','natural':'✍️ إدخال حر','multi':'🏢 عمود متعدد الطوابق','lang':'🌐 اللغة','cut':'جدول القص','schedule':'جدول التسليح','back':'رجوع','home':'الرئيسية'},
 'zh': {'title':'钢筋与混凝土计算器','foundation':'基础','columns':'柱','beams':'梁','roofs':'楼板与屋面','stairs':'楼梯','ties':'系梁','walls':'墙','quick':'快速计算','summary':'项目汇总','settings':'设置','equiv':'钢筋换算','help':'帮助','natural':'✍️ 自然输入','multi':'🏢 多层柱','lang':'🌐 语言','cut':'下料表','schedule':'钢筋表','back':'返回','home':'主页'},
}

def current_lang(context): return context.user_data.get('lang','fa') if context else 'fa'

def language_menu():
    return kb([[(f"{v['flag']} {v['name']}",f"lang_{k}") for k,v in LANG_META.items()]])

def natural_menu(lang):
    u=UI[lang]
    return kb([[('🧮 '+u['quick'],'quick_calc'),('🏢 '+u['multi'],'multi_column')],[(u['back'],'home')]])

def professional_column_menu(lang):
    return kb([[('🔗 '+('وصله و اورلپ' if lang=='fa' else 'Lap / Splice'),'column_splice'),('🔩 '+('کوپلر' if lang=='fa' else 'Couplers'),'column_coupler')],[('📐 '+('محل وصله' if lang=='fa' else 'Splice Location'),'column_location')],[('✂️ '+UI[lang]['cut'],'show_column_cut'),(UI[lang]['back'],'home')]])

def roof_menu(lang):
    u=UI.get(lang,UI["fa"])
    if lang == "fa":
        return kb([[('🟦 تیرچه یونولیت','roof_eps'),('🟫 تیرچه‌بلوک سفالی','roof_clay')],
                   [('🟪 وافل','roof_waffle'),('🟩 دال بتنی','roof_slab')],
                   [('⬅️ '+u['back'],'home')]])
    return kb([[('🟦 EPS Joist-Block','roof_eps'),('🟫 Clay Joist-Block','roof_clay')],
               [('🟪 Waffle','roof_waffle'),('🟩 Solid Slab','roof_slab')],
               [(u['back'],'home')]])

def roof_system_note(lang, system):
    notes={
      'eps':'محاسبات بر اساس ابعاد واقعی بلوک، فاصله تیرچه و اطلاعات اجرایی واردشده انجام می‌شود؛ ضریب تخمینی مخفی وجود ندارد.',
      'clay':'محاسبات بر اساس ابعاد واقعی بلوک سفالی، فاصله تیرچه و اطلاعات اجرایی واردشده انجام می‌شود؛ ضریب تخمینی مخفی وجود ندارد.',
      'waffle':'تعداد واحدهای وافل از ابعاد واقعی قالب/مدول یا تعداد صریح واردشده محاسبه می‌شود؛ ضریب تخمینی مخفی وجود ندارد.',
      'slab':'حجم و میلگرد دال بر اساس هندسه و مشخصات واقعی پروژه محاسبه می‌شود.'
    }
    return notes.get(system,'')

def main_menu(lang):
    u=UI.get(lang,UI['fa'])
    if lang=='fa':
        return kb([[('🧱 '+u['foundation'],'foundation'),('🏛️ '+u['columns'],'columns')],[('📐 '+u['beams'],'beams'),('🏠 '+u['roofs'],'roofs')],[('🪜 '+u['stairs'],'stairs'),('🔗 '+u['ties'],'ties')],[('🧱 '+u['walls'],'walls')],[('✍️ '+u['natural'],'natural_input'),('⚡ '+u['quick'],'quick_calc')],[('🏢 '+u['multi'],'multi_column'),('📊 '+u['summary'],'summary')],[('⚙️ '+u['settings'],'settings'),('🌐 '+u['lang'],'language')],[('🔁 '+u['equiv'],'equiv'),('ℹ️ '+u['help'],'help')]])
    return kb([[('🧱 '+u['foundation'],'foundation'),('🏛️ '+u['columns'],'columns')],[('📐 '+u['beams'],'beams'),('🏠 '+u['roofs'],'roofs')],[('🪜 '+u['stairs'],'stairs'),('🔗 '+u['ties'],'ties')],[('🧱 '+u['walls'],'walls')],[('✍️ '+u['natural'],'natural_input'),('⚡ '+u['quick'],'quick_calc')],[('🏢 '+u['multi'],'multi_column'),('📊 '+u['summary'],'summary')],[('⚙️ '+u['settings'],'settings'),('🌐 '+u['lang'],'language')],[('🔁 '+u['equiv'],'equiv'),('ℹ️ '+u['help'],'help')]])


def summary_text(kind,result,lang):
    names={'iso':'⬛ پی منفرد','strip':'▬ پی نواری','raft':'▰ رادیه','column_rect':'▯ ستون مستطیلی','column_round':'◯ ستون گرد','beam':'📐 تیر','tie':'🔗 شناژ / کلاف','wall':'🧱 دیوار','stair':'🪜 راه‌پله','roof':'🏠 سقف'}
    return (f"🏗️ <b>نتیجه محاسبه</b>\n\n<b>{names.get(kind,kind)}</b>\n\n<pre>"
            f"بتن              {float(result.get('total_concrete_m3',0)):.2f} m³\n"
            f"میلگرد            {float(result.get('total_rebar_kg',0)):.1f} kg\n"
            f"طول میلگرد        {float(result.get('total_rebar_length_m',0)):.2f} m\n"
            f"شاخه ۱۲ متری      {int(result.get('total_stock_bars_12m',0))}\n"
            f"پرت میلگرد        {float(result.get('total_rebar_waste_m',0)):.2f} m\n"
            f"درصد پرت          {float(result.get('rebar_waste_percent',0)):.2f}%"
            f"</pre>")


def rebar_text(details):
    if not details: return '🔩 <b>میلگرد</b>\n\nموردی ثبت نشده.'
    lines=['🔩 <b>جدول میلگرد</b>','','<pre>','قطر   قطعه   طول(m)   وزن(kg)   شاخه','────────────────────────────────']
    for x in details: lines.append(f"Φ{x['diameter_mm']:<4} {x['piece_count']:<6} {x['length_m']:<9.2f} {x['weight_kg']:<9.1f} {x['bars_12m']}")
    lines.append('</pre>'); return '\n'.join(lines)


def cut_text(details):
    if not details: return '✂️ <b>فهرست برش</b>\n\nموردی ثبت نشده.'
    out=['✂️ <b>فهرست برش</b>','']
    for x in details:
        out.append(f"<b>Φ{x['diameter_mm']}</b> — {x['bars_12m']} شاخه ۱۲ متری")
        out.append('<pre>')
        for i,p in enumerate(x.get('cut_plan',[]),1):
            if i>15: out.append(f"... {len(x['cut_plan'])-15} شاخه دیگر"); break
            pieces=' + '.join(f"{v:.2f}" for v in p.get('pieces',[])); out.append(f"{i:02d}) {pieces} = {p['used_m']:.2f} | پرت {p['waste_m']:.2f}")
        out.append('</pre>')
    return '\n'.join(out)



def quick_menu(lang):
    if lang == 'fa':
        return kb([[('🧱 حجم بتن','quick_concrete'),('⚖️ وزن میلگرد','quick_rebar_weight')],[('📏 طول میلگرد','quick_rebar_length'),('📦 شاخه ۱۲ متری','quick_stock')],[('🔩 میلگرد از تعداد/فاصله','quick_mesh')],[(TEXT[lang]['back'],'home')]])
    return kb([[('🧱 Concrete Volume','quick_concrete'),('⚖️ Rebar Weight','quick_rebar_weight')],[('📏 Rebar Length','quick_rebar_length'),('📦 12m Bars','quick_stock')],[('🔩 Bars by Spacing','quick_mesh')],[(TEXT[lang]['back'],'home')]])

QUICK_STEPS = {
    'quick_concrete': [('L','طول (m)','float'),('W','عرض (m)','float'),('T','ضخامت (m)','float')],
    'quick_rebar_weight': [('L','طول کل میلگرد (m)','float'),('dia','قطر میلگرد (mm)','int')],
    'quick_rebar_length': [('weight','وزن میلگرد (kg)','float'),('dia','قطر میلگرد (mm)','int')],
    'quick_stock': [('L','طول کل میلگرد (m)','float')],
    'quick_mesh': [('L','طول مسیر (m)','float'),('W','عرض مسیر (m)','float'),('spacing','فاصله میلگرد (mm)','float'),('dia','قطر میلگرد (mm)','int')],
}


def quick_result_text(kind,v):
    if kind == 'quick_concrete':
        vol=v['L']*v['W']*v['T']
        return f"⚡ <b>محاسبه سریع بتن</b>\n\nحجم بتن: <b>{vol:.3f} m³</b>"
    if kind == 'quick_rebar_weight':
        from calculations_v2_6 import rebar_weight
        w=rebar_weight(v['L'],int(v['dia']))
        return f"⚡ <b>وزن میلگرد</b>\n\nطول: {v['L']:.2f} m\nقطر: Φ{int(v['dia'])}\n\nوزن: <b>{w:.2f} kg</b>"
    if kind == 'quick_rebar_length':
        from calculations_v2_6 import REBAR_WEIGHT
        d=int(v['dia']); kgm=REBAR_WEIGHT.get(d,d*d/162.0); L=v['weight']/kgm
        return f"⚡ <b>طول میلگرد</b>\n\nوزن: {v['weight']:.2f} kg\nقطر: Φ{d}\n\nطول تقریبی: <b>{L:.2f} m</b>"
    if kind == 'quick_stock':
        import math
        bars=math.ceil(v['L']/12.0) if v['L']>0 else 0
        waste=bars*12.0-v['L']
        pct=waste/(bars*12.0)*100 if bars else 0
        return f"⚡ <b>شاخه ۱۲ متری</b>\n\nطول کل: {v['L']:.2f} m\n\nتعداد شاخه: <b>{bars}</b>\nپرت خام: {waste:.2f} m ({pct:.2f}%)"
    if kind == 'quick_mesh':
        import math
        count=math.floor(v['W']/(v['spacing']/1000.0))+1
        total=count*v['L']
        from calculations_v2_6 import rebar_weight
        weight=rebar_weight(total,int(v['dia']))
        bars=math.ceil(total/12.0)
        return f"⚡ <b>میلگرد از تعداد/فاصله</b>\n\nتعداد میلگرد: <b>{count}</b>\nطول کل: <b>{total:.2f} m</b>\nوزن تقریبی: <b>{weight:.2f} kg</b>\nشاخه ۱۲ متری: <b>{bars}</b>"
    return '❌ محاسبه ناشناخته.'


def project_summary(c):
    data=aggregate_project_results([x['result'] for x in c.get('project_results',[]) if isinstance(x,dict) and 'result' in x])
    lines=['📊 <b>خلاصه پروژه</b>','',f"<pre>{project_header(c)}\n\nاعضا              {data['member_count']}\nبتن کل            {data['total_concrete_m3']:.2f} m³\nمیلگرد کل         {data['total_rebar_kg']:.1f} kg\nطول میلگرد        {data['total_rebar_length_m']:.2f} m\nشاخه ۱۲ متری      {data['total_stock_bars_12m']}\nپرت                {data['total_rebar_waste_m']:.2f} m\nدرصد پرت           {data['rebar_waste_percent']:.2f}%\n\nBreakdown قطر:"]
    for dia,x in sorted(data['by_diameter'].items(),key=lambda z:int(z[0])): lines.append(f"Φ{dia:<3} {x['weight_kg']:>9.1f} kg | {x['length_m']:>9.2f} m | {x['bars_12m']:>4} شاخه")
    lines.append('</pre>'); return '\n'.join(lines)


def review_text(kind, values, lang):
    names={'iso':'پی منفرد','strip':'پی نواری','raft':'رادیه','column_rect':'ستون مستطیلی','column_round':'ستون گرد','beam':'تیر','tie':'شناژ / کلاف','wall':'دیوار','stair':'راه‌پله','roof':'سقف'}
    lines=['🔎 <b>بازبینی اطلاعات</b>','',f'🏗️ <b>{names.get(kind,kind)}</b>','<pre>']
    for key,label,typ in STEPS[kind]:
        if key in values:
            val=values[key]
            lines.append(f'{label}: {val}')
    lines += ['</pre>','', 'اگر اطلاعات درست است «محاسبه» را بزن؛ در غیر این صورت مرحله آخر را ویرایش کن.']
    return '\n'.join(lines)


def calculate(kind,v):
    if kind=='iso': return isolated_footing(int(v['count']),v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['bd']),v['bs'],int(v['td']) if v['td']>0 else None,v['ts'] if v['td']>0 and v['ts']>0 else None,v['cover'],v['lap'],v['pl'],v['pw'],v['ph'])
    if kind=='strip': return strip_footing(int(v['count']),v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['ld']),int(v['lc']),int(v['td']),v['ts'],int(v['tld']) if v['tld']>0 else None,int(v['tlc']) if v['tlc']>0 else None,int(v['ttd']) if v['ttd']>0 else None,v['tts'] if v['ttd']>0 and v['tts']>0 else None,v['cover'],v['lap'])
    if kind=='raft': return raft_foundation(v['L'],v['W'],v['T'],v['leanL'],v['leanW'],v['leanT'],int(v['bxd']),v['bxs'],int(v['byd']),v['bys'],int(v['txd']) if v['txd']>0 else None,v['txs'] if v['txd']>0 and v['txs']>0 else None,int(v['tyd']) if v['tyd']>0 else None,v['tys'] if v['tyd']>0 and v['tys']>0 else None,v['cover'],v['lap'])
    if kind=='column_rect': return column_rectangular(int(v['count']),v['W'],v['D'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],v['cover'])
    if kind=='column_round': return column_round(int(v['count']),v['D'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],v['cover'])
    if kind=='beam': return beam(int(v['count']),v['L'],v['W'],v['H'],int(v['bd']),int(v['bc']),int(v['td']),int(v['tc']),int(v['sd']),v['ss'],v['cover'])
    if kind=='tie': return tie_beam(int(v['count']),v['L'],v['W'],v['H'],int(v['ld']),int(v['lc']),int(v['sd']),v['ss'],v['cover'])
    if kind=='wall': return wall_concrete(v['L'],v['H'],v['T'],int(v['vd']),v['vs'],int(v['hd']),v['hs'],v['cover'])
    if kind=='stair': return stair_slab(v['L'],v['W'],v['T'],int(v['md']),v['ms'],int(v['dd']),v['ds'],int(v['steps']),v['riser'],v['tread'])
    if kind=='roof':
        rt=v.get('roof_system')
        if rt=='eps': return joist_eps_roof_detail(span_m=v['span'],width_m=v['width'],joist_spacing_mm=v['spacing'],eps_length_m=v['epsL'],eps_width_m=v['epsW'],eps_height_m=v['epsH'],joist_count=v.get('joist_count'),otka_count=v.get('otka_count'),otka_dia_mm=v.get('otka_dia'),otka_length_m=v.get('otka_len'),june_count=v.get('june_count'),june_top_dia_mm=v.get('june_top_dia'),june_bottom_dia_mm=v.get('june_bottom_dia'),june_pin_dia_mm=v.get('june_pin_dia'),june_pin_count=v.get('june_pin_count'),concrete_topping_thickness_m=v.get('topping'),block_count=v.get('block_count'))
        if rt=='clay': return joist_clay_roof_detail(span_m=v['span'],width_m=v['width'],joist_spacing_mm=v['spacing'],clay_length_m=v['clayL'],clay_width_m=v['clayW'],clay_height_m=v['clayH'],joist_count=v.get('joist_count'),otka_count=v.get('otka_count'),otka_dia_mm=v.get('otka_dia'),otka_length_m=v.get('otka_len'),june_count=v.get('june_count'),june_top_dia_mm=v.get('june_top_dia'),june_bottom_dia_mm=v.get('june_bottom_dia'),june_pin_dia_mm=v.get('june_pin_dia'),june_pin_count=v.get('june_pin_count'),concrete_topping_thickness_m=v.get('topping'),block_count=v.get('block_count'))
        if rt=='waffle': return waffle_roof_detail(length_m=v['span'],width_m=v['width'],module_length_m=v['moduleL'],module_width_m=v['moduleW'],module_count=v.get('module_count'),concrete_thickness_m=v.get('T'))
        return solid_slab_roof_detail(length_m=v['L'],width_m=v['W'],thickness_m=v['T'],main_dia_mm=int(v['md']),main_spacing_mm=float(v['ms']),dist_dia_mm=int(v['dd']),dist_spacing_mm=float(v['ds']))
    raise ValueError(f'Unknown calculation type: {kind}')


async def start_project_setup(update,context):
    context.user_data['project_results']=[]
    await update.message.reply_text('📚 <b>انتخاب استاندارد</b>',parse_mode='HTML',reply_markup=kb([[(v,k) for k,v in STANDARDS.items()]]))

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    context.user_data.clear(); context.user_data['lang']='fa'; await start_project_setup(update,context)

async def begin_wizard(update,context,kind):
    lang=context.user_data.get('lang','fa')
    if not project_ready(context.user_data): return await update.callback_query.edit_message_text('⚠️ ابتدا استاندارد و مصالح پروژه را تنظیم کن.',reply_markup=back_kb(lang))
    context.user_data.update(kind=kind,step_index=0,values={},history=[])
    f=STEPS[kind]; await update.callback_query.edit_message_text(prompt_text(lang,f[0][1],1,len(f)),parse_mode='HTML',reply_markup=step_kb(lang))

async def receive(update,context):
    lang=context.user_data.get('lang','fa'); kind=context.user_data.get('kind'); idx=context.user_data.get('step_index')
    if kind is None or idx is None: return await update.message.reply_text('ابتدا پروژه را تنظیم کن.')
    key,label,typ=STEPS[kind][idx]; raw=update.message.text.strip().replace(',','.').replace('٫','.')
    try:
        value=float(raw); value=int(value) if typ=='int' and value.is_integer() else value
        if value<0 or (typ=='int' and not isinstance(value,int)): raise ValueError
    except Exception: return await update.message.reply_text(TEXT[lang]['invalid'],reply_markup=step_kb(lang))
    context.user_data['values'][key]=value; context.user_data['history'].append(idx); nxt=idx+1
    if nxt<len(STEPS[kind]): context.user_data['step_index']=nxt; f=STEPS[kind][nxt]; return await update.message.reply_text(prompt_text(lang,f[1],nxt+1,len(STEPS[kind])),parse_mode='HTML',reply_markup=step_kb(lang))
    context.user_data['step_index']=None
    return await update.message.reply_text(review_text(kind,context.user_data['values'],lang),parse_mode='HTML',reply_markup=review_kb(lang))

async def buttons(update,context):
    q=update.callback_query; await q.answer(); data=q.data; lang=context.user_data.get('lang','fa')
    if data.startswith('std_'):
        std=data[4:]; context.user_data['standard']=std; context.user_data['edition']=EDITIONS[std]; context.user_data['project_results']=[]
        return await q.edit_message_text('🧱 <b>مقاومت بتن</b>',parse_mode='HTML',reply_markup=kb([[(f'C{x} MPa',f'fc_{x}') for x in CONCRETE_OPTIONS]]))
    if data.startswith('fc_'):
        context.user_data['fc']=int(data[3:]); context.user_data['project_results']=[]; std=context.user_data['standard']; opts=REBAR_OPTIONS[std]
        if not opts: return await q.edit_message_text('🔩 <b>China / GB</b>\n\nبرای این استاندارد fy را عددی وارد کن (MPa).',parse_mode='HTML',reply_markup=kb([[('✏️ ورود fy','china_fy')],[('🏠 صفحه اصلی','home')]]))
        return await q.edit_message_text('🔩 <b>گرید میلگرد</b>',parse_mode='HTML',reply_markup=kb([[(f'{g} ({fy} MPa)',f'grade_{g}') for g,fy in opts]]))
    if data.startswith('grade_'):
        grade=data[6:]; std=context.user_data['standard']; fy=next(f for g,f in REBAR_OPTIONS[std] if g==grade); context.user_data.update(grade=grade,fy=fy); context.user_data['project_results']=[]; return await q.edit_message_text(TEXT[lang]['welcome']+'\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=main_menu(lang))
    if data=='china_fy': context.user_data['await_fy']=True; return await q.edit_message_text('عدد fy را بر حسب MPa وارد کن:',reply_markup=back_kb(lang))
    if data.startswith('roofv_'):
        _,field,val=data.split('_',2)
        v=float(val) if field in ('span','width','spacing') else val
        context.user_data.setdefault('values',{})[field]=v
        nxt={'span':'width','width':'spacing','spacing':'block','block':'done'}.get(field,'done')
        rt=context.user_data.get('roof_system')
        if nxt=='done':
            # For block dimensions, request the exact block size then all required system inputs.
            if rt in ('eps','clay'):
                context.user_data['step_index']=0
                label='ابعاد بلوک: طول×عرض×ارتفاع (m) را دقیق وارد کنید.'
                return await q.edit_message_text(label,reply_markup=back_kb(lang,'roofs'))
            return await q.edit_message_text('اطلاعات پایه ثبت شد. جزئیات سیستم وافل را وارد کنید.',reply_markup=back_kb(lang,'roofs'))
        labels={'width':'عرض سقف (m)','spacing':'فاصله محور تیرچه (mm)','block':'ابعاد بلوک'}
        return await q.edit_message_text(f'📐 <b>{labels[nxt]}</b>\n\n{roof_system_note(lang,rt)}',parse_mode='HTML',reply_markup=roof_quick_buttons(lang,rt,nxt))

    if data=='quick_calc':
        return await q.edit_message_text('⚡ <b>محاسبه سریع</b>\n\nنوع محاسبه را انتخاب کن:',parse_mode='HTML',reply_markup=quick_menu(lang))
    if data=='language':
        return await q.edit_message_text('🌐 <b>انتخاب زبان / Language / اللغة / 语言</b>',parse_mode='HTML',reply_markup=language_menu())
    if data.startswith('lang_'):
        new_lang=data[5:]
        if new_lang not in LANG_META: new_lang='fa'
        context.user_data['lang']=new_lang
        u=UI[new_lang]
        return await q.edit_message_text(f"{LANG_META[new_lang]['flag']} <b>{escape(u['title'])}</b>\n\n{escape(u['home'])}",parse_mode='HTML',reply_markup=main_menu(new_lang))
    if data=='natural_input':
        context.user_data['natural_mode']=True
        msg={'fa':'✍️ <b>ورودی آزاد</b>\nمثلاً:\n<code>خاموت ۸ هر ۲۰ طول ۷</code>\n\nیا همه اطلاعات را در چند خط بنویس.','en':'✍️ <b>Natural Input</b>\nExample:\n<code>stirrups 8 spacing 20 length 7</code>','ar':'✍️ <b>إدخال حر</b>\nمثال:\n<code>كانة 8 كل 20 طول 7</code>','zh':'✍️ <b>自然输入</b>\n例如：<code>箍筋 8 间距 20 长度 7</code>'}[lang]
        return await q.edit_message_text(msg,parse_mode='HTML',reply_markup=back_kb(lang))
    if data=='multi_column':
        context.user_data['multi_mode']='input'
        msg={'fa':'🏢 <b>ستون چندطبقه</b>\nاطلاعات را آزاد وارد کن؛ مثلاً:\n<code>۱۰ طبقه، ارتفاع هر طبقه ۳.۲، ۱۶ میلگرد ۲۰</code>','en':'🏢 <b>Multi-Story Column</b>\nEnter: floors, story height, longitudinal bar count and diameter.','ar':'🏢 <b>عمود متعدد الطوابق</b>\nأدخل عدد الطوابق وارتفاعها وعدد وأقطار القضبان الطولية.','zh':'🏢 <b>多层柱</b>\n输入层数、层高、纵筋数量和直径。'}[lang]
        return await q.edit_message_text(msg,parse_mode='HTML',reply_markup=professional_column_menu(lang))
    if data.startswith('quick_') and data in QUICK_STEPS:
        context.user_data['quick_kind']=data; context.user_data['quick_step']=0; context.user_data['quick_values']={}
        f=QUICK_STEPS[data][0]
        return await q.edit_message_text(prompt_text(lang,f[1],1,len(QUICK_STEPS[data])),parse_mode='HTML',reply_markup=step_kb(lang))
    if data=='home':
        context.user_data.pop('kind',None); context.user_data.pop('values',None); context.user_data.pop('result',None); return await q.edit_message_text(TEXT[lang]['welcome']+'\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=main_menu(lang))
    if data=='cancel':
        for k in ('quick_kind','quick_step','quick_values','kind','values','result','step_index'): context.user_data.pop(k,None)
        return await q.edit_message_text(TEXT[lang]['welcome']+'\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=main_menu(lang))
    if data=='prev':
        kind=context.user_data.get('kind'); idx=context.user_data.get('step_index');
        if not kind or idx in (None,0): return await q.edit_message_text(TEXT[lang]['welcome'],parse_mode='HTML',reply_markup=main_menu(lang))
        idx-=1; context.user_data['step_index']=idx; context.user_data['values'].pop(STEPS[kind][idx][0],None); return await q.edit_message_text(prompt_text(lang,STEPS[kind][idx][1],idx+1,len(STEPS[kind])),parse_mode='HTML',reply_markup=step_kb(lang))
    if data=='foundation': return await q.edit_message_text('🧱 <b>فونداسیون</b>',parse_mode='HTML',reply_markup=section_kb(lang,[('⬛ پی منفرد','foundation_iso'),('▬ پی نواری','foundation_strip'),('▰ رادیه','foundation_raft')]))
    if data=='columns': return await q.edit_message_text('🏛️ <b>ستون‌ها</b>',parse_mode='HTML',reply_markup=section_kb(lang,[('▯ مستطیلی','column_rect'),('◯ گرد','column_round')]))
    if data=='beams': return await q.edit_message_text('📐 <b>تیرها</b>',parse_mode='HTML',reply_markup=section_kb(lang,[('📐 تیر اصلی','beam_main'),('📏 تیر فرعی','beam_secondary')]))
    if data=='ties': return await q.edit_message_text('🔗 <b>شناژ و کلاف</b>',parse_mode='HTML',reply_markup=section_kb(lang,[('🔗 شناژ','tie_beam'),('⛓️ کلاف','tie_cowl')]))
    if data=='walls': return await q.edit_message_text('🧱 <b>دیوارها</b>',parse_mode='HTML',reply_markup=section_kb(lang,[('🏢 دیوار برشی','wall_shear'),('🧱 دیوار حائل','wall_retaining')]))
    if data=='stairs': return await begin_wizard(update,context,'stair')
    if data=='roofs':
        return await q.edit_message_text('🏠 <b>سیستم سقف را انتخاب کنید</b>\n\nهر سیستم، اجزای مخصوص خودش را دارد.',parse_mode='HTML',reply_markup=roof_menu(lang))
    mapping={'foundation_iso':'iso','foundation_strip':'strip','foundation_raft':'raft','column_rect':'column_rect','column_round':'column_round','beam_main':'beam','beam_secondary':'beam','tie_beam':'tie','tie_cowl':'tie','wall_shear':'wall','wall_retaining':'wall'}
    if data in mapping: return await begin_wizard(update,context,mapping[data])
    if data.startswith('roof_'):
        if not project_ready(context.user_data): return await q.edit_message_text('⚠️ ابتدا استاندارد و مصالح پروژه را تنظیم کن.',reply_markup=back_kb(lang))
        rt=data[5:]
        context.user_data.update(kind='roof',roof_system=rt,step_index=0,values={},history=[],roof_name=ROOF_NAMES[rt],roof_stage='span')
        return await roof_stage_prompt(q,lang,rt,'span')
    if data.startswith('roofv_'):
        _,field,val=data.split('_',2)
        vals=context.user_data.setdefault('values',{})
        if field in ('span','width','spacing'): vals[field]=float(val)
        elif field in ('june_count','otka_count','june_pin_count'): vals[field]=int(val)
        else: vals[field]=val
        rt=context.user_data.get('roof_system')
        nxt=next_roof_stage(rt,field)
        if nxt=='done':
            return await roof_finish_review(q,context,lang)
        return await roof_stage_prompt(q,lang,rt,nxt)
    if data=='roof_custom':
        context.user_data['roof_custom']=True
        rt=context.user_data.get('roof_system'); stage=context.user_data.get('roof_stage','span')
        return await q.edit_message_text(f'✏️ <b>{roof_stage_label(rt,stage)}</b>\n\nمقدار دقیق را وارد کنید:',parse_mode='HTML',reply_markup=back_kb(lang,'roofs'))
    if data=='confirm_calc':
        kind=context.user_data.get('kind'); vals=context.user_data.get('values',{})
        try:
            result=calculate(kind,vals); context.user_data['result']=result
            c=context.user_data; results=c.setdefault('project_results',[])
            member_no=len(results)+1
            results.append({'kind':kind,'member_no':member_no,'result':result,'values':dict(vals)})
            return await q.edit_message_text(f'🏗️ <b>عضو شماره {member_no}</b>\n\n'+summary_text(kind,result,lang),parse_mode='HTML',reply_markup=result_kb(lang))
        except Exception:
            logger.exception('Calculation failed')
            return await q.edit_message_text('❌ محاسبه انجام نشد. ارتباط بین ورودی‌ها را بررسی کن.',reply_markup=review_kb(lang))
    if data=='edit_last':
        kind=context.user_data.get('kind'); vals=context.user_data.get('values',{})
        if not kind: return await q.edit_message_text(TEXT[lang]['welcome'],parse_mode='HTML',reply_markup=main_menu(lang))
        idx=max(0,len([k for k,_,_ in STEPS[kind] if k in vals])-1)
        context.user_data['step_index']=idx
        key=STEPS[kind][idx][0]; vals.pop(key,None)
        f=STEPS[kind][idx]
        return await q.edit_message_text('✏️ <b>ویرایش مرحله آخر</b>\n\n'+prompt_text(lang,f[1],idx+1,len(STEPS[kind])),parse_mode='HTML',reply_markup=step_kb(lang))
    if data=='show_rebar': return await q.edit_message_text(rebar_text(context.user_data.get('result',{}).get('rebar_details',[])),parse_mode='HTML',reply_markup=back_kb(lang,'back_result'))
    if data=='show_cut': return await q.edit_message_text(cut_text(context.user_data.get('result',{}).get('rebar_details',[])),parse_mode='HTML',reply_markup=back_kb(lang,'back_result'))
    if data=='back_result': return await q.edit_message_text(summary_text(context.user_data.get('kind',''),context.user_data.get('result',{}),lang),parse_mode='HTML',reply_markup=result_kb(lang))
    if data=='new_member':
        for k in ('kind','values','result','step_index','history','roof_name'): context.user_data.pop(k,None)
        return await q.edit_message_text(TEXT[lang]['welcome']+'\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=main_menu(lang))
    if data=='summary': return await q.edit_message_text(project_summary(context.user_data),parse_mode='HTML',reply_markup=back_kb(lang))
    if data=='settings': return await q.edit_message_text('⚙️ <b>تنظیمات پروژه</b>\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=kb([[('📚 تغییر استاندارد','change_std')],[('🧱 تغییر بتن','change_fc')],[('🔩 تغییر میلگرد','change_grade')],[('🏠 صفحه اصلی','home')]]))
    if data=='change_std': return await q.edit_message_text('📚 استاندارد جدید:',reply_markup=kb([[(v,f'std_{k}') for k,v in STANDARDS.items()]]))
    if data=='change_fc': return await q.edit_message_text('🧱 بتن جدید:',reply_markup=kb([[(f'C{x}',f'fc_{x}') for x in CONCRETE_OPTIONS]]))
    if data=='change_grade':
        opts=REBAR_OPTIONS.get(context.user_data.get('standard'),[]); return await q.edit_message_text('🔩 گرید جدید:',reply_markup=kb([[(f'{g} ({fy})',f'grade_{g}') for g,fy in opts]] or [[('✏️ fy چین','china_fy')]]))
    if data=='equiv': context.user_data['equiv_step']=0; return await q.edit_message_text('تعداد میلگرد فعلی را وارد کن:',reply_markup=back_kb(lang))
    if data=='help': return await q.edit_message_text('ℹ️ این نسخه برای محاسبه مقادیر بتن و میلگرد، Rebar Schedule و Cut List است. کنترل کامل آیین‌نامه‌ای باید از لایه Code Checks انجام شود.',reply_markup=back_kb(lang))
    return await q.edit_message_text(TEXT[lang]['welcome'],parse_mode='HTML',reply_markup=main_menu(lang))

async def text_router(update,context):
    if context.user_data.get('quick_kind'):
        lang=context.user_data.get('lang','fa'); kind=context.user_data['quick_kind']; idx=context.user_data.get('quick_step',0)
        key,label,typ=QUICK_STEPS[kind][idx]; raw=update.message.text.strip().replace(',','.').replace('٫','.')
        try:
            value=float(raw); value=int(value) if typ=='int' and value.is_integer() else value
            if value<=0 or (typ=='int' and not isinstance(value,int)): raise ValueError
        except Exception:
            return await update.message.reply_text(TEXT[lang]['invalid'],reply_markup=step_kb(lang))
        context.user_data['quick_values'][key]=value; nxt=idx+1
        if nxt<len(QUICK_STEPS[kind]):
            context.user_data['quick_step']=nxt; f=QUICK_STEPS[kind][nxt]
            return await update.message.reply_text(prompt_text(lang,f[1],nxt+1,len(QUICK_STEPS[kind])),parse_mode='HTML',reply_markup=step_kb(lang))
        try:
            result=quick_result_text(kind,context.user_data['quick_values'])
            context.user_data.pop('quick_kind',None); context.user_data.pop('quick_step',None); context.user_data.pop('quick_values',None)
            return await update.message.reply_text(result,parse_mode='HTML',reply_markup=back_kb(lang,'quick_calc'))
        except Exception:
            logger.exception('Quick calculation failed')
            return await update.message.reply_text('❌ محاسبه سریع انجام نشد.',reply_markup=back_kb(lang,'quick_calc'))
    if context.user_data.get('await_fy'):
        try: fy=float(update.message.text.strip().replace(',','.')); assert fy>0
        except Exception: return await update.message.reply_text('❌ fy نامعتبر است.')
        context.user_data.update(fy=fy,grade='Custom',await_fy=False); context.user_data['project_results']=[]; return await update.message.reply_text(TEXT['fa']['welcome']+'\n\n'+project_header(context.user_data),parse_mode='HTML',reply_markup=main_menu('fa'))
    if context.user_data.get('equiv_step') is not None:
        raw=update.message.text.strip().replace(',','.').replace('٫','.')
        try: value=float(raw); assert value>0
        except Exception: return await update.message.reply_text('❌ مقدار نامعتبر است.')
        step=context.user_data.get('equiv_step',0)
        if step==0:
            context.user_data['equiv_count']=value; context.user_data['equiv_step']=1
            return await update.message.reply_text('قطر میلگرد فعلی را بر حسب mm وارد کن:')
        if step==1:
            context.user_data['equiv_d1']=value; context.user_data['equiv_step']=2
            return await update.message.reply_text('قطر میلگرد جایگزین را بر حسب mm وارد کن:')
        try:
            result=equivalent_rebar_count(int(context.user_data['equiv_count']),int(context.user_data['equiv_d1']),int(value))
            context.user_data.pop('equiv_step',None)
            return await update.message.reply_text('🔁 <b>نتیجه معادل‌سازی</b>\n\n'+escape(str(result)),parse_mode='HTML',reply_markup=back_kb(context.user_data.get('lang','fa')))
        except Exception:
            return await update.message.reply_text('❌ معادل‌سازی انجام نشد.')
    if context.user_data.get('natural_mode'):
        parsed=parse_natural_input(update.message.text)
        f=parsed.get('fields',{}); context.user_data['natural_last']=parsed
        if not f:
            return await update.message.reply_text('❌ ورودی مهندسی قابل تشخیص نبود. نمونه: «خاموت ۸ هر ۲۰ طول ۷»',reply_markup=back_kb(lang))
        lines=['🔎 <b>اطلاعات تشخیص‌داده‌شده</b>','']
        labels={'diameter_mm':'قطر','spacing_mm':'فاصله','length_m':'طول','width_m':'عرض','depth_m':'عمق','height_m':'ارتفاع','count':'تعداد','floors':'طبقات','story_height_m':'ارتفاع طبقه'}
        for k,v in f.items(): lines.append(f"{labels.get(k,k)}: <b>{v:g}</b>")
        if 'length_m' in f and 'spacing_mm' in f and ('خاموت' in update.message.text or 'stirrup' in update.message.text.lower()):
            n=natural_stirrup_quantity(f['length_m'],f['spacing_mm'])
            lines += ['',f'🔩 <b>تعداد خاموت: {n} عدد</b>']
        lines += ['', 'اگر درست است ادامه بده؛ اگر چیزی کم است همان مورد را بنویس.']
        return await update.message.reply_text('\n'.join(lines),parse_mode='HTML',reply_markup=back_kb(lang))
    if context.user_data.get('multi_mode')=='input':
        parsed=parse_natural_input(update.message.text); f=parsed.get('fields',{})
        if not all(k in f for k in ('floors','story_height_m','count','diameter_mm')):
            return await update.message.reply_text('❌ برای ستون چندطبقه: تعداد طبقات، ارتفاع طبقه، تعداد میلگرد طولی و قطر میلگرد لازم است.',reply_markup=back_kb(lang))
        try:
            if 'ld_m' in f:
                lap=iran_column_lap_rule(f['ld_m'], splice_class=f.get('splice_class','B'), special_moment_frame=True)
                plan=multistory_column_splice_schedule(int(f['floors']),f['story_height_m'],int(f['count']),int(f['diameter_mm']),lap,coupler=bool(f.get('coupler_requested')),special_moment_frame=True)
                context.user_data['multi_plan']=plan; context.user_data['multi_mode']='done'
                rows='\n'.join([f"اتصال طبقات {r['connection_between_floors']}: {r['splice_start_from_lower_story_base_m']:.2f} تا {r['splice_end_from_lower_story_base_m']:.2f} متر از پای طبقه" for r in plan['schedule'][:8]])
                return await update.message.reply_text(f"🏢 <b>برنامه وصله ستون چندطبقه</b>\n\nطبقات: {plan['floors']}\nمیلگرد: {plan['bar_count']}Φ{plan['diameter_mm']}\nطول مهاری Ld: {lap['ld_m']:.3f} m\nکلاس وصله: {lap['splice_class']}\nطول وصله: <b>{lap['lap_length_m']:.3f} m</b>\nتعداد اتصالات: {plan['connections']}\nتعداد کوپلر: {plan['couplers']}\n\n📍 <b>محل وصله</b>\n{rows}\n\n📖 مبنا: {lap['edition']}، بند {lap['basis_clause']}\n✅ وصله در نیمه میانی هر طبقه جانمایی شده و از نواحی انتهایی دور نگه داشته شده است.",parse_mode='HTML',reply_markup=professional_column_menu(lang))
            plan=column_multistory_plan(int(f['floors']),f['story_height_m'],int(f['count']),int(f['diameter_mm']))
            context.user_data['multi_plan']=plan; context.user_data['multi_mode']='done'
            return await update.message.reply_text(f"🏢 <b>برنامه اولیه ستون چندطبقه</b>\n\nطبقات: {plan['floors']}\nارتفاع هر طبقه: {plan['story_height_m']:.2f} m\nمیلگرد طولی: {plan['longitudinal_bars']}Φ{plan['diameter_mm']}\nاتصالات بین طبقات: {plan['connections']}\n\n💡 برای کنترل کامل وصله، در ورودی مقدار <code>Ld</code> را هم بده.",parse_mode='HTML',reply_markup=professional_column_menu(lang))
        except Exception:
            logger.exception('Multi-story column failed')
            return await update.message.reply_text('❌ اطلاعات ستون چندطبقه معتبر نیست.')
    return await receive(update,context)

async def error_handler(update,context): logger.exception('Unhandled bot error',exc_info=context.error)

def main():
    if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN environment variable is not set')
    if not RENDER_EXTERNAL_URL: raise RuntimeError('RENDER_EXTERNAL_URL environment variable is not set')
    webhook_url=f'{RENDER_EXTERNAL_URL}/telegram'; app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start',start)); app.add_handler(CallbackQueryHandler(buttons)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_router)); app.add_error_handler(error_handler)
    print('Concrete & Rebar Calculator Bot v2.2'); print(f'Webhook: {webhook_url}')
    app.run_webhook(listen='0.0.0.0',port=PORT,url_path='telegram',webhook_url=webhook_url,allowed_updates=Update.ALL_TYPES,drop_pending_updates=True)

if __name__=='__main__': main()
