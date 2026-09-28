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


def bars_12m(length_m):
    return math.ceil(length_m / 12)


def rebar_weight(length_m, diameter_mm):
    if diameter_mm not in REBAR_WEIGHT:
        raise ValueError(f"قطر میلگرد {diameter_mm} در جدول موجود نیست.")
    return length_m * REBAR_WEIGHT[diameter_mm]


def number_of_bars(dimension_m, spacing_mm, cover_mm=50):
    usable_mm = dimension_m * 1000 - 2 * cover_mm

    if usable_mm <= 0:
        return 0

    return math.ceil(usable_mm / spacing_mm) + 1


def rebar_layer(length_m, width_m, diameter_mm, spacing_mm, cover_mm=50):
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

    length_1 = bars_in_width * usable_length
    length_2 = bars_in_length * usable_width

    total_length = length_1 + length_2
    weight = rebar_weight(total_length, diameter_mm)

    return {
        "diameter": diameter_mm,
        "spacing": spacing_mm,
        "length_m": total_length,
        "weight_kg": weight,
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

    # بتن مگر
    lean_concrete = (
        count
        * lean_length
        * lean_width
        * lean_thickness
    )

    # بتن فونداسیون
    footing_concrete = (
        count
        * footing_length
        * footing_width
        * footing_thickness
    )

    # بتن پدستال
    if pedestal_exists:
        pedestal_concrete = (
            count
            * pedestal_length
            * pedestal_width
            * pedestal_height
        )
    else:
        pedestal_concrete = 0

    # میلگرد پایین X
    bottom_x = rebar_layer(
        footing_length,
        footing_width,
        bottom_x_diameter,
        bottom_x_spacing,
        cover_mm
    )

    # میلگرد پایین Y
    bottom_y = rebar_layer(
        footing_length,
        footing_width,
        bottom_y_diameter,
        bottom_y_spacing,
        cover_mm
    )

    # میلگرد بالا X
    top_x = rebar_layer(
        footing_length,
        footing_width,
        top_x_diameter,
        top_x_spacing,
        cover_mm
    )

    # میلگرد بالا Y
    top_y = rebar_layer(
        footing_length,
        footing_width,
        top_y_diameter,
        top_y_spacing,
        cover_mm
    )

    # تعداد پی
    for layer in [bottom_x, bottom_y, top_x, top_y]:
        layer["length_m"] *= count
        layer["weight_kg"] *= count
        layer["bars_12m"] = bars_12m(layer["length_m"])

    # میلگرد انتظار ستون
    column_total_length = (
        count
        * column_bar_count
        * column_bar_length
    )

    column_weight = rebar_weight(
        column_total_length,
        column_diameter
    )

    column_bars_12m = bars_12m(column_total_length)

    # کل میلگرد
    total_rebar = (
        bottom_x["weight_kg"]
        + bottom_y["weight_kg"]
        + top_x["weight_kg"]
        + top_y["weight_kg"]
        + column_weight
    )

    # کل بتن
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

        "column_rebar": {
            "diameter": column_diameter,
            "count": column_bar_count * count,
            "length_m": column_total_length,
            "weight_kg": column_weight,
            "bars_12m": column_bars_12m,
        },

        "total_rebar_kg": total_rebar,
    }
