#!/usr/bin/env python3
"""
Validation suite for Foreign Service pay tables.
Tests: federal/foreign-service-pay-tables.json
Session 56: Initial build — 11 years (2016-2026), 9 grades, 14 steps.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FS_FILE = os.path.join(REPO_ROOT, "federal", "foreign-service-pay-tables.json")
MANIFEST_FILE = os.path.join(REPO_ROOT, "manifest.json")

passed = 0
failed = 0
errors = []


def check(condition, description):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(description)
        print(f"  FAIL: {description}")


def main():
    global passed, failed

    print("=" * 60)
    print("Validating: federal/foreign-service-pay-tables.json")
    print("=" * 60)

    # --- File existence ---
    check(os.path.isfile(FS_FILE), "foreign-service-pay-tables.json exists")
    if not os.path.isfile(FS_FILE):
        print("  SKIP: File not found")
        sys.exit(1)

    with open(FS_FILE) as f:
        data = json.load(f)

    # === METADATA ===
    print("\n=== Metadata ===")
    meta = data.get("_metadata", {})
    check("version" in meta, "version field present")
    check(meta.get("schema_version") == "2.2", f"schema_version is 2.2 (got {meta.get('schema_version')})")
    check("sources" in meta and len(meta["sources"]) >= 3, "at least 3 sources listed")
    check("description" in meta, "description present")
    check("update_frequency" in meta, "update_frequency present")
    check("_notes" in meta and len(meta["_notes"]) >= 5, "at least 5 notes")

    # === STRUCTURE ===
    print("\n=== Structure ===")
    grades = data.get("grades", [])
    steps = data.get("steps", [])
    check(len(grades) == 9, f"9 grades (got {len(grades)})")
    check(grades[0] == "FP-1" and grades[-1] == "FP-9", "grades range FP-1 to FP-9")
    check(len(steps) == 14, f"14 steps (got {len(steps)})")
    check(steps[0] == 1 and steps[-1] == 14, "steps range 1-14")

    # GS equivalency
    gs_equiv = data.get("gs_equivalency", {})
    check(len(gs_equiv) == 9, f"9 GS equivalency mappings (got {len(gs_equiv)})")
    check(gs_equiv.get("FP-1") == "GS-15", "FP-1 maps to GS-15")
    check(gs_equiv.get("FP-4") == "GS-12", "FP-4 maps to GS-12")

    # Step progression
    sp = data.get("step_progression", {})
    check("steps_1_to_4" in sp, "step progression documented")

    # === PAY RAISE HISTORY ===
    print("\n=== Pay Raise History ===")
    raises = data.get("pay_raise_history", [])
    check(len(raises) >= 10, f"at least 10 raise entries (got {len(raises)})")
    
    raise_by_year = {r["year"]: r["base_raise_pct"] for r in raises}
    # Verify known raise values
    check(raise_by_year.get(2017) == 1.0, f"2017 raise is 1.0% (got {raise_by_year.get(2017)})")
    check(raise_by_year.get(2020) == 2.6, f"2020 base raise is 2.6% (got {raise_by_year.get(2020)})")
    check(raise_by_year.get(2023) == 4.1, f"2023 base raise is 4.1% (got {raise_by_year.get(2023)})")
    check(raise_by_year.get(2024) == 4.7, f"2024 base raise is 4.7% (got {raise_by_year.get(2024)})")
    check(raise_by_year.get(2026) == 1.0, f"2026 raise is 1.0% (got {raise_by_year.get(2026)})")

    # All raises should be positive and reasonable
    for r in raises:
        check(0 < r["base_raise_pct"] <= 10, f"{r['year']} raise {r['base_raise_pct']}% is in 0-10% range")

    # === TABLES ===
    print("\n=== Pay Tables ===")
    tables = data.get("tables", {})
    expected_years = [str(y) for y in range(2016, 2027)]
    check(len(tables) >= 11, f"at least 11 years of tables (got {len(tables)})")

    for year_str in expected_years:
        check(year_str in tables, f"year {year_str} present in tables")

    # Validate each year's table structure and values
    for year_str in expected_years:
        if year_str not in tables:
            continue
        year_data = tables[year_str]
        rates = year_data.get("rates", {})

        # All 9 grades present
        for grade in ["FP-1","FP-2","FP-3","FP-4","FP-5","FP-6","FP-7","FP-8","FP-9"]:
            check(grade in rates, f"{year_str}: {grade} present")
            if grade not in rates:
                continue

            grade_rates = rates[grade]
            # All 14 steps present
            check(len(grade_rates) == 14, f"{year_str}/{grade}: 14 steps (got {len(grade_rates)})")

            # All values are positive integers
            for step_key, val in grade_rates.items():
                check(isinstance(val, int) and val > 0, f"{year_str}/{grade}/Step-{step_key}: positive int (got {val})")

    # === KNOWN VALUE VERIFICATION ===
    print("\n=== Known Value Verification ===")

    # 2017 anchor values (from official State Dept PDF)
    t2017 = tables.get("2017", {}).get("rates", {})
    check(t2017.get("FP-1", {}).get("1") == 103672, f"2017 FP-1/S1 = $103,672 (got {t2017.get('FP-1', {}).get('1')})")
    check(t2017.get("FP-5", {}).get("1") == 44693, f"2017 FP-5/S1 = $44,693 (got {t2017.get('FP-5', {}).get('1')})")
    check(t2017.get("FP-9", {}).get("14") == 41919, f"2017 FP-9/S14 = $41,919 (got {t2017.get('FP-9', {}).get('14')})")
    check(t2017.get("FP-1", {}).get("10") == 134776, f"2017 FP-1/S10 capped = $134,776")

    # 2024 Plumbook verification
    t2024 = tables.get("2024", {}).get("rates", {})
    fp1_s1_2024 = t2024.get("FP-1", {}).get("1", 0)
    check(abs(fp1_s1_2024 - 123041) <= 2, f"2024 FP-1/S1 = ~$123,041 (got ${fp1_s1_2024:,})")
    fp5_s1_2024 = t2024.get("FP-5", {}).get("1", 0)
    check(abs(fp5_s1_2024 - 53043) <= 2, f"2024 FP-5/S1 = ~$53,043 (got ${fp5_s1_2024:,})")
    fp9_s14_2024 = t2024.get("FP-9", {}).get("14", 0)
    check(abs(fp9_s14_2024 - 49751) <= 2, f"2024 FP-9/S14 = ~$49,751 (got ${fp9_s14_2024:,})")
    fp1_cap_2024 = t2024.get("FP-1", {}).get("10", 0)
    check(abs(fp1_cap_2024 - 159950) <= 2, f"2024 FP-1/S10 cap = ~$159,950 (got ${fp1_cap_2024:,})")

    # 2026 article verification (FP-5/Step-7 = $65,058)
    t2026 = tables.get("2026", {}).get("rates", {})
    fp5_s7_2026 = t2026.get("FP-5", {}).get("7", 0)
    check(abs(fp5_s7_2026 - 65058) <= 2, f"2026 FP-5/S7 = ~$65,058 (got ${fp5_s7_2026:,})")

    # === MONOTONICITY CHECKS ===
    print("\n=== Monotonicity Checks ===")

    for year_str in expected_years:
        if year_str not in tables:
            continue
        rates = tables[year_str].get("rates", {})

        # Within each grade, steps should be monotonically increasing (or equal for capped FP-1)
        for grade in ["FP-1","FP-2","FP-3","FP-4","FP-5","FP-6","FP-7","FP-8","FP-9"]:
            if grade not in rates:
                continue
            vals = [rates[grade].get(str(s), 0) for s in range(1, 15)]
            is_monotonic = all(vals[i] <= vals[i+1] for i in range(len(vals)-1))
            check(is_monotonic, f"{year_str}/{grade}: steps are monotonically non-decreasing")

        # Across grades, FP-1 Step 1 should be highest, FP-9 Step 1 should be lowest
        fp1_s1 = rates.get("FP-1", {}).get("1", 0)
        fp9_s1 = rates.get("FP-9", {}).get("1", 0)
        check(fp1_s1 > fp9_s1, f"{year_str}: FP-1/S1 (${fp1_s1:,}) > FP-9/S1 (${fp9_s1:,})")

        # Grade ordering: FP-1 > FP-2 > ... > FP-9 at Step 1
        grade_s1 = [rates.get(g, {}).get("1", 0) for g in ["FP-1","FP-2","FP-3","FP-4","FP-5","FP-6","FP-7","FP-8","FP-9"]]
        is_grade_ordered = all(grade_s1[i] > grade_s1[i+1] for i in range(len(grade_s1)-1))
        check(is_grade_ordered, f"{year_str}: grades are properly ordered at Step 1")

    # === YEAR-OVER-YEAR CONSISTENCY ===
    print("\n=== Year-over-Year Consistency ===")

    for yr in range(2017, 2027):
        prev = str(yr - 1)
        curr = str(yr)
        if prev not in tables or curr not in tables:
            continue

        # Every FP-5/Step-1 value should increase year over year
        prev_val = tables[prev]["rates"].get("FP-5", {}).get("1", 0)
        curr_val = tables[curr]["rates"].get("FP-5", {}).get("1", 0)
        check(curr_val > prev_val, f"FP-5/S1 {yr} (${curr_val:,}) > {yr-1} (${prev_val:,})")

        # The increase percentage should roughly match the stated raise
        expected_raise = raise_by_year.get(yr, 0)
        if prev_val > 0:
            actual_pct = (curr_val - prev_val) / prev_val * 100
            check(abs(actual_pct - expected_raise) < 0.15,
                  f"{yr} raise: actual {actual_pct:.2f}% vs stated {expected_raise}% (diff {abs(actual_pct-expected_raise):.3f}%)")

    # === FP-1 CAP CHECKS ===
    print("\n=== FP-1 Base Pay Cap ===")
    cap_history = data.get("base_pay_cap", {}).get("history", {})
    check(len(cap_history) >= 11, f"at least 11 years of cap history (got {len(cap_history)})")

    for year_str in expected_years:
        if year_str not in tables or year_str not in cap_history:
            continue
        cap = cap_history[year_str]
        rates = tables[year_str]["rates"]
        # FP-1 steps 10-14 should all equal the cap
        for step in ["10", "11", "12", "13", "14"]:
            val = rates.get("FP-1", {}).get(step, 0)
            check(val <= cap + 1, f"{year_str} FP-1/S{step} (${val:,}) <= cap (${cap:,})")

    # === SENIOR FOREIGN SERVICE ===
    print("\n=== Senior Foreign Service ===")
    sfs = data.get("senior_foreign_service", {})
    check(len(sfs) >= 11, f"at least 11 years of SFS data (got {len(sfs)})")

    for year_str in expected_years:
        if year_str not in sfs:
            continue
        s = sfs[year_str]
        check("counselor_min" in s, f"{year_str} SFS: counselor_min present")
        check("career_minister_max" in s, f"{year_str} SFS: career_minister_max present")
        # CM max should always be > OC min
        cm_max = s.get("career_minister_max", 0)
        oc_min = s.get("counselor_min", 0)
        check(cm_max > oc_min, f"{year_str} SFS: CM max (${cm_max:,}) > OC min (${oc_min:,})")

    # === EXECUTIVE SCHEDULE ===
    print("\n=== Executive Schedule ===")
    es = data.get("executive_schedule", {})
    check(len(es) >= 11, f"at least 11 years of ES data (got {len(es)})")
    # EX-I > EX-II > EX-III > EX-IV > EX-V for all years
    for year_str in expected_years:
        if year_str not in es:
            continue
        e = es[year_str]
        levels = [e.get("I",0), e.get("II",0), e.get("III",0), e.get("IV",0), e.get("V",0)]
        is_ordered = all(levels[i] > levels[i+1] for i in range(len(levels)-1))
        check(is_ordered, f"{year_str} ES: I > II > III > IV > V")

    # === RANGE REASONABLENESS ===
    print("\n=== Range Reasonableness ===")
    # 2026 FP-9/Step-1 should be a livable entry wage (> $30K)
    fp9_s1_2026 = tables.get("2026", {}).get("rates", {}).get("FP-9", {}).get("1", 0)
    check(fp9_s1_2026 > 30000, f"2026 FP-9/S1 (${fp9_s1_2026:,}) > $30,000")
    check(fp9_s1_2026 < 50000, f"2026 FP-9/S1 (${fp9_s1_2026:,}) < $50,000")

    # 2026 FP-1/Step-1 should be senior level (> $100K)
    fp1_s1_2026 = tables.get("2026", {}).get("rates", {}).get("FP-1", {}).get("1", 0)
    check(fp1_s1_2026 > 100000, f"2026 FP-1/S1 (${fp1_s1_2026:,}) > $100,000")
    check(fp1_s1_2026 < 200000, f"2026 FP-1/S1 (${fp1_s1_2026:,}) < $200,000")

    # Step multiplier: Step 14 / Step 1 should be ~1.3x for most grades
    for grade in ["FP-3", "FP-5", "FP-7"]:
        s1 = tables.get("2026", {}).get("rates", {}).get(grade, {}).get("1", 1)
        s14 = tables.get("2026", {}).get("rates", {}).get(grade, {}).get("14", 0)
        ratio = s14 / s1 if s1 > 0 else 0
        check(1.2 < ratio < 1.6, f"2026 {grade} S14/S1 ratio = {ratio:.3f} (expected 1.2-1.6)")

    # === NO PII ===
    print("\n=== PII & Consumer-Agnostic Checks ===")
    raw = json.dumps(data)
    check("SSN" not in raw and "social security number" not in raw.lower(), "No PII detected")
    for term in ["engine_usage", "meridian", "Meridian", "engine_number"]:
        check(term not in raw, f"No consumer-specific term: '{term}'")

    # === CROSS-FILE: retirement rules ===
    print("\n=== Cross-File Consistency ===")
    retirement_file = os.path.join(REPO_ROOT, "reference", "foreign-service-retirement-rules.json")
    if os.path.isfile(retirement_file):
        with open(retirement_file) as f:
            ret_data = json.load(f)
        # The retirement file should reference high_3 — verify it exists
        raw_ret = json.dumps(ret_data).lower()
        check("high_3" in raw_ret or "high-3" in raw_ret,
              "Retirement rules file references high-3 salary (pay table companion)")
    else:
        print("  WARN: foreign-service-retirement-rules.json not found, skipping cross-file check")

    # === MANIFEST ===
    print("\n=== Manifest Check ===")
    if os.path.isfile(MANIFEST_FILE):
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
        check("fs_pay_tables" in manifest.get("files", {}),
              "fs_pay_tables in manifest")
    else:
        print("  WARN: manifest.json not found")

    # === SUMMARY ===
    print(f"\n{'='*60}")
    print(f"FS PAY TABLES VALIDATION: {passed + failed} checks | PASS: {passed} | FAIL: {failed}")
    print(f"{'='*60}")

    if errors:
        print("\nFailed checks:")
        for e in errors:
            print(f"  - {e}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
