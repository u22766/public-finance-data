#!/usr/bin/env python3
"""
public-finance-data validation suite
Runs automatically via GitHub Actions on every push.
Can also be run locally: python tests/validate.py

Six validation layers:
  1. JSON syntax — all .json files parse without error
  2. Manifest consistency — every manifest URL resolves to an existing file
  3. Schema integrity — version fields present and well-formed
  4. Data integrity — critical values exist and have correct types
  5. Cross-file referential integrity — plan IDs, combinations, hire date mappings
  6. Consumer overlay compatibility — GitHub keys map to expected app key paths
"""

import json
import os
import sys
import re
from pathlib import Path

# ── Test framework ──

class ValidationSuite:
    def __init__(self, repo_root):
        self.root = Path(repo_root)
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.data = {}  # cached loaded files

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print(f"  PASS: {label}")
        else:
            self.failed += 1
            msg = f"{label}: {detail}" if detail else label
            self.errors.append(msg)
            print(f"  FAIL: {msg}")

    def load_json(self, rel_path):
        """Load and cache a JSON file by relative path."""
        if rel_path not in self.data:
            full = self.root / rel_path
            if full.exists():
                with open(full) as f:
                    self.data[rel_path] = json.load(f)
            else:
                self.data[rel_path] = None
        return self.data[rel_path]

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"TOTAL: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailures:")
            for e in self.errors:
                print(f"  - {e}")
        else:
            print("ALL CHECKS PASSED")
        print(f"{'=' * 60}")
        return self.failed == 0


# ── Layer 1: JSON Syntax ──

def test_json_syntax(s):
    print("\n--- Layer 1: JSON Syntax ---")
    json_files = sorted(s.root.rglob("*.json"))
    json_files = [f for f in json_files if ".git" not in str(f)]
    s.check("Found JSON files", len(json_files) > 0, f"found {len(json_files)}")
    for f in json_files:
        rel = f.relative_to(s.root)
        try:
            with open(f) as fh:
                json.load(fh)
            s.check(f"{rel}", True)
        except json.JSONDecodeError as e:
            s.check(f"{rel}", False, str(e))


# ── Layer 2: Manifest URL Consistency ──

def test_manifest_consistency(s):
    print("\n--- Layer 2: Manifest URL Consistency ---")
    manifest = s.load_json("manifest.json")
    s.check("manifest.json loads", manifest is not None)
    if not manifest:
        return

    files = manifest.get("files", {})
    s.check("Manifest has file entries", len(files) > 0, f"found {len(files)}")

    for key, entry in files.items():
        url = entry.get("url", "")
        s.check(f"{key} -> {url}", (s.root / url).is_file(),
                f"file not found: {url}")


# ── Layer 3: Schema Integrity ──

def test_schema_integrity(s):
    print("\n--- Layer 3: Schema Integrity ---")
    manifest = s.load_json("manifest.json")
    if not manifest:
        s.check("manifest.json available", False)
        return

    sv = manifest.get("schema_version")
    smc = manifest.get("schema_min_compatible")
    s.check("schema_version present", sv is not None)
    s.check("schema_min_compatible present", smc is not None)
    s.check("schema_version is string", isinstance(sv, str))
    s.check("schema_min_compatible is string", isinstance(smc, str))

    # Validate version format (digits and dots)
    ver_pattern = re.compile(r"^\d+(\.\d+)*$")
    if sv:
        s.check(f"schema_version format valid ({sv})", bool(ver_pattern.match(sv)))
    if smc:
        s.check(f"schema_min_compatible format valid ({smc})", bool(ver_pattern.match(smc)))

    # min_compatible <= schema_version
    if sv and smc:
        sv_parts = [int(x) for x in sv.split(".")]
        smc_parts = [int(x) for x in smc.split(".")]
        s.check("min_compatible <= schema_version", smc_parts <= sv_parts,
                f"{smc} > {sv}")

    # Every file entry has version and url
    for key, entry in manifest.get("files", {}).items():
        s.check(f"{key} has version", "version" in entry)
        s.check(f"{key} has url", "url" in entry)

    # last_updated present
    s.check("last_updated present", "last_updated" in manifest)


# ── Layer 4: Data Integrity ──

def test_data_integrity(s):
    print("\n--- Layer 4: Data Integrity ---")

    # rates-annual: required sections
    rates = s.load_json("federal/rates-annual.json")
    if rates:
        required_sections = ["tsp", "pay", "fers", "irmaa", "ira",
                             "social_security", "tax", "planning_assumption_defaults"]
        for sec in required_sections:
            s.check(f"rates-annual has '{sec}'", sec in rates)

        # Spot checks — types and ranges
        tsp = rates.get("tsp", {})
        s.check("tsp.regular_limit is int > 0",
                isinstance(tsp.get("regular_limit"), (int, float)) and tsp.get("regular_limit", 0) > 0)

        pay = rates.get("pay", {})
        s.check("pay.pay_cap is int > 100000",
                isinstance(pay.get("pay_cap"), (int, float)) and pay.get("pay_cap", 0) > 100000)

        fers = rates.get("fers", {})
        s.check("fers.standard_multiplier_default is decimal",
                isinstance(fers.get("standard_multiplier_default"), (int, float))
                and 0 < fers.get("standard_multiplier_default", 0) < 1)

        irmaa = rates.get("irmaa", {})
        mfj = irmaa.get("married_filing_jointly", [])
        s.check("irmaa MFJ has >= 5 tiers", isinstance(mfj, list) and len(mfj) >= 5)
        if mfj and len(mfj) >= 5:
            # Tiers should be ascending
            maxes = [t.get("income_max", 0) for t in mfj[:5] if "income_max" in t]
            s.check("irmaa MFJ tiers ascending", maxes == sorted(maxes) and len(maxes) == 5)

        ss = rates.get("social_security", {})
        bp = ss.get("bend_points", {})
        s.check("SS bend points present", "first_bend" in bp and "second_bend" in bp)
        if "first_bend" in bp and "second_bend" in bp:
            s.check("SS first_bend < second_bend", bp["first_bend"] < bp["second_bend"])

        pad = rates.get("planning_assumption_defaults", {})
        for pk in ["fers_cola_default", "ss_cola_default", "va_cola_default", "inflation_rate_default"]:
            val = pad.get(pk)
            s.check(f"planning_defaults.{pk} is decimal 0-1",
                    isinstance(val, (int, float)) and 0 <= val <= 1,
                    f"got {val}")
    else:
        s.check("rates-annual.json loads", False)

    # VA compensation
    va = s.load_json("federal/veterans-affairs/compensation.json")
    if va:
        s.check("Has 'compensation' section", "compensation" in va)
        comp = va.get("compensation", {})
        rbr = comp.get("rates_by_rating", {})
        s.check("Has rates_by_rating", len(rbr) > 0)
        # Must have ratings 10-100 in steps of 10
        expected_ratings = [str(r) for r in range(10, 110, 10)]
        for rating in expected_ratings:
            s.check(f"Rating {rating}% exists", rating in rbr)

        # 100% entry should have all dependent fields
        r100 = rbr.get("100", {})
        for field in ["base_rate", "spouse_addition", "first_child_with_spouse",
                      "first_child_no_spouse", "additional_child_under_18", "additional_child_school"]:
            s.check(f"100% has {field}", field in r100)

        # DIC
        s.check("Has 'dic' section", "dic" in va)
        dic = va.get("dic", {})
        for dk in ["base_rate_monthly", "eight_year_provision_monthly", "per_child_under_18"]:
            s.check(f"dic.{dk} present", dk in dic)
    else:
        s.check("compensation.json loads", False)

    # VGLI
    vgli = s.load_json("federal/veterans-affairs/vgli.json")
    if vgli:
        prem = vgli.get("premium_per_10k_monthly", {})
        expected_bands = ["under_30", "30_34", "35_39", "40_44", "45_49",
                          "50_54", "55_59", "60_64", "65_69", "70_74", "75_79", "80_plus"]
        for band in expected_bands:
            s.check(f"VGLI band '{band}' present",
                    band in prem and isinstance(prem.get(band), (int, float)))
    else:
        s.check("vgli.json loads", False)

    # Static refs
    refs = s.load_json("reference/static-refs.json")
    if refs:
        s.check("Has social_security_fra", "social_security_fra" in refs)
        s.check("Has rmd_uniform_lifetime_table", "rmd_uniform_lifetime_table" in refs)
        s.check("Has opm_locality_codes", "opm_locality_codes" in refs)
    else:
        s.check("static-refs.json loads", False)


# ── Layer 5: Cross-File Referential Integrity ──

def test_referential_integrity(s):
    print("\n--- Layer 5: Cross-File Referential Integrity ---")

    vrs = s.load_json("states/virginia/vrs-plans.json")
    erfc = s.load_json("states/virginia/fairfax-county/erfc-plans.json")
    combos = s.load_json("states/virginia/fairfax-county/plan-combinations.json")
    acers = s.load_json("states/virginia/arlington-county/acers-plans.json")

    # Collect all plan IDs
    all_plan_ids = set()
    if vrs:
        vrs_plans = vrs.get("plans", {})
        s.check("VRS has plans", len(vrs_plans) > 0)
        all_plan_ids.update(vrs_plans.keys())
        s.check("VRS has hireDateMapping", "hireDateMapping" in vrs)

        # Each plan has required fields
        for pid, plan in vrs_plans.items():
            # Hybrid plans use dbComponent/dcComponent instead of formula
            has_benefit_structure = "formula" in plan or "dbComponent" in plan
            s.check(f"VRS {pid} has formula or dbComponent", has_benefit_structure)
            s.check(f"VRS {pid} has vesting", "vesting" in plan)
    else:
        s.check("vrs-plans.json loads", False)

    if erfc:
        erfc_plans = erfc.get("plans", {})
        s.check("ERFC has plans", len(erfc_plans) > 0)
        all_plan_ids.update(erfc_plans.keys())
        s.check("ERFC has hireDateMapping", "hireDateMapping" in erfc)
        s.check("ERFC has jurisdiction", "jurisdiction" in erfc)

        for pid, plan in erfc_plans.items():
            s.check(f"ERFC {pid} has formula", "formula" in plan)
    else:
        s.check("erfc-plans.json loads", False)

    if acers:
        acers_plans = acers.get("plans", {})
        s.check("ACERS has plans", len(acers_plans) > 0)
        all_plan_ids.update(acers_plans.keys())
        s.check("ACERS has hireDateMapping", "hireDateMapping" in acers)
        s.check("ACERS has jurisdiction", "jurisdiction" in acers)
        s.check("ACERS scope is county", acers.get("scope") == "county")

        for pid, plan in acers_plans.items():
            has_formula_or_input = "formula" in plan or plan.get("inputMode") == "estimated_benefit"
            s.check(f"ACERS {pid} has formula or inputMode", has_formula_or_input)
            if "vesting" in plan:
                s.check(f"ACERS {pid} vesting has years", "years" in plan["vesting"])
            if "contributions" in plan and plan["contributions"].get("employee") is not None:
                s.check(f"ACERS {pid} employee contribution is numeric",
                        isinstance(plan["contributions"]["employee"], (int, float)))
            if "survivorOptions" in plan:
                s.check(f"ACERS {pid} has survivor options",
                        len(plan["survivorOptions"]) > 0)
    else:
        s.check("acers-plans.json loads", False)

    # Plan combinations should reference valid plan IDs
    if combos:
        pc = combos.get("planCombinations", {})
        s.check("Has planCombinations", len(pc) > 0)

        if isinstance(pc, dict):
            for combo_key, combo_val in pc.items():
                if isinstance(combo_val, dict):
                    primary = combo_val.get("primary")
                    supplemental = combo_val.get("supplemental")
                    if primary:
                        s.check(f"Combo '{combo_key}' primary '{primary}' exists in plans",
                                primary in all_plan_ids, f"not found in {sorted(all_plan_ids)}")
                    if supplemental:
                        s.check(f"Combo '{combo_key}' supplemental '{supplemental}' exists in plans",
                                supplemental in all_plan_ids, f"not found in {sorted(all_plan_ids)}")
    else:
        s.check("plan-combinations.json loads", False)

    # other-db-template should exist
    tmpl = s.load_json("reference/other-db-template.json")
    s.check("other-db-template.json loads", tmpl is not None)

    # state-benefits
    sb = s.load_json("states/state-benefits.json")
    s.check("state-benefits.json loads", sb is not None)


# ── Layer 6: Consumer Overlay Compatibility ──

def test_overlay_compatibility(s):
    """Verifies that every key path the Meridian app's applyFetchedRates()
    expects actually exists in the GitHub data files."""
    print("\n--- Layer 6: Consumer Overlay Compatibility ---")

    rates = s.load_json("federal/rates-annual.json")
    va = s.load_json("federal/veterans-affairs/compensation.json")
    vgli = s.load_json("federal/veterans-affairs/vgli.json")

    if not rates:
        s.check("rates-annual.json available", False)
        return

    # rates-annual expected paths (from applyFetchedRates)
    overlay_paths = [
        ("tsp.regular_limit", rates.get("tsp", {}).get("regular_limit")),
        ("tsp.catchup_age_50_59", rates.get("tsp", {}).get("catchup_age_50_59")),
        ("tsp.catchup_age_60_63", rates.get("tsp", {}).get("catchup_age_60_63")),
        ("tsp.catchup_income_threshold", rates.get("tsp", {}).get("catchup_income_threshold")),
        ("pay.pay_cap", rates.get("pay", {}).get("pay_cap")),
        ("pay.hourly_divisor", rates.get("pay", {}).get("hourly_divisor")),
        ("pay.sick_leave_hours_per_month", rates.get("pay", {}).get("sick_leave_hours_per_month")),
        ("pay.sick_leave_per_pay_period", rates.get("pay", {}).get("sick_leave_per_pay_period")),
        ("fers.standard_multiplier_default", rates.get("fers", {}).get("standard_multiplier_default")),
        ("fers.enhanced_multiplier", rates.get("fers", {}).get("enhanced_multiplier")),
        ("fers.sc_multiplier_first_20", rates.get("fers", {}).get("sc_multiplier_first_20")),
        ("fers.sc_multiplier_beyond_20", rates.get("fers", {}).get("sc_multiplier_beyond_20")),
        ("fers.survivor_full_pct", rates.get("fers", {}).get("survivor_full_pct")),
        ("fers.survivor_partial_pct", rates.get("fers", {}).get("survivor_partial_pct")),
        ("fers.survivor_full_cost", rates.get("fers", {}).get("survivor_full_cost")),
        ("fers.survivor_partial_cost", rates.get("fers", {}).get("survivor_partial_cost")),
        ("ira.contribution_limit", rates.get("ira", {}).get("contribution_limit")),
        ("ira.catchup_age_50_plus", rates.get("ira", {}).get("catchup_age_50_plus")),
        ("ira.roth_phase_out_mfj_start", rates.get("ira", {}).get("roth_phase_out_mfj_start")),
        ("ira.roth_phase_out_mfj_end", rates.get("ira", {}).get("roth_phase_out_mfj_end")),
        ("social_security.bend_points.first_bend",
         rates.get("social_security", {}).get("bend_points", {}).get("first_bend")),
        ("social_security.bend_points.second_bend",
         rates.get("social_security", {}).get("bend_points", {}).get("second_bend")),
        ("tax.standard_deduction_single", rates.get("tax", {}).get("standard_deduction_single")),
        ("tax.standard_deduction_mfj", rates.get("tax", {}).get("standard_deduction_mfj")),
        ("planning_assumption_defaults.fers_cola_default",
         rates.get("planning_assumption_defaults", {}).get("fers_cola_default")),
        ("planning_assumption_defaults.ss_cola_default",
         rates.get("planning_assumption_defaults", {}).get("ss_cola_default")),
        ("planning_assumption_defaults.va_cola_default",
         rates.get("planning_assumption_defaults", {}).get("va_cola_default")),
        ("planning_assumption_defaults.inflation_rate_default",
         rates.get("planning_assumption_defaults", {}).get("inflation_rate_default")),
    ]

    # IRMAA tiers (array access)
    mfj = rates.get("irmaa", {}).get("married_filing_jointly", [])
    for i in range(5):
        val = mfj[i].get("income_max") if i < len(mfj) else None
        overlay_paths.append((f"irmaa.married_filing_jointly[{i}].income_max", val))

    for path, val in overlay_paths:
        s.check(f"Overlay path: {path}",
                val is not None and isinstance(val, (int, float)),
                f"got {val} ({type(val).__name__})" if val is not None else "key missing")

    # VA compensation overlay paths
    if va:
        dic = va.get("dic", {})
        dic_paths = [
            ("dic.base_rate_monthly", dic.get("base_rate_monthly")),
            ("dic.eight_year_provision_monthly", dic.get("eight_year_provision_monthly")),
            ("dic.transitional_benefit_monthly", dic.get("transitional_benefit_monthly")),
            ("dic.transitional_benefit_duration_months", dic.get("transitional_benefit_duration_months")),
            ("dic.per_child_under_18", dic.get("per_child_under_18")),
        ]
        for path, val in dic_paths:
            s.check(f"Overlay path: {path}",
                    val is not None and isinstance(val, (int, float)),
                    f"got {val}" if val is not None else "key missing")

        rbr = va.get("compensation", {}).get("rates_by_rating", {})
        s.check("Overlay: compensation.rates_by_rating accessible", len(rbr) > 0)
        # Check that rating entries have the keys the overlay maps
        r100 = rbr.get("100", {})
        for field in ["base_rate", "spouse_addition", "first_child_with_spouse",
                      "first_child_no_spouse", "additional_child_under_18", "additional_child_school"]:
            s.check(f"Overlay: 100%.{field}", field in r100 and isinstance(r100[field], (int, float)))

    # VGLI overlay path
    if vgli:
        prem = vgli.get("premium_per_10k_monthly")
        s.check("Overlay path: premium_per_10k_monthly",
                isinstance(prem, dict) and len(prem) >= 12)


# ── Main ──

def main():
    # Determine repo root — script lives in tests/
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    # Allow override via command line
    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])

    print(f"Validating: {repo_root}")
    print(f"{'=' * 60}")

    s = ValidationSuite(repo_root)

    test_json_syntax(s)
    test_manifest_consistency(s)
    test_schema_integrity(s)
    test_data_integrity(s)
    test_referential_integrity(s)
    test_overlay_compatibility(s)

    success = s.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
