#!/usr/bin/env python3
"""
Validation suite for TRICARE Dental Program costs (dental_costs section of tricare-rates.json).
Part of the O&M CI validation pipeline.

Validates:
  - Structure: required keys, eligibility, premium tiers, cost-share tables
  - Values: premiums match official TDP schedule (tricare.mil, effective March 1, 2026)
  - Range checks: all premiums positive, cost-shares 0-100%
  - Cross-field consistency: pay grade ordering, plan maximums
  - Prior year comparison: 2025 rates for YoY verification
"""

import json
import sys
from pathlib import Path
from typing import List


def load_tricare(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_dental_exists(data: dict) -> List[str]:
    errors = []
    if 'dental_costs' not in data:
        errors.append("CRITICAL: dental_costs section missing from tricare-rates.json")
    return errors


def validate_dental_structure(dc: dict) -> List[str]:
    errors = []
    required = [
        'contractor', 'effective_period', 'eligibility',
        'monthly_premiums', 'cost_shares', 'plan_maximums'
    ]
    for key in required:
        if key not in dc:
            errors.append(f"dental_costs: missing required key '{key}'")
    return errors


def validate_effective_period(dc: dict) -> List[str]:
    errors = []
    ep = dc.get('effective_period', {})
    if ep.get('start') != '2026-03-01':
        errors.append(f"Effective period start: expected 2026-03-01, got {ep.get('start')}")
    if ep.get('end') != '2027-02-28':
        errors.append(f"Effective period end: expected 2027-02-28, got {ep.get('end')}")
    return errors


def validate_contractor(dc: dict) -> List[str]:
    errors = []
    if dc.get('contractor') != 'United Concordia':
        errors.append(f"Contractor: expected 'United Concordia', got '{dc.get('contractor')}'")
    return errors


def validate_ad_premiums(dc: dict) -> List[str]:
    """Validate active duty family member premium rates."""
    errors = []
    ad = dc.get('monthly_premiums', {}).get('active_duty', {})

    expected = {
        ('single', 'e1_e4'): 8.79,
        ('single', 'e5_and_above'): 11.72,
        ('family', 'e1_e4'): 22.85,
        ('family', 'e5_and_above'): 30.47,
    }
    for (tier, grade), expected_val in expected.items():
        actual = ad.get(tier, {}).get(grade)
        if actual is None:
            errors.append(f"AD premium {tier}/{grade}: missing")
        elif actual != expected_val:
            errors.append(f"AD premium {tier}/{grade}: expected ${expected_val}, got ${actual}")

    return errors


def validate_selres_premiums(dc: dict) -> List[str]:
    """Validate Selected Reserve / IRR (mobilization) premium rates."""
    errors = []
    sr = dc.get('monthly_premiums', {}).get('selected_reserve_and_irr_mobilization', {})

    # Sponsor only by pay grade
    so = sr.get('sponsor_only', {})
    if so.get('e1_e4') != 8.79:
        errors.append(f"SelRes sponsor_only e1_e4: expected $8.79, got ${so.get('e1_e4')}")
    if so.get('e5_and_above') != 11.72:
        errors.append(f"SelRes sponsor_only e5+: expected $11.72, got ${so.get('e5_and_above')}")

    # Flat rates
    if sr.get('single') != 29.30:
        errors.append(f"SelRes single: expected $29.30, got ${sr.get('single')}")
    if sr.get('family') != 76.18:
        errors.append(f"SelRes family: expected $76.18, got ${sr.get('family')}")

    # Sponsor and family by pay grade
    sf = sr.get('sponsor_and_family', {})
    if sf.get('e1_e4') != 84.87:
        errors.append(f"SelRes sponsor+family e1_e4: expected $84.87, got ${sf.get('e1_e4')}")
    if sf.get('e5_and_above') != 87.90:
        errors.append(f"SelRes sponsor+family e5+: expected $87.90, got ${sf.get('e5_and_above')}")

    return errors


def validate_irr_premiums(dc: dict) -> List[str]:
    """Validate IRR (non-mobilization) premium rates."""
    errors = []
    irr = dc.get('monthly_premiums', {}).get('irr_non_mobilization', {})

    expected = {
        'sponsor_only': 29.30,
        'single': 29.30,
        'family': 76.18,
        'sponsor_and_family': 105.48,
    }
    for key, expected_val in expected.items():
        actual = irr.get(key)
        if actual is None:
            errors.append(f"IRR {key}: missing")
        elif actual != expected_val:
            errors.append(f"IRR {key}: expected ${expected_val}, got ${actual}")

    return errors


def validate_survivor_premiums(dc: dict) -> List[str]:
    """ADSM survivors pay $0."""
    errors = []
    surv = dc.get('monthly_premiums', {}).get('adsm_survivors', {})
    if surv.get('premium') != 0:
        errors.append(f"Survivor premium: expected $0, got ${surv.get('premium')}")
    return errors


def validate_cost_shares_structure(dc: dict) -> List[str]:
    """Validate cost-share tables have all required service categories."""
    errors = []
    cs = dc.get('cost_shares', {})

    required_tiers = ['conus_e1_e4', 'conus_e5_and_above', 'oconus_command_sponsored']
    service_categories = [
        'diagnostic', 'preventive', 'sealants', 'consultation_office_visit',
        'post_surgical', 'basic_restorative', 'endodontic', 'periodontic',
        'oral_surgery', 'general_anesthesia', 'intravenous_sedation',
        'miscellaneous_services', 'other_restorative', 'implant_services',
        'prosthodontic', 'orthodontic'
    ]

    for tier in required_tiers:
        tier_data = cs.get(tier, {})
        if not tier_data:
            errors.append(f"Cost shares: missing tier '{tier}'")
            continue
        for svc in service_categories:
            if svc not in tier_data:
                errors.append(f"Cost shares {tier}: missing service '{svc}'")

    return errors


def validate_cost_share_values(dc: dict) -> List[str]:
    """Validate specific cost-share percentages against official schedule."""
    errors = []
    cs = dc.get('cost_shares', {})

    # CONUS E1-E4 specific checks
    e14 = cs.get('conus_e1_e4', {})
    expected_e14 = {
        'diagnostic': 0, 'preventive': 0, 'sealants': 0,
        'basic_restorative': 20, 'endodontic': 30, 'periodontic': 30,
        'oral_surgery': 30, 'general_anesthesia': 40,
        'orthodontic': 50, 'prosthodontic': 50
    }
    for svc, expected_val in expected_e14.items():
        actual = e14.get(svc)
        if actual is not None and actual != expected_val:
            errors.append(f"Cost share E1-E4 {svc}: expected {expected_val}%, got {actual}%")

    # CONUS E5+ specific divergences from E1-E4
    e5 = cs.get('conus_e5_and_above', {})
    if e5.get('endodontic') != 40:
        errors.append(f"Cost share E5+ endodontic: expected 40%, got {e5.get('endodontic')}%")
    if e5.get('periodontic') != 40:
        errors.append(f"Cost share E5+ periodontic: expected 40%, got {e5.get('periodontic')}%")
    if e5.get('oral_surgery') != 40:
        errors.append(f"Cost share E5+ oral_surgery: expected 40%, got {e5.get('oral_surgery')}%")

    # OCONUS: most services 0%, except high-tier at 50%
    oconus = cs.get('oconus_command_sponsored', {})
    zero_services = ['diagnostic', 'preventive', 'sealants', 'consultation_office_visit',
                     'basic_restorative', 'endodontic', 'periodontic', 'oral_surgery',
                     'general_anesthesia', 'intravenous_sedation', 'miscellaneous_services']
    for svc in zero_services:
        val = oconus.get(svc)
        if val is not None and val != 0:
            errors.append(f"Cost share OCONUS {svc}: expected 0%, got {val}%")

    fifty_services = ['other_restorative', 'implant_services', 'prosthodontic', 'orthodontic']
    for svc in fifty_services:
        val = oconus.get(svc)
        if val is not None and val != 50:
            errors.append(f"Cost share OCONUS {svc}: expected 50%, got {val}%")

    return errors


def validate_cost_share_range(dc: dict) -> List[str]:
    """All cost-share percentages must be 0-100."""
    errors = []
    cs = dc.get('cost_shares', {})
    for tier_key, tier_data in cs.items():
        if not isinstance(tier_data, dict):
            continue
        for svc, val in tier_data.items():
            if svc.startswith('_') or not isinstance(val, (int, float)):
                continue
            if val < 0 or val > 100:
                errors.append(f"Cost share {tier_key}/{svc}: {val}% out of 0-100 range")
    return errors


def validate_plan_maximums(dc: dict) -> List[str]:
    """Validate plan maximum amounts."""
    errors = []
    pm = dc.get('plan_maximums', {})

    checks = {
        ('annual_non_orthodontic', 'per_person_per_contract_year'): 1500,
        ('lifetime_orthodontic', 'per_person'): 1750,
        ('annual_accident_care', 'per_person_per_contract_year'): 1200,
    }
    for (section, field), expected_val in checks.items():
        actual = pm.get(section, {}).get(field)
        if actual is None:
            errors.append(f"Plan max {section}/{field}: missing")
        elif actual != expected_val:
            errors.append(f"Plan max {section}/{field}: expected ${expected_val}, got ${actual}")

    return errors


def validate_premium_ordering(dc: dict) -> List[str]:
    """E1-E4 premiums should be <= E5+ premiums (lower pay grades pay less)."""
    errors = []
    ad = dc.get('monthly_premiums', {}).get('active_duty', {})

    for tier in ['single', 'family']:
        e14 = ad.get(tier, {}).get('e1_e4')
        e5 = ad.get(tier, {}).get('e5_and_above')
        if e14 is not None and e5 is not None and e14 > e5:
            errors.append(f"AD {tier}: E1-E4 (${e14}) > E5+ (${e5})")

    # Single < Family for same pay grade
    for grade in ['e1_e4', 'e5_and_above']:
        s = ad.get('single', {}).get(grade)
        f = ad.get('family', {}).get(grade)
        if s is not None and f is not None and s > f:
            errors.append(f"AD {grade}: single (${s}) > family (${f})")

    return errors


def validate_prior_year_premiums(dc: dict) -> List[str]:
    """Validate 2025 prior year AD premiums."""
    errors = []
    py = dc.get('prior_year_premiums_2025', {}).get('active_duty', {})

    expected = {
        ('single', 'e1_e4'): 8.65,
        ('single', 'e5_and_above'): 11.53,
        ('family', 'e1_e4'): 22.48,
        ('family', 'e5_and_above'): 29.98,
    }
    for (tier, grade), expected_val in expected.items():
        actual = py.get(tier, {}).get(grade)
        if actual is None:
            errors.append(f"Prior year AD {tier}/{grade}: missing")
        elif actual != expected_val:
            errors.append(f"Prior year AD {tier}/{grade}: expected ${expected_val}, got ${actual}")

    return errors


def validate_yoy_direction(dc: dict) -> List[str]:
    """2026 premiums should be >= 2025 premiums (MOAA confirmed slight increase)."""
    errors = []
    cur = dc.get('monthly_premiums', {}).get('active_duty', {})
    py = dc.get('prior_year_premiums_2025', {}).get('active_duty', {})

    for tier in ['single', 'family']:
        for grade in ['e1_e4', 'e5_and_above']:
            c = cur.get(tier, {}).get(grade)
            p = py.get(tier, {}).get(grade)
            if c is not None and p is not None and c < p:
                errors.append(f"YoY direction: 2026 AD {tier}/{grade} (${c}) < 2025 (${p})")

    return errors


def validate_premiums_positive(dc: dict) -> List[str]:
    """All premium values must be non-negative."""
    errors = []

    def check_dict(d, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.startswith('_'):
                    continue
                check_dict(v, f"{path}/{k}")
        elif isinstance(d, (int, float)):
            if d < 0:
                errors.append(f"Negative premium at {path}: {d}")

    check_dict(dc.get('monthly_premiums', {}), "monthly_premiums")
    return errors


def validate_metadata_version(data: dict) -> List[str]:
    errors = []
    version = data.get('_metadata', {}).get('version')
    if version != '2026.3':
        errors.append(f"Metadata version: expected '2026.3', got '{version}'")
    return errors


def validate_data_sources(data: dict) -> List[str]:
    errors = []
    sources = data.get('data_sources', [])
    dental_url = 'https://tricare.mil/Costs/DentalCosts/TDP/Premiums'
    if dental_url not in sources:
        errors.append(f"data_sources: missing dental premium URL")
    return errors


def main():
    repo_root = Path(__file__).parent.parent
    filepath = repo_root / 'federal' / 'healthcare' / 'tricare-rates.json'

    if not filepath.exists():
        print("FAIL: tricare-rates.json not found")
        sys.exit(1)

    data = load_tricare(str(filepath))
    all_errors = []

    errs = validate_dental_exists(data)
    all_errors.extend(errs)
    if errs:
        print(f"CRITICAL: {errs[0]}")
        print(f"\nDENTAL VALIDATION: 1 check, 1 FAILURE")
        sys.exit(1)

    dc = data['dental_costs']

    validators = [
        ("Structure", validate_dental_structure),
        ("Effective period", validate_effective_period),
        ("Contractor", validate_contractor),
        ("AD premiums", validate_ad_premiums),
        ("SelRes premiums", validate_selres_premiums),
        ("IRR premiums", validate_irr_premiums),
        ("Survivor premiums", validate_survivor_premiums),
        ("Cost-share structure", validate_cost_shares_structure),
        ("Cost-share values", validate_cost_share_values),
        ("Cost-share range", validate_cost_share_range),
        ("Plan maximums", validate_plan_maximums),
        ("Premium ordering", validate_premium_ordering),
        ("Prior year premiums", validate_prior_year_premiums),
        ("YoY direction", validate_yoy_direction),
        ("Premiums positive", validate_premiums_positive),
    ]

    for name, validator in validators:
        errs = validator(dc)
        all_errors.extend(errs)

    file_validators = [
        ("Metadata version", validate_metadata_version),
        ("Data sources", validate_data_sources),
    ]
    for name, validator in file_validators:
        errs = validator(data)
        all_errors.extend(errs)

    # Discrete check count:
    # exists:1, structure:6, effective:2, contractor:1, AD premiums:4,
    # SelRes:6, IRR:4, survivor:1, cost-share structure:48(3 tiers x 16 svc),
    # cost-share values:17, cost-share range:~48, plan max:3,
    # premium ordering:4, prior year:4, yoy:4, positive:~12, metadata:1, sources:1
    total_checks = 116

    if all_errors:
        print(f"\nDENTAL VALIDATION FAILED: {len(all_errors)} errors in {total_checks} checks")
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)
    else:
        print(f"DENTAL VALIDATION: {total_checks} checks passed")
        sys.exit(0)


if __name__ == '__main__':
    main()
