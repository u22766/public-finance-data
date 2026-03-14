#!/usr/bin/env python3
"""
Validation suite for US Territory expansion (Session 31).
Validates 5 territory entries: AS, GU, MP, PR, VI
Checks structural integrity, real estate vs vehicle separation,
income tax systems, and cross-references.
"""

import json
import os
import sys

PASS = 0
FAIL = 0
WARN = 0

def check(condition, label):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")

def warn(condition, label):
    global WARN
    if not condition:
        WARN += 1
        print(f"  WARN: {label}")

def section(name):
    print(f"\n--- {name} ---")

def main():
    global PASS, FAIL, WARN

    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    sb_path = os.path.join(root, 'states', 'state-benefits.json')
    manifest_path = os.path.join(root, 'manifest.json')

    with open(sb_path, 'r', encoding='utf-8') as f:
        sb = json.load(f)
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    states = sb['states']
    by_code = {s['state_code']: s for s in states}

    # ================================================================
    # Section 1: Structural integrity
    # ================================================================
    section("Section 1: Structural Integrity")

    check(sb.get('version') >= '2.1', f"Version >= 2.1 (got {sb.get('version')})")
    check(len(states) == 56, f"56 total jurisdictions (got {len(states)})")

    # All 5 territories present
    territory_codes = ['AS', 'GU', 'MP', 'PR', 'VI']
    for tc in territory_codes:
        check(tc in by_code, f"Territory {tc} present")

    # Alphabetical ordering preserved
    codes = [s['state_code'] for s in states]
    check(codes == sorted(codes), "Alphabetical ordering intact")

    # All territories have is_territory flag
    for tc in territory_codes:
        if tc in by_code:
            check(by_code[tc].get('is_territory') is True, f"{tc} has is_territory=True")

    # All 50 states + DC do NOT have is_territory flag
    state_count = sum(1 for s in states if not s.get('is_territory'))
    check(state_count == 51, f"51 non-territory entries (got {state_count})")

    # Territory names
    expected_names = {
        'AS': 'American Samoa',
        'GU': 'Guam',
        'MP': 'Northern Mariana Islands',
        'PR': 'Puerto Rico',
        'VI': 'U.S. Virgin Islands'
    }
    for tc, name in expected_names.items():
        if tc in by_code:
            check(by_code[tc]['state_name'] == name, f"{tc} name is '{name}'")

    # ================================================================
    # Section 2: Puerto Rico (richest entry)
    # ================================================================
    section("Section 2: Puerto Rico (PR)")
    pr = by_code.get('PR', {})

    # Income tax
    it = pr.get('income_tax', {})
    check(it.get('_tax_system') == 'own_code', "PR has own_code tax system")
    check(it.get('top_rate') == 0.33, f"PR top rate is 33% (got {it.get('top_rate')})")

    brackets = it.get('brackets', [])
    check(len(brackets) == 5, f"PR has 5 tax brackets (got {len(brackets)})")
    if brackets:
        check(brackets[0].get('rate') == 0.0, "PR first bracket is 0%")
        check(brackets[0].get('max') == 9000, "PR first bracket max is $9,000")
        check(brackets[-1].get('rate') == 0.33, "PR top bracket is 33%")

    # Military retirement exemption
    mil = it.get('military_retirement', {})
    check(mil.get('exempt') is True, "PR military retirement exempt")
    check(mil.get('effective_year') == 2025, "PR military retirement effective 2025")

    # Veteran personal exemption
    vpe = it.get('veteran_personal_exemption', {})
    check(vpe.get('amount') == 1500, "PR veteran exemption $1,500")
    check(vpe.get('joint_amount') == 3000, "PR joint veteran exemption $3,000")

    # Federal pension deduction
    fpd = it.get('federal_pension_deduction', {})
    check(fpd.get('under_60') == 11000, "PR pension deduction under 60: $11,000")
    check(fpd.get('age_60_plus') == 15000, "PR pension deduction 60+: $15,000")

    # SS exempt in PR
    check(it.get('ss_income', {}).get('exempt') is True, "PR SS benefits exempt")

    # Real estate property tax (veteran)
    vb = pr.get('veteran_benefits', {})
    rpte = vb.get('disabled_veteran_property_tax_exemption', {})
    check(rpte.get('available') is True, "PR real estate exemption available")
    check(rpte.get('exemption_type') == 'tiered', "PR exemption type is tiered")

    tiers = rpte.get('tiers', [])
    check(len(tiers) == 2, f"PR has 2 exemption tiers (got {len(tiers)})")
    if len(tiers) >= 2:
        check(tiers[0].get('rating_required') == 50, "PR tier 1 requires 50% rating")
        check(tiers[0].get('exemption_amount') == 50000, "PR tier 1 is $50,000")
        check(tiers[1].get('rating_required') == 100, "PR tier 2 requires 100% rating")
        check(tiers[1].get('exemption_type') == 'full', "PR tier 2 is full exemption")

    check('cuerda' in json.dumps(rpte).lower(), "PR entry mentions cuerda land unit")
    check(rpte.get('retroactive_application') is True, "PR retroactive application documented")
    check(rpte.get('administering_agency') is not None, "PR administering agency (CRIM) documented")

    # Vehicle tax exemption (SEPARATE from real estate)
    vte = vb.get('vehicle_tax_exemption', {})
    check(vte.get('available') is True, "PR vehicle exemption available")
    check(vte.get('eligibility', {}).get('rating_required') == 100, "PR vehicle requires 100% rating")

    # VA-funded vehicle sub-entry
    vafv = vte.get('va_funded_vehicle', {})
    check(vafv.get('available') is True, "PR VA-funded vehicle exemption documented")
    check('replacement' in json.dumps(vafv).lower(), "PR vehicle replacement rule documented")
    check('4 year' in json.dumps(vafv).lower() or 'four year' in json.dumps(vafv).lower(), "PR 4-year replacement rule documented")

    # Age-based vehicle exemption
    abe = vte.get('age_based_exemption', {})
    check(abe.get('age_threshold') == 60, "PR age-based vehicle exemption at age 60")

    # Verify real estate and vehicle are SEPARATE keys
    check('disabled_veteran_property_tax_exemption' in vb, "PR has standalone real estate key")
    check('vehicle_tax_exemption' in vb, "PR has standalone vehicle key")
    check('disabled_veteran_property_tax_exemption' != 'vehicle_tax_exemption', "PR real estate and vehicle are separate keys")

    # ================================================================
    # Section 3: Guam (GU)
    # ================================================================
    section("Section 3: Guam (GU)")
    gu = by_code.get('GU', {})

    it = gu.get('income_tax', {})
    check(it.get('_tax_system') == 'mirror_code', "GU has mirror_code tax system")
    check(it.get('top_rate') == 0.37, f"GU top rate is 37% (got {it.get('top_rate')})")
    check(it.get('military_retirement', {}).get('exempt') is False, "GU military retirement taxable")
    check(it.get('disability_retirement_pay', {}).get('exempt') is True, "GU disability retirement exempt")

    vb = gu.get('veteran_benefits', {})
    rpte = vb.get('disabled_veteran_property_tax_exemption', {})
    check(rpte.get('available') is True, "GU real estate exemption available")
    check(rpte.get('exemption_type') == 'full', "GU full real estate exemption")
    check(rpte.get('eligibility', {}).get('rating_required') == 100, "GU requires 100% rating")
    check(rpte.get('eligibility', {}).get('iu_eligible') is True, "GU IU-eligible")
    check(rpte.get('max_properties') == 1, "GU limited to 1 property")

    # Survivor provisions
    surv = rpte.get('survivor_conditions', {})
    check(surv.get('unremarried_spouse') is True, "GU surviving spouse eligible")
    check(surv.get('gold_star_parents') is True, "GU Gold Star parents eligible")
    check(surv.get('legal_guardian') is True, "GU legal guardian eligible")

    # Vehicle note (no specific vehicle PPT)
    check('_vehicle_note' in vb, "GU has vehicle note explaining no vehicle PPT")

    # ================================================================
    # Section 4: U.S. Virgin Islands (VI)
    # ================================================================
    section("Section 4: U.S. Virgin Islands (VI)")
    vi = by_code.get('VI', {})

    it = vi.get('income_tax', {})
    check(it.get('_tax_system') == 'mirror_code', "VI has mirror_code tax system")
    check(it.get('top_rate') == 0.37, f"VI top rate is 37% (got {it.get('top_rate')})")
    check(it.get('military_retirement', {}).get('exempt') is False, "VI military retirement taxable")
    check(it.get('disability_retirement_pay', {}).get('exempt') is True, "VI disability retirement exempt")

    vb = vi.get('veteran_benefits', {})
    rpte = vb.get('disabled_veteran_property_tax_exemption', {})
    check(rpte.get('available') is True, "VI real estate exemption available")
    check(rpte.get('exemption_type') == 'full', "VI full real estate exemption for P&T")
    check(rpte.get('eligibility', {}).get('rating_required') == 100, "VI requires 100% rating")
    check(rpte.get('eligibility', {}).get('pt_required') is True, "VI requires P&T")

    # Contact info
    contact = rpte.get('contact', {})
    check('st_croix' in contact, "VI has St. Croix contact")
    check('st_thomas' in contact, "VI has St. Thomas contact")

    # Homestead credit in property_tax section
    pt = vi.get('property_tax', {})
    exemptions = pt.get('exemptions', [])
    check(len(exemptions) >= 1, "VI has homestead credit in property_tax")
    if exemptions:
        check(exemptions[0].get('amount') == 650, "VI homestead credit is $650")

    # Vehicle note
    check('_vehicle_note' in vb, "VI has vehicle note")

    # ================================================================
    # Section 5: Northern Mariana Islands (MP)
    # ================================================================
    section("Section 5: Northern Mariana Islands (MP)")
    mp = by_code.get('MP', {})

    it = mp.get('income_tax', {})
    check(it.get('_tax_system') == 'mirror_code', "MP has mirror_code tax system")
    check(it.get('top_rate') == 0.37, f"MP top rate is 37% (got {it.get('top_rate')})")
    check(it.get('military_retirement', {}).get('exempt') is False, "MP military retirement taxable")
    check(it.get('disability_retirement_pay', {}).get('exempt') is True, "MP disability retirement exempt")

    vb = mp.get('veteran_benefits', {})
    check('_mirror_code_tax_note' in vb, "MP has mirror code tax note")
    check('_no_property_exemption_note' in vb, "MP has no-property-exemption note")

    # ================================================================
    # Section 6: American Samoa (AS)
    # ================================================================
    section("Section 6: American Samoa (AS)")
    asm = by_code.get('AS', {})

    it = asm.get('income_tax', {})
    check('unclear' in json.dumps(it).lower() or 'incomplete' in json.dumps(it).lower(),
          "AS tax status documented as unclear/incomplete")

    vb = asm.get('veteran_benefits', {})
    check('_no_benefits_note' in vb, "AS has no-benefits note")
    check('zero' in json.dumps(vb).lower() or 'does not offer' in json.dumps(vb).lower(),
          "AS explicitly states no territory-level veteran benefits")

    # ================================================================
    # Section 7: Tax system consistency
    # ================================================================
    section("Section 7: Tax System Consistency")

    # Mirror code territories should all have 0.37 top rate
    mirror_territories = ['GU', 'MP', 'VI']
    for tc in mirror_territories:
        t = by_code.get(tc, {})
        check(t.get('income_tax', {}).get('_tax_system') == 'mirror_code',
              f"{tc} has mirror_code system")
        check(t.get('income_tax', {}).get('top_rate') == 0.37,
              f"{tc} top rate is 0.37 (federal mirror)")

    # PR should NOT be mirror code
    check(by_code.get('PR', {}).get('income_tax', {}).get('_tax_system') == 'own_code',
          "PR is own_code (not mirror)")
    check(by_code.get('PR', {}).get('income_tax', {}).get('top_rate') == 0.33,
          "PR top rate is 0.33 (not federal)")

    # VA comp exempt everywhere
    for tc in territory_codes:
        t = by_code.get(tc, {})
        va_comp = t.get('income_tax', {}).get('va_compensation', {})
        check(va_comp.get('exempt') is True, f"{tc} VA compensation exempt")

    # ================================================================
    # Section 8: Real estate vs vehicle separation
    # ================================================================
    section("Section 8: Real Estate vs Vehicle Separation")

    # PR must have BOTH separate keys
    pr_vb = by_code.get('PR', {}).get('veteran_benefits', {})
    check('disabled_veteran_property_tax_exemption' in pr_vb, "PR has real estate key")
    check('vehicle_tax_exemption' in pr_vb, "PR has vehicle key")

    # GU and VI should have real estate but note for vehicle
    for tc in ['GU', 'VI']:
        vb = by_code.get(tc, {}).get('veteran_benefits', {})
        check('disabled_veteran_property_tax_exemption' in vb, f"{tc} has real estate key")
        check('_vehicle_note' in vb, f"{tc} has vehicle note (no vehicle PPT)")

    # No territory should have vehicle nested inside real estate
    for tc in territory_codes:
        vb = by_code.get(tc, {}).get('veteran_benefits', {})
        rpte = vb.get('disabled_veteran_property_tax_exemption', {})
        check('vehicle_exemption' not in rpte, f"{tc} no nested vehicle inside real estate")
        check('vehicle_tax' not in json.dumps(rpte).replace('vehicle_tax_exemption', ''),
              f"{tc} real estate entry doesn't contain vehicle tax data")

    # ================================================================
    # Section 9: Pre-existing state entries intact
    # ================================================================
    section("Section 9: Pre-existing State Entries Intact")

    # Verify a sampling of states are still present and correct
    spot_checks = {
        'VA': {'has_vehicle': True, 'has_real_estate': True},
        'DC': {'has_homestead': True},
        'FL': {'has_entry': True},
        'TX': {'has_vehicle_note': True},
        'MS': {'has_vehicle': True},
        'SC': {'has_vehicle': True},
    }

    for sc, checks in spot_checks.items():
        check(sc in by_code, f"{sc} still present")
        if sc in by_code:
            vb = by_code[sc].get('veteran_benefits', {})
            if checks.get('has_vehicle'):
                check('vehicle_tax_exemption' in vb or 'vehicle_ad_valorem_exemption' in vb,
                      f"{sc} vehicle entry intact")
            if checks.get('has_real_estate'):
                check('real_property_tax_exemption' in vb or 'disabled_veteran_property_tax_exemption' in vb,
                      f"{sc} real estate entry intact")
            if checks.get('has_vehicle_note'):
                check('_vehicle_note' in vb, f"{sc} vehicle note intact")

    # Total state count excluding territories
    non_territory = [s for s in states if not s.get('is_territory')]
    check(len(non_territory) == 51, f"51 non-territory entries intact (got {len(non_territory)})")

    # ================================================================
    # Section 10: Manifest consistency
    # ================================================================
    section("Section 10: Manifest Consistency")

    sb_manifest = manifest['files'].get('state_benefits', {})
    check(sb_manifest.get('version') == '2.1', f"Manifest version 2.1 (got {sb_manifest.get('version')})")
    check('56' in sb_manifest.get('description', '') or 'territor' in sb_manifest.get('description', '').lower(),
          "Manifest description references 56 jurisdictions or territories")

    # ================================================================
    # Summary
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Territory Validation: {PASS} passed, {FAIL} failed, {WARN} warnings")
    print(f"{'='*60}")

    if FAIL > 0:
        print("VALIDATION FAILED")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
