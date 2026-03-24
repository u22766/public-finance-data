#!/usr/bin/env python3
"""
Validation suite for federal retirement eligibility and service credit rules.
Covers:
  - federal/fers-eligibility-rules.json (MRA schedule, retirement pathways, VERA/VSIP)
  - federal/fers-service-credit-rules.json (deposit, redeposit, military buyback, sick leave, interest rates)
"""

import json
import os
import sys

PASS = 0
FAIL = 0
CHECKS = 0

def check(check_id, condition, description):
    global PASS, FAIL, CHECKS
    CHECKS += 1
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL [{check_id}]: {description}")

# ── Locate files ──
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
elig_path = os.path.join(repo_root, "federal", "fers-eligibility-rules.json")
svc_path = os.path.join(repo_root, "federal", "fers-service-credit-rules.json")

for p, label in [(elig_path, "eligibility"), (svc_path, "service-credit")]:
    if not os.path.exists(p):
        print(f"FATAL: {label} file not found at {p}")
        sys.exit(1)

with open(elig_path) as f:
    elig = json.load(f)
with open(svc_path) as f:
    svc = json.load(f)

# ═══════════════════════════════════════════════════════════════
# PART 1: FERS ELIGIBILITY RULES
# ═══════════════════════════════════════════════════════════════
print("=== FERS Eligibility Rules ===\n")

# ── Metadata ──
meta = elig["metadata"]
check("E-001", meta["version"] == "1.0", "Version is 1.0")
check("E-002", "2026" in meta["last_updated"], "Last updated in 2026")
check("E-003", meta["schema_version"] == "2.2", "Schema version 2.2")
check("E-004", len(meta["sources"]) >= 5, f"At least 5 sources (got {len(meta['sources'])})")
check("E-005", any("8412" in s for s in meta["sources"]), "Sources cite 5 USC 8412")

# ── MRA Schedule ──
mra = elig["mra_schedule"]
schedule = mra["schedule"]
check("E-010", len(schedule) == 13, f"MRA schedule has 13 bands (got {len(schedule)})")
check("E-011", "8412" in mra["authority"], "MRA authority cites 8412")

# First band: born before 1948 → MRA 55
first = schedule[0]
check("E-012", first["birth_year_start"] is None, "First band starts at null (open-ended)")
check("E-013", first["birth_year_end"] == 1947, "First band ends at 1947")
check("E-014", first["mra_years"] == 55, "Born ≤1947: MRA is 55 years")
check("E-015", first["mra_months"] == 0, "Born ≤1947: MRA is 0 months")

# Transitional bands 1948-1952: each adds 2 months
for i, year in enumerate([1948, 1949, 1950, 1951, 1952]):
    band = schedule[i + 1]
    expected_months = (i + 1) * 2
    check(f"E-{20+i}", band["birth_year_start"] == year, f"Band for {year} starts at {year}")
    check(f"E-{25+i}", band["birth_year_end"] == year, f"Band for {year} ends at {year}")
    check(f"E-{30+i}", band["mra_years"] == 55, f"Born {year}: MRA years = 55")
    check(f"E-{35+i}", band["mra_months"] == expected_months, f"Born {year}: MRA months = {expected_months}")

# 1953-1964 band → MRA 56
band_56 = schedule[6]
check("E-040", band_56["birth_year_start"] == 1953, "56-year band starts at 1953")
check("E-041", band_56["birth_year_end"] == 1964, "56-year band ends at 1964")
check("E-042", band_56["mra_years"] == 56, "Born 1953-1964: MRA is 56")
check("E-043", band_56["mra_months"] == 0, "Born 1953-1964: 0 additional months")

# Transitional bands 1965-1969: each adds 2 months above 56
for i, year in enumerate([1965, 1966, 1967, 1968, 1969]):
    band = schedule[7 + i]
    expected_months = (i + 1) * 2
    check(f"E-{50+i}", band["birth_year_start"] == year, f"Band for {year} starts correctly")
    check(f"E-{55+i}", band["mra_years"] == 56, f"Born {year}: MRA years = 56")
    check(f"E-{60+i}", band["mra_months"] == expected_months, f"Born {year}: MRA months = {expected_months}")

# Last band: born 1970+ → MRA 57
last = schedule[12]
check("E-070", last["birth_year_start"] == 1970, "Last band starts at 1970")
check("E-071", last["birth_year_end"] is None, "Last band ends at null (open-ended)")
check("E-072", last["mra_years"] == 57, "Born 1970+: MRA is 57")
check("E-073", last["mra_months"] == 0, "Born 1970+: 0 additional months")

# Decimal values sanity
check("E-074", schedule[0]["mra_decimal"] == 55.0, "Decimal for ≤1947 is 55.0")
check("E-075", schedule[3]["mra_decimal"] == 55.5, "Decimal for 1950 is 55.5")
check("E-076", schedule[12]["mra_decimal"] == 57.0, "Decimal for 1970+ is 57.0")

# MRA range validation
for i, band in enumerate(schedule):
    check(f"E-080-{i}", 55.0 <= band["mra_decimal"] <= 57.0,
          f"MRA decimal in range 55-57 for band {i}")

# ── Immediate Retirement Pathways ──
pathways = elig["immediate_retirement"]["standard_pathways"]
check("E-100", len(pathways) == 4, f"4 standard pathways (got {len(pathways)})")

pathway_names = [p["pathway"] for p in pathways]
check("E-101", "mra_plus_30" in pathway_names, "MRA+30 pathway present")
check("E-102", "age_60_plus_20" in pathway_names, "Age 60+20 pathway present")
check("E-103", "age_62_plus_5" in pathway_names, "Age 62+5 pathway present")
check("E-104", "mra_plus_10" in pathway_names, "MRA+10 pathway present")

# MRA+30: unreduced
mra30 = [p for p in pathways if p["pathway"] == "mra_plus_30"][0]
check("E-110", mra30["service_years_required"] == 30, "MRA+30 requires 30 years")
check("E-111", mra30["annuity_reduction"] == False, "MRA+30 is unreduced")
check("E-112", mra30["srs_eligible"] == True, "MRA+30 eligible for SRS")

# Age 62+5: unreduced, no SRS
a62 = [p for p in pathways if p["pathway"] == "age_62_plus_5"][0]
check("E-120", a62["service_years_required"] == 5, "Age 62+5 requires 5 years")
check("E-121", a62["annuity_reduction"] == False, "Age 62+5 is unreduced")
check("E-122", a62["srs_eligible"] == False, "Age 62+5 not eligible for SRS")

# MRA+10: reduced
mra10 = [p for p in pathways if p["pathway"] == "mra_plus_10"][0]
check("E-130", mra10["service_years_required"] == 10, "MRA+10 requires 10 years")
check("E-131", mra10["annuity_reduction"] == True, "MRA+10 is reduced")
check("E-132", mra10["reduction_rate_per_year"] == 0.05, "MRA+10 reduction is 5% per year")
check("E-133", mra10["postponement_option"] == True, "MRA+10 allows postponement")

# ── Special Category ──
sc = elig["special_category_retirement"]
check("E-140", sc["eligibility"]["standard"]["age"] == 50, "SC standard age is 50")
check("E-141", sc["eligibility"]["standard"]["service_years"] == 20, "SC standard service is 20")
check("E-142", sc["eligibility"]["any_age"]["service_years"] == 25, "SC any-age service is 25")
check("E-143", sc["mandatory_retirement"]["age"] == 57, "SC mandatory retirement at 57")
check("E-144", sc["annuity_reduction"] == False, "SC retirement is unreduced")
check("E-145", len(sc["eligible_positions"]) >= 5, f"At least 5 eligible position types (got {len(sc['eligible_positions'])})")

# ── VERA/VSIP ──
vera = elig["early_retirement"]["vera"]
check("E-150", vera["eligibility"]["pathway_1"]["age"] == 50, "VERA pathway 1 age 50")
check("E-151", vera["eligibility"]["pathway_1"]["service_years"] == 20, "VERA pathway 1 service 20")
check("E-152", vera["eligibility"]["pathway_2"]["service_years"] == 25, "VERA pathway 2 service 25")
check("E-153", vera["annuity_reduction"] == False, "VERA is unreduced")
check("E-154", vera["srs_eligible"] == True, "VERA eligible for SRS")

vsip = elig["early_retirement"]["vsip"]
check("E-160", vsip["maximum_payment"] == 25000, "VSIP max payment is $25,000")
check("E-161", vsip["taxable"] == True, "VSIP is taxable")
check("E-162", vsip["repayment_if_rehired"] == True, "VSIP requires repayment if rehired")

# ── Deferred Retirement ──
deferred = elig["deferred_retirement"]
check("E-170", deferred["eligibility"]["minimum_service_years"] == 5, "Deferred requires 5 years")
check("E-171", len(deferred["commencement_options"]) == 2, "Two deferred commencement options")

# ── Disability Retirement ──
disability = elig["disability_retirement"]
check("E-180", disability["minimum_service_years"] == 18, "Disability requires 18 months")
check("E-181", disability["fehb_continues"] == True, "Disability continues FEHB")

# ── FEHB Five-Year Rule ──
fehb = elig["fehb_five_year_rule"]
check("E-190", "8905" in fehb["authority"], "FEHB rule cites 5 USC 8905")
check("E-191", len(fehb["exceptions"]) >= 1, "FEHB rule has waiver exceptions")

# ═══════════════════════════════════════════════════════════════
# PART 2: SERVICE CREDIT RULES
# ═══════════════════════════════════════════════════════════════
print("\n=== Service Credit Rules ===\n")

meta2 = svc["metadata"]
check("S-001", meta2["version"] == "1.0", "Version is 1.0")
check("S-002", "2026" in meta2["last_updated"], "Last updated in 2026")
check("S-003", len(meta2["sources"]) >= 6, f"At least 6 sources (got {len(meta2['sources'])})")

# ── Civilian Deposit ──
dep = svc["civilian_deposit"]
check("S-010", dep["fers_rules"]["deposit_rate_pct"] == 1.3, "FERS deposit rate is 1.3%")
check("S-011", dep["csrs_rules"]["pre_october_1982_service"]["deposit_rate_pct"] == 7.0, "CSRS pre-1982 deposit rate is 7%")
check("S-012", dep["csrs_rules"]["post_october_1982_service"]["deposit_rate_pct"] == 7.0, "CSRS post-1982 deposit rate is 7%")
check("S-013", "SF 3108" in dep["fers_rules"]["application_form"], "FERS deposit form is SF 3108")
check("S-014", len(dep["fers_rules"]["post_1988_exceptions"]) >= 2, "At least 2 post-1988 exceptions listed")

# CSRS pre-1982 effect: still credited but 10% reduction
check("S-015", "10%" in dep["csrs_rules"]["pre_october_1982_service"]["effect_if_unpaid"],
      "CSRS pre-1982 unpaid deposit causes 10% reduction")
# CSRS post-1982 effect: NOT credited
check("S-016", "NOT" in dep["csrs_rules"]["post_october_1982_service"]["effect_if_unpaid"],
      "CSRS post-1982 unpaid deposit means no credit")

# ── Redeposit ──
redep = svc["redeposit"]
check("S-020", "October 28, 2009" in redep["fers_rules"]["eligible"], "FERS redeposit cites Oct 28 2009")
check("S-021", "SF 3108" in redep["fers_rules"]["application_form"], "FERS redeposit form is SF 3108")
check("S-022", "4%" in str(redep["csrs_rules"]["refund_before_october_1982"]["interest_rule"]),
      "CSRS pre-1982 redeposit interest starts at 4%")

# ── Military Service Credit ──
mil = svc["military_service_credit"]
check("S-030", mil["general_rule"]["honorable_discharge_required"] == True, "Military buyback requires honorable discharge")
check("S-031", mil["fers_deposit"]["rate_pct"] == 3.0, "FERS military deposit rate is 3%")
check("S-032", mil["csrs_deposit"]["rate_pct"] == 7.0, "CSRS military deposit rate is 7%")
check("S-033", "waive" in mil["interaction_with_military_retirement"]["general_rule"].lower(),
      "Military retirement interaction mentions waiver")
check("S-034", "combat" in mil["interaction_with_military_retirement"]["exception_1"].lower(),
      "Exception 1 is combat-disabled veterans")
check("S-035", "SF 3108" in mil["application_process"]["forms"][0], "Military buyback uses SF 3108 (FERS)")
check("S-036", "SF 2803" in mil["application_process"]["forms"][1], "Military buyback uses SF 2803 (CSRS)")
check("S-037", "DD Form 214" in mil["application_process"]["supporting_documents"][0], "DD-214 required")
check("S-038", "RI 20-97" in mil["application_process"]["supporting_documents"][1], "RI 20-97 required")
check("S-039", mil["application_process"]["minimum_payment"] == 50, "Minimum payment is $50")

# ── Sick Leave Credit ──
sl = svc["sick_leave_credit"]
check("S-050", "111-84" in sl["authority"], "Sick leave authority cites P.L. 111-84")
check("S-051", sl["fers_rules"]["effective_date"] == "2009-10-28", "FERS sick leave effective Oct 28 2009")
check("S-052", "50%" in sl["fers_rules"]["phase_in"]["oct_28_2009_through_dec_31_2013"],
      "Phase-in: 50% through 2013")
check("S-053", "100%" in sl["fers_rules"]["phase_in"]["jan_1_2014_onward"],
      "Phase-in: 100% from 2014")
check("S-054", sl["csrs_rules"]["credit_pct"] == 100, "CSRS always credits 100%")
check("S-055", sl["csrs_rules"]["can_exceed_80pct_cap"] == True, "CSRS sick leave can exceed 80% cap")

# Conversion formula
conv = sl["conversion_formula"]
check("S-060", conv["hours_per_work_year"] == 2087, "2087 hours per work year")
check("S-061", conv["days_per_retirement_year"] == 360, "360 days per retirement year")
check("S-062", conv["days_per_retirement_month"] == 30, "30 days per retirement month")
check("S-063", abs(conv["hours_per_retirement_day"] - 5.797) < 0.01, "~5.797 hours per retirement day")

# Conversion table samples
table = sl["conversion_reference_table"]["samples"]
check("S-070", len(table) >= 15, f"At least 15 conversion samples (got {len(table)})")

# Verify known conversions from OPM
def find_sample(hours):
    for s in table:
        if s["hours"] == hours:
            return s
    return None

s441 = find_sample(441)
check("S-071", s441 is not None and s441["months"] == 2 and s441["days"] == 16,
      "441 hours = 2 months 16 days (OPM example)")
s1452 = find_sample(1452)
check("S-072", s1452 is not None and s1452["months"] == 8 and s1452["days"] == 11,
      "1452 hours = 8 months 11 days (OPM example)")
s2087 = find_sample(2087)
check("S-073", s2087 is not None and s2087["months"] == 12 and s2087["days"] == 0,
      "2087 hours = 12 months 0 days (full year)")
s835 = find_sample(835)
check("S-074", s835 is not None and s835["months"] == 4 and s835["days"] == 24,
      "835 hours = 4 months 24 days (OPM example)")

# Accrual rate
check("S-080", sl["accrual_rate"]["hours_per_pay_period"] == 4, "4 hours sick leave per pay period")
check("S-081", sl["accrual_rate"]["hours_per_year"] == 104, "104 hours sick leave per year")
check("S-082", sl["accrual_rate"]["no_accumulation_limit"] == True, "No limit on sick leave accumulation")

# ── Interest Rates ──
ir = svc["interest_rates"]
check("S-090", ir["pre_1985_rate"]["through_1947"] == 4.0, "Pre-1948 interest rate is 4%")
check("S-091", ir["pre_1985_rate"]["1948_through_1984"] == 3.0, "1948-1984 interest rate is 3%")

rates = ir["variable_rates"]
check("S-092", len(rates) == 42, f"42 years of variable rates 1985-2026 (got {len(rates)})")

# Verify first and last
check("S-093", rates[0]["year"] == 1985, "First variable rate year is 1985")
check("S-094", rates[0]["rate_pct"] == 13.0, "1985 rate is 13.0%")
check("S-095", rates[-1]["year"] == 2026, "Last variable rate year is 2026")
check("S-096", rates[-1]["rate_pct"] == 4.25, "2026 rate is 4.25%")

# Verify 2025 rate from BAL 25-301
r2025 = [r for r in rates if r["year"] == 2025][0]
check("S-097", r2025["rate_pct"] == 4.375, "2025 rate is 4.375% (BAL 25-301)")

# Range check: all rates between 1% and 15%
for r in rates:
    check(f"S-100-{r['year']}", 1.0 <= r["rate_pct"] <= 15.0,
          f"Year {r['year']} rate {r['rate_pct']}% in range 1-15%")

# Verify consecutive years with no gaps
years = [r["year"] for r in rates]
check("S-200", years == list(range(1985, 2027)), "Variable rates cover 1985-2026 consecutively with no gaps")

# Verify some historically known rates
known_rates = {
    1990: 8.75, 2000: 5.875, 2010: 3.875, 2020: 2.5, 2022: 1.375
}
for yr, expected in known_rates.items():
    actual = [r for r in rates if r["year"] == yr][0]["rate_pct"]
    check(f"S-210-{yr}", actual == expected, f"Year {yr} rate is {expected}%")

# ═══════════════════════════════════════════════════════════════
# CROSS-FILE CONSISTENCY
# ═══════════════════════════════════════════════════════════════
print("\n=== Cross-File Consistency ===\n")

# Load fers-computation-rules for cross-checks
comp_path = os.path.join(repo_root, "federal", "fers-computation-rules.json")
if os.path.exists(comp_path):
    with open(comp_path) as f:
        comp = json.load(f)

    # MRA+10 reduction rate should match
    comp_reduction = comp["mra_plus_10_reduction"]["reduction_per_year"]
    elig_reduction = mra10["reduction_rate_per_year"]
    check("X-001", comp_reduction == elig_reduction,
          f"MRA+10 reduction rate consistent: computation={comp_reduction}, eligibility={elig_reduction}")

    # Disability service requirement: 18 months in both
    if "fers_disability" in comp:
        comp_disability_months = comp["fers_disability"].get("eligibility", {}).get("minimum_service_months", None)
        if comp_disability_months is not None:
            check("X-002", comp_disability_months == 18,
                  "Disability 18-month requirement matches computation file")
        else:
            check("X-002", True, "Disability eligibility cross-check skipped (field not present)")
    else:
        check("X-002", True, "Disability cross-check skipped (section not present)")

# Load rates-annual for FERS survivor/COLA cross-checks
rates_path = os.path.join(repo_root, "federal", "rates-annual.json")
if os.path.exists(rates_path):
    with open(rates_path) as f:
        ra = json.load(f)

    # Verify FERS section exists
    check("X-010", "fers" in ra, "rates-annual.json has fers section")

# Load contribution rates for cross-check
contrib_path = os.path.join(repo_root, "federal", "fers-contribution-rates.json")
if os.path.exists(contrib_path):
    with open(contrib_path) as f:
        contrib = json.load(f)
    # FERS deposit rate (1.3%) vs contribution rate for FERS-FRAE (4.4%) — deposit should be lower
    fers_deposit_rate = dep["fers_rules"]["deposit_rate_pct"]
    frae_rate = contrib["cohorts"][2]["employee_rate_pct"]  # FERS-FRAE
    check("X-020", fers_deposit_rate < frae_rate,
          f"Deposit rate {fers_deposit_rate}% < FRAE contribution rate {frae_rate}%")

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"TOTAL: {CHECKS} checks | PASS: {PASS} | FAIL: {FAIL}")
print(f"{'='*60}")

if FAIL > 0:
    sys.exit(1)
