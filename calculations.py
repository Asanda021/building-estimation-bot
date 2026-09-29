import math

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
    36: 7.99,
}

STOCK_LENGTH_M = 12.0


def rebar_weight(length_m, diameter_mm):
    d = int(diameter_mm)
    return length_m * REBAR_WEIGHT.get(d, d * d / 162)


def rebar_area(diameter_mm):
    """مساحت سطح مقطع یک میلگرد بر حسب mm²"""
    d = float(diameter_mm)
    return math.pi * d * d / 4.0


def equivalent_rebar_count(current_count, current_diameter, replacement_diameter):
    """
    معادل‌سازی سریع میلگرد بر اساس سطح مقطع فولاد.

    مثال:
    3Φ20 → 2Φ25
    """

    current_count = int(current_count)
    current_diameter = int(current_diameter)
    replacement_diameter = int(replacement_diameter)

    if current_count <= 0:
        raise ValueError("Current rebar count must be greater than zero.")

    if current_diameter <= 0 or replacement_diameter <= 0:
        raise ValueError("Rebar diameter must be greater than zero.")

    current_area = current_count * rebar_area(current_diameter)
    replacement_area_each = rebar_area(replacement_diameter)

    required_count = math.ceil(current_area / replacement_area_each)

    provided_area = required_count * replacement_area_each

    excess_percent = (
        (provided_area - current_area) / current_area * 100
        if current_area > 0
        else 0
    )

    return {
        "current_count": current_count,
        "current_diameter": current_diameter,
        "replacement_diameter": replacement_diameter,
        "current_area_mm2": current_area,
        "replacement_area_each_mm2": replacement_area_each,
        "required_count": required_count,
        "provided_area_mm2": provided_area,
        "excess_percent": excess_percent,
        "area_equivalent": provided_area >= current_area,
    }


def bars_12m(length_m):
    return 0 if length_m <= 0 else math.ceil(length_m / STOCK_LENGTH_M)


def number_of_bars_in_direction(usable_length_m, spacing_mm):
    if usable_length_m <= 0 or spacing_mm <= 0:
        return 0

    return math.floor(
        usable_length_m / (spacing_mm / 1000)
    ) + 1


def usable_length(total_length_m, cover_mm=50):
    return max(
        total_length_m - 2 * cover_mm / 1000,
        0
    )


def bar_length_with_lap(length_m, lap_percent=0):
    if length_m <= 0:
        return 0

    return length_m * (1 + lap_percent / 100)


def optimize_12m_bars(piece_lengths):
    clean = sorted(
        [
            float(x)
            for x in piece_lengths
            if x is not None and float(x) > 0
        ],
        reverse=True,
    )

    for x in clean:
        if x > STOCK_LENGTH_M + 0.000001:
            raise ValueError(
                f"Bar piece length {x:.2f} m is longer than 12 m."
            )

    bars = []

    for piece in clean:
        placed = False

        for bar in bars:
            if bar["used_m"] + piece <= STOCK_LENGTH_M + 0.000001:
                bar["pieces"].append(piece)
                bar["used_m"] += piece

                # پرت مستقیماً از 12 - مصرف محاسبه می‌شود
                bar["waste_m"] = STOCK_LENGTH_M - bar["used_m"]

                placed = True
                break

        if not placed:
            bars.append(
                {
                    "pieces": [piece],
                    "used_m": piece,
                    "waste_m": STOCK_LENGTH_M - piece,
                }
            )

    return {
        "stock_bars": len(bars),
        "waste_m": sum(
            STOCK_LENGTH_M - float(x["used_m"])
            for x in bars
        ),
        "plans": bars,
    }


def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0,
):
    pieces = [
        bar_length_with_lap(float(x), lap_percent)
        for x in piece_lengths
        if float(x) > 0
    ]

    opt = optimize_12m_bars(pieces)
    total = sum(pieces)

    return {
        "diameter_mm": int(diameter_mm),
        "length_m": total,
        "weight_kg": rebar_weight(total, diameter_mm),
        "bars_12m": opt["stock_bars"],
        "piece_count": len(pieces),
        "piece_lengths_m": pieces,
        "waste_m": opt["waste_m"],
        "cut_plan": opt["plans"],
        "description": description,
    }


def add_rebar_detail(
    details,
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0,
):
    if piece_lengths:
        details.append(
            make_rebar_detail(
                diameter_mm,
                piece_lengths,
                description,
                lap_percent,
            )
        )


def finalize_rebar_details(details):
    grouped = {}
    desc = {}

    for d in details:
        dia = int(d["diameter_mm"])

        grouped.setdefault(dia, []).extend(
            d.get("piece_lengths_m", [])
        )

        if d.get("description"):
            desc.setdefault(dia, [])

            if d["description"] not in desc[dia]:
                desc[dia].append(d["description"])

    out = []

    for dia in sorted(grouped):
        pieces = grouped[dia]
        opt = optimize_12m_bars(pieces)
        total = sum(pieces)

        out.append(
            {
                "diameter_mm": dia,
                "length_m": total,
                "weight_kg": rebar_weight(total, dia),
                "bars_12m": opt["stock_bars"],
                "piece_count": len(pieces),
                "piece_lengths_m": pieces,
                "waste_m": opt["waste_m"],
                "cut_plan": opt["plans"],
                "description": " + ".join(
                    desc.get(dia, [])
                ),
            }
        )

    return out


# =========================================================
# FOUNDATION
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

    lean = (
        count
        * lean_concrete_length_m
        * lean_concrete_width_m
        * lean_concrete_thickness_m
    )

    footing = (
        count
        * length_m
        * width_m
        * thickness_m
    )

    pedestal = (
        count
        * pedestal_length_m
        * pedestal_width_m
        * pedestal_height_m
    )

    details = []

    L = usable_length(length_m, cover_mm)
    W = usable_length(width_m, cover_mm)

    nx = number_of_bars_in_direction(
        W,
        bottom_spacing_mm,
    )

    ny = number_of_bars_in_direction(
        L,
        bottom_spacing_mm,
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [L] * (nx * count),
        "پی منفرد - شبکه پایین X",
        lap_percent,
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [W] * (ny * count),
        "پی منفرد - شبکه پایین Y",
        lap_percent,
    )

    if (
        top_diameter_mm
        and top_spacing_mm
        and top_diameter_mm > 0
        and top_spacing_mm > 0
    ):
        nx = number_of_bars_in_direction(
            W,
            top_spacing_mm,
        )

        ny = number_of_bars_in_direction(
            L,
            top_spacing_mm,
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [L] * (nx * count),
            "پی منفرد - شبکه بالا X",
            lap_percent,
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [W] * (ny * count),
            "پی منفرد - شبکه بالا Y",
            lap_percent,
        )

    final = finalize_rebar_details(details)

    total_rebar = sum(
        x["weight_kg"]
        for x in final
    )

    return {
        "lean_concrete_m3": lean,
        "footing_concrete_m3": footing,
        "pedestal_concrete_m3": pedestal,
        "total_concrete_m3": (
            lean + footing + pedestal
        ),
        "bottom_rebar_weight_kg": total_rebar,
        "top_rebar_weight_kg": 0,
        "total_rebar_kg": total_rebar,
        "rebar_details": final,
    }


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
    n = int(strip_count)

    concrete = (
        n
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    details = []

    L = usable_length(
        strip_length_m,
        cover_mm,
    )

    W = usable_length(
        footing_width_m,
        cover_mm,
    )

    add_rebar_detail(
        details,
        longitudinal_diameter_mm,
        [L] * (int(longitudinal_count) * n),
        "پی نواری - طولی پایین",
        lap_percent,
    )

    nc = number_of_bars_in_direction(
        L,
        transverse_spacing_mm,
    )

    add_rebar_detail(
        details,
        transverse_diameter_mm,
        [W] * (nc * n),
        "پی نواری - عرضی پایین",
        lap_percent,
    )

    if (
        top_longitudinal_diameter_mm
        and top_longitudinal_count
    ):
        add_rebar_detail(
            details,
            top_longitudinal_diameter_mm,
            [L] * (
                int(top_longitudinal_count) * n
            ),
            "پی نواری - طولی بالا",
            lap_percent,
        )

    if (
        top_transverse_diameter_mm
        and top_transverse_spacing_mm
    ):
        nc = number_of_bars_in_direction(
            L,
            top_transverse_spacing_mm,
        )

        add_rebar_detail(
            details,
            top_transverse_diameter_mm,
            [W] * (nc * n),
            "پی نواری - عرضی بالا",
            lap_percent,
        )

    final = finalize_rebar_details(details)

    return {
        "lean_concrete_m3": 0,
        "footing_concrete_m3": concrete,
        "total_concrete_m3": concrete,
        "total_rebar_kg": sum(
            x["weight_kg"]
            for x in final
        ),
        "rebar_details": final,
    }


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
    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    L = usable_length(
        length_m,
        cover_mm,
    )

    W = usable_length(
        width_m,
        cover_mm,
    )

    nx = number_of_bars_in_direction(
        W,
        bottom_x_spacing_mm,
    )

    ny = number_of_bars_in_direction(
        L,
        bottom_y_spacing_mm,
    )

    add_rebar_detail(
        details,
        bottom_x_diameter_mm,
        [L] * nx,
        "رادیه - شبکه پایین X",
        lap_percent,
    )

    add_rebar_detail(
        details,
        bottom_y_diameter_mm,
        [W] * ny,
        "رادیه - شبکه پایین Y",
        lap_percent,
    )

    if (
        top_x_diameter_mm
        and top_x_spacing_mm
    ):
        nx = number_of_bars_in_direction(
            W,
            top_x_spacing_mm,
        )

        add_rebar_detail(
            details,
            top_x_diameter_mm,
            [L] * nx,
            "رادیه - شبکه بالا X",
            lap_percent,
        )

    if (
        top_y_diameter_mm
        and top_y_spacing_mm
    ):
        ny = number_of_bars_in_direction(
            L,
            top_y_spacing_mm,
        )

        add_rebar_detail(
            details,
            top_y_diameter_mm,
            [W] * ny,
            "رادیه - شبکه بالا Y",
            lap_percent,
        )

    final = finalize_rebar_details(details)

    return {
        "lean_concrete_m3": 0,
        "raft_concrete_m3": concrete,
        "total_concrete_m3": concrete,
        "total_rebar_kg": sum(
            x["weight_kg"]
            for x in final
        ),
        "rebar_details": final,
    }


# =========================================================
# COLUMNS
# =========================================================

def _member_result(
    concrete,
    details,
    **extra,
):
    final = finalize_rebar_details(details)

    return {
        "concrete_m3": concrete,
        "total_concrete_m3": concrete,
        "total_rebar_kg": sum(
            x["weight_kg"]
            for x in final
        ),
        "rebar_details": final,
        **extra,
    }


def column_rectangular(
    count,
    width_m,
    depth_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=40,
):
    n = int(count)

    concrete = (
        n
        * width_m
        * depth_m
        * height_m
    )

    details = []

    L = max(
        height_m - 2 * cover_mm / 1000,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (int(long_count) * n),
        "ستون - میلگرد طولی",
    )

    sc = max(
        1,
        math.floor(
            L / (stirrup_spacing / 1000)
        ) + 1,
    )

    stirrup_len = 2 * (
        (width_m - 2 * cover_mm / 1000)
        + (depth_m - 2 * cover_mm / 1000)
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_len] * (sc * n),
        "ستون - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
    )


def column_round(
    count,
    diameter_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=40,
):
    n = int(count)

    concrete = (
        n
        * math.pi
        * (diameter_m ** 2)
        / 4
        * height_m
    )

    details = []

    L = max(
        height_m - 2 * cover_mm / 1000,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (int(long_count) * n),
        "ستون گرد - میلگرد طولی",
    )

    sc = max(
        1,
        math.floor(
            L / (stirrup_spacing / 1000)
        ) + 1,
    )

    ring = (
        math.pi
        * max(
            diameter_m - 2 * cover_mm / 1000,
            0,
        )
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [ring] * (sc * n),
        "ستون گرد - خاموت حلقوی",
    )

    return _member_result(
        concrete,
        details,
        count=n,
    )


# =========================================================
# BEAMS
# =========================================================

def beam(
    count,
    length_m,
    width_m,
    height_m,
    long_dia,
    bottom_count,
    top_dia,
    top_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=40,
):
    n = int(count)

    concrete = (
        n
        * length_m
        * width_m
        * height_m
    )

    details = []

    L = max(
        length_m - 2 * cover_mm / 1000,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (int(bottom_count) * n),
        "تیر - میلگرد طولی پایین",
    )

    add_rebar_detail(
        details,
        top_dia,
        [L] * (int(top_count) * n),
        "تیر - میلگرد طولی بالا",
    )

    sc = max(
        1,
        math.floor(
            L / (stirrup_spacing / 1000)
        ) + 1,
    )

    stirrup_len = 2 * (
        (width_m - 2 * cover_mm / 1000)
        + (height_m - 2 * cover_mm / 1000)
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_len] * (sc * n),
        "تیر - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
    )


# =========================================================
# TIE BEAM
# =========================================================

def tie_beam(
    count,
    length_m,
    width_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=40,
):
    n = int(count)

    concrete = (
        n
        * length_m
        * width_m
        * height_m
    )

    details = []

    L = max(
        length_m - 2 * cover_mm / 1000,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (int(long_count) * n),
        "شناژ/کلاف - طولی",
    )

    sc = max(
        1,
        math.floor(
            L / (stirrup_spacing / 1000)
        ) + 1,
    )

    stirrup_len = 2 * (
        (width_m - 2 * cover_mm / 1000)
        + (height_m - 2 * cover_mm / 1000)
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_len] * (sc * n),
        "شناژ/کلاف - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
    )


# =========================================================
# WALL
# =========================================================

def wall_concrete(
    length_m,
    height_m,
    thickness_m,
    vertical_dia,
    vertical_spacing,
    horizontal_dia,
    horizontal_spacing,
    cover_mm=40,
):
    concrete = (
        length_m
        * height_m
        * thickness_m
    )

    details = []

    L = max(
        height_m - 2 * cover_mm / 1000,
        0,
    )

    W = max(
        length_m - 2 * cover_mm / 1000,
        0,
    )

    nv = number_of_bars_in_direction(
        W,
        vertical_spacing,
    )

    nh = number_of_bars_in_direction(
        L,
        horizontal_spacing,
    )

    add_rebar_detail(
        details,
        vertical_dia,
        [L] * nv,
        "دیوار - میلگرد قائم",
    )

    add_rebar_detail(
        details,
        horizontal_dia,
        [W] * nh,
        "دیوار - میلگرد افقی",
    )

    return _member_result(
        concrete,
        details,
    )


# =========================================================
# STAIR
# =========================================================

def stair_slab(
    length_m,
    width_m,
    thickness_m,
    main_dia,
    main_spacing,
    dist_dia,
    dist_spacing,
    steps=0,
    step_riser=0,
    step_tread=0,
):
    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    L = usable_length(
        length_m,
        40,
    )

    W = usable_length(
        width_m,
        40,
    )

    nm = number_of_bars_in_direction(
        W,
        main_spacing,
    )

    nd = number_of_bars_in_direction(
        L,
        dist_spacing,
    )

    add_rebar_detail(
        details,
        main_dia,
        [L] * nm,
        "راه‌پله - میلگرد اصلی",
    )

    add_rebar_detail(
        details,
        dist_dia,
        [W] * nd,
        "راه‌پله - میلگرد توزیعی",
    )

    step_concrete = 0

    if (
        steps
        and step_riser
        and step_tread
    ):
        step_concrete = (
            steps
            * step_riser
            * step_tread
            * width_m
        )

        concrete += step_concrete

    return _member_result(
        concrete,
        details,
        steps=steps,
    )


# =========================================================
# ROOF
# =========================================================

def roof_slab(
    area_m2,
    concrete_coeff,
    rebar_dia,
    rebar_kg_m2=0,
):
    concrete = area_m2 * concrete_coeff

    details = []

    if rebar_kg_m2 > 0:
        total_rebar_weight = (
            area_m2 * rebar_kg_m2
        )

        unit_weight = REBAR_WEIGHT.get(
            int(rebar_dia),
            int(rebar_dia) ** 2 / 162,
        )

        total_length = (
            total_rebar_weight
            / unit_weight
        )

        # برای سقف فعلی، این بخش صرفاً
        # مصرف نظری میلگرد را نگه می‌دارد.
        details.append(
            {
                "diameter_mm": int(rebar_dia),
                "length_m": total_length,
                "weight_kg": total_rebar_weight,
                "bars_12m": bars_12m(total_length),
                "piece_count": 1,
                "piece_lengths_m": [total_length],
                "waste_m": (
                    bars_12m(total_length)
                    * STOCK_LENGTH_M
                    - total_length
                ),
                "cut_plan": [],
                "description": (
                    "سقف - میلگرد حرارتی/تخمینی"
                ),
            }
        )

    return _member_result(
        concrete,
        details,
        area_m2=area_m2,
    )


# =========================================================
# TOTAL FOUNDATION
# =========================================================

def total_foundation_result(results):
    total_concrete = sum(
        r.get("total_concrete_m3", 0)
        for r in results
    )

    total_rebar = sum(
        r.get("total_rebar_kg", 0)
        for r in results
    )

    final = finalize_rebar_details(
        [
            d
            for r in results
            for d in r.get(
                "rebar_details",
                [],
            )
        ]
    )

    return {
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_rebar,
        "rebar_details": final,
    }
