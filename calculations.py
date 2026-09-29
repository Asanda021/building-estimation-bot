import math


# =========================================================
# وزن واحد میلگرد - kg/m
# =========================================================

REBAR_WEIGHT = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.21,
    16: 1.58,
    18: 2.00,
    20: 2.47,
    22: 2.98,
    25: 3.85,
    28: 4.83,
    32: 6.31,
}


# =========================================================
# Basic Rebar Functions
# =========================================================

def rebar_weight(length_m, diameter_mm):

    diameter_mm = int(diameter_mm)

    if diameter_mm in REBAR_WEIGHT:
        return length_m * REBAR_WEIGHT[diameter_mm]

    # Formula for uncommon diameters
    return length_m * (diameter_mm ** 2) / 162


def bars_12m(length_m):

    if length_m <= 0:
        return 0

    return math.ceil(length_m / 12)


def number_of_bars_in_direction(
    usable_length_m,
    spacing_mm
):

    if usable_length_m <= 0 or spacing_mm <= 0:
        return 0

    spacing_m = spacing_mm / 1000

    return math.floor(
        usable_length_m / spacing_m
    ) + 1


def usable_length(
    total_length_m,
    cover_mm=50
):

    cover_m = cover_mm / 1000

    return max(
        total_length_m - (2 * cover_m),
        0
    )


def bar_length_with_lap(
    length_m,
    lap_percent=0
):

    if length_m <= 0:
        return 0

    return length_m * (
        1 + lap_percent / 100
    )


# =========================================================
# 12m Stock Bar Optimization
# =========================================================

def optimize_12m_bars(
    piece_lengths
):

    clean_lengths = [
        float(x)
        for x in piece_lengths
        if x is not None and float(x) > 0
    ]

    if not clean_lengths:

        return {
            "stock_bars": 0,
            "waste_m": 0,
            "plans": []
        }

    # -----------------------------------------------------
    # هیچ قطعه‌ای نباید از شاخه 12 متری بزرگ‌تر باشد
    # -----------------------------------------------------

    for length in clean_lengths:

        if length > 12.000001:

            raise ValueError(
                f"Bar piece length {length:.2f} m "
                f"is longer than 12 m."
            )

    # -----------------------------------------------------
    # First Fit Decreasing
    # -----------------------------------------------------

    sorted_lengths = sorted(
        clean_lengths,
        reverse=True
    )

    bars = []

    for piece in sorted_lengths:

        placed = False

        for bar in bars:

            if (
                bar["used_m"] + piece
                <= 12.000001
            ):

                bar["pieces"].append(
                    piece
                )

                bar["used_m"] += piece

                bar["waste_m"] = (
                    12
                    - bar["used_m"]
                )

                placed = True

                break

        if not placed:

            bars.append({

                "pieces": [piece],

                "used_m": piece,

                "waste_m": 12 - piece

            })

    total_waste = sum(
        bar["waste_m"]
        for bar in bars
    )

    return {

        "stock_bars": len(bars),

        "waste_m": total_waste,

        "plans": bars
    }


# =========================================================
# Rebar Detail
# =========================================================

def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):

    processed_lengths = []

    for length in piece_lengths:

        length = float(length)

        if length <= 0:
            continue

        length = bar_length_with_lap(
            length,
            lap_percent
        )

        processed_lengths.append(
            length
        )

    total_length = sum(
        processed_lengths
    )

    weight = rebar_weight(
        total_length,
        diameter_mm
    )

    optimization = optimize_12m_bars(
        processed_lengths
    )

    return {

        "diameter_mm":
            int(diameter_mm),

        "length_m":
            total_length,

        "weight_kg":
            weight,

        "bars_12m":
            optimization["stock_bars"],

        "piece_count":
            len(processed_lengths),

        "piece_lengths_m":
            processed_lengths,

        "waste_m":
            optimization["waste_m"],

        "cut_plan":
            optimization["plans"],

        "description":
            description
    }


def add_rebar_detail(
    details,
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):

    if not piece_lengths:
        return

    new_detail = make_rebar_detail(
        diameter_mm,
        piece_lengths,
        description,
        lap_percent
    )

    details.append(
        new_detail
    )


def finalize_rebar_details(
    details
):

    if not details:
        return []

    # -----------------------------------------------------
    # تفکیک بر اساس قطر
    # -----------------------------------------------------

    grouped = {}

    for detail in details:

        diameter = int(
            detail["diameter_mm"]
        )

        if diameter not in grouped:

            grouped[diameter] = []

        grouped[diameter].extend(
            detail.get(
                "piece_lengths_m",
                []
            )
        )

    final_details = []

    for diameter in sorted(
        grouped.keys()
    ):

        pieces = grouped[diameter]

        optimization = optimize_12m_bars(
            pieces
        )

        total_length = sum(
            pieces
        )

        weight = rebar_weight(
            total_length,
            diameter
        )

        descriptions = []

        for detail in details:

            if (
                int(detail["diameter_mm"])
                == diameter
            ):

                description = detail.get(
                    "description",
                    ""
                )

                if (
                    description
                    and description not in descriptions
                ):

                    descriptions.append(
                        description
                    )

        final_details.append({

            "diameter_mm":
                diameter,

            "length_m":
                total_length,

            "weight_kg":
                weight,

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
                    descriptions
                )
        })

    return final_details


# =========================================================
# ISOLATED FOOTING
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
    pedestal_height_m=0
):

    count = int(count)

    # -----------------------------------------------------
    # Concrete
    # -----------------------------------------------------

    lean_concrete = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    footing_concrete = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    pedestal_concrete = (
        count
        * pedestal_length_m
        * pedestal_width_m
        * pedestal_height_m
    )

    # -----------------------------------------------------
    # Rebar Details
    # -----------------------------------------------------

    details = []

    # -----------------------------------------------------
    # Bottom Mesh - X
    # میلگردها در جهت طول پی
    # تعداد بر اساس عرض پی
    # -----------------------------------------------------

    usable_length_m = usable_length(
        length_m,
        cover_mm
    )

    usable_width_m = usable_length(
        width_m,
        cover_mm
    )

    bottom_x_count = number_of_bars_in_direction(
        usable_width_m,
        bottom_spacing_mm
    )

    bottom_x_piece_length = (
        usable_length_m
    )

    bottom_x_pieces = [
        bottom_x_piece_length
        for _ in range(
            bottom_x_count * count
        )
    ]

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        bottom_x_pieces,
        "پی منفرد - شبکه پایین X",
        lap_percent
    )

    # -----------------------------------------------------
    # Bottom Mesh - Y
    # -----------------------------------------------------

    bottom_y_count = number_of_bars_in_direction(
        usable_length_m,
        bottom_spacing_mm
    )

    bottom_y_piece_length = (
        usable_width_m
    )

    bottom_y_pieces = [
        bottom_y_piece_length
        for _ in range(
            bottom_y_count * count
        )
    ]

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        bottom_y_pieces,
        "پی منفرد - شبکه پایین Y",
        lap_percent
    )

    # -----------------------------------------------------
    # Top Mesh
    # -----------------------------------------------------

    if (
        top_diameter_mm
        and top_spacing_mm
        and top_diameter_mm > 0
        and top_spacing_mm > 0
    ):

        top_x_count = number_of_bars_in_direction(
            usable_width_m,
            top_spacing_mm
        )

        top_x_pieces = [
            usable_length_m
            for _ in range(
                top_x_count * count
            )
        ]

        add_rebar_detail(
            details,
            top_diameter_mm,
            top_x_pieces,
            "پی منفرد - شبکه بالا X",
            lap_percent
        )

        top_y_count = number_of_bars_in_direction(
            usable_length_m,
            top_spacing_mm
        )

        top_y_pieces = [
            usable_width_m
            for _ in range(
                top_y_count * count
            )
        ]

        add_rebar_detail(
            details,
            top_diameter_mm,
            top_y_pieces,
            "پی منفرد - شبکه بالا Y",
            lap_percent
        )

    # -----------------------------------------------------
    # Finalize
    # -----------------------------------------------------

    final_details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        item["weight_kg"]
        for item in final_details
    )

    return {

        "lean_concrete_m3":
            lean_concrete,

        "footing_concrete_m3":
            footing_concrete,

        "pedestal_concrete_m3":
            pedestal_concrete,

        "total_concrete_m3":
            lean_concrete
            + footing_concrete
            + pedestal_concrete,

        "bottom_rebar_weight_kg":
            sum(
                item["weight_kg"]
                for item in final_details
            ),

        "top_rebar_weight_kg":
            0,

        "total_rebar_kg":
            total_rebar,

        "rebar_details":
            final_details
    }


# =========================================================
# STRIP FOOTING
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
    lap_percent=0
):

    strip_count = int(
        strip_count
    )

    # -----------------------------------------------------
    # Concrete
    # -----------------------------------------------------

    footing_concrete = (
        strip_count
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    details = []

    # -----------------------------------------------------
    # Usable Dimensions
    # -----------------------------------------------------

    usable_strip_length_m = usable_length(
        strip_length_m,
        cover_mm
    )

    usable_width_m = usable_length(
        footing_width_m,
        cover_mm
    )

    # -----------------------------------------------------
    # Bottom Longitudinal
    # -----------------------------------------------------

    bottom_longitudinal_pieces = [
        usable_strip_length_m
        for _ in range(
            int(longitudinal_count)
            * strip_count
        )
    ]

    add_rebar_detail(
        details,
        longitudinal_diameter_mm,
        bottom_longitudinal_pieces,
        "پی نواری - طولی پایین",
        lap_percent
    )

    # -----------------------------------------------------
    # Bottom Transverse
    # -----------------------------------------------------

    transverse_count = number_of_bars_in_direction(
        usable_strip_length_m,
        transverse_spacing_mm
    )

    bottom_transverse_pieces = [
        usable_width_m
        for _ in range(
            transverse_count
            * strip_count
        )
    ]

    add_rebar_detail(
        details,
        transverse_diameter_mm,
        bottom_transverse_pieces,
        "پی نواری - عرضی پایین",
        lap_percent
    )

    # -----------------------------------------------------
    # Top Longitudinal
    # -----------------------------------------------------

    if (
        top_longitudinal_diameter_mm
        and top_longitudinal_count
        and top_longitudinal_diameter_mm > 0
        and top_longitudinal_count > 0
    ):

        top_longitudinal_pieces = [
            usable_strip_length_m
            for _ in range(
                int(top_longitudinal_count)
                * strip_count
            )
        ]

        add_rebar_detail(
            details,
            top_longitudinal_diameter_mm,
            top_longitudinal_pieces,
            "پی نواری - طولی بالا",
            lap_percent
        )

    # -----------------------------------------------------
    # Top Transverse
    # -----------------------------------------------------

    if (
        top_transverse_diameter_mm
        and top_transverse_spacing_mm
        and top_transverse_diameter_mm > 0
        and top_transverse_spacing_mm > 0
    ):

        top_transverse_count = (
            number_of_bars_in_direction(
                usable_strip_length_m,
                top_transverse_spacing_mm
            )
        )

        top_transverse_pieces = [
            usable_width_m
            for _ in range(
                top_transverse_count
                * strip_count
            )
        ]

        add_rebar_detail(
            details,
            top_transverse_diameter_mm,
            top_transverse_pieces,
            "پی نواری - عرضی بالا",
            lap_percent
        )

    # -----------------------------------------------------
    # Final
    # -----------------------------------------------------

    final_details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        item["weight_kg"]
        for item in final_details
    )

    return {

        "lean_concrete_m3":
            0,

        "footing_concrete_m3":
            footing_concrete,

        "total_concrete_m3":
            footing_concrete,

        "total_rebar_kg":
            total_rebar,

        "rebar_details":
            final_details
    }


# =========================================================
# RAFT FOUNDATION
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
    lap_percent=0
):

    # -----------------------------------------------------
    # Concrete
    # -----------------------------------------------------

    raft_concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    # -----------------------------------------------------
    # Usable Dimensions
    # -----------------------------------------------------

    usable_length_m = usable_length(
        length_m,
        cover_mm
    )

    usable_width_m = usable_length(
        width_m,
        cover_mm
    )

    # =====================================================
    # Bottom X
    # =====================================================

    bottom_x_count = number_of_bars_in_direction(
        usable_width_m,
        bottom_x_spacing_mm
    )

    bottom_x_pieces = [
        usable_length_m
        for _ in range(
            bottom_x_count
        )
    ]

    add_rebar_detail(
        details,
        bottom_x_diameter_mm,
        bottom_x_pieces,
        "رادیه - شبکه پایین X",
        lap_percent
    )

    # =====================================================
    # Bottom Y
    # =====================================================

    bottom_y_count = number_of_bars_in_direction(
        usable_length_m,
        bottom_y_spacing_mm
    )

    bottom_y_pieces = [
        usable_width_m
        for _ in range(
            bottom_y_count
        )
    ]

    add_rebar_detail(
        details,
        bottom_y_diameter_mm,
        bottom_y_pieces,
        "رادیه - شبکه پایین Y",
        lap_percent
    )

    # =====================================================
    # Top X
    # =====================================================

    if (
        top_x_diameter_mm
        and top_x_spacing_mm
        and top_x_diameter_mm > 0
        and top_x_spacing_mm > 0
    ):

        top_x_count = number_of_bars_in_direction(
            usable_width_m,
            top_x_spacing_mm
        )

        top_x_pieces = [
            usable_length_m
            for _ in range(
                top_x_count
            )
        ]

        add_rebar_detail(
            details,
            top_x_diameter_mm,
            top_x_pieces,
            "رادیه - شبکه بالا X",
            lap_percent
        )

    # =====================================================
    # Top Y
    # =====================================================

    if (
        top_y_diameter_mm
        and top_y_spacing_mm
        and top_y_diameter_mm > 0
        and top_y_spacing_mm > 0
    ):

        top_y_count = number_of_bars_in_direction(
            usable_length_m,
            top_y_spacing_mm
        )

        top_y_pieces = [
            usable_width_m
            for _ in range(
                top_y_count
            )
        ]

        add_rebar_detail(
            details,
            top_y_diameter_mm,
            top_y_pieces,
            "رادیه - شبکه بالا Y",
            lap_percent
        )

    # -----------------------------------------------------
    # Final
    # -----------------------------------------------------

    final_details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        item["weight_kg"]
        for item in final_details
    )

    return {

        "lean_concrete_m3":
            0,

        "raft_concrete_m3":
            raft_concrete,

        "total_concrete_m3":
            raft_concrete,

        "total_rebar_kg":
            total_rebar,

        "rebar_details":
            final_details
    }


# =========================================================
# Total Foundation Result
# =========================================================

def total_foundation_result(
    results
):

    total_concrete = 0
    total_rebar = 0

    all_details = []

    for result in results:

        total_concrete += result.get(
            "total_concrete_m3",
            0
        )

        total_rebar += result.get(
            "total_rebar_kg",
            0
        )

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
            total_concrete,

        "total_rebar_kg":
            total_rebar,

        "rebar_details":
            final_details
    }
