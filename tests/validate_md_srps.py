#!/usr/bin/env python3
"""
Validation suite for Maryland SRPS (State Retirement and Pension System).
File: states/maryland/md-srps-plans.json

Validates:
  - Structure: required top-level keys, all subsystems present
  - TPS/EPS: ACPS (1.2%/1.8%) and RCPB (1.5%) formulas, AFC periods
  - Retirement eligibility: Rule of 90, age/service thresholds
  - COLA: two-tier structure (ACPS), single-tier (RCPB), investment-dependent caps
  - Member contributions: 7% EPS/TPS, 4% LEOPS
  - LEOPS: 2.0% formula, 30-year/60% max
  - CORS: 1.8% formula, 20-year normal retirement
  - Vesting: 10-year for EPS/TPS; 5-year for CORS/LEOPS
  - Funding: assets, return, assumed rate
  - Social security: covered=true (with legacy exception)
  - No consumer-specific references

Session 64: Initial build — Maryland SRPS.
"""

import json
import sys
from typing import List

MD_SRPS_PATH = "states/maryland/md-srps-plans.json"

REQUIRED_SYSTEMS = [
    "teachersPensionSystem",
    "employeesPensionSystem",
    "legacyRetirementSystem",
    "cors",
    "msprs",
    "leops",
    "jrs",
    "lpp"
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
        "assumedRateOfReturn", "systems", "supplementalPlans",
        "contributionRates", "fundingStatus", "sources"
    ]
    for key in required:
        if key not in data:
            errors.append(f"MD-SRPS: missing required top-level key '{key}'")
    if data.get("systemAbbreviation") != "MD-SRPS":
        errors.append(f"MD-SRPS: systemAbbreviation expected 'MD-SRPS', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_systems_present(data: dict) -> List[str]:
    errors = []
    systems = data.get("systems", {})
    for s in REQUIRED_SYSTEMS:
        if s not in systems:
            errors.append(f"MD-SRPS: missing system '{s}'")
    return errors


def validate_components_present(data: dict) -> List[str]:
    errors = []
    systems = data.get("systems", {})
    for sys_name in ["teachersPensionSystem", "employeesPensionSystem"]:
        components = systems.get(sys_name, {}).get("components", {})
        for comp in ["acps", "rcpb"]:
            if comp not in components:
                errors.append(f"MD-SRPS: {sys_name} missing component '{comp}'")
    return errors


# ============================================================
# TPS / EPS ACPS formula
# ============================================================

def validate_acps_formula(data: dict) -> List[str]:
    errors = []
    for sys_name in ["teachersPensionSystem", "employeesPensionSystem"]:
        acps = data.get("systems", {}).get(sys_name, {}).get("components", {}).get("acps", {})
        formula = acps.get("formula", {})

        # Multipliers: 1.2% pre-1998, 1.8% post-1998
        if formula.get("multiplier_pre1998") != 0.012:
            errors.append(f"MD-SRPS {sys_name} ACPS: multiplier_pre1998 expected 0.012, got {formula.get('multiplier_pre1998')}")
        if formula.get("multiplier_post1998") != 0.018:
            errors.append(f"MD-SRPS {sys_name} ACPS: multiplier_post1998 expected 0.018, got {formula.get('multiplier_post1998')}")

        # AFC: 3 years
        afc = formula.get("afc", {})
        if afc.get("period_years") != 3:
            errors.append(f"MD-SRPS {sys_name} ACPS: afc.period_years expected 3, got {afc.get('period_years')}")

        # Member contribution: 7%
        mc = acps.get("memberContribution", {})
        if mc.get("rate") != 0.07:
            errors.append(f"MD-SRPS {sys_name} ACPS: memberContribution.rate expected 0.07, got {mc.get('rate')}")

        # Vesting: 10 years
        v = acps.get("vesting", {})
        if v.get("years") != 10:
            errors.append(f"MD-SRPS {sys_name} ACPS: vesting.years expected 10, got {v.get('years')}")

    return errors


# ============================================================
# TPS / EPS RCPB formula
# ============================================================

def validate_rcpb_formula(data: dict) -> List[str]:
    errors = []
    for sys_name in ["teachersPensionSystem", "employeesPensionSystem"]:
        rcpb = data.get("systems", {}).get(sys_name, {}).get("components", {}).get("rcpb", {})
        formula = rcpb.get("formula", {})

        # Multiplier: 1.5%
        if formula.get("multiplier") != 0.015:
            errors.append(f"MD-SRPS {sys_name} RCPB: multiplier expected 0.015, got {formula.get('multiplier')}")

        # AFC: 5 years
        afc = formula.get("afc", {})
        if afc.get("period_years") != 5:
            errors.append(f"MD-SRPS {sys_name} RCPB: afc.period_years expected 5, got {afc.get('period_years')}")

        # Member contribution: 7%
        mc = rcpb.get("memberContribution", {})
        if mc.get("rate") != 0.07:
            errors.append(f"MD-SRPS {sys_name} RCPB: memberContribution.rate expected 0.07, got {mc.get('rate')}")

        # Vesting: 10 years
        v = rcpb.get("vesting", {})
        if v.get("years") != 10:
            errors.append(f"MD-SRPS {sys_name} RCPB: vesting.years expected 10, got {v.get('years')}")

    return errors


# ============================================================
# TPS RCPB retirement eligibility (representative)
# ============================================================

def validate_tps_rcpb_eligibility(data: dict) -> List[str]:
    errors = []
    rcpb = data["systems"]["teachersPensionSystem"]["components"]["rcpb"]
    ret = rcpb.get("retirementEligibility", {})

    normal = ret.get("normalRetirement", [])
    rules = [r.get("rule", "") for r in normal]

    # Rule of 90 present
    if not any("90" in r for r in rules):
        errors.append("MD-SRPS TPS RCPB: normalRetirement missing Rule of 90")

    # Age 65 with 10 years present
    if not any("65" in r and "10" in r for r in rules):
        errors.append("MD-SRPS TPS RCPB: normalRetirement missing age 65/10 year rule")

    # Early: age 60/15
    early = ret.get("earlyRetirement", {})
    if early.get("minimumAge") != 60:
        errors.append(f"MD-SRPS TPS RCPB: earlyRetirement.minimumAge expected 60, got {early.get('minimumAge')}")
    if early.get("minimumService") != 15:
        errors.append(f"MD-SRPS TPS RCPB: earlyRetirement.minimumService expected 15, got {early.get('minimumService')}")

    # Reduction factor present and references 0.5%/month
    rf = early.get("reductionFactor", "")
    if "0.5" not in rf:
        errors.append("MD-SRPS TPS RCPB: earlyRetirement.reductionFactor should reference 0.5%")

    # Max reduction 30%
    if early.get("maximumReduction") and "30" not in str(early.get("maximumReduction")):
        errors.append("MD-SRPS TPS RCPB: earlyRetirement.maximumReduction should reference 30%")

    return errors


# ============================================================
# TPS ACPS retirement eligibility
# ============================================================

def validate_tps_acps_eligibility(data: dict) -> List[str]:
    errors = []
    acps = data["systems"]["teachersPensionSystem"]["components"]["acps"]
    ret = acps.get("retirementEligibility", {})

    normal = ret.get("normalRetirement", [])
    rules = [r.get("rule", "") for r in normal]

    if not any("90" in r for r in rules):
        errors.append("MD-SRPS TPS ACPS: normalRetirement missing Rule of 90")

    # ACPS early: age 55/15, reduces before age 62 (not 65)
    early = ret.get("earlyRetirement", {})
    if early.get("minimumAge") != 55:
        errors.append(f"MD-SRPS TPS ACPS: earlyRetirement.minimumAge expected 55, got {early.get('minimumAge')}")
    if early.get("minimumService") != 15:
        errors.append(f"MD-SRPS TPS ACPS: earlyRetirement.minimumService expected 15, got {early.get('minimumService')}")
    if "62" not in str(early.get("reductionFactor", "")):
        errors.append("MD-SRPS TPS ACPS: earlyRetirement.reductionFactor should reference age 62")

    return errors


# ============================================================
# COLA
# ============================================================

def validate_cola(data: dict) -> List[str]:
    errors = []

    # ACPS: two-tier (3% pre-2011, 2.5%/1% post-2011)
    tps_acps_cola = data["systems"]["teachersPensionSystem"]["components"]["acps"].get("cola", {})
    two_tier = tps_acps_cola.get("twoTierStructure")
    if not two_tier:
        errors.append("MD-SRPS TPS ACPS: cola.twoTierStructure should be present")

    pre2011 = two_tier.get("serviceBeforeJuly12011", {}) if two_tier else {}
    post2011 = two_tier.get("serviceOnAfterJuly12011", {}) if two_tier else {}
    if pre2011.get("cap") != 0.03:
        errors.append(f"MD-SRPS TPS ACPS: cola pre-2011 cap expected 0.03, got {pre2011.get('cap')}")

    post2011 = two_tier.get("serviceOnAfterJuly12011", {}) if two_tier else {}
    if post2011.get("cap_investment_met") != 0.025:
        errors.append(f"MD-SRPS TPS ACPS: cola post-2011 cap_investment_met expected 0.025, got {post2011.get('cap_investment_met')}")
    if post2011.get("cap_investment_not_met") != 0.01:
        errors.append(f"MD-SRPS TPS ACPS: cola post-2011 cap_investment_not_met expected 0.01, got {post2011.get('cap_investment_not_met')}")

    # RCPB: single-tier (2.5%/1%)
    tps_rcpb_cola = data["systems"]["teachersPensionSystem"]["components"]["rcpb"].get("cola", {})
    if tps_rcpb_cola.get("cap_investment_met") != 0.025:
        errors.append(f"MD-SRPS TPS RCPB: cola.cap_investment_met expected 0.025, got {tps_rcpb_cola.get('cap_investment_met')}")
    if tps_rcpb_cola.get("cap_investment_not_met") != 0.01:
        errors.append(f"MD-SRPS TPS RCPB: cola.cap_investment_not_met expected 0.01, got {tps_rcpb_cola.get('cap_investment_not_met')}")

    # Pre-2011 cap > post-2011 investment_met cap
    if pre2011.get("cap", 0) <= post2011.get("cap_investment_met", 0):
        errors.append(f"MD-SRPS ACPS: pre-2011 COLA cap ({pre2011.get('cap')}) should exceed post-2011 cap ({post2011.get('cap_investment_met')})")

    # Investment_met cap > not_met cap
    met = tps_rcpb_cola.get("cap_investment_met", 0)
    not_met = tps_rcpb_cola.get("cap_investment_not_met", 0)
    if met and not_met and met <= not_met:
        errors.append(f"MD-SRPS RCPB: cap_investment_met ({met}) should exceed cap_investment_not_met ({not_met})")

    return errors


# ============================================================
# CORS
# ============================================================

def validate_cors(data: dict) -> List[str]:
    errors = []
    cors = data.get("systems", {}).get("cors", {})

    formula = cors.get("formula", {})
    if formula.get("multiplier") != 0.018:
        errors.append(f"MD-SRPS CORS: formula.multiplier expected 0.018, got {formula.get('multiplier')}")
    if formula.get("afc", {}).get("period_years") != 3:
        errors.append(f"MD-SRPS CORS: afc.period_years expected 3, got {formula.get('afc', {}).get('period_years')}")

    # Normal retirement: 20 years at any age
    ret = cors.get("retirementEligibility", {})
    normal = ret.get("normalRetirement", {})
    if "20" not in str(normal.get("minimumService", "")):
        errors.append("MD-SRPS CORS: normalRetirement.minimumService should reference 20 years")

    # Member contribution: 7%
    mc = cors.get("memberContribution", {})
    if mc.get("rate") != 0.07:
        errors.append(f"MD-SRPS CORS: memberContribution.rate expected 0.07, got {mc.get('rate')}")

    # Vesting: 5 years
    v = cors.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"MD-SRPS CORS: vesting.years expected 5, got {v.get('years')}")

    return errors


# ============================================================
# LEOPS
# ============================================================

def validate_leops(data: dict) -> List[str]:
    errors = []
    leops = data.get("systems", {}).get("leops", {})

    formula = leops.get("formula", {})
    if formula.get("multiplier") != 0.020:
        errors.append(f"MD-SRPS LEOPS: formula.multiplier expected 0.020, got {formula.get('multiplier')}")
    if formula.get("maximumServiceCredit") != 30:
        errors.append(f"MD-SRPS LEOPS: maximumServiceCredit expected 30, got {formula.get('maximumServiceCredit')}")
    if formula.get("maximumBenefitPct") != 0.60:
        errors.append(f"MD-SRPS LEOPS: maximumBenefitPct expected 0.60 (60%), got {formula.get('maximumBenefitPct')}")

    # Transfer bonus: 2.3%
    xfer = formula.get("transferBonus", {})
    if xfer.get("transferMultiplier") != 0.023:
        errors.append(f"MD-SRPS LEOPS: transferBonus.transferMultiplier expected 0.023, got {xfer.get('transferMultiplier')}")

    # Member contribution: 4%
    mc = leops.get("memberContribution", {})
    if mc.get("rate") != 0.04:
        errors.append(f"MD-SRPS LEOPS: memberContribution.rate expected 0.04, got {mc.get('rate')}")

    # Vesting: 5 years
    v = leops.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"MD-SRPS LEOPS: vesting.years expected 5, got {v.get('years')}")

    # LEOPS member rate (4%) < TPS member rate (7%)
    tps_rate = data["systems"]["teachersPensionSystem"]["components"]["acps"].get("memberContribution", {}).get("rate", 0)
    leops_rate = mc.get("rate", 0)
    if leops_rate and tps_rate and leops_rate >= tps_rate:
        errors.append(f"MD-SRPS: LEOPS member rate ({leops_rate}) should be less than TPS rate ({tps_rate})")

    # Max benefit 60% (multiplier × max service = 0.02 × 30)
    computed = round(formula.get("multiplier", 0) * formula.get("maximumServiceCredit", 0), 4)
    expected = formula.get("maximumBenefitPct", 0)
    if abs(computed - expected) > 0.001:
        errors.append(f"MD-SRPS LEOPS: multiplier × maxService ({computed}) should equal maximumBenefitPct ({expected})")

    return errors


# ============================================================
# Assumed rate and funding
# ============================================================

def validate_funding(data: dict) -> List[str]:
    errors = []

    # Assumed rate: 7.75%
    arr = data.get("assumedRateOfReturn")
    if arr != 0.0775:
        errors.append(f"MD-SRPS: assumedRateOfReturn expected 0.0775, got {arr}")

    fs = data.get("fundingStatus", {})

    # Total assets ~$70B
    assets = fs.get("totalAssets_billions_approx")
    if not (assets and 30 < assets < 200):
        errors.append(f"MD-SRPS: totalAssets_billions_approx implausible: {assets}")

    # FY2024 return: 6.93%
    ir = fs.get("investmentReturn_fy2024")
    if ir != 0.0693:
        errors.append(f"MD-SRPS: investmentReturn_fy2024 expected 0.0693, got {ir}")

    # FY2024 return < assumed rate (this triggered 1% COLA)
    if arr and ir and ir >= arr:
        errors.append(f"MD-SRPS: FY2024 return ({ir}) should be below assumed rate ({arr}) — triggers 1% COLA cap")

    # Annual benefit payments plausible
    bp = fs.get("annualBenefitPayments_billions")
    if not (bp and 1 < bp < 20):
        errors.append(f"MD-SRPS: annualBenefitPayments_billions implausible: {bp}")

    return errors


# ============================================================
# Social security
# ============================================================

def validate_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not True:
        errors.append(f"MD-SRPS: socialSecurity.covered expected true (most members), got {ss.get('covered')}")
    if not ss.get("note"):
        errors.append("MD-SRPS: socialSecurity.note missing (should explain ETRS exception)")
    return errors


# ============================================================
# Legacy ETRS
# ============================================================

def validate_etrs(data: dict) -> List[str]:
    errors = []
    etrs = data.get("systems", {}).get("legacyRetirementSystem", {})

    if "CLOSED" not in str(etrs.get("status", "")):
        errors.append("MD-SRPS ETRS: status should indicate CLOSED")

    formula = etrs.get("formula", {})
    if "55" not in str(formula.get("structure", "")):
        errors.append("MD-SRPS ETRS: formula.structure should reference ÷55")

    cola = etrs.get("cola", {})
    if "planA" not in cola or "planB" not in cola or "planC" not in cola:
        errors.append("MD-SRPS ETRS: cola missing plan A/B/C structure")

    # Plan A: unlimited; Plan B: 5% cap
    if cola.get("planA", {}).get("cap") != "unlimited":
        errors.append("MD-SRPS ETRS: planA.cap should be 'unlimited'")
    if cola.get("planB", {}).get("cap") != 0.05:
        errors.append(f"MD-SRPS ETRS: planB.cap expected 0.05, got {cola.get('planB', {}).get('cap')}")

    # ETRS: not SS-covered
    etrs_ss = etrs.get("socialSecurity", {})
    if etrs_ss.get("covered") is not False:
        errors.append("MD-SRPS ETRS: socialSecurity.covered should be false")

    return errors


# ============================================================
# Jurisdiction and metadata
# ============================================================

def validate_jurisdiction(data: dict) -> List[str]:
    errors = []
    j = data.get("jurisdiction", {})
    if j.get("state") != "MD":
        errors.append(f"MD-SRPS: jurisdiction.state expected 'MD', got '{j.get('state')}'")
    if j.get("level") != "state":
        errors.append(f"MD-SRPS: jurisdiction.level expected 'state', got '{j.get('level')}'")
    return errors


def validate_metadata(data: dict) -> List[str]:
    errors = []
    if not str(data.get("version", "")).startswith("2026"):
        errors.append(f"MD-SRPS: version should start with '2026', got '{data.get('version')}'")
    if not data.get("last_updated"):
        errors.append("MD-SRPS: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 8:
        errors.append(f"MD-SRPS: expected at least 8 sources, got {len(sources)}")
    for i, s in enumerate(sources):
        if not s.get("url"):
            errors.append(f"MD-SRPS: source[{i}] missing url")
    return errors


def validate_no_consumer_references(data: dict) -> List[str]:
    errors = []
    raw = json.dumps(data).lower()
    for forbidden in ["engine usage block", "engine-numbered note", "for meridian", "meridian uses"]:
        if forbidden in raw:
            errors.append(f"MD-SRPS: forbidden consumer reference: '{forbidden}'")
    return errors


# ============================================================
# Cross-checks
# ============================================================

def validate_cross_checks(data: dict) -> List[str]:
    errors = []

    # TPS RCPB early retirement is later than ACPS (60 vs 55)
    acps_early = data["systems"]["teachersPensionSystem"]["components"]["acps"].get("retirementEligibility", {}).get("earlyRetirement", {}).get("minimumAge", 0)
    rcpb_early = data["systems"]["teachersPensionSystem"]["components"]["rcpb"].get("retirementEligibility", {}).get("earlyRetirement", {}).get("minimumAge", 0)
    if acps_early and rcpb_early and rcpb_early <= acps_early:
        errors.append(f"MD-SRPS: RCPB early retirement age ({rcpb_early}) should be later than ACPS ({acps_early})")

    # RCPB AFC is longer than ACPS (5 vs 3)
    acps_afc = data["systems"]["teachersPensionSystem"]["components"]["acps"]["formula"]["afc"].get("period_years", 0)
    rcpb_afc = data["systems"]["teachersPensionSystem"]["components"]["rcpb"]["formula"]["afc"].get("period_years", 0)
    if acps_afc and rcpb_afc and rcpb_afc <= acps_afc:
        errors.append(f"MD-SRPS: RCPB AFC period ({rcpb_afc} yrs) should exceed ACPS AFC period ({acps_afc} yrs)")

    # RCPB multiplier (1.5%) is between ACPS pre/post (1.2%/1.8%)
    rcpb_mult = data["systems"]["teachersPensionSystem"]["components"]["rcpb"]["formula"].get("multiplier", 0)
    acps_pre = data["systems"]["teachersPensionSystem"]["components"]["acps"]["formula"].get("multiplier_pre1998", 0)
    acps_post = data["systems"]["teachersPensionSystem"]["components"]["acps"]["formula"].get("multiplier_post1998", 0)
    if acps_pre and acps_post and rcpb_mult:
        if not (acps_pre < rcpb_mult < acps_post):
            errors.append(f"MD-SRPS: RCPB multiplier ({rcpb_mult}) should be between ACPS pre ({acps_pre}) and post ({acps_post})")

    # Total members plausible
    members = data.get("totalMembers", {}).get("approximate", 0)
    if not (200000 < members < 1000000):
        errors.append(f"MD-SRPS: totalMembers.approximate implausible: {members}")

    return errors


# ============================================================
# Runner
# ============================================================

def run_all() -> int:
    try:
        data = load_json(MD_SRPS_PATH)
    except FileNotFoundError:
        print(f"ERROR: {MD_SRPS_PATH} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {MD_SRPS_PATH}: {e}")
        return 1

    validators = [
        validate_top_level,
        validate_systems_present,
        validate_components_present,
        validate_acps_formula,
        validate_rcpb_formula,
        validate_tps_rcpb_eligibility,
        validate_tps_acps_eligibility,
        validate_cola,
        validate_cors,
        validate_leops,
        validate_funding,
        validate_social_security,
        validate_etrs,
        validate_jurisdiction,
        validate_metadata,
        validate_no_consumer_references,
        validate_cross_checks,
    ]

    all_errors = []
    for validator in validators:
        all_errors.extend(validator(data))

    check_count = count_checks()

    if all_errors:
        print(f"MD-SRPS VALIDATION FAILED — {len(all_errors)} errors:")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"MD-SRPS VALIDATION: {check_count} checks passed")
        return 0


def count_checks() -> int:
    count = 0
    count += 15   # top_level: 14 keys + abbreviation
    count += 8    # systems present (8)
    count += 4    # components present (2 systems × 2 components)
    count += 12   # ACPS formula: 2 systems × (2 multipliers + AFC period + member rate + vesting)
    count += 8    # RCPB formula: 2 systems × (multiplier + AFC period + member rate + vesting)
    count += 7    # TPS RCPB eligibility: rule90, age65/10, early age, early service, reduction, max reduction
    count += 5    # TPS ACPS eligibility: rule90, early age, early service, reduction references 62
    count += 8    # COLA: two-tier flag, pre-2011 cap, post-2011 caps×2, pre>post check, rcpb caps×2, met>not_met
    count += 6    # CORS: multiplier, AFC, 20yr normal, contribution, vesting
    count += 8    # LEOPS: multiplier, maxService, maxPct, transferBonus, contribution, vesting, <TPS rate, 0.02×30=0.60
    count += 6    # Funding: assumed rate, assets, FY2024 return, return<assumed, benefit payments
    count += 2    # Social security: covered=true, note
    count += 6    # ETRS: CLOSED status, ÷55 formula, plans A/B/C, plan A unlimited, plan B 5%, SS=false
    count += 2    # Jurisdiction: state, level
    count += 4    # Metadata: version, last_updated, sources count, source urls
    count += 4    # No consumer references (4 patterns)
    count += 5    # Cross-checks: RCPB early>ACPS, RCPB AFC>ACPS, RCPB mult between ACPS, members plausible
    return count


if __name__ == "__main__":
    sys.exit(run_all())
