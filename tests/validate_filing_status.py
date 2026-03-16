#!/usr/bin/env python3
"""Validation suite for filing-status-thresholds.json
   Tests structural integrity, cross-year consistency, bracket math,
   and known IRS reference values.
"""
import json
import sys
import os

def main():
    # Find the file
    paths = [
        'federal/filing-status-thresholds.json',
        'public-finance-data/federal/filing-status-thresholds.json',
    ]
    filepath = None
    for p in paths:
        if os.path.exists(p):
            filepath = p
            break
    if not filepath:
        print("ERROR: filing-status-thresholds.json not found")
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    checks = 0
    errors = []

    def check(condition, msg):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(msg)

    STATUSES = ['single', 'married_filing_jointly', 'married_filing_separately',
                'head_of_household', 'qualifying_surviving_spouse']
    DOMAINS = ['tax', 'social_security_taxation', 'irmaa', 'roth_ira',
               'traditional_ira_deductibility', 'salt_deduction_cap']
    TCJA_RATES = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]
    PRE_TCJA_RATES = [0.10, 0.15, 0.25, 0.28, 0.33, 0.35, 0.396]

    # =====================================================
    # 1. METADATA & TOP-LEVEL STRUCTURE
    # =====================================================
    check('metadata' in data, "Missing metadata")
    check('year' in data, "Missing year key")
    check('filing_statuses' in data, "Missing filing_statuses")
    check('transition_rules' in data, "Missing transition_rules")
    check('historical_years' in data, "Missing historical_years")

    # Consumer-agnostic check
    text = json.dumps(data)
    check('engine_usage' not in data, "engine_usage block should not be in published file")
    check(text.lower().count('meridian') == 0, "No Meridian references allowed")
    # Allow "Engine" only inside _note fields for historical context
    engine_in_notes_only = True
    for key in ['filing_statuses', 'transition_rules']:
        section = json.dumps(data.get(key, {}))
        if 'Engine ' in section:
            engine_in_notes_only = False
    check(engine_in_notes_only, "Engine references should not appear in data sections")

    # =====================================================
    # 2. CURRENT YEAR (2026) VALIDATION
    # =====================================================
    check(data['year'] == 2026, "Current year should be 2026")
    fs = data['filing_statuses']
    check(set(fs.keys()) == set(STATUSES), f"Expected 5 statuses, got {set(fs.keys())}")

    for status in STATUSES:
        if status not in fs:
            continue
        s = fs[status]
        for domain in DOMAINS:
            check(domain in s, f"2026 {status}: missing {domain}")

        # Bracket checks
        bkts = s.get('tax', {}).get('brackets', [])
        check(len(bkts) == 7, f"2026 {status}: expected 7 brackets, got {len(bkts)}")
        if len(bkts) == 7:
            rates = [b['rate'] for b in bkts]
            check(rates == TCJA_RATES, f"2026 {status}: wrong rate structure")
            # Continuity
            for i in range(1, len(bkts)):
                if bkts[i-1]['max'] is not None:
                    check(bkts[i]['min'] == bkts[i-1]['max'] + 1,
                          f"2026 {status}: bracket gap at {i}")
            # Last bracket max is null
            check(bkts[-1]['max'] is None, f"2026 {status}: last bracket max should be null")

    # MFS brackets = half MFJ
    mfj_b = fs['married_filing_jointly']['tax']['brackets']
    mfs_b = fs['married_filing_separately']['tax']['brackets']
    for i in range(len(mfj_b) - 1):  # exclude last (null max)
        if mfj_b[i]['max'] is not None and mfs_b[i]['max'] is not None:
            check(mfs_b[i]['max'] == mfj_b[i]['max'] // 2,
                  f"2026: MFS bracket {i} max should be half MFJ")

    # QSS brackets = MFJ
    qss_b = fs['qualifying_surviving_spouse']['tax']['brackets']
    for i in range(len(mfj_b)):
        check(qss_b[i]['min'] == mfj_b[i]['min'] and qss_b[i]['max'] == mfj_b[i]['max'],
              f"2026: QSS bracket {i} should match MFJ")

    # SS taxation constant checks
    check(fs['single']['social_security_taxation']['provisional_income_50pct_threshold'] == 25000,
          "2026: single SS 50% threshold")
    check(fs['single']['social_security_taxation']['provisional_income_85pct_threshold'] == 34000,
          "2026: single SS 85% threshold")
    check(fs['married_filing_jointly']['social_security_taxation']['provisional_income_50pct_threshold'] == 32000,
          "2026: MFJ SS 50% threshold")
    check(fs['married_filing_separately']['social_security_taxation']['provisional_income_50pct_threshold'] == 0,
          "2026: MFS SS 50% threshold")

    # IRMAA tier checks
    single_irmaa = fs['single']['irmaa']['tiers']
    check(len(single_irmaa) == 6, "2026: single should have 6 IRMAA tiers")
    check(single_irmaa[0]['part_b'] == 202.90, "2026: standard Part B premium $202.90")
    mfs_irmaa = fs['married_filing_separately']['irmaa']['tiers']
    check(len(mfs_irmaa) == 3, "2026: MFS should have 3 IRMAA tiers")

    # =====================================================
    # 3. HISTORICAL YEARS VALIDATION
    # =====================================================
    hist = data['historical_years']
    check(len(hist) == 10, f"Expected 10 historical years, got {len(hist)}")
    hist_years = [h['year'] for h in hist]
    check(hist_years == list(range(2016, 2026)), "Historical years should be 2016-2025")

    for h in hist:
        y = h['year']
        hfs = h['filing_statuses']

        check(set(hfs.keys()) == set(STATUSES), f"{y}: missing statuses")

        expected_rates = PRE_TCJA_RATES if y <= 2017 else TCJA_RATES

        for status in STATUSES:
            if status not in hfs:
                continue
            s = hfs[status]

            # Bracket structure
            bkts = s.get('tax', {}).get('brackets', [])
            check(len(bkts) == 7, f"{y} {status}: expected 7 brackets")
            if len(bkts) == 7:
                rates = [b['rate'] for b in bkts]
                check(rates == expected_rates, f"{y} {status}: wrong rates")
                for i in range(1, len(bkts)):
                    if bkts[i-1]['max'] is not None:
                        check(bkts[i]['min'] == bkts[i-1]['max'] + 1,
                              f"{y} {status}: bracket gap at {i}")

            # SS taxation constant
            ss = s.get('social_security_taxation', {})
            if status in ['single', 'head_of_household']:
                check(ss.get('provisional_income_50pct_threshold') == 25000, f"{y} {status}: SS 50%")
                check(ss.get('provisional_income_85pct_threshold') == 34000, f"{y} {status}: SS 85%")
            elif status in ['married_filing_jointly', 'qualifying_surviving_spouse']:
                check(ss.get('provisional_income_50pct_threshold') == 32000, f"{y} {status}: SS 50%")
                check(ss.get('provisional_income_85pct_threshold') == 44000, f"{y} {status}: SS 85%")
            elif status == 'married_filing_separately':
                check(ss.get('provisional_income_50pct_threshold') == 0, f"{y} {status}: SS 50%")
                check(ss.get('provisional_income_85pct_threshold') == 0, f"{y} {status}: SS 85%")

            # MFS Roth always $0-$10k
            if status == 'married_filing_separately':
                roth = s.get('roth_ira', {})
                check(roth.get('full_contribution_below_magi') == 0, f"{y} MFS: Roth start")
                check(roth.get('ineligible_at_magi') == 10000, f"{y} MFS: Roth end")

            # MFS trad IRA always $0-$10k
            if status == 'married_filing_separately':
                trad = s.get('traditional_ira_deductibility', {})
                check(trad.get('active_participant_full_below') == 0, f"{y} MFS: trad start")
                check(trad.get('active_participant_ineligible_at') == 10000, f"{y} MFS: trad end")

            # Standard deduction > 0
            sd = s.get('tax', {}).get('standard_deduction', 0)
            check(sd > 0, f"{y} {status}: SD should be > 0")

        # QSS brackets = MFJ
        qss_bkts = hfs['qualifying_surviving_spouse']['tax']['brackets']
        mfj_bkts = hfs['married_filing_jointly']['tax']['brackets']
        for i in range(len(mfj_bkts)):
            check(qss_bkts[i]['min'] == mfj_bkts[i]['min'] and qss_bkts[i]['max'] == mfj_bkts[i]['max'],
                  f"{y}: QSS bracket {i} != MFJ")

        # SALT checks
        if y < 2018:
            check(hfs['single']['salt_deduction_cap'].get('cap') is None,
                  f"{y}: pre-TCJA SALT should be null (unlimited)")
        elif y <= 2024:
            check(hfs['single']['salt_deduction_cap'].get('cap') == 10000,
                  f"{y}: TCJA SALT cap should be $10,000")
            check(hfs['married_filing_separately']['salt_deduction_cap'].get('cap') == 5000,
                  f"{y}: MFS SALT cap should be $5,000")

    # =====================================================
    # 4. YEAR-OVER-YEAR MONOTONICITY
    # =====================================================
    # Standard deductions should generally increase (or stay flat) year over year
    for i in range(1, len(hist)):
        prev = hist[i-1]
        curr = hist[i]
        py, cy = prev['year'], curr['year']
        sd_prev = prev['filing_statuses']['single']['tax']['standard_deduction']
        sd_curr = curr['filing_statuses']['single']['tax']['standard_deduction']
        check(sd_curr >= sd_prev, f"SD single should be non-decreasing {py}→{cy}")

    # IRA contribution limits should be non-decreasing
    for i in range(1, len(hist)):
        prev = hist[i-1]
        curr = hist[i]
        py, cy = prev['year'], curr['year']
        lim_prev = prev['filing_statuses']['single']['roth_ira']['contribution_limit']
        lim_curr = curr['filing_statuses']['single']['roth_ira']['contribution_limit']
        check(lim_curr >= lim_prev, f"IRA limit should be non-decreasing {py}→{cy}")

    # =====================================================
    # 5. KNOWN REFERENCE VALUE SPOT CHECKS
    # =====================================================
    # 2018 TCJA standard deduction jump
    h18 = [h for h in hist if h['year'] == 2018][0]
    check(h18['filing_statuses']['single']['tax']['standard_deduction'] == 12000,
          "2018: TCJA single SD should be $12,000")
    check(h18['filing_statuses']['married_filing_jointly']['tax']['standard_deduction'] == 24000,
          "2018: TCJA MFJ SD should be $24,000")
    check(h18['filing_statuses']['head_of_household']['tax']['standard_deduction'] == 18000,
          "2018: TCJA HoH SD should be $18,000")

    # 2019: 5th IRMAA tier added (>$500k)
    h19 = [h for h in hist if h['year'] == 2019][0]
    single_tiers_19 = h19['filing_statuses']['single']['irmaa']['tiers']
    check(len(single_tiers_19) == 6, "2019: should have 6 IRMAA tiers (5th bracket added)")

    # Pre-2019: only 5 tiers
    h17 = [h for h in hist if h['year'] == 2017][0]
    single_tiers_17 = h17['filing_statuses']['single']['irmaa']['tiers']
    check(len(single_tiers_17) == 5, "2017: should have 5 IRMAA tiers")

    # =====================================================
    # RESULTS
    # =====================================================
    print(f"\n{'='*50}")
    if errors:
        print(f"FAILED: {len(errors)} errors in {checks} checks")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"✓ {checks}/{checks} checks passed")
        sys.exit(0)

if __name__ == '__main__':
    main()
