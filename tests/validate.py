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
    fcers = s.load_json("states/virginia/fairfax-county/fcers-plans.json")

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

    # FCERS (Fairfax County Employees' Retirement System) — 5 plan tiers
    if fcers:
        fcers_plans = fcers.get("plans", {})
        s.check("FCERS has plans", len(fcers_plans) > 0)
        s.check("FCERS has 5 plan tiers", len(fcers_plans) == 5)
        all_plan_ids.update(fcers_plans.keys())
        s.check("FCERS has hireDateMapping", "hireDateMapping" in fcers)
        s.check("FCERS has 5 hireDateMapping entries", len(fcers.get("hireDateMapping", [])) == 5)
        s.check("FCERS has jurisdiction", "jurisdiction" in fcers)
        s.check("FCERS scope is county", fcers.get("scope") == "county")
        s.check("FCERS jurisdiction state is VA", fcers.get("jurisdiction", {}).get("state") == "VA")
        s.check("FCERS employer contains Fairfax",
                "Fairfax" in fcers.get("employer", ""))

        expected_plans = ["fcers_plan_a", "fcers_plan_b", "fcers_plan_c", "fcers_plan_d", "fcers_plan_e"]
        for ep in expected_plans:
            s.check(f"FCERS {ep} exists", ep in fcers_plans)

        for pid, plan in fcers_plans.items():
            s.check(f"FCERS {pid} has formula", "formula" in plan)
            s.check(f"FCERS {pid} has baseBenefit", "baseBenefit" in plan.get("formula", {}))
            bb = plan.get("formula", {}).get("baseBenefit", {})
            s.check(f"FCERS {pid} baseBenefit has multiplier", "multiplier" in bb)
            s.check(f"FCERS {pid} multiplier > 0",
                    isinstance(bb.get("multiplier"), (int, float)) and bb.get("multiplier") > 0)
            s.check(f"FCERS {pid} has eligibility", "eligibility" in plan)
            s.check(f"FCERS {pid} has normalRetirement",
                    "normalRetirement" in plan.get("eligibility", {}))
            s.check(f"FCERS {pid} has contributions", "contributions" in plan)
            if "vesting" in plan:
                s.check(f"FCERS {pid} vesting has years", "years" in plan["vesting"])
                s.check(f"FCERS {pid} vesting is 5 years", plan["vesting"]["years"] == 5)
            if "survivorOptions" in plan:
                s.check(f"FCERS {pid} has survivor options",
                        len(plan["survivorOptions"]) > 0)
            if "drop" in plan:
                s.check(f"FCERS {pid} DROP available", plan["drop"].get("available") == True)
                s.check(f"FCERS {pid} DROP max 3 years", plan["drop"].get("maxYears") == 3)
            if "disability" in plan:
                s.check(f"FCERS {pid} has disability provisions", "nonJobRelated" in plan["disability"])

        # Plan A/C should be 1.8%, B/D/E should be 2.0%
        for pid in ["fcers_plan_a", "fcers_plan_c"]:
            if pid in fcers_plans:
                m = fcers_plans[pid]["formula"]["baseBenefit"]["multiplier"]
                s.check(f"FCERS {pid} multiplier is 1.8%", abs(m - 0.018) < 0.001)
        for pid in ["fcers_plan_b", "fcers_plan_d", "fcers_plan_e"]:
            if pid in fcers_plans:
                m = fcers_plans[pid]["formula"]["baseBenefit"]["multiplier"]
                s.check(f"FCERS {pid} multiplier is 2.0%", abs(m - 0.02) < 0.001)

        # Plan E should NOT have Pre-SS benefit
        if "fcers_plan_e" in fcers_plans:
            s.check("FCERS Plan E has no Pre-SS benefit",
                    fcers_plans["fcers_plan_e"]["formula"].get("preSocialSecurityBenefit") is None)

        # Plans A/B should have Pre-SS benefit
        for pid in ["fcers_plan_a", "fcers_plan_b"]:
            if pid in fcers_plans:
                preSS = fcers_plans[pid]["formula"].get("preSocialSecurityBenefit")
                s.check(f"FCERS {pid} has Pre-SS benefit", preSS is not None and preSS is not False)

        # Plan A/B normal retirement: age 50 + rule of 80; C/D/E: age 55 + rule of 85
        for pid in ["fcers_plan_a", "fcers_plan_b"]:
            if pid in fcers_plans:
                conds = fcers_plans[pid]["eligibility"]["normalRetirement"]["conditions"]
                ages = [c.get("minAge") for c in conds if c.get("minAge")]
                s.check(f"FCERS {pid} normal min age 50", 50 in ages)
        for pid in ["fcers_plan_c", "fcers_plan_d", "fcers_plan_e"]:
            if pid in fcers_plans:
                conds = fcers_plans[pid]["eligibility"]["normalRetirement"]["conditions"]
                ages = [c.get("minAge") for c in conds if c.get("minAge")]
                s.check(f"FCERS {pid} normal min age 55", 55 in ages)
    else:
        s.check("fcers-plans.json loads", False)

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


def test_pors_plans(s):
    """Validate Fairfax County Police Officers Retirement System (PORS) data."""
    path = s.root / "states" / "virginia" / "fairfax-county" / "pors-plans.json"
    s.check("PORS file exists", path.exists())
    if not path.exists():
        return

    import json
    data = json.loads(path.read_text())

    # Top-level structure
    s.check("PORS has version", "version" in data)
    s.check("PORS has effective_date", "effective_date" in data)
    s.check("PORS has employer", "employer" in data)
    s.check("PORS has jurisdiction", "jurisdiction" in data)
    s.check("PORS jurisdiction is VA", data.get("jurisdiction", {}).get("state") == "VA")
    s.check("PORS jurisdiction is Fairfax County", "Fairfax" in data.get("jurisdiction", {}).get("county", ""))
    s.check("PORS has hireDateMapping", "hireDateMapping" in data and len(data["hireDateMapping"]) == 3)
    s.check("PORS has plans dict", "plans" in data and isinstance(data["plans"], dict))
    s.check("PORS has 3 plans", len(data.get("plans", {})) == 3)

    # Plan IDs match
    expected_plans = {"pors_plan_a", "pors_plan_b", "pors_plan_c"}
    actual_plans = set(data.get("plans", {}).keys())
    s.check("PORS plan IDs correct", actual_plans == expected_plans,
            f"expected {expected_plans}, got {actual_plans}")

    # Hire date mapping IDs match plans
    mapping_ids = {m["planId"] for m in data.get("hireDateMapping", [])}
    s.check("PORS hireDateMapping IDs match plans", mapping_ids == expected_plans)

    # Validate each plan
    for pid, plan in data.get("plans", {}).items():
        s.check(f"PORS {pid} has planName", "planName" in plan)
        s.check(f"PORS {pid} type is defined_benefit", plan.get("type") == "defined_benefit")
        s.check(f"PORS {pid} has benefitFormula", "benefitFormula" in plan)

        bf = plan.get("benefitFormula", {})
        s.check(f"PORS {pid} multiplier is 2.8", abs(bf.get("multiplier", 0) - 2.8) < 0.001)
        s.check(f"PORS {pid} has formula string", "formula" in bf)

        # FAS
        fas = plan.get("finalAverageSalary", {})
        s.check(f"PORS {pid} FAS periods is 78", fas.get("periods") == 78)
        s.check(f"PORS {pid} FAS is 36 months", fas.get("periodMonths") == 36)

        # Normal retirement
        nr = plan.get("normalRetirement", {})
        s.check(f"PORS {pid} normal ret age 55", nr.get("ageRequirement") == 55)
        s.check(f"PORS {pid} normal ret service 25", nr.get("serviceRequirement") == 25)

        # Early retirement
        er = plan.get("earlyRetirement", {})
        s.check(f"PORS {pid} early ret service 20", er.get("serviceRequirement") == 20)

        # Deferred vested
        dv = plan.get("deferredVested", {})
        s.check(f"PORS {pid} deferred vesting 5 years", dv.get("vestingYears") == 5)
        s.check(f"PORS {pid} deferred payable at 55", dv.get("payableAge") == 55)

        # Vesting
        s.check(f"PORS {pid} vesting is 5 years", plan.get("vestingYears") == 5)

        # Employee contribution
        ec = plan.get("employeeContribution", {})
        s.check(f"PORS {pid} contribution is 8.65%", abs(ec.get("rate", 0) - 8.65) < 0.01)
        s.check(f"PORS {pid} no Social Security", ec.get("socialSecurityParticipation") == False)

        # COLA
        cola = plan.get("cola", {})
        s.check(f"PORS {pid} COLA type is automatic_cpi", cola.get("type") == "automatic_cpi")
        s.check(f"PORS {pid} COLA cap is 4.0%", cola.get("cap") == 4.0)

        # DROP
        drop = plan.get("drop", {})
        s.check(f"PORS {pid} DROP available", drop.get("available") == True)
        s.check(f"PORS {pid} DROP max 3 years", drop.get("maxYears") == 3)
        s.check(f"PORS {pid} DROP interest 5%", drop.get("interestRate") == 5.0)

        # Survivor options
        so = plan.get("survivorOptions", {})
        s.check(f"PORS {pid} has J&LS options", len(so.get("jointAndLastSurvivor", [])) == 4)

        # Disability
        dis = plan.get("disability", {})
        s.check(f"PORS {pid} has nonServiceConnected disability", "nonServiceConnected" in dis)
        s.check(f"PORS {pid} has serviceConnected disability", "serviceConnected" in dis)
        sc = dis.get("serviceConnected", {})
        s.check(f"PORS {pid} service-connected is 66.67%",
                "66" in sc.get("formula", "") or "66.67" in sc.get("formula", ""))

        # Sick leave
        sl = plan.get("sickLeaveCredit", {})
        s.check(f"PORS {pid} sick leave available", sl.get("available") == True)

        # Membership stats
        ms = plan.get("membershipStats", {})
        s.check(f"PORS {pid} has membership stats", ms.get("activeMembers", 0) > 0)

    # Plan-specific checks
    # Plans A & B have 1.03 escalator; Plan C does not
    plan_a = data["plans"]["pors_plan_a"]
    plan_b = data["plans"]["pors_plan_b"]
    plan_c = data["plans"]["pors_plan_c"]

    s.check("PORS Plan A has 1.03 escalator",
            plan_a["benefitFormula"].get("escalator") == 1.03)
    s.check("PORS Plan B has 1.03 escalator",
            plan_b["benefitFormula"].get("escalator") == 1.03)
    s.check("PORS Plan C has NO escalator",
            plan_c["benefitFormula"].get("escalator") is None)

    # Plan statuses
    s.check("PORS Plan A is closed", plan_a.get("status") == "closed")
    s.check("PORS Plan B is closed", plan_b.get("status") == "closed")
    s.check("PORS Plan C is open", plan_c.get("status") == "open")

    # Plan B and C should have sick leave max hours
    s.check("PORS Plan B has sick leave max 2080",
            plan_b.get("sickLeaveCredit", {}).get("maxHours") == 2080)
    s.check("PORS Plan C has sick leave max 2080",
            plan_c.get("sickLeaveCredit", {}).get("maxHours") == 2080)


def test_urs_plans(s):
    """Validate Fairfax County Uniformed Retirement System (URS) data."""
    path = s.root / "states" / "virginia" / "fairfax-county" / "urs-plans.json"
    s.check("URS file exists", path.exists())
    if not path.exists():
        return

    import json
    data = json.loads(path.read_text())

    # Top-level structure
    s.check("URS has version", "version" in data)
    s.check("URS has effective_date", "effective_date" in data)
    s.check("URS has employer", "employer" in data)
    s.check("URS has jurisdiction", "jurisdiction" in data)
    s.check("URS jurisdiction is VA", data.get("jurisdiction", {}).get("state") == "VA")
    s.check("URS jurisdiction is Fairfax County", "Fairfax" in data.get("jurisdiction", {}).get("county", ""))
    s.check("URS has hireDateMapping", "hireDateMapping" in data and len(data["hireDateMapping"]) == 6)
    s.check("URS has plans dict", "plans" in data and isinstance(data["plans"], dict))
    s.check("URS has 4 modeled plans", len(data.get("plans", {})) == 4)

    # Plan IDs match
    expected_plans = {"urs_plan_b", "urs_plan_d", "urs_plan_e", "urs_plan_f"}
    actual_plans = set(data.get("plans", {}).keys())
    s.check("URS plan IDs correct", actual_plans == expected_plans,
            f"expected {expected_plans}, got {actual_plans}")

    # Validate each plan
    for pid, plan in data.get("plans", {}).items():
        s.check(f"URS {pid} has planName", "planName" in plan)
        s.check(f"URS {pid} type is defined_benefit", plan.get("type") == "defined_benefit")
        s.check(f"URS {pid} has benefitFormula", "benefitFormula" in plan)

        bf = plan.get("benefitFormula", {})
        s.check(f"URS {pid} has multiplier > 0", bf.get("multiplier", 0) > 0)
        s.check(f"URS {pid} has formula string", "formula" in bf)

        # FAS
        fas = plan.get("finalAverageSalary", {})
        s.check(f"URS {pid} FAS periods is 78", fas.get("periods") == 78)
        s.check(f"URS {pid} FAS is 36 months", fas.get("periodMonths") == 36)

        # Normal retirement
        nr = plan.get("normalRetirement", {})
        s.check(f"URS {pid} normal ret age 55", nr.get("ageRequirement") == 55)
        s.check(f"URS {pid} normal ret age+service 6", nr.get("ageServiceRequirement") == 6)
        s.check(f"URS {pid} normal ret service 25", nr.get("serviceOnlyRequirement") == 25)

        # Early retirement
        er = plan.get("earlyRetirement", {})
        s.check(f"URS {pid} early ret service 20", er.get("serviceRequirement") == 20)

        # Deferred vested
        dv = plan.get("deferredVested", {})
        s.check(f"URS {pid} deferred vesting 5 years", dv.get("vestingYears") == 5)
        s.check(f"URS {pid} deferred payable at 55", dv.get("payableAge") == 55)

        # Vesting
        s.check(f"URS {pid} vesting is 5 years", plan.get("vestingYears") == 5)

        # Employee contribution
        ec = plan.get("employeeContribution", {})
        s.check(f"URS {pid} contribution rate > 0", ec.get("rate", 0) > 0)
        s.check(f"URS {pid} participates in Social Security", ec.get("socialSecurityParticipation") == True)

        # COLA
        cola = plan.get("cola", {})
        s.check(f"URS {pid} COLA type is automatic_cpi", cola.get("type") == "automatic_cpi")
        s.check(f"URS {pid} COLA cap is 4.0%", cola.get("cap") == 4.0)

        # DROP
        drop = plan.get("drop", {})
        s.check(f"URS {pid} DROP available", drop.get("available") == True)
        s.check(f"URS {pid} DROP max 3 years", drop.get("maxYears") == 3)
        s.check(f"URS {pid} DROP interest 5%", drop.get("interestRate") == 5.0)

        # Survivor options
        so = plan.get("survivorOptions", {})
        s.check(f"URS {pid} has J&LS options", len(so.get("jointAndLastSurvivor", [])) == 4)

        # Disability
        dis = plan.get("disability", {})
        s.check(f"URS {pid} has serviceConnected disability", "serviceConnected" in dis)
        s.check(f"URS {pid} has severeServiceConnected disability", "severeServiceConnected" in dis)
        ssc = dis.get("severeServiceConnected", {})
        s.check(f"URS {pid} severe disability is 90%", "90%" in ssc.get("formula", ""))

        # Sick leave
        sl = plan.get("sickLeaveCredit", {})
        s.check(f"URS {pid} sick leave available", sl.get("available") == True)

        # Membership stats
        ms = plan.get("membershipStats", {})
        s.check(f"URS {pid} has membership stats", ms.get("activeMembers", 0) > 0)

    # Plan-specific formula checks
    plan_b = data["plans"]["urs_plan_b"]
    plan_d = data["plans"]["urs_plan_d"]
    plan_e = data["plans"]["urs_plan_e"]
    plan_f = data["plans"]["urs_plan_f"]

    # Plan B: 2.0% multiplier
    s.check("URS Plan B multiplier is 2.0%", abs(plan_b["benefitFormula"]["multiplier"] - 2.0) < 0.001)
    # Plans D, E: 2.5% multiplier
    s.check("URS Plan D multiplier is 2.5%", abs(plan_d["benefitFormula"]["multiplier"] - 2.5) < 0.001)
    s.check("URS Plan E multiplier is 2.5%", abs(plan_e["benefitFormula"]["multiplier"] - 2.5) < 0.001)
    s.check("URS Plan F multiplier is 2.5%", abs(plan_f["benefitFormula"]["multiplier"] - 2.5) < 0.001)

    # Escalator: B, D, E have 1.03; F does not
    s.check("URS Plan B has 1.03 escalator", plan_b["benefitFormula"].get("escalator") == 1.03)
    s.check("URS Plan D has 1.03 escalator", plan_d["benefitFormula"].get("escalator") == 1.03)
    s.check("URS Plan E has 1.03 escalator", plan_e["benefitFormula"].get("escalator") == 1.03)
    s.check("URS Plan F has NO escalator", plan_f["benefitFormula"].get("escalator") is None)

    # Pre-Social Security Benefit: B (0.2%), D & E (0.3%), F (none)
    s.check("URS Plan B Pre-SS multiplier is 0.2%",
            abs(plan_b.get("preSocialSecurityBenefit", {}).get("multiplier", 0) - 0.2) < 0.001)
    s.check("URS Plan D Pre-SS multiplier is 0.3%",
            abs(plan_d.get("preSocialSecurityBenefit", {}).get("multiplier", 0) - 0.3) < 0.001)
    s.check("URS Plan E Pre-SS multiplier is 0.3%",
            abs(plan_e.get("preSocialSecurityBenefit", {}).get("multiplier", 0) - 0.3) < 0.001)
    s.check("URS Plan F has NO Pre-SS benefit",
            plan_f.get("preSocialSecurityBenefit", {}).get("available") == False)

    # Pre-62 Supplement: B and D yes, E and F no
    s.check("URS Plan B has Pre-62 supplement",
            plan_b.get("pre62Supplement", {}).get("available") == True)
    s.check("URS Plan D has Pre-62 supplement",
            plan_d.get("pre62Supplement", {}).get("available") == True)
    s.check("URS Plan E has NO Pre-62 supplement",
            plan_e.get("pre62Supplement", {}).get("available") == False)
    s.check("URS Plan F has NO Pre-62 supplement",
            plan_f.get("pre62Supplement", {}).get("available") == False)

    # Plan statuses
    s.check("URS Plan B is closed", plan_b.get("status") == "closed")
    s.check("URS Plan D is closed", plan_d.get("status") == "closed")
    s.check("URS Plan E is closed", plan_e.get("status") == "closed")
    s.check("URS Plan F is open", plan_f.get("status") == "open")

    # Sick leave max for E and F
    s.check("URS Plan E has sick leave max 2080",
            plan_e.get("sickLeaveCredit", {}).get("maxHours") == 2080)
    s.check("URS Plan F has sick leave max 2080",
            plan_f.get("sickLeaveCredit", {}).get("maxHours") == 2080)

    # Cross-system comparison: PORS vs URS vs FCERS are different systems
    pors_path = s.root / "states" / "virginia" / "fairfax-county" / "pors-plans.json"
    if pors_path.exists():
        pors = json.loads(pors_path.read_text())
        s.check("PORS and URS are distinct systems",
                pors.get("employer") != data.get("employer"))
        # PORS does NOT participate in SS; URS does
        pors_ss = pors["plans"]["pors_plan_a"]["employeeContribution"].get("socialSecurityParticipation")
        urs_ss = plan_b["employeeContribution"].get("socialSecurityParticipation")
        s.check("PORS no SS, URS yes SS", pors_ss == False and urs_ss == True)


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
    test_pors_plans(s)
    test_urs_plans(s)

    success = s.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
