#!/usr/bin/env python3
"""
Validation suite for TRICARE pharmacy costs (pharmacy_costs section of tricare-rates.json).
Part of the O&M CI validation pipeline.

Validates:
  - Structure: required keys, beneficiary categories, pharmacy types
  - Values: copay amounts match official CY 2026 TRICARE schedule (tricare.mil)
  - Range checks: all copays non-negative and within expected bounds
  - Cross-field consistency: YoY changes, non-network rules, frozen rates
  - NDAA FY2018 compliance: medically retired/survivor rates frozen at 2017 levels
"""

import json
import sys
from pathlib import Path
from typing import List


def load_tricare(filepath: str) -> dict:
    """Load and parse TRICARE rates JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_pharmacy_exists(data: dict) -> List[str]:
    """Check that pharmacy_costs section exists."""
    errors = []
    if 'pharmacy_costs' not in data:
        errors.append("CRITICAL: pharmacy_costs section missing from tricare-rates.json")
    return errors


def validate_pharmacy_structure(pc: dict) -> List[str]:
    """Validate required top-level keys in pharmacy_costs."""
    errors = []
    required_keys = [
        'formulary_categories', 'pharmacy_types',
        'active_duty_service_members', 'standard_beneficiaries',
        'medically_retired_and_adsm_survivors',
        'prior_year_copays_2025', 'yoy_change_2025_to_2026',
        'ndaa_fy2018_copay_schedule_end'
    ]
    for key in required_keys:
        if key not in pc:
            errors.append(f"pharmacy_costs: missing required key '{key}'")
    return errors


def validate_formulary_categories(pc: dict) -> List[str]:
    """Validate formulary category definitions."""
    errors = []
    cats = pc.get('formulary_categories', {})
    required = ['generic_formulary', 'brand_name_formulary', 'non_formulary', 'non_covered']
    for cat in required:
        if cat not in cats:
            errors.append(f"formulary_categories: missing '{cat}'")
        elif not isinstance(cats[cat], str) or len(cats[cat]) < 10:
            errors.append(f"formulary_categories: '{cat}' must be a descriptive string")
    return errors


def validate_pharmacy_types(pc: dict) -> List[str]:
    """Validate pharmacy type definitions."""
    errors = []
    types = pc.get('pharmacy_types', {})
    required = ['military', 'home_delivery', 'retail_network',
                 'non_network_domestic', 'non_network_overseas']
    for pt in required:
        if pt not in types:
            errors.append(f"pharmacy_types: missing '{pt}'")
    return errors


def validate_adsm_costs(pc: dict) -> List[str]:
    """Active duty service members pay $0 everywhere."""
    errors = []
    adsm = pc.get('active_duty_service_members', {})
    for pharmacy in ['military', 'home_delivery_90day', 'retail_network_30day']:
        section = adsm.get(pharmacy, {})
        for drug_type in ['generic', 'brand', 'non_formulary']:
            val = section.get(drug_type)
            if val is None:
                errors.append(f"ADSM {pharmacy}: missing '{drug_type}'")
            elif val != 0:
                errors.append(f"ADSM {pharmacy} {drug_type}: expected $0, got ${val}")
    return errors


def validate_prime_remote_costs(pc: dict) -> List[str]:
    """AD family Prime Remote in US pays $0 as of Feb 28, 2026."""
    errors = []
    pr = pc.get('active_duty_family_prime_remote_us', {})
    if not pr:
        errors.append("Missing active_duty_family_prime_remote_us section")
        return errors

    if pr.get('effective_date') != '2026-02-28':
        errors.append(f"Prime Remote effective date: expected 2026-02-28, got {pr.get('effective_date')}")

    for pharmacy in ['military', 'home_delivery_90day', 'retail_network_30day']:
        section = pr.get(pharmacy, {})
        for drug_type in ['generic', 'brand', 'non_formulary']:
            val = section.get(drug_type)
            if val is None:
                errors.append(f"Prime Remote {pharmacy}: missing '{drug_type}'")
            elif val != 0:
                errors.append(f"Prime Remote {pharmacy} {drug_type}: expected $0, got ${val}")
    return errors


def validate_standard_beneficiary_copays(pc: dict) -> List[str]:
    """Validate CY 2026 standard beneficiary copays against official schedule."""
    errors = []
    sb = pc.get('standard_beneficiaries', {})

    # Military pharmacy: $0
    mil = sb.get('military', {})
    for dt in ['generic', 'brand']:
        val = mil.get(dt)
        if val is None:
            errors.append(f"Standard military: missing '{dt}'")
        elif val != 0:
            errors.append(f"Standard military {dt}: expected $0, got ${val}")

    # Home delivery 90-day: generic $14, brand $44, non-formulary $85
    hd = sb.get('home_delivery_90day', {})
    expected_hd = {'generic': 14, 'brand': 44, 'non_formulary': 85}
    for drug_type, expected_val in expected_hd.items():
        actual = hd.get(drug_type)
        if actual is None:
            errors.append(f"Standard home_delivery: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Standard home_delivery {drug_type}: expected ${expected_val}, got ${actual}")

    # Retail network 30-day: generic $16, brand $48, non-formulary $85
    rn = sb.get('retail_network_30day', {})
    expected_rn = {'generic': 16, 'brand': 48, 'non_formulary': 85}
    for drug_type, expected_val in expected_rn.items():
        actual = rn.get(drug_type)
        if actual is None:
            errors.append(f"Standard retail_network: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Standard retail_network {drug_type}: expected ${expected_val}, got ${actual}")

    # Non-network domestic structure
    nnd = sb.get('non_network_domestic', {})
    if 'prime_enrollees' not in nnd:
        errors.append("Standard non_network_domestic: missing 'prime_enrollees'")
    else:
        pe = nnd['prime_enrollees']
        if pe.get('cost_share_pct') != 50:
            errors.append(f"Standard non-network Prime cost-share: expected 50%, got {pe.get('cost_share_pct')}%")

    if 'all_other_beneficiaries' not in nnd:
        errors.append("Standard non_network_domestic: missing 'all_other_beneficiaries'")
    else:
        aob = nnd['all_other_beneficiaries']
        if aob.get('formulary_minimum') != 48:
            errors.append(f"Standard non-network formulary min: expected $48, got ${aob.get('formulary_minimum')}")
        if aob.get('non_formulary_minimum') != 85:
            errors.append(f"Standard non-network non-formulary min: expected $85, got ${aob.get('non_formulary_minimum')}")

    return errors


def validate_medically_retired_copays(pc: dict) -> List[str]:
    """Validate NDAA FY2018 frozen copays for medically retired/ADSM survivors."""
    errors = []
    mr = pc.get('medically_retired_and_adsm_survivors', {})

    if 'authority' not in mr:
        errors.append("Medically retired: missing 'authority' field")
    elif 'NDAA' not in mr['authority'] or '702' not in mr['authority']:
        errors.append(f"Medically retired authority should reference NDAA FY2018 Sec 702: got '{mr['authority']}'")

    # Military: $0
    mil = mr.get('military', {})
    for dt in ['generic', 'brand']:
        val = mil.get(dt)
        if val is None:
            errors.append(f"Med-retired military: missing '{dt}'")
        elif val != 0:
            errors.append(f"Med-retired military {dt}: expected $0, got ${val}")

    # Home delivery 90-day: generic $0, brand $20, non-formulary $49
    hd = mr.get('home_delivery_90day', {})
    expected_hd = {'generic': 0, 'brand': 20, 'non_formulary': 49}
    for drug_type, expected_val in expected_hd.items():
        actual = hd.get(drug_type)
        if actual is None:
            errors.append(f"Med-retired home_delivery: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Med-retired home_delivery {drug_type}: expected ${expected_val}, got ${actual}")

    # Retail network 30-day: generic $10, brand $24, non-formulary $50
    rn = mr.get('retail_network_30day', {})
    expected_rn = {'generic': 10, 'brand': 24, 'non_formulary': 50}
    for drug_type, expected_val in expected_rn.items():
        actual = rn.get(drug_type)
        if actual is None:
            errors.append(f"Med-retired retail_network: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Med-retired retail_network {drug_type}: expected ${expected_val}, got ${actual}")

    # Non-network domestic - Prime POS deductible
    nnd = mr.get('non_network_domestic', {})
    pe = nnd.get('prime_enrollees', {})
    if pe.get('point_of_service_deductible_individual') != 300:
        errors.append(f"Med-retired POS deductible individual: expected $300, got ${pe.get('point_of_service_deductible_individual')}")
    if pe.get('point_of_service_deductible_family') != 600:
        errors.append(f"Med-retired POS deductible family: expected $600, got ${pe.get('point_of_service_deductible_family')}")

    return errors


def validate_prior_year_copays(pc: dict) -> List[str]:
    """Validate 2025 prior-year copays for YoY comparison."""
    errors = []
    py = pc.get('prior_year_copays_2025', {})

    hd = py.get('home_delivery_90day', {})
    expected_hd = {'generic': 13, 'brand': 38, 'non_formulary': 76}
    for drug_type, expected_val in expected_hd.items():
        actual = hd.get(drug_type)
        if actual is None:
            errors.append(f"Prior year home_delivery: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Prior year home_delivery {drug_type}: expected ${expected_val}, got ${actual}")

    rn = py.get('retail_network_30day', {})
    expected_rn = {'generic': 16, 'brand': 43, 'non_formulary': 76}
    for drug_type, expected_val in expected_rn.items():
        actual = rn.get(drug_type)
        if actual is None:
            errors.append(f"Prior year retail_network: missing '{drug_type}'")
        elif actual != expected_val:
            errors.append(f"Prior year retail_network {drug_type}: expected ${expected_val}, got ${actual}")

    return errors


def validate_yoy_changes(pc: dict) -> List[str]:
    """Cross-validate YoY percentage changes against actual 2025 vs 2026 values."""
    errors = []
    yoy = pc.get('yoy_change_2025_to_2026', {})
    py = pc.get('prior_year_copays_2025', {})
    sb = pc.get('standard_beneficiaries', {})

    checks = [
        ('home_delivery_generic_pct', py.get('home_delivery_90day', {}).get('generic'),
         sb.get('home_delivery_90day', {}).get('generic')),
        ('home_delivery_brand_pct', py.get('home_delivery_90day', {}).get('brand'),
         sb.get('home_delivery_90day', {}).get('brand')),
        ('home_delivery_non_formulary_pct', py.get('home_delivery_90day', {}).get('non_formulary'),
         sb.get('home_delivery_90day', {}).get('non_formulary')),
        ('retail_generic_pct', py.get('retail_network_30day', {}).get('generic'),
         sb.get('retail_network_30day', {}).get('generic')),
        ('retail_brand_pct', py.get('retail_network_30day', {}).get('brand'),
         sb.get('retail_network_30day', {}).get('brand')),
        ('retail_non_formulary_pct', py.get('retail_network_30day', {}).get('non_formulary'),
         sb.get('retail_network_30day', {}).get('non_formulary')),
    ]

    for key, old_val, new_val in checks:
        stated_pct = yoy.get(key)
        if stated_pct is None:
            errors.append(f"YoY: missing '{key}'")
            continue
        if old_val is None or new_val is None:
            continue
        if old_val == 0:
            continue
        computed_pct = round(((new_val - old_val) / old_val) * 100, 1)
        if abs(computed_pct - stated_pct) > 0.2:
            errors.append(f"YoY {key}: stated {stated_pct}% but computed {computed_pct}%")

    return errors


def validate_copay_ordering(pc: dict) -> List[str]:
    """Verify generic <= brand <= non-formulary for all beneficiary types."""
    errors = []

    categories = [
        ('standard_beneficiaries', 'home_delivery_90day'),
        ('standard_beneficiaries', 'retail_network_30day'),
        ('medically_retired_and_adsm_survivors', 'home_delivery_90day'),
        ('medically_retired_and_adsm_survivors', 'retail_network_30day'),
        ('prior_year_copays_2025', 'home_delivery_90day'),
        ('prior_year_copays_2025', 'retail_network_30day'),
    ]

    for cat_key, pharm_key in categories:
        section = pc.get(cat_key, {}).get(pharm_key, {})
        g = section.get('generic')
        b = section.get('brand')
        nf = section.get('non_formulary')
        if g is not None and b is not None and nf is not None:
            if not (g <= b <= nf):
                errors.append(f"Copay ordering violated in {cat_key}/{pharm_key}: "
                              f"generic=${g}, brand=${b}, non_formulary=${nf}")

    return errors


def validate_non_negative(pc: dict) -> List[str]:
    """All copay values must be non-negative."""
    errors = []

    def check_dict(d, path=""):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.startswith('_'):
                    continue
                check_dict(v, f"{path}/{k}")
        elif isinstance(d, (int, float)):
            if d < 0:
                errors.append(f"Negative value at {path}: {d}")

    check_dict(pc, "pharmacy_costs")
    return errors


def validate_ndaa_end_date(pc: dict) -> List[str]:
    """NDAA FY2018 copay schedule ends Dec 31, 2027."""
    errors = []
    end = pc.get('ndaa_fy2018_copay_schedule_end')
    if end != '2027-12-31':
        errors.append(f"NDAA end date: expected '2027-12-31', got '{end}'")
    return errors


def validate_frozen_rates_lower(pc: dict) -> List[str]:
    """Medically retired/survivor rates should be <= standard rates (frozen at 2017)."""
    errors = []
    sb = pc.get('standard_beneficiaries', {})
    mr = pc.get('medically_retired_and_adsm_survivors', {})

    for pharm in ['home_delivery_90day', 'retail_network_30day']:
        sb_sec = sb.get(pharm, {})
        mr_sec = mr.get(pharm, {})
        for dt in ['generic', 'brand', 'non_formulary']:
            sb_val = sb_sec.get(dt)
            mr_val = mr_sec.get(dt)
            if sb_val is not None and mr_val is not None:
                if mr_val > sb_val:
                    errors.append(f"Frozen rate exceeds standard rate at {pharm}/{dt}: "
                                  f"frozen=${mr_val} > standard=${sb_val}")
    return errors


def validate_metadata_version(data: dict) -> List[str]:
    """Metadata version should be 2026.2 after pharmacy addition."""
    errors = []
    version = data.get('_metadata', {}).get('version', '')
    # Version must be 2026.2 or later (pharmacy was added in 2026.2)
    if not version.startswith('2026.') or float(version.split('.')[1]) < 2:
        errors.append(f"Metadata version: expected '2026.2' or later, got '{version}'")
    return errors


def validate_data_sources(data: dict) -> List[str]:
    """Pharmacy source URL should be in data_sources."""
    errors = []
    sources = data.get('data_sources', [])
    pharmacy_url = 'https://tricare.mil/Costs/PharmacyCosts'
    if pharmacy_url not in sources:
        errors.append(f"data_sources: missing pharmacy URL '{pharmacy_url}'")
    return errors


def main():
    """Run all pharmacy validation checks."""
    repo_root = Path(__file__).parent.parent
    filepath = repo_root / 'federal' / 'healthcare' / 'tricare-rates.json'

    if not filepath.exists():
        print("FAIL: tricare-rates.json not found")
        sys.exit(1)

    data = load_tricare(str(filepath))
    all_errors = []
    check_count = 0

    # Check 1: pharmacy section exists
    errs = validate_pharmacy_exists(data)
    check_count += 1
    all_errors.extend(errs)
    if errs:
        print(f"CRITICAL: {errs[0]}")
        print(f"\n{'='*60}")
        print(f"PHARMACY VALIDATION: {check_count} checks, {len(all_errors)} FAILURES")
        sys.exit(1)

    pc = data['pharmacy_costs']

    # Run all validation functions
    validators = [
        ("Structure", validate_pharmacy_structure),
        ("Formulary categories", validate_formulary_categories),
        ("Pharmacy types", validate_pharmacy_types),
        ("ADSM costs ($0)", validate_adsm_costs),
        ("Prime Remote costs ($0)", validate_prime_remote_costs),
        ("Standard beneficiary copays", validate_standard_beneficiary_copays),
        ("Medically retired copays", validate_medically_retired_copays),
        ("Prior year 2025 copays", validate_prior_year_copays),
        ("YoY change cross-validation", validate_yoy_changes),
        ("Copay ordering (generic<=brand<=NF)", validate_copay_ordering),
        ("Non-negative values", validate_non_negative),
        ("NDAA end date", validate_ndaa_end_date),
        ("Frozen rates <= standard rates", validate_frozen_rates_lower),
    ]

    for name, validator in validators:
        errs = validator(pc)
        check_count += len(errs) if errs else 1
        # Count individual checks within each validator
        all_errors.extend(errs)

    # File-level validators
    file_validators = [
        ("Metadata version", validate_metadata_version),
        ("Data sources", validate_data_sources),
    ]
    for name, validator in file_validators:
        errs = validator(data)
        check_count += 1
        all_errors.extend(errs)

    # Count actual discrete checks performed
    # Structure: 8 keys, formulary: 4, pharmacy types: 5, ADSM: 9, Prime Remote: 10,
    # Standard: 14, Med-retired: 14, Prior year: 6, YoY: 6, Ordering: 6, Non-neg: 1,
    # NDAA end: 1, Frozen rates: 6, Metadata: 1, Sources: 1
    total_checks = 92  # manual count of discrete assertions

    if all_errors:
        print(f"\n{'='*60}")
        print(f"PHARMACY VALIDATION FAILED: {len(all_errors)} errors in {total_checks} checks")
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)
    else:
        print(f"PHARMACY VALIDATION: {total_checks} checks passed")
        sys.exit(0)


if __name__ == '__main__':
    main()
