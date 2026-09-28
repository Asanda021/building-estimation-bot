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
        raise ValueError(f"قطر {diameter_mm} در جدول میلگرد موجود نیست.")
    return length_m * REBAR_WEIGHT[diameter_mm]


def bars_12m(length_m):
    if length_m <= 0:
        return 0
    return math.ceil(length_m / 12)


def number_of_bars(dimension_m, spacing_mm, cover_mm=50):
    usable_mm = dimension_m * 1000 - 2 * cover_mm

    if usable_mm <= 0 or spacing_mm <= 0:
        return 0

    return math.ceil(usable_mm / spacing_mm) + 1


def footing_rebar_layer(
    length_m,
    width_m,
    diameter_mm,
    spacing_mm,
    count,
    cover_mm=50
):
    usable_length = max(length_m - 2 * cover_mm / 1000, 0)
    usable_width = max(width_m - 2 * cover_mm / 1000, 0)

    bars_in_width = number_of_bars(
        width_m,
        spacing_mm,
        cover_mm
    )

    bars_in_length = number_of_bars(
        length_m,
        spacing_mm,
        cover_mm
    )

    total_length = (
        bars_in_width * usable_length
        + bars_in_length * usable_width
    ) * count

    return {
        "diameter": diameter_mm,
        "spacing": spacing_mm,
        "length_m": total_length,
        "weight_kg": rebar_weight(total_length, diameter_mm),
        "bars_12m": bars_12m(total_length),
    }


def isolated_footing_complete(
    count,
    footing_length,
    footing_width,
    footing_thickness,

    lean_length,
    lean_width,
    lean_thickness,

    bottom_x_diameter,
    bottom_x_spacing,

    bottom_y_diameter,
    bottom_y_spacing,

    top_x_diameter,
    top_x_spacing,

    top_y_diameter,
    top_y_spacing,

    column_diameter,
    column_bar_count,
    column_bar_length,

    pedestal_exists=False,
    pedestal_length=0,
    pedestal_width=0,
    pedestal_height=0,

    cover_mm=50
):
    lean_concrete = (
        count
        * lean_length
        * lean_width
        * lean_thickness
    )

    footing_concrete = (
        count
        * footing_length
        * footing_width
        * footing_thickness
    )

    if pedestal_exists:
        pedestal_concrete = (
            count
            * pedestal_length
            * pedestal_width
            * pedestal_height
        )
    else:
        pedestal_concrete = 0

    bottom_x = footing_rebar_layer(
        footing_length,
        footing_width,
        bottom_x_diameter,
        bottom_x_spacing,
        count,
        cover_mm
    )

    bottom_y = footing_rebar_layer(
        footing_length,
        footing_width,
        bottom_y_diameter,
        bottom_y_spacing,
        count,
        cover_mm
    )

    top_x = footing_rebar_layer(
        footing_length,
        footing_width,
        top_x_diameter,
        top_x_spacing,
        count,
        cover_mm
    )

    top_y = footing_rebar_layer(
        footing_length,
        footing_width,
        top_y_diameter,
        top_y_spacing,
        count,
        cover_mm
    )

    column_total_length = (
        count
        * column_bar_count
        * column_bar_length
    )

    column_weight = rebar_weight(
        column_total_length,
        column_diameter
    )

    column_rebar = {
        "diameter": column_diameter,
        "count": count * column_bar_count,
        "length_m": column_total_length,
        "weight_kg": column_weight,
        "bars_12m": bars_12m(column_total_length),
    }

    total_rebar = (
        bottom_x["weight_kg"]
        + bottom_y["weight_kg"]
        + top_x["weight_kg"]
        + top_y["weight_kg"]
        + column_weight
    )

    total_concrete = (
        lean_concrete
        + footing_concrete
        + pedestal_concrete
    )

    return {
        "lean_concrete_m3": lean_concrete,
        "footing_concrete_m3": footing_concrete,
        "pedestal_concrete_m3": pedestal_concrete,
        "total_concrete_m3": total_concrete,

        "bottom_x": bottom_x,
        "bottom_y": bottom_y,
        "top_x": top_x,
        "top_y": top_y,

        "column_rebar": column_rebar,

        "total_rebar_kg": total_rebar,
    }


# -------------------------
# توابع قبلی برای جلوگیری
# از خراب شدن بخش‌های موجود
# -------------------------

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
    return isolated_footing_complete(
        count=count,
        footing_length=length_m,
        footing_width=width_m,
        footing_thickness=thickness_m,

        lean_length=lean_concrete_length_m,
        lean_width=lean_concrete_width_m,
        lean_thickness=lean_concrete_thickness_m,

        bottom_x_diameter=bottom_diameter_mm,
        bottom_x_spacing=bottom_spacing_mm,

        bottom_y_diameter=bottom_diameter_mm,
        bottom_y_spacing=bottom_spacing_mm,

        top_x_diameter=top_diameter_mm or bottom_diameter_mm,
        top_x_spacing=top_spacing_mm or bottom_spacing_mm,

        top_y_diameter=top_diameter_mm or bottom_diameter_mm,
        top_y_spacing=top_spacing_mm or bottom_spacing_mm,

        column_diameter=bottom_diameter_mm,
        column_bar_count=0,
        column_bar_length=0,

        pedestal_exists=(
            pedestal_length_m > 0
            and pedestal_width_m > 0
            and pedestal_height_m > 0
        ),

        pedestal_length=pedestal_length_m,
        pedestal_width=pedestal_width_m,
        pedestal_height=pedestal_height_m,

        cover_mm=cover_mm
    )


def total_foundation_result(results):
    total_concrete = 0
    total_rebar = 0

    for result in results:
        total_concrete += result.get(
            "total_concrete_m3", 0
        )

        total_rebar += result.get(
            "total_rebar_kg", 0
        )

    return {
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_rebar,
    }
