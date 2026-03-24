#!/usr/bin/env python3
"""
Validation suite for New York State pension plan data (Session 61):
  - NYSLRS (states/new-york/nyslrs-plans.json)
  - NYSTRS (states/new-york/nystrs-plans.json)

Session 61: Initial build for OM-33 (NYSLRS) and OM-36 (NYSTRS).
"""

import json
import sys
from typing import List

NYSLRS_PATH = "states/new-york/nyslrs-plans.json"
NYSTRS_PATH = "states/new-york/nystrs-plans.json"


def load_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


# ============================================================
# NYSLRS Validators
# ============================================================

def validate_nyslrs_top_level(data: dict) -> List[str]:
    errors = []
    required = ["systemName", "systemAbbreviation", "version", "jurisdiction",
                 "ers", "pfrs", "cola", "tier6_contribution_brackets",
                 "socialSecurity", "sources", "last_updated"]
    for k in required:
        if k not in data:
            errors.append(f"NYSLRS: missing required key '{k}'")
    if data.get("systemAbbreviation") != "NYSLRS":
        errors.append(f"NYSLRS: systemAbbreviation expected 'NYSLRS'")
    if data.get("jurisdiction", {}).get("state") != "NY":
        errors.append("NYSLRS: jurisdiction.state expected 'NY'")
    return errors


def validate_nyslrs_ers_tiers(data: dict) -> List[str]:
    errors = []
    ers_tiers = data.get("ers", {}).get("tiers", {})
    expected = ["tier_1", "tier_2", "tier_3_and_4", "tier_5", "tier_6"]
    for t in expected:
        if t not in ers_tiers:
            errors.append(f"NYSLRS ERS: missing tier '{t}'")
    return errors


def validate_nyslrs_pfrs_tiers(data: dict) -> List[str]:
    errors = []
    pfrs_tiers = data.get("pfrs", {}).get("tiers", {})
    expected = ["tier_1_2", "tier_3", "tier_5", "tier_6"]
    for t in expected:
        if t not in pfrs_tiers:
            errors.append(f"NYSLRS PFRS: missing tier '{t}'")
    # No Tier 4 in PFRS
    pfrs_note = data.get("pfrs", {}).get("note", "")
    if "no Tier 4" not in pfrs_note and "no tier 4" not in pfrs_note.lower():
        errors.append("NYSLRS PFRS: note should indicate there is no Tier 4 in PFRS")
    return errors


def validate_nyslrs_ers_formulas(data: dict) -> List[str]:
    errors = []
    ers = data.get("ers", {}).get("tiers", {})

    # Tiers 3&4: <20 = 1.66%, 20-30 = 2%, 30+ = 2%x30 + 1.5% beyond
    t34 = ers.get("tier_3_and_4", {}).get("benefitFormula", {}).get("article15_coordinated", {})
    if t34.get("under20years", {}).get("multiplier") != 0.0166:
        errors.append(f"NYSLRS ERS T3/4: <20yr multiplier expected 0.0166, got {t34.get('under20years', {}).get('multiplier')}")
    if t34.get("20to30years", {}).get("multiplier") != 0.02:
        errors.append(f"NYSLRS ERS T3/4: 20-30yr multiplier expected 0.02")

    # Tier 5: same formula as T3/4
    t5 = ers.get("tier_5", {}).get("benefitFormula", {}).get("article15_coordinated", {})
    if t5.get("under20years", {}).get("multiplier") != 0.0166:
        errors.append(f"NYSLRS ERS T5: <20yr multiplier expected 0.0166")

    # Tier 6: <20 = 1.66%, at20 = 1.75%x20 = 35%, 20+ = 35% + 2% per yr beyond
    t6 = ers.get("tier_6", {}).get("benefitFormula", {}).get("article15_coordinated", {})
    if t6.get("under20years", {}).get("multiplier") != 0.0166:
        errors.append(f"NYSLRS ERS T6: <20yr multiplier expected 0.0166")
    t6_at20 = t6.get("exactly20years", {}).get("structure", "")
    if "1.75" not in t6_at20 and "35%" not in t6_at20:
        errors.append("NYSLRS ERS T6: at20years formula should reference 1.75% or 35% of FAE")

    return errors


def validate_nyslrs_ers_retirement_ages(data: dict) -> List[str]:
    errors = []
    ers = data.get("ers", {}).get("tiers", {})

    # T3/4 full benefits at 62
    t34 = ers.get("tier_3_and_4", {}).get("retirementAge", {})
    if t34.get("fullBenefits") != 62:
        errors.append(f"NYSLRS ERS T3/4: fullBenefits age expected 62")

    # T5 full benefits at 62
    t5 = ers.get("tier_5", {}).get("retirementAge", {})
    if t5.get("fullBenefits") != 62:
        errors.append(f"NYSLRS ERS T5: fullBenefits age expected 62")

    # T6 full benefits at 63
    t6 = ers.get("tier_6", {}).get("retirementAge", {})
    if t6.get("fullBenefits") != 63:
        errors.append(f"NYSLRS ERS T6: fullBenefits age expected 63, got {t6.get('fullBenefits')}")

    return errors


def validate_nyslrs_tier6_fae_update(data: dict) -> List[str]:
    errors = []
    t6 = data.get("ers", {}).get("tiers", {}).get("tier_6", {})
    fae = t6.get("finalAverageEarnings", {})
    if fae.get("years") != 3:
        errors.append(f"NYSLRS ERS T6: FAE years expected 3 (2024 law), got {fae.get('years')}")
    note = fae.get("tier6FAEUpdateNote", "")
    if "2024" not in note:
        errors.append("NYSLRS ERS T6: FAE note should reference 2024 law")
    return errors


def validate_nyslrs_tier6_contributions(data: dict) -> List[str]:
    errors = []
    brackets = data.get("tier6_contribution_brackets", {}).get("brackets", [])
    if len(brackets) < 5:
        errors.append(f"NYSLRS: tier6_contribution_brackets should have 5 brackets, got {len(brackets)}")
    # First bracket: up to $45K = 3%
    if brackets:
        b0 = brackets[0]
        if b0.get("rate") != 0.03:
            errors.append(f"NYSLRS: first contribution bracket rate expected 0.03, got {b0.get('rate')}")
        if b0.get("earningsUpTo") != 45000:
            errors.append(f"NYSLRS: first contribution bracket earningsUpTo expected 45000")
    # Last bracket: over $100K = 6%
    if len(brackets) >= 5:
        b4 = brackets[4]
        if b4.get("rate") != 0.06:
            errors.append(f"NYSLRS: last contribution bracket rate expected 0.06, got {b4.get('rate')}")
    min_rate = data.get("tier6_contribution_brackets", {}).get("minimum")
    max_rate = data.get("tier6_contribution_brackets", {}).get("maximum")
    if min_rate != 0.03:
        errors.append(f"NYSLRS: tier6 contribution minimum expected 0.03, got {min_rate}")
    if max_rate != 0.06:
        errors.append(f"NYSLRS: tier6 contribution maximum expected 0.06, got {max_rate}")
    return errors


def validate_nyslrs_cola(data: dict) -> List[str]:
    errors = []
    cola = data.get("cola", {})
    if cola.get("floor") != 0.01:
        errors.append(f"NYSLRS: COLA floor expected 0.01 (1%), got {cola.get('floor')}")
    if cola.get("cap") != 0.03:
        errors.append(f"NYSLRS: COLA cap expected 0.03 (3%), got {cola.get('cap')}")
    applies = cola.get("appliesTo", "")
    if "18,000" not in applies and "18000" not in applies:
        errors.append("NYSLRS: COLA appliesTo should reference $18,000")
    if cola.get("automatic") is not True:
        errors.append("NYSLRS: COLA automatic should be true")
    eligibility = cola.get("eligibility", {})
    if not eligibility.get("option1") or not eligibility.get("option2"):
        errors.append("NYSLRS: COLA eligibility should have option1 and option2")
    return errors


def validate_nyslrs_pfrs_special_plans(data: dict) -> List[str]:
    errors = []
    sp = data.get("pfrs", {}).get("specialPlans", {})
    if not sp.get("section384_25year"):
        errors.append("NYSLRS PFRS: missing section384_25year special plan")
    if not sp.get("section384d_20year"):
        errors.append("NYSLRS PFRS: missing section384d_20year special plan")
    # 25-year plan: 50% of FAE
    s384 = sp.get("section384_25year", {})
    if "50%" not in str(s384.get("benefit", "")):
        errors.append("NYSLRS PFRS: section384 25-year benefit should be 50% of FAE")
    # 20-year plan: 50% of FAE
    s384d = sp.get("section384d_20year", {})
    if "50%" not in str(s384d.get("benefit", "")):
        errors.append("NYSLRS PFRS: section384d 20-year benefit should be 50% of FAE")
    return errors


def validate_nyslrs_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not True:
        errors.append("NYSLRS: socialSecurity.covered should be true")
    return errors


def validate_nyslrs_vesting(data: dict) -> List[str]:
    errors = []
    v = data.get("vesting", {})
    if "5 years" not in str(v.get("note", "")) and not v.get("years"):
        errors.append("NYSLRS: vesting should reference 5 years")
    return errors


# ============================================================
# NYSTRS Validators
# ============================================================

def validate_nystrs_top_level(data: dict) -> List[str]:
    errors = []
    required = ["systemName", "systemAbbreviation", "version", "jurisdiction",
                 "tiers", "cola", "socialSecurity", "sources", "last_updated"]
    for k in required:
        if k not in data:
            errors.append(f"NYSTRS: missing required key '{k}'")
    if data.get("systemAbbreviation") != "NYSTRS":
        errors.append(f"NYSTRS: systemAbbreviation expected 'NYSTRS'")
    if data.get("jurisdiction", {}).get("state") != "NY":
        errors.append("NYSTRS: jurisdiction.state expected 'NY'")
    return errors


def validate_nystrs_tiers_exist(data: dict) -> List[str]:
    errors = []
    tiers = data.get("tiers", {})
    expected = ["tier_1", "tier_2", "tier_3", "tier_4", "tier_5", "tier_6"]
    for t in expected:
        if t not in tiers:
            errors.append(f"NYSTRS: missing tier '{t}'")
    return errors


def validate_nystrs_tier4_formula(data: dict) -> List[str]:
    errors = []
    t4 = data.get("tiers", {}).get("tier_4", {}).get("benefitFormula", {})
    if t4.get("under20years", {}).get("multiplier") not in [0.0167, 1/60]:
        val = t4.get("under20years", {}).get("multiplier")
        if not (0.0166 < val < 0.0168):
            errors.append(f"NYSTRS T4: <20yr multiplier expected ~0.0167, got {val}")
    if t4.get("20to30years", {}).get("multiplier") != 0.02:
        errors.append("NYSTRS T4: 20-30yr multiplier expected 0.02")
    # Over 30: 2% x 30 + 1.5% beyond
    over30 = t4.get("over30years", {}).get("structure", "")
    if "1.5" not in over30:
        errors.append("NYSTRS T4: over30 formula should reference 1.5%")
    return errors


def validate_nystrs_tier4_retirement(data: dict) -> List[str]:
    errors = []
    t4 = data.get("tiers", {}).get("tier_4", {})
    nr = t4.get("normalRetirement", {})
    if nr.get("ageWithService", {}).get("age") != 62:
        errors.append("NYSTRS T4: normal retirement age expected 62")
    if nr.get("earlyUnreduced", {}).get("age") != 55:
        errors.append("NYSTRS T4: early unreduced retirement age expected 55")
    if nr.get("earlyUnreduced", {}).get("service") != 30:
        errors.append("NYSTRS T4: early unreduced requires 30 years of service")
    return errors


def validate_nystrs_tier5_retirement(data: dict) -> List[str]:
    errors = []
    t5 = data.get("tiers", {}).get("tier_5", {})
    nr = t5.get("normalRetirement", {})
    # Tier 5: full benefits at 62, OR 57 with 30+ years
    if nr.get("ageWithService", {}).get("age") != 62:
        errors.append("NYSTRS T5: normal retirement age expected 62")
    if nr.get("earlyUnreduced", {}).get("age") != 57:
        errors.append(f"NYSTRS T5: early unreduced age expected 57 (not 55), got {nr.get('earlyUnreduced', {}).get('age')}")
    return errors


def validate_nystrs_tier6_formula(data: dict) -> List[str]:
    errors = []
    t6 = data.get("tiers", {}).get("tier_6", {}).get("benefitFormula", {})
    at20 = t6.get("at20years", {}).get("structure", "")
    if "1.75" not in at20 and "35%" not in at20:
        errors.append("NYSTRS T6: at20years formula should reference 1.75% or 35%")
    over20 = t6.get("over20years", {}).get("structure", "")
    if "35%" not in over20 or "2%" not in over20:
        errors.append("NYSTRS T6: over20years formula should reference 35% base + 2% per year")
    return errors


def validate_nystrs_tier6_retirement(data: dict) -> List[str]:
    errors = []
    t6 = data.get("tiers", {}).get("tier_6", {})
    nr = t6.get("normalRetirement", {})
    if nr.get("ageWithService", {}).get("age") != 63:
        errors.append(f"NYSTRS T6: normal retirement age expected 63, got {nr.get('ageWithService', {}).get('age')}")
    if nr.get("noReductionAge") != 63:
        errors.append("NYSTRS T6: noReductionAge expected 63")
    return errors


def validate_nystrs_tier6_fae(data: dict) -> List[str]:
    """NYSTRS Tier 6 FAS is still 5 years — did NOT get the 2024 3-year law."""
    errors = []
    t6 = data.get("tiers", {}).get("tier_6", {})
    fas = t6.get("finalAverageSalary", {})
    if fas.get("years") != 5:
        errors.append(f"NYSTRS T6: FAS years expected 5 (NYSTRS did NOT get the 2024 3-year law), got {fas.get('years')}")
    note = fas.get("nystrsVsNYSLRSNote", "")
    if "5" not in note or "NYSLRS" not in note:
        errors.append("NYSTRS T6: FAS should note it remains 5 years, distinguishing from NYSLRS")
    return errors


def validate_nystrs_tier6_contributions(data: dict) -> List[str]:
    errors = []
    t6 = data.get("tiers", {}).get("tier_6", {}).get("memberContributions", {})
    brackets = t6.get("brackets", [])
    if len(brackets) < 5:
        errors.append(f"NYSTRS T6: contribution brackets expected 5, got {len(brackets)}")
    if brackets:
        if brackets[0].get("rate") != 0.03:
            errors.append(f"NYSTRS T6: first bracket rate expected 0.03")
        if brackets[0].get("earningsUpTo") != 45000:
            errors.append("NYSTRS T6: first bracket earningsUpTo expected 45000")
    interest = t6.get("interestOnContributions")
    if interest != 0.05:
        errors.append(f"NYSTRS T6: contributions interest expected 0.05 (5%), got {interest}")
    return errors


def validate_nystrs_cola(data: dict) -> List[str]:
    errors = []
    cola = data.get("cola", {})
    if cola.get("floor") != 0.01:
        errors.append(f"NYSTRS: COLA floor expected 0.01, got {cola.get('floor')}")
    if cola.get("cap") != 0.03:
        errors.append(f"NYSTRS: COLA cap expected 0.03, got {cola.get('cap')}")
    if "18,000" not in str(cola.get("appliesTo", "")):
        errors.append("NYSTRS: COLA appliesTo should reference $18,000")
    if cola.get("automatic") is not True:
        errors.append("NYSTRS: COLA automatic should be true")
    return errors


def validate_nystrs_social_security(data: dict) -> List[str]:
    errors = []
    ss = data.get("socialSecurity", {})
    if ss.get("covered") is not True:
        errors.append("NYSTRS: socialSecurity.covered should be true")
    # Tier 3 SS offset should be mentioned
    if "Tier 3" not in str(ss.get("tier3SSOffset", "")) and "tier3SSOffset" not in str(ss):
        errors.append("NYSTRS: socialSecurity should note Tier 3 SS offset provision")
    return errors


def validate_nystrs_funding(data: dict) -> List[str]:
    errors = []
    # ratio may be in employerContributions or fundingStatus
    funding = data.get("employerContributions", {})
    ratio = funding.get("fundedRatioMarketValue")
    if ratio is None:
        ratio = data.get("fundingStatus", {}).get("fundedRatioMarketValue")
    if not ratio or not (0.9 < ratio < 1.1):
        errors.append(f"NYSTRS: fundedRatioMarketValue expected ~101.5% (1.015), got {ratio}")
    return errors


def validate_nystrs_tier3_ss_offset(data: dict) -> List[str]:
    errors = []
    t3 = data.get("tiers", {}).get("tier_3", {})
    if not t3.get("ssOffset"):
        errors.append("NYSTRS T3: ssOffset should be documented")
    return errors


# ============================================================
# Metadata validators
# ============================================================

def validate_metadata(abbrev: str, data: dict) -> List[str]:
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

    # --- NYSLRS ---
    try:
        nyslrs = load_json(NYSLRS_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading {NYSLRS_PATH}: {e}")
        return 1

    nyslrs_validators = [
        validate_nyslrs_top_level,
        validate_nyslrs_ers_tiers,
        validate_nyslrs_pfrs_tiers,
        validate_nyslrs_ers_formulas,
        validate_nyslrs_ers_retirement_ages,
        validate_nyslrs_tier6_fae_update,
        validate_nyslrs_tier6_contributions,
        validate_nyslrs_cola,
        validate_nyslrs_pfrs_special_plans,
        validate_nyslrs_social_security,
        validate_nyslrs_vesting,
        lambda d: validate_metadata("NYSLRS", d),
    ]
    for v in nyslrs_validators:
        all_errors.extend(v(nyslrs))

    # --- NYSTRS ---
    try:
        nystrs = load_json(NYSTRS_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading {NYSTRS_PATH}: {e}")
        return 1

    nystrs_validators = [
        validate_nystrs_top_level,
        validate_nystrs_tiers_exist,
        validate_nystrs_tier4_formula,
        validate_nystrs_tier4_retirement,
        validate_nystrs_tier5_retirement,
        validate_nystrs_tier6_formula,
        validate_nystrs_tier6_retirement,
        validate_nystrs_tier6_fae,
        validate_nystrs_tier6_contributions,
        validate_nystrs_cola,
        validate_nystrs_social_security,
        validate_nystrs_funding,
        validate_nystrs_tier3_ss_offset,
        lambda d: validate_metadata("NYSTRS", d),
    ]
    for v in nystrs_validators:
        all_errors.extend(v(nystrs))

    check_count = count_checks()

    if all_errors:
        print(f"NY PENSIONS VALIDATION: FAILED — {len(all_errors)} errors")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print(f"NY PENSIONS VALIDATION: {check_count} checks passed")
        return 0


def count_checks() -> int:
    c = 0
    # NYSLRS
    c += 11   # top-level keys + abbrev + state
    c += 5    # ERS tiers exist
    c += 3    # PFRS tiers exist + no Tier 4 note
    c += 5    # ERS formulas (T3/4 x2, T5, T6 <20, T6 at20)
    c += 3    # ERS retirement ages (T3/4, T5, T6)
    c += 2    # T6 FAE 3 years + 2024 note
    c += 5    # T6 contributions brackets + min + max + first bracket + last bracket
    c += 5    # COLA floor, cap, applies to, automatic, eligibility
    c += 4    # PFRS special plans exist x2 + benefits x2
    c += 1    # SS covered
    c += 1    # vesting
    c += 3    # metadata
    # NYSTRS
    c += 9    # top-level keys + abbrev + state
    c += 6    # tiers exist
    c += 4    # T4 formula (3 checks) + over30
    c += 3    # T4 retirement (age, early unreduced age, service)
    c += 2    # T5 retirement (age 62 + unreduced age 57)
    c += 2    # T6 formula at20 + over20
    c += 2    # T6 retirement age 63 + noReductionAge
    c += 2    # T6 FAE 5 years + note
    c += 3    # T6 contributions brackets + first bracket + interest
    c += 4    # COLA floor, cap, applies to, automatic
    c += 2    # SS covered + tier3 offset note
    c += 1    # funding ratio
    c += 1    # tier3 SS offset
    c += 3    # metadata
    return c


if __name__ == "__main__":
    sys.exit(run_all())
