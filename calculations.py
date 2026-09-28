import math


REBAR_WEIGHT = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.889,
    14: 1.210,
    16: 1.580,
    18: 2.000,
    20: 2.470,
    22: 2.980,
    25: 3.850,
    28: 4.830,
    32: 6.310,
}


def rebar_weight(length_m, diameter_mm):
    if diameter_mm not in REBAR_WEIGHT:
        raise ValueError(f"قطر {diameter_mm} در جدول موجود نیست.")

    return length_m * REBAR_WEIGHT[diameter_mm]


def bars_12m(total_length_m):
    if total_length_m <= 0:
        return 0

    return math.ceil(total_length_m / 12)


def bar_length_with_lap(length_m, lap_percent=10):
    return length_m * (1 + lap_percent / 100)


def number_of_bars_in_direction(
    dimension_m,
    spacing_mm,
    cover_mm=50
):
    usable_mm = dimension_m * 1000 - 2 * cover_mm

    if usable_mm <= 0:
        return 0

    return math.ceil(usable_mm / spacing_mm) + 1


# =========================================================
# پی منفرد
# =========================================================

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
    lap_percent=10,
    pedestal_length_m=0,
    pedestal_width_m=0,
    pedestal_height_m=0
):

    # بتن مگر
    lean_concrete = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    # بتن خود پی
    footing_concrete = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    # بتن پدستال
    pedestal_concrete = (
        count
        * pedestal_length_m
        * pedestal_width_m
        * pedestal_height_m
    )

    # -------------------------
    # آرماتور پایین
    # -------------------------

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

    usable_length = max(
        length_m - 2 * cover_mm / 1000,
        0
    )

    usable_width = max(
        width_m - 2 * cover_mm / 1000,
        0
    )

    length_x = (
        bars_x
        * usable_length
        * count
    )

    length_y = (
        bars_y
        * usable_width
        * count
    )

    bottom_total_length = bar_length_with_lap(
        length_x + length_y,
        lap_percent
    )

    bottom_weight = rebar_weight(
        bottom_total_length,
        bottom_diameter_mm
    )

    # -------------------------
    # آرماتور بالا
    # -------------------------

    top_total_length = 0
    top_weight = 0
    top_bars_x = 0
    top_bars_y = 0

    if top_diameter_mm and top_spacing_mm:

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

        top_length_x = (
            top_bars_x
            * usable_length
            * count
        )

        top_length_y = (
            top_bars_y
            * usable_width
            * count
        )

        top_total_length = bar_length_with_lap(
            top_length_x + top_length_y,
            lap_percent
        )

        top_weight = rebar_weight(
            top_total_length,
            top_diameter_mm
        )

    total_concrete = (
        lean_concrete
        + footing_concrete
        + pedestal_concrete
    )

    total_rebar = (
        bottom_weight
        + top_weight
    )

    return {
        "type": "isolated",

        "lean_concrete_m3": lean_concrete,

        "footing_concrete_m3": footing_concrete,

        "pedestal_concrete_m3": pedestal_concrete,

        "total_concrete_m3": total_concrete,

        "bottom_rebar_length_m": bottom_total_length,

        "bottom_rebar_weight_kg": bottom_weight,

        "top_rebar_length_m": top_total_length,

        "top_rebar_weight_kg": top_weight,

        "total_rebar_kg": total_rebar,

        "bottom_bars_12m": bars_12m(
            bottom_total_length
        ),

        "top_bars_12m": bars_12m(
            top_total_length
        ),
    }


# =========================================================
# پی نواری
# =========================================================

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
    top_diameter_mm=None,
    top_spacing_mm=None,
    cover_mm=50,
    lap_percent=10
):

    # بتن مگر
    lean_concrete = (
        strip_count
        * lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    # بتن پی
    footing_concrete = (
        strip_count
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    # -------------------------
    # میلگردهای طولی
    # -------------------------

    longitudinal_length = (
        strip_count
        * longitudinal_count
        * strip_length_m
    )

    longitudinal_length = bar_length_with_lap(
        longitudinal_length,
        lap_percent
    )

    longitudinal_weight = rebar_weight(
        longitudinal_length,
        longitudinal_diameter_mm
    )

    # -------------------------
    # میلگردهای عرضی
    # -------------------------

    transverse_count = (
        math.ceil(
            strip_length_m * 1000
            / transverse_spacing_mm
        )
        + 1
    )

    transverse_length_each = max(
        footing_width_m
        - 2 * cover_mm / 1000,
        0
    )

    transverse_length = (
        strip_count
        * transverse_count
        * transverse_length_each
    )

    transverse_length = bar_length_with_lap(
        transverse_length,
        lap_percent
    )

    transverse_weight = rebar_weight(
        transverse_length,
        transverse_diameter_mm
    )

    # -------------------------
    # آرماتور بالا
    # -------------------------

    top_length = 0
    top_weight = 0

    if top_diameter_mm and top_spacing_mm:

        top_count = (
            math.ceil(
                strip_length_m * 1000
                / top_spacing_mm
            )
            + 1
        )

        top_length = (
            strip_count
            * top_count
            * transverse_length_each
        )

        top_length = bar_length_with_lap(
            top_length,
            lap_percent
        )

        top_weight = rebar_weight(
            top_length,
            top_diameter_mm
        )

    total_concrete = (
        lean_concrete
        + footing_concrete
    )

    total_rebar = (
        longitudinal_weight
        + transverse_weight
        + top_weight
    )

    return {
        "type": "strip",

        "lean_concrete_m3": lean_concrete,

        "footing_concrete_m3": footing_concrete,

        "total_concrete_m3": total_concrete,

        "longitudinal_rebar_length_m":
            longitudinal_length,

        "longitudinal_rebar_weight_kg":
            longitudinal_weight,

        "transverse_rebar_length_m":
            transverse_length,

        "transverse_rebar_weight_kg":
            transverse_weight,

        "top_rebar_length_m":
            top_length,

        "top_rebar_weight_kg":
            top_weight,

        "total_rebar_kg":
            total_rebar,

        "longitudinal_bars_12m":
            bars_12m(longitudinal_length),

        "transverse_bars_12m":
            bars_12m(transverse_length),

        "top_bars_12m":
            bars_12m(top_length),
    }


# =========================================================
# پی رادیه
# =========================================================

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
    lap_percent=10
):

    # بتن مگر
    lean_concrete = (
        lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    # بتن رادیه
    raft_concrete = (
        length_m
        * width_m
        * thickness_m
    )

    usable_length = max(
        length_m - 2 * cover_mm / 1000,
        0
    )

    usable_width = max(
        width_m - 2 * cover_mm / 1000,
        0
    )

    # -------------------------
    # پایین X
    # -------------------------

    bottom_x_count = number_of_bars_in_direction(
        width_m,
        bottom_x_spacing_mm,
        cover_mm
    )

    bottom_x_length = (
        bottom_x_count
        * usable_length
    )

    bottom_x_length = bar_length_with_lap(
        bottom_x_length,
        lap_percent
    )

    bottom_x_weight = rebar_weight(
        bottom_x_length,
        bottom_x_diameter_mm
    )

    # -------------------------
    # پایین Y
    # -------------------------

    bottom_y_count = number_of_bars_in_direction(
        length_m,
        bottom_y_spacing_mm,
        cover_mm
    )

    bottom_y_length = (
        bottom_y_count
        * usable_width
    )

    bottom_y_length = bar_length_with_lap(
        bottom_y_length,
        lap_percent
    )

    bottom_y_weight = rebar_weight(
        bottom_y_length,
        bottom_y_diameter_mm
    )

    # -------------------------
    # بالا X
    # -------------------------

    top_x_length = 0
    top_x_weight = 0

    if top_x_diameter_mm and top_x_spacing_mm:

        top_x_count = number_of_bars_in_direction(
            width_m,
            top_x_spacing_mm,
            cover_mm
        )

        top_x_length = (
            top_x_count
            * usable_length
        )

        top_x_length = bar_length_with_lap(
            top_x_length,
            lap_percent
        )

        top_x_weight = rebar_weight(
            top_x_length,
            top_x_diameter_mm
        )

    # -------------------------
    # بالا Y
    # -------------------------

    top_y_length = 0
    top_y_weight = 0

    if top_y_diameter_mm and top_y_spacing_mm:

        top_y_count = number_of_bars_in_direction(
            length_m,
            top_y_spacing_mm,
            cover_mm
        )

        top_y_length = (
            top_y_count
            * usable_width
        )

        top_y_length = bar_length_with_lap(
            top_y_length,
            lap_percent
        )

        top_y_weight = rebar_weight(
            top_y_length,
            top_y_diameter_mm
        )

    total_concrete = (
        lean_concrete
        + raft_concrete
    )

    total_rebar = (
        bottom_x_weight
        + bottom_y_weight
        + top_x_weight
        + top_y_weight
    )

    total_rebar_length = (
        bottom_x_length
        + bottom_y_length
        + top_x_length
        + top_y_length
    )

    return {
        "type": "raft",

        "lean_concrete_m3":
            lean_concrete,

        "raft_concrete_m3":
            raft_concrete,

        "total_concrete_m3":
            total_concrete,

        "bottom_x_length_m":
            bottom_x_length,

        "bottom_x_weight_kg":
            bottom_x_weight,

        "bottom_y_length_m":
            bottom_y_length,

        "bottom_y_weight_kg":
            bottom_y_weight,

        "top_x_length_m":
            top_x_length,

        "top_x_weight_kg":
            top_x_weight,

        "top_y_length_m":
            top_y_length,

        "top_y_weight_kg":
            top_y_weight,

        "total_rebar_length_m":
            total_rebar_length,

        "total_rebar_kg":
            total_rebar,

        "bottom_x_bars_12m":
            bars_12m(bottom_x_length),

        "bottom_y_bars_12m":
            bars_12m(bottom_y_length),

        "top_x_bars_12m":
            bars_12m(top_x_length),

        "top_y_bars_12m":
            bars_12m(top_y_length),
    }


# =========================================================
# جمع نتایج فونداسیون
# =========================================================

def total_foundation_result(results):

    total_concrete = 0
    total_rebar = 0

    for result in results:

        total_concrete += result.get(
            "total_concrete_m3",
            0
        )

        total_rebar += result.get(
            "total_rebar_kg",
            0
        )

    return {
        "total_concrete_m3":
            total_concrete,

        "total_rebar_kg":
            total_rebar,
    }
