#!/usr/bin/env python3
"""
Validate pay-tables.json — multi-year GS base pay tables (2016-2026).
Checks structure, data integrity, cross-year consistency, and known OPM values.
"""
import json
import sys
import os

passed = 0
failed = 0

def check(condition, msg):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {msg}")

# Load
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
pt_path = os.path.join(repo_root, "federal", "pay-tables.json")

with open(pt_path) as f:
    data = json.load(f)

# ── Metadata ──
check("metadata" in data, "metadata key missing")
md = data.get("metadata", {})
check(md.get("version") == "2.0", f"version should be 2.0, got {md.get('version')}")
check("sources" in md, "sources missing from metadata")
check(len(md.get("sources", [])) >= 11, f"should have >= 11 source URLs, got {len(md.get('sources', []))}")

# ── Structure ──
check("tables" in data, "tables key missing")
check("grades" in data, "grades key missing")
check("steps" in data, "steps key missing")
check("hourly_divisor" in data, "hourly_divisor missing")
check(data.get("hourly_divisor") == 2087, f"hourly_divisor should be 2087, got {data.get('hourly_divisor')}")
check("locality_areas" in data, "locality_areas missing")

grades_list = data.get("grades", [])
check(len(grades_list) == 15, f"should have 15 grades, got {len(grades_list)}")
check(grades_list[0] == "GS-1", f"first grade should be GS-1, got {grades_list[0] if grades_list else 'empty'}")
check(grades_list[-1] == "GS-15", f"last grade should be GS-15")

steps_list = data.get("steps", [])
check(len(steps_list) == 10, f"should have 10 steps, got {len(steps_list)}")

tables = data.get("tables", {})

# ── Year coverage ──
expected_years = [str(y) for y in range(2016, 2027)]
check(sorted(tables.keys()) == expected_years, f"expected years 2016-2026, got {sorted(tables.keys())}")

# ── Per-year structural checks ──
for year in expected_years:
    if year not in tables:
        check(False, f"year {year} missing from tables")
        continue
    t = tables[year]
    check("effective_date" in t, f"{year}: missing effective_date")
    check("raise_pct" in t, f"{year}: missing raise_pct")
    check("rates" in t, f"{year}: missing rates")
    
    # Effective date format
    ed = t.get("effective_date", "")
    check(ed.startswith(year), f"{year}: effective_date {ed} doesn't start with year")
    
    # Raise percentage range
    rp = t.get("raise_pct", -1)
    check(0 <= rp <= 10, f"{year}: raise_pct {rp} out of range 0-10")
    
    rates = t.get("rates", {})
    check(len(rates) == 15, f"{year}: should have 15 grades, got {len(rates)}")
    
    for grade in grades_list:
        if grade not in rates:
            check(False, f"{year}: missing grade {grade}")
            continue
        steps = rates[grade]
        check(len(steps) == 10, f"{year}/{grade}: should have 10 steps, got {len(steps)}")
        check(all(isinstance(v, int) for v in steps), f"{year}/{grade}: all values should be integers")
        check(all(v > 0 for v in steps), f"{year}/{grade}: all values should be positive")
        # Steps should be monotonically increasing
        check(all(steps[i] <= steps[i+1] for i in range(len(steps)-1)), 
              f"{year}/{grade}: steps not monotonically increasing")
    
    # Grades should be monotonically increasing at Step 1
    step1_values = [rates.get(g, [0])[0] for g in grades_list if g in rates]
    check(all(step1_values[i] <= step1_values[i+1] for i in range(len(step1_values)-1)),
          f"{year}: grade Step 1 values not monotonically increasing")

# ── Known OPM values (spot checks from official PDFs) ──
print("\n  Verifying known OPM values...")

# 2026 - from OPM Salary Table 2026-GS PDF
known_2026 = {
    ("GS-1", 0): 22584, ("GS-1", 9): 28248,
    ("GS-5", 0): 34799, ("GS-5", 9): 45239,
    ("GS-7", 0): 43106, ("GS-7", 4): 48854,
    ("GS-9", 0): 52727, ("GS-9", 9): 68549,
    ("GS-11", 0): 63795, ("GS-11", 4): 72303,
    ("GS-12", 0): 76463, ("GS-12", 9): 99404,
    ("GS-13", 0): 90925, ("GS-13", 4): 103049,
    ("GS-13", 9): 118204,
    ("GS-14", 0): 107446, ("GS-14", 9): 139684,
    ("GS-15", 0): 126384, ("GS-15", 9): 164301,
}
for (grade, step), expected in known_2026.items():
    actual = tables.get("2026", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2026/{grade}/Step{step+1}: expected {expected}, got {actual}")

# 2025 - from OPM Salary Table 2025-GS PDF
known_2025 = {
    ("GS-1", 0): 22360, ("GS-9", 0): 52205,
    ("GS-13", 0): 90025, ("GS-13", 4): 102029,
    ("GS-15", 0): 125133, ("GS-15", 9): 162672,
}
for (grade, step), expected in known_2025.items():
    actual = tables.get("2025", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2025/{grade}/Step{step+1}: expected {expected}, got {actual}")

# 2024 - from OPM Salary Table 2024-GS PDF
known_2024 = {
    ("GS-1", 0): 21986, ("GS-9", 0): 51332,
    ("GS-13", 0): 88520, ("GS-15", 9): 159950,
}
for (grade, step), expected in known_2024.items():
    actual = tables.get("2024", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2024/{grade}/Step{step+1}: expected {expected}, got {actual}")

# 2023
known_2023 = {
    ("GS-1", 0): 20999, ("GS-13", 0): 84546, ("GS-15", 9): 152771,
}
for (grade, step), expected in known_2023.items():
    actual = tables.get("2023", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2023/{grade}/Step{step+1}: expected {expected}, got {actual}")

# 2020
known_2020 = {
    ("GS-1", 0): 19543, ("GS-13", 0): 78681, ("GS-15", 9): 142180,
}
for (grade, step), expected in known_2020.items():
    actual = tables.get("2020", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2020/{grade}/Step{step+1}: expected {expected}, got {actual}")

# 2016
known_2016 = {
    ("GS-1", 0): 18343, ("GS-13", 0): 73846, ("GS-15", 9): 133444,
}
for (grade, step), expected in known_2016.items():
    actual = tables.get("2016", {}).get("rates", {}).get(grade, [None]*10)[step]
    check(actual == expected, f"2016/{grade}/Step{step+1}: expected {expected}, got {actual}")

# ── Cross-year consistency ──
print("\n  Cross-year consistency checks...")

# Year-over-year values should increase (no year had negative raise in this range)
raise_pcts = {
    "2016": 1.0, "2017": 1.0, "2018": 1.4, "2019": 1.4,
    "2020": 2.6, "2021": 1.0, "2022": 2.2, "2023": 4.1,
    "2024": 4.7, "2025": 1.7, "2026": 1.0
}

for year_str, expected_pct in raise_pcts.items():
    actual_pct = tables.get(year_str, {}).get("raise_pct", -1)
    check(actual_pct == expected_pct, 
          f"{year_str}: raise_pct should be {expected_pct}, got {actual_pct}")

# Each year's GS-13/Step 1 should be > previous year
for i in range(len(expected_years) - 1):
    y1, y2 = expected_years[i], expected_years[i+1]
    v1 = tables.get(y1, {}).get("rates", {}).get("GS-13", [0])[0]
    v2 = tables.get(y2, {}).get("rates", {}).get("GS-13", [0])[0]
    check(v2 > v1, f"GS-13/S1 should increase from {y1} ({v1}) to {y2} ({v2})")

# Verify raise percentages produce approximately correct values
# (OPM rounds, so allow $2 tolerance per step)
for i in range(len(expected_years) - 1):
    y1, y2 = expected_years[i], expected_years[i+1]
    pct = raise_pcts[y2]
    v1 = tables[y1]["rates"]["GS-13"][0]
    v2 = tables[y2]["rates"]["GS-13"][0]
    expected_v2 = round(v1 * (1 + pct / 100))
    check(abs(v2 - expected_v2) <= 2, 
          f"GS-13/S1 {y1}→{y2}: expected ~{expected_v2} (from {v1} × {1+pct/100}), got {v2}")

# ── Locality areas ──
print("\n  Locality area checks...")
loc = data.get("locality_areas", {})
areas = loc.get("areas", [])
check(len(areas) >= 49, f"should have >= 49 locality areas, got {len(areas)}")

# Check a few known locality codes
area_codes = {a["code"]: a for a in areas}
check("DCB" in area_codes or any(a["code"].startswith("DC") or "washington" in a.get("name","").lower() for a in areas),
      "DC/Washington locality area missing")
check(any("rest" in a.get("name", "").lower() for a in areas), "Rest of US locality area missing")

# All areas should have code, name, pct
for area in areas:
    check("code" in area, f"locality area missing code: {area}")
    check("name" in area, f"locality area missing name: {area}")
    check("pct" in area, f"locality area missing pct: {area}")
    pct = area.get("pct", 0)
    check(0.10 <= pct <= 0.60, f"locality pct {pct} out of range for {area.get('name', '?')}")

# ── Cross-file consistency with federal-pay-raises.json ──
print("\n  Cross-file consistency...")
raises_path = os.path.join(repo_root, "federal", "federal-pay-raises.json")
if os.path.exists(raises_path):
    with open(raises_path) as f:
        raises_data = json.load(f)
    # Check that raise percentages match
    pr_years = raises_data.get("years", raises_data.get("raises", []))
    if isinstance(pr_years, list):
        for entry in pr_years:
            yr = str(entry.get("year", ""))
            gs_pct = entry.get("gs_raise_pct", entry.get("gs", entry.get("civilian", None)))
            if yr in tables and gs_pct is not None:
                table_pct = tables[yr].get("raise_pct")
                check(abs(float(table_pct) - float(gs_pct)) < 0.01,
                      f"raise_pct mismatch for {yr}: pay-tables says {table_pct}, pay-raises says {gs_pct}")
    elif isinstance(pr_years, dict):
        for yr, entry in pr_years.items():
            gs_pct = entry.get("gs_raise_pct") if isinstance(entry, dict) else entry
            if yr in tables and gs_pct is not None:
                table_pct = tables[yr].get("raise_pct")
                check(abs(float(table_pct) - float(gs_pct)) < 0.01,
                      f"raise_pct mismatch for {yr}: pay-tables says {table_pct}, pay-raises says {gs_pct}")
else:
    print("  (federal-pay-raises.json not found, skipping cross-file check)")

# ══════════════════════════════════════════════════════════
# VA COMPENSATION HISTORY
# ══════════════════════════════════════════════════════════
print("\n  VA compensation rate history checks...")

va_path = os.path.join(repo_root, "federal", "veterans-affairs", "compensation.json")
if os.path.exists(va_path):
    with open(va_path) as f:
        va_data = json.load(f)
    
    check("rate_history" in va_data, "VA: rate_history section missing")
    rh = va_data.get("rate_history", [])
    check(len(rh) >= 11, f"VA: should have >= 11 years of history, got {len(rh)}")
    
    expected_va_years = list(range(2016, 2027))
    actual_va_years = [e.get("year") for e in rh]
    check(actual_va_years == expected_va_years, f"VA: year range should be 2016-2026, got {actual_va_years}")
    
    ratings = ["10","20","30","40","50","60","70","80","90","100"]
    
    for entry in rh:
        yr = entry.get("year", "?")
        check("effective_date" in entry, f"VA {yr}: missing effective_date")
        check("cola_pct" in entry, f"VA {yr}: missing cola_pct")
        check("veteran_alone_monthly" in entry, f"VA {yr}: missing veteran_alone_monthly")
        
        vam = entry.get("veteran_alone_monthly", {})
        check(len(vam) == 10, f"VA {yr}: should have 10 ratings, got {len(vam)}")
        
        for r in ratings:
            if r in vam:
                val = vam[r]
                check(isinstance(val, (int, float)), f"VA {yr}/{r}%: value should be numeric, got {type(val)}")
                check(val > 0, f"VA {yr}/{r}%: value should be positive, got {val}")
        
        # Ratings should be monotonically increasing
        vals = [vam.get(r, 0) for r in ratings]
        check(all(vals[i] <= vals[i+1] for i in range(len(vals)-1)),
              f"VA {yr}: rates not monotonically increasing by rating")
    
    # Year-over-year: all ratings should increase (VA had positive COLA every year except 2016)
    for i in range(len(rh) - 1):
        y1, y2 = rh[i], rh[i+1]
        yr1, yr2 = y1["year"], y2["year"]
        v1_100 = y1.get("veteran_alone_monthly", {}).get("100", 0)
        v2_100 = y2.get("veteran_alone_monthly", {}).get("100", 0)
        if y2.get("cola_pct", 0) > 0:
            check(v2_100 > v1_100, f"VA 100% should increase from {yr1} to {yr2}: {v1_100} → {v2_100}")
    
    # Known VA.gov values (spot checks)
    # 2026 rates from current VA.gov
    check_va_2026 = {
        "10": 180.42, "20": 356.66, "30": 552.47, "50": 1132.90, "100": 3938.58
    }
    yr_2026 = next((e for e in rh if e["year"] == 2026), None)
    if yr_2026:
        for r, expected in check_va_2026.items():
            actual = yr_2026["veteran_alone_monthly"].get(r, 0)
            check(abs(actual - expected) < 0.01, f"VA 2026/{r}%: expected {expected}, got {actual}")
    
    # 2020 rates from VA.gov past rates page
    check_va_2020 = {
        "10": 142.29, "20": 281.27, "30": 435.69, "50": 893.43, 
        "60": 1131.68, "70": 1426.17, "80": 1657.80, "90": 1862.96, "100": 3106.04
    }
    yr_2020 = next((e for e in rh if e["year"] == 2020), None)
    if yr_2020:
        for r, expected in check_va_2020.items():
            actual = yr_2020["veteran_alone_monthly"].get(r, 0)
            check(abs(actual - expected) < 0.05, f"VA 2020/{r}%: expected {expected}, got {actual}")
    
    # Cross-check: 2026 rates should match current compensation.rates_by_rating
    current_rates = va_data.get("compensation", {}).get("rates_by_rating", {})
    if current_rates and yr_2026:
        for r in ratings:
            current = current_rates.get(r, {}).get("base_rate", 0)
            historical = yr_2026["veteran_alone_monthly"].get(r, 0)
            check(abs(current - historical) < 0.01,
                  f"VA {r}%: current rate ({current}) != 2026 history ({historical})")
    
    check(va_data.get("version") == "2026.2", f"VA version should be 2026.2, got {va_data.get('version')}")

else:
    print("  (VA compensation.json not found, skipping)")

# ── Summary ──
print(f"\n{'='*60}")
print(f"PAY TABLES BUNDLE VALIDATION: {passed + failed} checks | PASS: {passed} | FAIL: {failed}")
print(f"{'='*60}")

sys.exit(0 if failed == 0 else 1)
