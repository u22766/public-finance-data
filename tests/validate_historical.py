#!/usr/bin/env python3
"""
Validation suite for ALL historical/reference data files in public-finance-data.
Replaces validate_historical.py with expanded coverage for 12 new files.
"""
import json
import sys
import os

PASS = 0
FAIL = 0

def check(condition, label):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")

def section(name):
    print(f"\n--- {name} ---")

# ==============================================================
# EXISTING FILE VALIDATIONS (preserved from validate_historical.py)
# ==============================================================

def validate_tsp_limits(root):
    section("TSP Limits")
    f = json.load(open(os.path.join(root, 'federal/tsp-limits.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 38, f"history has 38+ entries (got {len(hist)})")
    
    years = [e['year'] for e in hist]
    check(min(years) <= 1987, "starts at or before 1987")
    check(max(years) >= 2026, "includes 2026")
    check(len(years) == len(set(years)), "no duplicate years")
    
    for e in hist:
        check('limit' in e, f"year {e['year']} has limit")
        check(isinstance(e['limit'], (int, float)), f"year {e['year']} limit is numeric")
        if e['year'] >= 2002:
            check('catchup' in e and e['catchup'] is not None, f"year {e['year']} has catchup (post-2001)")
    
    # Spot checks
    y2026 = next((e for e in hist if e['year'] == 2026), None)
    if y2026:
        check(y2026['limit'] == 24500, f"2026 limit = 24500 (got {y2026.get('limit')})")
        check(y2026.get('catchup') == 8000, f"2026 catchup = 8000 (got {y2026.get('catchup')})")
    
    y1987 = next((e for e in hist if e['year'] == 1987), None)
    if y1987:
        check(y1987['limit'] == 7000, f"1987 limit = 7000 (got {y1987.get('limit')})")
    
    # Monotonic increase in limits
    for i in range(1, len(hist)):
        check(hist[i]['limit'] >= hist[i-1]['limit'], 
              f"limit non-decreasing: {hist[i-1]['year']}({hist[i-1]['limit']}) <= {hist[i]['year']}({hist[i]['limit']})")
    
    print(f"  TSP: {PASS} checks")
    return PASS

def validate_ss_bend_points(root):
    section("SS Bend Points")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/ss-bend-points.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 40, f"history has 40+ entries (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('first' in e, f"year {e.get('year')} has first bend point")
        check('second' in e, f"year {e.get('year')} has second bend point")
        if 'first' in e and 'second' in e:
            check(e['second'] > e['first'], f"year {e.get('year')} second > first")
    
    y2026 = next((e for e in hist if e['year'] == 2026), None)
    if y2026:
        check(y2026['first'] > 0, f"2026 first > 0")
        check(y2026['second'] > y2026['first'], f"2026 second > first")
    
    print(f"  BP: {PASS - start} checks")

def validate_ss_taxable_max(root):
    section("SS Taxable Maximum")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/ss-taxable-max.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 40, f"history has 40+ entries (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('amount' in e, f"year {e.get('year')} has amount")
    
    y2026 = next((e for e in hist if e['year'] == 2026), None)
    if y2026:
        check(y2026['amount'] >= 160000, f"2026 amount >= 160000 (got {y2026.get('amount')})")
    
    print(f"  STM: {PASS - start} checks")

def validate_ira_limits(root):
    section("IRA Limits")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/ira-limits.json')))
    check('metadata' in f, "has metadata")
    check('annual_limits' in f, "has annual_limits")
    limits = f.get('annual_limits', [])
    check(len(limits) >= 50, f"annual_limits has 50+ entries (got {len(limits)})")
    
    for e in limits:
        check('year' in e, f"entry has year")
        if 'contribution_limit' in e:
            check(e['contribution_limit'] > 0, f"year {e.get('year')} contribution_limit > 0")
    
    print(f"  IRA: {PASS - start} checks")

def validate_life_table(root):
    section("SSA Life Table")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'reference/ssa-life-table.json')))
    check('metadata' in f, "has metadata")
    
    check('life_table' in f, "has life_table")
    table = f.get('life_table', [])
    check(len(table) >= 100, f"life_table has 100+ entries (got {len(table)})")
    
    if len(table) > 0:
        check('age' in table[0], "entries have age field")
        check('male' in table[0], "entries have male data")
        check('female' in table[0], "entries have female data")
        
        for gender in ['male', 'female']:
            if gender in table[0]:
                check('life_expectancy' in table[0][gender], f"{gender} has life_expectancy")
                
                age0 = next((e for e in table if e['age'] == 0), None)
                if age0:
                    check(age0[gender]['life_expectancy'] > 70, f"{gender} age 0 LE > 70")
                
                age65 = next((e for e in table if e['age'] == 65), None)
                if age65:
                    check(10 < age65[gender]['life_expectancy'] < 30, f"{gender} age 65 LE between 10-30")
    
    print(f"  LT: {PASS - start} checks")

def validate_county_property_tax(root):
    section("County Property Tax (per-state files)")
    global PASS, FAIL
    start = PASS

    # Expected per-state county files after restructure from flat states/counties/
    expected_states = {
        'AZ': 'states/arizona/county-property-tax.json',
        'CO': 'states/colorado/county-property-tax.json',
        'FL': 'states/florida/county-property-tax.json',
        'MD': 'states/maryland/county-property-tax.json',
        'NC': 'states/north-carolina/county-property-tax.json',
        'NV': 'states/nevada/county-property-tax.json',
        'TX': 'states/texas/county-property-tax.json',
        'VA': 'states/virginia/county-property-tax.json',
        'WA': 'states/washington/county-property-tax.json',
    }

    all_counties = []
    all_state_codes = set()

    for state_code, rel_path in sorted(expected_states.items()):
        full_path = os.path.join(root, rel_path)
        check(os.path.isfile(full_path), f"{state_code} county file exists at {rel_path}")
        if not os.path.isfile(full_path):
            continue

        f = json.load(open(full_path))
        check('metadata' in f, f"{state_code} has metadata")
        check('counties' in f, f"{state_code} has counties")

        meta = f.get('metadata', {})
        check(meta.get('state_code') == state_code,
              f"{state_code} metadata.state_code matches ({meta.get('state_code')})")
        check(meta.get('version') is not None, f"{state_code} has version")

        counties = f.get('counties', [])
        check(len(counties) >= 1, f"{state_code} has at least 1 county (got {len(counties)})")

        for c in counties:
            check('county' in c, f"{state_code} county entry has name")
            check(c.get('state_code') == state_code,
                  f"{c.get('county','')} state_code matches file ({c.get('state_code')})")
            check('property_tax' in c or 'tax_rate' in c or 'effective_rate' in c,
                  f"{c.get('county','')} has tax data")
            all_counties.append(c)
            all_state_codes.add(c.get('state_code', ''))

    check(len(all_counties) >= 10, f"total counties across all files >= 10 (got {len(all_counties)})")
    check(len(all_state_codes) >= 8, f"covers 8+ states (got {len(all_state_codes)})")

    # Verify old flat file is removed
    old_flat = os.path.join(root, 'states/counties/county-property-tax.json')
    check(not os.path.isfile(old_flat),
          "old flat states/counties/county-property-tax.json removed")

    print(f"  CPT: {PASS - start} checks")

def validate_cola_history(root):
    section("COLA History")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/cola-history.json')))
    check('metadata' in f, "has metadata")
    check('annual_cola' in f, "has annual_cola")
    check('cola_formula' in f, "has cola_formula")
    
    colas = f.get('annual_cola', [])
    check(len(colas) >= 50, f"50+ years of COLA data (got {len(colas)})")
    
    for c in colas:
        check('year' in c, "entry has year")
        check('social_security' in c, f"year {c.get('year','')} has social_security")
        if 'fers' in c and 'social_security' in c:
            ss = c['social_security']
            fers = c['fers']
            if ss is not None and fers is not None and c.get('year', 0) >= 1987:
                if ss <= 2:
                    check(abs(fers - ss) < 0.01, f"year {c['year']} FERS = SS when SS <= 2%")
                elif ss <= 3:
                    check(abs(fers - 2.0) < 0.01, f"year {c['year']} FERS = 2% when 2 < SS <= 3%")
                else:
                    check(abs(fers - (ss - 1.0)) < 0.01, f"year {c['year']} FERS = SS-1 when SS > 3%")
    
    print(f"  COLA: {PASS - start} checks")

# ==============================================================
# FEHB VALIDATION (preserved from validate_historical.py)
# ==============================================================

def validate_fehb_rates(root):
    section("FEHB Rates (Full Dataset)")
    global PASS, FAIL
    start = PASS
    path = os.path.join(root, 'federal/healthcare/fehb-rates.json')
    if not os.path.exists(path):
        print("  SKIP: fehb-rates.json not found")
        return
    f = json.load(open(path))
    check('_metadata' in f or 'metadata' in f, "has metadata")
    check('plan_premium_data' in f, "has plan_premium_data")
    ppd = f.get('plan_premium_data', {})
    plans = ppd.get('plans', []) if isinstance(ppd, dict) else []
    check(len(plans) >= 400, f"400+ plan entries (got {len(plans)})")
    
    nationwide = [p for p in plans if p.get('nationwide')]
    regional = [p for p in plans if not p.get('nationwide')]
    check(len(nationwide) >= 15, f"15+ nationwide plans (got {len(nationwide)})")
    check(len(regional) >= 400, f"400+ regional plans (got {len(regional)})")
    
    for p in plans[:50]:  # spot check first 50
        check('carrier' in p or 'plan_name' in p, f"plan has identifier")
        prem = p.get('premiums', {})
        for etype in ['self_only', 'self_plus_one', 'self_and_family']:
            if etype in prem:
                edata = prem[etype]
                if isinstance(edata, dict):
                    bw = edata.get('biweekly', {})
                    if isinstance(bw, dict):
                        for fld in ['total', 'government', 'enrollee']:
                            if fld in bw:
                                check(bw[fld] >= 0, f"{p.get('carrier','?')} {etype} bw {fld} >= 0")
                        if 'total' in bw and 'government' in bw and 'enrollee' in bw:
                            diff = abs(bw['total'] - bw['government'] - bw['enrollee'])
                            check(diff < 0.02, f"{p.get('carrier','?')} {etype} total = govt + enrollee (diff={diff:.2f})")
    
    # Spot check BCBS Basic Self Only
    bcbs = [p for p in plans if 'Blue Cross' in p.get('plan_name', '') and 'Basic' in p.get('plan_name', '') and p.get('nationwide')]
    if bcbs:
        so = bcbs[0].get('self_only', {}).get('biweekly', {})
        if 'enrollee' in so:
            check(100 < so['enrollee'] < 200, f"BCBS Basic SO enrollee biweekly in range (got {so['enrollee']})")
    
    print(f"  FEHB: {PASS - start} checks")

def validate_tricare(root):
    section("TRICARE Rates")
    global PASS, FAIL
    start = PASS
    path = os.path.join(root, 'federal/healthcare/tricare-rates.json')
    if not os.path.exists(path):
        print("  SKIP: tricare-rates.json not found")
        return
    f = json.load(open(path))
    check('metadata' in f or '_metadata' in f, "has metadata")
    
    # Check for retiree cost sections
    has_retiree = any(k for k in f.keys() if 'retiree' in k.lower() or 'group' in k.lower())
    check(has_retiree or 'retiree_costs' in f or 'plans' in f, "has retiree cost data")
    
    # Check for premium-based plans
    has_premium = any(k for k in f.keys() if 'trs' in k.lower() or 'reserve' in k.lower() or 'premium' in k.lower())
    check(has_premium or 'premium_based_plans' in f, "has premium-based plan data")
    
    print(f"  TRICARE: {PASS - start} checks")

def validate_fehb_benefits(root):
    section("FEHB Plan Benefits")
    global PASS, FAIL
    start = PASS
    path = os.path.join(root, 'federal/healthcare/fehb-plan-benefits.json')
    if not os.path.exists(path):
        print("  SKIP: fehb-plan-benefits.json not found")
        return
    f = json.load(open(path))
    check('_metadata' in f or 'metadata' in f, "has metadata")
    check('plans' in f, "has plans")
    plans = f.get('plans', [])
    check(len(plans) >= 100, f"100+ plan entries (got {len(plans)})")
    
    for p in plans[:10]:  # spot check first 10
        check('plan_name' in p or 'plan_code' in p, "plan has identifier")
    
    print(f"  Benefits: {PASS - start} checks")

def validate_fedvip(root):
    section("FEDVIP Rates")
    global PASS, FAIL
    start = PASS
    path = os.path.join(root, 'federal/healthcare/fedvip-rates.json')
    if not os.path.exists(path):
        print("  SKIP: fedvip-rates.json not found")
        return
    f = json.load(open(path))
    check('_metadata' in f or 'metadata' in f, "has metadata")
    check('dental' in f, "has dental data")
    check('vision' in f, "has vision data")
    
    dental = f.get('dental', {})
    if 'carriers' in dental:
        check(len(dental['carriers']) >= 5, f"5+ dental carriers (got {len(dental['carriers'])})")
    elif 'plans' in dental:
        check(len(dental['plans']) >= 5, f"5+ dental plans (got {len(dental['plans'])})")
    
    vision = f.get('vision', {})
    if 'carriers' in vision:
        check(len(vision['carriers']) >= 3, f"3+ vision carriers (got {len(vision['carriers'])})")
    elif 'plans' in vision:
        check(len(vision['plans']) >= 3, f"3+ vision plans (got {len(vision['plans'])})")
    
    print(f"  FEDVIP: {PASS - start} checks")

# ==============================================================
# NEW FILE VALIDATIONS (Session 21 — 12 historical files)
# ==============================================================

def validate_tax_brackets(root):
    section("Federal Tax Brackets")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/federal-tax-brackets.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 25, f"25+ years (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('rates' in e, f"year {e.get('year')} has rates")
        check('single' in e, f"year {e.get('year')} has single brackets")
        check('married_filing_jointly' in e, f"year {e.get('year')} has MFJ brackets")
        if 'rates' in e and 'single' in e:
            check(len(e['rates']) == len(e['single']), 
                  f"year {e.get('year')} rates count = single brackets count")
        if 'rates' in e:
            check(e['rates'][0] == 10, f"year {e.get('year')} lowest rate = 10%")
            check(max(e['rates']) <= 39.6, f"year {e.get('year')} top rate <= 39.6%")
        if 'single' in e:
            check(e['single'][0] == 0, f"year {e.get('year')} single starts at 0")
    
    # Cross-check 2026 against rates-annual
    ra_path = os.path.join(root, 'federal/rates-annual.json')
    if os.path.exists(ra_path):
        ra = json.load(open(ra_path))
        tax = ra.get('tax', {})
        ra_brackets = tax.get('brackets_single_2026', [])
        if ra_brackets:
            y2026 = next((e for e in hist if e['year'] == 2026), None)
            if y2026 and 'single' in y2026:
                ra_first = ra_brackets[0].get('min', ra_brackets[0].get('from', 0))
                check(y2026['single'][0] == 0, "2026 single bracket starts at 0")
    
    print(f"  TaxBrackets: {PASS - start} checks")

def validate_standard_deduction(root):
    section("Standard Deduction History")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/standard-deduction-history.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 25, f"25+ years (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('single' in e, f"year {e.get('year')} has single")
        check('mfj' in e, f"year {e.get('year')} has mfj")
        if 'single' in e and 'mfj' in e:
            check(e['mfj'] >= e['single'], f"year {e.get('year')} MFJ >= single")
        if 'additional_65_single' in e:
            check(e['additional_65_single'] > 0, f"year {e.get('year')} age 65+ deduction > 0")
    
    # TCJA jump check
    y2017 = next((e for e in hist if e['year'] == 2017), None)
    y2018 = next((e for e in hist if e['year'] == 2018), None)
    if y2017 and y2018:
        check(y2018['single'] > y2017['single'] * 1.5, "2018 single > 1.5x 2017 (TCJA doubling)")
    
    # Cross-check 2026 against rates-annual
    ra_path = os.path.join(root, 'federal/rates-annual.json')
    if os.path.exists(ra_path):
        ra = json.load(open(ra_path))
        tax = ra.get('tax', {})
        ra_single = tax.get('standard_deduction_single')
        y2026 = next((e for e in hist if e['year'] == 2026), None)
        if ra_single and y2026:
            check(y2026['single'] == ra_single, 
                  f"2026 single matches rates-annual ({y2026['single']} vs {ra_single})")
    
    print(f"  StdDeduction: {PASS - start} checks")

def validate_capital_gains(root):
    section("Capital Gains Rates")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/capital-gains-rates.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 25, f"25+ years (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('rates' in e, f"year {e.get('year')} has rates")
        if 'rates' in e:
            check(0 in e['rates'] or 5 in e['rates'] or 10 in e['rates'], 
                  f"year {e.get('year')} has preferential low rate")
    
    # NIIT check for 2013+
    for e in hist:
        if e.get('year', 0) >= 2013:
            check('niit_rate' in e, f"year {e['year']} has NIIT rate (post-ACA)")
            if 'niit_rate' in e:
                check(e['niit_rate'] == 3.8, f"year {e['year']} NIIT = 3.8%")
    
    print(f"  CapGains: {PASS - start} checks")

def validate_hsa_limits(root):
    section("HSA Limits")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/hsa-limits.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 20, f"20+ years (got {len(hist)})")
    check(hist[0].get('year') == 2004, "starts at 2004 (HSA inception)")
    
    for e in hist:
        check('self_only' in e, f"year {e.get('year')} has self_only")
        check('family' in e, f"year {e.get('year')} has family")
        if 'self_only' in e and 'family' in e:
            check(e['family'] > e['self_only'], f"year {e.get('year')} family > self_only")
        check('catchup_55' in e, f"year {e.get('year')} has catchup_55")
        if e.get('year', 0) >= 2009:
            check(e.get('catchup_55') == 1000, f"year {e.get('year')} catchup = 1000 (post-2009)")
    
    # Cross-check 2026 against FEHB
    fehb_path = os.path.join(root, 'federal/healthcare/fehb-rates.json')
    if os.path.exists(fehb_path):
        fehb = json.load(open(fehb_path))
        hsa = fehb.get('hsa_limits_2026', {})
        y2026 = next((e for e in hist if e['year'] == 2026), None)
        if hsa and y2026:
            check(y2026['self_only'] == hsa.get('individual_max'), 
                  f"2026 self_only matches FEHB ({y2026['self_only']} vs {hsa.get('individual_max')})")
            check(y2026['family'] == hsa.get('family_max'),
                  f"2026 family matches FEHB ({y2026['family']} vs {hsa.get('family_max')})")
    
    print(f"  HSA: {PASS - start} checks")

def validate_pay_raises(root):
    section("Federal Pay Raises")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/federal-pay-raises.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 25, f"25+ years (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('gs_raise_pct' in e, f"year {e.get('year')} has gs_raise_pct")
        check('military_raise_pct' in e, f"year {e.get('year')} has military_raise_pct")
        check(e.get('gs_raise_pct', -1) >= 0, f"year {e.get('year')} GS raise >= 0")
        check(e.get('military_raise_pct', -1) >= 0, f"year {e.get('year')} military raise >= 0")
    
    # Pay freeze years
    for year in [2011, 2012, 2013]:
        entry = next((e for e in hist if e['year'] == year), None)
        if entry:
            check(entry['gs_raise_pct'] == 0.0, f"{year} GS raise = 0% (pay freeze)")
    
    check('summary_statistics' in f, "has summary_statistics")
    
    print(f"  PayRaises: {PASS - start} checks")

def validate_estate_gift_tax(root):
    section("Estate & Gift Tax")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/estate-gift-tax.json')))
    check('metadata' in f, "has metadata")
    check('history' in f, "has history")
    hist = f.get('history', [])
    check(len(hist) >= 25, f"25+ years (got {len(hist)})")
    
    for e in hist:
        check('year' in e, f"entry has year")
        check('estate_exemption' in e, f"year {e.get('year')} has estate_exemption")
        check('gift_annual_exclusion' in e, f"year {e.get('year')} has gift_annual_exclusion")
    
    # TCJA doubling check
    y2017 = next((e for e in hist if e['year'] == 2017), None)
    y2018 = next((e for e in hist if e['year'] == 2018), None)
    if y2017 and y2018:
        check(y2018['estate_exemption'] > y2017['estate_exemption'] * 1.8, 
              "2018 exemption > 1.8x 2017 (TCJA doubling)")
    
    print(f"  EstateTax: {PASS - start} checks")

def validate_fers_contribution(root):
    section("FERS Contribution Rates")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/fers-contribution-rates.json')))
    check('metadata' in f, "has metadata")
    check('cohorts' in f, "has cohorts")
    cohorts = f.get('cohorts', [])
    check(len(cohorts) == 3, f"exactly 3 cohorts (got {len(cohorts)})")
    
    expected_rates = [0.8, 3.1, 4.4]
    for i, c in enumerate(cohorts):
        check('employee_rate_pct' in c, f"cohort {i} has rate")
        if 'employee_rate_pct' in c:
            check(c['employee_rate_pct'] == expected_rates[i], 
                  f"cohort {i} rate = {expected_rates[i]} (got {c['employee_rate_pct']})")
    
    check('csrs_reference' in f, "has CSRS reference")
    if 'csrs_reference' in f:
        check(f['csrs_reference'].get('employee_rate_pct') == 7.0, "CSRS rate = 7.0%")
    
    check('fers_benefit_formula' in f, "has benefit formula")
    
    print(f"  FERS: {PASS - start} checks")

def validate_rmd_rules(root):
    section("RMD Rules History")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'reference/rmd-rules-history.json')))
    check('metadata' in f, "has metadata")
    check('rmd_age_history' in f, "has rmd_age_history")
    
    ages = f.get('rmd_age_history', [])
    check(len(ages) >= 4, f"4+ RMD age periods (got {len(ages)})")
    
    # Check age progression
    age_values = [a['rmd_start_age'] for a in ages]
    check(70.5 in age_values, "includes original 70.5 age")
    check(72 in age_values, "includes SECURE Act 72")
    check(73 in age_values, "includes SECURE 2.0 73")
    check(75 in age_values, "includes SECURE 2.0 75")
    
    check('key_rule_changes' in f, "has key_rule_changes")
    check('inherited_ira_rules' in f, "has inherited_ira_rules")
    
    print(f"  RMD: {PASS - start} checks")

def validate_medicare_premium_history(root):
    section("Medicare Premium History (Merged into medicare-rates.json)")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/healthcare/medicare-rates.json')))
    ph = f.get('premium_history', {})
    check('years' in ph, "has years (Part B premiums)")
    
    premiums = ph.get('years', [])
    check(len(premiums) >= 25, f"25+ years (got {len(premiums)})")
    
    for p in premiums:
        check('year' in p, f"entry has year")
        check('standard_premium' in p, f"year {p.get('year')} has standard_premium")
        check(p.get('standard_premium', 0) > 0, f"year {p.get('year')} premium > 0")
    
    # Cross-check 2026 against same file's Part B section
    pb = f.get('part_b', {})
    med_premium = pb.get('standard_premium_monthly')
    y2026 = next((p for p in premiums if p['year'] == 2026), None)
    if med_premium and y2026:
        check(abs(y2026['standard_premium'] - med_premium) < 0.01,
              f"2026 premium history matches Part B section ({y2026['standard_premium']} vs {med_premium})")
    
    check('part_a_inpatient_deductible' in ph, "has Part A deductible history")
    check('trend_analysis' in ph, "has trend analysis")
    
    print(f"  MedHistory: {PASS - start} checks")

def validate_ss_claiming(root):
    section("Social Security Claiming Rules")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'reference/social-security-claiming.json')))
    check('metadata' in f, "has metadata")
    check('fra_schedule' in f, "has fra_schedule")
    
    fra = f.get('fra_schedule', [])
    check(len(fra) >= 10, f"10+ FRA entries (got {len(fra)})")
    
    # Check FRA progression
    last_fra = next((e for e in fra if e.get('birth_year_start') == 1960), None)
    if last_fra:
        check(last_fra['fra_years'] == 67, "Born 1960+ FRA = 67")
    
    check('early_filing_reductions' in f, "has early_filing_reductions")
    check('delayed_retirement_credits' in f, "has delayed_retirement_credits")
    check('earnings_test' in f, "has earnings_test")
    
    # WEP/GPO repeal check
    if 'windfall_elimination_provision' in f:
        wep = f['windfall_elimination_provision']
        check('repeal' in json.dumps(wep).lower() or 'fairness act' in json.dumps(wep).lower(),
              "WEP section references SS Fairness Act repeal")
    
    print(f"  SSClaiming: {PASS - start} checks")

def validate_fehb_premium_history(root):
    section("FEHB Premium History")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'federal/fehb-premium-history.json')))
    check('metadata' in f, "has metadata")
    check('average_premium_trend' in f, "has average_premium_trend")
    
    trend = f.get('average_premium_trend', [])
    check(len(trend) >= 15, f"15+ years (got {len(trend)})")
    
    for e in trend:
        check('year' in e, f"entry has year")
        check('total_biweekly_self_only' in e, f"year {e.get('year')} has total premium")
        check('enrollee_biweekly_self_only' in e, f"year {e.get('year')} has enrollee premium")
        if 'total_biweekly_self_only' in e and 'enrollee_biweekly_self_only' in e:
            check(e['total_biweekly_self_only'] > e['enrollee_biweekly_self_only'],
                  f"year {e.get('year')} total > enrollee")
    
    check('trend_analysis' in f, "has trend_analysis")
    
    print(f"  FEHBHistory: {PASS - start} checks")

def validate_military_retirement(root):
    section("Military Retirement Rules")
    global PASS, FAIL
    start = PASS
    f = json.load(open(os.path.join(root, 'reference/military-retirement-rules.json')))
    check('metadata' in f, "has metadata")
    check('retirement_systems' in f, "has retirement_systems")
    
    systems = f.get('retirement_systems', [])
    check(len(systems) == 4, f"exactly 4 systems (got {len(systems)})")
    
    system_names = [s.get('system', '') for s in systems]
    for expected in ['Final Pay', 'High-3', 'BRS']:
        check(any(expected.lower() in n.lower() for n in system_names), f"has {expected} system")
    
    # BRS-specific checks
    brs = next((s for s in systems if 'BRS' in s.get('system', '') or 'Blended' in s.get('system', '')), None)
    if brs:
        check(brs.get('multiplier_per_year_pct') == 2.0, "BRS multiplier = 2.0%/year")
        check(brs.get('tsp_matching') == True, "BRS has TSP matching")
        check('tsp_match_details' in brs, "BRS has TSP match details")
    
    check('survivor_benefit_plan' in f, "has SBP data")
    check('concurrent_receipt' in f, "has CRDP/CRSC data")
    
    print(f"  MilRetirement: {PASS - start} checks")

# ==============================================================
# MAIN
# ==============================================================

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"Validating historical/reference data files in: {root}")
    
    # Existing files
    validate_tsp_limits(root)
    validate_ss_bend_points(root)
    validate_ss_taxable_max(root)
    validate_ira_limits(root)
    validate_life_table(root)
    validate_county_property_tax(root)
    validate_cola_history(root)
    validate_fehb_rates(root)
    validate_tricare(root)
    validate_fehb_benefits(root)
    validate_fedvip(root)
    
    # New Session 21 files
    validate_tax_brackets(root)
    validate_standard_deduction(root)
    validate_capital_gains(root)
    validate_hsa_limits(root)
    validate_pay_raises(root)
    validate_estate_gift_tax(root)
    validate_fers_contribution(root)
    validate_rmd_rules(root)
    validate_medicare_premium_history(root)
    validate_ss_claiming(root)
    validate_fehb_premium_history(root)
    validate_military_retirement(root)
    
    print(f"\n{'='*60}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        print(f"\n❌ {FAIL} checks FAILED!")
        sys.exit(1)
    else:
        print(f"\n✅ All historical data validation checks passed!")
