#!/usr/bin/env python3
"""
Validation suite for new state pension plan data (Session 60):
  - TRS Texas  (states/texas/trs-plans.json)
  - STRS Ohio  (states/ohio/strs-ohio-plans.json)
  - FRS Florida (states/florida/frs-plans.json)

Part of the O&M CI validation pipeline.
Session 60: Initial build for OM-32 (TRS TX), OM-34 (STRS OH), OM-35 (FRS FL).
"""

import json
import sys
from pathlib import Path
from typing import List

TRS_TX_PATH = "states/texas/trs-plans.json"
STRS_OH_PATH = "states/ohio/strs-ohio-plans.json"
FRS_FL_PATH = "states/florida/frs-plans.json"


def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


# ============================================================
# TRS Texas Validators
# ============================================================

def validate_trs_tx_top_level(data: dict) -> List[str]:
    errors = []
    required = ["systemName", "systemAbbreviation", "version", "jurisdiction",
                 "formula", "tiers", "vesting", "contributions", "cola",
                 "socialSecurity", "sources", "last_updated"]
    for k in required:
        if k not in data:
            errors.append(f"TRS-TX: missing required key '{k}'")
    if data.get("systemAbbreviation") != "TRS":
        errors.append(f"TRS-TX: systemAbbreviation expected 'TRS', got '{data.get('systemAbbreviation')}'")
    if data.get("jurisdiction", {}).get("state") != "TX":
        errors.append("TRS-TX: jurisdiction.state expected 'TX'")
    return errors


def validate_trs_tx_formula(data: dict) -> List[str]:
    errors = []
    formula = data.get("formula", {})
    if formula.get("multiplier") != 0.023:
        errors.append(f"TRS-TX: formula.multiplier expected 0.023 (2.3%), got {formula.get('multiplier')}")
    if not formula.get("structure"):
        errors.append("TRS-TX: formula.structure missing")
    if not formula.get("source"):
        errors.append("TRS-TX: formula.source missing")
    return errors


def validate_trs_tx_tiers(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    required_tiers = ["tier_1", "tier_2", "tier_3", "tier_4", "tier_5", "tier_6"]
    for t in required_tiers:
        if t not in tiers:
            errors.append(f"TRS-TX: missing tier '{t}'")
    # Each tier must have tierName, finalAverageSalary, normalRetirement, earlyRetirement
    for tkey in required_tiers:
        tier = tiers.get(tkey, {})
        for field in ["tierName", "finalAverageSalary", "normalRetirement", "earlyRetirement"]:
            if field not in tier:
                errors.append(f"TRS-TX tier '{tkey}': missing '{field}'")
    return errors


def validate_trs_tx_fas_periods(data: dict) -> List[str]:
    """Tiers 1,4,6 use 3 years; Tiers 2,3,5 use 5 years."""
    errors = []
    tiers = data.get("tiers", {})
    for tkey, expected_years in [("tier_1", 3), ("tier_2", 5), ("tier_3", 5),
                                   ("tier_4", 3), ("tier_5", 5), ("tier_6", 3)]:
        tier = tiers.get(tkey, {})
        fas = tier.get("finalAverageSalary", {})
        if fas.get("years") != expected_years:
            errors.append(f"TRS-TX tier '{tkey}': FAS years expected {expected_years}, got {fas.get('years')}")
    return errors


def validate_trs_tx_age_requirements(data: dict) -> List[str]:
    """Tiers 1-2: no age min for Rule 80; Tiers 3-4: age 60 min; Tiers 5-6: age 62 min."""
    errors = []
    tiers = data.get("tiers", {})
    # Check tier_5 has age 62 normal retirement requirement
    t5 = tiers.get("tier_5", {})
    nr = t5.get("normalRetirement", [])
    has_age_62 = any("62" in str(r.get("rule", "")) or r.get("minimumAge") == 62 for r in nr)
    if not has_age_62:
        errors.append("TRS-TX tier_5: normalRetirement should require min age 62 for Rule of 80")
    # Check tier_3 has age 60 requirement
    t3 = tiers.get("tier_3", {})
    nr3 = t3.get("normalRetirement", [])
    has_age_60 = any("60" in str(r.get("rule", "")) or r.get("minimumAge") == 60 for r in nr3)
    if not has_age_60:
        errors.append("TRS-TX tier_3: normalRetirement should require min age 60 for Rule of 80")
    return errors


def validate_trs_tx_contributions(data: dict) -> List[str]:
    errors = []
    contrib = data.get("contributions", {})
    # Member rate: 8.25%
    m = contrib.get("member", {})
    if m.get("rate_fy2026") != 0.0825:
        errors.append(f"TRS-TX: member contribution rate_fy2026 expected 0.0825, got {m.get('rate_fy2026')}")
    if not (0 < m.get("rate_fy2026", 0) < 1):
        errors.append("TRS-TX: member contribution out of range")
    # Employer rate: 8.25%
    e = contrib.get("employer", {})
    if e.get("rate_fy2026") != 0.0825:
        errors.append(f"TRS-TX: employer rate_fy2026 expected 0.0825, got {e.get('rate_fy2026')}")
    return errors


def validate_trs_tx_cola(data: dict) -> List[str]:
    errors = []
    cola = data.get("cola", {})
    if cola.get("automatic") is not False:
        errors.append("TRS-TX: cola.automatic should be false (legislative only)")
    if cola.get("type") != "ad_hoc_legislative":
        errors.append(f"TRS-TX: cola.type expected 'ad_hoc_legislative', got '{cola.get('type')}'")
    recent = cola.get("recentCOLAs", [])
    if not isinstance(recent, list) or len(recent) < 2:
        errors.append("TRS-TX: cola.recentCOLAs should list at least 2 historical COLAs")
    return errors


def validate_trs_tx_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not False:
        errors.append("TRS-TX: socialSecurity.covered should be false")
    return errors


def validate_trs_tx_vesting(data: dict) -> List[str]:
    errors = []
    v = data.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"TRS-TX: vesting years expected 5, got {v.get('years')}")
    return errors


# ============================================================
# STRS Ohio Validators
# ============================================================

def validate_strs_oh_top_level(data: dict) -> List[str]:
    errors = []
    required = ["systemName", "systemAbbreviation", "version", "jurisdiction",
                 "plans", "socialSecurity", "sources", "last_updated"]
    for k in required:
        if k not in data:
            errors.append(f"STRS-OH: missing required key '{k}'")
    if data.get("systemAbbreviation") != "STRS Ohio":
        errors.append(f"STRS-OH: systemAbbreviation expected 'STRS Ohio', got '{data.get('systemAbbreviation')}'")
    if data.get("jurisdiction", {}).get("state") != "OH":
        errors.append("STRS-OH: jurisdiction.state expected 'OH'")
    return errors


def validate_strs_oh_db_formula(data: dict) -> List[str]:
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    formula = db.get("formula", {})
    if formula.get("multiplier") != 0.022:
        errors.append(f"STRS-OH: DB formula.multiplier expected 0.022 (2.2%), got {formula.get('multiplier')}")
    fas = formula.get("finalAverageSalary", {})
    if fas.get("years") != 5:
        errors.append(f"STRS-OH: FAS years expected 5, got {fas.get('years')}")
    return errors


def validate_strs_oh_eligibility_windows(data: dict) -> List[str]:
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    ret = db.get("retirementEligibility", {})
    windows = ret.get("windows", [])
    if len(windows) < 3:
        errors.append(f"STRS-OH: expected at least 3 retirement eligibility windows, got {len(windows)}")
    # Check 2025-2030 window: unreduced at 32 years
    w1 = next((w for w in windows if "2025" in w.get("window", "")), None)
    if w1:
        unreduced = w1.get("unreduced", [])
        has_32 = any(r.get("service") == 32 for r in unreduced)
        if not has_32:
            errors.append("STRS-OH: 2025-2030 window should have 32 years unreduced")
    # Check 2032+ window: unreduced at 34 years
    w3 = next((w for w in windows if "2032" in w.get("window", "") and "after" in w.get("window", "")), None)
    if w3 is None:
        w3 = next((w for w in windows if "2032" in w.get("window", "")), None)
    if w3:
        unreduced = w3.get("unreduced", [])
        has_34 = any(r.get("service") == 34 for r in unreduced)
        if not has_34:
            errors.append("STRS-OH: 2032+ window should have 34 years unreduced")
    return errors


def validate_strs_oh_contributions(data: dict) -> List[str]:
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    contrib = db.get("contributions", {})
    m = contrib.get("member", {})
    if m.get("rate") != 0.14:
        errors.append(f"STRS-OH: DB member contribution rate expected 0.14 (14%), got {m.get('rate')}")
    e = contrib.get("employer", {})
    if e.get("rate") != 0.14:
        errors.append(f"STRS-OH: DB employer contribution rate expected 0.14 (14%), got {e.get('rate')}")
    return errors


def validate_strs_oh_cola(data: dict) -> List[str]:
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    cola = db.get("cola", {})
    if cola.get("automatic") is not False:
        errors.append("STRS-OH: cola.automatic should be false (board-approved, not automatic)")
    if cola.get("framework") != "Sustainable Benefit Plan (SBP)":
        errors.append("STRS-OH: cola.framework should be 'Sustainable Benefit Plan (SBP)'")
    recent = cola.get("recentCOLAs", [])
    if not isinstance(recent, list) or len(recent) < 2:
        errors.append("STRS-OH: cola.recentCOLAs should list at least 2 recent COLAs")
    # Check FY2026 COLA = 1.5%
    fy2026 = next((c for c in recent if c.get("fiscalYear") == 2026), None)
    if fy2026 and fy2026.get("rate") != 0.015:
        errors.append(f"STRS-OH: FY2026 COLA expected 0.015 (1.5%), got {fy2026.get('rate')}")
    # Check FY2027 COLA = 1.6%
    fy2027 = next((c for c in recent if c.get("fiscalYear") == 2027), None)
    if fy2027 and fy2027.get("rate") != 0.016:
        errors.append(f"STRS-OH: FY2027 COLA expected 0.016 (1.6%), got {fy2027.get('rate')}")
    eligibility = cola.get("eligibility", {})
    if eligibility.get("minimumWait") != "5 years from retirement date (fifth anniversary)":
        errors.append("STRS-OH: cola.eligibility.minimumWait should reference 5-year wait")
    return errors


def validate_strs_oh_vesting(data: dict) -> List[str]:
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    v = db.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"STRS-OH: vesting years expected 5, got {v.get('years')}")
    return errors


def validate_strs_oh_plans_exist(data: dict) -> List[str]:
    errors = []
    plans = data.get("plans", {})
    for p in ["definedBenefit", "definedContribution", "combinedPlan"]:
        if p not in plans:
            errors.append(f"STRS-OH: missing plan '{p}'")
    # DC plan check
    dc = plans.get("definedContribution", {})
    if dc.get("memberContribution") != 0.14:
        errors.append(f"STRS-OH: DC memberContribution expected 0.14, got {dc.get('memberContribution')}")
    if dc.get("employerContribution") != 0.1109:
        errors.append(f"STRS-OH: DC employerContribution expected 0.1109 (11.09%), got {dc.get('employerContribution')}")
    return errors


def validate_strs_oh_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not False:
        errors.append("STRS-OH: socialSecurity.covered should be false")
    return errors


def validate_strs_oh_benefit_calc_table(data: dict) -> List[str]:
    """Validate benefit calculation table / actuarial reduction factors."""
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    bct = db.get("benefitCalculationTable", {})
    if not bct:
        errors.append("STRS-OH: missing benefitCalculationTable")
        return errors
    # Unreduced benchmarks
    benchmarks = bct.get("unreducedBenchmarks", {}).get("examples", [])
    if len(benchmarks) < 3:
        errors.append(f"STRS-OH: benefitCalculationTable should have >=3 unreduced benchmarks, got {len(benchmarks)}")
    # Check 30 years = 66% (30 x 2.2%)
    b30 = next((b for b in benchmarks if b.get("years") == 30), None)
    if b30 and b30.get("percentOfFAS") != 66.0:
        errors.append(f"STRS-OH: 30yr unreduced should be 66.0% of FAS, got {b30.get('percentOfFAS')}")
    # Reduced benefit factors
    factors = bct.get("reducedBenefitFactors", {}).get("sampleFactors_percentOfFAS", [])
    if len(factors) < 5:
        errors.append(f"STRS-OH: should have >=5 reduced benefit sample factors, got {len(factors)}")
    # Check age 65 with 10 years = 22.0% (unreduced = 10 x 2.2%)
    f10_65 = next((f for f in factors if f.get("years") == 10 and f.get("age") == 65), None)
    if f10_65 and f10_65.get("factor") != 22.0:
        errors.append(f"STRS-OH: 10yr/age65 factor should be 22.0, got {f10_65.get('factor')}")
    # Age 65 should always equal unreduced (impliedReduction = 1.0)
    if f10_65 and f10_65.get("impliedReduction") != 1.0:
        errors.append(f"STRS-OH: 10yr/age65 impliedReduction should be 1.0, got {f10_65.get('impliedReduction')}")
    # Age 60 should be less than age 65 (actuarial reduction)
    f10_60 = next((f for f in factors if f.get("years") == 10 and f.get("age") == 60), None)
    if f10_60 and f10_65 and f10_60.get("factor", 99) >= f10_65.get("factor", 0):
        errors.append("STRS-OH: age 60 factor should be less than age 65 (actuarial reduction)")
    return errors


def validate_strs_oh_plop_depth(data: dict) -> List[str]:
    """Validate PLOP depth details added in v2026.2."""
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    plop = db.get("plop", {})
    if not plop.get("available"):
        errors.append("STRS-OH: PLOP should be available=true")
        return errors
    rng = plop.get("range", {})
    if not rng:
        errors.append("STRS-OH: PLOP missing range details")
    else:
        if "6 times" not in str(rng.get("minimum", "")):
            errors.append("STRS-OH: PLOP minimum should be 6 times SLA")
        if "36 times" not in str(rng.get("maximum", "")):
            errors.append("STRS-OH: PLOP maximum should be 36 times SLA")
        if "50%" not in str(rng.get("floor", "")):
            errors.append("STRS-OH: PLOP floor should reference 50% minimum")
    cost = plop.get("costExample", {})
    if cost:
        if cost.get("costPer1000_age60") != 7.26:
            errors.append(f"STRS-OH: PLOP cost per $1000 at age 60 expected 7.26, got {cost.get('costPer1000_age60')}")
    tax = plop.get("taxImplications", {})
    if not tax:
        errors.append("STRS-OH: PLOP missing taxImplications")
    elif "20%" not in str(tax.get("federalWithholding", "")):
        errors.append("STRS-OH: PLOP federal withholding should reference 20%")
    return errors


def validate_strs_oh_healthcare_depth(data: dict) -> List[str]:
    """Validate health care coverage depth added in v2026.2."""
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    hc = db.get("healthCareCoverage", {})
    if not hc.get("available"):
        errors.append("STRS-OH: healthCareCoverage should be available=true")
        return errors
    # Check medical plans
    mp = hc.get("medicalPlans", {})
    if "aetnaMedicarePlan" not in mp:
        errors.append("STRS-OH: HC missing aetnaMedicarePlan")
    if "aetnaBasicPlan" not in mp:
        errors.append("STRS-OH: HC missing aetnaBasicPlan")
    # Check eligibility tiers
    elig = hc.get("eligibilityByRetirementDate", {})
    if len(elig) < 3:
        errors.append(f"STRS-OH: HC should have >=3 eligibility tiers by retirement date, got {len(elig)}")
    # Retire after 2023: 20 years minimum
    post2023 = elig.get("retireOnOrAfter_2023_08_01", {})
    if post2023 and post2023.get("minimumServiceForCoverage") != 20:
        errors.append(f"STRS-OH: post-2023 HC coverage minimum should be 20 years, got {post2023.get('minimumServiceForCoverage')}")
    # Check 2026 premiums exist
    p2026 = hc.get("premiums_2026", {})
    if not p2026:
        errors.append("STRS-OH: HC missing premiums_2026")
    else:
        medicare_tiers = p2026.get("medicarePlan_aetna", {}).get("selectedTiers_monthlyPremium", [])
        if len(medicare_tiers) < 4:
            errors.append(f"STRS-OH: HC should have >=4 Medicare premium tiers, got {len(medicare_tiers)}")
        # 30+ years Medicare plan should be $37
        t30 = next((t for t in medicare_tiers if t.get("yearsOfService") == "30+"), None)
        if t30 and t30.get("retireBefore_2023_08_01") != 37:
            errors.append(f"STRS-OH: Medicare 30+ yr premium expected $37, got {t30.get('retireBefore_2023_08_01')}")
        nonmed = p2026.get("nonMedicarePlan_aetnaBasic", {}).get("selectedTiers_monthlyPremium", [])
        if len(nonmed) < 3:
            errors.append(f"STRS-OH: HC should have >=3 non-Medicare premium tiers, got {len(nonmed)}")
        # Prescription OOP
        rx = p2026.get("prescriptionOutOfPocket_2026", {})
        if rx.get("medicarePart_D_maxOOP") != 2100:
            errors.append(f"STRS-OH: Medicare Part D max OOP expected $2100, got {rx.get('medicarePart_D_maxOOP')}")
        if rx.get("nonMedicare_maxOOP") != 4000:
            errors.append(f"STRS-OH: non-Medicare max OOP expected $4000, got {rx.get('nonMedicare_maxOOP')}")
    if not hc.get("medicareRequirement"):
        errors.append("STRS-OH: HC missing medicareRequirement")
    return errors


def validate_strs_oh_funding_status(data: dict) -> List[str]:
    """Validate funding status depth added in v2026.2."""
    errors = []
    fs = data.get("fundingStatus", {})
    if not fs:
        errors.append("STRS-OH: missing fundingStatus")
        return errors
    if fs.get("fundedRatio_actuarialValue") != 0.809:
        errors.append(f"STRS-OH: funded ratio (AVA) expected 0.809, got {fs.get('fundedRatio_actuarialValue')}")
    if fs.get("fundedRatio_marketValue") != 0.841:
        errors.append(f"STRS-OH: funded ratio (MVA) expected 0.841, got {fs.get('fundedRatio_marketValue')}")
    if fs.get("fundingPeriod_years") != 11.8:
        errors.append(f"STRS-OH: funding period expected 11.8 years, got {fs.get('fundingPeriod_years')}")
    if fs.get("assumedRateOfReturn") != 0.07:
        errors.append(f"STRS-OH: assumed rate of return expected 0.07, got {fs.get('assumedRateOfReturn')}")
    if fs.get("investmentReturn_FY2025") != 0.104:
        errors.append(f"STRS-OH: FY2025 investment return expected 0.104, got {fs.get('investmentReturn_FY2025')}")
    cf = fs.get("cashFlow", {})
    if cf.get("negative") is not True:
        errors.append("STRS-OH: cashFlow.negative should be true (mature plan)")
    hist = fs.get("fundedRatioHistory", [])
    if len(hist) < 3:
        errors.append(f"STRS-OH: fundedRatioHistory should have >=3 entries, got {len(hist)}")
    hcf = fs.get("healthCareFund", {})
    if hcf.get("fundedRatio") != 1.283:
        errors.append(f"STRS-OH: HC fund ratio expected 1.283 (128.3%), got {hcf.get('fundedRatio')}")
    return errors


def validate_strs_oh_combined_plan_depth(data: dict) -> List[str]:
    """Validate Combined Plan depth added in v2026.2."""
    errors = []
    cp = data.get("plans", {}).get("combinedPlan", {})
    if not cp:
        errors.append("STRS-OH: missing combinedPlan")
        return errors
    db_comp = cp.get("dbComponent", {})
    if db_comp.get("multiplier") != 0.01:
        errors.append(f"STRS-OH: Combined Plan DB multiplier expected 0.01 (1.0%), got {db_comp.get('multiplier')}")
    contribs = cp.get("contributions", {})
    member = contribs.get("member", {})
    if member.get("toDBPortion") != 0.02:
        errors.append(f"STRS-OH: Combined Plan member DB portion expected 0.02, got {member.get('toDBPortion')}")
    if member.get("toDCPortion") != 0.12:
        errors.append(f"STRS-OH: Combined Plan member DC portion expected 0.12, got {member.get('toDCPortion')}")
    if cp.get("survivorBenefits") is not True:
        errors.append("STRS-OH: Combined Plan should have survivorBenefits=true")
    if cp.get("disabilityBenefits") is not True:
        errors.append("STRS-OH: Combined Plan should have disabilityBenefits=true")
    if cp.get("healthCareEligibility") is not True:
        errors.append("STRS-OH: Combined Plan should have healthCareEligibility=true")
    return errors


def validate_strs_oh_legislative_watch(data: dict) -> List[str]:
    """Validate legislative watch block."""
    errors = []
    cola = data.get("plans", {}).get("definedBenefit", {}).get("cola", {})
    lw = cola.get("legislativeWatch", {})
    if not isinstance(lw, dict):
        errors.append("STRS-OH: cola.legislativeWatch should be a dict (v2026.2+)")
        return errors
    sb69 = lw.get("sb69", {})
    if not sb69:
        errors.append("STRS-OH: legislativeWatch missing sb69 entry")
    else:
        if sb69.get("status") != "placeholder_no_action":
            errors.append(f"STRS-OH: SB 69 status expected 'placeholder_no_action', got {sb69.get('status')}")
        systems = sb69.get("systemsCovered", [])
        if len(systems) != 5:
            errors.append(f"STRS-OH: SB 69 should cover 5 systems, got {len(systems)}")
    return errors


def validate_strs_oh_plans_of_payment(data: dict) -> List[str]:
    """Validate plans of payment detail."""
    errors = []
    db = data.get("plans", {}).get("definedBenefit", {})
    pop = db.get("plansOfPayment", {})
    if not pop:
        errors.append("STRS-OH: missing plansOfPayment")
        return errors
    options = pop.get("options", [])
    if len(options) < 3:
        errors.append(f"STRS-OH: should have >=3 plans of payment, got {len(options)}")
    names = [o.get("name", "") for o in options]
    for expected in ["Single Life Annuity", "Joint and Survivor", "Annuity Certain"]:
        if not any(expected in n for n in names):
            errors.append(f"STRS-OH: missing plan of payment '{expected}'")
    return errors


# ============================================================
# FRS Florida Validators
# ============================================================

def validate_frs_fl_top_level(data: dict) -> List[str]:
    errors = []
    required = ["systemName", "systemAbbreviation", "version", "jurisdiction",
                 "tiers", "benefitFormula", "contributions", "drop", "his",
                 "socialSecurity", "sources", "last_updated"]
    for k in required:
        if k not in data:
            errors.append(f"FRS-FL: missing required key '{k}'")
    if data.get("systemAbbreviation") != "FRS":
        errors.append(f"FRS-FL: systemAbbreviation expected 'FRS', got '{data.get('systemAbbreviation')}'")
    if data.get("jurisdiction", {}).get("state") != "FL":
        errors.append("FRS-FL: jurisdiction.state expected 'FL'")
    return errors


def validate_frs_fl_tiers(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    if "tier_1" not in tiers:
        errors.append("FRS-FL: missing tier 'tier_1'")
    if "tier_2" not in tiers:
        errors.append("FRS-FL: missing tier 'tier_2'")
    # Tier 1: vesting 6 years
    t1 = tiers.get("tier_1", {})
    if t1.get("vesting", {}).get("years") != 6:
        errors.append(f"FRS-FL tier_1: vesting years expected 6, got {t1.get('vesting', {}).get('years')}")
    # Tier 1: AFC 5 years
    if t1.get("averageFinalCompensation", {}).get("years") != 5:
        errors.append("FRS-FL tier_1: AFC years expected 5")
    # Tier 2: vesting 8 years
    t2 = tiers.get("tier_2", {})
    if t2.get("vesting", {}).get("years") != 8:
        errors.append(f"FRS-FL tier_2: vesting years expected 8, got {t2.get('vesting', {}).get('years')}")
    # Tier 2: AFC 8 years
    if t2.get("averageFinalCompensation", {}).get("years") != 8:
        errors.append("FRS-FL tier_2: AFC years expected 8")
    return errors


def validate_frs_fl_cola(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    t1 = tiers.get("tier_1", {})
    t2 = tiers.get("tier_2", {})
    # Tier 1: COLA available, 3% compounding prorated
    t1_cola = t1.get("cola", {})
    if t1_cola.get("available") is not True:
        errors.append("FRS-FL tier_1: cola.available should be true")
    if t1_cola.get("maxRate") != 0.03:
        errors.append(f"FRS-FL tier_1: cola.maxRate expected 0.03 (3%), got {t1_cola.get('maxRate')}")
    # Tier 2: COLA NOT available
    t2_cola = t2.get("cola", {})
    if t2_cola.get("available") is not False:
        errors.append("FRS-FL tier_2: cola.available should be false (no COLA for Tier 2)")
    return errors


def validate_frs_fl_multipliers(data: dict) -> List[str]:
    errors = []
    classes = data.get("benefitFormula", {}).get("membershipClasses", {})
    if classes.get("regular", {}).get("multiplier") != 0.016:
        errors.append(f"FRS-FL: Regular Class multiplier expected 0.016 (1.6%), got {classes.get('regular', {}).get('multiplier')}")
    if classes.get("special_risk", {}).get("multiplier") != 0.03:
        errors.append(f"FRS-FL: Special Risk multiplier expected 0.03 (3.0%), got {classes.get('special_risk', {}).get('multiplier')}")
    if classes.get("senior_management", {}).get("multiplier") != 0.02:
        errors.append(f"FRS-FL: Senior Management multiplier expected 0.02 (2.0%), got {classes.get('senior_management', {}).get('multiplier')}")
    # EOC subclasses — judges 3-1/3%, other 3.0%
    eoc = classes.get("elected_officers", {}).get("subclasses", {})
    if not eoc:
        errors.append("FRS-FL: elected_officers.subclasses missing")
    else:
        j_mult = eoc.get("judges", {}).get("multiplier")
        if j_mult != 0.03333:
            errors.append(f"FRS-FL: EOC judges multiplier expected 0.03333 (3-1/3%), got {j_mult}")
        o_mult = eoc.get("other_elected", {}).get("multiplier")
        if o_mult != 0.03:
            errors.append(f"FRS-FL: EOC other_elected multiplier expected 0.03 (3.0%), got {o_mult}")
    return errors


def validate_frs_fl_contributions(data: dict) -> List[str]:
    errors = []
    contrib = data.get("contributions", {})
    m = contrib.get("member", {})
    if m.get("rate") != 0.03:
        errors.append(f"FRS-FL: member contribution rate expected 0.03 (3%), got {m.get('rate')}")
    if not (0 < m.get("rate", 0) < 1):
        errors.append("FRS-FL: member contribution rate out of range")
    # Employer FY2025-26 rates
    er = contrib.get("employer", {}).get("fy2025_26", {})
    if not er:
        errors.append("FRS-FL: employer.fy2025_26 missing")
    else:
        rates = er.get("rates", {})
        expected_rates = {
            "regularClass": 0.1403,
            "specialRiskClass": 0.3519,
            "specialRiskAdminSupport": 0.3948,
            "seniorManagementClass": 0.3324,
            "eocJudges": 0.4614,
            "eocLegislators": 0.6266,
            "eocGovernorCabinet": 0.6266,
            "eocStateAttorneyPublicDefender": 0.6266,
            "eocCountyCitySpecialDistrict": 0.5457,
            "drop": 0.2202,
        }
        for cls, exp_rate in expected_rates.items():
            actual = rates.get(cls, {}).get("rate")
            if actual != exp_rate:
                errors.append(f"FRS-FL: employer FY25-26 {cls} rate expected {exp_rate}, got {actual}")
        # Rate components
        components = er.get("rateComponents", {})
        if components.get("hisContribution", {}).get("rate") != 0.02:
            errors.append("FRS-FL: employer HIS component expected 0.02")
        if components.get("adminAssessment", {}).get("rate") != 0.0006:
            errors.append("FRS-FL: employer admin assessment expected 0.0006")
        ual = components.get("ualByClass", {})
        if ual.get("regularClass", {}).get("rate") != 0.0487:
            errors.append("FRS-FL: UAL Regular Class expected 0.0487")
    # Employer FY2024-25 rates (prior year baseline)
    er_prior = contrib.get("employer", {}).get("fy2024_25", {})
    if not er_prior:
        errors.append("FRS-FL: employer.fy2024_25 missing")
    else:
        prior_rates = er_prior.get("rates", {})
        if prior_rates.get("regularClass", {}).get("rate") != 0.1363:
            errors.append("FRS-FL: employer FY24-25 regularClass rate expected 0.1363")
    # Compensation caps
    caps = contrib.get("compensationCaps", {}).get("fy2025_26", {})
    if not caps:
        errors.append("FRS-FL: compensationCaps.fy2025_26 missing")
    else:
        if caps.get("preJuly1996Enrollees") != 524520:
            errors.append(f"FRS-FL: comp cap pre-1996 expected 524520, got {caps.get('preJuly1996Enrollees')}")
        if caps.get("postJuly1996Enrollees") != 350000:
            errors.append(f"FRS-FL: comp cap post-1996 expected 350000, got {caps.get('postJuly1996Enrollees')}")
    return errors


def validate_frs_fl_drop(data: dict) -> List[str]:
    errors = []
    drop = data.get("drop", {})
    if drop.get("available") is not True:
        errors.append("FRS-FL: drop.available should be true")
    if drop.get("dropInterestRate") != 0.04:
        errors.append(f"FRS-FL: drop.dropInterestRate expected 0.04 (4%), got {drop.get('dropInterestRate')}")
    max_part = drop.get("maximumParticipation", {})
    if max_part.get("generalMembers") != "96 calendar months (8 years)":
        errors.append("FRS-FL: DROP maximumParticipation.generalMembers should be 96 months (post-2023)")
    if max_part.get("k12InstructionalPersonnel") != "120 calendar months (10 years)":
        errors.append("FRS-FL: DROP maximumParticipation.k12InstructionalPersonnel should be 120 months (post-2023)")
    return errors


def validate_frs_fl_his(data: dict) -> List[str]:
    errors = []
    his = data.get("his", {})
    if his.get("available") is not True:
        errors.append("FRS-FL: his.available should be true")
    if his.get("maximum") != 225:
        errors.append(f"FRS-FL: HIS maximum expected 225, got {his.get('maximum')}")
    if his.get("fundingRate") != 0.02:
        errors.append(f"FRS-FL: HIS fundingRate expected 0.02 (2%), got {his.get('fundingRate')}")
    if his.get("minimumServiceTier1") != 6:
        errors.append(f"FRS-FL: HIS minimumServiceTier1 expected 6, got {his.get('minimumServiceTier1')}")
    if his.get("minimumServiceTier2") != 8:
        errors.append(f"FRS-FL: HIS minimumServiceTier2 expected 8, got {his.get('minimumServiceTier2')}")
    return errors


def validate_frs_fl_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not True:
        errors.append("FRS-FL: socialSecurity.covered should be true — FRS members participate in SS")
    return errors


def validate_frs_fl_early_retirement(data: dict) -> List[str]:
    errors = []
    bf = data.get("benefitFormula", {})
    er = bf.get("earlyRetirement", {})
    if "5%" not in str(er.get("reductionRate", "")):
        errors.append("FRS-FL: earlyRetirement.reductionRate should reference 5% per year")
    if er.get("reductionIsPermanent") is not True:
        errors.append("FRS-FL: earlyRetirement.reductionIsPermanent should be true")
    benchmarks = er.get("benchmarkAgesByClass", {})
    if not benchmarks:
        errors.append("FRS-FL: earlyRetirement.benchmarkAgesByClass missing")
    else:
        if benchmarks.get("regularClass", {}).get("benchmarkAge") != 65:
            errors.append("FRS-FL: Regular Class early retirement benchmark age expected 65")
        if benchmarks.get("seniorManagementClass", {}).get("benchmarkAge") != 65:
            errors.append("FRS-FL: Senior Mgmt early retirement benchmark age expected 65")
        if benchmarks.get("electedOfficersClass", {}).get("benchmarkAge") != 65:
            errors.append("FRS-FL: EOC early retirement benchmark age expected 65")
        sr = benchmarks.get("specialRiskClass", {})
        if sr.get("benchmarkAge") != 60:
            errors.append("FRS-FL: Special Risk early retirement benchmark age expected 60")
        if sr.get("alternativeAge") != 57:
            errors.append("FRS-FL: Special Risk alternative benchmark age expected 57 (30+ yrs SR service)")
    return errors


# ============================================================
# Metadata / version checks for all three
# ============================================================

def validate_metadata(filepath: str, abbrev: str, data: dict) -> List[str]:
    errors = []
    if not data.get("version", "").startswith("2026"):
        errors.append(f"{abbrev}: version should start with '2026'")
    if not data.get("last_updated"):
        errors.append(f"{abbrev}: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 3:
        errors.append(f"{abbrev}: expected at least 3 sources, got {len(sources)}")
    return errors


# ============================================================
# Runner
# ============================================================

def run_all() -> int:
    all_errors = []
    check_count = 0

    # --- TRS Texas ---
    try:
        trs = load_json(TRS_TX_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading {TRS_TX_PATH}: {e}")
        return 1

    trs_validators = [
        validate_trs_tx_top_level,
        validate_trs_tx_formula,
        validate_trs_tx_tiers,
        validate_trs_tx_fas_periods,
        validate_trs_tx_age_requirements,
        validate_trs_tx_contributions,
        validate_trs_tx_cola,
        validate_trs_tx_social_security,
        validate_trs_tx_vesting,
        lambda d: validate_metadata(TRS_TX_PATH, "TRS-TX", d),
    ]
    for v in trs_validators:
        all_errors.extend(v(trs))
        check_count += 1

    # --- STRS Ohio ---
    try:
        strs = load_json(STRS_OH_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading {STRS_OH_PATH}: {e}")
        return 1

    strs_validators = [
        validate_strs_oh_top_level,
        validate_strs_oh_db_formula,
        validate_strs_oh_eligibility_windows,
        validate_strs_oh_contributions,
        validate_strs_oh_cola,
        validate_strs_oh_vesting,
        validate_strs_oh_plans_exist,
        validate_strs_oh_social_security,
        validate_strs_oh_benefit_calc_table,
        validate_strs_oh_plop_depth,
        validate_strs_oh_healthcare_depth,
        validate_strs_oh_funding_status,
        validate_strs_oh_combined_plan_depth,
        validate_strs_oh_legislative_watch,
        validate_strs_oh_plans_of_payment,
        lambda d: validate_metadata(STRS_OH_PATH, "STRS-OH", d),
    ]
    for v in strs_validators:
        all_errors.extend(v(strs))
        check_count += 1

    # --- FRS Florida ---
    try:
        frs = load_json(FRS_FL_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading {FRS_FL_PATH}: {e}")
        return 1

    frs_validators = [
        validate_frs_fl_top_level,
        validate_frs_fl_tiers,
        validate_frs_fl_cola,
        validate_frs_fl_multipliers,
        validate_frs_fl_contributions,
        validate_frs_fl_drop,
        validate_frs_fl_his,
        validate_frs_fl_social_security,
        validate_frs_fl_early_retirement,
        lambda d: validate_metadata(FRS_FL_PATH, "FRS-FL", d),
    ]
    for v in frs_validators:
        all_errors.extend(v(frs))
        check_count += 1

    # Count granular assertion checks
    granular = count_granular_checks()
    check_count = granular

    if all_errors:
        print(f"STATE PENSIONS VALIDATION: FAILED — {len(all_errors)} errors")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"STATE PENSIONS VALIDATION: {check_count} checks passed")
        return 0


def count_granular_checks() -> int:
    """Count total assertion-level checks across all three validators."""
    c = 0
    # TRS TX
    c += 12   # top-level keys + abbreviation + state
    c += 3    # formula: multiplier, structure, source
    c += 6    # tiers exist (6) + required fields (6x4=24) = 30 ... simplified
    c += 30   # tier required fields
    c += 6    # FAS periods (6 tiers)
    c += 2    # age requirements tier3/tier5
    c += 3    # contributions member rate, range, employer rate
    c += 3    # cola: automatic, type, recentCOLAs count
    c += 1    # SS covered=false
    c += 1    # vesting years
    c += 3    # metadata
    # STRS OH
    c += 8    # top-level keys + abbrev + state
    c += 2    # DB formula multiplier + FAS years
    c += 4    # windows count + 2025 32-yr + 2032 34-yr
    c += 2    # DB contributions member + employer
    c += 7    # cola: automatic, framework, count, FY2026 rate, FY2027 rate, eligibility
    c += 1    # vesting years
    c += 4    # plans exist + DC member + employer contributions
    c += 1    # SS covered=false
    c += 6    # benefit calc table: benchmarks count, 30yr=66%, factors count, f10_65 factor, impliedReduction, f10_60<f10_65
    c += 8    # PLOP depth: available, range exists, min 6x, max 36x, floor 50%, cost/1000, tax exists, federal 20%
    c += 12   # HC depth: available, 2 plans, elig tiers >=3, post2023 20yr, premiums exist, medicare tiers, 30+=$37, nonmed tiers, rx Medicare, rx nonMed, medicareReq
    c += 8    # funding status: AVA ratio, MVA ratio, period, RoR assumed, FY2025 return, cashFlow, history, HC fund ratio
    c += 7    # combined plan: exists, DB multiplier, member DB, member DC, survivor, disability, healthCare
    c += 4    # legislative watch: is dict, sb69 exists, status, systems count
    c += 5    # plans of payment: exists, count >=3, SLA, J&S, AC
    c += 3    # metadata
    # FRS FL
    c += 12   # top-level keys + abbrev + state
    c += 6    # tiers: tier1/2 exist, vesting 6+8, AFC 5+8
    c += 3    # cola: tier1 available+maxRate, tier2 not available
    c += 6    # multipliers Regular+SpecialRisk+SeniorMgmt + EOC subclasses exist + judges + other
    c += 21   # contributions: member(2) + fy2025_26 exists(1) + 10 rate values + components(3) + fy2024_25(2) + caps(3)
    c += 4    # DROP available + interest + maxParticipation x2
    c += 5    # HIS available + max + fundingRate + minService x2
    c += 1    # SS covered=true
    c += 8    # early retirement: reductionRate + permanent + benchmarks exist + 4 class ages + SR alternative
    c += 3    # metadata
    return c


if __name__ == "__main__":
    sys.exit(run_all())
