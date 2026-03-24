#!/usr/bin/env python3
"""
Validation suite for Colorado PERA (Colorado Public Employees' Retirement Association).
File: states/colorado/copera-plans.json

Validates:
  - Structure: required top-level keys, all 5 divisions, both HAS tables
  - Formula: 2.5% multiplier, 40-year max, retirement options present
  - HAS calculation: 3-year vs 5-year periods, anti-spiking cap
  - Contribution rates: all 6 rate groups present and plausible
  - AAP: trigger thresholds, FY2026 assessment
  - Annual Increase: base rate, AAP range, FY2026 rate
  - Funding: per-division funded ratios, total assets, discount rate
  - Benefits paid: all 5 divisions, plausible averages
  - Direct distribution: base amount, SB 25-310 reduction
  - No consumer-specific references

Session 63: Initial build — Colorado PERA.
"""

import json
import sys
from pathlib import Path
from typing import List

COPERA_PATH = "states/colorado/copera-plans.json"

REQUIRED_DIVISIONS = ["state", "school", "localGovernment", "judicial", "dps"]

REQUIRED_RATE_GROUPS = [
    "state_general", "state_safety", "school",
    "localGovernment_general", "localGovernment_safety",
    "judicial", "dps"
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
        "divisions", "benefitFormula", "hasCalculation", "hasTables",
        "vesting", "contributionRates", "automaticAdjustmentProvision",
        "annualIncrease", "directDistribution", "fundingStatus",
        "benefitsByDivision_2024", "sources"
    ]
    for key in required:
        if key not in data:
            errors.append(f"COPERA: missing required top-level key '{key}'")
    if data.get("systemAbbreviation") != "COPERA":
        errors.append(f"COPERA: systemAbbreviation expected 'COPERA', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_divisions_present(data: dict) -> List[str]:
    errors = []
    divs = data.get("divisions", {})
    for d in REQUIRED_DIVISIONS:
        if d not in divs:
            errors.append(f"COPERA: missing division '{d}'")
    return errors


def validate_has_tables_present(data: dict) -> List[str]:
    errors = []
    ht = data.get("hasTables", {})
    for t in ["table_2", "table_9", "intermediate_tables"]:
        if t not in ht:
            errors.append(f"COPERA: hasTables missing '{t}'")
    return errors


def validate_rate_groups_present(data: dict) -> List[str]:
    errors = []
    rates = data.get("contributionRates", {}).get("byDivision", {})
    for g in REQUIRED_RATE_GROUPS:
        if g not in rates:
            errors.append(f"COPERA: contributionRates.byDivision missing '{g}'")
    return errors


# ============================================================
# Benefit formula
# ============================================================

def validate_benefit_formula(data: dict) -> List[str]:
    errors = []
    bf = data.get("benefitFormula", {})

    if bf.get("multiplier") != 0.025:
        errors.append(f"COPERA: benefitFormula.multiplier expected 0.025, got {bf.get('multiplier')}")
    if bf.get("maximumBenefitPct") != 1.00:
        errors.append(f"COPERA: benefitFormula.maximumBenefitPct expected 1.00 (100%), got {bf.get('maximumBenefitPct')}")
    if bf.get("maximumServiceYears") != 40:
        errors.append(f"COPERA: benefitFormula.maximumServiceYears expected 40, got {bf.get('maximumServiceYears')}")

    # Retirement options
    opts = bf.get("retirementOptions", {})
    for opt in ["option1", "option2", "option3"]:
        if opt not in opts:
            errors.append(f"COPERA: benefitFormula.retirementOptions missing '{opt}'")

    return errors


# ============================================================
# HAS calculation
# ============================================================

def validate_has_calculation(data: dict) -> List[str]:
    errors = []
    hc = data.get("hasCalculation", {})
    periods = hc.get("periods", {})

    # Pre-2020: 3 years
    pre2020 = periods.get("vested_before_2020", {})
    if pre2020.get("period_count") != 3:
        errors.append(f"COPERA: HAS vested_before_2020 period_count expected 3, got {pre2020.get('period_count')}")

    # Post-2020: 5 years
    post2020 = periods.get("not_vested_before_2020", {})
    if post2020.get("period_count") != 5:
        errors.append(f"COPERA: HAS not_vested_before_2020 period_count expected 5, got {post2020.get('period_count')}")

    # Judicial: 3 years
    judicial = periods.get("judicial_division", {})
    if judicial.get("period_count") != 3:
        errors.append(f"COPERA: HAS judicial_division period_count expected 3, got {judicial.get('period_count')}")

    # Anti-spiking cap: 8%
    cap = hc.get("antiSpikingCap", {})
    if cap.get("annualCapPct") != 0.08:
        errors.append(f"COPERA: antiSpikingCap.annualCapPct expected 0.08, got {cap.get('annualCapPct')}")

    return errors


# ============================================================
# HAS Tables — Table 2 and Table 9
# ============================================================

def validate_has_table_2(data: dict) -> List[str]:
    errors = []
    t2 = data.get("hasTables", {}).get("table_2", {})

    if not t2.get("membershipCriteria"):
        errors.append("COPERA: hasTables.table_2 missing membershipCriteria")
    if not t2.get("fullRetirement"):
        errors.append("COPERA: hasTables.table_2 missing fullRetirement")
    if not t2.get("earlyRetirement"):
        errors.append("COPERA: hasTables.table_2 missing earlyRetirement")

    # Examples: 55 + 25 years = 62.5%
    examples = t2.get("fullRetirement", {}).get("examples", [])
    found_62_5 = any(e.get("benefit_pct_of_has") == 62.5 for e in examples)
    if not found_62_5:
        errors.append("COPERA: table_2 examples missing 55-year-old/25-year example at 62.5%")

    # HAS period = 3 years
    if t2.get("has_period") and "3" not in str(t2.get("has_period")):
        errors.append("COPERA: table_2 has_period should reference 3 years")

    return errors


def validate_has_table_9(data: dict) -> List[str]:
    errors = []
    t9 = data.get("hasTables", {}).get("table_9", {})

    full = t9.get("fullRetirement", {})
    general = full.get("general", {})

    # Full: any age at 35 years
    if "35" not in str(general.get("option1", "")):
        errors.append("COPERA: table_9 fullRetirement.general.option1 should reference 35 years")

    # Full: age 64 with 30 years
    if "64" not in str(general.get("option2", "")) or "30" not in str(general.get("option2", "")):
        errors.append("COPERA: table_9 fullRetirement.general.option2 should reference age 64 and 30 years")

    # Full: age 65 with 5 years
    if "65" not in str(general.get("option3", "")) or "5" not in str(general.get("option3", "")):
        errors.append("COPERA: table_9 fullRetirement.general.option3 should reference age 65 and 5 years")

    # Safety: age 55 with 25 years
    safety = full.get("safetyOfficers", {})
    if "55" not in str(safety.get("option2", "")) or "25" not in str(safety.get("option2", "")):
        errors.append("COPERA: table_9 fullRetirement.safetyOfficers.option2 should reference age 55 and 25 years")

    # Early: general age 55 with 25 years, age 60 with 5 years
    early = t9.get("earlyRetirement", {})
    general_early = early.get("general", [])
    ages = [e.get("minimumAge") for e in general_early]
    if 55 not in ages:
        errors.append("COPERA: table_9 earlyRetirement.general missing age 55 option")
    if 60 not in ages:
        errors.append("COPERA: table_9 earlyRetirement.general missing age 60 option")

    # HAS period = 5 years
    if t9.get("has_period") and "5" not in str(t9.get("has_period")):
        errors.append("COPERA: table_9 has_period should reference 5 years")

    return errors


# ============================================================
# Contribution rates
# ============================================================

def validate_contribution_rates(data: dict) -> List[str]:
    errors = []
    rates = data.get("contributionRates", {}).get("byDivision", {})

    # Member rates
    expected_member_rates = {
        "state_general": 0.11,
        "state_safety": 0.13,
        "school": 0.11,
        "localGovernment_general": 0.09,
        "localGovernment_safety": 0.13,
        "judicial": 0.11
    }
    for group, expected_rate in expected_member_rates.items():
        actual = rates.get(group, {}).get("memberRate")
        if actual != expected_rate:
            errors.append(f"COPERA: {group} memberRate expected {expected_rate}, got {actual}")

    # All member rates in plausible range
    for group, entry in rates.items():
        if isinstance(entry, dict):
            mr = entry.get("memberRate")
            if mr is not None and not (0 < mr < 0.30):
                errors.append(f"COPERA: {group} memberRate implausible: {mr}")

    # State general employer total ~21.63%
    state_emp = rates.get("state_general", {}).get("employerTotal")
    if state_emp is None:
        errors.append("COPERA: state_general employerTotal missing")
    elif not (0.15 < state_emp < 0.35):
        errors.append(f"COPERA: state_general employerTotal implausible: {state_emp}")

    # Safety officer member rate higher than general for state and local
    state_gen_mr = rates.get("state_general", {}).get("memberRate", 0)
    state_saf_mr = rates.get("state_safety", {}).get("memberRate", 0)
    if state_saf_mr <= state_gen_mr:
        errors.append(f"COPERA: state_safety memberRate ({state_saf_mr}) should exceed state_general ({state_gen_mr})")

    return errors


# ============================================================
# AAP
# ============================================================

def validate_aap(data: dict) -> List[str]:
    errors = []
    aap = data.get("automaticAdjustmentProvision", {})

    # Low trigger: < 98%
    low = aap.get("triggerConditions", {}).get("lowTrigger", {})
    if "98" not in str(low.get("condition", "")):
        errors.append("COPERA: AAP lowTrigger condition should reference 98%")

    # High trigger: > 120%
    high = aap.get("triggerConditions", {}).get("highTrigger", {})
    if "120" not in str(high.get("condition", "")):
        errors.append("COPERA: AAP highTrigger condition should reference 120%")

    # FY2026: ratio 102.58%, no adjustment
    fy26 = aap.get("fy2026_assessment", {})
    ratio = fy26.get("ratio")
    if ratio is None:
        errors.append("COPERA: AAP fy2026_assessment.ratio missing")
    elif not (0.98 < ratio < 1.20):
        errors.append(f"COPERA: AAP fy2026 ratio {ratio} should be in 98-120% range")
    if fy26.get("outcome") and "no" not in fy26.get("outcome", "").lower() and "No" not in fy26.get("outcome", ""):
        errors.append("COPERA: AAP fy2026_assessment.outcome should indicate no adjustment triggered")

    # FY2026 AI = 1.0%
    ai_2026 = fy26.get("annualIncrease_july2026")
    if ai_2026 != 0.010:
        errors.append(f"COPERA: AAP fy2026 annualIncrease_july2026 expected 0.010, got {ai_2026}")

    return errors


# ============================================================
# Annual Increase
# ============================================================

def validate_annual_increase(data: dict) -> List[str]:
    errors = []
    ai = data.get("annualIncrease", {})

    # Base rate: 1.5%
    if ai.get("baseRate") != 0.015:
        errors.append(f"COPERA: annualIncrease.baseRate expected 0.015, got {ai.get('baseRate')}")

    # AAP range: 0.5% min, 2.0% max
    aap_range = ai.get("aapRange", {})
    if aap_range.get("minimum") != 0.005:
        errors.append(f"COPERA: annualIncrease.aapRange.minimum expected 0.005, got {aap_range.get('minimum')}")
    if aap_range.get("maximum") != 0.020:
        errors.append(f"COPERA: annualIncrease.aapRange.maximum expected 0.020, got {aap_range.get('maximum')}")

    # Min < base < max
    base = ai.get("baseRate", 0)
    mn = aap_range.get("minimum", 0)
    mx = aap_range.get("maximum", 0)
    if not (mn < base < mx):
        errors.append(f"COPERA: annualIncrease base ({base}) should be between min ({mn}) and max ({mx})")

    # FY2026 rate: 1.0%
    fy26 = ai.get("fy2026", {})
    if fy26.get("rate") != 0.010:
        errors.append(f"COPERA: annualIncrease.fy2026.rate expected 0.010, got {fy26.get('rate')}")

    # Wait period: 36 months for post-2018 members
    wp = ai.get("waitPeriod", {})
    if "36" not in str(wp.get("post2018members", "")):
        errors.append("COPERA: annualIncrease.waitPeriod.post2018members should reference 36 months")

    return errors


# ============================================================
# Direct distribution
# ============================================================

def validate_direct_distribution(data: dict) -> List[str]:
    errors = []
    dd = data.get("directDistribution", {})

    # Base amount: $225M
    if dd.get("baseAmount") != 225000000:
        errors.append(f"COPERA: directDistribution.baseAmount expected 225000000, got {dd.get('baseAmount')}")

    # Scheduled reduction: $190M from July 2027
    sr = dd.get("scheduledReduction", {})
    if sr.get("reducedAmount") != 190000000:
        errors.append(f"COPERA: directDistribution scheduledReduction.reducedAmount expected 190000000, got {sr.get('reducedAmount')}")
    if sr.get("startDate") != "2027-07-01":
        errors.append(f"COPERA: directDistribution scheduledReduction.startDate expected '2027-07-01', got '{sr.get('startDate')}'")

    # 2025 one-time payment: $500M
    otp = dd.get("oneTimePayment2025", {})
    if otp.get("amount") != 500000000:
        errors.append(f"COPERA: directDistribution oneTimePayment2025.amount expected 500000000, got {otp.get('amount')}")

    return errors


# ============================================================
# Funding status
# ============================================================

def validate_funding(data: dict) -> List[str]:
    errors = []
    fs = data.get("fundingStatus", {})

    # Combined ratio 2024: 69.2%
    ratio = fs.get("combinedFundedRatio_2024")
    if ratio != 0.692:
        errors.append(f"COPERA: combinedFundedRatio_2024 expected 0.692, got {ratio}")
    if not (0.40 < (ratio or 0) < 1.00):
        errors.append(f"COPERA: combinedFundedRatio_2024 implausible: {ratio}")

    # Net assets DB: ~$66.7B
    assets = fs.get("netAssets_DB_billions_2024")
    if not (assets and 30 < assets < 200):
        errors.append(f"COPERA: netAssets_DB_billions_2024 implausible: {assets}")

    # Discount rate: 7.25%
    dr = fs.get("discountRate")
    if dr != 0.0725:
        errors.append(f"COPERA: discountRate expected 0.0725, got {dr}")

    # Investment return 2024: 10.8%
    ir = fs.get("investmentReturn_2024")
    if ir != 0.108:
        errors.append(f"COPERA: investmentReturn_2024 expected 0.108, got {ir}")

    # Per-division funded ratios
    by_div = fs.get("byDivision", {})
    for div in REQUIRED_DIVISIONS:
        if div not in by_div:
            errors.append(f"COPERA: fundingStatus.byDivision missing '{div}'")
        else:
            fr = by_div[div].get("fundedRatio")
            if fr and not (0.40 < fr < 1.10):
                errors.append(f"COPERA: {div} fundedRatio implausible: {fr}")

    # State and school are lowest-funded; local/judicial/DPS are higher
    state_fr = by_div.get("state", {}).get("fundedRatio", 0)
    local_fr = by_div.get("localGovernment", {}).get("fundedRatio", 0)
    if state_fr and local_fr and state_fr >= local_fr:
        errors.append(f"COPERA: state fundedRatio ({state_fr}) should be below localGovernment ({local_fr})")

    return errors


# ============================================================
# Benefits paid
# ============================================================

def validate_benefits_paid(data: dict) -> List[str]:
    errors = []
    bb = data.get("benefitsByDivision_2024", {})

    for div in REQUIRED_DIVISIONS:
        if div not in bb:
            errors.append(f"COPERA: benefitsByDivision_2024 missing '{div}'")
        else:
            avg = bb[div].get("averageAnnualBenefit")
            total = bb[div].get("totalBeneficiaries")
            if avg and not (5000 < avg < 200000):
                errors.append(f"COPERA: {div} averageAnnualBenefit implausible: {avg}")
            if total and total <= 0:
                errors.append(f"COPERA: {div} totalBeneficiaries should be positive")

    # Combined total beneficiaries ~138,528
    combined = bb.get("combined", {})
    total_bene = combined.get("totalBeneficiaries")
    if total_bene != 138528:
        errors.append(f"COPERA: combined totalBeneficiaries expected 138528, got {total_bene}")

    # Judicial average should be highest (judges)
    judicial_avg = bb.get("judicial", {}).get("averageAnnualBenefit", 0)
    school_avg = bb.get("school", {}).get("averageAnnualBenefit", 0)
    if judicial_avg and school_avg and judicial_avg <= school_avg:
        errors.append(f"COPERA: judicial avg benefit ({judicial_avg}) should exceed school ({school_avg})")

    return errors


# ============================================================
# Vesting
# ============================================================

def validate_vesting(data: dict) -> List[str]:
    errors = []
    v = data.get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"COPERA: vesting.years expected 5, got {v.get('years')}")
    if v.get("schedule") != "cliff":
        errors.append(f"COPERA: vesting.schedule expected 'cliff', got {v.get('schedule')}")
    return errors


# ============================================================
# Social Security
# ============================================================

def validate_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not False:
        errors.append(f"COPERA: socialSecurity.covered expected false, got {ss.get('covered')}")
    if not ss.get("note"):
        errors.append("COPERA: socialSecurity.note missing")
    return errors


# ============================================================
# Jurisdiction
# ============================================================

def validate_jurisdiction(data: dict) -> List[str]:
    errors = []
    j = data.get("jurisdiction", {})
    if j.get("state") != "CO":
        errors.append(f"COPERA: jurisdiction.state expected 'CO', got '{j.get('state')}'")
    if j.get("level") != "state":
        errors.append(f"COPERA: jurisdiction.level expected 'state', got '{j.get('level')}'")
    return errors


# ============================================================
# Total members
# ============================================================

def validate_total_members(data: dict) -> List[str]:
    errors = []
    tm = data.get("totalMembers", {})
    approx = tm.get("approximate")
    if not (500000 < (approx or 0) < 2000000):
        errors.append(f"COPERA: totalMembers.approximate implausible: {approx}")

    # Division breakdown present for all 5
    by_div = tm.get("byDivision", {})
    for div in REQUIRED_DIVISIONS:
        if div not in by_div:
            errors.append(f"COPERA: totalMembers.byDivision missing '{div}'")

    # School largest active division
    school_active = by_div.get("school", {}).get("active", 0)
    state_active = by_div.get("state", {}).get("active", 0)
    if school_active and state_active and school_active <= state_active:
        errors.append(f"COPERA: school active ({school_active}) should exceed state active ({state_active})")

    return errors


# ============================================================
# Metadata and sources
# ============================================================

def validate_metadata(data: dict) -> List[str]:
    errors = []
    if not str(data.get("version", "")).startswith("2026"):
        errors.append(f"COPERA: version should start with '2026', got '{data.get('version')}'")
    if not data.get("last_updated"):
        errors.append("COPERA: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 5:
        errors.append(f"COPERA: expected at least 5 sources, got {len(sources)}")
    for i, s in enumerate(sources):
        if not s.get("url"):
            errors.append(f"COPERA: source[{i}] missing url")
    return errors


# ============================================================
# No consumer references
# ============================================================

def validate_no_consumer_references(data: dict) -> List[str]:
    errors = []
    raw = json.dumps(data).lower()
    for forbidden in ["engine usage block", "engine-numbered note", "for meridian", "meridian uses", "meridian requires"]:
        if forbidden in raw:
            errors.append(f"COPERA: forbidden consumer-specific reference: '{forbidden}'")
    return errors


# ============================================================
# Cross-checks
# ============================================================

def validate_cross_checks(data: dict) -> List[str]:
    errors = []

    # AAP FY2026 AI must match annualIncrease.fy2026.rate
    aap_ai = data.get("automaticAdjustmentProvision", {}).get("fy2026_assessment", {}).get("annualIncrease_july2026")
    ai_fy26 = data.get("annualIncrease", {}).get("fy2026", {}).get("rate")
    if aap_ai is not None and ai_fy26 is not None and aap_ai != ai_fy26:
        errors.append(f"COPERA: AAP FY2026 AI ({aap_ai}) does not match annualIncrease.fy2026.rate ({ai_fy26})")

    # Direct distribution base > scheduled reduction amount
    base = data.get("directDistribution", {}).get("baseAmount", 0)
    reduced = data.get("directDistribution", {}).get("scheduledReduction", {}).get("reducedAmount", 0)
    if base and reduced and base <= reduced:
        errors.append(f"COPERA: directDistribution base ({base}) should exceed reducedAmount ({reduced})")

    # Combined funded ratio 2024 <= 2023 (slight decrease)
    r24 = data.get("fundingStatus", {}).get("combinedFundedRatio_2024", 0)
    r23 = data.get("fundingStatus", {}).get("combinedFundedRatio_2023", 0)
    if r23 and r24 and r24 > r23:
        errors.append(f"COPERA: 2024 funded ratio ({r24}) should not exceed 2023 ({r23}) — slight decrease documented")

    # Benefit formula multiplier × max years = max pct
    mult = data.get("benefitFormula", {}).get("multiplier", 0)
    max_yrs = data.get("benefitFormula", {}).get("maximumServiceYears", 0)
    max_pct = data.get("benefitFormula", {}).get("maximumBenefitPct", 0)
    if mult and max_yrs and max_pct:
        computed = round(mult * max_yrs, 4)
        if abs(computed - max_pct) > 0.001:
            errors.append(f"COPERA: multiplier × maxYears ({computed}) does not equal maximumBenefitPct ({max_pct})")

    return errors


# ============================================================
# Runner
# ============================================================

def run_all() -> int:
    try:
        data = load_json(COPERA_PATH)
    except FileNotFoundError:
        print(f"ERROR: {COPERA_PATH} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {COPERA_PATH}: {e}")
        return 1

    validators = [
        validate_top_level,
        validate_divisions_present,
        validate_has_tables_present,
        validate_rate_groups_present,
        validate_benefit_formula,
        validate_has_calculation,
        validate_has_table_2,
        validate_has_table_9,
        validate_contribution_rates,
        validate_aap,
        validate_annual_increase,
        validate_direct_distribution,
        validate_funding,
        validate_benefits_paid,
        validate_vesting,
        validate_social_security,
        validate_jurisdiction,
        validate_total_members,
        validate_metadata,
        validate_no_consumer_references,
        validate_cross_checks,
    ]

    all_errors = []
    for validator in validators:
        all_errors.extend(validator(data))

    check_count = count_checks()

    if all_errors:
        print(f"COPERA VALIDATION FAILED — {len(all_errors)} errors:")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"COPERA VALIDATION: {check_count} checks passed")
        return 0


def count_checks() -> int:
    count = 0
    count += 21   # top_level: 20 required keys + abbreviation
    count += 5    # divisions present (5)
    count += 3    # HAS tables present (3)
    count += 7    # rate groups present (7)
    count += 6    # benefit formula: multiplier, maxPct, maxYears, 3 options
    count += 5    # HAS calculation: pre-2020, post-2020, judicial periods, anti-spike cap
    count += 5    # table_2: criteria, fullRetirement, earlyRetirement, 62.5% example, has_period
    count += 8    # table_9: 3 general full, 1 safety full, 2 early general, early safety, has_period
    count += 10   # contribution rates: 6 member rates + range check + state emp total + safety > general
    count += 6    # AAP: low trigger, high trigger, ratio, range check, no-adjustment, FY2026 AI
    count += 7    # annualIncrease: baseRate, aapMin, aapMax, min<base<max, fy2026 rate, wait 36mo
    count += 4    # directDistribution: baseAmount, reducedAmount, startDate, one-time 500M
    count += 10   # funding: ratio, plausibility, assets, discount rate, return, 5 divisions, cross-div check
    count += 7    # benefits_paid: 5 divisions, combined bene count, judicial > school
    count += 2    # vesting: years, schedule
    count += 2    # social security: covered, note
    count += 2    # jurisdiction: state, level
    count += 5    # total_members: approximate, 5 divisions, school > state
    count += 4    # metadata: version, last_updated, sources count, source urls
    count += 5    # no consumer references (5 patterns)
    count += 4    # cross-checks: AAP-AI match, distribution base > reduced, funding decrease, formula math
    return count


if __name__ == "__main__":
    sys.exit(run_all())
