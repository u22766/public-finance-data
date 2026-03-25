#!/usr/bin/env python3
"""Validation suite for SDCERA pension plans data."""

import json
import os
import sys

PASSED = 0
FAILED = 0

def check(condition, description):
    global PASSED, FAILED
    if condition:
        PASSED += 1
    else:
        FAILED += 1
        print(f"  FAIL: {description}")

def main():
    global PASSED, FAILED

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdcera_path = os.path.join(repo_root, "states", "california", "san-diego-county", "sdcera-plans.json")

    if not os.path.exists(sdcera_path):
        print(f"SKIP: {sdcera_path} not found")
        sys.exit(0)

    with open(sdcera_path) as f:
        data = json.load(f)

    print("=== SDCERA System Overview ===")
    check(data.get("version") == "2026.1", "version is 2026.1")
    check("SDCERA" in data.get("description", ""), "description mentions SDCERA")
    check("1937" in data.get("description", ""), "description mentions 1937 Act")

    overview = data.get("system_overview", {})
    check(overview.get("abbreviation") == "SDCERA", "abbreviation is SDCERA")
    check(overview.get("established") == "1939-07-01", "established July 1, 1939")
    check(overview.get("governing_law") and "1937" in overview["governing_law"], "governing law references 1937 Act")
    check(overview.get("plan_type") == "defined_benefit", "plan type is defined_benefit")
    check(overview.get("irc_qualification") == "401(a)", "IRC qualification is 401(a)")
    check(set(overview.get("classifications", [])) == {"general", "safety"}, "two classifications: general and safety")
    check(len(overview.get("participating_employers", [])) >= 5, "at least 5 participating employers")
    check("County of San Diego" in overview.get("participating_employers", []), "County of San Diego is participating employer")

    membership = overview.get("membership_as_of_fy2024", {})
    check(membership.get("active", 0) >= 15000, "active members >= 15,000")
    check(membership.get("total", 0) >= 40000, "total members >= 40,000")
    check(overview.get("funded_ratio_pct", 0) > 50, "funded ratio > 50%")
    check(overview.get("assets_billions", 0) > 10, "assets > $10B")

    print("\n=== Membership Rules ===")
    rules = data.get("membership_rules", {})
    check(rules.get("vesting_years") == 5, "vesting is 5 years")
    check(rules.get("mandatory") is True, "membership is mandatory")

    print("\n=== Plan Count and Structure ===")
    plans = data.get("plans", {})
    check(len(plans) == 9, f"exactly 9 plans (got {len(plans)})")

    general_plans = [k for k, v in plans.items() if v.get("classification") == "general"]
    safety_plans = [k for k, v in plans.items() if v.get("classification") == "safety"]
    check(len(general_plans) == 5, f"5 general plans (got {len(general_plans)})")
    check(len(safety_plans) == 4, f"4 safety plans (got {len(safety_plans)})")

    # Expected plans
    expected_plans = [
        "general_tier_I", "general_tier_A", "general_tier_B",
        "general_tier_C", "general_tier_D",
        "safety_tier_A", "safety_tier_B", "safety_tier_C", "safety_tier_D"
    ]
    for ep in expected_plans:
        check(ep in plans, f"plan {ep} exists")

    print("\n=== Benefit Formulas ===")
    formula_checks = {
        "general_tier_I": ("2.62% at 62", 2.62, 62),
        "general_tier_A": ("3.0% at 60", 3.0, 60),
        "general_tier_B": ("2.62% at 62", 2.62, 62),
        "general_tier_C": ("2.5% at 67", 2.5, 67),
        "general_tier_D": ("1.62% at 65", 1.62, 65),
        "safety_tier_A": ("3.0% at 50", 3.0, 50),
        "safety_tier_B": ("3.0% at 55", 3.0, 55),
        "safety_tier_C": ("2.7% at 57", 2.7, 57),
        "safety_tier_D": ("2.5% at 57", 2.5, 57),
    }
    for plan_key, (name, max_pct, max_age) in formula_checks.items():
        if plan_key in plans:
            formula = plans[plan_key].get("benefit_formula", {})
            check(formula.get("name") == name, f"{plan_key} formula name is '{name}'")
            check(formula.get("max_age_factor_pct") == max_pct, f"{plan_key} max age factor is {max_pct}%")
            check(formula.get("max_age_factor_age") == max_age, f"{plan_key} max age factor age is {max_age}")

    print("\n=== Government Code Sections ===")
    gc_checks = {
        "general_tier_I": "§31676.12",
        "general_tier_A": "§31676.17",
        "general_tier_B": "§31676.12",
        "general_tier_C": "§7522.20(a)",
        "general_tier_D": "§31676.01",
        "safety_tier_A": "§31664.1",
        "safety_tier_B": "§31664.2",
        "safety_tier_C": "§7522.25(d)",
        "safety_tier_D": "§7522.25(c)",
    }
    for plan_key, gc in gc_checks.items():
        if plan_key in plans:
            check(plans[plan_key].get("government_code") == gc, f"{plan_key} gov code is {gc}")

    print("\n=== Final Average Compensation ===")
    for plan_key in ["general_tier_I", "general_tier_A", "safety_tier_A"]:
        if plan_key in plans:
            fac = plans[plan_key].get("final_average_compensation", {})
            check(fac.get("period") == "highest_1_year", f"{plan_key} FAC is highest 1 year")
            check(fac.get("pay_periods") == 26, f"{plan_key} FAC is 26 pay periods")

    for plan_key in ["general_tier_B", "general_tier_C", "general_tier_D",
                      "safety_tier_B", "safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            fac = plans[plan_key].get("final_average_compensation", {})
            check(fac.get("period") == "highest_3_year", f"{plan_key} FAC is highest 3 year")
            check(fac.get("pay_periods") == 78, f"{plan_key} FAC is 78 pay periods")

    print("\n=== COLA Caps ===")
    for plan_key in ["general_tier_I", "general_tier_A", "safety_tier_A"]:
        if plan_key in plans:
            cola = plans[plan_key].get("cola", {})
            check(cola.get("max_pct") == 3.0, f"{plan_key} COLA cap is 3.0%")
            check(cola.get("guaranteed") is False, f"{plan_key} COLA is not guaranteed")

    for plan_key in ["general_tier_B", "general_tier_C", "general_tier_D",
                      "safety_tier_B", "safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            cola = plans[plan_key].get("cola", {})
            check(cola.get("max_pct") == 2.0, f"{plan_key} COLA cap is 2.0%")

    print("\n=== Retirement Eligibility ===")
    # General Tier I, A: age 50 + 10 years
    for plan_key in ["general_tier_I", "general_tier_A"]:
        if plan_key in plans:
            elig = plans[plan_key].get("retirement_eligibility", {})
            normal = elig.get("normal", {})
            check(normal.get("age") == 50, f"{plan_key} normal retirement age is 50")
            check(normal.get("years_of_service") == 10, f"{plan_key} normal service is 10 years")
            check(elig.get("full_service", {}).get("years_of_service") == 30, f"{plan_key} full service at 30 years")

    # General Tier B: age 55 + 10 years
    if "general_tier_B" in plans:
        elig = plans["general_tier_B"].get("retirement_eligibility", {})
        check(elig.get("normal", {}).get("age") == 55, "general_tier_B normal retirement age is 55")
        check(elig.get("normal", {}).get("years_of_service") == 10, "general_tier_B normal service is 10 years")

    # General Tier C, D: age 52 + 5 years
    for plan_key in ["general_tier_C", "general_tier_D"]:
        if plan_key in plans:
            elig = plans[plan_key].get("retirement_eligibility", {})
            check(elig.get("normal", {}).get("age") == 52, f"{plan_key} normal retirement age is 52")
            check(elig.get("normal", {}).get("years_of_service") == 5, f"{plan_key} normal service is 5 years")

    # Safety Tier A, B: age 50 + 10 years, 20 years any age
    for plan_key in ["safety_tier_A", "safety_tier_B"]:
        if plan_key in plans:
            elig = plans[plan_key].get("retirement_eligibility", {})
            check(elig.get("normal", {}).get("age") == 50, f"{plan_key} normal retirement age is 50")
            check(elig.get("full_service", {}).get("years_of_service") == 20, f"{plan_key} full service at 20 years")

    # Safety Tier C, D: age 50 + 5 years
    for plan_key in ["safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            elig = plans[plan_key].get("retirement_eligibility", {})
            check(elig.get("normal", {}).get("age") == 50, f"{plan_key} normal retirement age is 50")
            check(elig.get("normal", {}).get("years_of_service") == 5, f"{plan_key} normal service is 5 years")

    # All tiers: age 70 regardless of service
    for plan_key in expected_plans:
        if plan_key in plans:
            elig = plans[plan_key].get("retirement_eligibility", {})
            check(elig.get("age_only", {}).get("age") == 70, f"{plan_key} age-only retirement at 70")

    print("\n=== PEPRA Flags ===")
    for plan_key in ["general_tier_C", "safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            check(plans[plan_key].get("pepra") is True, f"{plan_key} is PEPRA")

    # General Tier D is NOT PEPRA despite post-2013 date
    if "general_tier_D" in plans:
        check(plans["general_tier_D"].get("pepra") is False, "general_tier_D is NOT PEPRA (uses §31676.01)")

    print("\n=== Social Security Integration ===")
    for plan_key in ["general_tier_I", "general_tier_A", "general_tier_B"]:
        if plan_key in plans:
            check(plans[plan_key].get("social_security_integration") is True, f"{plan_key} is SS integrated")

    for plan_key in ["general_tier_C", "general_tier_D",
                      "safety_tier_A", "safety_tier_B", "safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            check(plans[plan_key].get("social_security_integration") is False, f"{plan_key} is NOT SS integrated")

    print("\n=== Excess Benefit Plan ===")
    for plan_key in ["general_tier_I", "general_tier_A", "general_tier_B",
                      "safety_tier_A", "safety_tier_B"]:
        if plan_key in plans:
            check(plans[plan_key].get("excess_benefit_plan_eligible") is True, f"{plan_key} eligible for excess benefit plan")

    for plan_key in ["general_tier_C", "general_tier_D", "safety_tier_C", "safety_tier_D"]:
        if plan_key in plans:
            check(plans[plan_key].get("excess_benefit_plan_eligible") is False, f"{plan_key} NOT eligible for excess benefit plan")

    print("\n=== Compensation Limits ===")
    for plan_key in ["general_tier_I", "general_tier_A", "general_tier_B",
                      "safety_tier_A", "safety_tier_B"]:
        if plan_key in plans:
            check(plans[plan_key].get("compensation_limit_2026") == 360000, f"{plan_key} comp limit $360K (2026)")
            check(plans[plan_key].get("irc_415b_limit_2026_at_62") == 290000, f"{plan_key} 415(b) limit $290K at 62")

    print("\n=== 30-Year Contribution Cessation ===")
    for plan_key in ["general_tier_I", "general_tier_A", "general_tier_B",
                      "safety_tier_A", "safety_tier_B"]:
        if plan_key in plans:
            check(plans[plan_key].get("contribution_cessation_years") == 30, f"{plan_key} contribution cessation at 30 years")

    print("\n=== Benefit Options ===")
    options = data.get("benefit_options", {})
    check(len(options.get("options", [])) == 5, "5 benefit options")
    option_names = [o.get("name") for o in options.get("options", [])]
    check("Unmodified" in option_names, "Unmodified option exists")
    check("Option 1" in option_names, "Option 1 exists")
    check("Option 4" in option_names, "Option 4 exists")

    # Unmodified = 60% continuance
    unmod = next((o for o in options.get("options", []) if o.get("name") == "Unmodified"), {})
    check(unmod.get("survivor_continuance_pct") == 60, "Unmodified: 60% survivor continuance")
    check(unmod.get("can_change_beneficiary_after_retirement") is True, "Unmodified: can change beneficiary")

    # Options 2-4 cannot change beneficiary
    for opt_name in ["Option 2", "Option 3", "Option 4"]:
        opt = next((o for o in options.get("options", []) if o.get("name") == opt_name), {})
        check(opt.get("can_change_beneficiary_after_retirement") is False, f"{opt_name}: cannot change beneficiary")

    print("\n=== Reciprocity and Other Features ===")
    check(data.get("reciprocity", {}).get("available") is True, "reciprocity is available")
    check(len(data.get("service_credit_purchases", {}).get("types", [])) >= 5, "at least 5 service credit purchase types")

    post_ret = data.get("post_retirement_employment", {})
    check(post_ret.get("waiting_period_days") == 180, "180-day reemployment waiting period")
    check(post_ret.get("max_hours_per_fiscal_year") == 960, "960 max hours per fiscal year")

    print("\n=== Reasonableness Checks ===")
    # Age factors should be monotonically ordered for safety: A > B formula age (50 < 55)
    safety_a = plans.get("safety_tier_A", {}).get("benefit_formula", {})
    safety_b = plans.get("safety_tier_B", {}).get("benefit_formula", {})
    check(safety_a.get("max_age_factor_age", 99) < safety_b.get("max_age_factor_age", 0),
          "Safety Tier A max factor age < Safety Tier B (50 < 55)")

    # General Tier A is most generous (3.0% at 60) > Tier I/B (2.62% at 62) > Tier D (1.62% at 65)
    gen_a_pct = plans.get("general_tier_A", {}).get("benefit_formula", {}).get("max_age_factor_pct", 0)
    gen_ib_pct = plans.get("general_tier_I", {}).get("benefit_formula", {}).get("max_age_factor_pct", 0)
    gen_d_pct = plans.get("general_tier_D", {}).get("benefit_formula", {}).get("max_age_factor_pct", 0)
    check(gen_a_pct > gen_ib_pct > gen_d_pct, f"General formula generosity: A ({gen_a_pct}) > I/B ({gen_ib_pct}) > D ({gen_d_pct})")

    # Safety Tier C (2.7%) > Safety Tier D (2.5%)
    safety_c_pct = plans.get("safety_tier_C", {}).get("benefit_formula", {}).get("max_age_factor_pct", 0)
    safety_d_pct = plans.get("safety_tier_D", {}).get("benefit_formula", {}).get("max_age_factor_pct", 0)
    check(safety_c_pct > safety_d_pct, f"Safety C ({safety_c_pct}) > Safety D ({safety_d_pct})")

    # Manifest check
    manifest_path = os.path.join(repo_root, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        check("sdcera_plans" in manifest.get("files", {}), "sdcera_plans in manifest")

    print(f"\n{'='*60}")
    print(f"SDCERA VALIDATION: {PASSED + FAILED} checks | PASS: {PASSED} | FAIL: {FAILED}")
    print(f"{'='*60}")

    if FAILED > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
