#!/usr/bin/env python3
"""Tier 3B State Expansion Validation — NJ, MN, WI, KY, CT, OK, IA, AR, MS, KS.

Validates data accuracy, schema conformance, and cross-field consistency
for the 10 Tier 3B state entries added in state-benefits v1.7.
"""

import json
import os
import sys


class ValidationResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, check_id, msg=""):
        self.passed.append((check_id, msg))

    def add_fail(self, check_id, msg):
        self.failed.append((check_id, msg))

    def add_warning(self, check_id, msg):
        self.warnings.append((check_id, msg))

    def summary(self):
        print(f"\n{'='*60}")
        print(f"TIER 3B VALIDATION RESULTS")
        print(f"{'='*60}")
        if self.failed:
            print(f"\nFAILED ({len(self.failed)}):")
            for cid, msg in self.failed:
                print(f"  ✗ {cid}: {msg}")
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for cid, msg in self.warnings:
                print(f"  ⚠ {cid}: {msg}")
        print(f"\nTotal checks: {len(self.passed) + len(self.failed)}")
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        if not self.failed:
            print(f"\n✓ ALL TIER 3B CHECKS PASSED")
        else:
            print(f"\n✗ TIER 3B VALIDATION FAILED")
        return len(self.failed) == 0


TIER3B_CODES = ["NJ", "MN", "WI", "KY", "CT", "OK", "IA", "AR", "MS", "KS"]

EXPECTED_STATE_NAMES = {
    "NJ": "New Jersey", "MN": "Minnesota", "WI": "Wisconsin",
    "KY": "Kentucky", "CT": "Connecticut", "OK": "Oklahoma",
    "IA": "Iowa", "AR": "Arkansas", "MS": "Mississippi", "KS": "Kansas"
}

# States that fully exempt military retirement
FULL_EXEMPT = ["NJ", "MN", "WI", "CT", "OK", "IA", "AR", "MS", "KS"]

# States with partial exemption
PARTIAL_EXEMPT = ["KY"]

VALID_EXEMPTION_TYPES = ["full", "partial", "deduction", "reduction", "discount",
                         "grant", "credit", "refund"]


def load_data():
    """Load state-benefits.json from repo root."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "states", "state-benefits.json")
    with open(path) as f:
        return json.load(f)


def get_t3b_states(data):
    """Extract Tier 3B state entries."""
    states_list = data.get("states", [])
    result = {}
    for s in states_list:
        code = s.get("state_code", "")
        if code in TIER3B_CODES:
            result[code] = s
    return result


# ─── Section 1: Structural checks ───

def check_version(data, r):
    """Version must be 1.7+."""
    v = data.get("version", "0")
    try:
        vf = float(v)
        if vf >= 1.7:
            r.add_pass("META-01", f"Version {v} >= 1.7")
        else:
            r.add_fail("META-01", f"Version {v} < 1.7")
    except ValueError:
        r.add_fail("META-01", f"Version not numeric: {v}")


def check_total_state_count(data, r):
    """Must have at least 35 states (25 prior + 10 new)."""
    count = len(data.get("states", []))
    if count >= 35:
        r.add_pass("META-02", f"State count {count} >= 35")
    else:
        r.add_fail("META-02", f"State count {count} < 35")


def check_all_t3b_present(states, r):
    """All 10 Tier 3B states must be present."""
    for code in TIER3B_CODES:
        if code in states:
            r.add_pass(f"PRES-{code}", f"{code} present")
        else:
            r.add_fail(f"PRES-{code}", f"{code} missing from state-benefits.json")


def check_state_names(states, r):
    """State names must match expected values."""
    for code, expected_name in EXPECTED_STATE_NAMES.items():
        if code not in states:
            continue
        actual = states[code].get("state_name", "")
        if actual == expected_name:
            r.add_pass(f"NAME-{code}", f"{code} = {actual}")
        else:
            r.add_fail(f"NAME-{code}", f"Expected '{expected_name}', got '{actual}'")


# ─── Section 2: Income tax checks ───

def check_required_income_tax_keys(states, r):
    """All T3B states must have income_tax with military_retirement and va_compensation."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        inc = states[code].get("income_tax", {})
        for key in ["military_retirement", "va_compensation"]:
            if key in inc:
                r.add_pass(f"INC-{code}-{key}", f"{code} has {key}")
            else:
                r.add_fail(f"INC-{code}-{key}", f"{code} missing {key} in income_tax")


def check_full_exempt_states(states, r):
    """States in FULL_EXEMPT list must have military_retirement.exempt = True."""
    for code in FULL_EXEMPT:
        if code not in states:
            continue
        mr = states[code].get("income_tax", {}).get("military_retirement", {})
        if mr.get("exempt") is True:
            r.add_pass(f"EXEMPT-{code}", f"{code} military_retirement.exempt = True")
        else:
            r.add_fail(f"EXEMPT-{code}", f"{code} should have military_retirement.exempt = True")


def check_ky_partial_exemption(states, r):
    """Kentucky must have partial exemption with amount."""
    if "KY" not in states:
        return
    mr = states["KY"].get("income_tax", {}).get("military_retirement", {})
    if mr.get("partial_exemption") is True:
        r.add_pass("KY-PARTIAL-01", "KY has partial_exemption = True")
    else:
        r.add_fail("KY-PARTIAL-01", "KY should have partial_exemption = True")
    amt = mr.get("exemption_amount", 0)
    if 25000 <= amt <= 40000:
        r.add_pass("KY-PARTIAL-02", f"KY exemption_amount = {amt}")
    else:
        r.add_fail("KY-PARTIAL-02", f"KY exemption_amount {amt} out of expected range 25000-40000")


def check_va_comp_exempt(states, r):
    """All states must have va_compensation.exempt = True."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        va = states[code].get("income_tax", {}).get("va_compensation", {})
        if va.get("exempt") is True:
            r.add_pass(f"VACOMP-{code}", f"{code} va_compensation.exempt = True")
        else:
            r.add_fail(f"VACOMP-{code}", f"{code} va_compensation.exempt should be True")


def check_top_rates_reasonable(states, r):
    """Top rates should be between 0 and 0.15."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        inc = states[code].get("income_tax", {})
        rate = inc.get("top_rate")
        if rate is not None:
            if 0 < rate < 0.15:
                r.add_pass(f"RATE-{code}", f"{code} top_rate = {rate}")
            else:
                r.add_fail(f"RATE-{code}", f"{code} top_rate {rate} out of range (0, 0.15)")


# ─── Section 3: Veteran benefits structure checks ───

def check_veteran_benefits_structure(states, r):
    """All T3B states must have veteran_benefits with at least one benefit key."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        vb = states[code].get("veteran_benefits", {})
        # Count non-underscore keys (actual benefits, not schema notes)
        benefit_keys = [k for k in vb if not k.startswith("_")]
        if len(benefit_keys) >= 1:
            r.add_pass(f"VB-{code}", f"{code} has {len(benefit_keys)} veteran benefit(s)")
        else:
            r.add_fail(f"VB-{code}", f"{code} has no veteran benefit entries")


def check_exemption_types_valid(states, r):
    """All exemption_type values must be in the valid set."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        vb = states[code].get("veteran_benefits", {})
        for key, val in vb.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and "exemption_type" in val:
                etype = val["exemption_type"]
                if etype in VALID_EXEMPTION_TYPES:
                    r.add_pass(f"ETYPE-{code}-{key}", f"{code}.{key} type = {etype}")
                else:
                    r.add_fail(f"ETYPE-{code}-{key}",
                               f"{code}.{key} invalid exemption_type '{etype}'")


def check_sources_not_empty(states, r):
    """All states must have at least one source URL."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        sources = states[code].get("sources", [])
        if len(sources) >= 1:
            r.add_pass(f"SRC-{code}", f"{code} has {len(sources)} source(s)")
        else:
            r.add_fail(f"SRC-{code}", f"{code} has no sources")


# ─── Section 4: State-specific spot checks ───

def check_nj_full_exemption(states, r):
    """NJ must have full property tax exemption for 100% P&T."""
    if "NJ" not in states:
        return
    vb = states["NJ"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_property_tax_exemption", {})
    if dv.get("exemption_type") == "full":
        r.add_pass("NJ-DV-01", "NJ disabled veteran exemption is 'full'")
    else:
        r.add_fail("NJ-DV-01", "NJ disabled veteran exemption should be 'full'")
    elig = dv.get("eligibility", {})
    if elig.get("rating_required") == 100:
        r.add_pass("NJ-DV-02", "NJ requires 100% rating")
    else:
        r.add_fail("NJ-DV-02", "NJ should require 100% rating")
    if elig.get("iu_eligible") is True:
        r.add_pass("NJ-DV-03", "NJ IU eligible")
    else:
        r.add_fail("NJ-DV-03", "NJ should have iu_eligible = True")
    # Veteran $6000 income tax exemption
    inc = states["NJ"].get("income_tax", {})
    vex = inc.get("veteran_income_tax_exemption", {})
    if vex.get("amount") == 6000:
        r.add_pass("NJ-VEX-01", "NJ veteran income tax exemption = $6,000")
    else:
        r.add_fail("NJ-VEX-01", "NJ veteran income tax exemption should be $6,000")


def check_mn_market_value_exclusion(states, r):
    """MN must have two-tier market value exclusion with correct amounts."""
    if "MN" not in states:
        return
    vb = states["MN"].get("veteran_benefits", {})
    mve = vb.get("disabled_veteran_market_value_exclusion", {})
    tiers = mve.get("tiers", [])
    if len(tiers) == 2:
        r.add_pass("MN-MVE-01", "MN has 2 exclusion tiers")
    else:
        r.add_fail("MN-MVE-01", f"MN should have 2 tiers, got {len(tiers)}")
    # Check tier amounts
    amounts = [t.get("exclusion_amount") for t in tiers]
    if 150000 in amounts:
        r.add_pass("MN-MVE-02", "MN $150,000 tier present")
    else:
        r.add_fail("MN-MVE-02", "MN missing $150,000 tier")
    if 300000 in amounts:
        r.add_pass("MN-MVE-03", "MN $300,000 tier present")
    else:
        r.add_fail("MN-MVE-03", "MN missing $300,000 tier")
    # Minimum rating
    elig = mve.get("eligibility", {})
    if elig.get("rating_required") == 70:
        r.add_pass("MN-MVE-04", "MN minimum rating 70%")
    else:
        r.add_fail("MN-MVE-04", "MN minimum rating should be 70%")
    if elig.get("iu_eligible") is True:
        r.add_pass("MN-MVE-05", "MN IU eligible")
    else:
        r.add_fail("MN-MVE-05", "MN should have iu_eligible = True")
    if elig.get("primary_caregiver_eligible") is True:
        r.add_pass("MN-MVE-06", "MN primary caregiver eligible")
    else:
        r.add_fail("MN-MVE-06", "MN should have primary_caregiver_eligible = True")


def check_wi_credit_mechanism(states, r):
    """WI must use 'credit' type, not 'full' exemption."""
    if "WI" not in states:
        return
    vb = states["WI"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_property_tax_credit", {})
    if dv.get("exemption_type") == "credit":
        r.add_pass("WI-CR-01", "WI uses 'credit' mechanism (not exemption)")
    else:
        r.add_fail("WI-CR-01", "WI should use 'credit' type")
    elig = dv.get("eligibility", {})
    if "residency_requirement" in elig:
        r.add_pass("WI-CR-02", "WI has residency requirement documented")
    else:
        r.add_fail("WI-CR-02", "WI should document residency requirement")


def check_ky_homestead(states, r):
    """KY must have homestead exemption amount in correct range."""
    if "KY" not in states:
        return
    vb = states["KY"].get("veteran_benefits", {})
    he = vb.get("homestead_exemption_for_disabled_veterans", {})
    amt = he.get("amount_2025_2026", 0)
    if 45000 <= amt <= 55000:
        r.add_pass("KY-HE-01", f"KY homestead amount {amt} in range")
    else:
        r.add_fail("KY-HE-01", f"KY homestead {amt} not in expected range 45000-55000")
    # KY is NOT veteran-specific
    elig = he.get("eligibility", {})
    if elig.get("veteran_specific") is False:
        r.add_pass("KY-HE-02", "KY correctly notes exemption is not veteran-specific")
    else:
        r.add_warning("KY-HE-02", "KY should document that exemption is general, not veteran-specific")


def check_ct_new_pt_exemption(states, r):
    """CT must have the new (2024) full dwelling exemption for 100% P&T."""
    if "CT" not in states:
        return
    vb = states["CT"].get("veteran_benefits", {})
    pt = vb.get("pt_disabled_veteran_dwelling_exemption", {})
    if pt.get("exemption_type") == "full":
        r.add_pass("CT-PT-01", "CT P&T dwelling exemption is 'full'")
    else:
        r.add_fail("CT-PT-01", "CT P&T dwelling exemption should be 'full'")
    if pt.get("effective_date") == "2024-10-01":
        r.add_pass("CT-PT-02", "CT effective date 2024-10-01")
    else:
        r.add_fail("CT-PT-02", "CT effective date should be 2024-10-01")
    # IU ambiguity should be documented
    elig = pt.get("eligibility", {})
    iu = elig.get("iu_eligible", "")
    if isinstance(iu, str) and "ambiguous" in iu.lower():
        r.add_pass("CT-PT-03", "CT IU ambiguity documented")
    else:
        r.add_warning("CT-PT-03", "CT should document IU eligibility ambiguity")
    # Also has tiered system
    tiered = vb.get("disabled_veteran_tiered_exemption", {})
    if tiered.get("available") is True:
        r.add_pass("CT-TIER-01", "CT also has older tiered exemption system")
    else:
        r.add_fail("CT-TIER-01", "CT should also have tiered exemption system")


def check_ok_constitutional(states, r):
    """OK must reference constitutional provision and full exemption."""
    if "OK" not in states:
        return
    vb = states["OK"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_property_tax_exemption", {})
    if dv.get("exemption_type") == "full":
        r.add_pass("OK-DV-01", "OK full exemption")
    else:
        r.add_fail("OK-DV-01", "OK should have full exemption")
    auth = dv.get("authority", "")
    if "Art. 10" in auth or "8E" in auth:
        r.add_pass("OK-DV-02", "OK references constitutional provision")
    else:
        r.add_fail("OK-DV-02", "OK should reference Okla. Const. Art. 10, §8E")
    # Sales tax exemption
    stx = vb.get("disabled_veteran_sales_tax_exemption", {})
    if stx.get("available") is True and stx.get("annual_limit") == 25000:
        r.add_pass("OK-STX-01", "OK sales tax exemption $25,000")
    else:
        r.add_fail("OK-STX-01", "OK sales tax exemption should be available with $25,000 limit")


def check_ia_full_credit(states, r):
    """IA must have 100% property tax credit for 100% disabled veterans."""
    if "IA" not in states:
        return
    vb = states["IA"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_homestead_tax_credit", {})
    if dv.get("exemption_type") == "credit":
        r.add_pass("IA-DV-01", "IA uses 'credit' type")
    else:
        r.add_fail("IA-DV-01", "IA should use 'credit' type")
    elig = dv.get("eligibility", {})
    if elig.get("iu_eligible") is True:
        r.add_pass("IA-DV-02", "IA IU eligible")
    else:
        r.add_fail("IA-DV-02", "IA should have iu_eligible = True")
    if elig.get("sah_grant_recipients") is True:
        r.add_pass("IA-DV-03", "IA SAH grant recipients eligible")
    else:
        r.add_fail("IA-DV-03", "IA should note SAH grant recipients eligible")
    # DIC survivors
    surv = dv.get("survivor_conditions", {})
    if surv.get("dic_recipients_eligible") is True:
        r.add_pass("IA-DV-04", "IA DIC survivors eligible")
    else:
        r.add_fail("IA-DV-04", "IA should note DIC survivors eligible")
    # Size limits
    limits = dv.get("size_limits", {})
    if "0.5" in str(limits.get("within_city", "")) or "1/2" in str(limits.get("within_city", "")):
        r.add_pass("IA-DV-05", "IA city size limit documented")
    else:
        r.add_fail("IA-DV-05", "IA should document 0.5 acre city limit")
    # Military service exemption
    mse = vb.get("military_service_tax_exemption", {})
    if mse.get("amount_wartime") == 1852:
        r.add_pass("IA-MSE-01", "IA military service exemption = $1,852")
    else:
        r.add_fail("IA-MSE-01", "IA military service exemption should be $1,852")


def check_ar_full_exemption(states, r):
    """AR must have full exemption for 100% disabled veterans."""
    if "AR" not in states:
        return
    vb = states["AR"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_property_tax_exemption", {})
    if dv.get("exemption_type") == "full":
        r.add_pass("AR-DV-01", "AR full exemption")
    else:
        r.add_fail("AR-DV-01", "AR should have full exemption")
    elig = dv.get("eligibility", {})
    alt = elig.get("alternative_qualifying_conditions", [])
    if len(alt) >= 2:
        r.add_pass("AR-DV-02", f"AR has {len(alt)} alternative qualifying conditions")
    else:
        r.add_fail("AR-DV-02", "AR should have alternative conditions (blind, limb loss)")


def check_ms_full_exemption(states, r):
    """MS must have full exemption for 100% P&T disabled veterans."""
    if "MS" not in states:
        return
    vb = states["MS"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_property_tax_exemption", {})
    if dv.get("exemption_type") == "full":
        r.add_pass("MS-DV-01", "MS full exemption")
    else:
        r.add_fail("MS-DV-01", "MS should have full exemption")
    elig = dv.get("eligibility", {})
    if elig.get("pt_required") is True:
        r.add_pass("MS-DV-02", "MS requires P&T")
    else:
        r.add_fail("MS-DV-02", "MS should require P&T")


def check_ks_refund_not_exemption(states, r):
    """KS must use 'refund' type (not full exemption)."""
    if "KS" not in states:
        return
    vb = states["KS"].get("veteran_benefits", {})
    dv = vb.get("disabled_veteran_homestead_refund", {})
    if dv.get("exemption_type") == "refund":
        r.add_pass("KS-DV-01", "KS uses 'refund' type (not exemption)")
    else:
        r.add_fail("KS-DV-01", "KS should use 'refund' type")
    if dv.get("max_refund") == 700:
        r.add_pass("KS-DV-02", "KS max refund = $700")
    else:
        r.add_fail("KS-DV-02", "KS max refund should be $700")
    elig = dv.get("eligibility", {})
    if elig.get("rating_required") == 50:
        r.add_pass("KS-DV-03", "KS minimum rating 50%")
    else:
        r.add_fail("KS-DV-03", "KS minimum rating should be 50%")
    # New sales tax exemption (2026)
    stx = vb.get("disabled_veteran_sales_tax_exemption", {})
    if stx.get("effective_date") == "2026-07-01":
        r.add_pass("KS-STX-01", "KS sales tax exemption effective 2026-07-01")
    else:
        r.add_fail("KS-STX-01", "KS sales tax exemption should be effective 2026-07-01")


# ─── Section 5: Cross-state consistency checks ───

def check_full_exemption_states(states, r):
    """States known to have full exemptions must have exemption_type = 'full'."""
    full_exemption_states = ["NJ", "OK", "AR", "MS"]
    for code in full_exemption_states:
        if code not in states:
            continue
        vb = states[code].get("veteran_benefits", {})
        found_full = False
        for key, val in vb.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and val.get("exemption_type") == "full":
                found_full = True
                break
        if found_full:
            r.add_pass(f"FULL-{code}", f"{code} has a 'full' exemption")
        else:
            r.add_fail(f"FULL-{code}", f"{code} should have at least one 'full' exemption")


def check_survivor_transfer_present(states, r):
    """All states must document survivor_transfer in primary veteran benefit."""
    for code in TIER3B_CODES:
        if code not in states:
            continue
        vb = states[code].get("veteran_benefits", {})
        has_survivor = False
        for key, val in vb.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and "survivor_transfer" in val:
                has_survivor = True
                break
        if has_survivor:
            r.add_pass(f"SURV-{code}", f"{code} has survivor_transfer documented")
        else:
            r.add_fail(f"SURV-{code}", f"{code} should document survivor_transfer")


# ─── Section 6: Manifest check ───

def check_manifest(r):
    """Manifest must reference state_benefits v1.7 with 35 states."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "manifest.json")
    with open(path) as f:
        m = json.load(f)
    sb = m.get("files", {}).get("state_benefits", {})
    v = sb.get("version", "")
    if v == "1.7":
        r.add_pass("MAN-01", "Manifest state_benefits version = 1.7")
    else:
        r.add_fail("MAN-01", f"Manifest state_benefits version should be 1.7, got {v}")
    desc = sb.get("description", "")
    if "35" in desc:
        r.add_pass("MAN-02", "Manifest description references 35 states")
    else:
        r.add_fail("MAN-02", f"Manifest description should reference 35 states")
    # Check all 10 new codes are mentioned
    for code in TIER3B_CODES:
        if code in desc:
            r.add_pass(f"MAN-{code}", f"Manifest description includes {code}")
        else:
            r.add_fail(f"MAN-{code}", f"Manifest description should include {code}")


def main():
    data = load_data()
    states = get_t3b_states(data)
    results = ValidationResult()

    # Section 1: Structural
    check_version(data, results)
    check_total_state_count(data, results)
    check_all_t3b_present(states, results)
    check_state_names(states, results)

    # Section 2: Income tax
    check_required_income_tax_keys(states, results)
    check_full_exempt_states(states, results)
    check_ky_partial_exemption(states, results)
    check_va_comp_exempt(states, results)
    check_top_rates_reasonable(states, results)

    # Section 3: Veteran benefits structure
    check_veteran_benefits_structure(states, results)
    check_exemption_types_valid(states, results)
    check_sources_not_empty(states, results)

    # Section 4: State-specific spot checks
    check_nj_full_exemption(states, results)
    check_mn_market_value_exclusion(states, results)
    check_wi_credit_mechanism(states, results)
    check_ky_homestead(states, results)
    check_ct_new_pt_exemption(states, results)
    check_ok_constitutional(states, results)
    check_ia_full_credit(states, results)
    check_ar_full_exemption(states, results)
    check_ms_full_exemption(states, results)
    check_ks_refund_not_exemption(states, results)

    # Section 5: Cross-state consistency
    check_full_exemption_states(states, results)
    check_survivor_transfer_present(states, results)

    # Section 6: Manifest
    check_manifest(results)

    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
