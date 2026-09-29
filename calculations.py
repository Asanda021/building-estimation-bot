import math


# ============================================================
# Concrete Structure Quantity Engine
# Standards:
#   iran   -> Iranian Mبحث 9
#   aci318 -> ACI 318
#   ec2    -> Eurocode 2 / EN 1992-1-1
#   china  -> GB/T 50010-2010 (2024)
# ============================================================


# ------------------------------------------------------------
# Rebar unit weights kg/m
# ------------------------------------------------------------

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
    40: 9.87,
}


STOCK_BAR_LENGTH_M = 12.0


# ------------------------------------------------------------
# Standard definitions
# ------------------------------------------------------------

STANDARDS = {
    "iran": {
        "name": "مبحث ۹ ایران",
        "code": "Mبحث ۹",
        "default_cover_foundation_mm": 50,
        "default_cover_member_mm": 40,
    },

    "aci318": {
        "name": "ACI 318",
        "code": "ACI 318",
        "default_cover_foundation_mm": 50,
        "default_cover_member_mm": 40,
    },

    "ec2": {
        "name": "Eurocode 2",
        "code": "EN 1992-1-1",
        "default_cover_foundation_mm": 50,
        "default_cover_member_mm": 30,
    },

    "china": {
        "name": "China GB/T 50010",
        "code": "GB/T 50010-2010 (2024)",
        "default_cover_foundation_mm": 40,
        "default_cover_member_mm": 20,
    },
}


# ------------------------------------------------------------
# Material settings
# ------------------------------------------------------------

DEFAULT_PROJECT = {
    "standard": "iran",
    "fc_mpa": 25.0,
    "fy_mpa": 400.0,
    "design_life_years": 50,
    "environment": "normal",
}


def normalize_standard(standard):
    if not standard:
        return "iran"

    value = str(standard).strip().lower()

    aliases = {
        "iran": "iran",
        "iranian": "iran",
        "mabhas9": "iran",
        "مبحث ۹": "iran",
        "مبحث9": "iran",

        "aci": "aci318",
        "aci318": "aci318",
        "aci 318": "aci318",

        "ec2": "ec2",
        "eurocode": "ec2",
        "eurocode2": "ec2",
        "eurocode 2": "ec2",

        "china": "china",
        "gb": "china",
        "gb50010": "china",
        "gb/t 50010": "china",
        "gb/t50010": "china",
        "chinese": "china",
        "چین": "china",
    }

    return aliases.get(value, "iran")


def get_standard_info(standard="iran"):
    return STANDARDS.get(normalize_standard(standard), STANDARDS["iran"])


# ------------------------------------------------------------
# Material normalization
# ------------------------------------------------------------

def normalize_fc(fc_mpa):
    try:
        return float(fc_mpa)
    except Exception:
        return 25.0


def normalize_fy(fy_mpa):
    try:
        return float(fy_mpa)
    except Exception:
        return 400.0


def project_settings(
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    return {
        "standard": normalize_standard(standard),
        "fc_mpa": normalize_fc(fc_mpa),
        "fy_mpa": normalize_fy(fy_mpa),
        "design_life_years": int(design_life_years),
        "environment": str(environment or "normal"),
    }


# ------------------------------------------------------------
# Rebar basic functions
# ------------------------------------------------------------

def rebar_weight(length_m, diameter_mm):
    d = int(diameter_mm)

    if length_m <= 0:
        return 0.0

    return float(length_m) * REBAR_WEIGHT.get(
        d,
        (d * d) / 162.0
    )


def rebar_area_mm2(diameter_mm):
    d = float(diameter_mm)
    return math.pi * d * d / 4.0


def bars_12m(length_m):
    if length_m <= 0:
        return 0

    return math.ceil(length_m / STOCK_BAR_LENGTH_M)


def number_of_bars_in_direction(usable_length_m, spacing_mm):
    if usable_length_m <= 0 or spacing_mm <= 0:
        return 0

    return math.floor(
        usable_length_m / (spacing_mm / 1000.0)
    ) + 1


# ------------------------------------------------------------
# Standard-aware concrete cover
# ------------------------------------------------------------

def required_cover_mm(
    standard="iran",
    member_type="member",
    fc_mpa=25,
    design_life_years=50,
    environment="normal",
):
    """
    Returns an internal cover value.

    IMPORTANT:
    This function is an engineering default layer for the quantity
    calculator. Final project cover must follow the project drawings
    and the applicable code/environment classification.

    China:
      GB/T 50010-2010 (2024)
      - stressed reinforcement cover >= bar diameter
      - 50-year table depends on environmental category
      - foundation cover from top of blinding/cushion >= 40 mm
      - if fc <= C25, table value increases by 5 mm

    Because the bot UI does not ask the user for an environmental
    category, conservative internal defaults are used here.
    """

    standard = normalize_standard(standard)
    member = str(member_type or "member").lower()

    fc = normalize_fc(fc_mpa)

    # --------------------------------------------------------
    # CHINA
    # --------------------------------------------------------

    if standard == "china":

        # Foundation:
        # GB/T 50010-2010 (2024), 8.2.1:
        # cover from top of concrete cushion >= 40 mm.
        if member in (
            "foundation",
            "footing",
            "raft",
            "strip_footing",
            "pile_cap",
        ):
            cover = 40.0

        # Normal building environment category I:
        # slab/wall/shell = 15 mm
        # beam/column/bar = 20 mm
        elif member in (
            "slab",
            "wall",
            "stair",
            "roof",
            "shell",
        ):
            cover = 15.0

        else:
            cover = 20.0

        # Design life 100 years:
        if int(design_life_years) >= 100:
            cover *= 1.4

        # C25 or lower -> +5 mm
        if fc <= 25:
            cover += 5.0

        return max(cover, 10.0)

    # --------------------------------------------------------
    # EUROCODE 2
    # --------------------------------------------------------

    if standard == "ec2":

        if member in (
            "foundation",
            "footing",
            "raft",
            "strip_footing",
            "pile_cap",
        ):
            cover = 50.0

        elif member in ("slab", "roof", "stair", "wall"):
            cover = 25.0

        else:
            cover = 30.0

        return cover

    # --------------------------------------------------------
    # ACI 318
    # --------------------------------------------------------

    if standard == "aci318":

        if member in (
            "foundation",
            "footing",
            "raft",
            "strip_footing",
            "pile_cap",
        ):
            cover = 50.0

        elif member in ("slab", "wall", "roof", "stair"):
            cover = 40.0

        else:
            cover = 40.0

        return cover

    # --------------------------------------------------------
    # IRAN - Mبحث ۹
    # --------------------------------------------------------

    if member in (
        "foundation",
        "footing",
        "raft",
        "strip_footing",
        "pile_cap",
    ):
        return 50.0

    return 40.0


def usable_length(
    total_length_m,
    cover_mm=None,
    standard="iran",
    member_type="member",
    fc_mpa=25,
    design_life_years=50,
    environment="normal",
):
    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard=standard,
            member_type=member_type,
            fc_mpa=fc_mpa,
            design_life_years=design_life_years,
            environment=environment,
        )

    return max(
        float(total_length_m) - 2.0 * float(cover_mm) / 1000.0,
        0.0,
    )


# ------------------------------------------------------------
# Legacy lap compatibility
# ------------------------------------------------------------

def bar_length_with_lap(length_m, lap_percent=0):
    """
    Backward-compatible helper.

    The old calculator used a percentage lap.
    The new standards engine does NOT use a fixed lap percentage.

    Kept so older bot calls do not break.
    """

    if length_m <= 0:
        return 0.0

    return float(length_m)


# ------------------------------------------------------------
# 12m stock optimization
# ------------------------------------------------------------

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
        if x > STOCK_BAR_LENGTH_M + 0.000001:
            raise ValueError(
                f"Bar piece length {x:.2f} m is longer than "
                f"{STOCK_BAR_LENGTH_M:.0f} m."
            )

    bars = []

    for piece in clean:

        placed = False

        for bar in bars:

            if (
                bar["used_m"] + piece
                <= STOCK_BAR_LENGTH_M + 0.000001
            ):
                bar["pieces"].append(piece)
                bar["used_m"] += piece
                bar["waste_m"] = (
                    STOCK_BAR_LENGTH_M - bar["used_m"]
                )
                placed = True
                break

        if not placed:

            bars.append(
                {
                    "pieces": [piece],
                    "used_m": piece,
                    "waste_m": STOCK_BAR_LENGTH_M - piece,
                }
            )

    return {
        "stock_bars": len(bars),
        "waste_m": sum(
            x["waste_m"]
            for x in bars
        ),
        "plans": bars,
    }


# ------------------------------------------------------------
# Rebar detail
# ------------------------------------------------------------

def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
    lap_percent=0,
):
    pieces = [
        float(x)
        for x in piece_lengths
        if x is not None and float(x) > 0
    ]

    opt = optimize_12m_bars(pieces)

    total = sum(pieces)

    return {
        "diameter_mm": int(diameter_mm),
        "length_m": total,
        "weight_kg": rebar_weight(
            total,
            diameter_mm,
        ),
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
    descriptions = {}

    for d in details:

        dia = int(d["diameter_mm"])

        grouped.setdefault(dia, []).extend(
            d.get("piece_lengths_m", [])
        )

        description = d.get("description")

        if description:
            descriptions.setdefault(
                dia,
                []
            )

            if description not in descriptions[dia]:
                descriptions[dia].append(
                    description
                )

    out = []

    for dia in sorted(grouped):

        pieces = grouped[dia]

        opt = optimize_12m_bars(pieces)

        total = sum(pieces)

        out.append(
            {
                "diameter_mm": dia,
                "length_m": total,
                "weight_kg": rebar_weight(
                    total,
                    dia,
                ),
                "bars_12m": opt["stock_bars"],
                "piece_count": len(pieces),
                "piece_lengths_m": pieces,
                "waste_m": opt["waste_m"],
                "cut_plan": opt["plans"],
                "description": " + ".join(
                    descriptions.get(dia, [])
                ),
            }
        )

    return out


# ------------------------------------------------------------
# Member result
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Isolated footing
# ------------------------------------------------------------

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
    cover_mm=None,
    lap_percent=0,
    pedestal_length_m=0,
    pedestal_width_m=0,
    pedestal_height_m=0,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    count = int(count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "foundation",
            fc_mpa,
            design_life_years,
            environment,
        )

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
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [W] * (ny * count),
        "پی منفرد - شبکه پایین Y",
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
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [W] * (ny * count),
            "پی منفرد - شبکه بالا Y",
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
        "cover_mm": cover_mm,
        "standard": normalize_standard(standard),
    }


# ------------------------------------------------------------
# Strip footing
# ------------------------------------------------------------

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
    cover_mm=None,
    lap_percent=0,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    n = int(strip_count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "foundation",
            fc_mpa,
            design_life_years,
            environment,
        )

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
        [L] * (
            int(longitudinal_count) * n
        ),
        "پی نواری - طولی پایین",
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
        )

    return _member_result(
        concrete,
        details,
        count=n,
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Raft foundation
# ------------------------------------------------------------

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
    cover_mm=None,
    lap_percent=0,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "foundation",
            fc_mpa,
            design_life_years,
            environment,
        )

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
    )

    add_rebar_detail(
        details,
        bottom_y_diameter_mm,
        [W] * ny,
        "رادیه - شبکه پایین Y",
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
        )

    return _member_result(
        concrete,
        details,
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Rectangular column
# ------------------------------------------------------------

def column_rectangular(
    count,
    width_m,
    depth_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    n = int(count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "column",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        n
        * width_m
        * depth_m
        * height_m
    )

    details = []

    L = max(
        height_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            int(long_count) * n
        ),
        "ستون - میلگرد طولی",
    )

    sc = max(
        1,
        math.floor(
            L
            / (stirrup_spacing / 1000.0)
        ) + 1,
    )

    stirrup_len = 2 * (
        (
            width_m
            - 2 * cover_mm / 1000.0
        )
        +
        (
            depth_m
            - 2 * cover_mm / 1000.0
        )
    )

    stirrup_len = max(
        stirrup_len,
        0,
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
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Round column
# ------------------------------------------------------------

def column_round(
    count,
    diameter_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    n = int(count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "column",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        n
        * math.pi
        * (diameter_m ** 2)
        / 4.0
        * height_m
    )

    details = []

    L = max(
        height_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            int(long_count) * n
        ),
        "ستون گرد - میلگرد طولی",
    )

    sc = max(
        1,
        math.floor(
            L
            / (stirrup_spacing / 1000.0)
        ) + 1,
    )

    ring = (
        math.pi
        * max(
            diameter_m
            - 2 * cover_mm / 1000.0,
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
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Beam
# ------------------------------------------------------------

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
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    n = int(count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "beam",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        n
        * length_m
        * width_m
        * height_m
    )

    details = []

    L = max(
        length_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            int(bottom_count) * n
        ),
        "تیر - میلگرد طولی پایین",
    )

    add_rebar_detail(
        details,
        top_dia,
        [L] * (
            int(top_count) * n
        ),
        "تیر - میلگرد طولی بالا",
    )

    sc = max(
        1,
        math.floor(
            L
            / (stirrup_spacing / 1000.0)
        ) + 1,
    )

    stirrup_len = 2 * (
        (
            width_m
            - 2 * cover_mm / 1000.0
        )
        +
        (
            height_m
            - 2 * cover_mm / 1000.0
        )
    )

    stirrup_len = max(
        stirrup_len,
        0,
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
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Tie beam / tie
# ------------------------------------------------------------

def tie_beam(
    count,
    length_m,
    width_m,
    height_m,
    long_dia,
    long_count,
    stirrup_dia,
    stirrup_spacing,
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    n = int(count)

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "beam",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        n
        * length_m
        * width_m
        * height_m
    )

    details = []

    L = max(
        length_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    add_rebar_detail(
        details,
        long_dia,
        [L] * (
            int(long_count) * n
        ),
        "شناژ/کلاف - طولی",
    )

    sc = max(
        1,
        math.floor(
            L
            / (stirrup_spacing / 1000.0)
        ) + 1,
    )

    stirrup_len = 2 * (
        (
            width_m
            - 2 * cover_mm / 1000.0
        )
        +
        (
            height_m
            - 2 * cover_mm / 1000.0
        )
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [max(stirrup_len, 0)] * (sc * n),
        "شناژ/کلاف - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Wall
# ------------------------------------------------------------

def wall_concrete(
    length_m,
    height_m,
    thickness_m,
    vertical_dia,
    vertical_spacing,
    horizontal_dia,
    horizontal_spacing,
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "wall",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        length_m
        * height_m
        * thickness_m
    )

    details = []

    L = max(
        height_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    W = max(
        length_m
        - 2 * cover_mm / 1000.0,
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
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Stair slab
# ------------------------------------------------------------

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
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "stair",
            fc_mpa,
            design_life_years,
            environment,
        )

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
        cover_mm=cover_mm,
        standard=normalize_standard(standard),
    )


# ------------------------------------------------------------
# Geometric roof reinforcement mesh
# ------------------------------------------------------------

def roof_mesh(
    length_m,
    width_m,
    thickness_m,
    mesh_dia,
    mesh_spacing,
    cover_mm=None,
    standard="iran",
    fc_mpa=25,
    fy_mpa=400,
    design_life_years=50,
    environment="normal",
):
    """
    Geometric thermal/distribution mesh.

    Unlike the old roof_slab() kg/m2 method, this calculates:
      - actual number of bars
      - actual piece lengths
      - total steel length
      - weight
      - 12m stock bars
      - waste
      - cut list
    """

    if cover_mm is None:
        cover_mm = required_cover_mm(
            standard,
            "roof",
            fc_mpa,
            design_life_years,
            environment,
        )

    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    L = usable_length(
        length_m,
        cover_mm,
    )

    W = usable_length(
        width_m,
        cover_mm,
    )

    # Bars running in X direction:
    # number determined across width
    nx = number_of_bars_in_direction(
        W,
        mesh_spacing,
    )

    # Bars running in Y direction:
    # number determined across length
    ny = number_of_bars_in_direction(
        L,
        mesh_spacing,
    )

    details = []

    add_rebar_detail(
        details,
        mesh_dia,
        [L] * nx,
        "سقف - مش حرارتی X",
    )

    add_rebar_detail(
        details,
        mesh_dia,
        [W] * ny,
        "سقف - مش حرارتی Y",
    )

    final = finalize_rebar_details(
        details
    )

    return {
        "concrete_m3": concrete,
        "total_concrete_m3": concrete,
        "total_rebar_kg": sum(
            x["weight_kg"]
            for x in final
        ),
        "rebar_details": final,
        "area_m2": (
            length_m
            * width_m
        ),
        "cover_mm": cover_mm,
        "standard": normalize_standard(
            standard
        ),
    }


# ------------------------------------------------------------
# Backward-compatible old roof function
# ------------------------------------------------------------

def roof_slab(
    area_m2,
    concrete_coeff,
    rebar_dia,
    rebar_kg_m2=0,
):
    """
    Legacy function.

    Kept for old bot compatibility.
    New UI should use roof_mesh().
    """

    concrete = (
        area_m2
        * concrete_coeff
    )

    details = []

    if rebar_kg_m2 > 0:

        weight = (
            area_m2
            * rebar_kg_m2
        )

        unit_weight = REBAR_WEIGHT.get(
            int(rebar_dia),
            int(rebar_dia) ** 2 / 162.0,
        )

        length = (
            weight
            / unit_weight
        )

        add_rebar_detail(
            details,
            rebar_dia,
            [length],
            "سقف - میلگرد حرارتی/تخمینی",
        )

    return _member_result(
        concrete,
        details,
        area_m2=area_m2,
    )


# ------------------------------------------------------------
# Rebar equivalency
# ------------------------------------------------------------

def rebar_equivalency(
    current_count,
    current_diameter_mm,
    replacement_diameter_mm,
    standard="iran",
):
    """
    Fast reinforcement area equivalency.

    IMPORTANT:
    This function checks steel area only.

    It does NOT by itself prove that the substitution is permitted
    in the structural design because spacing, development length,
    splice, minimum/maximum reinforcement, seismic detailing,
    bar arrangement and member-specific requirements may govern.
    """

    current_count = int(current_count)

    current_diameter_mm = float(
        current_diameter_mm
    )

    replacement_diameter_mm = float(
        replacement_diameter_mm
    )

    if current_count <= 0:
        raise ValueError(
            "Current rebar count must be greater than zero."
        )

    if (
        current_diameter_mm <= 0
        or replacement_diameter_mm <= 0
    ):
        raise ValueError(
            "Rebar diameter must be greater than zero."
        )

    current_area = (
        current_count
        * rebar_area_mm2(
            current_diameter_mm
        )
    )

    replacement_area_one = rebar_area_mm2(
        replacement_diameter_mm
    )

    required_count = math.ceil(
        current_area
        / replacement_area_one
    )

    replacement_area = (
        required_count
        * replacement_area_one
    )

    equivalent = (
        replacement_area
        >= current_area
    )

    area_difference = (
        replacement_area
        - current_area
    )

    return {
        "standard": normalize_standard(
            standard
        ),
        "current_count": current_count,
        "current_diameter_mm": current_diameter_mm,
        "current_area_mm2": current_area,
        "replacement_diameter_mm": replacement_diameter_mm,
        "required_replacement_count": required_count,
        "replacement_area_mm2": replacement_area,
        "area_difference_mm2": area_difference,
        "area_equivalent": equivalent,
        "status": (
            "area_equivalent"
            if equivalent
            else "not_area_equivalent"
        ),
        "warning": (
            "کنترل فقط از نظر سطح مقطع میلگرد انجام شده است؛ "
            "مجاز بودن نهایی جایگزینی نیازمند کنترل فاصله، "
            "مهاری/وصله، حداقل و حداکثر آرماتور و جزئیات عضو است."
        ),
    }


# ------------------------------------------------------------
# Development / anchorage helper
# ------------------------------------------------------------

def development_length_basic(
    diameter_mm,
    fy_mpa=400,
    fc_mpa=25,
    standard="iran",
):
    """
    Basic internal estimator.

    This is intentionally NOT presented as final code compliance.
    Exact anchorage/splice length depends on member condition,
    bar position, confinement, coating, concrete type, seismic
    requirements and other code variables.

    Returns a transparent baseline value so the bot can later
    expand it when the relevant project inputs are available.
    """

    d = float(diameter_mm)
    fy = normalize_fy(fy_mpa)
    fc = max(normalize_fc(fc_mpa), 1.0)

    standard = normalize_standard(
        standard
    )

    if standard == "china":
        # Conservative baseline placeholder for the engine.
        # Final GB/T calculation requires code-specific conditions.
        baseline = (
            0.10
            * fy
            / math.sqrt(fc)
            * d
        )

    elif standard == "ec2":
        baseline = (
            0.10
            * fy
            / (1.0 + math.sqrt(fc))
            * d
        )

    elif standard == "aci318":
        baseline = (
            0.10
            * fy
            / math.sqrt(fc)
            * d
        )

    else:
        baseline = (
            0.10
            * fy
            / math.sqrt(fc)
            * d
        )

    return {
        "standard": standard,
        "diameter_mm": d,
        "baseline_length_mm": max(
            baseline,
            10.0 * d,
        ),
        "is_final_code_check": False,
        "note": (
            "این مقدار برآورد پایه موتور است و "
            "جایگزین کنترل نهایی طول مهاری/وصله "
            "طبق شرایط کامل آیین‌نامه نیست."
        ),
    }


# ------------------------------------------------------------
# Foundation aggregation
# ------------------------------------------------------------

def total_foundation_result(results):
    total_concrete = sum(
        r.get(
            "total_concrete_m3",
            0,
        )
        for r in results
    )

    total_rebar = sum(
        r.get(
            "total_rebar_kg",
            0,
        )
        for r in results
    )

    all_details = []

    for r in results:
        all_details.extend(
            r.get(
                "rebar_details",
                [],
            )
        )

    final = finalize_rebar_details(
        all_details
    )

    return {
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_rebar,
        "rebar_details": final,
    }


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def cut_list_from_details(rebar_details):
    """
    Rebuilds cut-list information directly from 12m stock bars.
    Waste is ALWAYS recalculated as:
        12.0 - used
    """

    result = []

    for detail in rebar_details:

        dia = int(
            detail["diameter_mm"]
        )

        pieces = detail.get(
            "piece_lengths_m",
            [],
        )

        plan = optimize_12m_bars(
            pieces
        )

        result.append(
            {
                "diameter_mm": dia,
                "stock_bars": plan[
                    "stock_bars"
                ],
                "waste_m": plan[
                    "waste_m"
                ],
                "plans": plan[
                    "plans"
                ],
            }
        )

    return result


# ------------------------------------------------------------
# Standard information helper for bot.py
# ------------------------------------------------------------

def standard_summary(standard):
    standard = normalize_standard(
        standard
    )

    info = get_standard_info(
        standard
    )

    return {
        "id": standard,
        "name": info["name"],
        "code": info["code"],
    }
