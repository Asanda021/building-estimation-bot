# calculations.py
# -*- coding: utf-8 -*-

from math import ceil
from collections import defaultdict


# ============================================================
# وزن واحد میلگرد (kg/m)
# ============================================================

REBAR_WEIGHT = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.208,
    16: 1.578,
    18: 2.000,
    20: 2.466,
    22: 2.984,
    25: 3.853,
    28: 4.834,
    32: 6.313,
}


def rebar_weight(diameter_mm, length_m):
    """محاسبه وزن میلگرد بر اساس قطر و طول"""
    diameter_mm = int(diameter_mm)
    length_m = float(length_m)

    if diameter_mm not in REBAR_WEIGHT:
        raise ValueError(f"قطر میلگرد {diameter_mm} در جدول وجود ندارد.")

    return REBAR_WEIGHT[diameter_mm] * length_m


def bars_12m(total_length_m):
    """تعداد شاخه 12 متری مورد نیاز"""
    if total_length_m <= 0:
        return 0

    return ceil(total_length_m / 12)


# ============================================================
# ابزارهای عمومی
# ============================================================

def number_of_bars_in_direction(length_m, spacing_mm, cover_mm=50):
    """
    تعداد میلگرد در یک جهت
    """
    length_m = float(length_m)
    spacing_mm = float(spacing_mm)
    cover_mm = float(cover_mm)

    usable_mm = max(length_m * 1000 - 2 * cover_mm, 0)

    if spacing_mm <= 0:
        raise ValueError("فاصله میلگرد باید بیشتر از صفر باشد.")

    return max(2, ceil(usable_mm / spacing_mm) + 1)


def usable_length(length_m, cover_mm=50):
    """
    طول مفید داخل عضو با کسر کاور دو طرف
    """
    return max(float(length_m) - 2 * float(cover_mm) / 1000, 0)


def bar_length_with_lap(length_m, lap_percent=0):
    """
    افزایش طول به علت وصله پوششی
    """
    return float(length_m) * (1 + float(lap_percent) / 100)


# ============================================================
# بهینه‌سازی برش شاخه‌های 12 متری
# ============================================================

def optimize_12m_bars(cuts):
    """
    cuts:
        لیستی از طول قطعات بر حسب متر

    خروجی:
        لیست شاخه‌های 12 متری و قطعات قرار گرفته داخل هر شاخه
    """

    if not cuts:
        return []

    cuts = [float(x) for x in cuts if float(x) > 0]
    cuts.sort(reverse=True)

    bars = []

    for cut in cuts:
        placed = False

        for bar in bars:
            if bar["remaining"] + 1e-9 >= cut:
                bar["cuts"].append(cut)
                bar["remaining"] -= cut
                placed = True
                break

        if not placed:
            bars.append({
                "stock_length": 12.0,
                "cuts": [cut],
                "remaining": 12.0 - cut,
            })

    return bars


def make_rebar_detail(
    diameter_mm,
    pieces,
    piece_length_m,
    lap_percent=0,
    description=""
):
    """
    ساخت جزئیات میلگرد
    """

    diameter_mm = int(diameter_mm)
    pieces = int(pieces)
    piece_length_m = float(piece_length_m)

    final_length = bar_length_with_lap(
        piece_length_m,
        lap_percent
    )

    total_length = pieces * final_length
    weight = rebar_weight(
        diameter_mm,
        total_length
    )

    return {
        "diameter": diameter_mm,
        "pieces": pieces,
        "piece_length": round(final_length, 3),
        "total_length": round(total_length, 3),
        "weight": round(weight, 2),
        "bars_12m": bars_12m(total_length),
        "description": description,
    }


def add_rebar_detail(details, detail):
    """افزودن یک آیتم میلگرد"""
    details.append(detail)
    return details


def finalize_rebar_details(details):
    """
    جمع‌بندی میلگردها
    """

    total_weight = sum(
        item.get("weight", 0)
        for item in details
    )

    total_length = sum(
        item.get("total_length", 0)
        for item in details
    )

    return {
        "details": details,
        "total_weight": round(total_weight, 2),
        "total_length": round(total_length, 2),
    }


# ============================================================
# پی منفرد
# ============================================================

def isolated_footing(
    count,
    length_m,
    width_m,
    thickness_m,
    lean_concrete_length_m,
    lean_concrete_width_m,
    lean_concrete_thickness_m,
    bottom_diameter_mm,
    bottom_spacing_mm,
    top_diameter_mm=None,
    top_spacing_mm=None,
    cover_mm=50,
    lap_percent=0,
    pedestal_length_m=0,
    pedestal_width_m=0,
    pedestal_height_m=0,
):

    count = int(count)

    # بتن مگر
    lean_concrete = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    # بتن پی
    footing_concrete = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    # بتن ستونک / پدستال
    pedestal_concrete = (
        count
        * pedestal_length_m
        * pedestal_width_m
        * pedestal_height_m
    )

    structural_concrete = (
        footing_concrete +
        pedestal_concrete
    )

    details = []

    # --------------------------------------------------------
    # میلگرد پایین - جهت X
    # --------------------------------------------------------

    bars_x = number_of_bars_in_direction(
        width_m,
        bottom_spacing_mm,
        cover_mm
    )

    bars_y = number_of_bars_in_direction(
        length_m,
        bottom_spacing_mm,
        cover_mm
    )

    length_x = usable_length(
        length_m,
        cover_mm
    )

    length_y = usable_length(
        width_m,
        cover_mm
    )

    total_x = bars_x * length_x * count
    total_y = bars_y * length_y * count

    add_rebar_detail(
        details,
        make_rebar_detail(
            bottom_diameter_mm,
            bars_x * count,
            length_x,
            lap_percent,
            "شبکه پایین جهت X"
        )
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            bottom_diameter_mm,
            bars_y * count,
            length_y,
            lap_percent,
            "شبکه پایین جهت Y"
        )
    )

    # --------------------------------------------------------
    # میلگرد بالایی - اختیاری
    # --------------------------------------------------------

    if (
        top_diameter_mm
        and top_spacing_mm
    ):

        top_bars_x = number_of_bars_in_direction(
            width_m,
            top_spacing_mm,
            cover_mm
        )

        top_bars_y = number_of_bars_in_direction(
            length_m,
            top_spacing_mm,
            cover_mm
        )

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_diameter_mm,
                top_bars_x * count,
                length_x,
                lap_percent,
                "شبکه بالا جهت X"
            )
        )

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_diameter_mm,
                top_bars_y * count,
                length_y,
                lap_percent,
                "شبکه بالا جهت Y"
            )
        )

    summary = finalize_rebar_details(details)

    return {
        "type": "isolated_footing",
        "count": count,
        "lean_concrete": round(lean_concrete, 3),
        "footing_concrete": round(footing_concrete, 3),
        "pedestal_concrete": round(pedestal_concrete, 3),
        "structural_concrete": round(structural_concrete, 3),
        "total_concrete": round(
            lean_concrete + structural_concrete,
            3
        ),
        "rebar": summary,
    }


# ============================================================
# پی نواری
# ============================================================

def strip_footing(
    strip_count,
    strip_length_m,
    footing_width_m,
    footing_thickness_m,
    lean_length_m,
    lean_width_m,
    lean_thickness_m,
    longitudinal_diameter_mm,
    longitudinal_count,
    transverse_diameter_mm,
    transverse_spacing_mm,
    top_longitudinal_diameter_mm=None,
    top_longitudinal_count=None,
    top_transverse_diameter_mm=None,
    top_transverse_spacing_mm=None,
    cover_mm=50,
    lap_percent=0,
):

    strip_count = int(strip_count)

    lean_concrete = (
        strip_count
        * lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    footing_concrete = (
        strip_count
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    details = []

    # میلگردهای طولی پایین
    add_rebar_detail(
        details,
        make_rebar_detail(
            longitudinal_diameter_mm,
            longitudinal_count * strip_count,
            strip_length_m,
            lap_percent,
            "میلگرد طولی پایین"
        )
    )

    # میلگردهای عرضی پایین
    transverse_count = number_of_bars_in_direction(
        strip_length_m,
        transverse_spacing_mm,
        cover_mm
    )

    transverse_length = usable_length(
        footing_width_m,
        cover_mm
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            transverse_diameter_mm,
            transverse_count * strip_count,
            transverse_length,
            lap_percent,
            "میلگرد عرضی پایین"
        )
    )

    # میلگرد طولی بالا
    if (
        top_longitudinal_diameter_mm
        and top_longitudinal_count
    ):

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_longitudinal_diameter_mm,
                int(top_longitudinal_count) * strip_count,
                strip_length_m,
                lap_percent,
                "میلگرد طولی بالا"
            )
        )

    # میلگرد عرضی بالا
    if (
        top_transverse_diameter_mm
        and top_transverse_spacing_mm
    ):

        top_transverse_count = number_of_bars_in_direction(
            strip_length_m,
            top_transverse_spacing_mm,
            cover_mm
        )

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_transverse_diameter_mm,
                top_transverse_count * strip_count,
                transverse_length,
                lap_percent,
                "میلگرد عرضی بالا"
            )
        )

    summary = finalize_rebar_details(details)

    return {
        "type": "strip_footing",
        "count": strip_count,
        "lean_concrete": round(lean_concrete, 3),
        "footing_concrete": round(footing_concrete, 3),
        "structural_concrete": round(footing_concrete, 3),
        "total_concrete": round(
            lean_concrete + footing_concrete,
            3
        ),
        "rebar": summary,
    }


# ============================================================
# پی گسترده / رادیه
# ============================================================

def raft_foundation(
    length_m,
    width_m,
    thickness_m,
    lean_length_m,
    lean_width_m,
    lean_thickness_m,
    bottom_x_diameter_mm,
    bottom_x_spacing_mm,
    bottom_y_diameter_mm,
    bottom_y_spacing_mm,
    top_x_diameter_mm=None,
    top_x_spacing_mm=None,
    top_y_diameter_mm=None,
    top_y_spacing_mm=None,
    cover_mm=50,
    lap_percent=0,
):

    lean_concrete = (
        lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    raft_concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    # پایین X
    count_x = number_of_bars_in_direction(
        width_m,
        bottom_x_spacing_mm,
        cover_mm
    )

    length_x = usable_length(
        length_m,
        cover_mm
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            bottom_x_diameter_mm,
            count_x,
            length_x,
            lap_percent,
            "شبکه پایین X"
        )
    )

    # پایین Y
    count_y = number_of_bars_in_direction(
        length_m,
        bottom_y_spacing_mm,
        cover_mm
    )

    length_y = usable_length(
        width_m,
        cover_mm
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            bottom_y_diameter_mm,
            count_y,
            length_y,
            lap_percent,
            "شبکه پایین Y"
        )
    )

    # بالا X
    if (
        top_x_diameter_mm
        and top_x_spacing_mm
    ):

        count = number_of_bars_in_direction(
            width_m,
            top_x_spacing_mm,
            cover_mm
        )

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_x_diameter_mm,
                count,
                length_x,
                lap_percent,
                "شبکه بالا X"
            )
        )

    # بالا Y
    if (
        top_y_diameter_mm
        and top_y_spacing_mm
    ):

        count = number_of_bars_in_direction(
            length_m,
            top_y_spacing_mm,
            cover_mm
        )

        add_rebar_detail(
            details,
            make_rebar_detail(
                top_y_diameter_mm,
                count,
                length_y,
                lap_percent,
                "شبکه بالا Y"
            )
        )

    summary = finalize_rebar_details(details)

    return {
        "type": "raft_foundation",
        "lean_concrete": round(lean_concrete, 3),
        "raft_concrete": round(raft_concrete, 3),
        "structural_concrete": round(raft_concrete, 3),
        "total_concrete": round(
            lean_concrete + raft_concrete,
            3
        ),
        "rebar": summary,
    }


# ============================================================
# جمع‌بندی فونداسیون
# ============================================================

def total_foundation_result(results):
    """
    جمع نتایج چند نوع فونداسیون
    """

    total_concrete = sum(
        result.get("total_concrete", 0)
        for result in results
    )

    total_rebar = sum(
        result.get("rebar", {}).get("total_weight", 0)
        for result in results
    )

    return {
        "total_concrete": round(total_concrete, 3),
        "total_rebar": round(total_rebar, 2),
        "results": results,
    }


# ============================================================
# ستون مستطیلی
# ============================================================

def column_rectangular(
    count,
    width_m,
    depth_m,
    height_m,
    main_diameter_mm,
    main_count,
    stirrup_diameter_mm,
    stirrup_spacing_mm,
    cover_mm=40,
):

    count = int(count)

    concrete = (
        count
        * width_m
        * depth_m
        * height_m
    )

    # میلگردهای طولی
    main_length = max(
        height_m - 2 * cover_mm / 1000,
        0
    )

    details = []

    add_rebar_detail(
        details,
        make_rebar_detail(
            main_diameter_mm,
            main_count * count,
            main_length,
            0,
            "میلگرد طولی ستون"
        )
    )

    # خاموت
    stirrup_count = (
        ceil(
            max(
                height_m * 1000 - 2 * cover_mm,
                0
            )
            / stirrup_spacing_mm
        )
        + 1
    )

    stirrup_length = (
        2 * (
            max(width_m - 2 * cover_mm / 1000, 0)
            +
            max(depth_m - 2 * cover_mm / 1000, 0)
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            stirrup_diameter_mm,
            stirrup_count * count,
            stirrup_length,
            0,
            "خاموت ستون"
        )
    )

    summary = finalize_rebar_details(details)

    return {
        "type": "column_rectangular",
        "count": count,
        "concrete": round(concrete, 3),
        "rebar": summary,
    }


# ============================================================
# ستون گرد
# ============================================================

def column_round(
    count,
    diameter_m,
    height_m,
    main_diameter_mm,
    main_count,
    stirrup_diameter_mm,
    stirrup_spacing_mm,
    cover_mm=40,
):

    count = int(count)

    radius = diameter_m / 2

    concrete = (
        count
        * 3.141592653589793
        * radius ** 2
        * height_m
    )

    details = []

    main_length = max(
        height_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            main_diameter_mm,
            main_count * count,
            main_length,
            0,
            "میلگرد طولی ستون گرد"
        )
    )

    stirrup_count = (
        ceil(
            max(
                height_m * 1000 - 2 * cover_mm,
                0
            )
            / stirrup_spacing_mm
        )
        + 1
    )

    stirrup_length = (
        3.141592653589793
        * max(
            diameter_m - 2 * cover_mm / 1000,
            0
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            stirrup_diameter_mm,
            stirrup_count * count,
            stirrup_length,
            0,
            "خاموت / دورپیچ ستون گرد"
        )
    )

    summary = finalize_rebar_details(details)

    return {
        "type": "column_round",
        "count": count,
        "concrete": round(concrete, 3),
        "rebar": summary,
    }


# ============================================================
# تیر
# ============================================================

def beam(
    count,
    length_m,
    width_m,
    height_m,
    main_diameter_mm,
    main_top_count,
    main_bottom_count,
    stirrup_diameter_mm,
    stirrup_spacing_mm,
    cover_mm=40,
):

    count = int(count)

    concrete = (
        count
        * length_m
        * width_m
        * height_m
    )

    details = []

    main_length = max(
        length_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            main_diameter_mm,
            (
                main_top_count +
                main_bottom_count
            ) * count,
            main_length,
            0,
            "میلگرد طولی تیر"
        )
    )

    stirrup_count = (
        ceil(
            max(
                length_m * 1000 - 2 * cover_mm,
                0
            )
            / stirrup_spacing_mm
        )
        + 1
    )

    stirrup_length = (
        2 * (
            max(width_m - 2 * cover_mm / 1000, 0)
            +
            max(height_m - 2 * cover_mm / 1000, 0)
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            stirrup_diameter_mm,
            stirrup_count * count,
            stirrup_length,
            0,
            "خاموت تیر"
        )
    )

    summary = finalize_rebar_details(details)

    return {
        "type": "beam",
        "count": count,
        "concrete": round(concrete, 3),
        "rebar": summary,
    }


# ============================================================
# شناژ / کلاف
# ============================================================

def tie_beam(
    count,
    length_m,
    width_m,
    height_m,
    main_diameter_mm,
    main_count,
    stirrup_diameter_mm,
    stirrup_spacing_mm,
    cover_mm=40,
):

    return beam(
        count=count,
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        main_diameter_mm=main_diameter_mm,
        main_top_count=main_count,
        main_bottom_count=main_count,
        stirrup_diameter_mm=stirrup_diameter_mm,
        stirrup_spacing_mm=stirrup_spacing_mm,
        cover_mm=cover_mm,
    )


# ============================================================
# دیوار بتنی
# ============================================================

def wall_concrete(
    count,
    length_m,
    thickness_m,
    height_m,
    vertical_diameter_mm,
    vertical_spacing_mm,
    horizontal_diameter_mm,
    horizontal_spacing_mm,
    cover_mm=40,
):

    count = int(count)

    concrete = (
        count
        * length_m
        * thickness_m
        * height_m
    )

    details = []

    # قائم
    vertical_count = number_of_bars_in_direction(
        length_m,
        vertical_spacing_mm,
        cover_mm
    )

    vertical_length = max(
        height_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            vertical_diameter_mm,
            vertical_count * count,
            vertical_length,
            0,
            "میلگرد قائم دیوار"
        )
    )

    # افقی
    horizontal_count = number_of_bars_in_direction(
        height_m,
        horizontal_spacing_mm,
        cover_mm
    )

    horizontal_length = max(
        length_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            horizontal_diameter_mm,
            horizontal_count * count,
            horizontal_length,
            0,
            "میلگرد افقی دیوار"
        )
    )

    summary = finalize_rebar_details(details)

    return {
        "type": "wall",
        "count": count,
        "concrete": round(concrete, 3),
        "rebar": summary,
    }


# ============================================================
# راه‌پله
# ============================================================

def stair_slab(
    count,
    length_m,
    width_m,
    thickness_m,
    main_diameter_mm,
    main_spacing_mm,
    distribution_diameter_mm,
    distribution_spacing_mm,
    cover_mm=30,
):

    count = int(count)

    concrete = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    details = []

    main_count = number_of_bars_in_direction(
        width_m,
        main_spacing_mm,
        cover_mm
    )

    main_length = max(
        length_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            main_diameter_mm,
            main_count * count,
            main_length,
            0,
            "میلگرد اصلی راه‌پله"
        )
    )

    distribution_count = number_of_bars_in_direction(
        length_m,
        distribution_spacing_mm,
        cover_mm
    )

    distribution_length = max(
        width_m - 2 * cover_mm / 1000,
        0
    )

    add_rebar_detail(
        details,
        make_rebar_detail(
            distribution_diameter_mm,
            distribution_count * count,
            distribution_length,
            0,
            "میلگرد توزیعی راه‌پله"
        )
    )

    summary = finalize_rebar_details(details)

    return {
        "type": "stair",
        "count": count,
        "concrete": round(concrete, 3),
        "rebar": summary,
    }


# ============================================================
# سقف
# ============================================================

ROOF_CONCRETE_COEFFICIENTS = {
    "تیرچه یونولیتی": 0.18,
    "تیرچه سفالی": 0.20,
    "تیرچه دوبل": 0.23,
    "کرومیت": 0.18,
    "کامپوزیت": 0.15,
    "عرشه فولادی": 0.15,
    "دال بتنی": 0.20,
    "وافل": 0.20,
}


def roof_slab(
    roof_type,
    area_m2,
    rebar_kg_per_m2=0,
):

    area_m2 = float(area_m2)

    if roof_type not in ROOF_CONCRETE_COEFFICIENTS:
        raise ValueError(
            f"نوع سقف «{roof_type}» تعریف نشده است."
        )

    coefficient = ROOF_CONCRETE_COEFFICIENTS[
        roof_type
    ]

    concrete = area_m2 * coefficient

    rebar_weight_total = (
        area_m2 * float(rebar_kg_per_m2)
    )

    return {
        "type": "roof",
        "roof_type": roof_type,
        "area": round(area_m2, 2),
        "concrete": round(concrete, 3),
        "rebar_weight": round(
            rebar_weight_total,
            2
        ),
    }


# ============================================================
# تست سریع فایل
# ============================================================

if __name__ == "__main__":

    result = isolated_footing(
        count=4,
        length_m=2,
        width_m=2,
        thickness_m=0.5,
        lean_concrete_length_m=2.2,
        lean_concrete_width_m=2.2,
        lean_concrete_thickness_m=0.1,
        bottom_diameter_mm=16,
        bottom_spacing_mm=150,
        top_diameter_mm=12,
        top_spacing_mm=200,
        cover_mm=50,
        pedestal_length_m=0.5,
        pedestal_width_m=0.5,
        pedestal_height_m=0.6,
    )

    print("===== TEST =====")
    print("Concrete:", result["total_concrete"], "m3")
    print("Rebar:", result["rebar"]["total_weight"], "kg")
    print()

    for item in result["rebar"]["details"]:
        print(
            f"Φ{item['diameter']} | "
            f"{item['pieces']} قطعه | "
            f"{item['piece_length']} m | "
            f"{item['weight']} kg | "
            f"{item['bars_12m']} شاخه 12m"
        )
