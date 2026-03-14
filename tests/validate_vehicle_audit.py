#!/usr/bin/env python3
"""
Vehicle/Personal Property Tax Audit Validation (Session 30)
Validates that states with vehicle personal property taxes have appropriate
separate benefit entries distinct from real estate/homestead exemptions.

Sections:
  1. Structural checks — version, new entries exist
  2. Mississippi vehicle_ad_valorem_exemption — deep validation
  3. South Carolina vehicle_tax_exemption — extracted entry validation
  4. Connecticut vehicle_tax_exemption — P&T dwelling-alternative validation
  5. Alabama vehicle_tax_exemption — VA-funded vehicle validation
  6. Cross-reference notes — AR and NC _vehicle_note checks
  7. Pre-existing entries — GA, HI, OK, VA, TX still intact
  8. Manifest — version and description updated
"""

import json
import os
import sys

PASS = 0
FAIL = 0
WARN = 0

def check(condition, label, warn_only=False):
    global PASS, FAIL, WARN
    if condition:
        PASS += 1
    elif warn_only:
        WARN += 1
        print(f"  WARN: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label}")

def find_state(states, code):
    for s in states:
        if s.get('state_code') == code:
            return s
    return None

def main():
    global PASS, FAIL, WARN

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sb_path = os.path.join(base, 'states', 'state-benefits.json')
    manifest_path = os.path.join(base, 'manifest.json')

    with open(sb_path) as f:
        data = json.load(f)
    with open(manifest_path) as f:
        manifest = json.load(f)

    states = data['states']

    # ================================================================
    # SECTION 1: Structural checks
    # ================================================================
    print("Section 1: Structural checks")

    # Version
    ver = data.get('version', '0')
    ver_parts = ver.split('.')
    ver_num = float(f"{ver_parts[0]}.{ver_parts[1]}") if len(ver_parts) >= 2 else float(ver_parts[0])
    check(ver_num >= 2.0, f"Version >= 2.0 (got {ver})")

    # State count unchanged
    check(len(states) >= 51, f"State count >= 51 (got {len(states)})")

    # New entries exist
    ms = find_state(states, 'MS')
    sc = find_state(states, 'SC')
    ct = find_state(states, 'CT')
    al = find_state(states, 'AL')
    ar = find_state(states, 'AR')
    nc = find_state(states, 'NC')

    check(ms is not None, "Mississippi found")
    check(sc is not None, "South Carolina found")
    check(ct is not None, "Connecticut found")
    check(al is not None, "Alabama found")
    check(ar is not None, "Arkansas found")
    check(nc is not None, "North Carolina found")

    # New vehicle keys exist
    check('vehicle_ad_valorem_exemption' in ms.get('veteran_benefits', {}),
          "MS has vehicle_ad_valorem_exemption")
    check('vehicle_tax_exemption' in sc.get('veteran_benefits', {}),
          "SC has vehicle_tax_exemption")
    check('vehicle_tax_exemption' in ct.get('veteran_benefits', {}),
          "CT has vehicle_tax_exemption")
    check('vehicle_tax_exemption' in al.get('veteran_benefits', {}),
          "AL has vehicle_tax_exemption")
    check('_vehicle_note' in ar.get('veteran_benefits', {}),
          "AR has _vehicle_note")
    check('_vehicle_note' in nc.get('veteran_benefits', {}),
          "NC has _vehicle_note")

    # ================================================================
    # SECTION 2: Mississippi vehicle_ad_valorem_exemption
    # ================================================================
    print("Section 2: Mississippi vehicle_ad_valorem_exemption")

    ms_v = ms['veteran_benefits'].get('vehicle_ad_valorem_exemption', {})
    check(ms_v.get('available') is True, "MS vehicle available == True")
    check(ms_v.get('exemption_type') == 'full', "MS vehicle exemption_type == full")
    check(ms_v.get('max_vehicles') == 2, "MS max_vehicles == 2")

    # Eligibility
    ms_elig = ms_v.get('eligibility', {})
    check(ms_elig.get('rating_required') == 70, "MS rating_required == 70 (70%+ non-permanent)")
    check('100%' in str(ms_elig.get('rating_note', '')), "MS rating_note mentions 100% permanent")
    check('70' in str(ms_elig.get('rating_note', '')), "MS rating_note mentions 70%+ non-permanent")
    check(ms_elig.get('honorable_discharge_required') is True, "MS honorable discharge required")
    check(ms_elig.get('residency_required') is True, "MS residency required")
    check('non_permanent_renewal' in ms_elig, "MS has non_permanent_renewal field")

    # Vehicle types
    ms_types = ms_v.get('vehicle_types', [])
    check('private_passenger_vehicle' in ms_types, "MS vehicle_types includes passenger vehicle")
    check('pickup_truck' in ms_types, "MS vehicle_types includes pickup truck")
    check('motorcycle' in ms_types, "MS vehicle_types includes motorcycle")

    # License plate
    ms_plate = ms_v.get('license_plate', {})
    check(ms_plate.get('cost') == 1.00, "MS license plate cost == $1.00")
    check(ms_plate.get('non_transferable') is True, "MS plate non_transferable")

    # Survivor
    check(ms_v.get('survivor_transfer') is True, "MS survivor_transfer == True")
    ms_surv = ms_v.get('survivor_conditions', {})
    check(ms_surv.get('unremarried_spouse') is True, "MS unremarried spouse eligible")
    check(ms_surv.get('spouse_can_apply_posthumously') is True, "MS spouse can apply posthumously")

    # Authority and sources
    check('27-19-53' in str(ms_v.get('authority', '')), "MS authority cites §27-19-53")
    check('27-51-41' in str(ms_v.get('authority', '')), "MS authority cites §27-51-41")
    check(len(ms_v.get('sources', [])) >= 2, "MS has at least 2 sources")

    # Description mentions ad valorem
    check('ad valorem' in ms_v.get('description', '').lower(), "MS description mentions ad valorem")

    # ================================================================
    # SECTION 3: South Carolina vehicle_tax_exemption
    # ================================================================
    print("Section 3: South Carolina vehicle_tax_exemption")

    sc_v = sc['veteran_benefits'].get('vehicle_tax_exemption', {})
    check(sc_v.get('available') is True, "SC vehicle available == True")
    check(sc_v.get('exemption_type') == 'full', "SC vehicle exemption_type == full")
    check(sc_v.get('max_vehicles') == 2, "SC max_vehicles == 2")

    # Eligibility
    sc_elig = sc_v.get('eligibility', {})
    check(sc_elig.get('rating_required') == 100, "SC rating_required == 100")
    check(sc_elig.get('pt_required') is True, "SC pt_required == True")
    check(sc_elig.get('spouse_vehicle_eligible') is True, "SC spouse_vehicle_eligible == True")
    check('56-3-1110' in str(sc_elig.get('special_license_tags', '')), "SC cites §56-3-1110")

    # Trust-owned
    sc_trust = sc_v.get('trust_owned', {})
    check(sc_trust.get('eligible') is True, "SC trust-owned vehicles eligible")
    check('beneficiary' in str(sc_trust.get('conditions', '')).lower(), "SC trust conditions mention beneficiary")

    # Survivor
    check(sc_v.get('survivor_transfer') is True, "SC survivor_transfer == True")
    sc_surv = sc_v.get('survivor_conditions', {})
    check(sc_surv.get('unremarried_spouse') is True, "SC unremarried spouse eligible")
    check(sc_surv.get('max_vehicles_survivor') == 1, "SC survivor max_vehicles == 1")

    # POW/MOH
    check(sc_v.get('pow_moh_eligible') is True, "SC POW/MOH eligible")

    # Application
    sc_app = sc_v.get('application', {})
    check(sc_app.get('form') == 'PT-401I', "SC application form == PT-401I")
    check('MyDORWAY' in str(sc_app.get('where', '')), "SC application mentions MyDORWAY")

    # Authority
    check('12-37-220' in str(sc_v.get('authority', '')), "SC authority cites §12-37-220")
    check(len(sc_v.get('sources', [])) >= 2, "SC has at least 2 sources")

    # Cross-reference: old nested vehicle_exemption removed
    sc_prop = sc['veteran_benefits'].get('disabled_veteran_property_tax_exemption', {})
    check('vehicle_exemption' not in sc_prop, "SC: nested vehicle_exemption removed from property entry")
    check('_vehicle_cross_reference' in sc_prop, "SC: _vehicle_cross_reference added to property entry")

    # ================================================================
    # SECTION 4: Connecticut vehicle_tax_exemption
    # ================================================================
    print("Section 4: Connecticut vehicle_tax_exemption")

    ct_v = ct['veteran_benefits'].get('vehicle_tax_exemption', {})
    check(ct_v.get('available') is True, "CT vehicle available == True")
    check(ct_v.get('exemption_type') == 'full', "CT vehicle exemption_type == full")
    check(ct_v.get('max_vehicles') == 1, "CT max_vehicles == 1")

    # Eligibility
    ct_elig = ct_v.get('eligibility', {})
    check(ct_elig.get('rating_required') == 100, "CT rating_required == 100")
    check(ct_elig.get('pt_required') is True, "CT pt_required == True")
    check(ct_elig.get('must_not_own_dwelling') is True, "CT must_not_own_dwelling == True")
    check(ct_elig.get('vehicle_must_be_garaged_in_ct') is True, "CT vehicle must be garaged in CT")

    # Effective date
    check(ct_v.get('effective_date') == '2024-10-01', "CT effective_date == 2024-10-01")
    check('2026' in str(ct_v.get('effective_note', '')), "CT effective_note mentions 2026 tax bills")

    # Wartime veteran alternative
    ct_war = ct_v.get('wartime_veteran_alternative', {})
    check(ct_war.get('available') is True, "CT wartime alternative available")
    check('1,000' in str(ct_war.get('description', '')) or '1000' in str(ct_war.get('description', '')),
          "CT wartime alternative mentions $1,000 exemption")

    # Active duty
    ct_ad = ct_v.get('active_duty_exemption', {})
    check(ct_ad.get('available') is True, "CT active duty exemption available")

    # Survivor
    check(ct_v.get('survivor_transfer') is True, "CT survivor_transfer == True")
    ct_surv = ct_v.get('survivor_conditions', {})
    check(ct_surv.get('unremarried_spouse') is True, "CT unremarried spouse eligible")
    check(ct_surv.get('minor_child') is True, "CT minor child eligible")

    # Cannot combine
    check('12-81' in str(ct_v.get('cannot_combine_with', '')), "CT cannot_combine references §12-81")

    # Application
    ct_app = ct_v.get('application', {})
    check('D-2' in str(ct_app.get('form', '')), "CT application form includes D-2")
    check(ct_app.get('annual_filing') is True, "CT annual filing required")

    # Authority and sources
    check('PA 24-46' in str(ct_v.get('authority', '')), "CT authority cites PA 24-46")
    check('12-81(83)' in str(ct_v.get('authority', '')), "CT authority cites §12-81(83)")
    check(len(ct_v.get('sources', [])) >= 2, "CT has at least 2 sources")

    # Description mentions dwelling alternative
    check('dwelling' in ct_v.get('description', '').lower() or 'home' in ct_v.get('description', '').lower(),
          "CT description explains dwelling-alternative nature")

    # ================================================================
    # SECTION 5: Alabama vehicle_tax_exemption
    # ================================================================
    print("Section 5: Alabama vehicle_tax_exemption")

    al_v = al['veteran_benefits'].get('vehicle_tax_exemption', {})
    check(al_v.get('available') is True, "AL vehicle available == True")
    check(al_v.get('exemption_type') == 'full', "AL vehicle exemption_type == full")
    check(al_v.get('max_vehicles') == 1, "AL max_vehicles == 1")

    # Eligibility
    al_elig = al_v.get('eligibility', {})
    check(al_elig.get('va_funded_vehicle') is True, "AL va_funded_vehicle == True")
    check(al_elig.get('wartime_service_required') is True, "AL wartime_service_required == True")
    check(al_elig.get('private_use_only') is True, "AL private_use_only == True")

    # Registration fee exemption (broader benefit)
    al_reg = al_v.get('registration_fee_exemption', {})
    check(al_reg.get('available') is True, "AL registration fee exemption available")
    check(al_reg.get('rating_threshold') == 10, "AL registration fee rating_threshold == 10")
    check('50' in str(al_reg.get('description', '')), "AL registration fee describes 50%+ benefit")

    # Survivor
    check(al_v.get('survivor_transfer') is False, "AL survivor_transfer == False")

    # Authority
    check('40-12-254' in str(al_v.get('authority', '')), "AL authority cites §40-12-254")
    check(len(al_v.get('sources', [])) >= 2, "AL has at least 2 sources")

    # Description mentions VA funds
    check('va' in al_v.get('description', '').lower(), "AL description mentions VA")
    check('license' in al_v.get('description', '').lower() or 'ad valorem' in al_v.get('description', '').lower(),
          "AL description mentions license fees or ad valorem")

    # ================================================================
    # SECTION 6: Cross-reference notes (AR and NC)
    # ================================================================
    print("Section 6: Cross-reference notes")

    # Arkansas
    ar_note = ar['veteran_benefits'].get('_vehicle_note', '')
    check(isinstance(ar_note, str), "AR _vehicle_note is a string")
    check(len(ar_note) > 50, "AR _vehicle_note is substantive (>50 chars)")
    check('ad valorem' in ar_note.lower() or 'personal property' in ar_note.lower(),
          "AR _vehicle_note mentions ad valorem or personal property")
    check('tag renewal' in ar_note.lower() or 'registration' in ar_note.lower(),
          "AR _vehicle_note mentions tag renewal or registration")

    # North Carolina
    nc_note = nc['veteran_benefits'].get('_vehicle_note', '')
    check(isinstance(nc_note, str), "NC _vehicle_note is a string")
    check(len(nc_note) > 50, "NC _vehicle_note is substantive (>50 chars)")
    check('tag' in nc_note.lower() and 'tax' in nc_note.lower(),
          "NC _vehicle_note mentions Tag & Tax system")
    check('pending' in nc_note.lower() or 'S 660' in nc_note or 'H 39' in nc_note,
          "NC _vehicle_note mentions pending legislation")

    # ================================================================
    # SECTION 7: Pre-existing vehicle entries intact
    # ================================================================
    print("Section 7: Pre-existing vehicle entries intact")

    # Virginia
    va = find_state(states, 'VA')
    check('vehicle_tax_exemption' in va.get('veteran_benefits', {}),
          "VA vehicle_tax_exemption still present")
    va_v = va['veteran_benefits'].get('vehicle_tax_exemption', {})
    check(va_v.get('available') is True, "VA vehicle available == True")
    check(va_v.get('max_vehicles') == 1, "VA max_vehicles == 1")
    check(va_v.get('exemption_type') == 'full', "VA exemption_type == full")

    # Georgia
    ga = find_state(states, 'GA')
    check('vehicle_ad_valorem_exemption' in ga.get('veteran_benefits', {}),
          "GA vehicle_ad_valorem_exemption still present")

    # Hawaii
    hi = find_state(states, 'HI')
    check('vehicle_registration_fee_exemption' in hi.get('veteran_benefits', {}),
          "HI vehicle_registration_fee_exemption still present")

    # Oklahoma
    ok = find_state(states, 'OK')
    check('disabled_veteran_motor_vehicle_exemption' in ok.get('veteran_benefits', {}),
          "OK disabled_veteran_motor_vehicle_exemption still present")

    # Texas _vehicle_note
    tx = find_state(states, 'TX')
    check('_vehicle_note' in tx.get('veteran_benefits', {}),
          "TX _vehicle_note still present")

    # SC real property entry still exists
    check('disabled_veteran_property_tax_exemption' in sc.get('veteran_benefits', {}),
          "SC disabled_veteran_property_tax_exemption still present")

    # ================================================================
    # SECTION 8: Manifest checks
    # ================================================================
    print("Section 8: Manifest checks")

    sb_manifest = manifest.get('files', {}).get('state_benefits', {})
    m_ver = sb_manifest.get('version', '0')
    m_ver_parts = m_ver.split('.')
    m_ver_num = float(f"{m_ver_parts[0]}.{m_ver_parts[1]}") if len(m_ver_parts) >= 2 else float(m_ver_parts[0])
    check(m_ver_num >= 2.0, f"Manifest version >= 2.0 (got {m_ver})")

    m_desc = sb_manifest.get('description', '')
    check('vehicle' in m_desc.lower(), "Manifest description mentions vehicle")
    check('51' in m_desc or '56' in m_desc or '50 states' in m_desc.lower(), "Manifest description mentions jurisdiction count")
    check('personal property' in m_desc.lower() or 'vehicle' in m_desc.lower(),
          "Manifest description mentions personal property or vehicle")

    # ================================================================
    # Summary
    # ================================================================
    total = PASS + FAIL
    print(f"\n{'='*60}")
    print(f"Vehicle Audit Validation: {PASS}/{total} passed, {FAIL} failed, {WARN} warnings")
    print(f"{'='*60}")

    if FAIL > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
