#!/usr/bin/env python3
"""
Validation suite for military retirement rules v2.1+ and military pay tables.
Tests Gap 1 (Chapter 61 disability retirement), Gap 2 (concurrent receipt expansion),
and Gap 3 (military basic pay tables 2016-2026).
"""
import json
import os
import sys

PASS = 0
FAIL = 0
WARN = 0

def check(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")

def warn(condition, msg):
    global WARN
    if not condition:
        WARN += 1
        print(f"  WARN: {msg}")

def load_json(path):
    with open(path) as f:
        return json.load(f)

# ============================================================
# PATHS
# ============================================================
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(BASE, "reference", "military-retirement-rules.json")
PAY_PATH = os.path.join(BASE, "federal", "military-pay-tables.json")
MANIFEST_PATH = os.path.join(BASE, "manifest.json")

# ============================================================
# SECTION 1: military-retirement-rules.json (v2.0)
# ============================================================
print("=== Military Retirement Rules v2.1+ ===")

rules = load_json(RULES_PATH)

# Metadata checks
print("  Metadata...")
check(float(rules["metadata"]["version"]) >= 2.0, "Version should be >= 2.0")
check("disability_retirement" in rules, "Top-level disability_retirement key exists")
check("concurrent_receipt" in rules, "Top-level concurrent_receipt key exists")
check("retirement_systems" in rules, "Top-level retirement_systems key exists")
check("survivor_benefit_plan" in rules, "Top-level survivor_benefit_plan key exists")
check("reserve_retirement" in rules, "Top-level reserve_retirement key exists")

# --- Gap 1: Disability Retirement ---
print("  Gap 1: Disability retirement...")
dr = rules["disability_retirement"]
check(dr["chapter"] == "10 U.S.C. Chapter 61", "Chapter reference correct")
check("eligibility" in dr, "Eligibility field present")
check("temporary_disability_retired_list" in dr, "TDRL section present")
check("permanent_disability_retired_list" in dr, "PDRL section present")
check("formula" in dr, "Formula section present")

# TDRL checks
tdrl = dr["temporary_disability_retired_list"]
check(tdrl["max_duration_years"] == 5, "TDRL max duration 5 years")
check(tdrl["re_evaluation_interval_months"] == 18, "TDRL re-eval every 18 months")
check(len(tdrl["outcomes"]) == 3, "TDRL has 3 outcomes")

# Formula checks
formula = dr["formula"]
check("method_1_disability" in formula, "Method 1 (disability) present")
check("method_2_longevity" in formula, "Method 2 (longevity) present")
check(formula["method_1_disability"]["max_pct"] == 75, "Method 1 max 75%")
check(formula["method_2_longevity"]["max_pct"] == 75, "Method 2 max 75%")
check("diems_before_1980_09_08" in formula["method_1_disability"]["pay_base_rules"], "DIEMS pre-1980 rule present")
check("diems_on_or_after_1980_09_08" in formula["method_1_disability"]["pay_base_rules"], "DIEMS post-1980 rule present")

# Minimum floor
check(dr["minimum_retired_pay_floor"]["min_pct"] == 30, "Minimum retired pay floor 30%")

# Severance alternative
sev = dr["severance_alternative"]
check("formula" in sev, "Severance formula present")
check(sev["max_years"] == 19, "Severance max years 19")
check("taxability" in sev, "Severance taxability documented")

# COLA, TRICARE, SBP references
check("cola_rule" in dr, "COLA rule present")
check("tricare_eligibility" in dr, "TRICARE eligibility present")
check("sbp_eligibility" in dr, "SBP eligibility present")

# --- Gap 2: Concurrent Receipt ---
print("  Gap 2: Concurrent receipt...")
cr = rules["concurrent_receipt"]
check("overview" in cr, "Overview present")
check("va_offset_rule" in cr, "VA offset rule present")
check("crdp" in cr, "CRDP section present")
check("crsc" in cr, "CRSC section present")
check("crdp_vs_crsc_election" in cr, "CRDP vs CRSC election present")
check("no_concurrent_receipt_group" in cr, "No-relief group documented")
check("tax_exclusion_for_disability_retired_pay" in cr, "§ 104 tax exclusion present")

# VA offset
check("formula" in cr["va_offset_rule"], "VA offset formula present")
check("tax_effect" in cr["va_offset_rule"], "VA offset tax effect documented")

# CRDP eligibility
crdp = cr["crdp"]
check(isinstance(crdp["eligibility"], dict), "CRDP eligibility is detailed object")
check(crdp["eligibility"]["va_disability_rating_min_pct"] == 50, "CRDP requires 50% VA rating")
check(isinstance(crdp["not_eligible"], list), "CRDP not_eligible list present")
check(len(crdp["not_eligible"]) >= 2, "CRDP has at least 2 ineligible groups")
check("computation" in crdp, "CRDP computation present")
check("chapter_61_cap" in crdp["computation"], "CRDP Chapter 61 cap documented")
check(isinstance(crdp["tax_treatment"], dict), "CRDP tax treatment is detailed object")
check(crdp["application_required"] == False, "CRDP auto-applied (no application)")

# CRSC eligibility
crsc = cr["crsc"]
check(isinstance(crsc["eligibility"], dict), "CRSC eligibility is detailed object")
check(crsc["eligibility"]["va_disability_rating_min_pct"] == 0, "CRSC has no minimum VA rating")
check("combat_related_categories" in crsc, "CRSC combat categories present")
check(len(crsc["combat_related_categories"]) == 4, "CRSC has 4 combat categories (DC, HD, SW, IN)")
codes = [c["code"] for c in crsc["combat_related_categories"]]
check(set(codes) == {"DC","HD","SW","IN"}, "CRSC codes are DC, HD, SW, IN")
check("computation" in crsc, "CRSC computation present")
check("chapter_61_special_rule" in crsc["computation"], "CRSC Chapter 61 special rule documented")
check(isinstance(crsc["tax_treatment"], dict), "CRSC tax treatment is detailed object")
check(crsc["application_required"] == True, "CRSC requires application")
check(crsc["application_form"] == "DD Form 2860", "CRSC form is DD 2860")

# Election logic
election = cr["crdp_vs_crsc_election"]
check(isinstance(election["decision_factors"], list), "Decision factors is list")
check(len(election["decision_factors"]) >= 5, "At least 5 decision factors")
factor_names = [f["factor"] for f in election["decision_factors"]]
check("Tax bracket" in factor_names, "Tax bracket factor present")
check("State income tax" in factor_names, "State tax factor present")
check("Means-tested benefits" in factor_names, "Means-tested benefits factor present")

# § 104 exclusion
tax_excl = cr["tax_exclusion_for_disability_retired_pay"]
check("irs_rule" in tax_excl, "IRS rule citation present")
check("formula" in tax_excl, "Tax exclusion formula present")
check("combat_injured_exclusion" in tax_excl, "Combat injured exclusion documented")
check("interaction_with_crdp_crsc" in tax_excl, "Interaction with CRDP/CRSC documented")

# No-relief groups
no_relief = cr["no_concurrent_receipt_group"]
check("group_1" in no_relief, "No-relief group 1 present")
check("group_2" in no_relief, "No-relief group 2 present")

# ============================================================
# SECTION 2: military-pay-tables.json
# ============================================================
print("\n=== Military Pay Tables ===")

pay = load_json(PAY_PATH)

# Metadata
print("  Metadata...")
check(pay["_metadata"]["version"] == "2026.1", "Version is 2026.1")
check("2026-01-01" in pay["_metadata"]["effective_date"], "Effective date 2026-01-01")

# Structure
check(len(pay["yos_columns"]) == 22, "22 YOS columns defined")
check(pay["yos_columns"][0] == 0, "First YOS column is 0")
check(pay["yos_columns"][-1] == 40, "Last YOS column is 40")

# Grade lists
grades = pay["grades"]
check(len(grades["enlisted"]) == 9, "9 enlisted grades")
check(len(grades["warrant"]) == 5, "5 warrant grades")
check(len(grades["officer"]) == 10, "10 officer grades")
check(len(grades["prior_enlisted_officer"]) == 3, "3 prior-enlisted officer grades")

# Pay raise history
check(len(pay["pay_raise_history"]) == 11, "11 years of raise history")
raises = {r["year"]: r["raise_pct"] for r in pay["pay_raise_history"]}
check(raises[2026] == 3.8, "2026 raise is 3.8%")
check(raises[2025] == 4.5, "2025 raise is 4.5%")
check(raises[2024] == 5.2, "2024 raise is 5.2%")
check(raises[2016] == 1.3, "2016 raise is 1.3%")

# Tables — all 11 years present
print("  Year coverage...")
EXPECTED_YEARS = [str(y) for y in range(2016, 2027)]
for yr in EXPECTED_YEARS:
    check(yr in pay["tables"], f"Year {yr} table present")

ALL_GRADES = (grades["enlisted"] + grades["warrant"] + grades["officer"] + 
              grades["prior_enlisted_officer"])
check(len(ALL_GRADES) == 27, "27 total grades defined")

# Per-year checks
print("  Per-year validation...")
for yr_str in EXPECTED_YEARS:
    yr_data = pay["tables"][yr_str]
    check("effective_date" in yr_data, f"{yr_str}: effective_date present")
    check("rates" in yr_data, f"{yr_str}: rates present")
    check("e1_entry_rate" in yr_data, f"{yr_str}: e1_entry_rate present")
    
    rates = yr_data["rates"]
    for g in ALL_GRADES:
        check(g in rates, f"{yr_str}: Grade {g} present")
    
    # E-1 through E-7 should have YOS 0 values
    for g in ["E-1","E-2","E-3","E-4","E-5","E-6","E-7"]:
        if g in rates:
            check(rates[g]["0"] is not None, f"{yr_str} {g}: YOS 0 not null")
    
    # E-8, E-9 should NOT have YOS 0
    if "E-8" in rates:
        check(rates["E-8"]["0"] is None, f"{yr_str} E-8: YOS 0 is null (not authorized)")
    if "E-9" in rates:
        check(rates["E-9"]["0"] is None, f"{yr_str} E-9: YOS 0 is null (not authorized)")
    
    # W-5 should not have YOS 0
    if "W-5" in rates:
        check(rates["W-5"]["0"] is None, f"{yr_str} W-5: YOS 0 is null (not authorized)")
    
    # O-9, O-10 only at high YOS
    if "O-9" in rates:
        check(rates["O-9"]["0"] is None, f"{yr_str} O-9: YOS 0 is null")
    if "O-10" in rates:
        check(rates["O-10"]["0"] is None, f"{yr_str} O-10: YOS 0 is null")
    
    # O-1E, O-2E, O-3E only at YOS 4+
    for g in ["O-1E","O-2E","O-3E"]:
        if g in rates:
            check(rates[g]["0"] is None, f"{yr_str} {g}: YOS 0 is null")
            check(rates[g]["2"] is None, f"{yr_str} {g}: YOS 2 is null")
            check(rates[g]["3"] is None, f"{yr_str} {g}: YOS 3 is null")

# Value range checks (2026)
print("  Value range checks...")
r2026 = pay["tables"]["2026"]["rates"]
check(r2026["E-1"]["0"] >= 2000 and r2026["E-1"]["0"] <= 3000, "2026 E-1 YOS 0 in range $2000-$3000")
check(r2026["O-10"]["20"] >= 15000, "2026 O-10 YOS 20 >= $15,000")
check(r2026["E-9"]["30"] >= 9000, "2026 E-9 YOS 30 >= $9,000")
check(r2026["W-5"]["20"] >= 9000, "2026 W-5 YOS 20 >= $9,000")

# E-1 entry rate check
check(pay["tables"]["2026"]["e1_entry_rate"]["less_than_4_months"] < pay["tables"]["2026"]["e1_entry_rate"]["4_months_or_more"],
      "2026 E-1 entry rate < regular E-1 rate")

# Year-over-year increase check (values should generally increase)
print("  Year-over-year progression...")
for yr in range(2017, 2027):
    prev = pay["tables"][str(yr-1)]["rates"]["E-7"]["0"]
    curr = pay["tables"][str(yr)]["rates"]["E-7"]["0"]
    check(curr > prev, f"E-7 YOS 0: {yr} (${curr}) > {yr-1} (${prev})")

for yr in range(2017, 2027):
    prev = pay["tables"][str(yr-1)]["rates"]["O-5"]["10"]
    curr = pay["tables"][str(yr)]["rates"]["O-5"]["10"]
    check(curr > prev, f"O-5 YOS 10: {yr} (${curr}) > {yr-1} (${prev})")

# Cross-verify specific 2026 values against navycs.com
print("  2026 navycs.com cross-verification...")
navycs_2026 = {
    "E-5": {"0": 3343, "6": 4110, "10": 4395},
    "E-7": {"0": 3932, "8": 5135, "20": 6245},
    "E-9": {"10": 6910, "20": 8105, "30": 9730},
    "O-1": {"0": 4150, "3": 5222},
    "O-4": {"0": 6294, "8": 8816},
    "O-6": {"0": 8751, "20": 13751},
    "W-3": {"0": 5223, "18": 8150},
}
for grade, yos_checks in navycs_2026.items():
    for yos, expected in yos_checks.items():
        actual = r2026[grade][yos]
        check(actual == expected, f"2026 {grade} YOS {yos}: got ${actual}, expected ${expected}")

# Data point count
total_pts = sum(
    1 for yr_data in pay["tables"].values()
    for g_rates in yr_data["rates"].values()
    for v in g_rates.values() if v is not None
)
check(total_pts >= 4000, f"Total data points ({total_pts}) >= 4000")

# ============================================================
# SECTION 3: Manifest
# ============================================================
print("\n=== Manifest ===")

manifest = load_json(MANIFEST_PATH)
files = manifest.get("files", {})

# military_retirement_rules version bump
check("military_retirement_rules" in files, "military_retirement_rules in manifest")
if "military_retirement_rules" in files:
    check(float(files["military_retirement_rules"]["version"]) >= 2.0, "military_retirement_rules version >= 2.0")

# military_pay_tables entry
check("military_pay_tables" in files, "military_pay_tables in manifest")
if "military_pay_tables" in files:
    mpt = files["military_pay_tables"]
    check(mpt["version"] == "2026.1", "military_pay_tables version 2026.1")
    check("url" in mpt, "military_pay_tables has url field")
    check(mpt["url"] == "federal/military-pay-tables.json", "military_pay_tables url correct")
    check("description" in mpt, "military_pay_tables has description")
    check("last_updated" in mpt, "military_pay_tables has last_updated")
    check("effective_date" in mpt, "military_pay_tables has effective_date")
    check("update_frequency" in mpt, "military_pay_tables has update_frequency")

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*50}")
print(f"Military validation: {PASS} passed, {FAIL} failed, {WARN} warnings")
if FAIL > 0:
    print("VALIDATION FAILED")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
