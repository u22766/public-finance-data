#!/usr/bin/env python3
"""Tier 3A State Expansion Validation — CA, NY, OH, IL, MI, TN, SC, AL, MO, IN.

Validates data accuracy, schema conformance, and cross-field consistency
for the 10 Tier 3A state entries added in state-benefits v1.6.
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
        print(f"TIER 3A VALIDATION RESULTS")
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
            print(f"\n✓ ALL TIER 3A CHECKS PASSED")
        else:
            print(f"\n✗ TIER 3A VALIDATION FAILED")
        return len(self.failed) == 0


TIER3A_CODES = ["CA", "NY", "OH", "IL", "MI", "TN", "SC", "AL", "MO", "IN"]

EXPECTED_STATE_NAMES = {
    "CA": "California", "NY": "New York", "OH": "Ohio", "IL": "Illinois",
    "MI": "Michigan", "TN": "Tennessee", "SC": "South Carolina",
    "AL": "Alabama", "MO": "Missouri", "IN": "Indiana"
}

# States with no income tax — should NOT have military_retirement sub-key
NO_INCOME_TAX = ["TN"]

# States that fully exempt military retirement
FULL_EXEMPT = ["NY", "OH", "IL", "MI", "SC", "AL", "MO", "IN"]

# States with partial exemption
PARTIAL_EXEMPT = ["CA"]

VALID_EXEMPTION_TYPES = ["full", "partial", "deduction", "reduction", "discount", "grant", "credit"]


def load_data():
    """Load state-benefits.json from repo root."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "states", "state-benefits.json")
    with open(path) as f:
        return json.load(f)


def get_t3a_states(data):
    """Extract Tier 3A state entries."""
    return {s["state_code"]: s for s in data.get("states", []) if s.get("state_code") in TIER3A_CODES}


# ============================================================
# T3-0xx: Structural checks
# ============================================================

def check_all_present(states, results):
    """T3-001: All 10 Tier 3A states present."""
    for code in TIER3A_CODES:
        if code in states:
            results.add_pass(f"T3-001-present-{code}", f"{code} found")
        else:
            results.add_fail(f"T3-001-present-{code}", f"{code} MISSING from state-benefits.json")


def check_state_names(states, results):
    """T3-002: State names match expected values."""
    for code, expected_name in EXPECTED_STATE_NAMES.items():
        if code not in states:
            continue
        actual = states[code].get("state_name", "")
        if actual == expected_name:
            results.add_pass(f"T3-002-name-{code}")
        else:
            results.add_fail(f"T3-002-name-{code}", f"Expected '{expected_name}', got '{actual}'")


def check_required_sections(states, results):
    """T3-003: Each state has income_tax, property_tax or note, sources, veteran_benefits."""
    for code, state in states.items():
        has_income = bool(state.get("income_tax"))
        has_sources = bool(state.get("sources"))
        has_vet = bool(state.get("veteran_benefits"))

        if has_income and has_sources and has_vet:
            results.add_pass(f"T3-003-sections-{code}")
        else:
            missing = []
            if not has_income: missing.append("income_tax")
            if not has_sources: missing.append("sources")
            if not has_vet: missing.append("veteran_benefits")
            results.add_fail(f"T3-003-sections-{code}", f"Missing: {missing}")


def check_retiree_guidance(data, results):
    """T3-004: Root-level _retiree_guidance note exists."""
    if data.get("_retiree_guidance"):
        results.add_pass("T3-004-retiree-guidance", "Root _retiree_guidance note present")
    else:
        results.add_fail("T3-004-retiree-guidance", "Missing _retiree_guidance note at root level")


def check_version(data, results):
    """T3-005: Version is at least 1.6."""
    version = data.get("version", "")
    try:
        vf = float(version)
        if vf >= 1.6:
            results.add_pass("T3-005-version", f"Version {version} >= 1.6")
        else:
            results.add_fail("T3-005-version", f"Version {version} < 1.6")
    except ValueError:
        results.add_fail("T3-005-version", f"Version not numeric: {version}")


def check_total_state_count(data, results):
    """T3-006: Total states is at least 25 (15 prior + 10 Tier 3A)."""
    count = len(data.get("states", []))
    if count >= 25:
        results.add_pass("T3-006-count", f"{count} states (>= 25)")
    else:
        results.add_fail("T3-006-count", f"Expected >= 25 states, got {count}")


# ============================================================
# T3-1xx: Income tax checks
# ============================================================

def check_no_income_tax_states(states, results):
    """T3-100: No-income-tax states have taxes_federal_pension=False."""
    for code in NO_INCOME_TAX:
        if code not in states:
            continue
        it = states[code].get("income_tax", {})
        if it.get("taxes_federal_pension") is False:
            results.add_pass(f"T3-100-no-tax-{code}")
        else:
            results.add_fail(f"T3-100-no-tax-{code}",
                             f"{code} has no income tax but taxes_federal_pension != False")


def check_full_exempt_states(states, results):
    """T3-101: Full-exempt states show military_retirement.exempt=True."""
    for code in FULL_EXEMPT:
        if code not in states:
            continue
        it = states[code].get("income_tax", {})
        mr = it.get("military_retirement", {})
        if mr.get("exempt") is True:
            results.add_pass(f"T3-101-mil-exempt-{code}")
        else:
            results.add_fail(f"T3-101-mil-exempt-{code}",
                             f"{code} should show military_retirement.exempt=True")


def check_ca_partial_exemption(states, results):
    """T3-102: CA shows partial exemption with correct parameters."""
    if "CA" not in states:
        return
    it = states["CA"].get("income_tax", {})
    mr = it.get("military_retirement", {})

    # Should be partial, not full
    if mr.get("exempt") is False and mr.get("partial_exemption") is True:
        results.add_pass("T3-102-ca-partial", "CA correctly shows partial exemption")
    else:
        results.add_fail("T3-102-ca-partial", "CA should have exempt=False, partial_exemption=True")

    # Check $20K limit
    if mr.get("max_exclusion") == 20000:
        results.add_pass("T3-102-ca-20k", "CA $20,000 exclusion amount correct")
    else:
        results.add_fail("T3-102-ca-20k", f"Expected max_exclusion=20000, got {mr.get('max_exclusion')}")

    # Check AGI limits
    if mr.get("agi_limit_single") == 125000:
        results.add_pass("T3-102-ca-agi-single")
    else:
        results.add_fail("T3-102-ca-agi-single", f"Expected 125000, got {mr.get('agi_limit_single')}")

    if mr.get("agi_limit_joint") == 250000:
        results.add_pass("T3-102-ca-agi-joint")
    else:
        results.add_fail("T3-102-ca-agi-joint", f"Expected 250000, got {mr.get('agi_limit_joint')}")

    # Check sunset
    if mr.get("sunset_year") == 2030:
        results.add_pass("T3-102-ca-sunset", "CA sunset year 2030")
    else:
        results.add_fail("T3-102-ca-sunset", f"Expected sunset 2030, got {mr.get('sunset_year')}")


def check_ss_exempt(states, results):
    """T3-103: All Tier 3A states exempt Social Security (including no-tax states)."""
    for code, state in states.items():
        it = state.get("income_tax", {})
        ss = it.get("ss_income", {})
        # No-income-tax states inherently exempt
        if code in NO_INCOME_TAX:
            results.add_pass(f"T3-103-ss-{code}", "No income tax = SS exempt")
            continue
        if ss.get("exempt") is True:
            results.add_pass(f"T3-103-ss-{code}")
        else:
            results.add_fail(f"T3-103-ss-{code}", f"{code} should show ss_income.exempt=True")


def check_top_rates_reasonable(states, results):
    """T3-104: Top income tax rates are within reasonable range."""
    for code, state in states.items():
        it = state.get("income_tax", {})
        rate = it.get("top_rate")
        if rate is None:
            if code in NO_INCOME_TAX:
                results.add_pass(f"T3-104-rate-{code}", "No income tax")
            else:
                results.add_warning(f"T3-104-rate-{code}", "No top_rate specified")
            continue
        if 0.01 <= rate <= 0.15:
            results.add_pass(f"T3-104-rate-{code}", f"{rate*100:.2f}%")
        else:
            results.add_fail(f"T3-104-rate-{code}", f"Rate {rate} outside expected range 1-15%")


# ============================================================
# T3-2xx: Veteran benefits checks
# ============================================================

def check_veteran_benefits_structure(states, results):
    """T3-200: Each veteran_benefits has at least one non-underscore benefit key."""
    for code, state in states.items():
        vb = state.get("veteran_benefits", {})
        benefit_keys = [k for k in vb if not k.startswith("_")]
        if benefit_keys:
            results.add_pass(f"T3-200-vet-keys-{code}", f"{len(benefit_keys)} benefits")
        else:
            results.add_fail(f"T3-200-vet-keys-{code}", "No benefit entries found")


def check_exemption_types_valid(states, results):
    """T3-201: All exemption_type values are in allowed list."""
    for code, state in states.items():
        vb = state.get("veteran_benefits", {})
        for bk, bv in vb.items():
            if bk.startswith("_") or not isinstance(bv, dict):
                continue
            et = bv.get("exemption_type")
            if et is None:
                continue
            if et in VALID_EXEMPTION_TYPES:
                results.add_pass(f"T3-201-type-{code}-{bk}")
            else:
                results.add_fail(f"T3-201-type-{code}-{bk}",
                                 f"Invalid type '{et}', expected one of {VALID_EXEMPTION_TYPES}")


def check_ca_dv_exemption_amounts(states, results):
    """T3-210: CA disabled veterans exemption amounts are correct for 2025/2026."""
    if "CA" not in states:
        return
    vb = states["CA"].get("veteran_benefits", {})
    dve = vb.get("disabled_veterans_exemption", {})
    tiers = dve.get("tiers", {})

    basic = tiers.get("basic", {})
    if basic.get("amount_2025") == 175298:
        results.add_pass("T3-210-ca-basic-2025")
    else:
        results.add_fail("T3-210-ca-basic-2025", f"Expected 175298, got {basic.get('amount_2025')}")

    if basic.get("amount_2026") == 180671:
        results.add_pass("T3-210-ca-basic-2026")
    else:
        results.add_fail("T3-210-ca-basic-2026", f"Expected 180671, got {basic.get('amount_2026')}")

    low = tiers.get("low_income", {})
    if low.get("amount_2025") == 262950:
        results.add_pass("T3-210-ca-low-2025")
    else:
        results.add_fail("T3-210-ca-low-2025", f"Expected 262950, got {low.get('amount_2025')}")

    if low.get("amount_2026") == 271009:
        results.add_pass("T3-210-ca-low-2026")
    else:
        results.add_fail("T3-210-ca-low-2026", f"Expected 271009, got {low.get('amount_2026')}")


def check_oh_enhanced_homestead(states, results):
    """T3-211: OH enhanced homestead amounts correct."""
    if "OH" not in states:
        return
    vb = states["OH"].get("veteran_benefits", {})
    dvhe = vb.get("disabled_veteran_homestead_exemption", {})

    if dvhe.get("amount_2026") == 58000:
        results.add_pass("T3-211-oh-2026")
    else:
        results.add_fail("T3-211-oh-2026", f"Expected 58000, got {dvhe.get('amount_2026')}")

    elig = dvhe.get("eligibility", {})
    if elig.get("iu_eligible") is True:
        results.add_pass("T3-211-oh-iu", "OH IU eligible")
    else:
        results.add_fail("T3-211-oh-iu", "OH should show iu_eligible=True")


def check_il_tiers(states, results):
    """T3-212: IL tiered structure correct — 70%+ gets $250K EAV."""
    if "IL" not in states:
        return
    vb = states["IL"].get("veteran_benefits", {})
    shevd = vb.get("standard_homestead_exemption_for_veterans_with_disabilities", {})
    tiers = shevd.get("tiers", [])

    found_70 = False
    for t in tiers:
        if t.get("min_rating") == 70 and t.get("eav_reduction") == 250000:
            found_70 = True
    if found_70:
        results.add_pass("T3-212-il-70pct", "70%+ tier = $250,000 EAV")
    else:
        results.add_fail("T3-212-il-70pct", "IL 70%+ tier should show eav_reduction=250000")

    if len(tiers) == 3:
        results.add_pass("T3-212-il-tier-count", "3 tiers")
    else:
        results.add_fail("T3-212-il-tier-count", f"Expected 3 tiers, got {len(tiers)}")


def check_mi_iu_explicit(states, results):
    """T3-213: MI explicitly allows IU."""
    if "MI" not in states:
        return
    vb = states["MI"].get("veteran_benefits", {})
    dvpte = vb.get("disabled_veterans_property_tax_exemption", {})
    elig = dvpte.get("eligibility", {})

    if elig.get("iu_eligible") is True:
        results.add_pass("T3-213-mi-iu", "MI IU explicitly eligible")
    else:
        results.add_fail("T3-213-mi-iu", "MI should show iu_eligible=True")

    # Check no-reapplication note
    app = dvpte.get("application", {})
    reapp = app.get("reapplication", "")
    if "2025" in reapp and "not required" in reapp.lower():
        results.add_pass("T3-213-mi-no-reapp", "MI auto-renewal from 2025 documented")
    else:
        results.add_warning("T3-213-mi-no-reapp", "MI no-reapplication from 2025 should be documented")


def check_tn_reimbursement(states, results):
    """T3-214: TN correctly identifies as reimbursement/credit, not true exemption."""
    if "TN" not in states:
        return
    vb = states["TN"].get("veteran_benefits", {})
    dvptr = vb.get("disabled_veteran_property_tax_relief", {})

    if dvptr.get("max_market_value") == 175000:
        results.add_pass("T3-214-tn-175k", "TN $175K market value cap correct")
    else:
        results.add_fail("T3-214-tn-175k", f"Expected 175000, got {dvptr.get('max_market_value')}")

    if dvptr.get("credit_mechanism") == "reimbursement":
        results.add_pass("T3-214-tn-reimburse", "TN reimbursement mechanism documented")
    else:
        results.add_warning("T3-214-tn-reimburse", "TN should document credit_mechanism=reimbursement")


def check_sc_retroactive(states, results):
    """T3-215: SC retroactive to 2022 is documented."""
    if "SC" not in states:
        return
    vb = states["SC"].get("veteran_benefits", {})
    dvpte = vb.get("disabled_veteran_property_tax_exemption", {})

    if dvpte.get("retroactive_to") == 2022:
        results.add_pass("T3-215-sc-retro", "SC retroactive to 2022")
    else:
        results.add_fail("T3-215-sc-retro", f"Expected retroactive_to=2022, got {dvpte.get('retroactive_to')}")


def check_al_no_income_limit(states, results):
    """T3-216: AL P&T disabled has no income limit."""
    if "AL" not in states:
        return
    vb = states["AL"].get("veteran_benefits", {})
    dvhe = vb.get("disabled_veteran_homestead_exemption", {})

    il = dvhe.get("income_limit", "")
    if "none" in str(il).lower():
        results.add_pass("T3-216-al-no-limit", "AL no income limit for P&T")
    else:
        results.add_fail("T3-216-al-no-limit", f"AL P&T should have no income limit, got: {il}")


def check_mo_no_full_exemption(states, results):
    """T3-217: MO correctly shows NO general full property tax exemption."""
    if "MO" not in states:
        return
    vb = states["MO"].get("veteran_benefits", {})
    dvptc = vb.get("disabled_veteran_property_tax_credit", {})

    if dvptc.get("exemption_type") == "credit":
        results.add_pass("T3-217-mo-credit", "MO correctly uses credit type (not full exemption)")
    else:
        results.add_fail("T3-217-mo-credit", "MO should show exemption_type=credit")

    if dvptc.get("max_credit_homeowner") == 1100:
        results.add_pass("T3-217-mo-amount", "MO max credit $1,100")
    else:
        results.add_fail("T3-217-mo-amount", f"Expected 1100, got {dvptc.get('max_credit_homeowner')}")


def check_in_combined_deductions(states, results):
    """T3-218: IN deduction amounts are correct."""
    if "IN" not in states:
        return
    vb = states["IN"].get("veteran_benefits", {})

    wartime = vb.get("wartime_disabled_veteran_deduction", {})
    if wartime.get("deduction_amount") == 24960:
        results.add_pass("T3-218-in-wartime", "IN wartime deduction $24,960")
    else:
        results.add_fail("T3-218-in-wartime", f"Expected 24960, got {wartime.get('deduction_amount')}")

    total = vb.get("totally_disabled_veteran_deduction", {})
    if total.get("deduction_amount") == 14000:
        results.add_pass("T3-218-in-total", "IN total disability deduction $14,000")
    else:
        results.add_fail("T3-218-in-total", f"Expected 14000, got {total.get('deduction_amount')}")

    if total.get("assessed_value_cap") == 240000:
        results.add_pass("T3-218-in-cap", "IN $240K assessed value cap")
    else:
        results.add_fail("T3-218-in-cap", f"Expected 240000, got {total.get('assessed_value_cap')}")


def check_sources_not_empty(states, results):
    """T3-250: Each state has at least 2 sources."""
    for code, state in states.items():
        sources = state.get("sources", [])
        if len(sources) >= 2:
            results.add_pass(f"T3-250-sources-{code}", f"{len(sources)} sources")
        else:
            results.add_fail(f"T3-250-sources-{code}", f"Only {len(sources)} sources — minimum 2 required")


# ============================================================
# Main
# ============================================================

def main():
    data = load_data()
    states = get_t3a_states(data)
    results = ValidationResult()

    # Structural
    check_all_present(states, results)
    check_state_names(states, results)
    check_required_sections(states, results)
    check_retiree_guidance(data, results)
    check_version(data, results)
    check_total_state_count(data, results)

    # Income tax
    check_no_income_tax_states(states, results)
    check_full_exempt_states(states, results)
    check_ca_partial_exemption(states, results)
    check_ss_exempt(states, results)
    check_top_rates_reasonable(states, results)

    # Veteran benefits
    check_veteran_benefits_structure(states, results)
    check_exemption_types_valid(states, results)
    check_ca_dv_exemption_amounts(states, results)
    check_oh_enhanced_homestead(states, results)
    check_il_tiers(states, results)
    check_mi_iu_explicit(states, results)
    check_tn_reimbursement(states, results)
    check_sc_retroactive(states, results)
    check_al_no_income_limit(states, results)
    check_mo_no_full_exemption(states, results)
    check_in_combined_deductions(states, results)
    check_sources_not_empty(states, results)

    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
