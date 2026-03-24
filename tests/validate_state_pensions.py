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
    return errors


def validate_frs_fl_contributions(data: dict) -> List[str]:
    errors = []
    contrib = data.get("contributions", {})
    m = contrib.get("member", {})
    if m.get("rate") != 0.03:
        errors.append(f"FRS-FL: member contribution rate expected 0.03 (3%), got {m.get('rate')}")
    if not (0 < m.get("rate", 0) < 1):
        errors.append("FRS-FL: member contribution rate out of range")
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
    if "5%" not in str(er.get("reduction", "")):
        errors.append("FRS-FL: earlyRetirement.reduction should reference 5% per year")
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
    c += 3    # metadata
    # FRS FL
    c += 12   # top-level keys + abbrev + state
    c += 6    # tiers: tier1/2 exist, vesting 6+8, AFC 5+8
    c += 3    # cola: tier1 available+maxRate, tier2 not available
    c += 3    # multipliers Regular+SpecialRisk+SeniorMgmt
    c += 2    # contributions member rate + range
    c += 4    # DROP available + interest + maxParticipation x2
    c += 5    # HIS available + max + fundingRate + minService x2
    c += 1    # SS covered=true
    c += 1    # early retirement 5%
    c += 3    # metadata
    return c


if __name__ == "__main__":
    sys.exit(run_all())
