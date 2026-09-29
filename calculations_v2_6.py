import math
import re

# ============================================================
# Structural Quantity / Rebar Calculation Engine
# Version: 2.6
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
    STANDARD_IRAN, STANDARD_ACI, STANDARD_EUROCODE, STANDARD_CHINA
)

STANDARD_EDITIONS = {
    STANDARD_IRAN: "unspecified",
    STANDARD_ACI: "unspecified",
    STANDARD_EUROCODE: "unspecified",
    STANDARD_CHINA: "unspecified",
}


def normalize_standard(value, strict=True):
    """Normalize a standard name. Unknown standards are never silently mapped to Iran."""
    if value is None:
        if strict:
            raise ValueError("Standard is required.")
        return STANDARD_IRAN
    s = str(value).strip().lower().replace(" ", "").replace("-", "")
    aliases = {
        "iran": STANDARD_IRAN, "mبحث9": STANDARD_IRAN, "مبحث9": STANDARD_IRAN,
        "nbci": STANDARD_IRAN, "aci": STANDARD_ACI, "aci318": STANDARD_ACI,
        "aci318-19": STANDARD_ACI, "eurocode": STANDARD_EUROCODE,
        "eurocode2": STANDARD_EUROCODE, "ec2": STANDARD_EUROCODE,
        "china": STANDARD_CHINA, "chinese": STANDARD_CHINA,
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


def project_settings(standard=STANDARD_IRAN, concrete_strength_mpa=25,
                     rebar_grade="A3", rebar_yield_mpa=None, edition=None):
    std = normalize_standard(standard)
    fc = float(concrete_strength_mpa)
    if fc <= 0:
        raise ValueError("Concrete strength must be positive.")
    fy = rebar_yield_mpa if rebar_yield_mpa is not None else rebar_grade_yield_mpa(std, rebar_grade)
    return {
        "standard": std,
        "edition": edition or STANDARD_EDITIONS.get(std, "unspecified"),
        "fc_mpa": fc,
        "rebar_grade": rebar_grade,
        "fy_mpa": float(fy),
    }


def rebar_grade_yield_mpa(standard, grade):
    std = normalize_standard(standard)
    g = str(grade).strip().upper().replace(" ", "")
    tables = {
        STANDARD_IRAN: {"A1": 240, "A2": 300, "A3": 400, "A4": 500},
        STANDARD_ACI: {"GRADE40": 280, "40": 280, "GRADE60": 420, "60": 420},
        STANDARD_EUROCODE: {"B400": 400, "B500": 500, "B500A": 500, "B500B": 500, "B500C": 500},
    }
    if std == STANDARD_CHINA:
        # Do not invent a Chinese grade mapping. Supply fy explicitly until
        # the exact project code/edition/material grade is configured.
        raise ValueError("China rebar grade requires an explicit verified fy value.")
    if g not in tables[std]:
        raise ValueError(f"Unsupported rebar grade '{grade}' for {std}.")
    return tables[std][g]


def _positive(value, name):
    x = float(value)
    if x <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return x


def _nonnegative(value, name):
    x = float(value)
    if x < 0:
        raise ValueError(f"{name} cannot be negative.")
    return x


def _positive_int(value, name):
    x = int(value)
    if x <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return x


def _diameter(value):
    d = int(value)
    if d <= 0:
        raise ValueError("Rebar diameter must be positive.")
    return d


def rebar_weight(length_m, diameter_mm):
    length = _nonnegative(length_m, "Rebar length")
    d = _diameter(diameter_mm)
    return length * REBAR_WEIGHT.get(d, d * d / 162.0)


def bars_12m(length_m):
    length = _nonnegative(length_m, "Rebar length")
    return 0 if length <= 0 else math.ceil(length / STOCK_BAR_LENGTH_M)


def number_of_bars_in_direction(usable_length_m, spacing_mm):
    L = _nonnegative(usable_length_m, "Usable length")
    s = _positive(spacing_mm, "Spacing")
    if L <= 0:
        return 0
    return math.floor(L / (s / 1000.0)) + 1


def usable_length(total_length_m, cover_mm=50):
    L = _nonnegative(total_length_m, "Total length")
    c = _nonnegative(cover_mm, "Cover") / 1000.0
    return max(L - 2 * c, 0.0)


def bar_length_with_lap(length_m, lap_percent=0):
    L = _nonnegative(length_m, "Bar length")
    p = _nonnegative(lap_percent, "Lap percent")
    return L * (1.0 + p / 100.0)


def optimize_12m_bars(piece_lengths):
    clean = sorted(
        [float(x) for x in piece_lengths if x is not None and float(x) > 0],
        reverse=True,
    )
    for x in clean:
        if x > STOCK_BAR_LENGTH_M + 1e-6:
            raise ValueError(f"Bar piece length {x:.2f} m is longer than 12 m.")

    bars = []
    for piece in clean:
        placed = False
        for bar in bars:
            if bar["used_m"] + piece <= STOCK_BAR_LENGTH_M + 1e-9:
                bar["pieces"].append(piece)
                bar["used_m"] += piece
                bar["waste_m"] = max(STOCK_BAR_LENGTH_M - bar["used_m"], 0.0)
                placed = True
                break
        if not placed:
            bars.append({
                "pieces": [piece],
                "used_m": piece,
                "waste_m": STOCK_BAR_LENGTH_M - piece,
            })

    waste = sum(x["waste_m"] for x in bars)
    return {
        "stock_length_m": STOCK_BAR_LENGTH_M,
        "stock_bars": len(bars),
        "used_m": sum(clean),
        "waste_m": waste,
        "waste_percent": (waste / (len(bars) * STOCK_BAR_LENGTH_M) * 100.0) if bars else 0.0,
        "plans": bars,
    }


def make_rebar_detail(diameter_mm, piece_lengths, description="", lap_percent=0):
    d = _diameter(diameter_mm)
    pieces = [bar_length_with_lap(float(x), lap_percent) for x in piece_lengths if float(x) > 0]
    opt = optimize_12m_bars(pieces)
    total = sum(pieces)
    return {
        "diameter_mm": d,
        "length_m": total,
        "weight_kg": rebar_weight(total, d),
        "bars_12m": opt["stock_bars"],
        "piece_count": len(pieces),
        "piece_lengths_m": pieces,
        "waste_m": opt["waste_m"],
        "waste_percent": opt["waste_percent"],
        "cut_plan": opt["plans"],
        "description": description,
    }


def add_rebar_detail(details, diameter_mm, piece_lengths, description="", lap_percent=0):
    if piece_lengths:
        details.append(make_rebar_detail(diameter_mm, piece_lengths, description, lap_percent))


def finalize_rebar_details(details):
    grouped = {}
    descriptions = {}
    for d in details or []:
        dia = _diameter(d["diameter_mm"])
        grouped.setdefault(dia, []).extend(d.get("piece_lengths_m", []))
        desc = d.get("description")
        if desc and desc not in descriptions.setdefault(dia, []):
            descriptions[dia].append(desc)

    out = []
    for dia in sorted(grouped):
        pieces = grouped[dia]
        opt = optimize_12m_bars(pieces)
        total = sum(pieces)
        out.append({
            "diameter_mm": dia,
            "length_m": total,
            "weight_kg": rebar_weight(total, dia),
            "bars_12m": opt["stock_bars"],
            "piece_count": len(pieces),
            "piece_lengths_m": pieces,
            "waste_m": opt["waste_m"],
            "waste_percent": opt["waste_percent"],
            "cut_plan": opt["plans"],
            "description": " + ".join(descriptions.get(dia, [])),
        })
    return out


def _member_result(concrete, details, **extra):
    concrete = _nonnegative(concrete, "Concrete volume")
    final = finalize_rebar_details(details)
    total_length = sum(x["length_m"] for x in final)
    total_weight = sum(x["weight_kg"] for x in final)
    stock_bars = sum(x["bars_12m"] for x in final)
    waste = sum(x["waste_m"] for x in final)
    stock_length = stock_bars * STOCK_BAR_LENGTH_M
    return {
        "concrete_m3": concrete,
        "total_concrete_m3": concrete,
        "total_rebar_kg": total_weight,
        "total_rebar_length_m": total_length,
        "total_stock_bars_12m": stock_bars,
        "total_stock_length_m": stock_length,
        "total_rebar_waste_m": waste,
        "rebar_waste_percent": (waste / stock_length * 100.0) if stock_length else 0.0,
        "rebar_details": final,
        **extra,
    }


def isolated_footing(count, length_m, width_m, thickness_m,
                     lean_concrete_length_m, lean_concrete_width_m, lean_concrete_thickness_m,
                     bottom_diameter_mm, bottom_spacing_mm, top_diameter_mm=None, top_spacing_mm=None,
                     cover_mm=50, lap_percent=0, pedestal_length_m=0, pedestal_width_m=0,
                     pedestal_height_m=0):
    n = _positive_int(count, "Footing count")
    Lm = _positive(length_m, "Footing length"); Wm = _positive(width_m, "Footing width")
    Tm = _positive(thickness_m, "Footing thickness")
    lean = n * _nonnegative(lean_concrete_length_m, "Lean length") * _nonnegative(lean_concrete_width_m, "Lean width") * _nonnegative(lean_concrete_thickness_m, "Lean thickness")
    footing = n * Lm * Wm * Tm
    pedestal = n * _nonnegative(pedestal_length_m, "Pedestal length") * _nonnegative(pedestal_width_m, "Pedestal width") * _nonnegative(pedestal_height_m, "Pedestal height")
    details=[]; L=usable_length(Lm,cover_mm); W=usable_length(Wm,cover_mm)
    nx=number_of_bars_in_direction(W,bottom_spacing_mm); ny=number_of_bars_in_direction(L,bottom_spacing_mm)
    add_rebar_detail(details,bottom_diameter_mm,[L]*(nx*n),'پی منفرد - شبکه پایین X',lap_percent)
    add_rebar_detail(details,bottom_diameter_mm,[W]*(ny*n),'پی منفرد - شبکه پایین Y',lap_percent)
    if top_diameter_mm and top_spacing_mm:
        nx=number_of_bars_in_direction(W,top_spacing_mm); ny=number_of_bars_in_direction(L,top_spacing_mm)
        add_rebar_detail(details,top_diameter_mm,[L]*(nx*n),'پی منفرد - شبکه بالا X',lap_percent)
        add_rebar_detail(details,top_diameter_mm,[W]*(ny*n),'پی منفرد - شبکه بالا Y',lap_percent)
    result = _member_result(lean+footing+pedestal,details,lean_concrete_m3=lean,footing_concrete_m3=footing,pedestal_concrete_m3=pedestal,count=n)
    result['bottom_rebar_weight_kg'] = sum(x['weight_kg'] for x in result['rebar_details'] if 'پایین' in x.get('description',''))
    result['top_rebar_weight_kg'] = sum(x['weight_kg'] for x in result['rebar_details'] if 'بالا' in x.get('description',''))
    return result


def strip_footing(strip_count, strip_length_m, footing_width_m, footing_thickness_m,
                  lean_length_m, lean_width_m, lean_thickness_m, longitudinal_diameter_mm,
                  longitudinal_count, transverse_diameter_mm, transverse_spacing_mm,
                  top_longitudinal_diameter_mm=None, top_longitudinal_count=None,
                  top_transverse_diameter_mm=None, top_transverse_spacing_mm=None,
                  cover_mm=50, lap_percent=0):
    n=_positive_int(strip_count,"Strip count"); Lm=_positive(strip_length_m,"Strip length"); Wm=_positive(footing_width_m,"Footing width"); Tm=_positive(footing_thickness_m,"Footing thickness")
    lean = n * _nonnegative(lean_length_m, 'Lean length') * _nonnegative(lean_width_m, 'Lean width') * _nonnegative(lean_thickness_m, 'Lean thickness')
    concrete=n*Lm*Wm*Tm; details=[]; L=usable_length(Lm,cover_mm); W=usable_length(Wm,cover_mm)
    add_rebar_detail(details,longitudinal_diameter_mm,[L]*(_positive_int(longitudinal_count,"Longitudinal count")*n),'پی نواری - طولی پایین',lap_percent)
    nc=number_of_bars_in_direction(L,transverse_spacing_mm); add_rebar_detail(details,transverse_diameter_mm,[W]*(nc*n),'پی نواری - عرضی پایین',lap_percent)
    if top_longitudinal_diameter_mm and top_longitudinal_count: add_rebar_detail(details,top_longitudinal_diameter_mm,[L]*(int(top_longitudinal_count)*n),'پی نواری - طولی بالا',lap_percent)
    if top_transverse_diameter_mm and top_transverse_spacing_mm:
        nc=number_of_bars_in_direction(L,top_transverse_spacing_mm); add_rebar_detail(details,top_transverse_diameter_mm,[W]*(nc*n),'پی نواری - عرضی بالا',lap_percent)
    return _member_result(lean+concrete,details,lean_concrete_m3=lean,footing_concrete_m3=concrete,count=n)


def raft_foundation(length_m,width_m,thickness_m,lean_length_m,lean_width_m,lean_thickness_m,
                    bottom_x_diameter_mm,bottom_x_spacing_mm,bottom_y_diameter_mm,bottom_y_spacing_mm,
                    top_x_diameter_mm=None,top_x_spacing_mm=None,top_y_diameter_mm=None,top_y_spacing_mm=None,
                    cover_mm=50,lap_percent=0):
    Lm=_positive(length_m,"Raft length"); Wm=_positive(width_m,"Raft width"); Tm=_positive(thickness_m,"Raft thickness")
    lean = _nonnegative(lean_length_m, 'Lean length') * _nonnegative(lean_width_m, 'Lean width') * _nonnegative(lean_thickness_m, 'Lean thickness')
    concrete=Lm*Wm*Tm; details=[]; L=usable_length(Lm,cover_mm); W=usable_length(Wm,cover_mm)
    nx=number_of_bars_in_direction(W,bottom_x_spacing_mm); ny=number_of_bars_in_direction(L,bottom_y_spacing_mm)
    add_rebar_detail(details,bottom_x_diameter_mm,[L]*nx,'رادیه - شبکه پایین X',lap_percent); add_rebar_detail(details,bottom_y_diameter_mm,[W]*ny,'رادیه - شبکه پایین Y',lap_percent)
    if top_x_diameter_mm and top_x_spacing_mm:
        nx=number_of_bars_in_direction(W,top_x_spacing_mm); add_rebar_detail(details,top_x_diameter_mm,[L]*nx,'رادیه - شبکه بالا X',lap_percent)
    if top_y_diameter_mm and top_y_spacing_mm:
        ny=number_of_bars_in_direction(L,top_y_spacing_mm); add_rebar_detail(details,top_y_diameter_mm,[W]*ny,'رادیه - شبکه بالا Y',lap_percent)
    return _member_result(concrete+lean,details,lean_concrete_m3=lean,raft_concrete_m3=concrete)


def column_rectangular(count,width_m,depth_m,height_m,long_dia,long_count,stirrup_dia,stirrup_spacing,cover_mm=40):
    n=_positive_int(count,"Column count"); w=_positive(width_m,"Column width"); d=_positive(depth_m,"Column depth"); h=_positive(height_m,"Column height")
    concrete=n*w*d*h; details=[]; L=usable_length(h,cover_mm)
    add_rebar_detail(details,long_dia,[L]*(_positive_int(long_count,"Longitudinal count")*n),'ستون - میلگرد طولی')
    sc=number_of_bars_in_direction(L,stirrup_spacing); stirrup_len=2*(usable_length(w,cover_mm)+usable_length(d,cover_mm))
    add_rebar_detail(details,stirrup_dia,[stirrup_len]*(sc*n),'ستون - خاموت')
    return _member_result(concrete,details,count=n)


def column_round(count,diameter_m,height_m,long_dia,long_count,stirrup_dia,stirrup_spacing,cover_mm=40):
    n=_positive_int(count,"Column count"); dia=_positive(diameter_m,"Column diameter"); h=_positive(height_m,"Column height")
    concrete=n*math.pi*dia*dia/4*h; details=[]; L=usable_length(h,cover_mm)
    add_rebar_detail(details,long_dia,[L]*(_positive_int(long_count,"Longitudinal count")*n),'ستون گرد - میلگرد طولی')
    sc=number_of_bars_in_direction(L,stirrup_spacing); ring=math.pi*max(dia-2*cover_mm/1000,0)
    add_rebar_detail(details,stirrup_dia,[ring]*(sc*n),'ستون گرد - خاموت حلقوی')
    return _member_result(concrete,details,count=n)


def beam(count,length_m,width_m,height_m,long_dia,bottom_count,top_dia,top_count,stirrup_dia,stirrup_spacing,cover_mm=40):
    n=_positive_int(count,"Beam count"); Lm=_positive(length_m,"Beam length"); w=_positive(width_m,"Beam width"); h=_positive(height_m,"Beam height")
    concrete=n*Lm*w*h; details=[]; L=usable_length(Lm,cover_mm)
    add_rebar_detail(details,long_dia,[L]*(_positive_int(bottom_count,"Bottom count")*n),'تیر - میلگرد طولی پایین')
    add_rebar_detail(details,top_dia,[L]*(_positive_int(top_count,"Top count")*n),'تیر - میلگرد طولی بالا')
    sc=number_of_bars_in_direction(L,stirrup_spacing); stirrup_len=2*(usable_length(w,cover_mm)+usable_length(h,cover_mm))
    add_rebar_detail(details,stirrup_dia,[stirrup_len]*(sc*n),'تیر - خاموت')
    return _member_result(concrete,details,count=n)


def tie_beam(count,length_m,width_m,height_m,long_dia,long_count,stirrup_dia,stirrup_spacing,cover_mm=40):
    n=_positive_int(count,"Tie count"); Lm=_positive(length_m,"Tie length"); w=_positive(width_m,"Tie width"); h=_positive(height_m,"Tie height")
    concrete=n*Lm*w*h; details=[]; L=usable_length(Lm,cover_mm)
    add_rebar_detail(details,long_dia,[L]*(_positive_int(long_count,"Longitudinal count")*n),'شناژ/کلاف - طولی')
    sc=number_of_bars_in_direction(L,stirrup_spacing); sl=2*(usable_length(w,cover_mm)+usable_length(h,cover_mm))
    add_rebar_detail(details,stirrup_dia,[sl]*(sc*n),'شناژ/کلاف - خاموت')
    return _member_result(concrete,details,count=n)


def wall_concrete(length_m,height_m,thickness_m,vertical_dia,vertical_spacing,horizontal_dia,horizontal_spacing,cover_mm=40):
    Lm=_positive(length_m,"Wall length"); h=_positive(height_m,"Wall height"); t=_positive(thickness_m,"Wall thickness")
    concrete=Lm*h*t; details=[]; L=usable_length(h,cover_mm); W=usable_length(Lm,cover_mm)
    nv=number_of_bars_in_direction(W,vertical_spacing); nh=number_of_bars_in_direction(L,horizontal_spacing)
    add_rebar_detail(details,vertical_dia,[L]*nv,'دیوار - میلگرد قائم'); add_rebar_detail(details,horizontal_dia,[W]*nh,'دیوار - میلگرد افقی')
    return _member_result(concrete,details)


def stair_slab(length_m,width_m,thickness_m,main_dia,main_spacing,dist_dia,dist_spacing,steps=0,step_riser=0,step_tread=0):
    Lm=_positive(length_m,"Stair length"); Wm=_positive(width_m,"Stair width"); Tm=_positive(thickness_m,"Stair thickness")
    concrete=Lm*Wm*Tm; details=[]; L=usable_length(Lm,40); W=usable_length(Wm,40)
    nm=number_of_bars_in_direction(W,main_spacing); nd=number_of_bars_in_direction(L,dist_spacing)
    add_rebar_detail(details,main_dia,[L]*nm,'راه‌پله - میلگرد اصلی'); add_rebar_detail(details,dist_dia,[W]*nd,'راه‌پله - میلگرد توزیعی')
    step_concrete=0.0
    if steps and step_riser and step_tread:
        step_concrete=_positive(steps,"Steps")*_positive(step_riser,"Step riser")*_positive(step_tread,"Step tread")*Wm
        concrete+=step_concrete
    return _member_result(concrete,details,steps=steps,step_concrete_m3=step_concrete)


def roof_slab(area_m2,concrete_coeff,rebar_dia,rebar_kg_m2=0):
    area=_positive(area_m2,"Roof area"); coeff=_positive(concrete_coeff,"Concrete coefficient"); concrete=area*coeff; details=[]
    if rebar_kg_m2 and float(rebar_kg_m2)>0:
        d=_diameter(rebar_dia)
        total_length=(area*float(rebar_kg_m2))/REBAR_WEIGHT.get(d,d*d/162.0)
        # This is a quantity allowance, not one physical 300+ m bar.
        # Split it into <=12 m pieces so the cut-list engine can optimize it.
        piece_count=max(1, math.ceil(total_length/STOCK_BAR_LENGTH_M))
        pieces=[STOCK_BAR_LENGTH_M]*(piece_count-1)
        last=total_length-sum(pieces)
        if last>1e-9: pieces.append(last)
        add_rebar_detail(details,d,pieces,'سقف - میلگرد حرارتی/تخمینی')
    return _member_result(concrete,details,area_m2=area)


def roof_mesh(length_m,width_m,thickness_m,mesh_dia,mesh_spacing,cover_mm=30):
    Lm=_positive(length_m,"Roof length"); Wm=_positive(width_m,"Roof width"); Tm=_positive(thickness_m,"Roof thickness")
    concrete=Lm*Wm*Tm; details=[]; L=usable_length(Lm,cover_mm); W=usable_length(Wm,cover_mm)
    nx=number_of_bars_in_direction(W,mesh_spacing); ny=number_of_bars_in_direction(L,mesh_spacing)
    add_rebar_detail(details,mesh_dia,[L]*nx,'سقف - مش X'); add_rebar_detail(details,mesh_dia,[W]*ny,'سقف - مش Y')
    return _member_result(concrete,details)


def equivalent_rebar_count(current_count,current_dia,replacement_dia):
    n=_positive_int(current_count,"Current rebar count"); d1=_diameter(current_dia); d2=_diameter(replacement_dia)
    current_area=n*math.pi*d1*d1/4.0; replacement_area=math.pi*d2*d2/4.0
    required=math.ceil(current_area/replacement_area)
    return {
        "current_count": n, "current_dia": d1, "replacement_dia": d2,
        "current_area_mm2": current_area, "replacement_bar_area_mm2": replacement_area,
        "required_count": required,
        "area_equivalent": required*replacement_area >= current_area,
        "engineering_warning": "Area equivalency only; spacing, minimum/maximum reinforcement, development, splice, anchorage and detailing must be checked separately.",
    }


def aggregate_project_results(results):
    """Aggregate member results for Project Summary / Report / AI input."""
    results = results or []
    total_concrete = sum(float(r.get("total_concrete_m3",0) or 0) for r in results)
    total_weight = sum(float(r.get("total_rebar_kg",0) or 0) for r in results)
    total_length = sum(float(r.get("total_rebar_length_m",0) or 0) for r in results)
    total_stock = sum(int(r.get("total_stock_bars_12m",0) or 0) for r in results)
    total_waste = sum(float(r.get("total_rebar_waste_m",0) or 0) for r in results)
    details = finalize_rebar_details([d for r in results for d in r.get("rebar_details",[])])
    by_diameter = {
        str(x["diameter_mm"]): {
            "length_m": x["length_m"], "weight_kg": x["weight_kg"],
            "bars_12m": x["bars_12m"], "waste_m": x["waste_m"],
            "waste_percent": x["waste_percent"], "piece_count": x["piece_count"],
        } for x in details
    }
    return {
        "member_count": len(results),
        "total_concrete_m3": total_concrete,
        "total_rebar_kg": total_weight,
        "total_rebar_length_m": total_length,
        "total_stock_bars_12m": total_stock,
        "total_stock_length_m": total_stock * STOCK_BAR_LENGTH_M,
        "total_rebar_waste_m": total_waste,
        "rebar_waste_percent": (total_waste/(total_stock*STOCK_BAR_LENGTH_M)*100.0) if total_stock else 0.0,
        "rebar_schedule": details,
        "by_diameter": by_diameter,
        "members": results,
    }


def rebar_schedule(results):
    return aggregate_project_results(results)["rebar_schedule"]


def cut_list(results):
    return [
        {
            "diameter_mm": x["diameter_mm"],
            "stock_bars": x["bars_12m"],
            "piece_count": x["piece_count"],
            "total_length_m": x["length_m"],
            "waste_m": x["waste_m"],
            "waste_percent": x["waste_percent"],
            "plans": x["cut_plan"],
        }
        for x in aggregate_project_results(results)["rebar_schedule"]
    ]


def total_foundation_result(results):
    return aggregate_project_results(results)


__all__ = [name for name in globals() if not name.startswith("_")]


# ============================================================
# v2.4 Professional Natural Input / Multistory Planning Layer
# ============================================================
import re

PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

def normalize_digits(text):
    return str(text).translate(PERSIAN_DIGITS).replace('٫', '.').replace('٬', ',')

def _num(text):
    m = re.search(r'[-+]?\d+(?:[\.,]\d+)?', normalize_digits(text))
    return float(m.group(0).replace(',', '.')) if m else None

def _unit_to_m(value, unit):
    u=(unit or 'm').lower().replace(' ','')
    if u in ('mm','میلیمتر','میلی‌متر'): return value/1000
    if u in ('cm','سانت','سانتی','سانتیمتر','سانتی‌متر'): return value/100
    return value

def parse_natural_input(text):
    """Engineering-oriented free-form parser. Returns internal SI fields and warnings."""
    raw=normalize_digits(str(text)).strip(); t=raw.lower()
    f={}; w=[]
    # diameter
    m=re.search(r'(?:خاموت|میلگرد|میلگرد\s*طولی|قطر|dia(?:meter)?|phi|φ|Φ)\s*[:=\-]?\s*(\d+(?:[\.,]\d+)?)\s*(mm|میلیمتر|میلی‌متر)?',t,re.I)
    if m: f['diameter_mm']=float(m.group(1).replace(',','.'))
    # spacing: هر 20 / فاصله 20 / @20; default cm for construction shorthand
    m=re.search(r'(?:هر|فاصله|spacing|@)\s*[:=\-]?\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m|سانت|سانتی|متر)?',t,re.I)
    if m:
        v=float(m.group(1).replace(',','.')); u=m.group(2) or 'cm'
        f['spacing_mm']=_unit_to_m(v,u)*1000
    # length, with explicit unit; construction shorthand after طول defaults m
    m=re.search(r'(?:طول|length|L)\s*[:=\-]?\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m|متر|سانت|سانتی)?',t,re.I)
    if m:
        v=float(m.group(1).replace(',','.')); f['length_m']=_unit_to_m(v,m.group(2) or 'm')
    # "7 متری" / "7 متر" when accompanied by تیر/ستون/member
    if 'length_m' not in f:
        m=re.search(r'(?:تیر|ستون|عضو|member)\s*(?:به\s*)?(\d+(?:[\.,]\d+)?)\s*(?:متری|متر|m)\b',t,re.I)
        if m: f['length_m']=float(m.group(1).replace(',','.'))
    # Development length / lap design inputs
    m=re.search(r'(?:ld|l_d|طول\s*مهاری|مهاری)\s*[:=\-]?\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m|متر|سانت|سانتی)?',t,re.I)
    if m:
        f['ld_m']=_unit_to_m(float(m.group(1).replace(',','.')),m.group(2) or 'm')
    m=re.search(r'(?:کلاس\s*وصله|splice\s*class|class)\s*[:=\-]?\s*([ab])\b',t,re.I)
    if m: f['splice_class']=m.group(1).upper()
    if 'کوپلر' in t or 'coupler' in t: f['coupler_requested']=True
    # count: تعداد 16 / 16 میلگرد / 16 عدد
    m=re.search(r'(?:تعداد|count|number)\s*[:=\-]?\s*(\d+)',t,re.I)
    if m: f['count']=int(m.group(1))
    if 'count' not in f:
        m=re.search(r'(?<![a-zA-Z])(\d+)\s*(?:عدد|میلگرد|bars?|rebar)',t,re.I)
        if m: f['count']=int(m.group(1))
    # floors/story count: طبقات 10 / 10 طبقه
    m=re.search(r'(?:طبقات?|floors?|stories?)\s*[:=\-]?\s*(\d+)',t,re.I)
    if m: f['floors']=int(m.group(1))
    if 'floors' not in f:
        m=re.search(r'(?<![a-zA-Z])(\d+)\s*(?:طبقه|طبقات|floor|floors|story|stories)\b',t,re.I)
        if m: f['floors']=int(m.group(1))
    m=re.search(r'(?:ارتفاع\s*(?:هر\s*)?(?:طبقه)?|story\s*height)\s*[:=\-]?\s*(\d+(?:[\.,]\d+)?)\s*(m|متر|cm|سانت)?',t,re.I)
    if m: f['story_height_m']=_unit_to_m(float(m.group(1).replace(',','.')),m.group(2) or 'm')
    # dimensions such as 40x40 cm
    m=re.search(r'(\d+(?:[\.,]\d+)?)\s*[x×*]\s*(\d+(?:[\.,]\d+)?)\s*(cm|mm|سانت|میلیمتر)?',t,re.I)
    if m:
        u=m.group(3) or 'cm'; f['width_m']=_unit_to_m(float(m.group(1).replace(',','.')),u); f['depth_m']=_unit_to_m(float(m.group(2).replace(',','.')),u)
    if not f: w.append('ورودی قابل تشخیص نبود.')
    return {'fields':f,'warnings':w}

def natural_stirrup_quantity(member_length_m, spacing_mm, include_both_ends=True):
    L=float(member_length_m); s=float(spacing_mm)
    if L<=0 or s<=0: raise ValueError('طول و فاصله باید مثبت باشند.')
    return max(1, math.floor(L*1000/s)+(1 if include_both_ends else 0))

def verified_splice_length(splice_length_m, *, standard, edition, source_clause, source_note='', critical_zone_status='not_checked'):
    """Register a verified code result. No code-specific value is invented here."""
    if not splice_length_m or float(splice_length_m)<=0: raise ValueError('طول وصله معتبر نیست.')
    if not source_clause or not edition: raise ValueError('ویرایش و بند آیین‌نامه برای وصله الزامی است.')
    return {'splice_length_m':float(splice_length_m),'standard':standard,'edition':edition,'source_clause':source_clause,'source_note':source_note,'critical_zone_status':critical_zone_status,'verified':True}

def column_multistory_plan(floors, story_height_m, longitudinal_count, diameter_mm, splice=None, coupler_per_connection=False):
    n=int(floors); H=float(story_height_m); bars=int(longitudinal_count); d=int(diameter_mm)
    if n<1 or H<=0 or bars<1 or d<=0: raise ValueError('مشخصات ستون چندطبقه نامعتبر است.')
    lap=None
    if splice:
        if not splice.get('verified'): raise ValueError('وصله باید با ضابطه تأییدشده تعریف شود.')
        lap=float(splice['splice_length_m'])
    rows=[]
    for floor in range(1,n+1):
        rows.append({'floor':floor,'story_height_m':H,'bar_diameter_mm':d,'longitudinal_bars':bars,'splice_length_m':lap,'critical_zone_status':(splice or {}).get('critical_zone_status','not_checked')})
    connections=max(n-1,0)*bars
    return {'floors':n,'story_height_m':H,'diameter_mm':d,'longitudinal_bars':bars,'splice':splice,'connections':connections,'couplers':connections if coupler_per_connection else 0,'rows':rows}


# ============================================================
# Verified code-rule helpers used by the professional column layer
# ============================================================
def iran_column_lap_rule(ld_m, *, splice_class='B', special_moment_frame=False,
                         splice_bars_fraction=0.5, available_rebar_ratio=2.0,
                         min_lap_m=0.30):
    """Mabhas 9 v1399-oriented column lap rule.

    The caller supplies Ld calculated by the project design layer.
    Class B uses 1.3 Ld; Class A can use Ld only when the two stated
    reduction conditions are both satisfied. For special moment frames,
    the result is still governed by the seismic/detailing restrictions.
    """
    ld=float(ld_m)
    if ld<=0: raise ValueError('Ld must be positive.')
    cls=str(splice_class).upper()
    if cls=='A':
        if available_rebar_ratio < 2.0 or splice_bars_fraction > 0.50:
            raise ValueError('Class A lap reduction conditions are not satisfied.')
        lap=max(ld,min_lap_m)
    elif cls=='B':
        lap=max(1.30*ld,min_lap_m)
    else:
        raise ValueError('splice_class must be A or B.')
    return {
        'standard':'iran','edition':'مبحث نهم ویرایش ۱۳۹۹',
        'basis_clause':'9-21-4-2-1', 'ld_m':ld, 'splice_class':cls,
        'lap_length_m':lap, 'minimum_m':min_lap_m,
        'special_moment_frame':bool(special_moment_frame),
        'reduction_conditions_met': (available_rebar_ratio>=2.0 and splice_bars_fraction<=0.50),
        'note':'برای قاب خمشی ویژه، طول وصله میلگردهای طولی باید بر مبنای حالت کششی کنترل شود و محدودیت محل وصله فصل لرزه‌ای نیز اعمال می‌شود.'
    }

def iran_column_splice_location(story_height_m, lap_length_m, *, special_moment_frame=True):
    """Place a lap symmetrically in the middle half of a story when required.
    Returns absolute distances from story base/top and a compliance status.
    """
    H=float(story_height_m); lap=float(lap_length_m)
    if H<=0 or lap<=0: raise ValueError('Story height and lap length must be positive.')
    if lap > H/2.0:
        return {'status':'not_feasible','reason':'طول وصله از طول مجاز نیمه میانی بیشتر است.','story_height_m':H,'lap_length_m':lap}
    if special_moment_frame:
        start=H/2.0-lap/2.0; end=H/2.0+lap/2.0
        return {'status':'ok','zone':'middle_half','start_from_story_base_m':start,'end_from_story_base_m':end,
                'distance_from_base_m':start,'distance_from_top_m':H-end}
    start=max(0.0,H/2.0-lap/2.0); end=start+lap
    return {'status':'ok','zone':'middle_region','start_from_story_base_m':start,'end_from_story_base_m':end,
            'distance_from_base_m':start,'distance_from_top_m':H-end}

def multistory_column_splice_schedule(floors, story_height_m, bar_count, diameter_mm,
                                      lap_rule, *, special_moment_frame=True,
                                      coupler=False, alternate_bars=True):
    n=int(floors); H=float(story_height_m); bars=int(bar_count); d=int(diameter_mm)
    lap=float(lap_rule['lap_length_m'])
    if n<1 or H<=0 or bars<1 or d<=0: raise ValueError('Invalid column inputs.')
    loc=iran_column_splice_location(H,lap,special_moment_frame=special_moment_frame)
    if loc['status']!='ok': raise ValueError(loc['reason'])
    rows=[]
    for floor in range(1,n):
        rows.append({
            'connection_between_floors':f'{floor}-{floor+1}',
            'splice_start_from_lower_story_base_m':loc['start_from_story_base_m'],
            'splice_end_from_lower_story_base_m':loc['end_from_story_base_m'],
            'splice_length_m':lap,
            'bar_groups':'یک‌درمیان' if alternate_bars else 'همه در یک گروه',
            'location_status':'مجاز در نیمه میانی' if special_moment_frame else 'طبق ضوابط محل وصله پروژه کنترل شود'
        })
    connections=(n-1)*bars
    return {
        'standard':lap_rule['standard'],'edition':lap_rule['edition'],'basis_clause':lap_rule['basis_clause'],
        'floors':n,'story_height_m':H,'bar_count':bars,'diameter_mm':d,'lap_length_m':lap,
        'connections':connections,'couplers':connections if coupler else 0,
        'schedule':rows,'critical_zone_avoided':True,
        'execution_note':'طول برش و محل وصله برای جلوگیری از ورود وصله به ناحیه ممنوعه/بحرانی تنظیم شده است.'
    }

# ---------------------------------------------------------------------------
# v2.5 engineering detailing extensions
# ---------------------------------------------------------------------------
def _ceil_count(length_m, spacing_mm):
    L = _positive(length_m, "Length")
    s = _positive(spacing_mm, "Spacing") / 1000.0
    return max(1, math.floor(L / s) + 1)


def beam_critical_zone(beam_height_m, *, ductility="medium", critical_length_m=None):
    """Return end critical zones used for detailing/cut-planning.

    For Iran M9:1399 medium-ductility beam end critical length is commonly
    taken as 2h.  The value is exposed as an input so the engineer can replace
    it when the selected structural system/code requires another rule.
    """
    h = _positive(beam_height_m, "Beam height")
    if critical_length_m is not None:
        l0 = _positive(critical_length_m, "Critical length")
        basis = "user_defined"
    elif str(ductility).lower() in ("medium", "متوسط"):
        l0 = 2.0 * h
        basis = "M9:1399 beam end critical zone: 2h (verify system-specific detailing)"
    else:
        l0 = 2.0 * h
        basis = "engineering default 2h; verify selected code/system"
    return {"critical_length_m": l0, "left_zone": [0.0, l0], "right_zone": [0.0, l0], "basis": basis}


def _zone_aware_cut_pieces(span_m, critical_length_m, count, *, cover_m=0.04,
                           end_anchor_m=0.0, support_extra_m=0.0,
                           continuous=True):
    """Create explicit bar pieces while keeping splice/cut locations away from ends.

    This is a quantity/detailing planner, not a substitute for structural design.
    """
    L = _positive(span_m, "Beam span")
    c = max(0.0, float(cover_m))
    n = _positive_int(count, "Bar count")
    l0 = min(_positive(critical_length_m, "Critical length"), L / 2.0)
    clear = max(L - 2*c, 0.0)
    if continuous:
        return [clear] * n
    return [max(clear + end_anchor_m + support_extra_m, 0.0)] * n


def beam_reinforcement_plan(*, count=1, span_m, width_m, height_m,
                            bottom_dia_mm, bottom_count,
                            top_dia_mm, top_count,
                            stirrup_dia_mm, stirrup_spacing_mm,
                            cover_mm=40,
                            critical_length_m=None,
                            critical_stirrup_spacing_mm=None,
                            supplementary_bars=None,
                            skin_dia_mm=None, skin_count_each_side=0,
                            pin_dia_mm=None, pin_spacing_mm=None,
                            ductility="medium"):
    """Engineering quantity/detailing package for beams.

    supplementary_bars is a list of dicts, e.g.:
      {"position":"top_support", "diameter_mm":16, "count":2,
       "length_m":1.80}
    This makes strengthening bars first-class items in Rebar Schedule/Cut List.
    """
    n = _positive_int(count, "Beam count")
    L = _positive(span_m, "Beam span")
    W = _positive(width_m, "Beam width")
    H = _positive(height_m, "Beam height")
    cover = _nonnegative(cover_mm, "Cover") / 1000.0
    zone = beam_critical_zone(H, ductility=ductility, critical_length_m=critical_length_m)
    l0 = min(zone["critical_length_m"], L / 2.0)

    details = []
    add_rebar_detail(details, bottom_dia_mm, _zone_aware_cut_pieces(L, l0, int(bottom_count), cover_m=cover),
                     "تیر - میلگرد طولی پایین / continuous", 0)
    add_rebar_detail(details, top_dia_mm, _zone_aware_cut_pieces(L, l0, int(top_count), cover_m=cover),
                     "تیر - میلگرد طولی بالا / continuous", 0)

    # Dense stirrups in both critical end zones + normal spacing in the middle.
    s_crit = critical_stirrup_spacing_mm or stirrup_spacing_mm
    left_n = _ceil_count(l0, s_crit)
    right_n = _ceil_count(l0, s_crit)
    middle_len = max(L - 2*l0, 0.0)
    middle_n = _ceil_count(middle_len, stirrup_spacing_mm) if middle_len > 0 else 0
    total_stirrups = max(1, left_n + right_n + middle_n - (1 if middle_n else 0))
    stirrup_len = 2 * max(W - 2*cover, 0.0) + 2 * max(H - 2*cover, 0.0)
    add_rebar_detail(details, stirrup_dia_mm, [stirrup_len] * (total_stirrups*n),
                     "تیر - خاموت (ناحیه بحرانی / عادی)")

    # Side skin / longitudinal side bars (کمرکش).
    if skin_dia_mm and int(skin_count_each_side) > 0:
        skin_total = int(skin_count_each_side) * 2 * n
        add_rebar_detail(details, skin_dia_mm, _zone_aware_cut_pieces(L, l0, skin_total, cover_m=cover),
                         "تیر - کمرکش / Side Skin Bars")

    # Pin bars in the beam, quantity controlled by user-defined spacing.
    pin_count = 0
    if pin_dia_mm and pin_spacing_mm:
        pin_count = _ceil_count(L, pin_spacing_mm)
        pin_len = max(W - 2*cover, 0.0)
        add_rebar_detail(details, pin_dia_mm, [pin_len] * (pin_count*n),
                         "تیر - سنجاقی / Pin Bars")

    # Strengthening bars are deliberately explicit; no guessed code quantity.
    if supplementary_bars:
        for item in supplementary_bars:
            dia = int(item["diameter_mm"])
            qty = _positive_int(item["count"], "Supplementary bar count")
            length = _positive(item["length_m"], "Supplementary bar length")
            pos = item.get("position", "تقویتی")
            add_rebar_detail(details, dia, [length] * (qty*n), f"تیر - میلگرد تقویتی / {pos}")

    result = _member_result(
        n * L * W * H, details,
        count=n,
        critical_zone=zone,
        critical_stirrup_spacing_mm=s_crit,
        normal_stirrup_spacing_mm=stirrup_spacing_mm,
        critical_stirrup_count_per_beam=left_n + right_n,
        normal_stirrup_count_per_beam=middle_n,
        stirrup_count_per_beam=total_stirrups,
        pin_count_per_beam=pin_count,
        supplementary_bar_groups=len(supplementary_bars or []),
        engineering_note="Critical-zone lengths and reinforcement quantities must be verified against the selected structural system, drawings and governing code before construction."
    )
    return result


def _ceil_count_exact(length_m, spacing_mm):
    L = _positive(length_m, "Length")
    s = _positive(spacing_mm, "Spacing") / 1000.0
    return max(1, math.ceil(L / s))


def _roof_net_area(length_m, width_m, openings=None):
    area = _positive(length_m, "Roof length") * _positive(width_m, "Roof width")
    opening_area = 0.0
    for op in openings or []:
        opening_area += _positive(op["length_m"], "Opening length") * _positive(op["width_m"], "Opening width")
    if opening_area > area:
        raise ValueError("Opening area cannot exceed roof area.")
    return area - opening_area


def _block_count_by_grid(length_m, width_m, block_length_m, block_width_m, openings=None, explicit_count=None):
    """Return block count without inventing quantities.

    A rectangular grid count is valid only when the roof has no irregular
    openings/layout constraints. If openings are present, an explicit block
    count must be supplied because simple area subtraction does not determine
    the actual number of cut blocks.
    """
    L = _positive(length_m, "Roof length")
    W = _positive(width_m, "Roof width")
    bl = _positive(block_length_m, "Block length")
    bw = _positive(block_width_m, "Block width")
    if explicit_count is not None:
        return _positive_int(explicit_count, "Block count")
    if openings:
        raise ValueError("For roofs with openings, explicit EPS/clay block count is required; no estimated count is allowed.")
    return math.ceil(L / bl) * math.ceil(W / bw)


def joist_eps_roof_detail(*, span_m, width_m, joist_spacing_mm,
                           eps_length_m, eps_width_m, eps_height_m,
                           joist_length_m=None, joist_count=None,
                           thermal_dia_mm=None, thermal_spacing_mm=None,
                           transverse_dia_mm=None, transverse_count=None,
                           otka_count=None, otka_dia_mm=None, otka_length_m=None,
                           june_count=None, june_top_dia_mm=None, june_bottom_dia_mm=None,
                           june_pin_dia_mm=None, june_pin_count=None,
                           concrete_topping_thickness_m=None,
                           block_count=None, openings=None):
    """Deterministic quantity package for EPS joist-block roof.

    No empirical coefficient is inserted. Counts that depend on drawings/system
    rules must be supplied explicitly; otherwise the function raises an error.
    """
    L = _positive(span_m, "Roof span")
    W = _positive(width_m, "Roof width")
    js = _positive(joist_spacing_mm, "Joist spacing")
    eL = _positive(eps_length_m, "EPS length")
    eW = _positive(eps_width_m, "EPS width")
    eH = _positive(eps_height_m, "EPS height")
    net_area = _roof_net_area(L, W, openings)
    if joist_count is None:
        joist_count = _ceil_count_exact(W, js)
    else:
        joist_count = _positive_int(joist_count, "Joist count")
    if joist_length_m is None:
        joist_length_m = L
    joist_length_m = _positive(joist_length_m, "Joist length")

    # EPS count is geometric and does not include a hidden waste percentage.
    eps_count = _block_count_by_grid(L, W, eL, eW, openings, explicit_count=block_count)
    details = []
    if thermal_dia_mm and thermal_spacing_mm:
        n = _ceil_count_exact(L, thermal_spacing_mm)
        add_rebar_detail(details, thermal_dia_mm, [W] * n, "تیرچه یونولیت - میلگرد حرارتی")
    if transverse_dia_mm and transverse_count:
        add_rebar_detail(details, transverse_dia_mm, [W] * int(transverse_count), "تیرچه یونولیت - میلگرد عرضی")
    if otka_count is not None:
        oc = _positive_int(otka_count, "Otka count")
        if not (otka_dia_mm and otka_length_m):
            raise ValueError("Otka diameter and length are required when Otka count is supplied.")
        add_rebar_detail(details, otka_dia_mm, [otka_length_m] * oc, "تیرچه یونولیت - اُتکا / ادکا")
    if june_count is not None:
        jc = _positive_int(june_count, "June count")
        if not (june_top_dia_mm and june_bottom_dia_mm):
            raise ValueError("June top and bottom diameters are required when June count is supplied.")
        add_rebar_detail(details, june_top_dia_mm, [W] * jc, "تیرچه یونولیت - ژوئن / کلاف عرضی - بالا")
        add_rebar_detail(details, june_bottom_dia_mm, [W] * jc, "تیرچه یونولیت - ژوئن / کلاف عرضی - پایین")
        if june_pin_dia_mm and june_pin_count is not None:
            add_rebar_detail(details, june_pin_dia_mm, [max(js / 1000.0, 0.0)] * int(june_pin_count), "تیرچه یونولیت - سنجاقی ژوئن")
    concrete = 0.0
    if concrete_topping_thickness_m is not None:
        t = _positive(concrete_topping_thickness_m, "Concrete topping thickness")
        concrete = net_area * t
    return _member_result(
        concrete, details,
        roof_system="joist_eps",
        span_m=L, width_m=W, net_area_m2=net_area,
        joist_spacing_mm=js, joist_count=joist_count, joist_length_m=joist_length_m,
        eps_dimensions_m=(eL, eW, eH), eps_count=eps_count,
        otka_count=otka_count, june_count=june_count, june_pin_count=june_pin_count,
        no_hidden_waste_factor=True,
        note="تعداد ژوئن، اُتکا و سنجاقی فقط در صورت ارائه مقدار/ضابطه معتبر محاسبه می‌شود؛ ضریب تجربی پنهان وجود ندارد."
    )


def joist_clay_roof_detail(*, span_m, width_m, joist_spacing_mm,
                            clay_length_m, clay_width_m, clay_height_m,
                            joist_length_m=None, joist_count=None,
                            thermal_dia_mm=None, thermal_spacing_mm=None,
                            transverse_dia_mm=None, transverse_count=None,
                            otka_count=None, otka_dia_mm=None, otka_length_m=None,
                            june_count=None, june_top_dia_mm=None, june_bottom_dia_mm=None,
                            june_pin_dia_mm=None, june_pin_count=None,
                            concrete_topping_thickness_m=None, block_count=None, openings=None):
    """Deterministic quantity package for clay joist-block roof."""
    L = _positive(span_m, "Roof span")
    W = _positive(width_m, "Roof width")
    js = _positive(joist_spacing_mm, "Joist spacing")
    cL = _positive(clay_length_m, "Clay block length")
    cW = _positive(clay_width_m, "Clay block width")
    cH = _positive(clay_height_m, "Clay block height")
    net_area = _roof_net_area(L, W, openings)
    if joist_count is None:
        joist_count = _ceil_count_exact(W, js)
    else:
        joist_count = _positive_int(joist_count, "Joist count")
    if joist_length_m is None:
        joist_length_m = L
    details = []
    clay_count = _block_count_by_grid(L, W, cL, cW, openings, explicit_count=block_count)
    if thermal_dia_mm and thermal_spacing_mm:
        n = _ceil_count_exact(L, thermal_spacing_mm)
        add_rebar_detail(details, thermal_dia_mm, [W] * n, "تیرچه سفالی - میلگرد حرارتی")
    if transverse_dia_mm and transverse_count:
        add_rebar_detail(details, transverse_dia_mm, [W] * int(transverse_count), "تیرچه سفالی - میلگرد عرضی")
    if otka_count is not None:
        oc = _positive_int(otka_count, "Otka count")
        if not (otka_dia_mm and otka_length_m):
            raise ValueError("Otka diameter and length are required when Otka count is supplied.")
        add_rebar_detail(details, otka_dia_mm, [otka_length_m] * oc, "تیرچه سفالی - اُتکا / ادکا")
    if june_count is not None:
        jc = _positive_int(june_count, "June count")
        if not (june_top_dia_mm and june_bottom_dia_mm):
            raise ValueError("June top and bottom diameters are required when June count is supplied.")
        add_rebar_detail(details, june_top_dia_mm, [W] * jc, "تیرچه سفالی - ژوئن / کلاف عرضی - بالا")
        add_rebar_detail(details, june_bottom_dia_mm, [W] * jc, "تیرچه سفالی - ژوئن / کلاف عرضی - پایین")
        if june_pin_dia_mm and june_pin_count is not None:
            add_rebar_detail(details, june_pin_dia_mm, [max(js / 1000.0, 0.0)] * int(june_pin_count), "تیرچه سفالی - سنجاقی ژوئن")
    concrete = 0.0
    if concrete_topping_thickness_m is not None:
        concrete = net_area * _positive(concrete_topping_thickness_m, "Concrete topping thickness")
    return _member_result(
        concrete, details,
        roof_system="joist_clay",
        span_m=L, width_m=W, net_area_m2=net_area,
        joist_spacing_mm=js, joist_count=joist_count, joist_length_m=_positive(joist_length_m, "Joist length"),
        clay_dimensions_m=(cL, cW, cH), clay_count=clay_count,
        otka_count=otka_count, june_count=june_count, june_pin_count=june_pin_count,
        no_hidden_waste_factor=True,
        note="تعداد ژوئن، اُتکا و سنجاقی فقط در صورت ارائه مقدار/ضابطه معتبر محاسبه می‌شود؛ ضریب تجربی پنهان وجود ندارد."
    )


def waffle_roof_detail(*, length_m, width_m, module_length_m, module_width_m,
                       module_count=None, concrete_thickness_m=None,
                       rebar_dia_mm=None, rebar_spacing_mm=None,
                       supplementary_bars=None, openings=None):
    """Deterministic waffle quantity package. Module count is geometric or explicit."""
    L = _positive(length_m, "Waffle length")
    W = _positive(width_m, "Waffle width")
    ml = _positive(module_length_m, "Waffle module length")
    mw = _positive(module_width_m, "Waffle module width")
    net_area = _roof_net_area(L, W, openings)
    if module_count is None:
        module_count = math.ceil(L / ml) * math.ceil(W / mw)
    else:
        module_count = _positive_int(module_count, "Waffle module count")
    concrete = 0.0
    if concrete_thickness_m is not None:
        concrete = net_area * _positive(concrete_thickness_m, "Waffle concrete thickness")
    details = []
    if rebar_dia_mm and rebar_spacing_mm:
        nx = _ceil_count_exact(W, rebar_spacing_mm)
        ny = _ceil_count_exact(L, rebar_spacing_mm)
        add_rebar_detail(details, rebar_dia_mm, [L] * nx, "وافل - میلگرد در جهت X")
        add_rebar_detail(details, rebar_dia_mm, [W] * ny, "وافل - میلگرد در جهت Y")
    for item in supplementary_bars or []:
        add_rebar_detail(details, int(item["diameter_mm"]),
                         [_positive(item["length_m"], "Supplementary bar length")] * _positive_int(item["count"], "Supplementary bar count"),
                         f"وافل - میلگرد تقویتی / {item.get('position','تقویتی')}")
    return _member_result(concrete, details, roof_system="waffle", net_area_m2=net_area,
                          module_dimensions_m=(ml, mw), waffle_module_count=module_count,
                          no_hidden_waste_factor=True)



def solid_slab_roof_detail(*, length_m, width_m, thickness_m, main_dia_mm, main_spacing_mm, dist_dia_mm, dist_spacing_mm, openings=None):
    L=_positive(length_m,"Slab length"); W=_positive(width_m,"Slab width"); T=_positive(thickness_m,"Slab thickness")
    area=_roof_net_area(L,W,openings); details=[]
    nx=_ceil_count_exact(W,main_spacing_mm); ny=_ceil_count_exact(L,dist_spacing_mm)
    add_rebar_detail(details,main_dia_mm,[L]*nx,"دال بتنی - میلگرد اصلی")
    add_rebar_detail(details,dist_dia_mm,[W]*ny,"دال بتنی - میلگرد توزیعی")
    return _member_result(area*T,details,roof_system="solid_slab",net_area_m2=area,no_hidden_waste_factor=True)

def material_waste(base_quantity, waste_percent=0.0):
    """Explicit user/project waste only. No internal default coefficient."""
    q = _nonnegative(base_quantity, "Base quantity")
    p = _nonnegative(waste_percent, "Waste percent")
    return {"base_quantity": q, "waste_percent": p,
            "waste_quantity": q * p / 100.0,
            "order_quantity": q * (1.0 + p / 100.0),
            "source": "user_or_project_explicit"}

# Natural engineering parsers for beam/joist detailing

def _pair(text, pattern):
    m = re.search(pattern, text, re.I)
    return float(m.group(1).replace(',', '.')) if m else None


def parse_beam_detail_input(text):
    t = normalize_digits(text).replace('٫', '.').replace(',', '.')
    out = {}
    out['span_m'] = _pair(t, r'(?:تیر|beam)?\s*(?:طول|دهانه|span|length)\s*(\d+(?:\.\d+)?)')
    out['width_m'] = _pair(t, r'(?:عرض|width|b)\s*(\d+(?:\.\d+)?)')
    out['height_m'] = _pair(t, r'(?:ارتفاع|عمق|height|depth|h)\s*(\d+(?:\.\d+)?)')
    # fallback: "تیر 7×0.30×0.50"
    if None in (out['span_m'], out['width_m'], out['height_m']):
        m = re.search(r'(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)', t, re.I)
        if m:
            out['span_m'], out['width_m'], out['height_m'] = map(float, m.groups())
    def dia_count(kind):
        m = re.search(rf'(?:{kind}|{kind.replace("بالا","top").replace("پایین","bottom")})\s*(\d+)\s*[Φφ]?\s*[x×*]?\s*(\d+)', t, re.I)
        return (int(m.group(2)), int(m.group(1))) if m else None
    b = dia_count('پایین|bottom')
    if b: out['bottom_dia_mm'], out['bottom_count'] = b
    a = dia_count('بالا|top')
    if a: out['top_dia_mm'], out['top_count'] = a
    m = re.search(r'(?:خاموت|stirrup|ties?)\s*(\d+)\s*@\s*(\d+)', t, re.I)
    if m:
        spacing = int(m.group(2)); spacing = spacing * 10 if spacing <= 50 else spacing
        out['stirrup_dia_mm'], out['stirrup_spacing_mm'] = int(m.group(1)), spacing
    m = re.search(r'(?:بحرانی|critical)\s*(?:خاموت|stirrup)?\s*(\d+)\s*@\s*(\d+)', t, re.I)
    if m:
        spacing = int(m.group(2)); spacing = spacing * 10 if spacing <= 50 else spacing
        out['critical_stirrup_dia_mm'], out['critical_stirrup_spacing_mm'] = int(m.group(1)), spacing
    m = re.search(r'(?:کمرکش|skin|side)\s*(\d+)\s*[Φφ]\s*(\d+)', t, re.I)
    if m: out['skin_count_each_side'], out['skin_dia_mm'] = int(m.group(1)), int(m.group(2))
    m = re.search(r'(?:سنجاقی|pin)\s*(\d+)\s*[Φφ]\s*(?:@\s*)?(\d+)', t, re.I)
    if m:
        spacing = int(m.group(2)); spacing = spacing * 10 if spacing <= 50 else spacing
        out['pin_dia_mm'], out['pin_spacing_mm'] = int(m.group(1)), spacing
    # "تقویتی بالا 2Φ16 طول 1.8" / "تقویتی پایین 2Φ16 طول 2"
    supp=[]
    for m in re.finditer(r'(?:تقویتی|extra|supplementary)\s*(بالا|پایین|support|midspan)?\s*(\d+)\s*[Φφ]\s*(\d+)\s*(?:طول|length)\s*(\d+(?:\.\d+)?)', t, re.I):
        supp.append({'position':m.group(1) or 'supplementary','count':int(m.group(2)),'diameter_mm':int(m.group(3)),'length_m':float(m.group(4))})
    if supp: out['supplementary_bars'] = supp
    out['critical_length_m'] = _pair(t, r'(?:ناحیه بحرانی|critical zone|l0)\s*(?:=|:)\s*(\d+(?:\.\d+)?)')
    return {k:v for k,v in out.items() if v is not None}


def parse_joist_roof_input(text):
    t = normalize_digits(text).replace('٫', '.').replace(',', '.')
    out={}
    for key, pats in {
        'span_m':[r'(?:دهانه|span|طول)\s*(\d+(?:\.\d+)?)'],
        'width_m':[r'(?:عرض|width)\s*(\d+(?:\.\d+)?)'],
        'joist_spacing_mm':[r'(?:فاصله تیرچه|joist spacing)\s*(\d+(?:\.\d+)?)'],
    }.items():
        for p in pats:
            v=_pair(t,p)
            if v is not None: out[key]=v; break
    m=re.search(r'(?:بار زنده|live load)\s*(\d+(?:\.\d+)?)',t,re.I)
    if m: out['live_load_kg_m2']=float(m.group(1))
    return out
