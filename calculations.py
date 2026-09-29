# -*- coding: utf-8 -*-

import math


# =========================================================
# وزن واحد میلگرد - kg/m
# =========================================================

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


# =========================================================
# ابزارهای عمومی
# =========================================================

def rebar_weight(diameter_mm, length_m):
    diameter_mm = int(diameter_mm)

    unit_weight = REBAR_WEIGHT.get(
        diameter_mm,
        diameter_mm * diameter_mm / 162.0
    )

    return float(length_m) * unit_weight


def usable_length(length_m, cover_mm=50):
    """
    طول مفید میلگرد با کسر کاور از دو طرف
    """

    result = (
        float(length_m)
        - 2 * float(cover_mm) / 1000
    )

    return max(result, 0.0)


def number_of_bars_in_direction(
    length_m,
    spacing_mm,
    cover_mm=50
):
    """
    تعداد میلگرد در یک جهت

    مثال:
    طول = 10m
    فاصله = 20cm
    """

    spacing_m = float(spacing_mm) / 1000

    if spacing_m <= 0:
        raise ValueError(
            "فاصله میلگرد باید بزرگ‌تر از صفر باشد."
        )

    usable = usable_length(
        length_m,
        cover_mm
    )

    return (
        math.floor(
            usable / spacing_m + 1e-9
        )
        + 1
    )


def bar_length_with_lap(
    length_m,
    lap_percent=0
):
    return (
        float(length_m)
        * (1 + float(lap_percent) / 100)
    )


# =========================================================
# برش شاخه 12 متری
# =========================================================

def optimize_12m_bars(cuts):

    pieces = sorted(
        [
            float(x)
            for x in cuts
            if float(x) > 0
        ],
        reverse=True
    )

    for piece in pieces:

        if piece > 12.000001:
            raise ValueError(
                "طول یک قطعه از شاخه ۱۲ متری بیشتر است."
            )

    bars = []

    for piece in pieces:

        placed = False

        for bar in bars:

            if bar["used"] + piece <= 12.000001:

                bar["pieces"].append(piece)

                bar["used"] += piece

                bar["waste"] = (
                    12 - bar["used"]
                )

                placed = True

                break

        if not placed:

            bars.append(
                {
                    "pieces": [piece],
                    "used": piece,
                    "waste": 12 - piece,
                }
            )

    return {
        "stock_bars": len(bars),
        "waste_m": sum(
            b["waste"]
            for b in bars
        ),
        "plans": bars,
    }


# =========================================================
# جزئیات میلگرد
# =========================================================

def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):

    pieces = [
        bar_length_with_lap(
            x,
            lap_percent
        )
        for x in piece_lengths
        if float(x) > 0
    ]

    optimization = optimize_12m_bars(
        pieces
    )

    total_length = sum(pieces)

    return {

        "diameter_mm":
            int(diameter_mm),

        "length_m":
            total_length,

        "weight_kg":
            rebar_weight(
                diameter_mm,
                total_length
            ),

        "bars_12m":
            optimization["stock_bars"],

        "piece_count":
            len(pieces),

        "piece_lengths_m":
            pieces,

        "waste_m":
            optimization["waste_m"],

        "cut_plan":
            optimization["plans"],

        "description":
            description,
    }


def add_rebar_detail(
    details,
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):

    if piece_lengths:

        details.append(
            make_rebar_detail(
                diameter_mm,
                piece_lengths,
                description,
                lap_percent
            )
        )


def finalize_rebar_details(details):

    grouped = {}

    descriptions = {}

    for item in details:

        diameter = int(
            item["diameter_mm"]
        )

        grouped.setdefault(
            diameter,
            []
        ).extend(
            item["piece_lengths_m"]
        )

        if item.get("description"):

            descriptions.setdefault(
                diameter,
                []
            ).append(
                item["description"]
            )

    result = []

    for diameter in sorted(
        grouped.keys()
    ):

        pieces = grouped[diameter]

        optimization = optimize_12m_bars(
            pieces
        )

        total_length = sum(pieces)

        result.append(
            {
                "diameter_mm":
                    diameter,

                "length_m":
                    total_length,

                "weight_kg":
                    rebar_weight(
                        diameter,
                        total_length
                    ),

                "bars_12m":
                    optimization["stock_bars"],

                "piece_count":
                    len(pieces),

                "piece_lengths_m":
                    pieces,

                "waste_m":
                    optimization["waste_m"],

                "cut_plan":
                    optimization["plans"],

                "description":
                    " + ".join(
                        dict.fromkeys(
                            descriptions.get(
                                diameter,
                                []
                            )
                        )
                    ),
            }
        )

    return result


# =========================================================
# نتیجه عمومی فونداسیون
# =========================================================

def _foundation_result(
    lean_concrete,
    structural_concrete,
    details,
    **extra
):

    rebar_details = finalize_rebar_details(
        details
    )

    return {

        "lean_concrete_m3":
            lean_concrete,

        "structural_concrete_m3":
            structural_concrete,

        "total_concrete_m3":
            lean_concrete
            + structural_concrete,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in rebar_details
            ),

        "rebar_details":
            rebar_details,

        **extra,
    }


# =========================================================
# 1 - پی منفرد
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
    lap_percent=0,

    pedestal_length_m=0,
    pedestal_width_m=0,
    pedestal_height_m=0,
):

    count = int(count)

    if count <= 0:
        raise ValueError(
            "تعداد پی باید بزرگ‌تر از صفر باشد."
        )

    # بتن پی
    footing_concrete = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    # بتن مگر
    lean_concrete = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    # بتن پدستال
    pedestal_concrete = (
        count
        * pedestal_length_m
        * pedestal_width_m
        * pedestal_height_m
    )

    details = []

    usable_L = usable_length(
        length_m,
        cover_mm
    )

    usable_W = usable_length(
        width_m,
        cover_mm
    )

    # -----------------------------------------
    # شبکه پایین X
    # -----------------------------------------

    number_X = number_of_bars_in_direction(
        width_m,
        bottom_spacing_mm,
        cover_mm
    )

    add_rebar_detail(

        details,

        bottom_diameter_mm,

        [usable_L]
        * (
            number_X
            * count
        ),

        "پی منفرد - شبکه پایین X",

        lap_percent
    )

    # -----------------------------------------
    # شبکه پایین Y
    # -----------------------------------------

    number_Y = number_of_bars_in_direction(
        length_m,
        bottom_spacing_mm,
        cover_mm
    )

    add_rebar_detail(

        details,

        bottom_diameter_mm,

        [usable_W]
        * (
            number_Y
            * count
        ),

        "پی منفرد - شبکه پایین Y",

        lap_percent
    )

    # -----------------------------------------
    # شبکه بالا X/Y
    # -----------------------------------------

    if (
        top_diameter_mm
        and top_spacing_mm
    ):

        number_X = number_of_bars_in_direction(
            width_m,
            top_spacing_mm,
            cover_mm
        )

        number_Y = number_of_bars_in_direction(
            length_m,
            top_spacing_mm,
            cover_mm
        )

        add_rebar_detail(

            details,

            top_diameter_mm,

            [usable_L]
            * (
                number_X
                * count
            ),

            "پی منفرد - شبکه بالا X",

            lap_percent
        )

        add_rebar_detail(

            details,

            top_diameter_mm,

            [usable_W]
            * (
                number_Y
                * count
            ),

            "پی منفرد - شبکه بالا Y",

            lap_percent
        )

    result = _foundation_result(

        lean_concrete,

        footing_concrete
        + pedestal_concrete,

        details,

        count=count,

        footing_concrete_m3=
            footing_concrete,

        pedestal_concrete_m3=
            pedestal_concrete,
    )

    return result


# =========================================================
# 2 - پی نواری
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

    top_longitudinal_diameter_mm=None,
    top_longitudinal_count=None,

    top_transverse_diameter_mm=None,
    top_transverse_spacing_mm=None,

    cover_mm=50,
    lap_percent=0,
):

    strip_count = int(
        strip_count
    )

    longitudinal_count = int(
        longitudinal_count
    )

    if strip_count <= 0:
        raise ValueError(
            "تعداد نوار باید بزرگ‌تر از صفر باشد."
        )

    if longitudinal_count <= 0:
        raise ValueError(
            "تعداد میلگرد طولی باید بزرگ‌تر از صفر باشد."
        )

    if transverse_spacing_mm <= 0:
        raise ValueError(
            "فاصله میلگرد عرضی باید بزرگ‌تر از صفر باشد."
        )

    # -----------------------------------------
    # بتن
    # -----------------------------------------

    lean_concrete = (
        strip_count
        * lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    structural_concrete = (
        strip_count
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    details = []

    usable_L = usable_length(
        strip_length_m,
        cover_mm
    )

    usable_W = usable_length(
        footing_width_m,
        cover_mm
    )

    # -----------------------------------------
    # میلگرد طولی پایین
    # -----------------------------------------

    add_rebar_detail(

        details,

        longitudinal_diameter_mm,

        [usable_L]
        * (
            longitudinal_count
            * strip_count
        ),

        "پی نواری - طولی پایین",

        lap_percent
    )

    # -----------------------------------------
    # میلگرد عرضی پایین
    # -----------------------------------------

    transverse_count = (
        number_of_bars_in_direction(
            strip_length_m,
            transverse_spacing_mm,
            cover_mm
        )
    )

    add_rebar_detail(

        details,

        transverse_diameter_mm,

        [usable_W]
        * (
            transverse_count
            * strip_count
        ),

        "پی نواری - عرضی پایین",

        lap_percent
    )

    # -----------------------------------------
    # طولی بالا
    # -----------------------------------------

    if (
        top_longitudinal_diameter_mm
        and top_longitudinal_count
    ):

        add_rebar_detail(

            details,

            top_longitudinal_diameter_mm,

            [usable_L]
            * (
                int(top_longitudinal_count)
                * strip_count
            ),

            "پی نواری - طولی بالا",

            lap_percent
        )

    # -----------------------------------------
    # عرضی بالا
    # -----------------------------------------

    if (
        top_transverse_diameter_mm
        and top_transverse_spacing_mm
    ):

        top_transverse_count = (
            number_of_bars_in_direction(
                strip_length_m,
                top_transverse_spacing_mm,
                cover_mm
            )
        )

        add_rebar_detail(

            details,

            top_transverse_diameter_mm,

            [usable_W]
            * (
                top_transverse_count
                * strip_count
            ),

            "پی نواری - عرضی بالا",

            lap_percent
        )

    return _foundation_result(

        lean_concrete,

        structural_concrete,

        details,

        count=strip_count,

        footing_concrete_m3=
            structural_concrete,
    )


# =========================================================
# 3 - پی گسترده / رادیه
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
    lap_percent=0,
):

    lean_concrete = (
        lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    structural_concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    usable_L = usable_length(
        length_m,
        cover_mm
    )

    usable_W = usable_length(
        width_m,
        cover_mm
    )

    # -----------------------------------------
    # شبکه پایین X
    # -----------------------------------------

    number_X = number_of_bars_in_direction(
        width_m,
        bottom_x_spacing_mm,
        cover_mm
    )

    add_rebar_detail(

        details,

        bottom_x_diameter_mm,

        [usable_L]
        * number_X,

        "رادیه - شبکه پایین X",

        lap_percent
    )

    # -----------------------------------------
    # شبکه پایین Y
    # -----------------------------------------

    number_Y = number_of_bars_in_direction(
        length_m,
        bottom_y_spacing_mm,
        cover_mm
    )

    add_rebar_detail(

        details,

        bottom_y_diameter_mm,

        [usable_W]
        * number_Y,

        "رادیه - شبکه پایین Y",

        lap_percent
    )

    # -----------------------------------------
    # شبکه بالا X
    # -----------------------------------------

    if (
        top_x_diameter_mm
        and top_x_spacing_mm
    ):

        number_X = number_of_bars_in_direction(
            width_m,
            top_x_spacing_mm,
            cover_mm
        )

        add_rebar_detail(

            details,

            top_x_diameter_mm,

            [usable_L]
            * number_X,

            "رادیه - شبکه بالا X",

            lap_percent
        )

    # -----------------------------------------
    # شبکه بالا Y
    # -----------------------------------------

    if (
        top_y_diameter_mm
        and top_y_spacing_mm
    ):

        number_Y = number_of_bars_in_direction(
            length_m,
            top_y_spacing_mm,
            cover_mm
        )

        add_rebar_detail(

            details,

            top_y_diameter_mm,

            [usable_W]
            * number_Y,

            "رادیه - شبکه بالا Y",

            lap_percent
        )

    return _foundation_result(

        lean_concrete,

        structural_concrete,

        details,

        raft_concrete_m3=
            structural_concrete
    )


# =========================================================
# جمع چند فونداسیون
# =========================================================

def total_foundation_result(
    results
):

    all_details = []

    for result in results:

        all_details.extend(
            result.get(
                "rebar_details",
                []
            )
        )

    final_details = finalize_rebar_details(
        all_details
    )

    return {

        "total_concrete_m3":
            sum(
                x.get(
                    "total_concrete_m3",
                    0
                )
                for x in results
            ),

        "total_rebar_kg":
            sum(
                x.get(
                    "total_rebar_kg",
                    0
                )
                for x in results
            ),

        "rebar_details":
            final_details,
    }


# =========================================================
# ستون مستطیلی
# =========================================================

def column_rectangular(

    count,
    width_m,
    depth_m,
    height_m,

    main_diameter_mm,
    main_count,

    stirrup_diameter_mm,
    stirrup_spacing_mm,

    cover_mm=40
):

    count = int(count)

    concrete = (
        count
        * width_m
        * depth_m
        * height_m
    )

    details = []

    usable_H = usable_length(
        height_m,
        cover_mm
    )

    add_rebar_detail(

        details,

        main_diameter_mm,

        [usable_H]
        * (
            int(main_count)
            * count
        ),

        "ستون - میلگرد طولی"
    )

    stirrup_count = (
        number_of_bars_in_direction(
            height_m,
            stirrup_spacing_mm,
            cover_mm
        )
    )

    stirrup_length = (
        2
        * (
            usable_length(
                width_m,
                cover_mm
            )
            +
            usable_length(
                depth_m,
                cover_mm
            )
        )
    )

    add_rebar_detail(

        details,

        stirrup_diameter_mm,

        [stirrup_length]
        * (
            stirrup_count
            * count
        ),

        "ستون - خاموت"
    )

    return {

        "type":
            "column_rectangular",

        "count":
            count,

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            finalize_rebar_details(
                details
            ),

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in finalize_rebar_details(
                    details
                )
            )
    }


# =========================================================
# ستون گرد
# =========================================================

def column_round(

    count,
    diameter_m,
    height_m,

    main_diameter_mm,
    main_count,

    stirrup_diameter_mm,
    stirrup_spacing_mm,

    cover_mm=40
):

    count = int(count)

    concrete = (
        count
        * math.pi
        * diameter_m ** 2
        / 4
        * height_m
    )

    details = []

    usable_H = usable_length(
        height_m,
        cover_mm
    )

    add_rebar_detail(

        details,

        main_diameter_mm,

        [usable_H]
        * (
            int(main_count)
            * count
        ),

        "ستون گرد - طولی"
    )

    ring_length = (
        math.pi
        * max(
            diameter_m
            - 2 * cover_mm / 1000,
            0
        )
    )

    ring_count = (
        number_of_bars_in_direction(
            height_m,
            stirrup_spacing_mm,
            cover_mm
        )
    )

    add_rebar_detail(

        details,

        stirrup_diameter_mm,

        [ring_length]
        * (
            ring_count
            * count
        ),

        "ستون گرد - خاموت حلقوی"
    )

    final = finalize_rebar_details(
        details
    )

    return {

        "type":
            "column_round",

        "count":
            count,

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            final,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            )
    }


# =========================================================
# تیر
# =========================================================

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

    cover_mm=40
):

    count = int(count)

    concrete = (
        count
        * length_m
        * width_m
        * height_m
    )

    details = []

    usable_L = usable_length(
        length_m,
        cover_mm
    )

    add_rebar_detail(

        details,

        main_diameter_mm,

        [usable_L]
        * (
            int(main_bottom_count)
            * count
        ),

        "تیر - طولی پایین"
    )

    add_rebar_detail(

        details,

        main_diameter_mm,

        [usable_L]
        * (
            int(main_top_count)
            * count
        ),

        "تیر - طولی بالا"
    )

    stirrup_count = (
        number_of_bars_in_direction(
            length_m,
            stirrup_spacing_mm,
            cover_mm
        )
    )

    stirrup_length = (
        2
        * (
            usable_length(
                width_m,
                cover_mm
            )
            +
            usable_length(
                height_m,
                cover_mm
            )
        )
    )

    add_rebar_detail(

        details,

        stirrup_diameter_mm,

        [stirrup_length]
        * (
            stirrup_count
            * count
        ),

        "تیر - خاموت"
    )

    final = finalize_rebar_details(
        details
    )

    return {

        "type":
            "beam",

        "count":
            count,

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            final,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            )
    }


# =========================================================
# شناژ / کلاف
# =========================================================

def tie_beam(

    count,
    length_m,
    width_m,
    height_m,

    main_diameter_mm,
    main_count,

    stirrup_diameter_mm,
    stirrup_spacing_mm,

    cover_mm=40
):

    return beam(

        count,

        length_m,
        width_m,
        height_m,

        main_diameter_mm,

        main_count,
        main_count,

        stirrup_diameter_mm,
        stirrup_spacing_mm,

        cover_mm
    )


# =========================================================
# دیوار
# =========================================================

def wall_concrete(

    length_m,
    height_m,
    thickness_m,

    vertical_diameter_mm,
    vertical_spacing_mm,

    horizontal_diameter_mm,
    horizontal_spacing_mm,

    cover_mm=40
):

    concrete = (
        length_m
        * height_m
        * thickness_m
    )

    details = []

    usable_H = usable_length(
        height_m,
        cover_mm
    )

    usable_L = usable_length(
        length_m,
        cover_mm
    )

    vertical_count = (
        number_of_bars_in_direction(
            length_m,
            vertical_spacing_mm,
            cover_mm
        )
    )

    horizontal_count = (
        number_of_bars_in_direction(
            height_m,
            horizontal_spacing_mm,
            cover_mm
        )
    )

    add_rebar_detail(

        details,

        vertical_diameter_mm,

        [usable_H]
        * vertical_count,

        "دیوار - قائم"
    )

    add_rebar_detail(

        details,

        horizontal_diameter_mm,

        [usable_L]
        * horizontal_count,

        "دیوار - افقی"
    )

    final = finalize_rebar_details(
        details
    )

    return {

        "type":
            "wall",

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            final,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            )
    }


# =========================================================
# راه پله
# =========================================================

def stair_slab(

    length_m,
    width_m,
    thickness_m,

    main_diameter_mm,
    main_spacing_mm,

    distribution_diameter_mm,
    distribution_spacing_mm,

    steps=0,
    step_riser=0,
    step_tread=0
):

    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    usable_L = usable_length(
        length_m,
        40
    )

    usable_W = usable_length(
        width_m,
        40
    )

    main_count = (
        number_of_bars_in_direction(
            width_m,
            main_spacing_mm,
            40
        )
    )

    distribution_count = (
        number_of_bars_in_direction(
            length_m,
            distribution_spacing_mm,
            40
        )
    )

    add_rebar_detail(

        details,

        main_diameter_mm,

        [usable_L]
        * main_count,

        "راه‌پله - اصلی"
    )

    add_rebar_detail(

        details,

        distribution_diameter_mm,

        [usable_W]
        * distribution_count,

        "راه‌پله - توزیعی"
    )

    # حجم تقریبی پله‌ها در صورت ورود ابعاد
    if (
        steps
        and step_riser
        and step_tread
    ):

        concrete += (
            steps
            * step_riser
            * step_tread
            * width_m
        )

    final = finalize_rebar_details(
        details
    )

    return {

        "type":
            "stair",

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            final,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            )
    }


# =========================================================
# ضرایب بتن سقف
# =========================================================

ROOF_CONCRETE_COEFFICIENTS = {

    "تیرچه یونولیتی":
        0.18,

    "تیرچه سفالی":
        0.20,

    "تیرچه دوبل":
        0.23,

    "کرومیت":
        0.18,

    "کامپوزیت":
        0.15,

    "عرشه فولادی":
        0.15,

    "دال بتنی":
        0.20,

    "وافل":
        0.20,
}


def roof_slab(

    roof_type,
    area_m2,
    rebar_kg_per_m2=0
):

    coefficient = (
        ROOF_CONCRETE_COEFFICIENTS[
            roof_type
        ]
    )

    concrete = (
        area_m2
        * coefficient
    )

    return {

        "type":
            "roof",

        "roof_type":
            roof_type,

        "area":
            area_m2,

        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "rebar_details":
            [],

        "total_rebar_kg":
            area_m2
            * rebar_kg_per_m2
    }
