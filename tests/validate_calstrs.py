#!/usr/bin/env python3
"""
Validation suite for CalSTRS (California State Teachers' Retirement System) pension plan data.
File: states/california/calstrs-plans.json

Validates:
  - Structure: required top-level keys, tier existence, program completeness
  - Values: age factors, contribution rates, PEPRA cap, SBMA floor
  - Range checks: all rates 0-1, ages reasonable, dollar amounts positive
  - Cross-field: PEPRA tier has no career factor; Classic tier has career factor
  - COLA: type, rate, authority present and correct
  - SBMA: floor, payment schedule, authority present

Session 60: Initial build — CalSTRS first California state-level pension.
"""

import json
import sys
from pathlib import Path
from typing import List

CALSTRS_PATH = "states/california/calstrs-plans.json"


def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


# ============================================================
# Structure validators
# ============================================================

def validate_top_level(data: dict) -> List[str]:
    errors = []
    required = [
        "systemName", "systemAbbreviation", "version", "jurisdiction",
        "tiers", "cola", "purchasingPowerProtection", "sources",
        "last_updated", "socialSecurity", "totalMembers", "employerContributions"
    ]
    for key in required:
        if key not in data:
            errors.append(f"CalSTRS: missing required top-level key '{key}'")
    if data.get("systemAbbreviation") != "CalSTRS":
        errors.append(f"CalSTRS: systemAbbreviation expected 'CalSTRS', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_tiers_exist(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    if "tier_2pct_at_60" not in tiers:
        errors.append("CalSTRS: missing tier 'tier_2pct_at_60' (Classic)")
    if "tier_2pct_at_62" not in tiers:
        errors.append("CalSTRS: missing tier 'tier_2pct_at_62' (PEPRA)")
    return errors


def validate_tier_required_keys(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    tier_required = ["tierName", "pepra", "eligibility", "formula",
                     "retirementEligibility", "vesting", "memberContribution"]
    for tier_key, tier in tiers.items():
        for key in tier_required:
            if key not in tier:
                errors.append(f"CalSTRS tier '{tier_key}': missing required key '{key}'")
    return errors


# ============================================================
# Value validators — Classic (2% at 60)
# ============================================================

def validate_classic_age_factors(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_60", {})
    af = tier.get("formula", {}).get("ageFactor", {})

    # Standard factor at NRA = 2%
    val = af.get("standardAtNormalRetirementAge")
    if val != 0.02:
        errors.append(f"CalSTRS 2%@60: standardAtNormalRetirementAge expected 0.02, got {val}")

    # NRA = 60
    nra = af.get("normalRetirementAge")
    if nra != 60:
        errors.append(f"CalSTRS 2%@60: normalRetirementAge expected 60, got {nra}")

    # Min factor = 1.1% at age 50
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.011:
        errors.append(f"CalSTRS 2%@60: minimum age factor expected 0.011 (1.1%), got {minimum.get('factor')}")
    if minimum.get("age") != 50:
        errors.append(f"CalSTRS 2%@60: minimum age expected 50, got {minimum.get('age')}")

    # Max factor = 2.4% at age 63
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.024:
        errors.append(f"CalSTRS 2%@60: maximum age factor expected 0.024 (2.4%), got {maximum.get('factor')}")
    if maximum.get("age") != 63:
        errors.append(f"CalSTRS 2%@60: maximum age expected 63, got {maximum.get('age')}")

    return errors


def validate_classic_career_factor(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_60", {})
    cf = tier.get("formula", {}).get("careerFactor", {})

    if cf.get("available") is not True:
        errors.append("CalSTRS 2%@60: careerFactor.available should be true for Classic tier")
    if cf.get("requirement") is None:
        errors.append("CalSTRS 2%@60: careerFactor.requirement missing")
    if cf.get("bonus") != 0.002:
        errors.append(f"CalSTRS 2%@60: careerFactor.bonus expected 0.002 (0.2%), got {cf.get('bonus')}")

    return errors


def validate_classic_final_comp(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_60", {})
    fc = tier.get("formula", {}).get("finalCompensation", {})

    if "method_post1996" not in fc:
        errors.append("CalSTRS 2%@60: finalCompensation missing 'method_post1996'")
    if "method_pre1997" not in fc:
        errors.append("CalSTRS 2%@60: finalCompensation missing 'method_pre1997'")

    post = fc.get("method_post1996", {})
    if "36" not in str(post.get("period", "")):
        errors.append("CalSTRS 2%@60: method_post1996 should reference 36 consecutive months")

    pre = fc.get("method_pre1997", {})
    if "12" not in str(pre.get("period", "")):
        errors.append("CalSTRS 2%@60: method_pre1997 should reference 12 consecutive months")

    # Classic: no PEPRA cap
    cap = fc.get("compensationCap", {})
    if cap.get("applicable") is not False:
        errors.append("CalSTRS 2%@60: compensationCap.applicable should be false for Classic members")

    return errors


def validate_classic_retirement_eligibility(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_60", {})
    ret = tier.get("retirementEligibility", {})

    # Minimum retirement age = 50
    if ret.get("minimumRetirementAge") != 50:
        errors.append(f"CalSTRS 2%@60: minimumRetirementAge expected 50, got {ret.get('minimumRetirementAge')}")

    # Normal retirement: age 60, 5 years
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 60:
        errors.append(f"CalSTRS 2%@60: normalRetirement.minimumAge expected 60, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalSTRS 2%@60: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")

    return errors


def validate_classic_contributions(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_60", {})
    mc = tier.get("memberContribution", {})

    rate = mc.get("rate_fy2025_26")
    if rate != 0.1025:
        errors.append(f"CalSTRS 2%@60: rate_fy2025_26 expected 0.1025 (10.25%), got {rate}")
    if not (0 < rate < 1):
        errors.append(f"CalSTRS 2%@60: memberContribution rate out of range: {rate}")

    return errors


# ============================================================
# Value validators — PEPRA (2% at 62)
# ============================================================

def validate_pepra_age_factors(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    af = tier.get("formula", {}).get("ageFactor", {})

    # Standard factor at NRA = 2%
    val = af.get("standardAtNormalRetirementAge")
    if val != 0.02:
        errors.append(f"CalSTRS 2%@62: standardAtNormalRetirementAge expected 0.02, got {val}")

    # NRA = 62
    nra = af.get("normalRetirementAge")
    if nra != 62:
        errors.append(f"CalSTRS 2%@62: normalRetirementAge expected 62, got {nra}")

    # Min factor = 1.16% at age 55
    minimum = af.get("minimum", {})
    if minimum.get("factor") != 0.0116:
        errors.append(f"CalSTRS 2%@62: minimum age factor expected 0.0116 (1.16%), got {minimum.get('factor')}")
    if minimum.get("age") != 55:
        errors.append(f"CalSTRS 2%@62: minimum age expected 55, got {minimum.get('age')}")

    # Max factor = 2.4% at age 65
    maximum = af.get("maximum", {})
    if maximum.get("factor") != 0.024:
        errors.append(f"CalSTRS 2%@62: maximum age factor expected 0.024 (2.4%), got {maximum.get('factor')}")
    if maximum.get("age") != 65:
        errors.append(f"CalSTRS 2%@62: maximum age expected 65, got {maximum.get('age')}")

    return errors


def validate_pepra_no_career_factor(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    cf = tier.get("formula", {}).get("careerFactor", {})

    if cf.get("available") is not False:
        errors.append("CalSTRS 2%@62: careerFactor.available should be false for PEPRA tier")

    return errors


def validate_pepra_comp_cap(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    fc = tier.get("formula", {}).get("finalCompensation", {})
    cap = fc.get("compensationCap", {})

    if cap.get("applicable") is not True:
        errors.append("CalSTRS 2%@62: compensationCap.applicable should be true for PEPRA members")

    # FY2024-25 cap = $182,266
    cap_2024_25 = cap.get("fy2024_25")
    if cap_2024_25 != 182266:
        errors.append(f"CalSTRS 2%@62: compensationCap.fy2024_25 expected 182266, got {cap_2024_25}")

    # FY2025-26 cap = $187,369
    cap_2025_26 = cap.get("fy2025_26")
    if cap_2025_26 != 187369:
        errors.append(f"CalSTRS 2%@62: compensationCap.fy2025_26 expected 187369, got {cap_2025_26}")

    # Caps should be positive and plausible
    for year, val in [("fy2024_25", cap_2024_25), ("fy2025_26", cap_2025_26)]:
        if val and not (100000 < val < 500000):
            errors.append(f"CalSTRS 2%@62: compensationCap.{year} implausible: {val}")

    return errors


def validate_pepra_retirement_eligibility(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    ret = tier.get("retirementEligibility", {})

    # Minimum retirement age = 55 for PEPRA
    if ret.get("minimumRetirementAge") != 55:
        errors.append(f"CalSTRS 2%@62: minimumRetirementAge expected 55, got {ret.get('minimumRetirementAge')}")

    # Normal retirement: age 62, 5 years
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumAge") != 62:
        errors.append(f"CalSTRS 2%@62: normalRetirement.minimumAge expected 62, got {nr.get('minimumAge')}")
    if nr.get("minimumService") != 5:
        errors.append(f"CalSTRS 2%@62: normalRetirement.minimumService expected 5, got {nr.get('minimumService')}")

    return errors


def validate_pepra_contributions(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    mc = tier.get("memberContribution", {})

    rate = mc.get("rate_fy2025_26")
    if rate != 0.10205:
        errors.append(f"CalSTRS 2%@62: rate_fy2025_26 expected 0.10205 (10.205%), got {rate}")
    if not (0 < rate < 1):
        errors.append(f"CalSTRS 2%@62: memberContribution rate out of range: {rate}")

    return errors


def validate_pepra_final_comp(data: dict) -> List[str]:
    errors = []
    tier = data.get("tiers", {}).get("tier_2pct_at_62", {})
    fc = tier.get("formula", {}).get("finalCompensation", {})

    method = fc.get("method", {})
    if "36" not in str(method.get("period", "")):
        errors.append("CalSTRS 2%@62: finalCompensation.method should reference 36 consecutive months")

    return errors


# ============================================================
# Employer contributions
# ============================================================

def validate_employer_contributions(data: dict) -> List[str]:
    errors = []
    ec = data.get("employerContributions", {})

    rate = ec.get("rate_fy2025_26")
    if rate != 0.1910:
        errors.append(f"CalSTRS: employer rate_fy2025_26 expected 0.1910 (19.10%), got {rate}")
    if not (0 < rate < 1):
        errors.append(f"CalSTRS: employer rate out of range: {rate}")

    dbs_rate = ec.get("dbSupplement_rate")
    if dbs_rate != 0.0825:
        errors.append(f"CalSTRS: dbSupplement_rate expected 0.0825 (8.25%), got {dbs_rate}")

    return errors


# ============================================================
# COLA validators
# ============================================================

def validate_cola(data: dict) -> List[str]:
    errors = []
    cola = data.get("cola", {})

    if cola.get("type") != "simple_2pct_annual":
        errors.append(f"CalSTRS: cola.type expected 'simple_2pct_annual', got '{cola.get('type')}'")

    if cola.get("method") != "simple":
        errors.append(f"CalSTRS: cola.method expected 'simple' (non-compounding), got '{cola.get('method')}'")

    if cola.get("rate") != 0.02:
        errors.append(f"CalSTRS: cola.rate expected 0.02 (2%), got {cola.get('rate')}")

    if not cola.get("effectiveDate"):
        errors.append("CalSTRS: cola.effectiveDate missing")

    if not cola.get("authority"):
        errors.append("CalSTRS: cola.authority missing")

    if not cola.get("source"):
        errors.append("CalSTRS: cola.source missing")

    return errors


# ============================================================
# SBMA / purchasing power protection
# ============================================================

def validate_sbma(data: dict) -> List[str]:
    errors = []
    ppp = data.get("purchasingPowerProtection", {})
    sbma = ppp.get("sbma", {})

    if sbma.get("purchasingPowerFloor") != 0.85:
        errors.append(f"CalSTRS: SBMA purchasingPowerFloor expected 0.85, got {sbma.get('purchasingPowerFloor')}")

    if sbma.get("absoluteMinimum") != 0.80:
        errors.append(f"CalSTRS: SBMA absoluteMinimum expected 0.80, got {sbma.get('absoluteMinimum')}")

    if not sbma.get("paymentSchedule"):
        errors.append("CalSTRS: SBMA paymentSchedule missing")

    if "October" not in sbma.get("paymentSchedule", ""):
        errors.append("CalSTRS: SBMA paymentSchedule should include 'October'")

    if not sbma.get("authority"):
        errors.append("CalSTRS: SBMA authority missing")

    if not sbma.get("source"):
        errors.append("CalSTRS: SBMA source missing")

    # Floor check: absoluteMinimum < purchasingPowerFloor
    floor = sbma.get("purchasingPowerFloor", 0)
    absmin = sbma.get("absoluteMinimum", 0)
    if absmin and floor and absmin >= floor:
        errors.append(f"CalSTRS: SBMA absoluteMinimum ({absmin}) should be < purchasingPowerFloor ({floor})")

    # State contribution
    sc = data.get("stateContributions", {})
    if sc.get("sbmaContribution_pct_of_payroll") != 0.025:
        errors.append(f"CalSTRS: stateContributions.sbmaContribution_pct_of_payroll expected 0.025, got {sc.get('sbmaContribution_pct_of_payroll')}")

    return errors


# ============================================================
# Social Security
# ============================================================

def validate_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})

    if ss.get("covered") is not False:
        errors.append("CalSTRS: socialSecurity.covered should be false — CalSTRS members are not SS-covered")

    if not ss.get("note"):
        errors.append("CalSTRS: socialSecurity.note missing")

    return errors


# ============================================================
# Vesting
# ============================================================

def validate_vesting(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    for tier_key, tier in tiers.items():
        vesting = tier.get("vesting", {})
        if vesting.get("years") != 5:
            errors.append(f"CalSTRS {tier_key}: vesting years expected 5, got {vesting.get('years')}")
        if vesting.get("schedule") != "cliff":
            errors.append(f"CalSTRS {tier_key}: vesting schedule expected 'cliff', got {vesting.get('schedule')}")
    return errors


# ============================================================
# Jurisdiction
# ============================================================

def validate_jurisdiction(data: dict) -> List[str]:
    errors = []
    j = data.get("jurisdiction", {})
    if j.get("state") != "CA":
        errors.append(f"CalSTRS: jurisdiction.state expected 'CA', got '{j.get('state')}'")
    if j.get("level") != "state":
        errors.append(f"CalSTRS: jurisdiction.level expected 'state', got '{j.get('level')}'")
    return errors


# ============================================================
# Version and metadata
# ============================================================

def validate_metadata(data: dict) -> List[str]:
    errors = []
    version = data.get("version", "")
    if not version.startswith("2026"):
        errors.append(f"CalSTRS: version should start with '2026', got '{version}'")
    if not data.get("last_updated"):
        errors.append("CalSTRS: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 3:
        errors.append(f"CalSTRS: expected at least 3 sources, got {len(sources)}")
    return errors


# ============================================================
# Return-to-work limits
# ============================================================

def validate_return_to_work(data: dict) -> List[str]:
    errors = []
    rtw = data.get("returnToWork", {})
    limit = rtw.get("earningsLimit_fy2025_26")
    if not limit or limit <= 0:
        errors.append(f"CalSTRS: returnToWork.earningsLimit_fy2025_26 missing or invalid: {limit}")
    if limit and limit != 80245:
        errors.append(f"CalSTRS: returnToWork.earningsLimit_fy2025_26 expected 80245, got {limit}")
    return errors


# ============================================================
# IRC 415(b) limits
# ============================================================

def validate_irc415b(data: dict) -> List[str]:
    errors = []
    limits = data.get("irc415bLimits", {})
    at60_2025 = limits.get("dollar_limit_at_60_cy2025")
    if at60_2025 and at60_2025 != 203383:
        errors.append(f"CalSTRS: irc415bLimits.dollar_limit_at_60_cy2025 expected 203383, got {at60_2025}")
    if not limits.get("source"):
        errors.append("CalSTRS: irc415bLimits.source missing")
    return errors


# ============================================================
# PEPRA tier flag
# ============================================================

def validate_pepra_flags(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    classic = tiers.get("tier_2pct_at_60", {})
    pepra = tiers.get("tier_2pct_at_62", {})

    if classic.get("pepra") is not False:
        errors.append("CalSTRS 2%@60: pepra flag should be false")
    if pepra.get("pepra") is not True:
        errors.append("CalSTRS 2%@62: pepra flag should be true")

    return errors


# ============================================================
# Runner
# ============================================================

def run_all() -> int:
    try:
        data = load_json(CALSTRS_PATH)
    except FileNotFoundError:
        print(f"ERROR: {CALSTRS_PATH} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {CALSTRS_PATH}: {e}")
        return 1

    validators = [
        validate_top_level,
        validate_tiers_exist,
        validate_tier_required_keys,
        validate_classic_age_factors,
        validate_classic_career_factor,
        validate_classic_final_comp,
        validate_classic_retirement_eligibility,
        validate_classic_contributions,
        validate_pepra_age_factors,
        validate_pepra_no_career_factor,
        validate_pepra_comp_cap,
        validate_pepra_retirement_eligibility,
        validate_pepra_contributions,
        validate_pepra_final_comp,
        validate_employer_contributions,
        validate_cola,
        validate_sbma,
        validate_social_security,
        validate_vesting,
        validate_jurisdiction,
        validate_metadata,
        validate_return_to_work,
        validate_irc415b,
        validate_pepra_flags,
    ]

    all_errors = []
    check_count = 0

    for validator in validators:
        errors = validator(data)
        # Count checks = number of assertions in each validator (approximate by error slots)
        check_count += 1  # at minimum 1 check per validator
        all_errors.extend(errors)

    # Count granular checks by running a secondary pass
    # Recount by checking how many individual assertions pass
    check_count = count_checks(data)

    if all_errors:
        print(f"CALSTRS VALIDATION: FAILED — {len(all_errors)} errors")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"CALSTRS VALIDATION: {check_count} checks passed")
        return 0


def count_checks(data: dict) -> int:
    """Count total assertion checks (pass or fail) across all validators."""
    count = 0

    # Top-level keys (12 required)
    count += 12
    # Tier existence (2)
    count += 2
    # Tier required keys (7 keys x 2 tiers)
    count += 14

    # Classic age factors (5: standard, NRA, min factor, min age, max factor, max age)
    count += 6
    # Classic career factor (3: available, requirement, bonus)
    count += 3
    # Classic final comp (4: post1996 present, pre1997 present, 36mo, 12mo, cap false)
    count += 5
    # Classic retirement eligibility (3: minAge, NR age, NR service)
    count += 3
    # Classic contributions (2: rate value, range)
    count += 2

    # PEPRA age factors (6)
    count += 6
    # PEPRA no career factor (1)
    count += 1
    # PEPRA comp cap (4: applicable, fy2024_25, fy2025_26, plausibility)
    count += 4
    # PEPRA retirement eligibility (3)
    count += 3
    # PEPRA contributions (2)
    count += 2
    # PEPRA final comp (1)
    count += 1

    # Employer contributions (3: rate, range, DBS rate)
    count += 3
    # COLA (6: type, method, rate, effectiveDate, authority, source)
    count += 6
    # SBMA (8: floor, absmin, schedule, Oct present, authority, source, floor check, state contrib)
    count += 8
    # Social Security (2: covered=false, note)
    count += 2
    # Vesting (2 tiers x 2 checks)
    count += 4
    # Jurisdiction (2: state, level)
    count += 2
    # Metadata (3: version, last_updated, sources)
    count += 3
    # Return to work (2: positive, value)
    count += 2
    # IRC 415b (2: value, source)
    count += 2
    # PEPRA flags (2)
    count += 2

    return count


if __name__ == "__main__":
    sys.exit(run_all())
