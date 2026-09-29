import math

# ============================================================
# Structural Quantity / Rebar Calculation Engine
# Version: 2.0
# NOTE: This module performs quantity/rebar calculations.
# Code-specific design checks belong in code_checks.py.
# ============================================================

STOCK_BAR_LENGTH_M = 12.0

REBAR_WEIGHT = {
    6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.210,
    16: 1.580, 18: 2.000, 20: 2.470, 22: 2.980, 25: 3.850,
    28: 4.830, 32: 6.310, 36: 7.990,
}

STANDARD_IRAN = "iran"
STANDARD_ACI = "aci318"
STANDARD_EUROCODE = "eurocode2"
STANDARD_CHINA = "china"

SUPPORTED_STANDARDS = (
    STANDARD_IRAN,
    STANDARD_ACI,
    STANDARD_EUROCODE,
    STANDARD_CHINA,
)

STANDARD_EDITIONS = {
    STANDARD_IRAN: "unspecified",
    STANDARD_ACI: "unspecified",
    STANDARD_EUROCODE: "unspecified",
    STANDARD_CHINA: "unspecified",
}


def normalize_standard(value, strict=True):
    """Normalize a standard name.
    Unknown standards are never silently mapped to Iran.
    """
    if value is None:
        if strict:
            raise ValueError("Standard is required.")
        return STANDARD_IRAN

    s = (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
    )

    aliases = {
        "iran": STANDARD_IRAN,
        "mبحث9": STANDARD_IRAN,
        "مبحث9": STANDARD_IRAN,
        "nbci": STANDARD_IRAN,

        "aci": STANDARD_ACI,
        "aci318": STANDARD_ACI,
        "aci31819": STANDARD_ACI,

        "eurocode": STANDARD_EUROCODE,
        "eurocode2": STANDARD_EUROCODE,
        "ec2": STANDARD_EUROCODE,

        "china": STANDARD_CHINA,
        "chinese": STANDARD_CHINA,
        "gb50010": STANDARD_CHINA,
    }

    if s in aliases:
        return aliases[s]

    if strict:
        raise ValueError(f"Unsupported standard: {value}")

    return STANDARD_IRAN


def standard_info(standard, edition=None):
    std = normalize_standard(standard)

    return {
        "standard": std,
        "edition": edition or STANDARD_EDITIONS.get(std, "unspecified"),
        "supported": True,
    }


def project_settings(
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_grade="A3",
    rebar_yield_mpa=None,
    edition=None,
):
    std = normalize_standard(standard)

    fc = float(concrete_strength_mpa)

    if fc <= 0:
        raise ValueError("Concrete strength must be positive.")

    fy = (
        rebar_yield_mpa
        if rebar_yield_mpa is not None
        else rebar_grade_yield_mpa(std, rebar_grade)
    )

    return {
        "standard": std,
        "edition": edition or STANDARD_EDITIONS.get(std, "unspecified"),
        "fc_mpa": fc,
        "rebar_grade": rebar_grade,
        "fy_mpa": float(fy),
    }


def rebar_grade_yield_mpa(standard, grade):
    std = normalize_standard(standard)

    g = (
        str(grade)
        .strip()
        .upper()
        .replace(" ", "")
    )

    tables = {
        STANDARD_IRAN: {
            "A1": 240,
            "A2": 300,
            "A3": 400,
            "A4": 500,
        },

        STANDARD_ACI: {
            "GRADE40": 280,
            "40": 280,
            "GRADE60": 420,
            "60": 420,
        },

        STANDARD_EUROCODE: {
            "B400": 400,
            "B500": 500,
            "B500A": 500,
            "B500B": 500,
            "B500C": 500,
        },
    }

    if std == STANDARD_CHINA:
        # Do not invent a Chinese grade mapping.
        # Supply fy explicitly until the exact project
        # code/edition/material grade is configured.
        raise ValueError(
            "China rebar grade requires an explicit verified fy value."
        )

    if g not in tables[std]:
        raise ValueError(
            f"Unsupported rebar grade '{grade}' for {std}."
        )

    return tables[std][g]


# ============================================================
# Validation Helpers
# ============================================================

def _positive(value, name):
    x = float(value)

    if x <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return x


def _nonnegative(value, name):
    x = float(value)

    if x < 0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return x


def _positive_int(value, name):
    x = int(value)

    if x <= 0:
        raise ValueError(
            f"{name} must be a positive integer."
        )

    return x


def _diameter(value):
    d = int(value)

    if d <= 0:
        raise ValueError(
            "Rebar diameter must be positive."
        )

    return d


# ============================================================
# Basic Rebar Calculations
# ============================================================

def rebar_weight(length_m, diameter_mm):
    length = _nonnegative(
        length_m,
        "Rebar length"
    )

    d = _diameter(diameter_mm)

    return length * REBAR_WEIGHT.get(
        d,
        d * d / 162.0
    )


def bars_12m(length_m):
    length = _nonnegative(
        length_m,
        "Rebar length"
    )

    if length <= 0:
        return 0

    return math.ceil(
        length / STOCK_BAR_LENGTH_M
    )


def number_of_bars_in_direction(
    usable_length_m,
    spacing_mm
):
    L = _nonnegative(
        usable_length_m,
        "Usable length"
    )

    s = _positive(
        spacing_mm,
        "Spacing"
    )

    if L <= 0:
        return 0

    return math.floor(
        L / (s / 1000.0)
    ) + 1


def usable_length(
    total_length_m,
    cover_mm=50
):
    L = _nonnegative(
        total_length_m,
        "Total length"
    )

    c = (
        _nonnegative(
            cover_mm,
            "Cover"
        )
        / 1000.0
    )

    return max(
        L - 2 * c,
        0.0
    )


def bar_length_with_lap(
    length_m,
    lap_percent=0
):
    L = _nonnegative(
        length_m,
        "Bar length"
    )

    p = _nonnegative(
        lap_percent,
        "Lap percent"
    )

    return L * (
        1.0 + p / 100.0
    )


# ============================================================
# 12m Stock Bar Optimization
# ============================================================

def optimize_12m_bars(piece_lengths):

    clean = sorted(
        [
            float(x)
            for x in piece_lengths
            if x is not None
            and float(x) > 0
        ],
        reverse=True,
    )

    for x in clean:
        if x > STOCK_BAR_LENGTH_M + 1e-6:
            raise ValueError(
                f"Bar piece length {x:.2f} m "
                f"is longer than 12 m."
            )

    bars = []

    for piece in clean:

        placed = False

        for bar in bars:

            if (
                bar["used_m"] + piece
                <= STOCK_BAR_LENGTH_M + 1e-9
            ):
                bar["pieces"].append(piece)

                bar["used_m"] += piece

                bar["waste_m"] = max(
                    STOCK_BAR_LENGTH_M
                    - bar["used_m"],
                    0.0,
                )

                placed = True
                break

        if not placed:

            bars.append(
                {
                    "pieces": [piece],
                    "used_m": piece,
                    "waste_m":
                        STOCK_BAR_LENGTH_M - piece,
                }
            )

    waste = sum(
        x["waste_m"]
        for x in bars
    )

    return {
        "stock_length_m":
            STOCK_BAR_LENGTH_M,

        "stock_bars":
            len(bars),

        "used_m":
            sum(clean),

        "waste_m":
            waste,

        "waste_percent":
            (
                waste
                / (
                    len(bars)
                    * STOCK_BAR_LENGTH_M
                )
                * 100.0
            )
            if bars
            else 0.0,

        "plans":
            bars,
    }


# ============================================================
# Rebar Detail
# ============================================================

def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0,
):

    d = _diameter(
        diameter_mm
    )

    pieces = [
        bar_length_with_lap(
            float(x),
            lap_percent,
        )
        for x in piece_lengths
        if float(x) > 0
    ]

    opt = optimize_12m_bars(
        pieces
    )

    total = sum(
        pieces
    )

    return {
        "diameter_mm":
            d,

        "length_m":
            total,

        "weight_kg":
            rebar_weight(
                total,
                d,
            ),

        "bars_12m":
            opt["stock_bars"],

        "piece_count":
            len(pieces),

        "piece_lengths_m":
            pieces,

        "waste_m":
            opt["waste_m"],

        "waste_percent":
            opt["waste_percent"],

        "cut_plan":
            opt["plans"],

        "description":
            description,
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
    descriptions = {}

    for d in details or []:

        dia = _diameter(
            d["diameter_mm"]
        )

        grouped.setdefault(
            dia,
            []
        ).extend(
            d.get(
                "piece_lengths_m",
                []
            )
        )

        desc = d.get(
            "description"
        )

        if (
            desc
            and desc
            not in descriptions.setdefault(
                dia,
                []
            )
        ):
            descriptions[
                dia
            ].append(desc)

    out = []

    for dia in sorted(
        grouped
    ):

        pieces = grouped[
            dia
        ]

        opt = optimize_12m_bars(
            pieces
        )

        total = sum(
            pieces
        )

        out.append(
            {
                "diameter_mm":
                    dia,

                "length_m":
                    total,

                "weight_kg":
                    rebar_weight(
                        total,
                        dia,
                    ),

                "bars_12m":
                    opt["stock_bars"],

                "piece_count":
                    len(pieces),

                "piece_lengths_m":
                    pieces,

                "waste_m":
                    opt["waste_m"],

                "waste_percent":
                    opt["waste_percent"],

                "cut_plan":
                    opt["plans"],

                "description":
                    " + ".join(
                        descriptions.get(
                            dia,
                            []
                        )
                    ),
            }
        )

    return out


# ============================================================
# Standard Member Result
# ============================================================

def _member_result(
    concrete,
    details,
    **extra
):

    concrete = _nonnegative(
        concrete,
        "Concrete volume"
    )

    final = finalize_rebar_details(
        details
    )

    total_length = sum(
        x["length_m"]
        for x in final
    )

    total_weight = sum(
        x["weight_kg"]
        for x in final
    )

    stock_bars = sum(
        x["bars_12m"]
        for x in final
    )

    waste = sum(
        x["waste_m"]
        for x in final
    )

    stock_length = (
        stock_bars
        * STOCK_BAR_LENGTH_M
    )

    return {
        "concrete_m3":
            concrete,

        "total_concrete_m3":
            concrete,

        "total_rebar_kg":
            total_weight,

        "total_rebar_length_m":
            total_length,

        "total_stock_bars_12m":
            stock_bars,

        "total_stock_length_m":
            stock_length,

        "total_rebar_waste_m":
            waste,

        "rebar_waste_percent":
            (
                waste
                / stock_length
                * 100.0
            )
            if stock_length
            else 0.0,

        "rebar_details":
            final,

        **extra,
    }


# ============================================================
# Foundations
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

    n = _positive_int(
        count,
        "Footing count"
    )

    Lm = _positive(
        length_m,
        "Footing length"
    )

    Wm = _positive(
        width_m,
        "Footing width"
    )

    Tm = _positive(
        thickness_m,
        "Footing thickness"
    )

    lean = (
        n
        * _nonnegative(
            lean_concrete_length_m,
            "Lean length"
        )
        * _nonnegative(
            lean_concrete_width_m,
            "Lean width"
        )
        * _nonnegative(
            lean_concrete_thickness_m,
            "Lean thickness"
        )
    )

    footing = (
        n
        * Lm
        * Wm
        * Tm
    )

    pedestal = (
        n
        * _nonnegative(
            pedestal_length_m,
            "Pedestal length"
        )
        * _nonnegative(
            pedestal_width_m,
            "Pedestal width"
        )
        * _nonnegative(
            pedestal_height_m,
            "Pedestal height"
        )
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    W = usable_length(
        Wm,
        cover_mm
    )

    nx = number_of_bars_in_direction(
        W,
        bottom_spacing_mm
    )

    ny = number_of_bars_in_direction(
        L,
        bottom_spacing_mm
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [L] * (nx * n),
        "پی منفرد - شبکه پایین X",
        lap_percent,
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [W] * (ny * n),
        "پی منفرد - شبکه پایین Y",
        lap_percent,
    )

    if (
        top_diameter_mm
        and top_spacing_mm
    ):

        nx = number_of_bars_in_direction(
            W,
            top_spacing_mm
        )

        ny = number_of_bars_in_direction(
            L,
            top_spacing_mm
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [L] * (nx * n),
            "پی منفرد - شبکه بالا X",
            lap_percent,
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [W] * (ny * n),
            "پی منفرد - شبکه بالا Y",
            lap_percent,
        )

    return _member_result(
        lean
        + footing
        + pedestal,
        details,
        lean_concrete_m3=lean,
        footing_concrete_m3=footing,
        pedestal_concrete_m3=pedestal,
        count=n,
    )


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

    n = _positive_int(
        strip_count,
        "Strip count"
    )

    Lm = _positive(
        strip_length_m,
        "Strip length"
    )

    Wm = _positive(
        footing_width_m,
        "Footing width"
    )

    Tm = _positive(
        footing_thickness_m,
        "Footing thickness"
    )

    concrete = (
        n
        * Lm
        * Wm
        * Tm
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    W = usable_length(
        Wm,
        cover_mm
    )

    add_rebar_detail(
        details,
        longitudinal_diameter_mm,
        [L] * (
            _positive_int(
                longitudinal_count,
                "Longitudinal count"
            )
            * n
        ),
        "پی نواری - طولی پایین",
        lap_percent,
    )

    nc = number_of_bars_in_direction(
        L,
        transverse_spacing_mm
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
                int(top_longitudinal_count)
                * n
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
            top_transverse_spacing_mm
        )

        add_rebar_detail(
            details,
            top_transverse_diameter_mm,
            [W] * (nc * n),
            "پی نواری - عرضی بالا",
            lap_percent,
        )

    return _member_result(
        concrete,
        details,
        count=n,
    )


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

    Lm = _positive(
        length_m,
        "Raft length"
    )

    Wm = _positive(
        width_m,
        "Raft width"
    )

    Tm = _positive(
        thickness_m,
        "Raft thickness"
    )

    concrete = (
        Lm
        * Wm
        * Tm
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    W = usable_length(
        Wm,
        cover_mm
    )

    nx = number_of_bars_in_direction(
        W,
        bottom_x_spacing_mm
    )

    ny = number_of_bars_in_direction(
        L,
        bottom_y_spacing_mm
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
            top_x_spacing_mm
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
            top_y_spacing_mm
        )

        add_rebar_detail(
            details,
            top_y_diameter_mm,
            [W] * ny,
            "رادیه - شبکه بالا Y",
            lap_percent,
        )

    return _member_result(
        concrete,
        details,
        lean_concrete_m3=0,
        raft_concrete_m3=concrete,
    )


# ============================================================
# Columns
# ============================================================

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

    n = _positive_int(
        count,
        "Column count"
    )

    w = _positive(
        width_m,
        "Column width"
    )

    d = _positive(
        depth_m,
        "Column depth"
    )

    h = _positive(
        height_m,
        "Column height"
    )

    concrete = (
        n
        * w
        * d
        * h
    )

    details = []

    L = usable_length(
        h,
        cover_mm
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            _positive_int(
                long_count,
                "Longitudinal count"
            )
            * n
        ),
        "ستون - میلگرد طولی",
    )

    sc = number_of_bars_in_direction(
        L,
        stirrup_spacing
    )

    stirrup_len = 2 * (
        usable_length(
            w,
            cover_mm
        )
        +
        usable_length(
            d,
            cover_mm
        )
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

    n = _positive_int(
        count,
        "Column count"
    )

    dia = _positive(
        diameter_m,
        "Column diameter"
    )

    h = _positive(
        height_m,
        "Column height"
    )

    concrete = (
        n
        * math.pi
        * dia
        * dia
        / 4
        * h
    )

    details = []

    L = usable_length(
        h,
        cover_mm
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            _positive_int(
                long_count,
                "Longitudinal count"
            )
            * n
        ),
        "ستون گرد - میلگرد طولی",
    )

    sc = number_of_bars_in_direction(
        L,
        stirrup_spacing
    )

    ring = (
        math.pi
        * max(
            dia
            - 2 * cover_mm / 1000,
            0
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


# ============================================================
# Beams / Ties
# ============================================================

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

    n = _positive_int(
        count,
        "Beam count"
    )

    Lm = _positive(
        length_m,
        "Beam length"
    )

    w = _positive(
        width_m,
        "Beam width"
    )

    h = _positive(
        height_m,
        "Beam height"
    )

    concrete = (
        n
        * Lm
        * w
        * h
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            _positive_int(
                bottom_count,
                "Bottom count"
            )
            * n
        ),
        "تیر - میلگرد طولی پایین",
    )

    add_rebar_detail(
        details,
        top_dia,
        [L] * (
            _positive_int(
                top_count,
                "Top count"
            )
            * n
        ),
        "تیر - میلگرد طولی بالا",
    )

    sc = number_of_bars_in_direction(
        L,
        stirrup_spacing
    )

    stirrup_len = 2 * (
        usable_length(
            w,
            cover_mm
        )
        +
        usable_length(
            h,
            cover_mm
        )
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

    n = _positive_int(
        count,
        "Tie count"
    )

    Lm = _positive(
        length_m,
        "Tie length"
    )

    w = _positive(
        width_m,
        "Tie width"
    )

    h = _positive(
        height_m,
        "Tie height"
    )

    concrete = (
        n
        * Lm
        * w
        * h
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            _positive_int(
                long_count,
                "Longitudinal count"
            )
            * n
        ),
        "شناژ/کلاف - طولی",
    )

    sc = number_of_bars_in_direction(
        L,
        stirrup_spacing
    )

    sl = 2 * (
        usable_length(
            w,
            cover_mm
        )
        +
        usable_length(
            h,
            cover_mm
        )
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [sl] * (sc * n),
        "شناژ/کلاف - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
    )


# ============================================================
# Walls / Stairs
# ============================================================

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

    Lm = _positive(
        length_m,
        "Wall length"
    )

    h = _positive(
        height_m,
        "Wall height"
    )

    t = _positive(
        thickness_m,
        "Wall thickness"
    )

    concrete = (
        Lm
        * h
        * t
    )

    details = []

    L = usable_length(
        h,
        cover_mm
    )

    W = usable_length(
        Lm,
        cover_mm
    )

    nv = number_of_bars_in_direction(
        W,
        vertical_spacing
    )

    nh = number_of_bars_in_direction(
        L,
        horizontal_spacing
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

    Lm = _positive(
        length_m,
        "Stair length"
    )

    Wm = _positive(
        width_m,
        "Stair width"
    )

    Tm = _positive(
        thickness_m,
        "Stair thickness"
    )

    concrete = (
        Lm
        * Wm
        * Tm
    )

    details = []

    L = usable_length(
        Lm,
        40
    )

    W = usable_length(
        Wm,
        40
    )

    nm = number_of_bars_in_direction(
        W,
        main_spacing
    )

    nd = number_of_bars_in_direction(
        L,
        dist_spacing
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

    step_concrete = 0.0

    if (
        steps
        and step_riser
        and step_tread
    ):

        step_concrete = (
            _positive(
                steps,
                "Steps"
            )
            *
            _positive(
                step_riser,
                "Step riser"
            )
            *
            _positive(
                step_tread,
                "Step tread"
            )
            *
            Wm
        )

        concrete += step_concrete

    return _member_result(
        concrete,
        details,
        steps=steps,
        step_concrete_m3=step_concrete,
    )


# ============================================================
# Roof
# ============================================================

def roof_slab(
    area_m2,
    concrete_coeff,
    rebar_dia,
    rebar_kg_m2=0,
):

    area = _positive(
        area_m2,
        "Roof area"
    )

    coeff = _positive(
        concrete_coeff,
        "Concrete coefficient"
    )

    concrete = (
        area
        * coeff
    )

    details = []

    if (
        rebar_kg_m2
        and float(rebar_kg_m2) > 0
    ):

        d = _diameter(
            rebar_dia
        )

        length = (
            area
            * float(rebar_kg_m2)
        ) / REBAR_WEIGHT.get(
            d,
            d * d / 162.0
        )

        add_rebar_detail(
            details,
            d,
            [length],
            "سقف - میلگرد حرارتی/تخمینی",
        )

    return _member_result(
        concrete,
        details,
        area_m2=area,
    )


def roof_mesh(
    length_m,
    width_m,
    thickness_m,
    mesh_dia,
    mesh_spacing,
    cover_mm=30,
):

    Lm = _positive(
        length_m,
        "Roof length"
    )

    Wm = _positive(
        width_m,
        "Roof width"
    )

    Tm = _positive(
        thickness_m,
        "Roof thickness"
    )

    concrete = (
        Lm
        * Wm
        * Tm
    )

    details = []

    L = usable_length(
        Lm,
        cover_mm
    )

    W = usable_length(
        Wm,
        cover_mm
    )

    nx = number_of_bars_in_direction(
        W,
        mesh_spacing
    )

    ny = number_of_bars_in_direction(
        L,
        mesh_spacing
    )

    add_rebar_detail(
        details,
        mesh_dia,
        [L] * nx,
        "سقف - مش X",
    )

    add_rebar_detail(
        details,
        mesh_dia,
        [W] * ny,
        "سقف - مش Y",
    )

    return _member_result(
        concrete,
        details,
    )


# ============================================================
# Rebar Equivalency
# ============================================================

def equivalent_rebar_count(
    current_count,
    current_dia,
    replacement_dia,
):

    n = _positive_int(
        current_count,
        "Current rebar count"
    )

    d1 = _diameter(
        current_dia
    )

    d2 = _diameter(
        replacement_dia
    )

    current_area = (
        n
        * math.pi
        * d1
        * d1
        / 4.0
    )

    replacement_area = (
        math.pi
        * d2
        * d2
        / 4.0
    )

    required = math.ceil(
        current_area
        / replacement_area
    )

    return {
        "current_count":
            n,

        "current_dia":
            d1,

        "replacement_dia":
            d2,

        "current_area_mm2":
            current_area,

        "replacement_bar_area_mm2":
            replacement_area,

        "required_count":
            required,

        "area_equivalent":
            (
                required
                * replacement_area
                >= current_area
            ),

        "engineering_warning":
            "Area equivalency only; spacing, minimum/maximum reinforcement, development, splice, anchorage and detailing must be checked separately.",
    }


# ============================================================
# Project Summary / Rebar Schedule / Cut List
# ============================================================

def aggregate_project_results(results):
    """Aggregate member results for Project Summary / Report / AI input."""

    results = results or []

    total_concrete = sum(
        float(
            r.get(
                "total_concrete_m3",
                0
            )
            or 0
        )
        for r in results
    )

    total_weight = sum(
        float(
            r.get(
                "total_rebar_kg",
                0
            )
            or 0
        )
        for r in results
    )

    total_length = sum(
        float(
            r.get(
                "total_rebar_length_m",
                0
            )
            or 0
        )
        for r in results
    )

    total_stock = sum(
        int(
            r.get(
                "total_stock_bars_12m",
                0
            )
            or 0
        )
        for r in results
    )

    total_waste = sum(
        float(
            r.get(
                "total_rebar_waste_m",
                0
            )
            or 0
        )
        for r in results
    )

    details = finalize_rebar_details(
        [
            d
            for r in results
            for d in r.get(
                "rebar_details",
                []
            )
        ]
    )

    by_diameter = {
        str(
            x["diameter_mm"]
        ): {
            "length_m":
                x["length_m"],

            "weight_kg":
                x["weight_kg"],

            "bars_12m":
                x["bars_12m"],

            "waste_m":
                x["waste_m"],

            "waste_percent":
                x["waste_percent"],

            "piece_count":
                x["piece_count"],
        }
        for x in details
    }

    return {
        "member_count":
            len(results),

        "total_concrete_m3":
            total_concrete,

        "total_rebar_kg":
            total_weight,

        "total_rebar_length_m":
            total_length,

        "total_stock_bars_12m":
            total_stock,

        "total_stock_length_m":
            total_stock
            * STOCK_BAR_LENGTH_M,

        "total_rebar_waste_m":
            total_waste,

        "rebar_waste_percent":
            (
                total_waste
                / (
                    total_stock
                    * STOCK_BAR_LENGTH_M
                )
                * 100.0
            )
            if total_stock
            else 0.0,

        "rebar_schedule":
            details,

        "by_diameter":
            by_diameter,

        "members":
            results,
    }


def rebar_schedule(results):
    return aggregate_project_results(
        results
    )["rebar_schedule"]


def cut_list(results):

    return [
        {
            "diameter_mm":
                x["diameter_mm"],

            "stock_bars":
                x["bars_12m"],

            "piece_count":
                x["piece_count"],

            "total_length_m":
                x["length_m"],

            "waste_m":
                x["waste_m"],

            "waste_percent":
                x["waste_percent"],

            "plans":
                x["cut_plan"],
        }

        for x in aggregate_project_results(
            results
        )["rebar_schedule"]
    ]


def total_foundation_result(results):
    return aggregate_project_results(
        results
    )


# ============================================================
# Public API
# ============================================================

__all__ = [
    name
    for name in globals()
    if not name.startswith("_")
]
