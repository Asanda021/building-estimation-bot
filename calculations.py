import math


# -----------------------------
# وزن واحد میلگرد
# -----------------------------

REBAR_WEIGHT = {
    8: 0.395,
    10: 0.617,
    12: 0.889,
    14: 1.21,
    16: 1.58,
    18: 2.00,
    20: 2.47,
    22: 2.98,
    25: 3.86,
    28: 4.83,
    32: 6.31,
}


def rebar_weight(length, diameter):
    """محاسبه وزن میلگرد"""
    return length * REBAR_WEIGHT[diameter]


def rebar_bars(length):
    """تعداد شاخه ۱۲ متری"""
    return math.ceil(length / 12)


# -----------------------------
# بتن سقف
# -----------------------------

ROOF_CONCRETE_COEFFICIENT = {
    "تیرچه یونولیتی": 0.18,
    "تیرچه سفالی": 0.20,
    "تیرچه دوبل": 0.23,
    "کرومیت": 0.18,
    "کامپوزیت": 0.15,
    "عرشه فولادی": 0.15,
    "دال بتنی": 0.20,
    "وافل": 0.20,
}


def roof_concrete(area, roof_type):
    """محاسبه حجم بتن سقف"""
    coefficient = ROOF_CONCRETE_COEFFICIENT[roof_type]
    return area * coefficient


# -----------------------------
# بتن فونداسیون
# -----------------------------

def foundation_concrete(length, width, height):
    """حجم بتن فونداسیون"""
    return length * width * height


# -----------------------------
# بتن ستون
# -----------------------------

def column_concrete(count, width, depth, height):
    """حجم بتن ستون‌ها"""
    return count * width * depth * height


# -----------------------------
# بتن تیر
# -----------------------------

def beam_concrete(count, length, width, height):
    """حجم بتن تیرها"""
    return count * length * width * height
