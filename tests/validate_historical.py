#!/usr/bin/env python3
"""
validate_historical.py — CI validation for historical data files
  federal/tsp-limits.json
  federal/ss-bend-points.json
  federal/ss-taxable-max.json
  federal/ira-limits.json

Run: python tests/validate_historical.py
"""
import json
import sys
import os

passed = 0
failed = 0
errors = []

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        msg = f"FAIL: {label}"
        if detail:
            msg += f" — {detail}"
        errors.append(msg)
        print(msg)

def resolve_path(filename):
    """Find the file relative to repo root or CWD."""
    candidates = [
        filename,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return filename

# ============================================================
# 1. TSP LIMITS
# ============================================================
print("=" * 60)
print("TSP Limits Validation")
print("=" * 60)

tsp_path = resolve_path('federal/tsp-limits.json')
with open(tsp_path) as f:
    tsp = json.load(f)

# Structure
check("TSP: has metadata", 'metadata' in tsp)
check("TSP: has current_year", 'current_year' in tsp)
check("TSP: has history", 'history' in tsp)
check("TSP: metadata.version exists", tsp.get('metadata', {}).get('version') is not None)

# Current year structure
cy = tsp.get('current_year', {})
check("TSP: current_year.year is 2026", cy.get('year') == 2026)
check("TSP: elective_deferral_limit present", 'elective_deferral_limit' in cy)
check("TSP: elective_deferral_limit is int", isinstance(cy.get('elective_deferral_limit'), int))
check("TSP: catchup_50_plus present", 'catchup_50_plus' in cy)
check("TSP: super_catchup_60_63 present", 'super_catchup_60_63' in cy)
check("TSP: annual_additions_limit present", 'annual_additions_limit' in cy)

# 2026 spot checks against TSP.gov / IRS Notice 2025-67
check("TSP: 2026 deferral limit = 24500", cy.get('elective_deferral_limit') == 24500)
check("TSP: 2026 catchup 50+ = 8000", cy.get('catchup_50_plus') == 8000)
check("TSP: 2026 super catchup 60-63 = 11250", cy.get('super_catchup_60_63') == 11250)
check("TSP: 2026 total_50_plus = 32500", cy.get('total_50_plus') == 32500)
check("TSP: 2026 total_60_63 = 35750", cy.get('total_60_63') == 35750)
check("TSP: 2026 annual additions = 72000", cy.get('annual_additions_limit') == 72000)

# History
hist = tsp.get('history', [])
check("TSP: history has 30+ entries", len(hist) >= 30)
check("TSP: history entries have year", all('year' in e for e in hist))
check("TSP: history entries have limit", all('limit' in e for e in hist))
check("TSP: years are sequential", 
      sorted([e['year'] for e in hist]) == list(range(min(e['year'] for e in hist), max(e['year'] for e in hist) + 1)),
      f"gaps in year sequence")
check("TSP: earliest year <= 1987", min(e['year'] for e in hist) <= 1987)
check("TSP: latest year = 2026", max(e['year'] for e in hist) == 2026)

# Spot check historical values
hist_by_year = {e['year']: e for e in hist}
check("TSP: 2024 limit = 23000", hist_by_year.get(2024, {}).get('limit') == 23000)
check("TSP: 2020 limit = 19500", hist_by_year.get(2020, {}).get('limit') == 19500)

# Monotonic: limits should generally increase (allow same, not decrease except rare)
limits = [e['limit'] for e in sorted(hist, key=lambda x: x['year'])]
decreases = sum(1 for i in range(1, len(limits)) if limits[i] < limits[i-1])
check("TSP: limits mostly non-decreasing", decreases <= 2, f"{decreases} decreases found")

print(f"  TSP: {passed} checks\n")
tsp_count = passed

# ============================================================
# 2. SS BEND POINTS
# ============================================================
print("=" * 60)
print("SS Bend Points Validation")
print("=" * 60)

bp_path = resolve_path('federal/ss-bend-points.json')
with open(bp_path) as f:
    bp = json.load(f)

# Structure
check("BP: has metadata", 'metadata' in bp)
check("BP: has current_year", 'current_year' in bp)
check("BP: has history", 'history' in bp)

# Current year
bcy = bp.get('current_year', {})
check("BP: current_year.year is 2026", bcy.get('year') == 2026)
check("BP: first_bend_point present", 'first_bend_point' in bcy)
check("BP: second_bend_point present", 'second_bend_point' in bcy)
check("BP: pia_factors present", 'pia_factors' in bcy)

# 2026 spot checks against SSA
check("BP: 2026 first bend = 1286", bcy.get('first_bend_point') == 1286)
check("BP: 2026 second bend = 7749", bcy.get('second_bend_point') == 7749)
check("BP: first < second", bcy.get('first_bend_point', 0) < bcy.get('second_bend_point', 0))

# PIA factors
pia = bcy.get('pia_factors', {})
check("BP: PIA below_first = 0.90", pia.get('below_first') == 0.90)
check("BP: PIA between = 0.32", pia.get('between') == 0.32)
check("BP: PIA above_second = 0.15", pia.get('above_second') == 0.15)

# History
bhist = bp.get('history', [])
check("BP: history has 40+ entries", len(bhist) >= 40)
check("BP: entries have year", all('year' in e for e in bhist))
check("BP: entries have first", all('first' in e for e in bhist))
check("BP: entries have second", all('second' in e for e in bhist))
check("BP: earliest year <= 1979", min(e['year'] for e in bhist) <= 1979)
check("BP: latest year = 2026", max(e['year'] for e in bhist) == 2026)

# Bend points should increase over time
firsts = [(e['year'], e['first']) for e in sorted(bhist, key=lambda x: x['year'])]
first_decreases = sum(1 for i in range(1, len(firsts)) if firsts[i][1] < firsts[i-1][1])
check("BP: first bend mostly non-decreasing", first_decreases <= 1, f"{first_decreases} decreases")

# Cross-field: first always < second
check("BP: first < second in all history", 
      all(e['first'] < e['second'] for e in bhist),
      "found entry where first >= second")

print(f"  BP: {passed - tsp_count} checks\n")
bp_count = passed

# ============================================================
# 3. SS TAXABLE MAXIMUM
# ============================================================
print("=" * 60)
print("SS Taxable Maximum Validation")
print("=" * 60)

stm_path = resolve_path('federal/ss-taxable-max.json')
with open(stm_path) as f:
    stm = json.load(f)

# Structure
check("STM: has metadata", 'metadata' in stm)
check("STM: has current_year", 'current_year' in stm)
check("STM: has history", 'history' in stm)

# Current year
scy = stm.get('current_year', {})
check("STM: current_year.year is 2026", scy.get('year') == 2026)
check("STM: amount present", 'amount' in scy)
check("STM: oasdi_rate_employee present", 'oasdi_rate_employee' in scy)

# 2026 spot checks against SSA
check("STM: 2026 amount = 184500", scy.get('amount') == 184500)
check("STM: 2026 employee rate = 0.062", scy.get('oasdi_rate_employee') == 0.062)
check("STM: 2026 employer rate = 0.062", scy.get('oasdi_rate_employer') == 0.062)
check("STM: 2026 self-employed rate = 0.124", scy.get('oasdi_rate_self_employed') == 0.124)

# Max tax cross-check: amount * rate = max_tax
expected_max = round(scy.get('amount', 0) * scy.get('oasdi_rate_employee', 0), 2)
actual_max = scy.get('max_employee_tax', 0)
check("STM: max_employee_tax = amount * rate", 
      abs(expected_max - actual_max) < 1.0,
      f"expected ~{expected_max}, got {actual_max}")

# History
shist = stm.get('history', [])
check("STM: history has 80+ entries", len(shist) >= 80)
check("STM: entries have year", all('year' in e for e in shist))
check("STM: entries have amount", all('amount' in e for e in shist))
check("STM: earliest year <= 1937", min(e['year'] for e in shist) <= 1937)
check("STM: latest year = 2026", max(e['year'] for e in shist) == 2026)

# Spot check historical
shist_by_year = {e['year']: e for e in shist}
check("STM: 2024 amount = 168600", shist_by_year.get(2024, {}).get('amount') == 168600)
check("STM: 2020 amount = 137700", shist_by_year.get(2020, {}).get('amount') == 137700)

# Mostly non-decreasing (SS taxable max has never decreased)
amounts = [e['amount'] for e in sorted(shist, key=lambda x: x['year'])]
stm_decreases = sum(1 for i in range(1, len(amounts)) if amounts[i] < amounts[i-1])
check("STM: amounts non-decreasing", stm_decreases == 0, f"{stm_decreases} decreases found")

print(f"  STM: {passed - bp_count} checks\n")
stm_count = passed

# ============================================================
# 4. IRA LIMITS
# ============================================================
print("=" * 60)
print("IRA Limits Validation")
print("=" * 60)

ira_path = resolve_path('federal/ira-limits.json')
with open(ira_path) as f:
    ira = json.load(f)

# Structure
check("IRA: has metadata", 'metadata' in ira)
check("IRA: has annual_limits", 'annual_limits' in ira)
check("IRA: metadata version = 2.0", ira.get('metadata', {}).get('version') == '2.0')

limits = ira.get('annual_limits', [])
check("IRA: has 50+ entries", len(limits) >= 50)
check("IRA: entries have year", all('year' in e for e in limits))
check("IRA: entries have contribution_limit", all('contribution_limit' in e for e in limits))
check("IRA: entries have roth_available", all('roth_available' in e for e in limits))

years = [e['year'] for e in limits]
check("IRA: earliest year <= 1975", min(years) <= 1975)
check("IRA: latest year = 2026", max(years) == 2026)
check("IRA: years sequential", 
      sorted(years) == list(range(min(years), max(years) + 1)),
      "gaps in year sequence")

# 2026 spot checks
ira_by_year = {e['year']: e for e in limits}
e2026 = ira_by_year.get(2026, {})
check("IRA: 2026 contribution_limit = 7500", e2026.get('contribution_limit') == 7500)
check("IRA: 2026 catchup_50_plus = 1100", e2026.get('catchup_50_plus') == 1100)
check("IRA: 2026 roth_available = true", e2026.get('roth_available') == True)

# Roth availability timeline
check("IRA: 1997 roth_available = false", ira_by_year.get(1997, {}).get('roth_available') == False)
check("IRA: 1998 roth_available = true", ira_by_year.get(1998, {}).get('roth_available') == True,
      "Roth IRA introduced in 1998")

# Roth income limits structure (post-1998)
roth_years = [e for e in limits if e.get('roth_available') and e.get('roth_income_limits')]
check("IRA: Roth years have income limits", len(roth_years) >= 25,
      f"found {len(roth_years)} years with roth_income_limits")

if roth_years:
    sample = roth_years[-1]  # most recent
    ril = sample.get('roth_income_limits', {})
    check("IRA: Roth limits have single", 'single' in ril)
    check("IRA: Roth limits have married_joint", 'married_joint' in ril)
    check("IRA: Roth limits have married_separate", 'married_separate' in ril)
    
    for status in ['single', 'married_joint', 'married_separate']:
        if status in ril:
            check(f"IRA: {status} has full_contribution_below", 
                  'full_contribution_below' in ril[status])
            check(f"IRA: {status} has ineligible_at", 
                  'ineligible_at' in ril[status])
            # ineligible_at > full_contribution_below
            fcb = ril[status].get('full_contribution_below', 0)
            ina = ril[status].get('ineligible_at', 0)
            check(f"IRA: {status} ineligible_at > full_contribution_below",
                  ina > fcb or (status == 'married_separate' and fcb == 0),
                  f"fcb={fcb}, ina={ina}")

# 2026 Roth income limit spot checks
r2026 = e2026.get('roth_income_limits', {})
check("IRA: 2026 single full_below = 153000", 
      r2026.get('single', {}).get('full_contribution_below') == 153000)
check("IRA: 2026 single ineligible = 168000",
      r2026.get('single', {}).get('ineligible_at') == 168000)
check("IRA: 2026 MFJ full_below = 242000",
      r2026.get('married_joint', {}).get('full_contribution_below') == 242000)
check("IRA: 2026 MFJ ineligible = 252000",
      r2026.get('married_joint', {}).get('ineligible_at') == 252000)
check("IRA: 2026 MFS ineligible = 10000",
      r2026.get('married_separate', {}).get('ineligible_at') == 10000)

# Contribution limits non-decreasing
clims = [e['contribution_limit'] for e in sorted(limits, key=lambda x: x['year'])]
ira_decreases = sum(1 for i in range(1, len(clims)) if clims[i] < clims[i-1])
check("IRA: contribution limits non-decreasing", ira_decreases == 0, 
      f"{ira_decreases} decreases found")

# Pre-Roth years should not have roth_income_limits
pre_roth = [e for e in limits if not e.get('roth_available')]
bad_pre_roth = [e for e in pre_roth if 'roth_income_limits' in e]
check("IRA: pre-Roth years have no roth_income_limits", len(bad_pre_roth) == 0,
      f"{len(bad_pre_roth)} pre-Roth entries have income limits")

print(f"  IRA: {passed - stm_count} checks\n")
ira_count = passed

# ============================================================
# 5. SSA ACTUARIAL LIFE TABLE
# ============================================================
print("=" * 60)
print("SSA Life Table Validation")
print("=" * 60)

lt_path = resolve_path('reference/ssa-life-table.json')
with open(lt_path) as f:
    lt = json.load(f)

# Structure
check("LT: has metadata", 'metadata' in lt)
check("LT: has life_table", 'life_table' in lt)
check("LT: has retirement_planning_reference", 'retirement_planning_reference' in lt)
check("LT: metadata version = 1.0", lt.get('metadata', {}).get('version') == '1.0')
check("LT: data_year = 2022", lt.get('metadata', {}).get('data_year') == 2022)
check("LT: trustees_report = 2025", lt.get('metadata', {}).get('trustees_report') == '2025')

# Life table entries
ltable = lt.get('life_table', [])
check("LT: has 120 entries", len(ltable) == 120)
check("LT: ages 0-119", 
      ltable[0]['age'] == 0 and ltable[-1]['age'] == 119 if ltable else False)
check("LT: all entries have age", all('age' in e for e in ltable))
check("LT: all entries have male", all('male' in e for e in ltable))
check("LT: all entries have female", all('female' in e for e in ltable))

# Male/female structure
if ltable:
    sample = ltable[65]  # age 65
    for sex in ['male', 'female']:
        s = sample.get(sex, {})
        check(f"LT: age 65 {sex} has death_probability", 'death_probability' in s)
        check(f"LT: age 65 {sex} has number_of_lives", 'number_of_lives' in s)
        check(f"LT: age 65 {sex} has life_expectancy", 'life_expectancy' in s)

# Death probability range checks
for entry in ltable:
    age = entry['age']
    for sex in ['male', 'female']:
        dp = entry[sex]['death_probability']
        if not (0 < dp <= 1.0):
            check(f"LT: age {age} {sex} death_prob in (0,1]", False, f"got {dp}")
            break
else:
    check("LT: all death probabilities in valid range (0,1]", True)

# Age 119 should have death_probability = 1.0
check("LT: age 119 male death_prob = 1.0", ltable[-1]['male']['death_probability'] == 1.0)
check("LT: age 119 female death_prob = 1.0", ltable[-1]['female']['death_probability'] == 1.0)

# Life expectancy decreases with age
male_les = [(e['age'], e['male']['life_expectancy']) for e in ltable]
le_increases = sum(1 for i in range(1, len(male_les)) if male_les[i][1] > male_les[i-1][1])
check("LT: male life expectancy decreases with age", le_increases == 0,
      f"{le_increases} increases found")

# Female life expectancy > male at most ages
female_gt_male = sum(1 for e in ltable if e['age'] <= 100 and 
                     e['female']['life_expectancy'] > e['male']['life_expectancy'])
check("LT: female LE > male LE for ages 0-100", female_gt_male >= 95,
      f"female > male at {female_gt_male}/101 ages")

# Spot checks against SSA source (2022 period table, 2025 TR)
check("LT: age 0 male LE = 74.74", ltable[0]['male']['life_expectancy'] == 74.74)
check("LT: age 0 female LE = 80.18", ltable[0]['female']['life_expectancy'] == 80.18)
check("LT: age 65 male LE = 17.48", ltable[65]['male']['life_expectancy'] == 17.48)
check("LT: age 65 female LE = 20.12", ltable[65]['female']['life_expectancy'] == 20.12)
check("LT: age 65 male death_prob = 0.017897", ltable[65]['male']['death_probability'] == 0.017897)

# Retirement planning reference
ref = lt.get('retirement_planning_reference', {}).get('ages', {})
check("LT: has planning ref for age 62", '62' in ref)
check("LT: has planning ref for age 65", '65' in ref)
check("LT: has planning ref for age 67", '67' in ref)
check("LT: has planning ref for age 70", '70' in ref)

# Cross-check planning ref against life table
if '65' in ref:
    ref65 = ref['65']
    check("LT: planning ref 65 male LE matches table", 
          ref65.get('male_life_expectancy') == ltable[65]['male']['life_expectancy'])
    check("LT: planning ref 65 expected death age = 65 + LE",
          ref65.get('male_expected_age_at_death') == round(65 + ltable[65]['male']['life_expectancy'], 1))

print(f"  LT: {passed - ira_count} checks\n")
lt_count = passed

# ============================================================
# 6. COUNTY PROPERTY TAX
# ============================================================
print("=" * 60)
print("County Property Tax Validation")
print("=" * 60)

cpt_path = resolve_path('states/counties/county-property-tax.json')
with open(cpt_path) as f:
    cpt = json.load(f)

# Structure
check("CPT: has metadata", 'metadata' in cpt)
check("CPT: has counties", 'counties' in cpt)
check("CPT: metadata version = 1.0", cpt.get('metadata', {}).get('version') == '1.0')

counties = cpt.get('counties', [])
check("CPT: has 10 counties", len(counties) == 10)

# Required fields per county
required_fields = ['county', 'state_code', 'fips', 'military_installations', 
                   'property_tax', 'veteran_exemptions', 'application', 'source']
for county in counties:
    name = f"{county.get('county', '?')}, {county.get('state_code', '?')}"
    for field in required_fields:
        check(f"CPT: {name} has {field}", field in county)

# State codes should be valid 2-letter codes
valid_states = {'VA', 'MD', 'NC', 'TX', 'FL', 'CO', 'WA', 'AZ', 'NV', 'DC',
                'GA', 'PA', 'AK', 'HI', 'OR'}
for county in counties:
    check(f"CPT: {county['county']} state_code valid",
          county.get('state_code') in valid_states,
          f"got {county.get('state_code')}")

# FIPS codes should be 5 digits
for county in counties:
    fips = county.get('fips', '')
    check(f"CPT: {county['county']} FIPS is 5 digits",
          len(fips) == 5 and fips.isdigit(),
          f"got {fips}")

# Each county should have at least one military installation
for county in counties:
    check(f"CPT: {county['county']} has military installations",
          len(county.get('military_installations', [])) >= 1)

# Veteran exemptions should have at least one entry with a type
for county in counties:
    exemptions = county.get('veteran_exemptions', {})
    types_found = [v.get('type') for v in exemptions.values() if isinstance(v, dict)]
    valid_types = {'full_exemption', 'partial_exemption', 'reduction'}
    check(f"CPT: {county['county']} has valid exemption type",
          any(t in valid_types for t in types_found),
          f"types: {types_found}")

# Spot checks
fairfax = [c for c in counties if c['county'] == 'Fairfax County']
if fairfax:
    f = fairfax[0]
    check("CPT: Fairfax rate = 1.095", f['property_tax'].get('real_estate_rate_per_100') == 1.095)
    check("CPT: Fairfax is full_exemption",
          f['veteran_exemptions'].get('disabled_veteran_100_pct', {}).get('type') == 'full_exemption')

bexar = [c for c in counties if c['county'] == 'Bexar County']
if bexar:
    b = bexar[0]
    check("CPT: Bexar has partial tiers",
          len(b['veteran_exemptions'].get('disabled_veteran_partial', {}).get('tiers', [])) == 4)

print(f"  CPT: {passed - lt_count} checks\n")
cpt_count = passed

# ============================================================
# 7. COLA HISTORY
# ============================================================
print("=" * 60)
print("COLA History Validation")
print("=" * 60)

cola_path = resolve_path('federal/cola-history.json')
with open(cola_path) as f:
    cola = json.load(f)

check("COLA: has metadata", 'metadata' in cola)
check("COLA: has annual_cola", 'annual_cola' in cola)
check("COLA: has cola_formula", 'cola_formula' in cola)
check("COLA: has summary_statistics", 'summary_statistics' in cola)
check("COLA: metadata version = 1.0", cola.get('metadata', {}).get('version') == '1.0')

entries = cola.get('annual_cola', [])
check("COLA: has 51 entries", len(entries) == 51)
check("COLA: first year = 1975", entries[0].get('year') == 1975 if entries else False)
check("COLA: last year = 2025", entries[-1].get('year') == 2025 if entries else False)

# All entries have required fields
check("COLA: all have year", all('year' in e for e in entries))
check("COLA: all have social_security", all('social_security' in e for e in entries))
check("COLA: all have csrs", all('csrs' in e for e in entries))
check("COLA: all have va", all('va' in e for e in entries))

# FERS present for 1987+
fers_entries = [e for e in entries if e['year'] >= 1987]
check("COLA: FERS present for 1987+", all('fers' in e for e in fers_entries))

# COLA values are non-negative
check("COLA: all SS COLAs >= 0", all(e['social_security'] >= 0 for e in entries))

# Spot checks against SSA source
cola_by_year = {e['year']: e for e in entries}
check("COLA: 1980 SS = 14.3", cola_by_year.get(1980, {}).get('social_security') == 14.3)
check("COLA: 2009 SS = 0.0", cola_by_year.get(2009, {}).get('social_security') == 0.0)
check("COLA: 2010 SS = 0.0", cola_by_year.get(2010, {}).get('social_security') == 0.0)
check("COLA: 2015 SS = 0.0", cola_by_year.get(2015, {}).get('social_security') == 0.0)
check("COLA: 2022 SS = 8.7", cola_by_year.get(2022, {}).get('social_security') == 8.7)
check("COLA: 2025 SS = 2.8", cola_by_year.get(2025, {}).get('social_security') == 2.8)

# CSRS = SS (no cap)
check("COLA: CSRS matches SS for all years", 
      all(e['csrs'] == e['social_security'] for e in entries))

# VA = SS
check("COLA: VA matches SS for all years",
      all(e['va'] == e['social_security'] for e in entries))

# FERS cap formula validation
for e in fers_entries:
    ss = e['social_security']
    fers = e['fers']
    if ss <= 2.0:
        expected = ss
    elif ss <= 3.0:
        expected = 2.0
    else:
        expected = round(ss - 1.0, 1)
    check(f"COLA: {e['year']} FERS cap correct (SS={ss}, FERS={fers})",
          fers == expected, f"expected {expected}, got {fers}")

# Summary stats
stats = cola.get('summary_statistics', {})
check("COLA: zero_cola_years = [2009, 2010, 2015]",
      stats.get('zero_cola_years') == [2009, 2010, 2015])

print(f"  COLA: {passed - cpt_count} checks\n")

# ============================================================
# SUMMARY
# ============================================================
print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if errors:
    print("\nFailures:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("\n✅ All historical data validation checks passed!")
    sys.exit(0)
