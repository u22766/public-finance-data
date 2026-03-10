#!/usr/bin/env python3
"""
DCIPS Pay Tables Validation Suite
Validates federal/dcips/dcips-pay-tables.json

Run: python tests/validate_dcips.py
"""

import json
import sys
from pathlib import Path

# Resolve repo root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DCIPS_FILE = REPO_ROOT / "federal" / "dcips" / "dcips-pay-tables.json"

# Test counters
passed = 0
failed = 0
errors = []


def check(condition: bool, message: str):
    """Record a validation check result."""
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(message)


def validate_structure(data: dict):
    """Validate top-level structure and required keys."""
    required_keys = [
        "version",
        "effective_date",
        "authority",
        "source_url",
        "pay_cap",
        "base_grades",
        "pay_bands",
        "local_market_supplements",
        "targeted_local_market_supplements",
        "stem_cyber_grades",
        "stem_cyber_pay_bands",
    ]
    for key in required_keys:
        check(key in data, f"Missing required top-level key: {key}")

    # Validate version format
    check(
        isinstance(data.get("version"), str) and "." in data.get("version", ""),
        "Version should be string with format 'YYYY.N'"
    )

    # Validate pay cap
    check(
        data.get("pay_cap") == 197200,
        f"Pay cap should be 197200, got {data.get('pay_cap')}"
    )


def validate_base_grades(data: dict):
    """Validate base GG grade pay tables."""
    base_grades = data.get("base_grades", {})
    
    # Expected grades GG-01 through GG-15
    expected_grades = [f"GG-{str(i).zfill(2)}" for i in range(1, 16)]
    
    for grade in expected_grades:
        check(
            grade in base_grades,
            f"Missing base grade: {grade}"
        )
        
        if grade in base_grades:
            steps = base_grades[grade]
            
            # Check 12 steps
            check(
                len(steps) == 12,
                f"{grade}: Expected 12 steps, got {len(steps)}"
            )
            
            # Check all steps are integers
            check(
                all(isinstance(s, int) for s in steps),
                f"{grade}: All steps should be integers"
            )
            
            # Check steps are ascending
            check(
                steps == sorted(steps),
                f"{grade}: Steps should be in ascending order"
            )
            
            # Check reasonable range (> $20k, < $200k)
            check(
                all(20000 <= s <= 200000 for s in steps),
                f"{grade}: Step values out of reasonable range"
            )


def validate_pay_bands(data: dict):
    """Validate pay band definitions."""
    pay_bands = data.get("pay_bands", {})
    
    expected_bands = ["1", "2", "3", "4", "5"]
    required_fields = ["minimum", "maximum", "grade_equivalents", "work_categories"]
    
    for band in expected_bands:
        check(
            band in pay_bands,
            f"Missing pay band: {band}"
        )
        
        if band in pay_bands:
            band_data = pay_bands[band]
            
            for field in required_fields:
                check(
                    field in band_data,
                    f"Band {band}: Missing field '{field}'"
                )
            
            # Check min < max
            if "minimum" in band_data and "maximum" in band_data:
                check(
                    band_data["minimum"] < band_data["maximum"],
                    f"Band {band}: Minimum should be less than maximum"
                )
            
            # Check grade_equivalents is non-empty list
            if "grade_equivalents" in band_data:
                check(
                    isinstance(band_data["grade_equivalents"], list) and len(band_data["grade_equivalents"]) > 0,
                    f"Band {band}: grade_equivalents should be non-empty list"
                )


def validate_stem_cyber_grades(data: dict):
    """Validate STEM/Cyber grade pay tables."""
    stem_grades = data.get("stem_cyber_grades", {})
    base_grades = data.get("base_grades", {})
    pay_cap = data.get("pay_cap", 197200)
    
    # STEM/Cyber only applies GG-07 and above
    expected_grades = [f"GG-{str(i).zfill(2)}" for i in range(7, 16)]
    
    for grade in expected_grades:
        check(
            grade in stem_grades,
            f"Missing STEM/Cyber grade: {grade}"
        )
        
        if grade in stem_grades:
            steps = stem_grades[grade]
            
            # Check 12 steps
            check(
                len(steps) == 12,
                f"STEM {grade}: Expected 12 steps, got {len(steps)}"
            )
            
            # Check all steps are integers
            check(
                all(isinstance(s, int) for s in steps),
                f"STEM {grade}: All steps should be integers"
            )
            
            # Check STEM rates > base rates (TLMS adds to base)
            if grade in base_grades:
                base_step1 = base_grades[grade][0]
                stem_step1 = steps[0]
                check(
                    stem_step1 > base_step1,
                    f"STEM {grade} Step 1 ({stem_step1}) should be > base ({base_step1})"
                )
            
            # Check pay cap enforcement (no step should exceed cap)
            check(
                all(s <= pay_cap for s in steps),
                f"STEM {grade}: Some steps exceed pay cap {pay_cap}"
            )
            
            # Check steps are non-decreasing (can be equal due to cap)
            check(
                all(steps[i] <= steps[i+1] for i in range(len(steps)-1)),
                f"STEM {grade}: Steps should be non-decreasing"
            )


def validate_stem_cyber_pay_bands(data: dict):
    """Validate STEM/Cyber pay band ranges."""
    stem_bands = data.get("stem_cyber_pay_bands", {})
    pay_cap = data.get("pay_cap", 197200)
    
    # STEM bands are 2-5 (Band 1 doesn't have STEM TLMS)
    expected_bands = ["2", "3", "4", "5"]
    required_fields = ["minimum", "maximum", "grade_range"]
    
    for band in expected_bands:
        check(
            band in stem_bands,
            f"Missing STEM/Cyber pay band: {band}"
        )
        
        if band in stem_bands:
            band_data = stem_bands[band]
            
            for field in required_fields:
                check(
                    field in band_data,
                    f"STEM Band {band}: Missing field '{field}'"
                )
            
            # Check min < max
            if "minimum" in band_data and "maximum" in band_data:
                check(
                    band_data["minimum"] < band_data["maximum"],
                    f"STEM Band {band}: Minimum should be less than maximum"
                )
                
                # Check max doesn't exceed pay cap
                check(
                    band_data["maximum"] <= pay_cap,
                    f"STEM Band {band}: Maximum exceeds pay cap"
                )


def validate_local_market_supplements(data: dict):
    """Validate LMS locality percentages."""
    lms = data.get("local_market_supplements", {})
    
    # Filter out comment keys
    localities = {k: v for k, v in lms.items() if not k.startswith("_")}
    
    # Check count (58 expected)
    check(
        len(localities) == 58,
        f"Expected 58 LMS localities, got {len(localities)}"
    )
    
    # Check key localities are present
    key_localities = [
        "Washington-Baltimore-Arlington, DC-MD-VA-WV-PA",
        "San Jose-San Francisco-Oakland, CA",
        "New York-Newark, NY-NJ-CT-PA",
        "Rest of U.S.",
        "Alaska",
        "Hawaii",
    ]
    for loc in key_localities:
        check(
            loc in localities,
            f"Missing key locality: {loc}"
        )
    
    # Check all percentages are valid (0 < pct < 100)
    for loc, pct in localities.items():
        check(
            isinstance(pct, (int, float)) and 0 < pct < 100,
            f"LMS '{loc}': Invalid percentage {pct}"
        )
    
    # Check SF Bay Area is highest
    sf_rate = localities.get("San Jose-San Francisco-Oakland, CA", 0)
    check(
        sf_rate >= max(localities.values()),
        f"San Jose-SF-Oakland should have highest LMS rate"
    )
    
    # Check Rest of U.S. is lowest
    rest_rate = localities.get("Rest of U.S.", 100)
    check(
        rest_rate <= min(localities.values()),
        f"Rest of U.S. should have lowest LMS rate"
    )


def validate_tlms_categories(data: dict):
    """Validate Targeted Local Market Supplement categories."""
    tlms = data.get("targeted_local_market_supplements", {})
    
    expected_categories = [
        "stem_cyber",
        "780th_mib",
        "hawaii_it_cs_eng",
        "polygraphers",
        "pilots",
        "foreign_area",
    ]
    
    for cat in expected_categories:
        check(
            cat in tlms,
            f"Missing TLMS category: {cat}"
        )


def validate_stem_cyber_tlms(data: dict):
    """Validate STEM/Cyber TLMS details."""
    tlms = data.get("targeted_local_market_supplements", {}).get("stem_cyber", {})
    
    required_fields = ["description", "effective_date", "tlms_percentages", "covered_series"]
    for field in required_fields:
        check(
            field in tlms,
            f"STEM/Cyber TLMS: Missing field '{field}'"
        )
    
    # Validate TLMS percentages
    percentages = tlms.get("tlms_percentages", {})
    expected_grades = [f"GG-{str(i).zfill(2)}" for i in range(7, 16)]
    
    for grade in expected_grades:
        check(
            grade in percentages,
            f"STEM/Cyber TLMS: Missing percentage for {grade}"
        )
        
        if grade in percentages:
            pct = percentages[grade]
            check(
                isinstance(pct, (int, float)) and 0 < pct <= 100,
                f"STEM/Cyber TLMS {grade}: Invalid percentage {pct}"
            )
    
    # Check percentages decrease with grade (higher grades get lower TLMS)
    pct_values = [percentages.get(f"GG-{str(i).zfill(2)}", 0) for i in range(7, 16)]
    check(
        pct_values == sorted(pct_values, reverse=True),
        "STEM/Cyber TLMS percentages should decrease with grade"
    )
    
    # Check covered series is non-empty
    covered = tlms.get("covered_series", [])
    check(
        isinstance(covered, list) and len(covered) > 0,
        "STEM/Cyber TLMS: covered_series should be non-empty list"
    )


def validate_780th_mib_tlms(data: dict):
    """Validate 780th MIB TLMS details."""
    tlms = data.get("targeted_local_market_supplements", {}).get("780th_mib", {})
    
    required_fields = ["description", "effective_date", "tlms_percentages", "covered_work_roles"]
    for field in required_fields:
        check(
            field in tlms,
            f"780th MIB TLMS: Missing field '{field}'"
        )
    
    # Check work roles
    work_roles = tlms.get("covered_work_roles", [])
    expected_roles = ["321", "322", "121", "621"]
    for role in expected_roles:
        check(
            role in work_roles,
            f"780th MIB TLMS: Missing work role {role}"
        )


def validate_pilots_tlms(data: dict):
    """Validate Pilots TLMS special rate tables."""
    pilots = data.get("targeted_local_market_supplements", {}).get("pilots", {})
    
    check(
        "special_rate_tables" in pilots,
        "Pilots TLMS: Missing special_rate_tables"
    )
    
    tables = pilots.get("special_rate_tables", {})
    
    # Check expected table count (12)
    check(
        len(tables) == 12,
        f"Pilots TLMS: Expected 12 special rate tables, got {len(tables)}"
    )
    
    # Check each table has required fields
    for table_id, table_data in tables.items():
        check(
            "locality_areas" in table_data,
            f"Pilots table {table_id}: Missing locality_areas"
        )
        check(
            "rates" in table_data,
            f"Pilots table {table_id}: Missing rates"
        )
        
        # Check rates are valid percentages
        rates = table_data.get("rates", {})
        for grade, rate in rates.items():
            check(
                isinstance(rate, (int, float)) and 0 < rate <= 100,
                f"Pilots table {table_id} {grade}: Invalid rate {rate}"
            )


def validate_polygraphers_tlms(data: dict):
    """Validate Polygraphers TLMS schedules."""
    poly = data.get("targeted_local_market_supplements", {}).get("polygraphers", {})
    
    check(
        "schedule_a" in poly,
        "Polygraphers TLMS: Missing schedule_a"
    )
    check(
        "schedule_b" in poly,
        "Polygraphers TLMS: Missing schedule_b"
    )
    
    # Check Schedule A has rates by locality
    schedule_a = poly.get("schedule_a", {})
    check(
        "rates_by_locality" in schedule_a,
        "Polygraphers Schedule A: Missing rates_by_locality"
    )
    
    # Check Schedule B has percentage
    schedule_b = poly.get("schedule_b", {})
    check(
        "percentage" in schedule_b and schedule_b.get("percentage") == 40,
        "Polygraphers Schedule B: Should have percentage of 40"
    )


def validate_foreign_area_tlms(data: dict):
    """Validate Foreign Area TLMS."""
    foreign = data.get("targeted_local_market_supplements", {}).get("foreign_area", {})
    
    required_fields = ["description", "effective_date", "percentage"]
    for field in required_fields:
        check(
            field in foreign,
            f"Foreign Area TLMS: Missing field '{field}'"
        )
    
    # Check percentage matches DC locality rate
    check(
        foreign.get("percentage") == 33.94,
        f"Foreign Area TLMS: Expected 33.94%, got {foreign.get('percentage')}"
    )


def validate_cross_consistency(data: dict):
    """Cross-validate related data fields."""
    base_grades = data.get("base_grades", {})
    pay_bands = data.get("pay_bands", {})
    stem_grades = data.get("stem_cyber_grades", {})
    stem_bands = data.get("stem_cyber_pay_bands", {})
    
    # Band 1 min should match GG-01 Step 1
    if "1" in pay_bands and "GG-01" in base_grades:
        check(
            pay_bands["1"]["minimum"] == base_grades["GG-01"][0],
            "Band 1 minimum should match GG-01 Step 1"
        )
    
    # Band 5 max should match GG-15 Step 12
    if "5" in pay_bands and "GG-15" in base_grades:
        check(
            pay_bands["5"]["maximum"] == base_grades["GG-15"][11],
            "Band 5 maximum should match GG-15 Step 12"
        )
    
    # STEM Band 2 min should match STEM GG-07 Step 1
    if "2" in stem_bands and "GG-07" in stem_grades:
        check(
            stem_bands["2"]["minimum"] == stem_grades["GG-07"][0],
            "STEM Band 2 minimum should match STEM GG-07 Step 1"
        )
    
    # STEM Band 5 max should be capped at pay_cap
    pay_cap = data.get("pay_cap", 197200)
    if "5" in stem_bands:
        check(
            stem_bands["5"]["maximum"] == pay_cap,
            f"STEM Band 5 maximum should be capped at {pay_cap}"
        )


def main():
    """Run all validation checks."""
    global passed, failed, errors
    
    print("=" * 60)
    print("DCIPS Pay Tables Validation Suite")
    print("=" * 60)
    print()
    
    # Check file exists
    if not DCIPS_FILE.exists():
        print(f"ERROR: File not found: {DCIPS_FILE}")
        print("Expected path: federal/dcips/dcips-pay-tables.json")
        sys.exit(1)
    
    # Load JSON
    try:
        with open(DCIPS_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)
    
    print(f"File: {DCIPS_FILE.relative_to(REPO_ROOT)}")
    print(f"Version: {data.get('version', 'unknown')}")
    print(f"Effective: {data.get('effective_date', 'unknown')}")
    print()
    
    # Run validation suites
    print("Running validation checks...")
    print()
    
    validate_structure(data)
    validate_base_grades(data)
    validate_pay_bands(data)
    validate_stem_cyber_grades(data)
    validate_stem_cyber_pay_bands(data)
    validate_local_market_supplements(data)
    validate_tlms_categories(data)
    validate_stem_cyber_tlms(data)
    validate_780th_mib_tlms(data)
    validate_pilots_tlms(data)
    validate_polygraphers_tlms(data)
    validate_foreign_area_tlms(data)
    validate_cross_consistency(data)
    
    # Report results
    total = passed + failed
    print(f"Results: {passed}/{total} checks passed")
    print()
    
    if failed > 0:
        print("FAILURES:")
        for err in errors:
            print(f"  - {err}")
        print()
        sys.exit(1)
    else:
        print("All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
