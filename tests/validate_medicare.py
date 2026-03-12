#!/usr/bin/env python3
"""
Validation suite for medicare-rates.json
Part of the O&M CI validation pipeline.
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

def load_medicare_rates(filepath: str) -> dict:
    """Load and parse Medicare rates JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_structure(data: dict) -> List[str]:
    """Validate required top-level structure."""
    errors = []
    required_keys = ['version', 'effective_date', 'part_b', 'part_d', 'part_a', 'sources']
    
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required top-level key: {key}")
    
    return errors

def validate_part_b(data: dict) -> List[str]:
    """Validate Part B structure and values."""
    errors = []
    
    if 'part_b' not in data:
        return ["Part B section missing"]
    
    pb = data['part_b']
    
    # Required fields
    required = ['standard_premium_monthly', 'annual_deductible', 'irmaa']
    for key in required:
        if key not in pb:
            errors.append(f"Part B: missing {key}")
    
    # Value range checks
    if 'standard_premium_monthly' in pb:
        premium = pb['standard_premium_monthly']
        if not (100 <= premium <= 500):
            errors.append(f"Part B premium out of expected range: ${premium}")
    
    if 'annual_deductible' in pb:
        ded = pb['annual_deductible']
        if not (100 <= ded <= 500):
            errors.append(f"Part B deductible out of expected range: ${ded}")
    
    # IRMAA bracket validation
    if 'irmaa' in pb:
        irmaa = pb['irmaa']
        for bracket_type in ['single_filer_brackets', 'joint_filer_brackets', 'married_filing_separately_brackets']:
            if bracket_type not in irmaa:
                errors.append(f"Part B IRMAA: missing {bracket_type}")
                continue
            
            brackets = irmaa[bracket_type]
            if len(brackets) < 3:
                errors.append(f"Part B IRMAA {bracket_type}: insufficient brackets")
            
            # Check bracket ordering
            prev_min = -1
            for b in brackets:
                if 'magi_min' not in b:
                    errors.append(f"Part B IRMAA: bracket missing magi_min")
                    continue
                if b['magi_min'] <= prev_min:
                    errors.append(f"Part B IRMAA: brackets not in ascending order")
                prev_min = b['magi_min']
                
                # Check IRMAA amount is non-negative
                if 'irmaa_amount' in b and b['irmaa_amount'] < 0:
                    errors.append(f"Part B IRMAA: negative irmaa_amount in bracket {b.get('bracket', '?')}")
                
                # Check total premium calculation
                if 'total_premium' in b and 'irmaa_amount' in b:
                    expected = pb['standard_premium_monthly'] + b['irmaa_amount']
                    if abs(b['total_premium'] - expected) > 0.01:
                        errors.append(f"Part B IRMAA bracket {b.get('bracket', '?')}: total_premium mismatch")
    
    return errors

def validate_part_d(data: dict) -> List[str]:
    """Validate Part D structure and values."""
    errors = []
    
    if 'part_d' not in data:
        return ["Part D section missing"]
    
    pd = data['part_d']
    
    # IRMAA bracket validation
    if 'irmaa' not in pd:
        errors.append("Part D: missing irmaa section")
    else:
        irmaa = pd['irmaa']
        for bracket_type in ['single_filer_brackets', 'joint_filer_brackets', 'married_filing_separately_brackets']:
            if bracket_type not in irmaa:
                errors.append(f"Part D IRMAA: missing {bracket_type}")
                continue
            
            brackets = irmaa[bracket_type]
            
            # Check bracket count matches Part B
            if 'part_b' in data and 'irmaa' in data['part_b']:
                pb_count = len(data['part_b']['irmaa'].get(bracket_type, []))
                pd_count = len(brackets)
                if pb_count != pd_count:
                    errors.append(f"Part D IRMAA {bracket_type}: bracket count ({pd_count}) differs from Part B ({pb_count})")
            
            # Check IRMAA amounts
            for b in brackets:
                if 'irmaa_amount' in b and b['irmaa_amount'] < 0:
                    errors.append(f"Part D IRMAA: negative irmaa_amount")
    
    return errors

def validate_part_a(data: dict) -> List[str]:
    """Validate Part A structure and values."""
    errors = []
    
    if 'part_a' not in data:
        return ["Part A section missing"]
    
    pa = data['part_a']
    
    # Premiums
    if 'premiums' not in pa:
        errors.append("Part A: missing premiums section")
    else:
        prems = pa['premiums']
        if 'full_premium_monthly' in prems and 'reduced_premium_monthly' in prems:
            if prems['reduced_premium_monthly'] >= prems['full_premium_monthly']:
                errors.append("Part A: reduced premium should be less than full premium")
    
    # Hospital costs
    if 'inpatient_hospital' not in pa:
        errors.append("Part A: missing inpatient_hospital section")
    else:
        hosp = pa['inpatient_hospital']
        if 'deductible_per_benefit_period' in hosp:
            ded = hosp['deductible_per_benefit_period']
            if not (1000 <= ded <= 3000):
                errors.append(f"Part A hospital deductible out of expected range: ${ded}")
        
        # Coinsurance ordering check
        if 'coinsurance_days_61_90' in hosp and 'coinsurance_lifetime_reserve_days' in hosp:
            if hosp['coinsurance_lifetime_reserve_days'] <= hosp['coinsurance_days_61_90']:
                errors.append("Part A: lifetime reserve coinsurance should exceed days 61-90 coinsurance")
    
    return errors

def validate_irmaa_consistency(data: dict) -> List[str]:
    """Validate IRMAA bracket consistency between Part B and Part D."""
    errors = []
    
    if 'part_b' not in data or 'part_d' not in data:
        return errors
    
    pb_irmaa = data['part_b'].get('irmaa', {})
    pd_irmaa = data['part_d'].get('irmaa', {})
    
    for bracket_type in ['single_filer_brackets', 'joint_filer_brackets']:
        pb_brackets = pb_irmaa.get(bracket_type, [])
        pd_brackets = pd_irmaa.get(bracket_type, [])
        
        for pb, pd in zip(pb_brackets, pd_brackets):
            # MAGI thresholds should match
            if pb.get('magi_min') != pd.get('magi_min'):
                errors.append(f"IRMAA {bracket_type}: magi_min mismatch between Part B and Part D")
            if pb.get('magi_max') != pd.get('magi_max'):
                errors.append(f"IRMAA {bracket_type}: magi_max mismatch between Part B and Part D")
    
    return errors

def validate_premium_history(data: dict) -> List[str]:
    """Validate premium history section."""
    errors = []
    
    if 'premium_history' not in data:
        return ["Premium history section missing"]
    
    history = data['premium_history']
    if 'years' not in history:
        return ["Premium history: missing years array"]
    
    years = history['years']
    
    # Check for current year
    year_list = [y['year'] for y in years]
    effective_year = int(data.get('effective_date', '2026')[:4])
    
    if effective_year not in year_list:
        errors.append(f"Premium history: missing current year {effective_year}")
    
    # Check ordering
    for i in range(1, len(years)):
        if years[i]['year'] <= years[i-1]['year']:
            errors.append("Premium history: years not in ascending order")
            break
    
    # Check for required fields in each year
    for y in years:
        if 'year' not in y:
            errors.append("Premium history: entry missing year")
        if 'standard_premium' not in y:
            errors.append(f"Premium history: year {y.get('year', '?')} missing standard_premium")
    
    return errors

def validate_sources(data: dict) -> List[str]:
    """Validate sources section."""
    errors = []
    
    if 'sources' not in data:
        return ["Sources section missing"]
    
    sources = data['sources']
    if len(sources) == 0:
        errors.append("Sources: no sources listed")
    
    for i, src in enumerate(sources):
        if 'url' not in src:
            errors.append(f"Source {i+1}: missing url")
        if 'name' not in src:
            errors.append(f"Source {i+1}: missing name")
    
    return errors

def run_validation(filepath: str) -> Tuple[int, int]:
    """Run all validation checks and return (passed, failed) counts."""
    data = load_medicare_rates(filepath)
    
    all_checks = [
        ("Structure validation", validate_structure),
        ("Part B validation", validate_part_b),
        ("Part D validation", validate_part_d),
        ("Part A validation", validate_part_a),
        ("IRMAA consistency", validate_irmaa_consistency),
        ("Premium history", validate_premium_history),
        ("Sources validation", validate_sources),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for check_name, check_func in all_checks:
        errors = check_func(data)
        if errors:
            print(f"❌ {check_name}:")
            for err in errors:
                print(f"   - {err}")
                total_failed += 1
        else:
            print(f"✅ {check_name}")
            total_passed += 1
    
    return total_passed, total_failed

def main():
    """Main entry point."""
    # Default path - adjust for repo structure
    default_path = "federal/healthcare/medicare-rates.json"
    
    filepath = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    
    print(f"Validating: {filepath}")
    print("=" * 50)
    
    try:
        passed, failed = run_validation(filepath)
        print("=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
        else:
            print("\n✅ All Medicare rates validation checks passed!")
            sys.exit(0)
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
