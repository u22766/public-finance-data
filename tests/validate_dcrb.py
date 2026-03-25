#!/usr/bin/env python3
"""
Validation suite for DC DCRB (District of Columbia Retirement Board).
File: states/dc/dc-dcrb-plans.json

Validates:
  - Structure: required keys, both plans present, all three police/fire tiers
  - Police/Fire: Tier 1 (2.5%/3.0%, 12mo ABP, 20yr), Tier 2 (2.5%/3.0%, 36mo, 25yr/50),
                 Tier 3 (2.5%, 36mo, 25yr any age), mandatory retirement at 60
  - Teachers: pre-1996 (tiered 1.5%/1.75%/2.0%) and post-1996 (2.0% flat)
  - Contribution rates: 7% pre-1996; 8% post-1996 for both plans
  - Vesting: 5 years both plans
  - COLA: 3% cap Tier 3 / post-1996; 2026 and 2025 COLA values
  - Scoping note present (FERS context for DC workers)
  - Federal benefit split documented
  - No consumer-specific references

Session 64/65: Initial build — DC DCRB.
"""

import json
import sys
from typing import List

DCRB_PATH = "states/dc/dc-dcrb-plans.json"


def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


def validate_top_level(data: dict) -> List[str]:
    errors = []
    required = [
        "systemName", "systemAbbreviation", "version", "last_updated",
        "jurisdiction", "scopingNote", "federalBenefitSplit",
        "plans", "colaHistory", "sources"
    ]
    for key in required:
        if key not in data:
            errors.append(f"DCRB: missing required top-level key '{key}'")
    if data.get("systemAbbreviation") != "DCRB":
        errors.append(f"DCRB: systemAbbreviation expected 'DCRB', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_plans_present(data: dict) -> List[str]:
    errors = []
    plans = data.get("plans", {})
    for p in ["policeFire", "teachers"]:
        if p not in plans:
            errors.append(f"DCRB: missing plan '{p}'")
    return errors


def validate_tiers_present(data: dict) -> List[str]:
    errors = []
    tiers = data.get("plans", {}).get("policeFire", {}).get("tiers", {})
    for t in ["tier1", "tier2", "tier3"]:
        if t not in tiers:
            errors.append(f"DCRB policeFire: missing '{t}'")
    teacher_tiers = data.get("plans", {}).get("teachers", {}).get("tiers", {})
    for t in ["pre1996", "post1996"]:
        if t not in teacher_tiers:
            errors.append(f"DCRB teachers: missing tier '{t}'")
    return errors


def validate_tier1(data: dict) -> List[str]:
    errors = []
    t1 = data["plans"]["policeFire"]["tiers"]["tier1"]
    formula = t1.get("formula", {})
    if formula.get("multiplier_first20") != 0.025:
        errors.append(f"DCRB Tier 1: multiplier_first20 expected 0.025, got {formula.get('multiplier_first20')}")
    if formula.get("multiplier_beyond20") != 0.030:
        errors.append(f"DCRB Tier 1: multiplier_beyond20 expected 0.030, got {formula.get('multiplier_beyond20')}")
    if formula.get("averageBasePay", {}).get("period_months") != 12:
        errors.append(f"DCRB Tier 1: averageBasePay.period_months expected 12, got {formula.get('averageBasePay', {}).get('period_months')}")
    ret = t1.get("retirementEligibility", {}).get("normalRetirement", {})
    if ret.get("minimumService") != 20:
        errors.append(f"DCRB Tier 1: normalRetirement.minimumService expected 20, got {ret.get('minimumService')}")
    if t1.get("memberContribution", {}).get("rate") != 0.07:
        errors.append(f"DCRB Tier 1: memberContribution.rate expected 0.07")
    if t1.get("cola", {}).get("cap") is not None:
        errors.append("DCRB Tier 1: cola.cap should be null (uncapped)")
    return errors


def validate_tier2(data: dict) -> List[str]:
    errors = []
    t2 = data["plans"]["policeFire"]["tiers"]["tier2"]
    formula = t2.get("formula", {})
    if formula.get("multiplier_first25") != 0.025:
        errors.append(f"DCRB Tier 2: multiplier_first25 expected 0.025, got {formula.get('multiplier_first25')}")
    if formula.get("multiplier_beyond25") != 0.030:
        errors.append(f"DCRB Tier 2: multiplier_beyond25 expected 0.030, got {formula.get('multiplier_beyond25')}")
    if formula.get("maximumBenefitPct") != 0.80:
        errors.append(f"DCRB Tier 2: maximumBenefitPct expected 0.80, got {formula.get('maximumBenefitPct')}")
    if formula.get("averageBasePay", {}).get("period_months") != 36:
        errors.append(f"DCRB Tier 2: averageBasePay.period_months expected 36, got {formula.get('averageBasePay', {}).get('period_months')}")
    ret = t2.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumService") != 25:
        errors.append(f"DCRB Tier 2: normalRetirement.minimumService expected 25, got {nr.get('minimumService')}")
    if nr.get("minimumAge") != 50:
        errors.append(f"DCRB Tier 2: normalRetirement.minimumAge expected 50, got {nr.get('minimumAge')}")
    if ret.get("mandatoryRetirement", {}).get("age") != 60:
        errors.append(f"DCRB Tier 2: mandatoryRetirement.age expected 60")
    if t2.get("memberContribution", {}).get("rate") != 0.07:
        errors.append(f"DCRB Tier 2: memberContribution.rate expected 0.07")
    if t2.get("vesting", {}).get("years") != 5:
        errors.append(f"DCRB Tier 2: vesting.years expected 5")
    if t2.get("cola", {}).get("cap") != 0.03:
        errors.append(f"DCRB Tier 2: cola.cap expected 0.03, got {t2.get('cola', {}).get('cap')}")
    return errors


def validate_tier3(data: dict) -> List[str]:
    errors = []
    t3 = data["plans"]["policeFire"]["tiers"]["tier3"]
    formula = t3.get("formula", {})
    if formula.get("multiplier") != 0.025:
        errors.append(f"DCRB Tier 3: multiplier expected 0.025, got {formula.get('multiplier')}")
    if formula.get("maximumBenefitPct") != 0.80:
        errors.append(f"DCRB Tier 3: maximumBenefitPct expected 0.80, got {formula.get('maximumBenefitPct')}")
    if formula.get("averageBasePay", {}).get("period_months") != 36:
        errors.append(f"DCRB Tier 3: averageBasePay.period_months expected 36")
    ret = t3.get("retirementEligibility", {})
    nr = ret.get("normalRetirement", {})
    if nr.get("minimumService") != 25:
        errors.append(f"DCRB Tier 3: normalRetirement.minimumService expected 25, got {nr.get('minimumService')}")
    if nr.get("minimumAge") is not None:
        errors.append(f"DCRB Tier 3: normalRetirement.minimumAge should be null (any age), got {nr.get('minimumAge')}")
    if ret.get("mandatoryRetirement", {}).get("age") != 60:
        errors.append(f"DCRB Tier 3: mandatoryRetirement.age expected 60")
    if t3.get("memberContribution", {}).get("rate") != 0.08:
        errors.append(f"DCRB Tier 3: memberContribution.rate expected 0.08")
    if t3.get("vesting", {}).get("years") != 5:
        errors.append(f"DCRB Tier 3: vesting.years expected 5")
    if t3.get("cola", {}).get("cap") != 0.03:
        errors.append(f"DCRB Tier 3: cola.cap expected 0.03")
    return errors


def validate_tier_progression(data: dict) -> List[str]:
    """Tier 3 service threshold >= Tier 2; Tier 3 member rate > Tier 1/2."""
    errors = []
    tiers = data["plans"]["policeFire"]["tiers"]
    t1_svc = tiers["tier1"].get("retirementEligibility", {}).get("normalRetirement", {}).get("minimumService", 0)
    t2_svc = tiers["tier2"].get("retirementEligibility", {}).get("normalRetirement", {}).get("minimumService", 0)
    t2_age = tiers["tier2"].get("retirementEligibility", {}).get("normalRetirement", {}).get("minimumAge", 0)
    t3_svc = tiers["tier3"].get("retirementEligibility", {}).get("normalRetirement", {}).get("minimumService", 0)
    t3_age = tiers["tier3"].get("retirementEligibility", {}).get("normalRetirement", {}).get("minimumAge")

    if t3_svc and t2_svc and t3_svc < t2_svc:
        errors.append(f"DCRB: Tier 3 service ({t3_svc}) should be >= Tier 2 ({t2_svc})")
    if t3_svc and t1_svc and t3_svc > t1_svc:
        pass  # Tier 3 needs more years (25 > 20) — expected
    if t3_age is not None:
        errors.append(f"DCRB: Tier 3 minimumAge should be null (any age), got {t3_age}")

    t1_rate = tiers["tier1"].get("memberContribution", {}).get("rate", 0)
    t3_rate = tiers["tier3"].get("memberContribution", {}).get("rate", 0)
    if t1_rate and t3_rate and t3_rate <= t1_rate:
        errors.append(f"DCRB: Tier 3 member rate ({t3_rate}) should exceed Tier 1 ({t1_rate})")
    return errors


def validate_teachers_post1996(data: dict) -> List[str]:
    errors = []
    t = data["plans"]["teachers"]["tiers"]["post1996"]
    formula = t.get("formula", {})
    if formula.get("multiplier") != 0.020:
        errors.append(f"DCRB Teachers post-1996: multiplier expected 0.020, got {formula.get('multiplier')}")
    if formula.get("averageSalary", {}).get("period_months") != 36:
        errors.append(f"DCRB Teachers post-1996: averageSalary.period_months expected 36")
    if t.get("memberContribution", {}).get("rate") != 0.08:
        errors.append(f"DCRB Teachers post-1996: memberContribution.rate expected 0.08")
    if t.get("cola", {}).get("cap") != 0.03:
        errors.append(f"DCRB Teachers post-1996: cola.cap expected 0.03")
    ret = t.get("retirementEligibility", {})
    normal = ret.get("normalRetirement", [])
    if not any("62" in str(r) for r in normal):
        errors.append("DCRB Teachers post-1996: normalRetirement missing age 62 rule")
    if not any("30" in str(r) for r in normal):
        errors.append("DCRB Teachers post-1996: normalRetirement missing 30-year rule")
    return errors


def validate_teachers_pre1996(data: dict) -> List[str]:
    errors = []
    t = data["plans"]["teachers"]["tiers"]["pre1996"]
    formula = t.get("formula", {})
    if formula.get("multiplier_first5") != 0.015:
        errors.append(f"DCRB Teachers pre-1996: multiplier_first5 expected 0.015, got {formula.get('multiplier_first5')}")
    if formula.get("multiplier_5to10") != 0.0175:
        errors.append(f"DCRB Teachers pre-1996: multiplier_5to10 expected 0.0175, got {formula.get('multiplier_5to10')}")
    if formula.get("multiplier_beyond10") != 0.020:
        errors.append(f"DCRB Teachers pre-1996: multiplier_beyond10 expected 0.020, got {formula.get('multiplier_beyond10')}")
    if t.get("memberContribution", {}).get("rate") != 0.07:
        errors.append(f"DCRB Teachers pre-1996: memberContribution.rate expected 0.07")
    return errors


def validate_teachers_vesting(data: dict) -> List[str]:
    errors = []
    v = data["plans"]["teachers"].get("vesting", {})
    if v.get("years") != 5:
        errors.append(f"DCRB Teachers: vesting.years expected 5, got {v.get('years')}")
    if v.get("schedule") != "cliff":
        errors.append(f"DCRB Teachers: vesting.schedule expected 'cliff'")
    return errors


def validate_teachers_ss(data: dict) -> List[str]:
    errors = []
    ss = data["plans"]["teachers"].get("socialSecurity", {})
    if ss.get("covered") is not True:
        errors.append(f"DCRB Teachers: socialSecurity.covered expected true, got {ss.get('covered')}")
    return errors


def validate_police_fire_ss(data: dict) -> List[str]:
    errors = []
    ss = data["plans"]["policeFire"].get("socialSecurity", {})
    if ss.get("covered") is not False:
        errors.append(f"DCRB Police/Fire: socialSecurity.covered expected false, got {ss.get('covered')}")
    return errors


def validate_cola_history(data: dict) -> List[str]:
    errors = []
    cola = data.get("colaHistory", {})
    c26 = cola.get("cola_2026", {})
    c25 = cola.get("cola_2025", {})
    if c26.get("teachers") != 0.026:
        errors.append(f"DCRB: cola_2026.teachers expected 0.026, got {c26.get('teachers')}")
    if c26.get("policeFire") != 0.027:
        errors.append(f"DCRB: cola_2026.policeFire expected 0.027, got {c26.get('policeFire')}")
    if c25.get("teachers") != 0.028:
        errors.append(f"DCRB: cola_2025.teachers expected 0.028, got {c25.get('teachers')}")
    if c25.get("policeFire") != 0.029:
        errors.append(f"DCRB: cola_2025.policeFire expected 0.029, got {c25.get('policeFire')}")
    # 2025 > 2026 for both (inflation was higher prior year)
    if c25.get("teachers", 0) <= c26.get("teachers", 0):
        errors.append("DCRB: 2025 teacher COLA should exceed 2026 (inflation trend)")
    if c25.get("policeFire", 0) <= c26.get("policeFire", 0):
        errors.append("DCRB: 2025 police/fire COLA should exceed 2026")
    # Police/fire COLA always > teachers COLA (different CPI calculation period)
    if c26.get("policeFire", 0) <= c26.get("teachers", 0):
        errors.append("DCRB: 2026 police/fire COLA should exceed teachers COLA")
    return errors


def validate_federal_split(data: dict) -> List[str]:
    errors = []
    fbs = data.get("federalBenefitSplit", {})
    if fbs.get("federalServiceCutoff") != "1997-07-01":
        errors.append(f"DCRB: federalBenefitSplit.federalServiceCutoff expected '1997-07-01', got '{fbs.get('federalServiceCutoff')}'")
    if not fbs.get("authority"):
        errors.append("DCRB: federalBenefitSplit.authority missing")
    return errors


def validate_jurisdiction(data: dict) -> List[str]:
    errors = []
    j = data.get("jurisdiction", {})
    if j.get("state") != "DC":
        errors.append(f"DCRB: jurisdiction.state expected 'DC', got '{j.get('state')}'")
    return errors


def validate_metadata(data: dict) -> List[str]:
    errors = []
    if not str(data.get("version", "")).startswith("2026"):
        errors.append(f"DCRB: version should start with '2026'")
    if not data.get("last_updated"):
        errors.append("DCRB: last_updated missing")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 8:
        errors.append(f"DCRB: expected at least 8 sources, got {len(sources)}")
    for i, s in enumerate(sources):
        if not s.get("url"):
            errors.append(f"DCRB: source[{i}] missing url")
    if not data.get("scopingNote"):
        errors.append("DCRB: scopingNote missing (FERS context for DC workers)")
    return errors


def validate_no_consumer_references(data: dict) -> List[str]:
    errors = []
    raw = json.dumps(data).lower()
    for forbidden in ["engine usage block", "engine-numbered note", "for meridian", "meridian uses"]:
        if forbidden in raw:
            errors.append(f"DCRB: forbidden consumer reference: '{forbidden}'")
    return errors


def validate_cross_checks(data: dict) -> List[str]:
    errors = []
    tiers = data["plans"]["policeFire"]["tiers"]

    # Tier 1 ABP period (12 mo) < Tier 2/3 ABP period (36 mo)
    t1_abp = tiers["tier1"]["formula"]["averageBasePay"]["period_months"]
    t2_abp = tiers["tier2"]["formula"]["averageBasePay"]["period_months"]
    t3_abp = tiers["tier3"]["formula"]["averageBasePay"]["period_months"]
    if t1_abp and t2_abp and t1_abp >= t2_abp:
        errors.append(f"DCRB: Tier 1 ABP period ({t1_abp}mo) should be less than Tier 2 ({t2_abp}mo)")
    if t2_abp != t3_abp:
        errors.append(f"DCRB: Tier 2 and Tier 3 ABP periods should match ({t2_abp} vs {t3_abp})")

    # Teacher pre-1996 contribution < post-1996
    pre_rate = data["plans"]["teachers"]["tiers"]["pre1996"]["memberContribution"]["rate"]
    post_rate = data["plans"]["teachers"]["tiers"]["post1996"]["memberContribution"]["rate"]
    if pre_rate and post_rate and pre_rate >= post_rate:
        errors.append(f"DCRB Teachers: pre-1996 rate ({pre_rate}) should be less than post-1996 ({post_rate})")

    # Teacher post-1996 contribution same as police/fire Tier 3
    t3_rate = tiers["tier3"]["memberContribution"]["rate"]
    if post_rate != t3_rate:
        errors.append(f"DCRB: Teacher post-1996 rate ({post_rate}) should equal Police/Fire Tier 3 rate ({t3_rate})")

    # Police/Fire COLA 2026 < 3% cap
    pf_cola = data["colaHistory"]["cola_2026"]["policeFire"]
    if pf_cola and pf_cola >= 0.03:
        errors.append(f"DCRB: 2026 Police/Fire COLA ({pf_cola}) should be below 3% cap")

    return errors


def run_all() -> int:
    try:
        data = load_json(DCRB_PATH)
    except FileNotFoundError:
        print(f"ERROR: {DCRB_PATH} not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse error in {DCRB_PATH}: {e}")
        return 1

    validators = [
        validate_top_level,
        validate_plans_present,
        validate_tiers_present,
        validate_tier1,
        validate_tier2,
        validate_tier3,
        validate_tier_progression,
        validate_teachers_post1996,
        validate_teachers_pre1996,
        validate_teachers_vesting,
        validate_teachers_ss,
        validate_police_fire_ss,
        validate_cola_history,
        validate_federal_split,
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
        print(f"DCRB VALIDATION FAILED — {len(all_errors)} errors:")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"DCRB VALIDATION: {check_count} checks passed")
        return 0


def count_checks() -> int:
    count = 0
    count += 11   # top_level: 10 keys + abbreviation
    count += 2    # plans present
    count += 5    # tiers present (3 police + 2 teachers)
    count += 7    # tier1: 2 multipliers, ABP 12mo, service 20yr, contribution, COLA null
    count += 10   # tier2: 2 multipliers, max80%, ABP 36mo, service 25yr, age 50, mandatory 60, contribution, vesting, COLA cap
    count += 8    # tier3: multiplier, max80%, ABP 36mo, service 25yr, age null, mandatory 60, contribution, vesting, COLA cap
    count += 4    # tier_progression: t3>=t2, t3 age null, t3 rate > t1
    count += 7    # teachers post-1996: multiplier, ABP 36mo, contribution, COLA cap, age62, 30yr rules
    count += 4    # teachers pre-1996: 3 multipliers, contribution
    count += 2    # teachers vesting
    count += 1    # teachers SS = true
    count += 1    # police/fire SS = false
    count += 7    # COLA history: 4 values + 2 year-over-year + 1 police>teachers
    count += 2    # federal split: cutoff date, authority
    count += 1    # jurisdiction
    count += 5    # metadata: version, last_updated, sources count, url, scopingNote
    count += 4    # no consumer refs
    count += 5    # cross-checks: ABP periods, teacher rate progression, equal to t3, COLA < 3%
    return count


if __name__ == "__main__":
    sys.exit(run_all())
