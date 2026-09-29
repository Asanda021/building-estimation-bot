# calculations.py
# -*- coding: utf-8 -*-

import math


# =========================================================
# REBAR WEIGHTS
# kg/m
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
    28: 4.837,
    32: 6.313,
    36: 7.990,
    40: 9.865,
}


# =========================================================
# BASIC HELPERS
# =========================================================

def rebar_weight(diameter_mm):
    diameter_mm = int(diameter_mm)

    if diameter_mm not in REBAR_WEIGHT:
        raise ValueError(
            f"قطر میلگرد Φ{diameter_mm} در جدول وزن تعریف نشده است."
        )

    return REBAR_WEIGHT[diameter_mm]


def bars_12m(piece_count, piece_length):
    """
    حداقل تعداد شاخه 12 متری موردنیاز
    بر اساس مجموع طول قطعات.
    """
    piece_count = int(piece_count)
    piece_length = float(piece_length)

    if piece_count <= 0 or piece_length <= 0:
        return 0

    total_length = piece_count * piece_length

    return math.ceil(total_length / 12.0)


def number_of_bars_in_direction(length_m, spacing_mm):
    """
    تعداد میلگرد در یک جهت.
    """
    length_m = float(length_m)
    spacing_mm = float(spacing_mm)

    if length_m <= 0 or spacing_mm <= 0:
        return 0

    spacing_m = spacing_mm / 1000.0

    return max(
        2,
        math.ceil(length_m / spacing_m) + 1
    )


def usable_length(length_m, cover_mm):
    """
    طول مفید میلگرد در یک جهت با کسر کاور دو طرف.
    """
    length_m = float(length_m)
    cover_mm = float(cover_mm)

    value = length_m - (2.0 * cover_mm / 1000.0)

    return max(0.0, value)


def bar_length_with_lap(length_m, lap_percent):
    """
    اضافه‌کردن درصد اورلپ به طول قطعه.
    """
    return float(length_m) * (
        1.0 + float(lap_percent) / 100.0
    )


# =========================================================
# CUT LIST OPTIMIZER
# =========================================================

def optimize_12m_bars(piece_length, piece_count):
    """
    قطعات مساوی را تا حد امکان داخل شاخه‌های 12 متری می‌چیند.

    خروجی:
        bars
        waste_m
        cut_plan
        total_used_m
    """

    piece_length = float(piece_length)
    piece_count = int(piece_count)

    if piece_length <= 0 or piece_count <= 0:
        return {
            "bars": 0,
            "waste_m": 0.0,
            "cut_plan": [],
            "total_used_m": 0.0,
        }

    if piece_length > 12.0:
        raise ValueError(
            f"طول قطعه {piece_length:.2f} متر بیشتر از شاخه 12 متری است."
        )

    pieces_per_bar = int(
        math.floor(
            12.0 / piece_length
        )
    )

    if pieces_per_bar < 1:
        raise ValueError(
            "قطعه قابل برش از شاخه 12 متری نیست."
        )

    remaining = piece_count
    cut_plan = []
    total_used = 0.0

    while remaining > 0:

        count = min(
            pieces_per_bar,
            remaining
        )

        pieces = [
            piece_length
            for _ in range(count)
        ]

        used = sum(pieces)

        waste = max(
            0.0,
            12.0 - used
        )

        cut_plan.append({
            "pieces": pieces,
            "used_m": used,
            "waste_m": waste,
        })

        total_used += used
        remaining -= count

    return {
        "bars": len(cut_plan),
        "waste_m": sum(
            item["waste_m"]
            for item in cut_plan
        ),
        "cut_plan": cut_plan,
        "total_used_m": total_used,
    }


# =========================================================
# REBAR DETAIL
# =========================================================

def make_rebar_detail(
    diameter_mm,
    piece_count,
    length_m,
    description="",
):
    """
    ساخت جزئیات میلگرد + Cut List.
    """

    diameter_mm = int(diameter_mm)
    piece_count = int(piece_count)
    length_m = float(length_m)

    if diameter_mm <= 0 or piece_count <= 0 or length_m <= 0:
        return None

    kgm = rebar_weight(
        diameter_mm
    )

    plan = optimize_12m_bars(
        length_m,
        piece_count
    )

    total_length = (
        piece_count * length_m
    )

    total_weight = (
        total_length * kgm
    )

    return {
        "diameter_mm": diameter_mm,
        "piece_count": piece_count,
        "length_m": length_m,
        "total_length_m": total_length,
        "weight_kg": total_weight,
        "bars_12m": plan["bars"],
        "waste_m": plan["waste_m"],
        "cut_plan": plan["cut_plan"],
        "description": description,
    }


def add_rebar_detail(
    details,
    diameter_mm,
    piece_count,
    length_m,
    description="",
):
    item = make_rebar_detail(
        diameter_mm,
        piece_count,
        length_m,
        description
    )

    if item:
        details.append(item)


def finalize_rebar_details(details):
    total_weight = sum(
        float(
            item.get(
                "weight_kg",
                0
            )
        )
        for item in details
    )

    total_bars = sum(
        int(
            item.get(
                "bars_12m",
                0
            )
        )
        for item in details
    )

    total_waste = sum(
        float(
            item.get(
                "waste_m",
                0
            )
        )
        for item in details
    )

    return (
        details,
        total_weight,
        total_bars,
        total_waste,
    )


# =========================================================
# RESULT BUILDER
# =========================================================

def _result(
    concrete_m3=0.0,
    rebar_details=None,
    extra=None,
):
    if rebar_details is None:
        rebar_details = []

    (
        rebar_details,
        total_rebar_kg,
        total_bars_12m,
        total_waste_m,
    ) = finalize_rebar_details(
        rebar_details
    )

    result = {
        "concrete_m3": float(concrete_m3),
        "total_concrete_m3": float(concrete_m3),
        "total_rebar_kg": float(total_rebar_kg),
        "total_bars_12m": int(total_bars_12m),
        "total_waste_m": float(total_waste_m),
        "rebar_details": rebar_details,
    }

    if extra:
        result.update(extra)

    return result


# =========================================================
# ISOLATED FOOTING
# =========================================================

def isolated_footing(
    count,
    L,
    W,
    T,
    leanL,
    leanW,
    leanT,
    bd,
    bs,
    td=None,
    ts=None,
    cover=50,
    lap=10,
    pl=0,
    pw=0,
    ph=0,
):
    count = int(count)

    L = float(L)
    W = float(W)
    T = float(T)

    leanL = float(leanL)
    leanW = float(leanW)
    leanT = float(leanT)

    cover = float(cover)
    lap = float(lap)

    # -------------------------
    # Concrete
    # -------------------------

    footing_concrete = (
        count * L * W * T
    )

    lean_concrete = (
        count * leanL * leanW * leanT
    )

    pedestal_concrete = (
        count * float(pl)
        * float(pw)
        * float(ph)
    )

    total_concrete = (
        footing_concrete
        + lean_concrete
        + pedestal_concrete
    )

    # -------------------------
    # Bottom reinforcement
    # -------------------------

    details = []

    bottom_piece_length_x = (
        usable_length(
            L,
            cover
        )
    )

    bottom_piece_length_y = (
        usable_length(
            W,
            cover
        )
    )

    # میلگردهای موازی X
    bottom_count_x = (
        number_of_bars_in_direction(
            W,
            bs
        )
    )

    bottom_count_x *= count

    bottom_piece_length_x = (
        bar_length_with_lap(
            bottom_piece_length_x,
            lap
        )
    )

    add_rebar_detail(
        details,
        bd,
        bottom_count_x,
        bottom_piece_length_x,
        "پایین - جهت X"
    )

    # میلگردهای موازی Y
    bottom_count_y = (
        number_of_bars_in_direction(
            L,
            bs
        )
    )

    bottom_count_y *= count

    bottom_piece_length_y = (
        bar_length_with_lap(
            bottom_piece_length_y,
            lap
        )
    )

    add_rebar_detail(
        details,
        bd,
        bottom_count_y,
        bottom_piece_length_y,
        "پایین - جهت Y"
    )

    # -------------------------
    # Top reinforcement
    # -------------------------

    if (
        td is not None
        and ts is not None
        and int(td) > 0
        and float(ts) > 0
    ):

        top_count_x = (
            number_of_bars_in_direction(
                W,
                ts
            )
            * count
        )

        top_count_y = (
            number_of_bars_in_direction(
                L,
                ts
            )
            * count
        )

        top_length_x = bar_length_with_lap(
            usable_length(
                L,
                cover
            ),
            lap
        )

        top_length_y = bar_length_with_lap(
            usable_length(
                W,
                cover
            ),
            lap
        )

        add_rebar_detail(
            details,
            td,
            top_count_x,
            top_length_x,
            "بالا - جهت X"
        )

        add_rebar_detail(
            details,
            td,
            top_count_y,
            top_length_y,
            "بالا - جهت Y"
        )

    return _result(
        total_concrete,
        details,
        {
            "footing_concrete_m3": footing_concrete,
            "lean_concrete_m3": lean_concrete,
            "pedestal_concrete_m3": pedestal_concrete,
            "count": count,
        }
    )


# =========================================================
# STRIP FOOTING
# =========================================================

def strip_footing(
    count,
    L,
    W,
    T,
    leanL,
    leanW,
    leanT,
    ld,
    lc,
    td,
    ts,
    tld=None,
    tlc=None,
    ttd=None,
    tts=None,
    cover=50,
    lap=10,
):
    count = int(count)

    L = float(L)
    W = float(W)
    T = float(T)

    lean_concrete = (
        count
        * float(leanL)
        * float(leanW)
        * float(leanT)
    )

    footing_concrete = (
        count * L * W * T
    )

    total_concrete = (
        footing_concrete
        + lean_concrete
    )

    details = []

    # پایین طولی
    length_longitudinal = bar_length_with_lap(
        usable_length(
            L,
            cover
        ),
        lap
    )

    add_rebar_detail(
        details,
        ld,
        int(lc) * count,
        length_longitudinal,
        "پایین - طولی"
    )

    # پایین عرضی
    transverse_count = (
        number_of_bars_in_direction(
            L,
            ts
        )
        * count
    )

    transverse_length = bar_length_with_lap(
        usable_length(
            W,
            cover
        ),
        lap
    )

    add_rebar_detail(
        details,
        td,
        transverse_count,
        transverse_length,
        "پایین - عرضی"
    )

    # بالا طولی
    if (
        tld is not None
        and tlc is not None
        and int(tld) > 0
        and int(tlc) > 0
    ):

        add_rebar_detail(
            details,
            tld,
            int(tlc) * count,
            length_longitudinal,
            "بالا - طولی"
        )

    # بالا عرضی
    if (
        ttd is not None
        and tts is not None
        and int(ttd) > 0
        and float(tts) > 0
    ):

        top_transverse_count = (
            number_of_bars_in_direction(
                L,
                tts
            )
            * count
        )

        add_rebar_detail(
            details,
            ttd,
            top_transverse_count,
            transverse_length,
            "بالا - عرضی"
        )

    return _result(
        total_concrete,
        details,
        {
            "footing_concrete_m3": footing_concrete,
            "lean_concrete_m3": lean_concrete,
            "count": count,
        }
    )


# =========================================================
# RAFT FOUNDATION
# =========================================================

def raft_foundation(
    L,
    W,
    T,
    leanL,
    leanW,
    leanT,
    bxd,
    bxs,
    byd,
    bys,
    txd=None,
    txs=None,
    tyd=None,
    tys=None,
    cover=50,
    lap=10,
):
    L = float(L)
    W = float(W)
    T = float(T)

    concrete = (
        L * W * T
    )

    lean_concrete = (
        float(leanL)
        * float(leanW)
        * float(leanT)
    )

    total_concrete = (
        concrete
        + lean_concrete
    )

    details = []

    # -------------------------
    # Bottom X
    # -------------------------

    count_x = number_of_bars_in_direction(
        W,
        bxs
    )

    length_x = bar_length_with_lap(
        usable_length(
            L,
            cover
        ),
        lap
    )

    add_rebar_detail(
        details,
        bxd,
        count_x,
        length_x,
        "پایین - X"
    )

    # -------------------------
    # Bottom Y
    # -------------------------

    count_y = number_of_bars_in_direction(
        L,
        bys
    )

    length_y = bar_length_with_lap(
        usable_length(
            W,
            cover
        ),
        lap
    )

    add_rebar_detail(
        details,
        byd,
        count_y,
        length_y,
        "پایین - Y"
    )

    # -------------------------
    # Top X
    # -------------------------

    if (
        txd is not None
        and txs is not None
        and int(txd) > 0
        and float(txs) > 0
    ):

        top_x_count = (
            number_of_bars_in_direction(
                W,
                txs
            )
        )

        add_rebar_detail(
            details,
            txd,
            top_x_count,
            length_x,
            "بالا - X"
        )

    # -------------------------
    # Top Y
    # -------------------------

    if (
        tyd is not None
        and tys is not None
        and int(tyd) > 0
        and float(tys) > 0
    ):

        top_y_count = (
            number_of_bars_in_direction(
                L,
                tys
            )
        )

        add_rebar_detail(
            details,
            tyd,
            top_y_count,
            length_y,
            "بالا - Y"
        )

    return _result(
        total_concrete,
        details,
        {
            "raft_concrete_m3": concrete,
            "lean_concrete_m3": lean_concrete,
        }
    )


# =========================================================
# RECTANGULAR COLUMN
# =========================================================

def column_rectangular(
    count,
    W,
    D,
    H,
    ld,
    lc,
    sd,
    ss,
    cover=40,
):
    count = int(count)

    W = float(W)
    D = float(D)
    H = float(H)

    concrete = (
        count * W * D * H
    )

    details = []

    # طولی
    longitudinal_length = H

    add_rebar_detail(
        details,
        ld,
        int(lc) * count,
        longitudinal_length,
        "میلگرد طولی ستون"
    )

    # خاموت
    stirrup_count_each = (
        math.ceil(
            H * 1000.0 / float(ss)
        )
        + 1
    )

    total_stirrups = (
        stirrup_count_each * count
    )

    stirrup_length = (
        2.0
        * (
            max(
                0.0,
                W - 2.0 * cover / 1000.0
            )
            +
            max(
                0.0,
                D - 2.0 * cover / 1000.0
            )
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        sd,
        total_stirrups,
        stirrup_length,
        "خاموت ستون"
    )

    return _result(
        concrete,
        details,
        {
            "count": count,
            "column_concrete_m3": concrete,
            "stirrup_count": total_stirrups,
        }
    )


# =========================================================
# ROUND COLUMN
# =========================================================

def column_round(
    count,
    D,
    H,
    ld,
    lc,
    sd,
    ss,
    cover=40,
):
    count = int(count)

    D = float(D)
    H = float(H)

    concrete = (
        count
        * math.pi
        * (D ** 2)
        / 4.0
        * H
    )

    details = []

    add_rebar_detail(
        details,
        ld,
        int(lc) * count,
        H,
        "میلگرد طولی ستون گرد"
    )

    stirrup_count_each = (
        math.ceil(
            H * 1000.0 / float(ss)
        )
        + 1
    )

    total_stirrups = (
        stirrup_count_each * count
    )

    stirrup_diameter = max(
        0.0,
        D - 2.0 * cover / 1000.0
    )

    stirrup_length = (
        math.pi
        * stirrup_diameter
        + 0.20
    )

    add_rebar_detail(
        details,
        sd,
        total_stirrups,
        stirrup_length,
        "خاموت دایره‌ای ستون"
    )

    return _result(
        concrete,
        details,
        {
            "count": count,
            "column_concrete_m3": concrete,
            "stirrup_count": total_stirrups,
        }
    )


# =========================================================
# BEAM
# =========================================================

def beam(
    count,
    L,
    W,
    H,
    bd,
    bc,
    td,
    tc,
    sd,
    ss,
    cover=40,
):
    count = int(count)

    L = float(L)
    W = float(W)
    H = float(H)

    concrete = (
        count * L * W * H
    )

    details = []

    longitudinal_length = L

    # پایین
    add_rebar_detail(
        details,
        bd,
        int(bc) * count,
        longitudinal_length,
        "میلگرد پایین تیر"
    )

    # بالا
    add_rebar_detail(
        details,
        td,
        int(tc) * count,
        longitudinal_length,
        "میلگرد بالا تیر"
    )

    # خاموت
    stirrup_count_each = (
        math.ceil(
            L * 1000.0 / float(ss)
        )
        + 1
    )

    total_stirrups = (
        stirrup_count_each * count
    )

    stirrup_length = (
        2.0
        * (
            max(
                0.0,
                W - 2.0 * cover / 1000.0
            )
            +
            max(
                0.0,
                H - 2.0 * cover / 1000.0
            )
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        sd,
        total_stirrups,
        stirrup_length,
        "خاموت تیر"
    )

    return _result(
        concrete,
        details,
        {
            "count": count,
            "beam_concrete_m3": concrete,
            "stirrup_count": total_stirrups,
        }
    )


# =========================================================
# TIE BEAM / TIE
# =========================================================

def tie_beam(
    count,
    L,
    W,
    H,
    ld,
    lc,
    sd,
    ss,
    cover=40,
):
    count = int(count)

    L = float(L)
    W = float(W)
    H = float(H)

    concrete = (
        count * L * W * H
    )

    details = []

    add_rebar_detail(
        details,
        ld,
        int(lc) * count,
        L,
        "میلگرد طولی شناژ"
    )

    stirrup_count_each = (
        math.ceil(
            L * 1000.0 / float(ss)
        )
        + 1
    )

    total_stirrups = (
        stirrup_count_each * count
    )

    stirrup_length = (
        2.0
        * (
            max(
                0.0,
                W - 2.0 * cover / 1000.0
            )
            +
            max(
                0.0,
                H - 2.0 * cover / 1000.0
            )
        )
        + 0.20
    )

    add_rebar_detail(
        details,
        sd,
        total_stirrups,
        stirrup_length,
        "خاموت شناژ"
    )

    return _result(
        concrete,
        details,
        {
            "count": count,
            "tie_concrete_m3": concrete,
            "stirrup_count": total_stirrups,
        }
    )


# =========================================================
# WALL
# =========================================================

def wall_concrete(
    L,
    H,
    T,
    vd,
    vs,
    hd,
    hs,
    cover=40,
):
    L = float(L)
    H = float(H)
    T = float(T)

    concrete = (
        L * H * T
    )

    details = []

    # قائم
    vertical_count = (
        number_of_bars_in_direction(
            L,
            vs
        )
    )

    vertical_length = (
        usable_length(
            H,
            cover
        )
    )

    add_rebar_detail(
        details,
        vd,
        vertical_count,
        vertical_length,
        "میلگرد قائم دیوار"
    )

    # افقی
    horizontal_count = (
        number_of_bars_in_direction(
            H,
            hs
        )
    )

    horizontal_length = (
        usable_length(
            L,
            cover
        )
    )

    add_rebar_detail(
        details,
        hd,
        horizontal_count,
        horizontal_length,
        "میلگرد افقی دیوار"
    )

    return _result(
        concrete,
        details,
        {
            "wall_concrete_m3": concrete,
        }
    )


# =========================================================
# STAIR
# =========================================================

def stair_slab(
    L,
    W,
    T,
    md,
    ms,
    dd,
    ds,
    steps,
    riser,
    tread,
):
    L = float(L)
    W = float(W)
    T = float(T)

    steps = int(steps)
    riser = float(riser)
    tread = float(tread)

    # حجم دال شیب‌دار
    concrete = (
        L * W * T
    )

    # حجم تقریبی پله‌ها
    stair_step_concrete = (
        steps
        * tread
        * riser
        * W
        / 2.0
    )

    total_concrete = (
        concrete
        + stair_step_concrete
    )

    details = []

    # میلگرد اصلی
    main_count = (
        number_of_bars_in_direction(
            W,
            ms
        )
    )

    add_rebar_detail(
        details,
        md,
        main_count,
        L,
        "میلگرد اصلی راه‌پله"
    )

    # توزیعی
    dist_count = (
        number_of_bars_in_direction(
            L,
            ds
        )
    )

    add_rebar_detail(
        details,
        dd,
        dist_count,
        W,
        "میلگرد توزیعی راه‌پله"
    )

    return _result(
        total_concrete,
        details,
        {
            "slab_concrete_m3": concrete,
            "step_concrete_m3": stair_step_concrete,
            "steps": steps,
        }
    )


# =========================================================
# ROOF SLAB
# =========================================================

def roof_slab(
    area,
    coeff,
    dia,
    kgm2=0,
):
    area = float(area)
    coeff = float(coeff)
    dia = int(dia)
    kgm2 = float(kgm2)

    if area < 0:
        raise ValueError(
            "مساحت سقف نمی‌تواند منفی باشد."
        )

    if coeff < 0:
        raise ValueError(
            "ضریب بتن سقف نمی‌تواند منفی باشد."
        )

    concrete = (
        area * coeff
    )

    details = []

    # اگر kg/m2 داده شده باشد
    if kgm2 > 0 and dia > 0:

        total_rebar = (
            area * kgm2
        )

        kgm = rebar_weight(
            dia
        )

        total_length = (
            total_rebar / kgm
        )

        piece_length = 12.0

        piece_count = max(
            1,
            math.ceil(
                total_length
                / piece_length
            )
        )

        add_rebar_detail(
            details,
            dia,
            piece_count,
            piece_length,
            "میلگرد مصرفی سقف"
        )

        # وزن واقعی بر اساس قطعات 12 متری
        # را جداگانه در خروجی ثبت می‌کنیم.
        calculated_weight = (
            total_length * kgm
        )

    else:
        calculated_weight = 0.0

    return _result(
        concrete,
        details,
        {
            "roof_area_m2": area,
            "roof_coeff": coeff,
            "target_rebar_kg": calculated_weight,
        }
    )


# =========================================================
# GENERAL TOTAL
# =========================================================

def total_foundation_result(results):
    """
    جمع نتایج چند عضو/مرحله.
    """

    if not results:
        return {
            "total_concrete_m3": 0.0,
            "total_rebar_kg": 0.0,
            "total_bars_12m": 0,
            "total_waste_m": 0.0,
            "rebar_details": [],
        }

    total_concrete = 0.0
    total_rebar = 0.0
    total_bars = 0
    total_waste = 0.0

    all_details = []

    for result in results:

        total_concrete += float(
            result.get(
                "total_concrete_m3",
                result.get(
                    "concrete_m3",
                    0
                )
            )
            or 0
        )

        total_rebar += float(
            result.get(
                "total_rebar_kg",
                0
            )
            or 0
        )

        total_bars += int(
            result.get(
                "total_bars_12m",
                0
            )
            or 0
        )

        total_waste += float(
            result.get(
                "total_waste_m",
                0
            )
            or 0
        )

        all_details.extend(
            result.get(
                "rebar_details",
                []
            )
        )

    return {
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_rebar,
        "total_bars_12m": total_bars,
        "total_waste_m": total_waste,
        "rebar_details": all_details,
    }
