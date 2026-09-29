import math

REBAR_WEIGHT = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.208,
    16: 1.578,
    18: 2.000,
    20: 2.469,
    22: 2.984,
    25: 3.858,
    28: 4.830,
    32: 6.313,
}


# =========================================================
# BASIC REBAR FUNCTIONS
# =========================================================

def rebar_weight(length_m, diameter_mm):
    """
    Weight of rebar based on actual length.
    """
    if length_m <= 0 or diameter_mm <= 0:
        return 0.0

    if diameter_mm in REBAR_WEIGHT:
        return length_m * REBAR_WEIGHT[diameter_mm]

    # Standard formula: d² / 162
    return length_m * (diameter_mm ** 2) / 162


def bars_12m(length_m):
    """
    Simple theoretical number of 12m bars.
    Kept for compatibility.
    """
    if length_m <= 0:
        return 0

    return math.ceil(length_m / 12)


def number_of_bars_in_direction(length_m, spacing_mm):
    """
    Number of bars required along a direction.
    """
    if length_m <= 0 or spacing_mm <= 0:
        return 0

    return math.ceil((length_m * 1000) / spacing_mm) + 1


def usable_length(length_m, cover_mm=50):
    """
    Clear usable dimension after subtracting cover from both sides.
    """
    value = length_m - (2 * cover_mm / 1000)

    if value < 0:
        return 0

    return value


def bar_length_with_lap(
    length_m,
    lap_percent=0
):
    """
    Adds lap allowance only when explicitly requested.
    """
    if length_m <= 0:
        return 0

    if lap_percent <= 0:
        return length_m

    return length_m * (1 + lap_percent / 100)


# =========================================================
# CUTTING / 12M BAR OPTIMIZATION
# =========================================================

def optimize_12m_bars(piece_lengths):
    """
    Simple First-Fit Decreasing optimization.

    Example:
        [5.2, 4.8, 6.0, 6.0]
    tries to place pieces into 12m stock bars
    with minimum unused length.

    Returns:
        {
            "stock_bars": number,
            "waste_m": total waste,
            "plans": [
                {
                    "stock_length_m": 12,
                    "pieces": [...],
                    "used_m": ...,
                    "waste_m": ...
                }
            ]
        }
    """

    pieces = [
        float(x)
        for x in piece_lengths
        if x is not None and x > 0
    ]

    if not pieces:
        return {
            "stock_bars": 0,
            "waste_m": 0.0,
            "plans": []
        }

    # Longest pieces first
    pieces.sort(reverse=True)

    stocks = []

    for piece in pieces:

        placed = False

        # Best-fit:
        # place the piece in the stock bar with
        # the smallest remaining space that can accept it.
        best_index = None
        best_remaining = None

        for i, stock in enumerate(stocks):

            remaining = 12.0 - stock["used_m"]

            if piece <= remaining + 1e-9:

                after = remaining - piece

                if best_remaining is None or after < best_remaining:
                    best_remaining = after
                    best_index = i

        if best_index is not None:

            stock = stocks[best_index]
            stock["pieces"].append(piece)
            stock["used_m"] += piece
            stock["waste_m"] = 12.0 - stock["used_m"]

            placed = True

        if not placed:

            stocks.append({
                "stock_length_m": 12.0,
                "pieces": [piece],
                "used_m": piece,
                "waste_m": 12.0 - piece
            })

    total_waste = sum(x["waste_m"] for x in stocks)

    return {
        "stock_bars": len(stocks),
        "waste_m": total_waste,
        "plans": stocks
    }


def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):
    """
    Creates a detailed rebar record.

    Each physical bar is represented as one piece.
    """

    if not piece_lengths:
        return None

    final_lengths = []

    for length in piece_lengths:

        if length <= 0:
            continue

        final_length = bar_length_with_lap(
            length,
            lap_percent
        )

        final_lengths.append(final_length)

    if not final_lengths:
        return None

    total_length = sum(final_lengths)

    weight = rebar_weight(
        total_length,
        diameter_mm
    )

    optimization = optimize_12m_bars(
        final_lengths
    )

    return {
        "diameter_mm": int(diameter_mm),
        "length_m": total_length,
        "weight_kg": weight,

        # Real optimized number of stock bars
        "bars_12m": optimization["stock_bars"],

        # Additional information
        "piece_count": len(final_lengths),
        "piece_lengths_m": final_lengths,
        "waste_m": optimization["waste_m"],
        "cut_plan": optimization["plans"],
        "description": description,
    }


def add_rebar_detail(
    details,
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0
):
    """
    Adds one reinforcement group to rebar_details.
    """

    if not piece_lengths:
        return

    item = make_rebar_detail(
        diameter_mm=diameter_mm,
        piece_lengths=piece_lengths,
        description=description,
        lap_percent=lap_percent
    )

    if item:
        details.append(item)


def finalize_rebar_details(details):
    """
    Combines all reinforcement groups having the same diameter.

    The Telegram bot already expects:
        diameter_mm
        length_m
        weight_kg
        bars_12m
    """

    if not details:
        return []

    grouped = {}

    for item in details:

        diameter = item["diameter_mm"]

        if diameter not in grouped:

            grouped[diameter] = {
                "diameter_mm": diameter,
                "length_m": 0.0,
                "weight_kg": 0.0,
                "bars_12m": 0,
                "piece_count": 0,
                "waste_m": 0.0,
                "piece_lengths_m": [],
                "cut_plan": [],
                "description": "",
            }

        grouped[diameter]["length_m"] += item["length_m"]
        grouped[diameter]["weight_kg"] += item["weight_kg"]
        grouped[diameter]["piece_count"] += item.get(
            "piece_count",
            0
        )
        grouped[diameter]["waste_m"] += item.get(
            "waste_m",
            0
        )

        grouped[diameter]["piece_lengths_m"].extend(
            item.get("piece_lengths_m", [])
        )

        if item.get("description"):
            if grouped[diameter]["description"]:
                grouped[diameter]["description"] += " + "

            grouped[diameter]["description"] += item["description"]

    # Re-optimize all pieces of each diameter together.
    # This is more realistic because different reinforcement
    # groups of the same diameter can share 12m stock bars.
    for diameter, item in grouped.items():

        optimization = optimize_12m_bars(
            item["piece_lengths_m"]
        )

        item["bars_12m"] = optimization["stock_bars"]
        item["waste_m"] = optimization["waste_m"]
        item["cut_plan"] = optimization["plans"]

    return sorted(
        grouped.values(),
        key=lambda x: x["diameter_mm"]
    )


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

    # -----------------------------------------------------
    # CONCRETE
    # -----------------------------------------------------

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

    lean_concrete = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    total_concrete = (
        footing_concrete
        + pedestal_concrete
    )

    # -----------------------------------------------------
    # REBAR DETAILS
    # -----------------------------------------------------

    details = []

    # Usable dimensions after cover
    usable_length = usable_length(
        length_m,
        cover_mm
    )

    usable_width = usable_length(
        width_m,
        cover_mm
    )

    # -----------------------------------------------------
    # BOTTOM MESH
    # -----------------------------------------------------

    if bottom_diameter_mm and bottom_spacing_mm:

        # Bars running in X direction
        x_count = number_of_bars_in_direction(
            width_m - (2 * cover_mm / 1000),
            bottom_spacing_mm
        )

        # Bars running in Y direction
        y_count = number_of_bars_in_direction(
            length_m - (2 * cover_mm / 1000),
            bottom_spacing_mm
        )

        x_pieces = [
            usable_length
            for _ in range(x_count * count)
        ]

        y_pieces = [
            usable_width
            for _ in range(y_count * count)
        ]

        add_rebar_detail(
            details,
            bottom_diameter_mm,
            x_pieces,
            "پی منفرد - پایین X",
            lap_percent
        )

        add_rebar_detail(
            details,
            bottom_diameter_mm,
            y_pieces,
            "پی منفرد - پایین Y",
            lap_percent
        )

    # -----------------------------------------------------
    # TOP MESH
    # -----------------------------------------------------

    if (
        top_diameter_mm
        and top_spacing_mm
    ):

        x_count = number_of_bars_in_direction(
            width_m - (2 * cover_mm / 1000),
            top_spacing_mm
        )

        y_count = number_of_bars_in_direction(
            length_m - (2 * cover_mm / 1000),
            top_spacing_mm
        )

        x_pieces = [
            usable_length
            for _ in range(x_count * count)
        ]

        y_pieces = [
            usable_width
            for _ in range(y_count * count)
        ]

        add_rebar_detail(
            details,
            top_diameter_mm,
            x_pieces,
            "پی منفرد - بالا X",
            lap_percent
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            y_pieces,
            "پی منفرد - بالا Y",
            lap_percent
        )

    details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        x["weight_kg"]
        for x in details
    )

    return {
        "lean_concrete_m3": lean_concrete,
        "footing_concrete_m3": footing_concrete,
        "pedestal_concrete_m3": pedestal_concrete,
        "total_concrete_m3": total_concrete,

        "rebar_details": details,

        "bottom_rebar_weight_kg": sum(
            x["weight_kg"]
            for x in details
        ),

        "top_rebar_weight_kg": 0,
        "total_rebar_kg": total_rebar,
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

    # -----------------------------------------------------
    # CONCRETE
    # -----------------------------------------------------

    footing_concrete = (
        strip_count
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    lean_concrete = (
        strip_count
        * lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    details = []

    usable_length = usable_length(
        strip_length_m,
        cover_mm
    )

    usable_width = usable_length(
        footing_width_m,
        cover_mm
    )

    # -----------------------------------------------------
    # BOTTOM LONGITUDINAL
    # -----------------------------------------------------

    if (
        longitudinal_diameter_mm
        and longitudinal_count
    ):

        pieces = [
            usable_length
            for _ in range(
                strip_count
                * int(longitudinal_count)
            )
        ]

        add_rebar_detail(
            details,
            longitudinal_diameter_mm,
            pieces,
            "پی نواری - پایین طولی",
            lap_percent
        )

    # -----------------------------------------------------
    # BOTTOM TRANSVERSE
    # -----------------------------------------------------

    if (
        transverse_diameter_mm
        and transverse_spacing_mm
    ):

        transverse_count = number_of_bars_in_direction(
            strip_length_m - (2 * cover_mm / 1000),
            transverse_spacing_mm
        )

        pieces = [
            usable_width
            for _ in range(
                strip_count
                * transverse_count
            )
        ]

        add_rebar_detail(
            details,
            transverse_diameter_mm,
            pieces,
            "پی نواری - پایین عرضی",
            lap_percent
        )

    # -----------------------------------------------------
    # TOP LONGITUDINAL
    # -----------------------------------------------------

    if (
        top_longitudinal_diameter_mm
        and top_longitudinal_count
    ):

        pieces = [
            usable_length
            for _ in range(
                strip_count
                * int(top_longitudinal_count)
            )
        ]

        add_rebar_detail(
            details,
            top_longitudinal_diameter_mm,
            pieces,
            "پی نواری - بالا طولی",
            lap_percent
        )

    # -----------------------------------------------------
    # TOP TRANSVERSE
    # -----------------------------------------------------

    if (
        top_transverse_diameter_mm
        and top_transverse_spacing_mm
    ):

        transverse_count = number_of_bars_in_direction(
            strip_length_m - (2 * cover_mm / 1000),
            top_transverse_spacing_mm
        )

        pieces = [
            usable_width
            for _ in range(
                strip_count
                * transverse_count
            )
        ]

        add_rebar_detail(
            details,
            top_transverse_diameter_mm,
            pieces,
            "پی نواری - بالا عرضی",
            lap_percent
        )

    details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        x["weight_kg"]
        for x in details
    )

    return {
        "lean_concrete_m3": lean_concrete,
        "footing_concrete_m3": footing_concrete,

        "bottom_rebar_length_m": sum(
            x["length_m"]
            for x in details
        ),

        "top_rebar_length_m": 0,

        "bottom_rebar_weight_kg": total_rebar,
        "top_rebar_weight_kg": 0,

        "rebar_details": details,

        "total_rebar_kg": total_rebar,
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
    # CONCRETE
    # -----------------------------------------------------

    raft_concrete = (
        length_m
        * width_m
        * thickness_m
    )

    lean_concrete = (
        lean_length_m
        * lean_width_m
        * lean_thickness_m
    )

    details = []

    usable_length_m = usable_length(
        length_m,
        cover_mm
    )

    usable_width_m = usable_length(
        width_m,
        cover_mm
    )

    # -----------------------------------------------------
    # BOTTOM X
    # -----------------------------------------------------

    if (
        bottom_x_diameter_mm
        and bottom_x_spacing_mm
    ):

        count_x = number_of_bars_in_direction(
            width_m - (2 * cover_mm / 1000),
            bottom_x_spacing_mm
        )

        pieces = [
            usable_length_m
            for _ in range(count_x)
        ]

        add_rebar_detail(
            details,
            bottom_x_diameter_mm,
            pieces,
            "رادیه - پایین X",
            lap_percent
        )

    # -----------------------------------------------------
    # BOTTOM Y
    # -----------------------------------------------------

    if (
        bottom_y_diameter_mm
        and bottom_y_spacing_mm
    ):

        count_y = number_of_bars_in_direction(
            length_m - (2 * cover_mm / 1000),
            bottom_y_spacing_mm
        )

        pieces = [
            usable_width_m
            for _ in range(count_y)
        ]

        add_rebar_detail(
            details,
            bottom_y_diameter_mm,
            pieces,
            "رادیه - پایین Y",
            lap_percent
        )

    # -----------------------------------------------------
    # TOP X
    # -----------------------------------------------------

    if (
        top_x_diameter_mm
        and top_x_spacing_mm
    ):

        count_x = number_of_bars_in_direction(
            width_m - (2 * cover_mm / 1000),
            top_x_spacing_mm
        )

        pieces = [
            usable_length_m
            for _ in range(count_x)
        ]

        add_rebar_detail(
            details,
            top_x_diameter_mm,
            pieces,
            "رادیه - بالا X",
            lap_percent
        )

    # -----------------------------------------------------
    # TOP Y
    # -----------------------------------------------------

    if (
        top_y_diameter_mm
        and top_y_spacing_mm
    ):

        count_y = number_of_bars_in_direction(
            length_m - (2 * cover_mm / 1000),
            top_y_spacing_mm
        )

        pieces = [
            usable_width_m
            for _ in range(count_y)
        ]

        add_rebar_detail(
            details,
            top_y_diameter_mm,
            pieces,
            "رادیه - بالا Y",
            lap_percent
        )

    details = finalize_rebar_details(
        details
    )

    total_rebar = sum(
        x["weight_kg"]
        for x in details
    )

    return {
        "lean_concrete_m3": lean_concrete,
        "raft_concrete_m3": raft_concrete,

        "bottom_rebar_length_m": sum(
            x["length_m"]
            for x in details
        ),

        "top_rebar_length_m": 0,

        "bottom_rebar_weight_kg": total_rebar,
        "top_rebar_weight_kg": 0,

        "rebar_details": details,

        "total_rebar_kg": total_rebar,
    }


# =========================================================
# TOTAL FOUNDATION RESULT
# =========================================================

def total_foundation_result(results):
    """
    Combines multiple foundation results.
    """

    total_concrete = 0.0
    total_rebar = 0.0

    all_details = []

    for result in results:

        total_concrete += result.get(
            "total_concrete_m3",
            result.get(
                "footing_concrete_m3",
                result.get(
                    "raft_concrete_m3",
                    0
                )
            )
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

    all_details = finalize_rebar_details(
        all_details
    )

    total_rebar = sum(
        x["weight_kg"]
        for x in all_details
    )

    return {
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_rebar,
        "rebar_details": all_details,
    }
