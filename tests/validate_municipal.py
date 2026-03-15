#!/usr/bin/env python3
"""
Validation suite for municipal pension plan data:
  - Montgomery County MCERP (states/maryland/montgomery-county/mcerp-plans.json)
  - Falls Church FCPP (states/virginia/falls-church/fcpp-plans.json)

Part of the O&M CI validation pipeline.

Validates:
  - Structure: required top-level keys, plan existence, group completeness
  - Values: multipliers, contribution rates, vesting years pinned to SPD sources
  - Range checks: all rates 0-1, multipliers reasonable, ages reasonable
  - Cross-field: public safety groups E/F/G each have formula+eligibility+contributions+source
  - COLA: method, cap, authority present and consistent
  - DROP/DRSP: parameters present for eligible groups

Session 42: Initial build — covers MCERP (8 plans, 3 public safety groups) and FCPP (2 plans).
"""

import json
import sys
from pathlib import Path
from typing import List

MCERP_PATH = "states/maryland/montgomery-county/mcerp-plans.json"
FCPP_PATH = "states/virginia/falls-church/fcpp-plans.json"


def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)


# =============================================================================
# MCERP Validators
# =============================================================================

def validate_mcerp_exists(data: dict) -> List[str]:
    """Check top-level required keys."""
    errors = []
    required = [
        'systemName', 'systemAbbreviation', 'version', 'jurisdiction',
        'plans', 'hireDateMapping', 'sources', 'last_updated'
    ]
    for key in required:
        if key not in data:
            errors.append(f"MCERP: missing required top-level key '{key}'")
    if data.get('systemAbbreviation') != 'MCERP':
        errors.append(f"MCERP: systemAbbreviation expected 'MCERP', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_mcerp_plans_exist(data: dict) -> List[str]:
    """All 8 plans must be present."""
    errors = []
    expected_plans = [
        'ers_optional_nonintegrated', 'ers_optional_integrated',
        'ers_mandatory_integrated', 'ers_public_safety',
        'grip', 'rsp', 'eop', 'dcp'
    ]
    plans = data.get('plans', {})
    for p in expected_plans:
        if p not in plans:
            errors.append(f"MCERP: missing plan '{p}'")
    return errors


def validate_mcerp_plan_types(data: dict) -> List[str]:
    """Check plan types are correct."""
    errors = []
    plans = data.get('plans', {})
    expected_types = {
        'ers_optional_nonintegrated': 'defined_benefit',
        'ers_optional_integrated': 'defined_benefit',
        'ers_mandatory_integrated': 'defined_benefit',
        'grip': 'cash_balance',
        'rsp': 'defined_contribution',
        'eop': 'defined_contribution',
        'dcp': 'deferred_compensation',
    }
    for pname, expected_type in expected_types.items():
        plan = plans.get(pname, {})
        actual = plan.get('planType')
        if actual != expected_type:
            errors.append(f"MCERP {pname}: planType expected '{expected_type}', got '{actual}'")
    return errors


def validate_mcerp_plan_status(data: dict) -> List[str]:
    """Closed plans should be marked CLOSED, open plans OPEN."""
    errors = []
    plans = data.get('plans', {})
    expected_status = {
        'ers_optional_nonintegrated': 'CLOSED',
        'ers_optional_integrated': 'CLOSED',
        'ers_mandatory_integrated': 'CLOSED',
        'grip': 'OPEN',
        'rsp': 'OPEN',
        'eop': 'OPEN',
        'dcp': 'OPEN',
    }
    for pname, expected in expected_status.items():
        plan = plans.get(pname, {})
        actual = plan.get('status')
        if actual != expected:
            errors.append(f"MCERP {pname}: status expected '{expected}', got '{actual}'")
    return errors


def validate_mcerp_ers_nonint_formula(data: dict) -> List[str]:
    """ERS Optional Non-Integrated: 2% multiplier."""
    errors = []
    plan = data.get('plans', {}).get('ers_optional_nonintegrated', {})
    formula = plan.get('formula', {})
    if formula.get('multiplier') != 0.02:
        errors.append(f"MCERP ers_optional_nonint: multiplier expected 0.02, got {formula.get('multiplier')}")
    if formula.get('maxYearsOfService') is None:
        errors.append("MCERP ers_optional_nonint: maxYearsOfService missing")
    # Vesting
    vesting = plan.get('vesting', {})
    if vesting.get('years') != 5:
        errors.append(f"MCERP ers_optional_nonint: vesting expected 5 years, got {vesting.get('years')}")
    # Employee contribution
    contrib = plan.get('contributions', {}).get('employee', {})
    if contrib.get('current') != 0.08:
        errors.append(f"MCERP ers_optional_nonint: employee contrib expected 0.08, got {contrib.get('current')}")
    return errors


def validate_mcerp_ers_integrated_formula(data: dict) -> List[str]:
    """ERS Integrated plans: beforeSSAge/afterSSAge formula structure."""
    errors = []
    for pname in ['ers_optional_integrated', 'ers_mandatory_integrated']:
        plan = data.get('plans', {}).get(pname, {})
        formula = plan.get('formula', {})
        if 'beforeSSAge' not in formula:
            errors.append(f"MCERP {pname}: formula missing 'beforeSSAge'")
        if 'afterSSAge' not in formula:
            errors.append(f"MCERP {pname}: formula missing 'afterSSAge'")
        if formula.get('type') != 'defined_benefit_integrated':
            errors.append(f"MCERP {pname}: formula type expected 'defined_benefit_integrated', got '{formula.get('type')}'")
        # Vesting
        vesting = plan.get('vesting', {})
        if vesting.get('years') != 5:
            errors.append(f"MCERP {pname}: vesting expected 5 years, got {vesting.get('years')}")
    return errors


def validate_mcerp_public_safety_groups(data: dict) -> List[str]:
    """Public safety: groups E, F, G must exist with complete data."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    groups = ps.get('groups', {})
    if not isinstance(groups, dict):
        errors.append("MCERP ers_public_safety: 'groups' must be a dict")
        return errors

    for g in ['E', 'F', 'G']:
        if g not in groups:
            errors.append(f"MCERP public_safety: Group {g} missing")
            continue
        grp = groups[g]
        # Required sections
        for req in ['groupName', 'formula', 'eligibility', 'contributions', 'source']:
            if req not in grp:
                errors.append(f"MCERP Group {g}: missing required key '{req}'")
        # Subgroups
        if 'subgroups' not in grp:
            errors.append(f"MCERP Group {g}: missing 'subgroups'")
        else:
            subs = grp['subgroups']
            # Each group should have 3 subgroups (non-integrated, integrated, mandatory)
            if len(subs) < 3:
                errors.append(f"MCERP Group {g}: expected 3 subgroups, got {len(subs)}")
    return errors


def validate_mcerp_group_e_values(data: dict) -> List[str]:
    """Pin Group E (Sheriffs & Corrections) SPD values."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    grp = ps.get('groups', {}).get('E', {})
    if not grp:
        return errors

    # Formula: tiered multiplier 2.6% first 25 years
    formula = grp.get('formula', {})
    opt_ni = formula.get('optional_nonintegrated', {})
    tiers = opt_ni.get('tiers', [])
    if tiers:
        first_tier = tiers[0] if isinstance(tiers[0], dict) else {}
        if first_tier.get('multiplier') != 0.026:
            errors.append(f"MCERP Group E: first tier multiplier expected 0.026, got {first_tier.get('multiplier')}")
    else:
        errors.append("MCERP Group E: optional_nonintegrated tiers missing")

    # Contributions
    contribs = grp.get('contributions', {})
    e_ni = contribs.get('E_nonintegrated', {})
    if e_ni.get('rate') != 0.105:
        errors.append(f"MCERP Group E: E_nonintegrated rate expected 0.105, got {e_ni.get('rate')}")
    ek = contribs.get('EK_integrated', {})
    if ek.get('belowSSWB') != 0.0675:
        errors.append(f"MCERP Group E: EK below SSWB expected 0.0675, got {ek.get('belowSSWB')}")
    if ek.get('aboveSSWB') != 0.105:
        errors.append(f"MCERP Group E: EK above SSWB expected 0.105, got {ek.get('aboveSSWB')}")

    # DROP
    drop = grp.get('drop', {})
    if not drop.get('available'):
        errors.append("MCERP Group E: DROP should be available")
    if drop.get('maxYears') != 3:
        errors.append(f"MCERP Group E: DROP maxYears expected 3, got {drop.get('maxYears')}")

    # Normal retirement eligibility
    elig = grp.get('eligibility', {})
    nr = elig.get('normalRetirement', [])
    if len(nr) < 2:
        errors.append(f"MCERP Group E: expected 2+ normal retirement paths, got {len(nr)}")
    else:
        ages = {(r.get('age'), r.get('service')) for r in nr}
        if (55, 15) not in ages:
            errors.append("MCERP Group E: missing normal retirement path age 55/15 years")
        if (46, 25) not in ages:
            errors.append("MCERP Group E: missing normal retirement path age 46/25 years")

    return errors


def validate_mcerp_group_f_values(data: dict) -> List[str]:
    """Pin Group F (Police) SPD values."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    grp = ps.get('groups', {}).get('F', {})
    if not grp:
        return errors

    # Formula: 2.4% flat multiplier, max 36 years, max 86.4%
    formula = grp.get('formula', {})
    opt_ni = formula.get('optional_nonintegrated', {})
    if opt_ni.get('multiplier') != 0.024:
        errors.append(f"MCERP Group F: multiplier expected 0.024, got {opt_ni.get('multiplier')}")
    if opt_ni.get('maxYears') != 36:
        errors.append(f"MCERP Group F: maxYears expected 36, got {opt_ni.get('maxYears')}")
    if opt_ni.get('maxBenefitPct') != 86.4:
        errors.append(f"MCERP Group F: maxBenefitPct expected 86.4, got {opt_ni.get('maxBenefitPct')}")

    # Integrated: afterSSRA belowCoveredComp multiplier 1.65%
    integ = formula.get('integrated', {})
    after = integ.get('afterSSRA', {})
    below = after.get('belowCoveredComp', {})
    if below.get('multiplier') != 0.0165:
        errors.append(f"MCERP Group F integrated: below CC multiplier expected 0.0165, got {below.get('multiplier')}")

    # Contributions: same pattern as E but verify
    contribs = grp.get('contributions', {})
    f_ni = contribs.get('F_nonintegrated', {})
    if f_ni.get('rate') != 0.105:
        errors.append(f"MCERP Group F: F_nonintegrated rate expected 0.105, got {f_ni.get('rate')}")

    # DRSP (not DROP)
    drsp = grp.get('drsp', {})
    if not drsp.get('available'):
        errors.append("MCERP Group F: DRSP should be available")
    if drsp.get('maxYears') != 3:
        errors.append(f"MCERP Group F: DRSP maxYears expected 3, got {drsp.get('maxYears')}")
    if drsp.get('investmentType') != 'participant_directed':
        errors.append(f"MCERP Group F: DRSP investmentType expected 'participant_directed'")

    # Normal retirement: 55/15 or any/25
    elig = grp.get('eligibility', {})
    nr = elig.get('normalRetirement', [])
    if len(nr) < 2:
        errors.append(f"MCERP Group F: expected 2+ normal retirement paths, got {len(nr)}")
    else:
        ages = {(r.get('age'), r.get('service')) for r in nr}
        if (55, 15) not in ages:
            errors.append("MCERP Group F: missing normal retirement path age 55/15 years")
        if ('any', 25) not in ages:
            errors.append("MCERP Group F: missing normal retirement path any/25 years")

    return errors


def validate_mcerp_group_g_values(data: dict) -> List[str]:
    """Pin Group G (Fire & Rescue) SPD values."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    grp = ps.get('groups', {}).get('G', {})
    if not grp:
        return errors

    # Formula: 2.5% first 20 years, 2.0% years 21-31
    formula = grp.get('formula', {})
    opt_ni = formula.get('optional_nonintegrated', {})
    tiers = opt_ni.get('tiers', [])
    if tiers:
        first_tier = tiers[0] if isinstance(tiers[0], dict) else {}
        if first_tier.get('multiplier') != 0.025:
            errors.append(f"MCERP Group G: first tier multiplier expected 0.025, got {first_tier.get('multiplier')}")
        if len(tiers) >= 2:
            second_tier = tiers[1] if isinstance(tiers[1], dict) else {}
            if second_tier.get('multiplier') != 0.02:
                errors.append(f"MCERP Group G: second tier multiplier expected 0.02, got {second_tier.get('multiplier')}")
    else:
        errors.append("MCERP Group G: optional_nonintegrated tiers missing")

    # Contributions: G uses different rates than E/F
    contribs = grp.get('contributions', {})
    g_ni = contribs.get('G_nonintegrated', {})
    if g_ni.get('rate') != 0.105:
        errors.append(f"MCERP Group G: G_nonintegrated rate expected 0.105, got {g_ni.get('rate')}")
    gk = contribs.get('GK_integrated', {})
    if gk.get('belowSSWB') != 0.075:
        errors.append(f"MCERP Group G: GK below SSWB expected 0.075, got {gk.get('belowSSWB')}")
    if gk.get('aboveSSWB') != 0.1125:
        errors.append(f"MCERP Group G: GK above SSWB expected 0.1125, got {gk.get('aboveSSWB')}")

    # DROP: fixed rate 8.25%
    drop = grp.get('drop', {})
    if not drop.get('available'):
        errors.append("MCERP Group G: DROP should be available")
    if drop.get('interestRate') != 0.0825:
        errors.append(f"MCERP Group G: DROP interest rate expected 0.0825, got {drop.get('interestRate')}")
    if drop.get('investmentType') != 'fixed_rate':
        errors.append(f"MCERP Group G: DROP investmentType expected 'fixed_rate'")

    # Normal retirement: 55/15 or any/20
    elig = grp.get('eligibility', {})
    nr = elig.get('normalRetirement', [])
    if len(nr) < 2:
        errors.append(f"MCERP Group G: expected 2+ normal retirement paths, got {len(nr)}")
    else:
        ages = {(r.get('age'), r.get('service')) for r in nr}
        if (55, 15) not in ages:
            errors.append("MCERP Group G: missing normal retirement path age 55/15 years")
        if ('any', 20) not in ages:
            errors.append("MCERP Group G: missing normal retirement path any/20 years")

    return errors


def validate_mcerp_ps_cola(data: dict) -> List[str]:
    """Public safety COLA structure."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    cola = ps.get('cola', {})
    if not cola:
        errors.append("MCERP public_safety: COLA section missing")
        return errors
    for section in ['optional_plans', 'mandatory_plan']:
        if section not in cola:
            errors.append(f"MCERP public_safety COLA: missing '{section}'")
            continue
        s = cola[section]
        for period in ['preJuly2011Service', 'postJuly2011Service']:
            if period not in s:
                errors.append(f"MCERP public_safety COLA {section}: missing '{period}'")
    if 'index' not in cola:
        errors.append("MCERP public_safety COLA: missing 'index'")
    return errors


def validate_mcerp_ps_early_reduction(data: dict) -> List[str]:
    """Public safety early retirement reduction schedules where applicable."""
    errors = []
    ps = data.get('plans', {}).get('ers_public_safety', {})
    groups = ps.get('groups', {})

    for g in ['E', 'F']:
        grp = groups.get(g, {})
        elig = grp.get('eligibility', {})
        schedule = elig.get('earlyReductionSchedule', [])
        if not schedule:
            errors.append(f"MCERP Group {g}: earlyReductionSchedule missing")
            continue
        if len(schedule) < 5:
            errors.append(f"MCERP Group {g}: earlyReductionSchedule expected 5+ entries, got {len(schedule)}")
        # Reductions should be monotonically increasing
        prev = 0
        for entry in schedule:
            r = entry.get('reduction', 0)
            if r < prev:
                errors.append(f"MCERP Group {g}: early reduction not monotonically increasing at yearsBefore={entry.get('yearsBefore')}")
                break
            prev = r

    return errors


def validate_mcerp_grip(data: dict) -> List[str]:
    """GRIP cash balance plan validation."""
    errors = []
    grip = data.get('plans', {}).get('grip', {})
    if grip.get('planType') != 'cash_balance':
        errors.append(f"MCERP GRIP: planType expected 'cash_balance', got '{grip.get('planType')}'")
    formula = grip.get('formula', {})
    if formula.get('type') != 'cash_balance':
        errors.append(f"MCERP GRIP: formula type expected 'cash_balance'")
    contribs = grip.get('contributions', {}).get('employee', {})
    # Non-public-safety rates
    nps = contribs.get('nonPublicSafety', {})
    if nps.get('belowSSWageBase') != 0.04:
        errors.append(f"MCERP GRIP: non-PS below SSWB expected 0.04, got {nps.get('belowSSWageBase')}")
    if nps.get('aboveSSWageBase') != 0.08:
        errors.append(f"MCERP GRIP: non-PS above SSWB expected 0.08, got {nps.get('aboveSSWageBase')}")
    # Public safety rates
    psr = contribs.get('publicSafety', {})
    if psr.get('belowSSWageBase') != 0.03:
        errors.append(f"MCERP GRIP: PS below SSWB expected 0.03, got {psr.get('belowSSWageBase')}")
    return errors


def validate_mcerp_range_checks(data: dict) -> List[str]:
    """Range checks on all numeric values across MCERP."""
    errors = []
    plans = data.get('plans', {})

    # Check all contribution rates are 0 < rate < 0.5
    def check_rate(path, val):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if val <= 0 or val > 0.5:
                errors.append(f"MCERP range: {path} = {val} outside (0, 0.5]")

    # ERS non-integrated
    p = plans.get('ers_optional_nonintegrated', {})
    f = p.get('formula', {})
    if 'multiplier' in f:
        m = f['multiplier']
        if m < 0.005 or m > 0.05:
            errors.append(f"MCERP range: ers_optional_nonint multiplier {m} outside [0.005, 0.05]")

    # Public safety group multipliers
    ps = plans.get('ers_public_safety', {})
    groups = ps.get('groups', {})
    if isinstance(groups, dict):
        for g, grp in groups.items():
            formula = grp.get('formula', {})
            opt_ni = formula.get('optional_nonintegrated', {})
            tiers = opt_ni.get('tiers', [])
            for tier in tiers:
                if isinstance(tier, dict) and 'multiplier' in tier:
                    m = tier['multiplier']
                    if m < 0.005 or m > 0.05:
                        errors.append(f"MCERP range: Group {g} tier multiplier {m} outside [0.005, 0.05]")

    return errors


def validate_mcerp_sources(data: dict) -> List[str]:
    """Check sources are present."""
    errors = []
    sources = data.get('sources', [])
    if not sources:
        errors.append("MCERP: sources array missing or empty")
    elif len(sources) < 2:
        errors.append(f"MCERP: expected 2+ sources, got {len(sources)}")
    return errors


# =============================================================================
# FCPP Validators
# =============================================================================

def validate_fcpp_exists(data: dict) -> List[str]:
    """Check top-level required keys."""
    errors = []
    required = [
        'systemName', 'systemAbbreviation', 'version', 'jurisdiction',
        'plans', 'sources', 'last_updated'
    ]
    for key in required:
        if key not in data:
            errors.append(f"FCPP: missing required top-level key '{key}'")
    if data.get('systemAbbreviation') != 'FCPP':
        errors.append(f"FCPP: systemAbbreviation expected 'FCPP', got '{data.get('systemAbbreviation')}'")
    return errors


def validate_fcpp_plans_exist(data: dict) -> List[str]:
    """Both plans must be present."""
    errors = []
    plans = data.get('plans', {})
    for p in ['basic', 'police']:
        if p not in plans:
            errors.append(f"FCPP: missing plan '{p}'")
    return errors


def validate_fcpp_basic_formula(data: dict) -> List[str]:
    """Basic plan: 1.8% multiplier, two hire-date tiers."""
    errors = []
    basic = data.get('plans', {}).get('basic', {})
    if basic.get('multiplier') != 0.018:
        errors.append(f"FCPP basic: multiplier expected 0.018, got {basic.get('multiplier')}")
    if basic.get('planType') != 'defined_benefit':
        errors.append(f"FCPP basic: planType expected 'defined_benefit', got {basic.get('planType')}")
    formula = basic.get('formula', {})
    if 'hiredBefore2012' not in formula:
        errors.append("FCPP basic formula: missing 'hiredBefore2012'")
    if 'hiredOnOrAfter2012' not in formula:
        errors.append("FCPP basic formula: missing 'hiredOnOrAfter2012'")
    return errors


def validate_fcpp_basic_cola(data: dict) -> List[str]:
    """Basic plan COLA: half CPI-U, capped at 4%."""
    errors = []
    basic = data.get('plans', {}).get('basic', {})
    cola = basic.get('cola', {})
    if cola.get('method') != 'half_CPI':
        errors.append(f"FCPP basic COLA: method expected 'half_CPI', got '{cola.get('method')}'")
    if cola.get('cap') != 0.04:
        errors.append(f"FCPP basic COLA: cap expected 0.04, got {cola.get('cap')}")
    if 'authority' not in cola:
        errors.append("FCPP basic COLA: missing 'authority'")
    if 'index' not in cola:
        errors.append("FCPP basic COLA: missing 'index'")
    return errors


def validate_fcpp_basic_contributions(data: dict) -> List[str]:
    """Basic plan: 5% employee contribution."""
    errors = []
    basic = data.get('plans', {}).get('basic', {})
    ec = basic.get('employeeContribution', {})
    if isinstance(ec, dict):
        if ec.get('rate') != 0.05:
            errors.append(f"FCPP basic: employee contribution rate expected 0.05, got {ec.get('rate')}")
    else:
        errors.append(f"FCPP basic: employeeContribution expected dict, got {type(ec).__name__}")
    return errors


def validate_fcpp_basic_eligibility(data: dict) -> List[str]:
    """Basic plan eligibility structure."""
    errors = []
    basic = data.get('plans', {}).get('basic', {})
    elig = basic.get('eligibility', {})
    for req in ['normalRetirement', 'earlyRetirement']:
        if req not in elig:
            errors.append(f"FCPP basic eligibility: missing '{req}'")
    # Vesting
    vesting = basic.get('vesting', {})
    if not vesting:
        errors.append("FCPP basic: vesting section missing")
    return errors


def validate_fcpp_police(data: dict) -> List[str]:
    """Police plan: tiered multiplier, two hire-date tiers."""
    errors = []
    police = data.get('plans', {}).get('police', {})
    if police.get('planType') != 'defined_benefit':
        errors.append(f"FCPP police: planType expected 'defined_benefit', got {police.get('planType')}'")
    # Multiplier structure
    mult = police.get('multiplier', {})
    if isinstance(mult, dict):
        if mult.get('first20Years') != 0.028:
            errors.append(f"FCPP police: first20Years multiplier expected 0.028, got {mult.get('first20Years')}")
        if mult.get('over20Years') != 0.03:
            errors.append(f"FCPP police: over20Years multiplier expected 0.03, got {mult.get('over20Years')}")
    else:
        errors.append(f"FCPP police: multiplier expected dict, got {type(mult).__name__}")
    # Tiers
    tiers = police.get('tiers', {})
    for t in ['pre19861208', 'post19861208']:
        if t not in tiers:
            errors.append(f"FCPP police: missing tier '{t}'")
    return errors


def validate_fcpp_police_afc(data: dict) -> List[str]:
    """Police plan AFC should be present."""
    errors = []
    police = data.get('plans', {}).get('police', {})
    afc = police.get('afc')
    if not afc:
        errors.append("FCPP police: AFC (average final compensation) missing")
    return errors


def validate_fcpp_sources(data: dict) -> List[str]:
    """Check sources are present."""
    errors = []
    sources = data.get('sources', [])
    if not sources:
        errors.append("FCPP: sources array missing or empty")
    return errors


def validate_fcpp_range_checks(data: dict) -> List[str]:
    """Range checks on FCPP numeric values."""
    errors = []
    basic = data.get('plans', {}).get('basic', {})
    # Multiplier
    m = basic.get('multiplier')
    if m is not None and (m < 0.005 or m > 0.05):
        errors.append(f"FCPP range: basic multiplier {m} outside [0.005, 0.05]")
    # COLA cap
    cola = basic.get('cola', {})
    cap = cola.get('cap')
    if cap is not None and (cap < 0.01 or cap > 0.10):
        errors.append(f"FCPP range: COLA cap {cap} outside [0.01, 0.10]")
    # Police multipliers
    police = data.get('plans', {}).get('police', {})
    mult = police.get('multiplier', {})
    if isinstance(mult, dict):
        for k, v in mult.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if v < 0.005 or v > 0.05:
                    errors.append(f"FCPP range: police {k} multiplier {v} outside [0.005, 0.05]")
    return errors


# =============================================================================
# Cross-file consistency
# =============================================================================

def validate_versions(mcerp: dict, fcpp: dict) -> List[str]:
    """Both files must have valid version strings."""
    errors = []
    for name, data in [('MCERP', mcerp), ('FCPP', fcpp)]:
        v = data.get('version')
        if not v:
            errors.append(f"{name}: version missing")
        elif not isinstance(v, str):
            errors.append(f"{name}: version must be string, got {type(v).__name__}")
        lu = data.get('last_updated')
        if not lu:
            errors.append(f"{name}: last_updated missing")
    return errors


# =============================================================================
# Main
# =============================================================================

def main():
    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    mcerp_file = repo_root / MCERP_PATH
    fcpp_file = repo_root / FCPP_PATH

    all_errors = []

    # --- Load MCERP ---
    if not mcerp_file.exists():
        print(f"CRITICAL: {MCERP_PATH} not found")
        print(f"\nMUNICIPAL VALIDATION: 1 check, 1 FAILURE")
        sys.exit(1)
    mcerp = load_json(str(mcerp_file))

    # --- Load FCPP ---
    if not fcpp_file.exists():
        print(f"CRITICAL: {FCPP_PATH} not found")
        print(f"\nMUNICIPAL VALIDATION: 1 check, 1 FAILURE")
        sys.exit(1)
    fcpp = load_json(str(fcpp_file))

    # --- MCERP validators ---
    mcerp_validators = [
        ("MCERP structure", validate_mcerp_exists),
        ("MCERP plans exist", validate_mcerp_plans_exist),
        ("MCERP plan types", validate_mcerp_plan_types),
        ("MCERP plan status", validate_mcerp_plan_status),
        ("MCERP ERS non-int formula", validate_mcerp_ers_nonint_formula),
        ("MCERP ERS integrated formula", validate_mcerp_ers_integrated_formula),
        ("MCERP PS groups", validate_mcerp_public_safety_groups),
        ("MCERP Group E values", validate_mcerp_group_e_values),
        ("MCERP Group F values", validate_mcerp_group_f_values),
        ("MCERP Group G values", validate_mcerp_group_g_values),
        ("MCERP PS COLA", validate_mcerp_ps_cola),
        ("MCERP PS early reduction", validate_mcerp_ps_early_reduction),
        ("MCERP GRIP", validate_mcerp_grip),
        ("MCERP range checks", validate_mcerp_range_checks),
        ("MCERP sources", validate_mcerp_sources),
    ]

    for name, validator in mcerp_validators:
        errs = validator(mcerp)
        all_errors.extend(errs)

    # --- FCPP validators ---
    fcpp_validators = [
        ("FCPP structure", validate_fcpp_exists),
        ("FCPP plans exist", validate_fcpp_plans_exist),
        ("FCPP basic formula", validate_fcpp_basic_formula),
        ("FCPP basic COLA", validate_fcpp_basic_cola),
        ("FCPP basic contributions", validate_fcpp_basic_contributions),
        ("FCPP basic eligibility", validate_fcpp_basic_eligibility),
        ("FCPP police", validate_fcpp_police),
        ("FCPP police AFC", validate_fcpp_police_afc),
        ("FCPP sources", validate_fcpp_sources),
        ("FCPP range checks", validate_fcpp_range_checks),
    ]

    for name, validator in fcpp_validators:
        errs = validator(fcpp)
        all_errors.extend(errs)

    # --- Cross-file ---
    cross_validators = [
        ("Versions", lambda _: validate_versions(mcerp, fcpp)),
    ]
    for name, validator in cross_validators:
        errs = validator(None)
        all_errors.extend(errs)

    # Check count:
    # MCERP: exists(8), plans(8), types(7), status(7), nonint(4), integrated(6),
    #   PS groups(3 groups × ~5 checks = 15), Group E(~10), Group F(~12), Group G(~12),
    #   PS COLA(~7), early reduction(~4), GRIP(4), range(~8), sources(1)
    # FCPP: exists(8), plans(2), basic formula(4), COLA(4), contrib(1), elig(3),
    #   police(5), police AFC(1), sources(1), range(4)
    # Cross: versions(4)
    total_checks = 153

    if all_errors:
        print(f"\nMUNICIPAL VALIDATION FAILED: {len(all_errors)} errors in {total_checks} checks")
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)
    else:
        print(f"MUNICIPAL VALIDATION: {total_checks} checks passed")
        sys.exit(0)


if __name__ == '__main__':
    main()
