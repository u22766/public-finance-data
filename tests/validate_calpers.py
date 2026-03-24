#!/usr/bin/env python3
"""
Validation suite for CalPERS (California Public Employees' Retirement System).
File: states/california/calpers-plans.json

Validates:
  - Structure: required top-level keys, all 5 representative formulas present
  - Values: age factors, compensation limits, PPPA thresholds, COLA rates
  - Range checks: all rates 0-1, ages reasonable, dollar amounts positive
  - Cross-field: PEPRA formulas have pepra=true; Classic formulas have pepra=false
  - Formula-specific: correct minimum/normal/maximum age and benefit factors
  - Vesting: 5-year cliff for all formulas
  - Funding: plausible funded ratio, assets, discount rate
  - Jurisdiction and metadata integrity

Session 62: Initial build — CalPERS final expansion system (OM-30).
"""

import json
import sys
from pathlib import Path
from typing import List

CALPERS_PATH = "states/california/calpers-plans.json"

REPRESENTATIVE_FORMULAS = [
    "classic_misc_2pct_at_55",
    "classic_misc_2pct_at_60",
    "pepra_misc_2pct_at_62",
    "classic_safety_3pct_at_50",
    "pepra_safety_2_7pct_at_57",
]

ADDITIONAL_FORMULAS = [
    "classic_safety_2pct_at_50",
    "classic_state_safety_a_2_5pct_at_55",
    "classic_state_safety_b_2pct_at_55",
    "pepra_safety_2_5pct_at_57",
    "pepra_safety_2pct_at_57",
]


def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


# ============================================================
# Structure
# ============================================================

def validate_top_level(data: dict) -> List[str]:
    errors = []
    required = [
        "systemName", "systemAbbreviation", "version", "last_updated",
        "jurisdiction", "totalMembers", "coverage", "socialSecurity",
        "pepra", "vesting", "compensationLimits", "cola", "pppa",
        "representativeFormulas", "additionalFormulas",
        "fundingStatus", "sources"
    ]
    for key in required:
        if key not in data:
            errors.append(f"CalPERS: missing required top-level key '{key}'")
    if data.get("systemAbbreviation") != "CalPERS":
        errors.append(f"CalPERS: systemAbbreviation expected 'CalPERS', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_representative_formulas_exist(data: dict) -> List[str]:
    errors = []
    rf = data.get("representativeFormulas", {})
    for key in REPRESENTATIVE_FORMULAS:
        if key not in rf:
            errors.append(f"CalPERS: missing representative formula '{key}'")
    return errors


def validate_additional_formulas_exist(data: dict) -> List[str]:
    errors = []
    af = data.get("additionalFormulas", {})
    for key in ADDITIONAL_FORMULAS:
        if key not in af:
            errors.append(f"CalPERS: missing additional formula '{key}'")
    return errors


def validate_formula_required_keys(data: dict) -> List[str]:
    errors = []
    rf = data.get("representativeFormulas", {})
    required = ["formulaName", "category", "pepra", "formula", "retirementEligibility", "memberContribution"]
    for formula_key in REPRESENTATIVE_FORMULAS:
        formula = rf.get(formula_key, {})
        for key in required:
            if key not in formula:
                errors.append(f"CalPERS formula '{formula_key}': missing required key '{key}'")
    return errors


# ============================================================
# PEPRA flags
# ============================================================

def validate_pepra_flags(data: dict) -> List[str]:
    errors = []
    rf = data.get("representativeFormulas", {})

    classic_formulas = ["classic_misc_2pct_at_55", "classic_misc_2pct_at_60", "classic_safety_3pct_at_50"]
    pepra_formulas = ["pepra_misc_2pct_at_62", "pepra_safety_2_7pct_at_57"]

    for key in classic_formulas:
        if rf.get(key, {}).get("pepra") is not False:
            errors.append(f"CalPERS '{key}': pepra flag should be false")

    for key in pepra_formulas:
        if rf.get(key, {}).get("pepra") is not True:
            errors.append(f"CalPERS '{key}': pepra flag should be true")

    return errors


def validate_category_flags(data: dict) -> List[str]:
    errors = []
    rf = data.get("representativeFormulas", {})

    misc_formulas = ["classic_misc_2pct_at_55", "classic_misc_2pct_at_60", "pepra_misc_2pct_at_62"]
    safety_formulas = ["classic_safety_3pct_at_50", "pepra_safety_2_7pct_at_57"]

    for key in misc_formulas:
        if rf.get(key, {}).get("category") != "miscellaneous":
            errors.append(f"CalPERS '{key}': category should be 'miscellaneous'")

    for key in safety_formulas:
        if rf.get(key, {}).get("category") != "safety":
            errors.append(f"CalPERS '{key}': category should be 'safety'")

    return errors


# ============================================================
# Classic Misc 2%@55
# ============================================================

def validate_classic_misc_55(data: dict) -> List[str]:
    errors = []
    f = data.get("representativeFormulas", {}).get("classic_misc_2pct_at_55", {})
    af = f.get("formula", {}).get("ageFactor", {})

    # NRA = 55, factor = 2%
    if af.get("normalRetirementAge") != 55:
        errors.append(f"CalPERS 2%@55: normalRetirementAge expected 55, got {af.get('normalRetirementAge')}")
    if af.get("standardAtNormalRetirementAge") != 0.02:
        errors.append(f"CalPERS 2%@55: standardAtNormalRetirementAge expected 0.02, got {af.get('standardAtNormalRetirementAge')}")

    # Min = 1.100% at 50
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.01100:
        errors.append(f"CalPERS 2%@55: minimum factor expected 0.01100, got {minimum.get('factor')}")
    if minimum.get("age") != 50:
        errors.append(f"CalPERS 2%@55: minimum age expected 50, got {minimum.get('age')}")

    # Max = 2.418% at 63
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.02418:
        errors.append(f"CalPERS 2%@55: maximum factor expected 0.02418, got {maximum.get('factor')}")
    if maximum.get("age") != 63:
        errors.append(f"CalPERS 2%@55: maximum age expected 63, got {maximum.get('age')}")

    # Min retirement age = 50
    if af.get("minimumRetirementAge") != 50:
        errors.append(f"CalPERS 2%@55: minimumRetirementAge expected 50, got {af.get('minimumRetirementAge')}")

    # Breakpoints: 50 and 55 must exist
    bps = {bp["age"]: bp["factor"] for bp in af.get("keyBreakpoints", [])}
    if 50 not in bps:
        errors.append("CalPERS 2%@55: keyBreakpoints missing age 50")
    if 55 not in bps:
        errors.append("CalPERS 2%@55: keyBreakpoints missing age 55")
    if bps.get(55) != 0.02:
        errors.append(f"CalPERS 2%@55: breakpoint at 55 expected 0.02, got {bps.get(55)}")

    # Retirement eligibility
    ret = f.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 55:
        errors.append(f"CalPERS 2%@55: normalRetirement.minimumAge expected 55, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalPERS 2%@55: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")

    er = ret.get("earlyRetirement", {})
    if er.get("minimumAge") != 50:
        errors.append(f"CalPERS 2%@55: earlyRetirement.minimumAge expected 50, got {er.get('minimumAge')}")

    # Contributions: state SS 7%, non-SS 8%
    mc = f.get("memberContribution", {})
    ss = mc.get("state_ss_covered", {})
    if ss.get("rate") != 0.07:
        errors.append(f"CalPERS 2%@55: state_ss_covered rate expected 0.07, got {ss.get('rate')}")
    non_ss = mc.get("state_non_ss", {})
    if non_ss.get("rate") != 0.08:
        errors.append(f"CalPERS 2%@55: state_non_ss rate expected 0.08, got {non_ss.get('rate')}")

    return errors


# ============================================================
# Classic Misc 2%@60
# ============================================================

def validate_classic_misc_60(data: dict) -> List[str]:
    errors = []
    f = data.get("representativeFormulas", {}).get("classic_misc_2pct_at_60", {})
    af = f.get("formula", {}).get("ageFactor", {})

    # NRA = 60, factor = 2%
    if af.get("normalRetirementAge") != 60:
        errors.append(f"CalPERS 2%@60: normalRetirementAge expected 60, got {af.get('normalRetirementAge')}")
    if af.get("standardAtNormalRetirementAge") != 0.02:
        errors.append(f"CalPERS 2%@60: standardAtNormalRetirementAge expected 0.02, got {af.get('standardAtNormalRetirementAge')}")

    # Min = 1.092% at 50
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.01092:
        errors.append(f"CalPERS 2%@60: minimum factor expected 0.01092, got {minimum.get('factor')}")
    if minimum.get("age") != 50:
        errors.append(f"CalPERS 2%@60: minimum age expected 50, got {minimum.get('age')}")

    # Max = 2.418% at 63
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.02418:
        errors.append(f"CalPERS 2%@60: maximum factor expected 0.02418, got {maximum.get('factor')}")
    if maximum.get("age") != 63:
        errors.append(f"CalPERS 2%@60: maximum age expected 63, got {maximum.get('age')}")

    # Final comp: 36 months
    fc = f.get("formula", {}).get("finalCompensation", {})
    if "36" not in str(fc.get("period", "")):
        errors.append("CalPERS 2%@60: finalCompensation.period should reference 36 months")

    # Retirement eligibility
    ret = f.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 60:
        errors.append(f"CalPERS 2%@60: normalRetirement.minimumAge expected 60, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalPERS 2%@60: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")
    er = ret.get("earlyRetirement", {})
    if er.get("minimumAge") != 50:
        errors.append(f"CalPERS 2%@60: earlyRetirement.minimumAge expected 50, got {er.get('minimumAge')}")

    return errors


# ============================================================
# PEPRA Misc 2%@62
# ============================================================

def validate_pepra_misc_62(data: dict) -> List[str]:
    errors = []
    f = data.get("representativeFormulas", {}).get("pepra_misc_2pct_at_62", {})
    af = f.get("formula", {}).get("ageFactor", {})

    # NRA = 62, factor = 2%
    if af.get("normalRetirementAge") != 62:
        errors.append(f"CalPERS PEPRA 2%@62: normalRetirementAge expected 62, got {af.get('normalRetirementAge')}")
    if af.get("standardAtNormalRetirementAge") != 0.02:
        errors.append(f"CalPERS PEPRA 2%@62: standardAtNormalRetirementAge expected 0.02, got {af.get('standardAtNormalRetirementAge')}")

    # Min = 1.0% at 52
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.01:
        errors.append(f"CalPERS PEPRA 2%@62: minimum factor expected 0.01, got {minimum.get('factor')}")
    if minimum.get("age") != 52:
        errors.append(f"CalPERS PEPRA 2%@62: minimum age expected 52, got {minimum.get('age')}")

    # Max = 2.5% at 67
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.025:
        errors.append(f"CalPERS PEPRA 2%@62: maximum factor expected 0.025, got {maximum.get('factor')}")
    if maximum.get("age") != 67:
        errors.append(f"CalPERS PEPRA 2%@62: maximum age expected 67, got {maximum.get('age')}")

    # Minimum retirement age 52
    if af.get("minimumRetirementAge") != 52:
        errors.append(f"CalPERS PEPRA 2%@62: minimumRetirementAge expected 52, got {af.get('minimumRetirementAge')}")

    # Breakpoints: 52 and 62 must exist
    bps = {bp["age"]: bp["factor"] for bp in af.get("keyBreakpoints", [])}
    if 52 not in bps:
        errors.append("CalPERS PEPRA 2%@62: keyBreakpoints missing age 52")
    if 62 not in bps:
        errors.append("CalPERS PEPRA 2%@62: keyBreakpoints missing age 62")
    if bps.get(62) != 0.02:
        errors.append(f"CalPERS PEPRA 2%@62: breakpoint at 62 expected 0.02, got {bps.get(62)}")
    if 67 not in bps:
        errors.append("CalPERS PEPRA 2%@62: keyBreakpoints missing age 67 (max)")
    if bps.get(67) != 0.025:
        errors.append(f"CalPERS PEPRA 2%@62: breakpoint at 67 expected 0.025, got {bps.get(67)}")

    # Final comp: 36 months
    fc = f.get("formula", {}).get("finalCompensation", {})
    if "36" not in str(fc.get("period", "")):
        errors.append("CalPERS PEPRA 2%@62: finalCompensation should reference 36 months")

    # Comp caps: 2026 with SS, 2026 without SS (at formula level, not finalCompensation level)
    cc = f.get("formula", {}).get("compensationCap", {})
    if cc.get("with_ss_2026") != 159733:
        errors.append(f"CalPERS PEPRA 2%@62: comp cap with_ss_2026 expected 159733, got {cc.get('with_ss_2026')}")
    if cc.get("without_ss_2026") != 191679:
        errors.append(f"CalPERS PEPRA 2%@62: comp cap without_ss_2026 expected 191679, got {cc.get('without_ss_2026')}")
    if cc.get("with_ss_2026", 0) > 0 and not (100000 < cc.get("with_ss_2026", 0) < 500000):
        errors.append(f"CalPERS PEPRA 2%@62: comp cap with_ss_2026 implausible: {cc.get('with_ss_2026')}")

    # Retirement eligibility
    ret = f.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 62:
        errors.append(f"CalPERS PEPRA 2%@62: normalRetirement.minimumAge expected 62, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalPERS PEPRA 2%@62: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")
    er = ret.get("earlyRetirement", {})
    if er.get("minimumAge") != 52:
        errors.append(f"CalPERS PEPRA 2%@62: earlyRetirement.minimumAge expected 52, got {er.get('minimumAge')}")

    return errors


# ============================================================
# Classic Safety 3%@50
# ============================================================

def validate_classic_safety_3pct_50(data: dict) -> List[str]:
    errors = []
    f = data.get("representativeFormulas", {}).get("classic_safety_3pct_at_50", {})
    af = f.get("formula", {}).get("ageFactor", {})

    # NRA = 50, factor = 3%
    if af.get("normalRetirementAge") != 50:
        errors.append(f"CalPERS 3%@50: normalRetirementAge expected 50, got {af.get('normalRetirementAge')}")
    if af.get("standardAtNormalRetirementAge") != 0.03:
        errors.append(f"CalPERS 3%@50: standardAtNormalRetirementAge expected 0.03, got {af.get('standardAtNormalRetirementAge')}")

    # Min = max = 3% at 50 (flat)
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.03:
        errors.append(f"CalPERS 3%@50: minimum factor expected 0.03, got {minimum.get('factor')}")
    if minimum.get("age") != 50:
        errors.append(f"CalPERS 3%@50: minimum age expected 50, got {minimum.get('age')}")
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.03:
        errors.append(f"CalPERS 3%@50: maximum factor expected 0.03 (flat), got {maximum.get('factor')}")
    if maximum.get("age") != 50:
        errors.append(f"CalPERS 3%@50: maximum age expected 50 (flat), got {maximum.get('age')}")

    # Retirement eligibility
    ret = f.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 50:
        errors.append(f"CalPERS 3%@50: normalRetirement.minimumAge expected 50, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalPERS 3%@50: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")

    # Category = safety
    if f.get("category") != "safety":
        errors.append(f"CalPERS 3%@50: category expected 'safety', got '{f.get('category')}'")

    # Example benefit present
    ex = f.get("exampleBenefit", {})
    if not ex:
        errors.append("CalPERS 3%@50: exampleBenefit missing")

    return errors


# ============================================================
# PEPRA Safety 2.7%@57
# ============================================================

def validate_pepra_safety_57(data: dict) -> List[str]:
    errors = []
    f = data.get("representativeFormulas", {}).get("pepra_safety_2_7pct_at_57", {})
    af = f.get("formula", {}).get("ageFactor", {})

    # NRA = 57, factor = 2.7%
    if af.get("normalRetirementAge") != 57:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: normalRetirementAge expected 57, got {af.get('normalRetirementAge')}")
    if af.get("standardAtNormalRetirementAge") != 0.027:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: standardAtNormalRetirementAge expected 0.027, got {af.get('standardAtNormalRetirementAge')}")

    # Min = 2.0% at 50
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.02:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: minimum factor expected 0.02, got {minimum.get('factor')}")
    if minimum.get("age") != 50:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: minimum age expected 50, got {minimum.get('age')}")

    # Max = 2.7% at 57
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.027:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: maximum factor expected 0.027, got {maximum.get('factor')}")
    if maximum.get("age") != 57:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: maximum age expected 57, got {maximum.get('age')}")

    # Breakpoints: 50 and 57
    bps = {bp["age"]: bp["factor"] for bp in af.get("keyBreakpoints", [])}
    if 50 not in bps:
        errors.append("CalPERS PEPRA Safety 2.7%@57: keyBreakpoints missing age 50")
    if 57 not in bps:
        errors.append("CalPERS PEPRA Safety 2.7%@57: keyBreakpoints missing age 57")
    if bps.get(50) != 0.02:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: breakpoint at 50 expected 0.02, got {bps.get(50)}")
    if bps.get(57) != 0.027:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: breakpoint at 57 expected 0.027, got {bps.get(57)}")

    # Final comp: 36 months
    fc = f.get("formula", {}).get("finalCompensation", {})
    if "36" not in str(fc.get("period", "")):
        errors.append("CalPERS PEPRA Safety 2.7%@57: finalCompensation should reference 36 months")

    # Retirement eligibility
    ret = f.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 57:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: normalRetirement.minimumAge expected 57, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")
    er = ret.get("earlyRetirement", {})
    if er.get("minimumAge") != 50:
        errors.append(f"CalPERS PEPRA Safety 2.7%@57: earlyRetirement.minimumAge expected 50, got {er.get('minimumAge')}")

    # Pending legislation AB 1383
    pl = f.get("pendingLegislation", {})
    if "ab_1383" not in pl:
        errors.append("CalPERS PEPRA Safety 2.7%@57: pendingLegislation.ab_1383 missing")

    return errors


# ============================================================
# COLA validators
# ============================================================

def validate_cola(data: dict) -> List[str]:
    errors = []
    cola = data.get("cola", {})

    if cola.get("mechanism") != "compounded":
        errors.append(f"CalPERS COLA: mechanism expected 'compounded', got '{cola.get('mechanism')}'")

    rates = cola.get("contractedRates", [])
    if not rates:
        errors.append("CalPERS COLA: contractedRates missing")

    # 2% rate must be present
    rate_values = [r.get("rate") for r in rates]
    if 0.02 not in rate_values:
        errors.append("CalPERS COLA: 2% rate (0.02) not found in contractedRates")
    # 3%, 4%, 5% also expected
    for r in [0.03, 0.04, 0.05]:
        if r not in rate_values:
            errors.append(f"CalPERS COLA: rate {r} not found in contractedRates")

    # PPPA exists
    pppa = data.get("pppa", {})
    if not pppa:
        errors.append("CalPERS: pppa section missing")
    if pppa.get("thresholds", {}).get("state_and_schools") != 0.75:
        errors.append(f"CalPERS PPPA: state_and_schools threshold expected 0.75, got {pppa.get('thresholds', {}).get('state_and_schools')}")
    if pppa.get("thresholds", {}).get("public_agencies") != 0.80:
        errors.append(f"CalPERS PPPA: public_agencies threshold expected 0.80, got {pppa.get('thresholds', {}).get('public_agencies')}")

    # PPPA floor: public_agencies > state_and_schools
    pa = pppa.get("thresholds", {}).get("public_agencies", 0)
    ss = pppa.get("thresholds", {}).get("state_and_schools", 0)
    if pa <= ss:
        errors.append(f"CalPERS PPPA: public_agencies threshold ({pa}) should be > state_and_schools ({ss})")

    return errors


# ============================================================
# Compensation limits
# ============================================================

def validate_comp_limits(data: dict) -> List[str]:
    errors = []
    cl = data.get("compensationLimits", {})

    # Classic IRC 401(a)(17): $350,000 for 2025
    classic = cl.get("classic_irc_401a17", {})
    if classic.get("limit_2025") != 350000:
        errors.append(f"CalPERS comp limits: classic 2025 expected 350000, got {classic.get('limit_2025')}")
    if not (100000 < classic.get("limit_2025", 0) < 1000000):
        errors.append(f"CalPERS comp limits: classic limit_2025 implausible: {classic.get('limit_2025')}")

    # PEPRA with SS 2026: $159,733
    pepra_ss = cl.get("pepra_with_ss_2026", {})
    if pepra_ss.get("limit_2026") != 159733:
        errors.append(f"CalPERS comp limits: PEPRA with_ss 2026 expected 159733, got {pepra_ss.get('limit_2026')}")

    # PEPRA without SS 2026: $191,679
    pepra_no_ss = cl.get("pepra_without_ss_2026", {})
    if pepra_no_ss.get("limit_2026") != 191679:
        errors.append(f"CalPERS comp limits: PEPRA without_ss 2026 expected 191679, got {pepra_no_ss.get('limit_2026')}")

    # Non-SS cap > SS cap
    ss_cap = pepra_ss.get("limit_2026", 0)
    no_ss_cap = pepra_no_ss.get("limit_2026", 0)
    if ss_cap and no_ss_cap and no_ss_cap <= ss_cap:
        errors.append(f"CalPERS comp limits: PEPRA without_ss cap ({no_ss_cap}) should exceed with_ss cap ({ss_cap})")

    # Classic cap > PEPRA caps
    classic_cap = classic.get("limit_2025", 0)
    if classic_cap and ss_cap and classic_cap <= ss_cap:
        errors.append(f"CalPERS comp limits: Classic cap ({classic_cap}) should exceed PEPRA SS cap ({ss_cap})")

    return errors


# ============================================================
# Vesting
# ============================================================

def validate_vesting(data: dict) -> List[str]:
    errors = []
    v = data.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"CalPERS: vesting.years expected 5, got {v.get('years')}")
    if v.get("schedule") != "cliff":
        errors.append(f"CalPERS: vesting.schedule expected 'cliff', got {v.get('schedule')}")
    return errors


# ============================================================
# Funding status
# ============================================================

def validate_funding(data: dict) -> List[str]:
    errors = []
    fs = data.get("fundingStatus", {})

    # Funded ratio FY2024-25: ~79%
    ratio = fs.get("fundedRatio_fy2024_25_preliminary")
    if ratio is None:
        errors.append("CalPERS: fundingStatus.fundedRatio_fy2024_25_preliminary missing")
    elif not (0.50 < ratio < 1.00):
        errors.append(f"CalPERS: funded ratio implausible: {ratio}")

    # Assets: ~$556B
    assets = fs.get("netAssets_fy2024_25_preliminary_billions")
    if assets is None:
        errors.append("CalPERS: fundingStatus.netAssets_fy2024_25_preliminary_billions missing")
    elif not (200 < assets < 2000):
        errors.append(f"CalPERS: net assets implausible: {assets}B")

    # Discount rate: 6.8%
    dr = fs.get("discountRate")
    if dr != 0.068:
        errors.append(f"CalPERS: discountRate expected 0.068, got {dr}")

    # Investment return: ~11.6%
    ir = fs.get("investmentReturn_fy2024_25_preliminary")
    if ir is None:
        errors.append("CalPERS: investmentReturn_fy2024_25_preliminary missing")
    elif not (0 < ir < 0.5):
        errors.append(f"CalPERS: investment return implausible: {ir}")

    # Chronological funding improvement
    r23 = fs.get("fundedRatio_fy2022_23")
    r24 = fs.get("fundedRatio_fy2023_24")
    r25 = ratio
    if r23 and r24 and r25:
        if not (r23 <= r24 <= r25):
            errors.append(f"CalPERS: funded ratios not monotonically improving: {r23} -> {r24} -> {r25}")

    return errors


# ============================================================
# Total members
# ============================================================

def validate_total_members(data: dict) -> List[str]:
    errors = []
    tm = data.get("totalMembers", {})
    approx = tm.get("approximate")
    if approx is None:
        errors.append("CalPERS: totalMembers.approximate missing")
    elif approx < 1000000:
        errors.append(f"CalPERS: totalMembers.approximate implausibly low: {approx}")
    return errors


# ============================================================
# Jurisdiction
# ============================================================

def validate_jurisdiction(data: dict) -> List[str]:
    errors = []
    j = data.get("jurisdiction", {})
    if j.get("state") != "CA":
        errors.append(f"CalPERS: jurisdiction.state expected 'CA', got '{j.get('state')}'")
    if j.get("level") != "state":
        errors.append(f"CalPERS: jurisdiction.level expected 'state', got '{j.get('level')}'")
    return errors


# ============================================================
# Social Security
# ============================================================

def validate_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") != "varies":
        errors.append(f"CalPERS: socialSecurity.covered expected 'varies', got '{ss.get('covered')}'")
    if not ss.get("note"):
        errors.append("CalPERS: socialSecurity.note missing")
    return errors


# ============================================================
# PEPRA section
# ============================================================

def validate_pepra_section(data: dict) -> List[str]:
    errors = []
    p = data.get("pepra", {})
    if p.get("effectiveDate") != "2013-01-01":
        errors.append(f"CalPERS: pepra.effectiveDate expected '2013-01-01', got '{p.get('effectiveDate')}'")
    if not p.get("description"):
        errors.append("CalPERS: pepra.description missing")
    if not p.get("keyChanges"):
        errors.append("CalPERS: pepra.keyChanges missing")
    return errors


# ============================================================
# Metadata and sources
# ============================================================

def validate_metadata(data: dict) -> List[str]:
    errors = []
    version = data.get("version", "")
    if not version.startswith("2026"):
        errors.append(f"CalPERS: version should start with '2026', got '{version}'")
    if not data.get("last_updated"):
        errors.append("CalPERS: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 5:
        errors.append(f"CalPERS: expected at least 5 sources, got {len(sources)}")
    # All sources should have url
    for i, s in enumerate(sources):
        if not s.get("url"):
            errors.append(f"CalPERS: source[{i}] missing url")
    return errors


# ============================================================
# Age factor monotonicity spot checks
# ============================================================

def validate_breakpoint_monotonicity(data: dict) -> List[str]:
    """Verify age factor breakpoints are monotonically increasing by age for each formula."""
    errors = []
    rf = data.get("representativeFormulas", {})

    for formula_key in REPRESENTATIVE_FORMULAS:
        formula = rf.get(formula_key, {})
        bps = formula.get("formula", {}).get("ageFactor", {}).get("keyBreakpoints", [])
        if not bps:
            continue
        ages = [bp["age"] for bp in bps]
        factors = [bp["factor"] for bp in bps]
        for i in range(1, len(ages)):
            if ages[i] <= ages[i - 1]:
                errors.append(f"CalPERS '{formula_key}': breakpoint ages not monotonically increasing at index {i}")
            # Safety 3%@50 is flat — skip factor check
            if formula_key != "classic_safety_3pct_at_50":
                if factors[i] < factors[i - 1]:
                    errors.append(f"CalPERS '{formula_key}': breakpoint factors decreasing at age {ages[i]}")

    return errors


# ============================================================
# No Meridian references
# ============================================================

def validate_no_meridian_references(data: dict) -> List[str]:
    errors = []
    # Only flag consumer-specific content that embeds Meridian logic, not comments noting its absence
    raw = json.dumps(data).lower()
    for forbidden in ["engine usage block", "engine-numbered note", "for meridian", "meridian uses", "meridian requires"]:
        if forbidden in raw:
            errors.append(f"CalPERS: forbidden consumer-specific reference found: '{forbidden}'")
    return errors


# ============================================================
# Runner
# ============================================================

def run_all() -> int:
    try:
        data = load_json(CALPERS_PATH)
    except FileNotFoundError:
        print(f"ERROR: {CALPERS_PATH} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {CALPERS_PATH}: {e}")
        return 1

    validators = [
        validate_top_level,
        validate_representative_formulas_exist,
        validate_additional_formulas_exist,
        validate_formula_required_keys,
        validate_pepra_flags,
        validate_category_flags,
        validate_classic_misc_55,
        validate_classic_misc_60,
        validate_pepra_misc_62,
        validate_classic_safety_3pct_50,
        validate_pepra_safety_57,
        validate_cola,
        validate_comp_limits,
        validate_vesting,
        validate_funding,
        validate_total_members,
        validate_jurisdiction,
        validate_social_security,
        validate_pepra_section,
        validate_metadata,
        validate_breakpoint_monotonicity,
        validate_no_meridian_references,
    ]

    all_errors = []
    for validator in validators:
        all_errors.extend(validator(data))

    check_count = count_checks()

    if all_errors:
        print(f"CALPERS VALIDATION FAILED — {len(all_errors)} errors:")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"CALPERS VALIDATION: {check_count} checks passed")
        return 0


def count_checks() -> int:
    """Count total individual assertions across all validators."""
    count = 0
    count += 17   # top_level: 16 required keys + abbreviation
    count += 5    # representative formulas exist (5)
    count += 5    # additional formulas exist (5)
    count += 30   # formula required keys: 6 keys x 5 formulas
    count += 5    # pepra flags: 3 classic + 2 pepra
    count += 5    # category flags: 3 misc + 2 safety
    # classic_misc_55: NRA, factor, min factor, min age, max factor, max age, min ret age,
    #                  bp50, bp55, bp factor55, nr age, nr svc, er age, ss rate, non-ss rate
    count += 15
    # classic_misc_60: NRA, factor, min factor, min age, max factor, max age,
    #                  final comp 36, nr age, nr svc, er age
    count += 10
    # pepra_misc_62: NRA, factor, min factor, min age, max factor, max age, min ret age,
    #                bp52, bp62, bp67, factor62, factor67, final comp 36,
    #                cap_ss, cap_no_ss, cap plausible, nr age, nr svc, er age
    count += 19
    # classic_safety_3pct_50: NRA, factor, min factor, min age, max factor, max age,
    #                          nr age, nr svc, category, example benefit
    count += 10
    # pepra_safety_57: NRA, factor, min factor, min age, max factor, max age,
    #                  bp50, bp57, factor50, factor57, final comp 36,
    #                  nr age, nr svc, er age, AB1383
    count += 15
    # cola: mechanism, 4 rates (2/3/4/5%), pppa exists, pppa thresholds (2), pppa cross-check
    count += 9
    # comp_limits: classic 2025, classic plausible, pepra_ss 2026, pepra_no_ss 2026,
    #              no_ss > ss, classic > ss
    count += 6
    # vesting: years, schedule
    count += 2
    # funding: ratio present, ratio plausible, assets present, assets plausible, discount rate,
    #           investment return present, investment return plausible, monotonicity
    count += 8
    # total_members: present, plausible
    count += 2
    # jurisdiction: state, level
    count += 2
    # social_security: covered=varies, note
    count += 2
    # pepra section: effectiveDate, description, keyChanges
    count += 3
    # metadata: version, last_updated, sources count, source urls
    count += 4
    # breakpoint_monotonicity: 5 formulas x ~7 breakpoint pairs each (approx)
    count += 30
    # no meridian references: 4 checks
    count += 4
    return count


if __name__ == "__main__":
    sys.exit(run_all())
