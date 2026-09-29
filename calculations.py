# calculations.py
# -*- coding: utf-8 -*-

import math


# =========================================================
# CONSTANTS
# =========================================================

STOCK_BAR_LENGTH_M = 12.0

REBAR_WEIGHT = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.210,
    16: 1.580,
    18: 2.000,
    20: 2.470,
    22: 2.980,
    25: 3.850,
    28: 4.830,
    32: 6.310,
    36: 7.990,
}


# =========================================================
# STANDARD DEFINITIONS
# =========================================================

STANDARD_IRAN = "iran"
STANDARD_ACI = "aci318"
STANDARD_EUROCODE = "eurocode2"


def normalize_standard(standard):
    """
    Converts different names/codes to one internal value.
    """

    if not standard:
        return STANDARD_IRAN

    value = str(standard).strip().lower()

    aliases = {
        "iran": STANDARD_IRAN,
        "مبحث ۹": STANDARD_IRAN,
        "مبحث9": STANDARD_IRAN,
        "mبحث9": STANDARD_IRAN,
        "nbci": STANDARD_IRAN,

        "aci": STANDARD_ACI,
        "aci318": STANDARD_ACI,
        "aci 318": STANDARD_ACI,
        "aci-318": STANDARD_ACI,

        "eurocode": STANDARD_EUROCODE,
        "eurocode2": STANDARD_EUROCODE,
        "eurocode 2": STANDARD_EUROCODE,
        "en1992": STANDARD_EUROCODE,
        "en 1992-1-1": STANDARD_EUROCODE,
    }

    return aliases.get(value, STANDARD_IRAN)


# =========================================================
# PROJECT SETTINGS
# =========================================================

def project_settings(
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_grade="A3",
    rebar_yield_mpa=None,
):
    """
    Project-level settings.

    These values should be entered once per project,
    not repeatedly for every member.
    """

    standard = normalize_standard(standard)

    fc = float(concrete_strength_mpa)

    if fc <= 0:
        raise ValueError(
            "Concrete strength must be positive."
        )

    if rebar_yield_mpa is not None:
        fy = float(rebar_yield_mpa)
    else:
        fy = rebar_grade_yield_mpa(
            rebar_grade,
            standard,
        )

    return {
        "standard": standard,
        "concrete_strength_mpa": fc,
        "rebar_grade": str(rebar_grade),
        "rebar_yield_mpa": fy,
    }


def rebar_grade_yield_mpa(
    grade,
    standard=STANDARD_IRAN,
):
    """
    Project-level default yield strength.

    The exact material designation should eventually
    come from the selected material database.
    """

    standard = normalize_standard(standard)
    value = str(grade).strip().upper()

    # Iranian common designations
    if standard == STANDARD_IRAN:

        iran_values = {
            "A1": 240.0,
            "A2": 300.0,
            "A3": 400.0,
            "A4": 500.0,
        }

        return iran_values.get(
            value,
            400.0,
        )

    # Eurocode commonly uses steel grade B500
    if standard == STANDARD_EUROCODE:

        euro_values = {
            "B400": 400.0,
            "B500": 500.0,
            "B500A": 500.0,
            "B500B": 500.0,
            "B500C": 500.0,
        }

        return euro_values.get(
            value,
            500.0,
        )

    # ACI commonly uses Grade 60
    if standard == STANDARD_ACI:

        aci_values = {
            "GRADE40": 280.0,
            "GRADE 40": 280.0,
            "GRADE60": 420.0,
            "GRADE 60": 420.0,
            "60": 420.0,
        }

        return aci_values.get(
            value,
            420.0,
        )

    return 400.0


# =========================================================
# REBAR BASIC CALCULATIONS
# =========================================================

def rebar_unit_weight(diameter_mm):
    d = float(diameter_mm)

    if d <= 0:
        return 0.0

    if int(d) in REBAR_WEIGHT:
        return REBAR_WEIGHT[int(d)]

    return d * d / 162.0


def rebar_weight(length_m, diameter_mm):
    return (
        float(length_m)
        * rebar_unit_weight(diameter_mm)
    )


def rebar_area_mm2(diameter_mm):
    d = float(diameter_mm)

    if d <= 0:
        return 0.0

    return math.pi * d * d / 4.0


def bars_12m(length_m):
    if length_m <= 0:
        return 0

    return math.ceil(
        float(length_m)
        / STOCK_BAR_LENGTH_M
    )


# =========================================================
# COVER
# =========================================================

def default_cover_mm(
    standard,
    member_type,
    exposure="normal",
    cast_against_ground=False,
):
    """
    Internal cover selector.

    IMPORTANT:
    This is an engineering input layer, not a replacement
    for the complete project-specific durability/fire design.

    Ground-contact concrete is treated separately.
    """

    standard = normalize_standard(
        standard
    )

    member = str(
        member_type
    ).strip().lower()

    if cast_against_ground:
        # Conservative construction-side default.
        # Final project design must verify the exact code condition.
        return 75.0

    # Generic member categories.
    # These values are intentionally kept as internal defaults
    # and can be refined when exposure/fire conditions are collected.
    if member in {
        "footing",
        "foundation",
        "raft",
        "strip_footing",
    }:
        return 50.0

    if member in {
        "column",
        "column_rect",
        "column_round",
    }:
        return 40.0

    if member in {
        "beam",
        "tie",
        "wall",
        "stair",
    }:
        return 40.0

    if member in {
        "roof",
        "slab",
    }:
        return 30.0

    return 40.0


def usable_length(
    total_length_m,
    cover_mm=50,
):
    total = float(total_length_m)
    cover = float(cover_mm)

    return max(
        total
        - 2.0 * cover / 1000.0,
        0.0,
    )


# =========================================================
# BAR COUNT
# =========================================================

def number_of_bars_in_direction(
    usable_length_m,
    spacing_mm,
):
    usable = float(usable_length_m)
    spacing = float(spacing_mm)

    if usable <= 0 or spacing <= 0:
        return 0

    return (
        math.floor(
            usable
            / (spacing / 1000.0)
        )
        + 1
    )


# =========================================================
# DEVELOPMENT / SPLICE ENGINE
# =========================================================

def development_length(
    standard,
    diameter_mm,
    concrete_strength_mpa,
    rebar_yield_mpa,
    member_type="beam",
    tension=True,
    bond_condition="good",
):
    """
    Returns an engineering development-length estimate
    using a standard-specific calculation path.

    IMPORTANT:
    A final design check may require additional parameters:
    bar position, confinement, coating, transverse reinforcement,
    seismic detailing, member condition, etc.

    Therefore this function exposes the assumptions explicitly.
    """

    standard = normalize_standard(
        standard
    )

    db = float(diameter_mm)
    fc = float(concrete_strength_mpa)
    fy = float(rebar_yield_mpa)

    if db <= 0:
        raise ValueError(
            "Bar diameter must be positive."
        )

    if fc <= 0:
        raise ValueError(
            "Concrete strength must be positive."
        )

    if fy <= 0:
        raise ValueError(
            "Rebar yield strength must be positive."
        )

    # -----------------------------------------------------
    # EUROCODE 2
    # -----------------------------------------------------
    #
    # EC2 uses:
    # l_bd = alpha factors × basic anchorage length
    #
    # Exact alpha factors depend on anchorage geometry,
    # cover, confinement, bar position, etc.
    #
    # For a straight bar with good bond and normal conditions,
    # use the EC2 basic relationship here.
    #
    # f_bd = 2.25 × eta1 × eta2 × f_ctd
    #
    # f_ctd = alpha_ct × f_ctk,0.05 / gamma_c
    #
    # For this calculation layer we use a transparent
    # normal-condition approximation and expose the assumptions.
    # -----------------------------------------------------

    if standard == STANDARD_EUROCODE:

        # Approximate fctm relationship for normal concrete
        if fc <= 50:
            fctm = 0.30 * (
                fc ** (2.0 / 3.0)
            )
        else:
            fctm = (
                2.12
                * math.log(
                    1.0
                    + fc / 10.0
                )
            )

        fctk05 = 0.70 * fctm

        gamma_c = 1.50

        f_ctd = (
            fctk05
            / gamma_c
        )

        eta1 = 1.0 if bond_condition == "good" else 0.7

        eta2 = min(
            1.0,
            (
                132.0 - db
            ) / 100.0,
        )

        f_bd = max(
            2.25
            * eta1
            * eta2
            * f_ctd,
            0.001,
        )

        alpha_1 = 1.0
        alpha_2 = 1.0
        alpha_3 = 1.0
        alpha_4 = 1.0
        alpha_5 = 1.0

        l_b_rqd = (
            db
            / 4.0
            * fy
            / f_bd
        )

        l_bd = (
            alpha_1
            * alpha_2
            * alpha_3
            * alpha_4
            * alpha_5
            * l_b_rqd
        )

        l_bd = max(
            l_bd,
            10.0 * db,
        )

        return l_bd / 1000.0

    # -----------------------------------------------------
    # IRAN / Mبحث 9
    # -----------------------------------------------------
    #
    # The Iranian path is deliberately separated from ACI
    # and Eurocode. The exact Chapter 21 parameters depend
    # on bar/concrete/member/detailing conditions.
    #
    # We therefore calculate a transparent base development
    # value and do not pretend that one fixed multiplier is
    # the complete Mبحث 9 design check.
    # -----------------------------------------------------

    if standard == STANDARD_IRAN:

        # Base bond-style calculation.
        # This is an internal calculation layer.
        #
        # Final detailed implementation can add:
        # Ktr, cover, confinement, top-bar factor,
        # bar location and seismic conditions.

        sqrt_fc = math.sqrt(
            max(fc, 1.0)
        )

        base = (
            fy
            * db
            / (
                4.0
                * sqrt_fc
            )
        )

        # Minimum practical anchorage floor.
        # The final project-specific Chapter 21 check
        # should still be applied.
        ld_mm = max(
            base,
            300.0,
        )

        return ld_mm / 1000.0

    # -----------------------------------------------------
    # ACI 318
    # -----------------------------------------------------
    #
    # ACI 318-25 has dedicated development/splice provisions.
    # A complete ACI calculation requires additional conditions
    # such as bar location, coating, confinement and geometry.
    #
    # This path therefore calculates the base development
    # requirement without silently inventing those missing
    # modifiers.
    # -----------------------------------------------------

    if standard == STANDARD_ACI:

        # SI-compatible base expression.
        # Additional ACI modifiers are intentionally exposed
        # rather than hidden in an arbitrary fixed percentage.

        sqrt_fc = math.sqrt(
            max(fc, 1.0)
        )

        base = (
            fy
            * db
            / (
                4.0
                * sqrt_fc
            )
        )

        ld_mm = max(
            base,
            300.0,
        )

        return ld_mm / 1000.0

    return 0.0


def splice_length(
    standard,
    diameter_mm,
    concrete_strength_mpa,
    rebar_yield_mpa,
    member_type="beam",
    tension=True,
    bond_condition="good",
):
    """
    Standard-specific lap-splice calculation.

    This deliberately does NOT use:
        length × 1.10
        length × 1.15
        or another arbitrary percentage.

    The actual splice requirement depends on the selected
    standard and detailing conditions.
    """

    ld = development_length(
        standard=standard,
        diameter_mm=diameter_mm,
        concrete_strength_mpa=concrete_strength_mpa,
        rebar_yield_mpa=rebar_yield_mpa,
        member_type=member_type,
        tension=tension,
        bond_condition=bond_condition,
    )

    standard = normalize_standard(
        standard
    )

    if standard == STANDARD_EUROCODE:
        # EC2 lap length depends on the proportion of
        # lapped bars and transverse reinforcement.
        # For the base/default path we use the full
        # development length.
        return ld

    if standard == STANDARD_IRAN:
        return ld

    if standard == STANDARD_ACI:
        return ld

    return ld


def piece_length_with_splice(
    base_length_m,
    standard,
    diameter_mm,
    concrete_strength_mpa,
    rebar_yield_mpa,
    member_type="beam",
):
    """
    Adds only the calculated splice/anchorage allowance
    when a bar piece actually needs a splice.

    For a continuous single piece, the base length is retained.
    """

    base = float(base_length_m)

    if base <= 0:
        return 0.0

    splice = splice_length(
        standard=standard,
        diameter_mm=diameter_mm,
        concrete_strength_mpa=concrete_strength_mpa,
        rebar_yield_mpa=rebar_yield_mpa,
        member_type=member_type,
    )

    # This function represents one required development/
    # splice allowance. The calling member determines whether
    # an actual splice is necessary.
    return base + splice


# =========================================================
# 12 m CUTTING
# =========================================================

def optimize_12m_bars(
    piece_lengths,
):
    clean = []

    for value in piece_lengths:

        if value is None:
            continue

        value = float(value)

        if value <= 0:
            continue

        if value > STOCK_BAR_LENGTH_M + 0.000001:
            raise ValueError(
                f"Bar piece length {value:.2f} m "
                f"is longer than 12 m."
            )

        clean.append(value)

    clean.sort(
        reverse=True
    )

    bars = []

    for piece in clean:

        placed = False

        for bar in bars:

            if (
                bar["used_m"]
                + piece
                <= STOCK_BAR_LENGTH_M
                + 0.000001
            ):

                bar["pieces"].append(
                    piece
                )

                bar["used_m"] += piece

                bar["waste_m"] = (
                    STOCK_BAR_LENGTH_M
                    - bar["used_m"]
                )

                placed = True
                break

        if not placed:

            bars.append(
                {
                    "pieces": [piece],
                    "used_m": piece,
                    "waste_m":
                        STOCK_BAR_LENGTH_M
                        - piece,
                }
            )

    return {
        "stock_bars": len(bars),

        "waste_m": sum(
            STOCK_BAR_LENGTH_M
            - float(x["used_m"])
            for x in bars
        ),

        "plans": bars,
    }


# =========================================================
# REBAR DETAIL
# =========================================================

def make_rebar_detail(
    diameter_mm,
    piece_lengths,
    description="",
):
    pieces = [
        float(x)
        for x in piece_lengths
        if x is not None
        and float(x) > 0
    ]

    optimization = optimize_12m_bars(
        pieces
    )

    total_length = sum(
        pieces
    )

    return {
        "diameter_mm":
            int(diameter_mm),

        "length_m":
            total_length,

        "weight_kg":
            rebar_weight(
                total_length,
                diameter_mm,
            ),

        "bars_12m":
            optimization[
                "stock_bars"
            ],

        "piece_count":
            len(pieces),

        "piece_lengths_m":
            pieces,

        "waste_m":
            sum(
                STOCK_BAR_LENGTH_M
                - float(x["used_m"])
                for x in optimization[
                    "plans"
                ]
            ),

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
):
    if not piece_lengths:
        return

    details.append(
        make_rebar_detail(
            diameter_mm,
            piece_lengths,
            description,
        )
    )


def finalize_rebar_details(
    details,
):
    grouped = {}
    descriptions = {}

    for detail in details:

        diameter = int(
            detail["diameter_mm"]
        )

        grouped.setdefault(
            diameter,
            [],
        ).extend(
            detail.get(
                "piece_lengths_m",
                [],
            )
        )

        description = detail.get(
            "description",
            "",
        )

        if description:

            descriptions.setdefault(
                diameter,
                [],
            )

            if description not in descriptions[
                diameter
            ]:

                descriptions[
                    diameter
                ].append(
                    description
                )

    output = []

    for diameter in sorted(
        grouped
    ):

        pieces = grouped[
            diameter
        ]

        optimization = optimize_12m_bars(
            pieces
        )

        total_length = sum(
            pieces
        )

        output.append(
            {
                "diameter_mm":
                    diameter,

                "length_m":
                    total_length,

                "weight_kg":
                    rebar_weight(
                        total_length,
                        diameter,
                    ),

                "bars_12m":
                    optimization[
                        "stock_bars"
                    ],

                "piece_count":
                    len(pieces),

                "piece_lengths_m":
                    pieces,

                "waste_m":
                    sum(
                        STOCK_BAR_LENGTH_M
                        - float(
                            x["used_m"]
                        )
                        for x in optimization[
                            "plans"
                        ]
                    ),

                "cut_plan":
                    optimization[
                        "plans"
                    ],

                "description":
                    " + ".join(
                        descriptions.get(
                            diameter,
                            [],
                        )
                    ),
            }
        )

    return output


# =========================================================
# RESULT
# =========================================================

def _member_result(
    concrete,
    details,
    **extra,
):
    final = finalize_rebar_details(
        details
    )

    return {
        "concrete_m3":
            float(concrete),

        "total_concrete_m3":
            float(concrete),

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            ),

        "rebar_details":
            final,

        **extra,
    }


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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
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

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "footing",
            cast_against_ground=True,
        )

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
        [L] * (
            nx * count
        ),
        "پی منفرد - شبکه پایین X",
    )

    add_rebar_detail(
        details,
        bottom_diameter_mm,
        [W] * (
            ny * count
        ),
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
            [L] * (
                nx * count
            ),
            "پی منفرد - شبکه بالا X",
        )

        add_rebar_detail(
            details,
            top_diameter_mm,
            [W] * (
                ny * count
            ),
            "پی منفرد - شبکه بالا Y",
        )

    final = finalize_rebar_details(
        details
    )

    return {
        "lean_concrete_m3":
            lean,

        "footing_concrete_m3":
            footing,

        "pedestal_concrete_m3":
            pedestal,

        "total_concrete_m3":
            lean
            + footing
            + pedestal,

        "bottom_rebar_weight_kg":
            sum(
                x["weight_kg"]
                for x in final
            ),

        "top_rebar_weight_kg":
            0,

        "total_rebar_kg":
            sum(
                x["weight_kg"]
                for x in final
            ),

        "rebar_details":
            final,

        "standard":
            normalize_standard(
                standard
            ),
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
    lap_percent=0,
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    n = int(strip_count)

    concrete = (
        n
        * strip_length_m
        * footing_width_m
        * footing_thickness_m
    )

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "strip_footing",
            cast_against_ground=True,
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
            int(longitudinal_count)
            * n
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
        [W] * (
            nc * n
        ),
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
                int(
                    top_longitudinal_count
                )
                * n
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
            [W] * (
                nc * n
            ),
            "پی نواری - عرضی بالا",
        )

    return _member_result(
        concrete,
        details,
        count=n,
        standard=normalize_standard(
            standard
        ),
    )


# =========================================================
# RAFT
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "raft",
            cast_against_ground=True,
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
        standard=normalize_standard(
            standard
        ),
    )


# =========================================================
# COLUMNS
# =========================================================

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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    n = int(count)

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "column_rect",
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
            int(long_count)
            * n
        ),
        "ستون - میلگرد طولی",
    )

    stirrup_count = max(
        1,
        math.floor(
            L
            / (
                stirrup_spacing
                / 1000.0
            )
        )
        + 1,
    )

    stirrup_width = max(
        width_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_depth = max(
        depth_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_length = 2 * (
        stirrup_width
        + stirrup_depth
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_length]
        * (
            stirrup_count
            * n
        ),
        "ستون - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
        standard=normalize_standard(
            standard
        ),
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    n = int(count)

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "column_round",
        )

    concrete = (
        n
        * math.pi
        * diameter_m ** 2
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
            int(long_count)
            * n
        ),
        "ستون گرد - میلگرد طولی",
    )

    stirrup_count = max(
        1,
        math.floor(
            L
            / (
                stirrup_spacing
                / 1000.0
            )
        )
        + 1,
    )

    ring_diameter = max(
        diameter_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    ring_length = (
        math.pi
        * ring_diameter
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [ring_length]
        * (
            stirrup_count
            * n
        ),
        "ستون گرد - خاموت حلقوی",
    )

    return _member_result(
        concrete,
        details,
        count=n,
        standard=normalize_standard(
            standard
        ),
    )


# =========================================================
# BEAM
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    n = int(count)

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "beam",
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
            int(bottom_count)
            * n
        ),
        "تیر - میلگرد طولی پایین",
    )

    add_rebar_detail(
        details,
        top_dia,
        [L] * (
            int(top_count)
            * n
        ),
        "تیر - میلگرد طولی بالا",
    )

    stirrup_count = max(
        1,
        math.floor(
            L
            / (
                stirrup_spacing
                / 1000.0
            )
        )
        + 1,
    )

    stirrup_width = max(
        width_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_height = max(
        height_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_length = 2 * (
        stirrup_width
        + stirrup_height
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_length]
        * (
            stirrup_count
            * n
        ),
        "تیر - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
        standard=normalize_standard(
            standard
        ),
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    n = int(count)

    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "tie",
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
            int(long_count)
            * n
        ),
        "شناژ/کلاف - طولی",
    )

    stirrup_count = max(
        1,
        math.floor(
            L
            / (
                stirrup_spacing
                / 1000.0
            )
        )
        + 1,
    )

    stirrup_width = max(
        width_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_height = max(
        height_m
        - 2 * cover_mm / 1000.0,
        0,
    )

    stirrup_length = 2 * (
        stirrup_width
        + stirrup_height
    )

    add_rebar_detail(
        details,
        stirrup_dia,
        [stirrup_length]
        * (
            stirrup_count
            * n
        ),
        "شناژ/کلاف - خاموت",
    )

    return _member_result(
        concrete,
        details,
        count=n,
        standard=normalize_standard(
            standard
        ),
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "wall",
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

    vertical_count = number_of_bars_in_direction(
        W,
        vertical_spacing,
    )

    horizontal_count = number_of_bars_in_direction(
        L,
        horizontal_spacing,
    )

    add_rebar_detail(
        details,
        vertical_dia,
        [L] * vertical_count,
        "دیوار - میلگرد قائم",
    )

    add_rebar_detail(
        details,
        horizontal_dia,
        [W] * horizontal_count,
        "دیوار - میلگرد افقی",
    )

    return _member_result(
        concrete,
        details,
        standard=normalize_standard(
            standard
        ),
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
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    cover = default_cover_mm(
        standard,
        "stair",
    )

    concrete = (
        length_m
        * width_m
        * thickness_m
    )

    details = []

    L = usable_length(
        length_m,
        cover,
    )

    W = usable_length(
        width_m,
        cover,
    )

    main_count = number_of_bars_in_direction(
        W,
        main_spacing,
    )

    distribution_count = number_of_bars_in_direction(
        L,
        dist_spacing,
    )

    add_rebar_detail(
        details,
        main_dia,
        [L] * main_count,
        "راه‌پله - میلگرد اصلی",
    )

    add_rebar_detail(
        details,
        dist_dia,
        [W] * distribution_count,
        "راه‌پله - میلگرد توزیعی",
    )

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

    return _member_result(
        concrete,
        details,
        steps=steps,
        standard=normalize_standard(
            standard
        ),
    )


# =========================================================
# ROOF THERMAL MESH
# =========================================================

ROOF_CONCRETE_COEFF = {
    "foam": 0.18,
    "clay": 0.20,
    "double": 0.23,
    "kromit": 0.18,
    "composite": 0.15,
    "steeldeck": 0.15,
    "slab": 0.20,
    "waffle": 0.20,
}


def roof_mesh(
    length_m,
    width_m,
    thickness_m,
    mesh_diameter_mm,
    mesh_spacing_mm,
    concrete_coeff=0.20,
    cover_mm=None,
    standard=STANDARD_IRAN,
    concrete_strength_mpa=25,
    rebar_yield_mpa=400,
):
    if cover_mm is None:
        cover_mm = default_cover_mm(
            standard,
            "roof",
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

    bars_across_width = number_of_bars_in_direction(
        W,
        mesh_spacing_mm,
    )

    bars_across_length = number_of_bars_in_direction(
        L,
        mesh_spacing_mm,
    )

    details = []

    add_rebar_detail(
        details,
        mesh_diameter_mm,
        [L] * bars_across_width,
        "سقف - شبکه حرارتی X",
    )

    add_rebar_detail(
        details,
        mesh_diameter_mm,
        [W] * bars_across_length,
        "سقف - شبکه حرارتی Y",
    )

    return _member_result(
        concrete,
        details,
        area_m2=(
            length_m
            * width_m
        ),
        mesh_diameter_mm=int(
            mesh_diameter_mm
        ),
        mesh_spacing_mm=float(
            mesh_spacing_mm
        ),
        standard=normalize_standard(
            standard
        ),
    )


def roof_slab(
    area_m2,
    concrete_coeff,
    rebar_dia,
    rebar_kg_m2=0,
):
    """
    Backward-compatible old API.

    New UI should use roof_mesh().
    """

    concrete = (
        float(area_m2)
        * float(concrete_coeff)
    )

    details = []

    if rebar_kg_m2 > 0:

        target_weight = (
            float(area_m2)
            * float(rebar_kg_m2)
        )

        total_length = (
            target_weight
            / rebar_unit_weight(
                rebar_dia
            )
        )

        add_rebar_detail(
            details,
            rebar_dia,
            [total_length],
            "سقف - میلگرد حرارتی",
        )

    return _member_result(
        concrete,
        details,
        area_m2=float(area_m2),
    )


# =========================================================
# REBAR EQUIVALENCY
# =========================================================

def equivalent_rebar_count(
    current_count,
    current_diameter_mm,
    replacement_diameter_mm,
    standard=STANDARD_IRAN,
):
    """
    Fast substitution check.

    The mathematical equivalency is based on required
    reinforcement area.

    A complete structural substitution check additionally
    requires member design, spacing, development/splice,
    minimum/maximum reinforcement and detailing conditions.
    """

    current_count = int(
        current_count
    )

    current_diameter_mm = float(
        current_diameter_mm
    )

    replacement_diameter_mm = float(
        replacement_diameter_mm
    )

    if current_count <= 0:
        raise ValueError(
            "Current bar count must be positive."
        )

    current_area = (
        current_count
        * rebar_area_mm2(
            current_diameter_mm
        )
    )

    replacement_one_area = (
        rebar_area_mm2(
            replacement_diameter_mm
        )
    )

    required_count = math.ceil(
        current_area
        / replacement_one_area
    )

    replacement_area = (
        required_count
        * replacement_one_area
    )

    return {
        "standard":
            normalize_standard(
                standard
            ),

        "current_count":
            current_count,

        "current_diameter_mm":
            int(current_diameter_mm),

        "current_area_mm2":
            current_area,

        "replacement_diameter_mm":
            int(
                replacement_diameter_mm
            ),

        "required_count":
            required_count,

        "replacement_area_mm2":
            replacement_area,

        "area_difference_mm2":
            replacement_area
            - current_area,

        "area_ratio":
            replacement_area
            / current_area,

        "area_equivalent":
            replacement_area
            >= current_area,
    }


# =========================================================
# PROJECT TOTAL
# =========================================================

def total_foundation_result(
    results,
):
    total_concrete = sum(
        float(
            r.get(
                "total_concrete_m3",
                0,
            )
            or 0
        )
        for r in results
    )

    total_rebar = sum(
        float(
            r.get(
                "total_rebar_kg",
                0,
            )
            or 0
        )
        for r in results
    )

    final = finalize_rebar_details(
        [
            detail
            for result in results
            for detail in result.get(
                "rebar_details",
                [],
            )
        ]
    )

    return {
        "total_concrete_m3":
            total_concrete,

        "total_rebar_kg":
            total_rebar,

        "rebar_details":
            final,
    }
