#!/usr/bin/env python3
"""
Validation suite for LEO Premium Pay and FERS Computation Rules.
Tests: federal/leo-premium-pay.json and federal/fers-computation-rules.json
"""

import json
import os
import sys
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEO_FILE = os.path.join(REPO_ROOT, "federal", "leo-premium-pay.json")
FERS_COMP_FILE = os.path.join(REPO_ROOT, "federal", "fers-computation-rules.json")
MANIFEST_FILE = os.path.join(REPO_ROOT, "manifest.json")

passed = 0
failed = 0
errors = []


def check(condition, description):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(description)
        print(f"  FAIL: {description}")


def validate_leo_premium_pay():
    global passed, failed
    print("=" * 60)
    print("Validating: federal/leo-premium-pay.json")
    print("=" * 60)

    # --- File existence ---
    check(os.path.isfile(LEO_FILE), "leo-premium-pay.json exists")
    if not os.path.isfile(LEO_FILE):
        print("  SKIP: File not found, skipping remaining LEO checks")
        return

    with open(LEO_FILE) as f:
        data = json.load(f)

    # --- Metadata ---
    check("metadata" in data, "LEO: metadata section present")
    meta = data.get("metadata", {})
    check(meta.get("schema_version") == "2.2", "LEO: schema_version is 2.2")
    check("sources" in meta and len(meta["sources"]) >= 3, "LEO: at least 3 sources listed")
    check("version" in meta, "LEO: version field present")
    check("last_updated" in meta, "LEO: last_updated field present")

    # --- LEAP Section ---
    check("leap" in data, "LEO: leap section present")
    leap = data.get("leap", {})

    # LEAP rate must be exactly 0.25
    check(leap.get("rate") == 0.25, f"LEO: LEAP rate must equal 0.25 (got {leap.get('rate')})")
    check(leap.get("rate_type") == "flat", "LEO: LEAP rate_type is 'flat'")
    check(leap.get("statutory_authority") == "5 USC §5545a", "LEO: LEAP statutory authority is 5 USC §5545a")
    check("description" in leap and len(leap["description"]) > 20, "LEO: LEAP description is substantive")
    check("retirement_treatment" in leap, "LEO: LEAP retirement_treatment documented")
    check("tsp_treatment" in leap, "LEO: LEAP tsp_treatment documented")
    check("life_insurance_treatment" in leap, "LEO: LEAP life_insurance_treatment documented")
    check("premium_pay_cap" in leap, "LEO: LEAP premium_pay_cap documented")
    check("substantial_hours_requirement" in leap, "LEO: LEAP substantial_hours_requirement documented")
    check("exclusions" in leap, "LEO: LEAP exclusions documented")

    # LEAP eligible series
    check("eligible_series" in leap, "LEO: LEAP eligible_series present")
    series_list = leap.get("eligible_series", [])
    check(len(series_list) >= 2, f"LEO: At least 2 eligible series (got {len(series_list)})")

    series_codes = [s.get("series") for s in series_list]
    check("1811" in series_codes, "LEO: Series 1811 (Criminal Investigation) in LEAP eligible list")
    check("1812" in series_codes, "LEO: Series 1812 (Game Law Enforcement) in LEAP eligible list")

    # Validate all series codes are 4-digit format
    for entry in series_list:
        code = entry.get("series", "")
        check(
            re.match(r"^\d{4}$", code) is not None,
            f"LEO: LEAP series '{code}' is valid 4-digit OPM series format"
        )
        check("title" in entry, f"LEO: LEAP series {code} has title")
        check("note" in entry, f"LEO: LEAP series {code} has note")

    # Position-based eligibility note
    check("_note_eligibility" in leap, "LEO: LEAP position-based eligibility note present")

    # --- AUO Section ---
    check("auo" in data, "LEO: auo section present")
    auo = data.get("auo", {})

    # AUO rate boundaries
    check(auo.get("min_rate") == 0.10, f"LEO: AUO min_rate must equal 0.10 (got {auo.get('min_rate')})")
    check(auo.get("max_rate") == 0.25, f"LEO: AUO max_rate must equal 0.25 (got {auo.get('max_rate')})")
    check(
        auo.get("max_rate", 0) >= auo.get("min_rate", 1),
        "LEO: AUO max_rate >= min_rate (boundary integrity)"
    )
    check(auo.get("rate_type") == "tiered", "LEO: AUO rate_type is 'tiered'")
    check(auo.get("statutory_authority") == "5 USC §5545(c)(2)", "LEO: AUO statutory authority is 5 USC §5545(c)(2)")
    check("description" in auo and len(auo["description"]) > 20, "LEO: AUO description is substantive")
    check("retirement_treatment" in auo, "LEO: AUO retirement_treatment documented")
    check("rate_determination" in auo, "LEO: AUO rate_determination documented")
    check("exclusions" in auo, "LEO: AUO exclusions documented")

    # AUO rate tiers
    check("rate_tiers" in auo, "LEO: AUO rate_tiers present")
    tiers = auo.get("rate_tiers", [])
    check(len(tiers) == 4, f"LEO: AUO must have exactly 4 rate tiers (got {len(tiers)})")

    expected_rates = [0.10, 0.15, 0.20, 0.25]
    for i, tier in enumerate(tiers):
        check(
            tier.get("rate") == expected_rates[i] if i < len(expected_rates) else False,
            f"LEO: AUO tier {i+1} rate is {expected_rates[i] if i < len(expected_rates) else '?'} (got {tier.get('rate')})"
        )
        check("hours_per_week_min" in tier, f"LEO: AUO tier {i+1} has hours_per_week_min")
        check("label" in tier, f"LEO: AUO tier {i+1} has label")

    # Tier boundary continuity: each tier's min should equal prior tier's max
    for i in range(1, len(tiers)):
        prev_max = tiers[i-1].get("hours_per_week_max")
        curr_min = tiers[i].get("hours_per_week_min")
        check(
            prev_max is not None and curr_min is not None and prev_max == curr_min,
            f"LEO: AUO tier boundary continuity: tier {i} max ({prev_max}) == tier {i+1} min ({curr_min})"
        )

    # Last tier has no upper bound
    check(
        tiers[-1].get("hours_per_week_max") is None if tiers else False,
        "LEO: AUO highest tier has no upper hour bound (null)"
    )

    # --- Position-to-Premium Map ---
    check("position_premium_map" in data, "LEO: position_premium_map present")
    pmap = data.get("position_premium_map", [])
    check(len(pmap) >= 4, f"LEO: At least 4 position mappings (got {len(pmap)})")

    premium_types_seen = set()
    for entry in pmap:
        code = entry.get("series", "")
        check(
            re.match(r"^\d{4}$", code) is not None,
            f"LEO: Position map series '{code}' is valid 4-digit format"
        )
        check("typical_premium" in entry, f"LEO: Position map series {code} has typical_premium")
        check("note" in entry, f"LEO: Position map series {code} has note")
        premium_types_seen.add(entry.get("typical_premium"))

    # Should cover leap, auo, varies, and none
    check("leap" in premium_types_seen, "LEO: Position map includes 'leap' premium type")
    check("auo" in premium_types_seen, "LEO: Position map includes 'auo' premium type")
    check("varies" in premium_types_seen, "LEO: Position map includes 'varies' premium type")
    check("none" in premium_types_seen, "LEO: Position map includes 'none' premium type")

    # Mutual exclusivity note
    check("_note_mutual_exclusivity" in data, "LEO: Mutual exclusivity note present")

    # --- No PII ---
    raw = json.dumps(data)
    check("SSN" not in raw and "social security number" not in raw.lower(), "LEO: No PII detected")

    # --- No consumer-specific references ---
    check(
        "meridian" not in raw.lower() and "engine" not in raw.lower(),
        "LEO: No consumer-specific references (Meridian/engine)"
    )


def validate_fers_computation_rules():
    global passed, failed
    print()
    print("=" * 60)
    print("Validating: federal/fers-computation-rules.json")
    print("=" * 60)

    # --- File existence ---
    check(os.path.isfile(FERS_COMP_FILE), "FERS-COMP: fers-computation-rules.json exists")
    if not os.path.isfile(FERS_COMP_FILE):
        print("  SKIP: File not found, skipping remaining FERS computation checks")
        return

    with open(FERS_COMP_FILE) as f:
        data = json.load(f)

    # --- Metadata ---
    check("metadata" in data, "FERS-COMP: metadata section present")
    meta = data.get("metadata", {})
    check(meta.get("schema_version") == "2.2", "FERS-COMP: schema_version is 2.2")
    check("sources" in meta and len(meta["sources"]) >= 3, "FERS-COMP: at least 3 sources listed")
    check("version" in meta, "FERS-COMP: version field present")

    # --- Standard Formula ---
    check("standard_formula" in data, "FERS-COMP: standard_formula section present")
    sf = data.get("standard_formula", {})
    check(sf.get("standard_multiplier") == 0.01, f"FERS-COMP: standard_multiplier is 0.01 (got {sf.get('standard_multiplier')})")
    check(sf.get("enhanced_multiplier") == 0.011, f"FERS-COMP: enhanced_multiplier is 0.011 (got {sf.get('enhanced_multiplier')})")
    check("enhanced_condition" in sf, "FERS-COMP: enhanced_condition documented")
    check("formula" in sf, "FERS-COMP: formula string present")

    # --- Special Category ---
    check("special_category" in data, "FERS-COMP: special_category section present")
    sc = data.get("special_category", {})
    check(sc.get("fers_multiplier_first_20") == 0.017, f"FERS-COMP: SC first 20 multiplier is 0.017 (got {sc.get('fers_multiplier_first_20')})")
    check(sc.get("fers_multiplier_beyond_20") == 0.01, f"FERS-COMP: SC beyond 20 multiplier is 0.01 (got {sc.get('fers_multiplier_beyond_20')})")
    check("formula" in sc, "FERS-COMP: SC formula string present")

    # SC eligible categories
    cats = sc.get("eligible_categories", [])
    check(len(cats) >= 7, f"FERS-COMP: At least 7 SC categories (got {len(cats)})")

    expected_cats = {
        "law_enforcement_officer", "firefighter", "nuclear_materials_courier",
        "customs_border_protection_officer", "capitol_police",
        "supreme_court_police", "air_traffic_controller"
    }
    actual_cats = {c.get("category") for c in cats}
    for ec in expected_cats:
        check(ec in actual_cats, f"FERS-COMP: SC category '{ec}' present")

    for cat in cats:
        check("title" in cat, f"FERS-COMP: SC category '{cat.get('category')}' has title")
        check("statutory_reference" in cat, f"FERS-COMP: SC category '{cat.get('category')}' has statutory_reference")
        check("mandatory_retirement_age" in cat, f"FERS-COMP: SC category '{cat.get('category')}' has mandatory_retirement_age")
        mra = cat.get("mandatory_retirement_age")
        if cat.get("category") == "air_traffic_controller":
            check(mra == 56, f"FERS-COMP: ATC mandatory retirement age is 56 (got {mra})")
        else:
            check(mra == 57, f"FERS-COMP: SC category '{cat.get('category')}' mandatory retirement age is 57 (got {mra})")

    # SC retirement eligibility
    check("retirement_eligibility" in sc, "FERS-COMP: SC retirement_eligibility present")

    # --- MRA+10 Age Reduction ---
    check("mra_plus_10_reduction" in data, "FERS-COMP: mra_plus_10_reduction section present")
    mra = data.get("mra_plus_10_reduction", {})
    check(
        mra.get("reduction_per_year") == 0.05,
        f"FERS-COMP: MRA+10 reduction_per_year is 0.05 (got {mra.get('reduction_per_year')})"
    )
    # 5/12 of 1% = 0.00416666... — check within tolerance
    rpm = mra.get("reduction_per_month", 0)
    check(
        abs(rpm - 0.004167) < 0.0001,
        f"FERS-COMP: MRA+10 reduction_per_month ≈ 0.004167 (got {rpm})"
    )
    # Verify 12 × monthly ≈ annual
    check(
        abs(rpm * 12 - mra.get("reduction_per_year", 0)) < 0.001,
        "FERS-COMP: MRA+10 monthly × 12 ≈ annual rate (internal consistency)"
    )
    check("does_not_apply_if" in mra, "FERS-COMP: MRA+10 does_not_apply_if conditions listed")
    check(
        isinstance(mra.get("does_not_apply_if"), list) and len(mra["does_not_apply_if"]) >= 2,
        "FERS-COMP: MRA+10 at least 2 exception conditions"
    )
    check("postponement" in mra, "FERS-COMP: MRA+10 postponement rules documented")
    check("csrs_component_impact" in mra, "FERS-COMP: MRA+10 CSRS component impact documented")
    check("source" in mra, "FERS-COMP: MRA+10 source URL present")

    # --- FERS Disability ---
    check("fers_disability" in data, "FERS-COMP: fers_disability section present")
    dis = data.get("fers_disability", {})

    # Eligibility
    check("eligibility" in dis, "FERS-COMP: disability eligibility section present")
    elig = dis.get("eligibility", {})
    check("minimum_service" in elig, "FERS-COMP: disability minimum_service documented")

    # First 12 months
    check("first_12_months" in dis, "FERS-COMP: disability first_12_months present")
    f12 = dis.get("first_12_months", {})
    check(f12.get("rate") == 0.60, f"FERS-COMP: disability first 12 months rate is 0.60 (got {f12.get('rate')})")
    check(f12.get("ss_offset") == 1.00, f"FERS-COMP: disability first 12 months SS offset is 1.00 (got {f12.get('ss_offset')})")
    check(f12.get("floor") == "earned_annuity", "FERS-COMP: disability first 12 months floor is earned_annuity")
    check(f12.get("cola_eligibility") is False, "FERS-COMP: disability first 12 months no COLA eligibility")

    # After 12 months
    check("after_12_months" in dis, "FERS-COMP: disability after_12_months present")
    a12 = dis.get("after_12_months", {})
    check(a12.get("rate") == 0.40, f"FERS-COMP: disability after 12 months rate is 0.40 (got {a12.get('rate')})")
    check(a12.get("ss_offset") == 0.60, f"FERS-COMP: disability after 12 months SS offset is 0.60 (got {a12.get('ss_offset')})")
    check(a12.get("floor") == "earned_annuity", "FERS-COMP: disability after 12 months floor is earned_annuity")

    # Recomputation at 62
    check("recomputation_at_62" in dis, "FERS-COMP: disability recomputation_at_62 present")
    r62 = dis.get("recomputation_at_62", {})
    check(r62.get("standard_multiplier") == 0.01, f"FERS-COMP: disability recomp standard mult is 0.01 (got {r62.get('standard_multiplier')})")
    check(r62.get("enhanced_multiplier") == 0.011, f"FERS-COMP: disability recomp enhanced mult is 0.011 (got {r62.get('enhanced_multiplier')})")
    check(r62.get("enhanced_threshold_years") == 20, f"FERS-COMP: disability recomp enhanced threshold is 20 (got {r62.get('enhanced_threshold_years')})")
    check("service_credit" in r62, "FERS-COMP: disability recomp service_credit documented")
    check("high_3_adjustment" in r62, "FERS-COMP: disability recomp high_3_adjustment documented")

    # Earning capacity test
    check("earning_capacity_test" in dis, "FERS-COMP: disability earning_capacity_test documented")

    check("source" in dis, "FERS-COMP: disability source URL present")

    # --- CSRS-to-FERS Transfer ---
    check("csrs_to_fers_transfer" in data, "FERS-COMP: csrs_to_fers_transfer section present")
    xfer = data.get("csrs_to_fers_transfer", {})
    check("eligibility" in xfer, "FERS-COMP: CSRS transfer eligibility documented")
    check("components" in xfer and len(xfer["components"]) == 2, "FERS-COMP: CSRS transfer has 2 components")

    # FERS component
    check("fers_component" in xfer, "FERS-COMP: CSRS transfer fers_component present")
    fc = xfer.get("fers_component", {})
    check(fc.get("standard_multiplier") == 0.01, f"FERS-COMP: CSRS transfer FERS mult is 0.01 (got {fc.get('standard_multiplier')})")
    check(fc.get("enhanced_multiplier") == 0.011, f"FERS-COMP: CSRS transfer FERS enhanced mult is 0.011 (got {fc.get('enhanced_multiplier')})")

    # CSRS component
    check("csrs_component" in xfer, "FERS-COMP: CSRS transfer csrs_component present")
    cc = xfer.get("csrs_component", {})
    check(cc.get("first_5_years") == 0.015, f"FERS-COMP: CSRS transfer first 5 years is 0.015 (got {cc.get('first_5_years')})")
    check(cc.get("next_5_years") == 0.0175, f"FERS-COMP: CSRS transfer next 5 years is 0.0175 (got {cc.get('next_5_years')})")
    check(cc.get("beyond_10_years") == 0.02, f"FERS-COMP: CSRS transfer beyond 10 years is 0.02 (got {cc.get('beyond_10_years')})")
    check("formula" in cc, "FERS-COMP: CSRS transfer csrs_component formula string present")

    # CSRS SC component
    check("csrs_component_sc" in xfer, "FERS-COMP: CSRS transfer SC component present")
    csc = xfer.get("csrs_component_sc", {})
    check(csc.get("first_20_years") == 0.025, f"FERS-COMP: CSRS transfer SC first 20 is 0.025 (got {csc.get('first_20_years')})")
    check(csc.get("beyond_20_years") == 0.02, f"FERS-COMP: CSRS transfer SC beyond 20 is 0.02 (got {csc.get('beyond_20_years')})")

    # COLA treatment
    check("cola_treatment" in xfer, "FERS-COMP: CSRS transfer COLA treatment documented")

    check("source" in xfer, "FERS-COMP: CSRS transfer source URL present")

    # --- Congressional Employee ---
    check("congressional_employee" in data, "FERS-COMP: congressional_employee section present")
    cong = data.get("congressional_employee", {})
    check(cong.get("fers_multiplier_first_20") == 0.017, f"FERS-COMP: Congressional first 20 mult is 0.017 (got {cong.get('fers_multiplier_first_20')})")
    check(cong.get("fers_multiplier_beyond_20") == 0.01, f"FERS-COMP: Congressional beyond 20 mult is 0.01 (got {cong.get('fers_multiplier_beyond_20')})")
    check("eligibility" in cong, "FERS-COMP: Congressional eligibility documented")
    check(cong.get("includes_capitol_police") is True, "FERS-COMP: Congressional includes Capitol Police = true")
    check("fers_rae_frae_exclusion" in cong, "FERS-COMP: Congressional FERS-RAE/FRAE exclusion documented")

    # CSRS Congressional component
    check("csrs_component_if_transferred" in cong, "FERS-COMP: Congressional CSRS transfer component present")
    ccong = cong.get("csrs_component_if_transferred", {})
    check(ccong.get("first_tier_rate") == 0.025, f"FERS-COMP: Congressional CSRS first tier is 0.025 (got {ccong.get('first_tier_rate')})")
    check(ccong.get("second_tier_rate") == 0.0175, f"FERS-COMP: Congressional CSRS second tier is 0.0175 (got {ccong.get('second_tier_rate')})")
    check(ccong.get("third_tier_rate") == 0.02, f"FERS-COMP: Congressional CSRS third tier is 0.02 (got {ccong.get('third_tier_rate')})")

    check("source" in cong, "FERS-COMP: Congressional source URL present")

    # --- Cross-file consistency with rates-annual.json ---
    rates_file = os.path.join(REPO_ROOT, "federal", "rates-annual.json")
    if os.path.isfile(rates_file):
        rates = json.load(open(rates_file))
        fers_rates = rates.get("fers", {})
        check(
            sf.get("standard_multiplier") == fers_rates.get("standard_multiplier_default"),
            "FERS-COMP: standard_multiplier matches rates-annual.json standard_multiplier_default"
        )
        check(
            sf.get("enhanced_multiplier") == fers_rates.get("enhanced_multiplier"),
            "FERS-COMP: enhanced_multiplier matches rates-annual.json enhanced_multiplier"
        )
        check(
            sc.get("fers_multiplier_first_20") == fers_rates.get("sc_multiplier_first_20"),
            "FERS-COMP: SC first 20 multiplier matches rates-annual.json sc_multiplier_first_20"
        )
        check(
            sc.get("fers_multiplier_beyond_20") == fers_rates.get("sc_multiplier_beyond_20"),
            "FERS-COMP: SC beyond 20 multiplier matches rates-annual.json sc_multiplier_beyond_20"
        )
    else:
        print("  WARN: rates-annual.json not found, skipping cross-file checks")

    # --- No PII ---
    raw = json.dumps(data)
    check("SSN" not in raw and "social security number" not in raw.lower(), "FERS-COMP: No PII detected")

    # --- No consumer-specific references ---
    check(
        "meridian" not in raw.lower() and "engine" not in raw.lower(),
        "FERS-COMP: No consumer-specific references (Meridian/engine)"
    )


def validate_manifest_entries():
    global passed, failed
    print()
    print("=" * 60)
    print("Validating: Manifest entries for new files")
    print("=" * 60)

    check(os.path.isfile(MANIFEST_FILE), "Manifest file exists")
    if not os.path.isfile(MANIFEST_FILE):
        return

    manifest = json.load(open(MANIFEST_FILE))
    files = manifest.get("files", {})

    # LEO premium pay manifest entry
    check("leo_premium_pay" in files, "Manifest: leo_premium_pay entry present")
    leo_entry = files.get("leo_premium_pay", {})
    check(
        leo_entry.get("url") == "federal/leo-premium-pay.json",
        f"Manifest: leo_premium_pay url correct (got {leo_entry.get('url')})"
    )
    check("description" in leo_entry, "Manifest: leo_premium_pay has description")
    check("version" in leo_entry, "Manifest: leo_premium_pay has version")

    # Verify the file URL actually exists
    leo_path = os.path.join(REPO_ROOT, leo_entry.get("url", ""))
    check(os.path.isfile(leo_path), "Manifest: leo_premium_pay url points to existing file")

    # FERS computation rules manifest entry
    check("fers_computation_rules" in files, "Manifest: fers_computation_rules entry present")
    fers_entry = files.get("fers_computation_rules", {})
    check(
        fers_entry.get("url") == "federal/fers-computation-rules.json",
        f"Manifest: fers_computation_rules url correct (got {fers_entry.get('url')})"
    )
    check("description" in fers_entry, "Manifest: fers_computation_rules has description")
    check("version" in fers_entry, "Manifest: fers_computation_rules has version")

    # Verify the file URL actually exists
    fers_path = os.path.join(REPO_ROOT, fers_entry.get("url", ""))
    check(os.path.isfile(fers_path), "Manifest: fers_computation_rules url points to existing file")


if __name__ == "__main__":
    validate_leo_premium_pay()
    validate_fers_computation_rules()
    validate_manifest_entries()

    print()
    print("=" * 60)
    print(f"Results: {passed}/{passed + failed} passed")
    if errors:
        print(f"\n{len(errors)} FAILURES:")
        for e in errors:
            print(f"  - {e}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
