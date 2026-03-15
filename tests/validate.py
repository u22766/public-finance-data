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
            # Hybrid plans use dbComponent/dcComponent or definedBenefit/definedContribution instead of formula
            has_benefit_structure = "formula" in plan or "dbComponent" in plan or "definedBenefit" in plan
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


def test_rrs_plans(s):
    """Validate Richmond Retirement System (RRS) pension data."""
    path = s.root / "states" / "virginia" / "richmond" / "rrs-plans.json"
    s.check("RRS file exists", path.exists())
    if not path.exists():
        return

    data = json.loads(path.read_text())

    # Top-level structure
    s.check("RRS has systemName", data.get("systemName") == "Richmond Retirement System")
    s.check("RRS has systemAbbreviation", data.get("systemAbbreviation") == "RRS")
    s.check("RRS established 1945", data.get("established") == 1945)
    s.check("RRS status is CLOSED", data.get("status") == "CLOSED")
    s.check("RRS closedDate is 2024-01-01", data.get("closedDate") == "2024-01-01")
    s.check("RRS participates in SS", data.get("socialSecurityParticipation") is True)
    s.check("RRS has version", "version" in data)
    s.check("RRS has lastUpdated", "lastUpdated" in data)
    s.check("RRS has sources list", isinstance(data.get("sources"), list) and len(data["sources"]) >= 2)
    s.check("RRS has jurisdiction", "jurisdiction" in data)
    s.check("RRS jurisdiction state is virginia", data.get("jurisdiction", {}).get("state") == "virginia")
    s.check("RRS jurisdiction city is richmond", data.get("jurisdiction", {}).get("city") == "richmond")
    s.check("RRS scope is city", data.get("scope") == "city")

    # Membership stats
    stats = data.get("membershipStats", {})
    s.check("RRS has membershipStats", bool(stats))
    s.check("RRS totalMembers >= 10000", stats.get("totalMembers", 0) >= 10000)
    s.check("RRS activeRetirees >= 4000", stats.get("activeRetirees", 0) >= 4000)

    # Portability agreements
    port = data.get("portabilityAgreements", [])
    s.check("RRS has portability agreements", len(port) >= 5)
    s.check("RRS has VRS portability", "VRS" in port)

    # Hire date mapping
    hdm = data.get("hireDateMapping", [])
    s.check("RRS has 8 hireDateMapping entries", len(hdm) == 8)
    emp_types = {m.get("employeeType") for m in hdm}
    s.check("RRS mapping has general/sworn/executive", {"general", "sworn", "executive"}.issubset(emp_types))

    # Check VRS transition mappings (2024+)
    vrs_mappings = [m for m in hdm if m.get("hireStart") == "2024-01-01"]
    s.check("RRS has VRS transition mappings", len(vrs_mappings) >= 2)
    for vm in vrs_mappings:
        s.check(f"RRS {vm.get('employeeType')} post-2024 has empty planIds",
                vm.get("planIds") == [])

    # Plans structure
    plans = data.get("plans", {})
    s.check("RRS has plans dict", isinstance(plans, dict))
    s.check("RRS has 8 plans", len(plans) == 8)

    expected_plan_ids = {
        "general_db_basic", "general_db_enhanced",
        "sworn_db_basic", "sworn_db_enhanced",
        "general_dc",
        "executive_db_basic", "executive_db_enhanced", "executive_2to1"
    }
    actual_plan_ids = set(plans.keys())
    s.check("RRS plan IDs correct", actual_plan_ids == expected_plan_ids,
            f"expected {expected_plan_ids}, got {actual_plan_ids}")

    # All plans should be CLOSED
    for pid, plan in plans.items():
        s.check(f"RRS {pid} is CLOSED", plan.get("status") == "CLOSED")
        s.check(f"RRS {pid} has planName", "planName" in plan)
        s.check(f"RRS {pid} has planType", "planType" in plan)

    # ── General DB Basic ──
    gdb = plans.get("general_db_basic", {})
    gf = gdb.get("formula", {})
    s.check("RRS general_db_basic multiplier is 1.75%", abs(gf.get("multiplier", 0) - 0.0175) < 0.0001)
    s.check("RRS general_db_basic max years is 35", gf.get("maxYearsOfService") == 35)
    afc = gf.get("averageFinalCompensation", {})
    s.check("RRS general_db_basic AFC 36 months", afc.get("months") == 36)
    s.check("RRS general_db_basic AFC is highest consecutive", afc.get("method") == "highest_consecutive")
    s.check("RRS general_db_basic AFC excludes overtime", "overtime" in afc.get("excludes", []))

    gelig = gdb.get("eligibility", {})
    s.check("RRS general_db_basic normal ret age 65", gelig.get("normalRetirement", {}).get("age") == 65)
    s.check("RRS general_db_basic early ret age 55", gelig.get("earlyRetirement", {}).get("minimumAge") == 55)
    s.check("RRS general_db_basic vesting 5 years", gdb.get("vesting", {}).get("years") == 5)
    s.check("RRS general_db_basic EE contrib 5%", abs(gdb.get("contributions", {}).get("employee", {}).get("rate", 0) - 0.05) < 0.001)

    # Benefit % of AFC checks
    bpct = gdb.get("benefitAsPercentOfAFC", {})
    s.check("RRS general_db_basic 35yr = 61.25%", abs(bpct.get("35_years", 0) - 61.25) < 0.01)
    s.check("RRS general_db_basic 30yr = 52.5%", abs(bpct.get("30_years", 0) - 52.5) < 0.01)
    s.check("RRS general_db_basic 20yr = 35.0%", abs(bpct.get("20_years", 0) - 35.0) < 0.01)

    # Payout options
    opts = gdb.get("benefitPayoutOptions", [])
    s.check("RRS general_db_basic has 4 payout options", len(opts) == 4)
    opt_names = {o.get("name") for o in opts}
    s.check("RRS general_db_basic has Basic Benefit option", "Basic Benefit" in opt_names)
    s.check("RRS general_db_basic has J&LS option", "Joint and Last Survivor" in opt_names)
    jls = [o for o in opts if o.get("name") == "Joint and Last Survivor"]
    if jls:
        s.check("RRS general J&LS has 4 sub-options", len(jls[0].get("subOptions", [])) == 4)

    # Creditable service
    cs = gdb.get("creditableService", [])
    s.check("RRS general_db_basic has creditable service list", len(cs) >= 5)
    s.check("RRS general_db_basic includes sick leave", any("sick" in c for c in cs))

    # ── General DB Enhanced ──
    gde = plans.get("general_db_enhanced", {})
    gef = gde.get("formula", {})
    s.check("RRS general_db_enhanced multiplier is 2.0%", abs(gef.get("multiplier", 0) - 0.02) < 0.0001)
    s.check("RRS general_db_enhanced max years is 35", gef.get("maxYearsOfService") == 35)
    s.check("RRS general_db_enhanced EE contrib 8.57%",
            abs(gde.get("contributions", {}).get("employee", {}).get("rate", 0) - 0.0857) < 0.001)
    s.check("RRS general_db_enhanced min enhanced years 3",
            gde.get("contributions", {}).get("employee", {}).get("minimumEnhancedYears") == 3)

    bpct_e = gde.get("benefitAsPercentOfAFC", {})
    s.check("RRS general_db_enhanced 35yr = 70%", abs(bpct_e.get("35_years", 0) - 70.0) < 0.01)
    s.check("RRS general_db_enhanced 25yr = 50%", abs(bpct_e.get("25_years", 0) - 50.0) < 0.01)

    # ── Sworn DB Basic ──
    sdb = plans.get("sworn_db_basic", {})
    sf = sdb.get("formula", {})
    s.check("RRS sworn_db_basic multiplier is 1.65%", abs(sf.get("multiplier", 0) - 0.0165) < 0.0001)
    s.check("RRS sworn_db_basic max years is 35", sf.get("maxYearsOfService") == 35)

    # Pre-65 supplement
    supp = sf.get("pre65Supplement", {})
    s.check("RRS sworn supplement multiplier is 0.75%", abs(supp.get("multiplier", 0) - 0.0075) < 0.0001)
    s.check("RRS sworn supplement max years 25", supp.get("maxYears") == 25)
    s.check("RRS sworn supplement payable until age 65", supp.get("payableUntil") == "age 65")
    s.check("RRS sworn supplement not for deferred vested", supp.get("deferredVestedEligible") is False)

    selig = sdb.get("eligibility", {})
    s.check("RRS sworn_db_basic normal ret age 60", selig.get("normalRetirement", {}).get("age") == 60)
    s.check("RRS sworn_db_basic unreduced at 25 years",
            "25" in str(selig.get("normalRetirement", {}).get("or", "")))
    s.check("RRS sworn_db_basic early ret age 50", selig.get("earlyRetirement", {}).get("minimumAge") == 50)
    s.check("RRS sworn_db_basic mandatory ret 73", selig.get("mandatoryRetirementAge") == 73)
    s.check("RRS sworn_db_basic EE contrib 5%",
            abs(sdb.get("contributions", {}).get("employee", {}).get("rate", 0) - 0.05) < 0.001)

    # Benefit % with and without supplement
    sbpct = sdb.get("benefitAsPercentOfAFC", {})
    s.check("RRS sworn with supplement 25yr = 60%",
            abs(sbpct.get("withSupplement", {}).get("25_years", 0) - 60.0) < 0.01)
    s.check("RRS sworn after65 25yr = 41.25%",
            abs(sbpct.get("afterAge65", {}).get("25_years", 0) - 41.25) < 0.01)
    s.check("RRS sworn with supplement 35yr = 76.5%",
            abs(sbpct.get("withSupplement", {}).get("35_years", 0) - 76.5) < 0.01)

    # DROP
    drop = sdb.get("drop", {})
    s.check("RRS sworn_db_basic DROP available", drop.get("available") is True)
    s.check("RRS sworn_db_basic DROP max 6 years", drop.get("maxYears") == 6)

    # 5 payout options for sworn (includes Level)
    sworn_opts = sdb.get("benefitPayoutOptions", [])
    s.check("RRS sworn_db_basic has 5 payout options", len(sworn_opts) == 5)
    sworn_opt_names = {o.get("name") for o in sworn_opts}
    s.check("RRS sworn has Level option", "Level" in sworn_opt_names)

    # ── Sworn DB Enhanced ──
    sde = plans.get("sworn_db_enhanced", {})
    sef = sde.get("formula", {})
    s.check("RRS sworn_db_enhanced multiplier is 1.65%", abs(sef.get("multiplier", 0) - 0.0165) < 0.0001)
    s.check("RRS sworn_db_enhanced has pre65 supplement", "pre65Supplement" in sef)
    seelig = sde.get("eligibility", {})
    s.check("RRS sworn_enhanced unreduced at 20 years",
            "20" in str(seelig.get("normalRetirement", {}).get("or", "")))
    s.check("RRS sworn_enhanced EE contrib 8.95%",
            abs(sde.get("contributions", {}).get("employee", {}).get("rate", 0) - 0.0895) < 0.001)
    s.check("RRS sworn_enhanced min enhanced years 3",
            sde.get("contributions", {}).get("employee", {}).get("minimumEnhancedYears") == 3)
    s.check("RRS sworn_enhanced DROP available", sde.get("drop", {}).get("available") is True)

    # ── General DC ──
    dc = plans.get("general_dc", {})
    s.check("RRS DC planType is defined_contribution", dc.get("planType") == "defined_contribution")
    s.check("RRS DC administered by Mission Square", dc.get("administeredBy") == "Mission Square Retirement")
    dc_rates = dc.get("contributions", {}).get("employer", {}).get("rates", [])
    s.check("RRS DC has 4 employer tiers", len(dc_rates) == 4)
    if dc_rates:
        s.check("RRS DC first tier is 5%", abs(dc_rates[0].get("rate", 0) - 0.05) < 0.001)
        s.check("RRS DC last tier is 10%", abs(dc_rates[-1].get("rate", 0) - 0.10) < 0.001)
    s.check("RRS DC vesting 5 years", dc.get("vesting", {}).get("years") == 5)

    # ── Executive plans ──
    exb = plans.get("executive_db_basic", {})
    s.check("RRS executive_db_basic multiplier 1.75%",
            abs(exb.get("formula", {}).get("multiplier", 0) - 0.0175) < 0.0001)
    exe = plans.get("executive_db_enhanced", {})
    s.check("RRS executive_db_enhanced multiplier 2.0%",
            abs(exe.get("formula", {}).get("multiplier", 0) - 0.02) < 0.0001)

    ex21 = plans.get("executive_2to1", {})
    s.check("RRS executive_2to1 has service multiplier", "serviceMultiplier" in ex21)
    s.check("RRS executive_2to1 ratio is 2:1", ex21.get("serviceMultiplier", {}).get("ratio") == "2:1")
    s.check("RRS executive_2to1 max doubled 15 years",
            ex21.get("serviceMultiplier", {}).get("maxDoubledYears") == 15)
    s.check("RRS executive_2to1 min exec years 10",
            ex21.get("serviceMultiplier", {}).get("minimumExecYears") == 10)
    s.check("RRS executive_2to1 additional contrib 3.06%",
            abs(ex21.get("additionalContribution", {}).get("rate", 0) - 0.0306) < 0.001)

    # ── COLA ──
    cola = data.get("cola", {})
    s.check("RRS COLA type is ad_hoc", cola.get("type") == "ad_hoc")

    # ── OPEB ──
    opeb = data.get("opeb", {})
    health = opeb.get("retireeHealth", {})
    s.check("RRS has retiree health info", bool(health))
    ec = health.get("employerContributions", [])
    s.check("RRS health has 4 contribution tiers", len(ec) == 4)
    if ec:
        s.check("RRS health max monthly is $400", ec[-1].get("monthly") == 400)
    s.check("RRS health assessment bonus $25", health.get("healthAssessmentBonus") == 25)

    # ── VRS Transition ──
    vrs = data.get("vrsTransition", {})
    s.check("RRS VRS transition date 2024-01-01", vrs.get("effectiveDate") == "2024-01-01")
    s.check("RRS VRS election deadline 2024-12-31", vrs.get("electionDeadline") == "2024-12-31")

    # ── Cross-system checks ──
    # RRS is distinct from Fairfax County systems
    fcers_path = s.root / "states" / "virginia" / "fairfax-county" / "fcers-plans.json"
    if fcers_path.exists():
        fcers = json.loads(fcers_path.read_text())
        s.check("RRS and FCERS are different systems",
                data.get("systemAbbreviation") != fcers.get("systemAbbreviation", ""))
    # RRS COLA is ad hoc unlike VRS formula-based
    s.check("RRS COLA differs from VRS automatic", cola.get("type") == "ad_hoc")


def test_vrs_consolidated(s):
    """Validate consolidated VRS plan data."""
    path = s.root / "states" / "virginia" / "vrs-plans.json"
    s.check("VRS file exists", path.exists())
    if not path.exists():
        return

    data = json.loads(path.read_text())

    # Top-level
    s.check("VRS systemName", data.get("systemName") == "Virginia Retirement System")
    s.check("VRS abbreviation", data.get("systemAbbreviation") == "VRS")
    s.check("VRS established 1942", data.get("established") == 1942)
    s.check("VRS OPEN", data.get("status") == "OPEN")
    s.check("VRS SS participation", data.get("socialSecurityParticipation") is True)
    s.check("VRS has sources", len(data.get("sources", [])) >= 3)

    # Plans
    plans = data.get("plans", {})
    s.check("VRS has 3 plans", len(plans) == 3)
    s.check("VRS has plan1/plan2/hybrid", {"vrs_plan1", "vrs_plan2", "vrs_hybrid"} == set(plans.keys()))

    # Plan 1
    p1 = plans.get("vrs_plan1", {})
    s.check("VRS P1 multiplier 1.7%", abs(p1.get("formula", {}).get("multiplier", 0) - 0.017) < 0.0001)
    s.check("VRS P1 AFC 36 months", p1.get("formula", {}).get("averageFinalCompensation", {}).get("months") == 36)
    s.check("VRS P1 EE contrib 5%", abs(p1.get("contributions", {}).get("employee", {}).get("rate", 0) - 0.05) < 0.001)
    s.check("VRS P1 vesting 5 years", p1.get("vesting", {}).get("years") == 5)
    s.check("VRS P1 COLA max 5%", abs(p1.get("cola", {}).get("maximum", 0) - 0.05) < 0.001)
    s.check("VRS P1 normal ret age 65", p1.get("eligibility", {}).get("normalRetirementAge") == 65)
    s.check("VRS P1 has PLOP", "plop" in p1)
    s.check("VRS P1 has 5 payout options", len(p1.get("benefitPayoutOptions", [])) == 5)

    # Plan 2
    p2 = plans.get("vrs_plan2", {})
    s.check("VRS P2 multiplier post-2013 1.65%", abs(p2.get("formula", {}).get("multiplier_post_2013", 0) - 0.0165) < 0.0001)
    s.check("VRS P2 multiplier pre-2013 1.7%", abs(p2.get("formula", {}).get("multiplier_pre_2013", 0) - 0.017) < 0.0001)
    s.check("VRS P2 AFC 60 months", p2.get("formula", {}).get("averageFinalCompensation", {}).get("months") == 60)
    s.check("VRS P2 COLA max 3%", abs(p2.get("cola", {}).get("maximum", 0) - 0.03) < 0.001)
    s.check("VRS P2 reduced ret age 60", p2.get("eligibility", {}).get("reducedRetirement", [{}])[0].get("age") == 60)
    s.check("VRS P2 mandatory ret 73", p2.get("eligibility", {}).get("mandatoryRetirementAge") == 73)

    # Hybrid
    hyb = plans.get("vrs_hybrid", {})
    s.check("VRS Hybrid is hybrid_db_dc", hyb.get("planType") == "hybrid_db_dc")
    s.check("VRS Hybrid OPEN", hyb.get("status") == "OPEN")
    db = hyb.get("definedBenefit", {})
    s.check("VRS Hybrid DB multiplier 1.0%", abs(db.get("multiplier", 0) - 0.01) < 0.001)
    s.check("VRS Hybrid DB AFC 60 months", db.get("averageFinalCompensation", {}).get("months") == 60)
    dc = hyb.get("definedContribution", {})
    s.check("VRS Hybrid DC has mandatory", "mandatory" in dc)
    s.check("VRS Hybrid DC has voluntary", "voluntary" in dc)
    s.check("VRS Hybrid DC EE mandatory 1%", abs(dc.get("mandatory", {}).get("employee", {}).get("rate", 0) - 0.01) < 0.001)
    s.check("VRS Hybrid DC ER match max 2.5%", abs(dc.get("voluntary", {}).get("employerMatch", {}).get("maxRate", 0) - 0.025) < 0.001)
    dcv = dc.get("vesting", {})
    s.check("VRS Hybrid DC 4yr full vest", abs(dcv.get("4_years", 0) - 1.0) < 0.001)
    s.check("VRS Hybrid COLA max 3%", abs(hyb.get("cola", {}).get("maximum", 0) - 0.03) < 0.001)

    # Hazardous duty
    hd = data.get("hazardousDuty", {})
    s.check("VRS has hazardousDuty section", bool(hd))
    systems = hd.get("systems", {})
    s.check("VRS has SPORS/VaLORS/polSub", {"SPORS", "VaLORS", "politicalSubdivisionEnhanced"} == set(systems.keys()))

    spors = systems.get("SPORS", {})
    s.check("VRS SPORS multiplier 1.85%", abs(spors.get("multiplier", 0) - 0.0185) < 0.0001)
    s.check("VRS SPORS mandatory ret 70", spors.get("eligibility", {}).get("mandatoryRetirementAge") == 70)

    valors = systems.get("VaLORS", {})
    s.check("VRS VaLORS post-2001 multiplier 2.0%", abs(valors.get("multiplier_post_2001", 0) - 0.02) < 0.001)

    supp = hd.get("hazardousDutySupplement", {})
    s.check("VRS HD supplement $17,856/yr", supp.get("currentAmount", {}).get("annual") == 17856)
    s.check("VRS HD supplement $1,488/mo", supp.get("currentAmount", {}).get("monthly") == 1488)
    s.check("VRS HD supplement requires 20 years", "20" in str(supp.get("eligibility", "")))

    # Health insurance credit
    hic = data.get("healthInsuranceCredit", {})
    s.check("VRS health credit requires 15 years", "15" in str(hic.get("eligibility", "")))
    s.check("VRS health credit tax free", hic.get("taxFree") is True)
    s.check("VRS state $4.25/yr", abs(hic.get("stateEmployees", {}).get("perYearOfService", 0) - 4.25) < 0.01)

    # Portability
    port = data.get("portabilityAgreements", [])
    s.check("VRS has 7 portability agreements", len(port) == 7)
    s.check("VRS portability includes Richmond", "Richmond" in port)


def test_mcerp_plans(s):
    """Validate Montgomery County Employee Retirement Plans (MCERP) data."""
    path = s.root / "states" / "maryland" / "montgomery-county" / "mcerp-plans.json"
    s.check("MCERP file exists", path.exists())
    if not path.exists():
        return

    data = json.loads(path.read_text())

    # Top-level structure
    s.check("MCERP has systemName", data.get("systemName") == "Montgomery County Employee Retirement Plans")
    s.check("MCERP abbreviation is MCERP", data.get("systemAbbreviation") == "MCERP")
    s.check("MCERP established 1965", data.get("established") == 1965)
    s.check("MCERP has version", "version" in data)
    s.check("MCERP participates in SS", data.get("socialSecurityParticipation") is True)
    s.check("MCERP jurisdiction state maryland", data.get("jurisdiction", {}).get("state") == "maryland")
    s.check("MCERP scope is county", data.get("scope") == "county")
    s.check("MCERP has participating agencies", len(data.get("participatingAgencies", [])) >= 5)

    # Membership stats
    stats = data.get("membershipStats", {})
    s.check("MCERP assets >= $7B", stats.get("totalAssets", 0) >= 7000000000)
    s.check("MCERP active >= 9000", stats.get("activeEmployees", 0) >= 9000)
    s.check("MCERP retirees >= 6000", stats.get("retirees", 0) >= 6000)

    # Plans structure
    plans = data.get("plans", {})
    s.check("MCERP has 8 plans", len(plans) == 8)
    expected = {"ers_optional_nonintegrated", "ers_optional_integrated", "ers_mandatory_integrated",
                "ers_public_safety", "grip", "rsp", "eop", "dcp"}
    s.check("MCERP plan IDs correct", set(plans.keys()) == expected)

    # ERS Optional Non-Integrated
    oni = plans.get("ers_optional_nonintegrated", {})
    s.check("MCERP oni multiplier 2%", abs(oni.get("formula", {}).get("multiplier", 0) - 0.02) < 0.001)
    s.check("MCERP oni max years 36", oni.get("formula", {}).get("maxYearsOfService") == 36)
    s.check("MCERP oni AFE 12 months", oni.get("formula", {}).get("averageFinalEarnings", {}).get("months") == 12)
    s.check("MCERP oni not SS integrated", oni.get("formula", {}).get("socialSecurityIntegration") is False)
    s.check("MCERP oni normal ret age 60", oni.get("eligibility", {}).get("normalRetirement", {}).get("age") == 60)
    s.check("MCERP oni early ret age 50", oni.get("eligibility", {}).get("earlyRetirement", {}).get("age") == 50)
    s.check("MCERP oni vesting 5 years", oni.get("vesting", {}).get("years") == 5)
    s.check("MCERP oni current EE contrib 8%", abs(oni.get("contributions", {}).get("employee", {}).get("current", 0) - 0.08) < 0.001)
    s.check("MCERP oni interest 4%", abs(oni.get("contributions", {}).get("interestOnContributions", 0) - 0.04) < 0.001)
    s.check("MCERP oni has 7 payout options", len(oni.get("benefitPayoutOptions", [])) == 7)
    s.check("MCERP oni has rule85", "rule85" in oni.get("eligibility", {}))
    s.check("MCERP oni sick leave max 24 months", oni.get("formula", {}).get("sickLeaveCredit", {}).get("maxMonths") == 24)

    # Early reduction schedule
    er = oni.get("eligibility", {}).get("earlyReduction", {})
    s.check("MCERP oni 1yr reduction 2%", abs(er.get("1_year", 0) - 0.02) < 0.001)
    s.check("MCERP oni 5yr reduction 20%", abs(er.get("5_years", 0) - 0.20) < 0.001)
    s.check("MCERP oni 10yr reduction 60%", abs(er.get("10_years", 0) - 0.60) < 0.001)

    # COLA
    cola = oni.get("cola", {})
    s.check("MCERP oni has pre/post July 2011 COLA", "preJuly2011Service" in cola and "postJuly2011Service" in cola)
    s.check("MCERP oni post-2011 COLA max 2.5%", "2.5%" in str(cola.get("postJuly2011Service", "")))

    # Disability
    dis = oni.get("disability", {})
    s.check("MCERP oni has service-connected disability", "serviceConnected" in dis)
    s.check("MCERP oni has non-service disability", "nonServiceConnected" in dis)

    # ERS Optional Integrated
    oi = plans.get("ers_optional_integrated", {})
    s.check("MCERP oi is SS integrated", oi.get("formula", {}).get("type") == "defined_benefit_integrated")
    s.check("MCERP oi before SS multiplier 2%", abs(oi.get("formula", {}).get("beforeSSAge", {}).get("multiplier", 0) - 0.02) < 0.001)
    s.check("MCERP oi after SS below comp 1.25%", abs(oi.get("formula", {}).get("afterSSAge", {}).get("belowSSCoveredComp", 0) - 0.0125) < 0.001)
    s.check("MCERP oi after SS above comp 2%", abs(oi.get("formula", {}).get("afterSSAge", {}).get("aboveSSCoveredComp", 0) - 0.02) < 0.001)
    s.check("MCERP oi AFE 12 months", oi.get("formula", {}).get("averageFinalEarnings", {}).get("months") == 12)

    # ERS Mandatory Integrated
    mi = plans.get("ers_mandatory_integrated", {})
    s.check("MCERP mi AFE 36 months", mi.get("formula", {}).get("averageFinalEarnings", {}).get("months") == 36)
    s.check("MCERP mi is SS integrated", mi.get("formula", {}).get("type") == "defined_benefit_integrated")
    s.check("MCERP mi closed Oct 1994", mi.get("closedToNewEntrants") == "1994-10-01")
    mi_cola = mi.get("cola", {})
    s.check("MCERP mi has complex pre-2011 COLA", "7.5%" in str(mi_cola.get("preJuly2011Service", "")))

    # Public Safety
    ps = plans.get("ers_public_safety", {})
    s.check("MCERP public safety OPEN", ps.get("status") == "OPEN")
    s.check("MCERP public safety has groups E/F/G", set(ps.get("groups", [])) == {"E", "F", "G"})
    s.check("MCERP public safety vesting 5 years", ps.get("vesting", {}).get("years") == 5)

    # GRIP
    grip = plans.get("grip", {})
    s.check("MCERP GRIP is cash_balance", grip.get("planType") == "cash_balance")
    s.check("MCERP GRIP OPEN", grip.get("status") == "OPEN")
    gc = grip.get("contributions", {})
    s.check("MCERP GRIP non-PS EE below SS 4%", abs(gc.get("employee", {}).get("nonPublicSafety", {}).get("belowSSWageBase", 0) - 0.04) < 0.001)
    s.check("MCERP GRIP non-PS EE above SS 8%", abs(gc.get("employee", {}).get("nonPublicSafety", {}).get("aboveSSWageBase", 0) - 0.08) < 0.001)
    s.check("MCERP GRIP PS EE below SS 3%", abs(gc.get("employee", {}).get("publicSafety", {}).get("belowSSWageBase", 0) - 0.03) < 0.001)
    s.check("MCERP GRIP non-PS ER 8%", abs(gc.get("employer", {}).get("nonPublicSafety", 0) - 0.08) < 0.001)
    s.check("MCERP GRIP PS ER 10%", abs(gc.get("employer", {}).get("publicSafety", 0) - 0.10) < 0.001)
    gv = grip.get("vesting", {})
    s.check("MCERP GRIP EE vest immediate", gv.get("employeeContributions") == "immediate")
    s.check("MCERP GRIP ER vest 3 years", gv.get("employerContributions", {}).get("years") == 3)

    # RSP
    rsp = plans.get("rsp", {})
    s.check("MCERP RSP is DC", rsp.get("planType") == "defined_contribution")
    s.check("MCERP RSP OPEN", rsp.get("status") == "OPEN")

    # DCP
    dcp = plans.get("dcp", {})
    s.check("MCERP DCP is 457", dcp.get("planCode") == "457(b)")

    # Cross-system: MCERP is different from RRS
    rrs_path = s.root / "states" / "virginia" / "richmond" / "rrs-plans.json"
    if rrs_path.exists():
        rrs = json.loads(rrs_path.read_text())
        s.check("MCERP and RRS are different systems",
                data.get("systemAbbreviation") != rrs.get("systemAbbreviation"))
        s.check("MCERP in MD, RRS in VA",
                data.get("jurisdiction", {}).get("state") != rrs.get("jurisdiction", {}).get("state"))


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
    test_rrs_plans(s)
    test_vrs_consolidated(s)
    test_mcerp_plans(s)

    success = s.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
