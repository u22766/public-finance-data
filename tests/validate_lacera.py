#!/usr/bin/env python3
"""
Validation suite for LACERA (Los Angeles County) retirement plans.
Tests: metadata, structure, plan provisions, benefit formulas, COLA rules,
eligibility, cross-plan consistency, benefit factor table verification,
PII/consumer-agnostic compliance, and manifest presence.
"""
import json
import os
import sys
import re

PASS = 0
FAIL = 0

def check(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")

def main():
    global PASS, FAIL

    # Locate file
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fpath = os.path.join(base, "states", "california", "los-angeles-county", "lacera-plans.json")
    check(os.path.exists(fpath), "lacera-plans.json exists")

    with open(fpath) as f:
        data = json.load(f)

    # ── METADATA ──────────────────────────────────────────────────
    print("Metadata checks...")
    check(data.get("version") == "2026.3", f"version is 2026.3, got {data.get('version')}")
    check("effective_date" in data, "effective_date present")
    check("description" in data, "description present")
    check("source" in data, "source present")
    check(isinstance(data.get("source_urls"), list), "source_urls is list")
    check(len(data.get("source_urls", [])) >= 5, f"source_urls has >=5 entries, got {len(data.get('source_urls', []))}")

    # All source URLs should be HTTPS
    for i, url in enumerate(data.get("source_urls", [])):
        check(url.startswith("https://"), f"source_url[{i}] is HTTPS")

    # ── SYSTEM OVERVIEW ───────────────────────────────────────────
    print("System overview checks...")
    so = data.get("system_overview", {})
    check(so.get("abbreviation") == "LACERA", "abbreviation is LACERA")
    check(so.get("name") == "Los Angeles County Employees Retirement Association", "full name correct")
    check(so.get("established") == 1938, f"established 1938, got {so.get('established')}")
    check(so.get("plan_type") == "defined_benefit", "plan_type is defined_benefit")
    check(so.get("irc_qualification") == "401(a)", "IRC qualification is 401(a)")
    check("general" in so.get("classifications", []), "general classification present")
    check("safety" in so.get("classifications", []), "safety classification present")
    check(isinstance(so.get("assets_billions"), (int, float)), "assets_billions is numeric")
    check(so.get("assets_billions", 0) > 50, f"assets > $50B, got {so.get('assets_billions')}")
    check(isinstance(so.get("funded_ratio_pct"), (int, float)), "funded_ratio_pct is numeric")
    check(50 < so.get("funded_ratio_pct", 0) < 120, f"funded_ratio 50-120%, got {so.get('funded_ratio_pct')}")
    check(so.get("actuary") == "Milliman", f"actuary is Milliman, got {so.get('actuary')}")
    check("lacera.gov" in so.get("website", ""), "website contains lacera.gov")
    check(so.get("phone") == "800-786-6464", f"phone correct, got {so.get('phone')}")

    # Membership numbers
    mem = so.get("membership_as_of_fy2024", {})
    check(mem.get("total", 0) > 100000, f"total membership > 100K, got {mem.get('total')}")
    check(mem.get("active", 0) > 50000, f"active > 50K, got {mem.get('active')}")
    check(mem.get("retirees_and_beneficiaries", 0) > 30000, "retirees > 30K")

    # ── PLAN STRUCTURE ────────────────────────────────────────────
    print("Plan structure checks...")
    plans = data.get("plans", {})
    EXPECTED_PLANS = [
        "general_A", "general_B", "general_C", "general_D", "general_E",
        "general_G", "safety_A", "safety_B", "safety_C"
    ]
    check(len(plans) == 9, f"9 plans present, got {len(plans)}")
    for p in EXPECTED_PLANS:
        check(p in plans, f"plan {p} present")

    # ── PER-PLAN STRUCTURAL CHECKS ────────────────────────────────
    print("Per-plan provision checks...")
    REQUIRED_PLAN_KEYS = [
        "classification", "pepra", "membership_dates", "contributory",
        "benefit_formula", "final_average_compensation", "max_benefit_pct_of_fac",
        "max_benefit_age", "retirement_eligibility", "vesting_years", "cola"
    ]
    for pname, plan in plans.items():
        for key in REQUIRED_PLAN_KEYS:
            check(key in plan, f"{pname} has key '{key}'")

        # Classification consistency
        if pname.startswith("general_"):
            check(plan.get("classification") == "general", f"{pname} classification is general")
        elif pname.startswith("safety_"):
            check(plan.get("classification") == "safety", f"{pname} classification is safety")

        # PEPRA flag
        if pname in ("general_G", "safety_C"):
            check(plan.get("pepra") is True, f"{pname} pepra is True")
        else:
            check(plan.get("pepra") is False, f"{pname} pepra is False")

        # Benefit formula structure
        bf = plan.get("benefit_formula", {})
        check("name" in bf, f"{pname} benefit_formula has name")
        check("max_age_factor_pct" in bf, f"{pname} benefit_formula has max_age_factor_pct")
        check("max_age_factor_age" in bf, f"{pname} benefit_formula has max_age_factor_age")
        check(isinstance(bf.get("max_age_factor_pct"), (int, float)), f"{pname} max_age_factor_pct is numeric")
        check(0.5 <= bf.get("max_age_factor_pct", 0) <= 4.0, f"{pname} max_age_factor_pct in range 0.5-4.0")

        # FAC structure
        fac = plan.get("final_average_compensation", {})
        check("months" in fac, f"{pname} FAC has months")
        check(fac.get("months") in (12, 36), f"{pname} FAC months is 12 or 36, got {fac.get('months')}")

        # Max benefit
        check(plan.get("max_benefit_pct_of_fac") in (80, 100), f"{pname} max_benefit 80 or 100, got {plan.get('max_benefit_pct_of_fac')}")

        # Retirement eligibility structure
        elig = plan.get("retirement_eligibility", {})
        check("normal" in elig, f"{pname} has normal eligibility")
        normal = elig.get("normal", {})
        check("age" in normal, f"{pname} normal eligibility has age")
        check("years_of_service" in normal, f"{pname} normal eligibility has years_of_service")

        # Vesting
        check(plan.get("vesting_years") in (5, 10), f"{pname} vesting is 5 or 10, got {plan.get('vesting_years')}")

        # COLA structure
        cola = plan.get("cola", {})
        check("max_pct" in cola, f"{pname} COLA has max_pct")
        check(cola.get("max_pct") in (2.0, 3.0), f"{pname} COLA max is 2.0 or 3.0, got {cola.get('max_pct')}")
        check(cola.get("cola_bank") is True, f"{pname} COLA bank is True")
        check("CPI" in cola.get("index", ""), f"{pname} COLA index references CPI")
        check("Los Angeles" in cola.get("index", ""), f"{pname} COLA index references Los Angeles")

    # ── SPECIFIC PLAN PROVISION VERIFICATION ──────────────────────
    print("Plan-specific provision verification...")

    # General A
    ga = plans["general_A"]
    check(ga["benefit_formula"]["max_age_factor_age"] == 62, "General A max benefit age 62")
    check(ga["cola"]["max_pct"] == 3.0, "General A COLA max 3%")
    check(ga["final_average_compensation"]["months"] == 12, "General A FAC 12 months")
    check(ga["max_benefit_pct_of_fac"] == 100, "General A max benefit 100%")

    # General B
    gb = plans["general_B"]
    check(gb["benefit_formula"]["max_age_factor_age"] == 65, "General B max benefit age 65")
    check(gb["cola"]["max_pct"] == 2.0, "General B COLA max 2%")

    # General C
    gc = plans["general_C"]
    check(gc["benefit_formula"]["max_age_factor_age"] == 65, "General C max benefit age 65")
    check(gc["cola"]["max_pct"] == 2.0, "General C COLA max 2%")

    # General D
    gd = plans["general_D"]
    check(gd["benefit_formula"]["max_age_factor_age"] == 65, "General D max benefit age 65")
    check(gd["cola"]["max_pct"] == 2.0, "General D COLA max 2%")
    check(gd["cola"]["applies_to_all_service"] is False, "General D COLA not for all service")
    check(gd["cola"]["cola_service_start_date"] == "2002-06-04", "General D COLA starts 6/4/2002")
    check(gd["final_average_compensation"]["months"] == 12, "General D FAC 12 months")
    check(gd["vesting_years"] == 5, "General D vesting 5 years")

    # General E (noncontributory)
    ge = plans["general_E"]
    check(ge["contributory"] is False, "General E is noncontributory")
    check(ge["benefit_formula"]["max_age_factor_pct"] == 1.6, "General E max factor 1.6%")
    check(ge["benefit_formula"]["max_age_factor_age"] == 65, "General E max benefit age 65")
    check(ge["max_benefit_pct_of_fac"] == 80, "General E max benefit 80%")
    check(ge["vesting_years"] == 10, "General E vesting 10 years")
    check(ge["retirement_eligibility"]["normal"]["age"] == 55, "General E min age 55")
    check(ge["retirement_eligibility"]["normal"]["years_of_service"] == 10, "General E min service 10")
    check(ge["cola"]["applies_to_all_service"] is False, "General E COLA not for all service")
    check(ge["cola"]["cola_service_start_date"] == "2002-06-04", "General E COLA starts 6/4/2002")
    check(ge["cola"].get("elective_cola_purchasable") is True, "General E elective COLA purchasable")
    check(ge.get("disability_retirement", {}).get("lacera_administered") is False, "General E no LACERA disability")
    check(ge.get("county_life_insurance_active") == 10000, "General E county life insurance $10K")
    check(ge["final_average_compensation"]["months"] == 36, "General E FAC 36 months")

    # General G (PEPRA)
    gg = plans["general_G"]
    check(gg["pepra"] is True, "General G is PEPRA")
    check(gg["benefit_formula"]["max_age_factor_pct"] == 2.5, "General G max factor 2.5%")
    check(gg["benefit_formula"]["max_age_factor_age"] == 67, "General G max age 67")
    check(gg["benefit_formula"]["min_age_factor_pct"] == 1.0, "General G min factor 1.0%")
    check(gg["benefit_formula"]["min_age_factor_age"] == 52, "General G min age 52")
    check(gg["retirement_eligibility"]["normal"]["age"] == 52, "General G min retire age 52")
    check(gg["retirement_eligibility"]["normal"]["years_of_service"] == 5, "General G min service 5")
    check(gg["final_average_compensation"]["months"] == 36, "General G FAC 36 months")
    check("compensation_limit_2026" in gg, "General G has comp limit")
    check(gg["compensation_limit_2026"]["ss_covered"] == 159733, "General G SS-covered limit $159,733")
    check(gg["compensation_limit_2026"]["non_ss_covered"] == 191679, "General G non-SS limit $191,679")

    # Safety A
    sa = plans["safety_A"]
    check(sa["benefit_formula"]["max_age_factor_pct"] == 3.0, "Safety A max factor 3.0%")
    check(sa["benefit_formula"]["max_age_factor_age"] == 55, "Safety A max benefit age 55")
    check(sa["cola"]["max_pct"] == 3.0, "Safety A COLA max 3%")
    check(sa["social_security_coverage"] == "not_covered", "Safety A not SS covered")
    check(sa["final_average_compensation"]["months"] == 12, "Safety A FAC 12 months")

    # Safety B
    sb = plans["safety_B"]
    check(sb["benefit_formula"]["max_age_factor_pct"] == 3.0, "Safety B max factor 3.0%")
    check(sb["benefit_formula"]["max_age_factor_age"] == 55, "Safety B max benefit age 55")
    check(sb["cola"]["max_pct"] == 2.0, "Safety B COLA max 2%")
    check(sb["social_security_coverage"] == "not_covered", "Safety B not SS covered")

    # Safety C (PEPRA)
    sc = plans["safety_C"]
    check(sc["pepra"] is True, "Safety C is PEPRA")
    check(sc["benefit_formula"]["max_age_factor_pct"] == 2.7, "Safety C max factor 2.7%")
    check(sc["benefit_formula"]["max_age_factor_age"] == 57, "Safety C max age 57")
    check(sc["benefit_formula"]["min_age_factor_pct"] == 2.0, "Safety C min factor 2.0%")
    check(sc["benefit_formula"]["min_age_factor_age"] == 50, "Safety C min age 50")
    check(sc["retirement_eligibility"]["normal"]["age"] == 50, "Safety C min retire age 50")
    check(sc["retirement_eligibility"]["normal"]["years_of_service"] == 5, "Safety C min service 5")
    check(sc["social_security_coverage"] == "not_covered", "Safety C not SS covered")
    check(sc["final_average_compensation"]["months"] == 36, "Safety C FAC 36 months")
    check("compensation_limit_2026" in sc, "Safety C has comp limit")
    check(sc["compensation_limit_2026"]["non_ss_covered"] == 191679, "Safety C non-SS limit $191,679")

    # ── BENEFIT FACTOR TABLE VERIFICATION (Plan G) ────────────────
    print("Plan G benefit factor table verification...")
    bft = gg.get("benefit_factor_table", {})
    # Remove description key
    factors = {k: v for k, v in bft.items() if not k.startswith("_")}
    check(len(factors) == 16, f"Plan G has 16 age entries (52-67), got {len(factors)}")

    # Verify specific known values from official LACERA table
    # At 52 with 5 years = 5.0% → per year = 1.0%
    check(factors.get("52") == 1.0, f"Plan G factor at 52 = 1.0%, got {factors.get('52')}")
    # At 55 with 10 years = 13.0% → per year = 1.3%
    check(factors.get("55") == 1.3, f"Plan G factor at 55 = 1.3%, got {factors.get('55')}")
    # At 60 with 20 years = 36.0% → per year = 1.8%
    check(factors.get("60") == 1.8, f"Plan G factor at 60 = 1.8%, got {factors.get('60')}")
    # At 62 with 10 years = 20.0% → per year = 2.0%
    check(factors.get("62") == 2.0, f"Plan G factor at 62 = 2.0%, got {factors.get('62')}")
    # At 67 with 40 years = 100.0% → per year = 2.5%
    check(factors.get("67") == 2.5, f"Plan G factor at 67 = 2.5%, got {factors.get('67')}")

    # Monotonicity: factors should increase with age
    ages = sorted([int(k) for k in factors.keys()])
    for i in range(1, len(ages)):
        prev_age = str(ages[i-1])
        curr_age = str(ages[i])
        check(factors[curr_age] > factors[prev_age],
              f"Plan G factor monotonically increases: age {curr_age} ({factors[curr_age]}) > age {prev_age} ({factors[prev_age]})")

    # Increment consistency: should increase by 0.1 per year
    for i in range(1, len(ages)):
        prev_age = str(ages[i-1])
        curr_age = str(ages[i])
        diff = round(factors[curr_age] - factors[prev_age], 4)
        check(abs(diff - 0.1) < 0.001,
              f"Plan G factor increment age {prev_age}→{curr_age} = 0.1, got {diff}")

    # Verify table reproduces official LACERA percentages
    # 25 years at age 60 should produce 45.0%
    check(abs(25 * factors.get("60", 0) - 45.0) < 0.01, "25yrs × 1.8% at 60 = 45.0%")
    # 30 years at age 62 should produce 60.0%
    check(abs(30 * factors.get("62", 0) - 60.0) < 0.01, "30yrs × 2.0% at 62 = 60.0%")
    # 40 years at age 67 should produce 100.0%
    check(abs(40 * factors.get("67", 0) - 100.0) < 0.01, "40yrs × 2.5% at 67 = 100.0%")
    # 10 years at age 55 should produce 13.0%
    check(abs(10 * factors.get("55", 0) - 13.0) < 0.01, "10yrs × 1.3% at 55 = 13.0%")
    # 20 years at age 57 should produce 30.0%
    check(abs(20 * factors.get("57", 0) - 30.0) < 0.01, "20yrs × 1.5% at 57 = 30.0%")

    # ── BENEFIT FACTOR TABLE VERIFICATION (ALL PLANS) ─────────────
    print("All-plan benefit factor table verification...")

    # Helper: extract numeric factors from a plan's benefit_factor_table
    def get_factors(plan_id):
        tbl = plans[plan_id].get("benefit_factor_table", {})
        return {k: v for k, v in tbl.items() if not k.startswith("_")}

    # Every plan must have a benefit_factor_table
    for pid in plans:
        check("benefit_factor_table" in plans[pid],
              f"{pid} has benefit_factor_table")

    # -- Plan A: 13 ages (50-62), max 2.611 at 62 --
    fa = get_factors("general_A")
    check(len(fa) == 13, f"Plan A has 13 age entries (50-62), got {len(fa)}")
    check(fa.get("50") == 1.475, f"Plan A factor at 50 = 1.475, got {fa.get('50')}")
    check(fa.get("55") == 1.948, f"Plan A factor at 55 = 1.948, got {fa.get('55')}")
    check(fa.get("62") == 2.611, f"Plan A factor at 62 = 2.611, got {fa.get('62')}")
    # Cross-check: 20yr @ 60 = 48.80%
    check(abs(20 * fa.get("60", 0) - 48.80) < 0.02, "Plan A: 20yrs × 2.44% at 60 ≈ 48.80%")

    # -- Plan B: 16 ages (50-65), max 2.611 at 65 --
    fb = get_factors("general_B")
    check(len(fb) == 16, f"Plan B has 16 age entries (50-65), got {len(fb)}")
    check(fb.get("50") == 1.242, f"Plan B factor at 50 = 1.242, got {fb.get('50')}")
    check(fb.get("55") == 1.667, f"Plan B factor at 55 = 1.667, got {fb.get('55')}")
    check(fb.get("65") == 2.611, f"Plan B factor at 65 = 2.611, got {fb.get('65')}")
    # Cross-check: 30yr @ 65 = 78.33% (official table shows ~78.33 with rounding)
    check(abs(30 * fb.get("65", 0) - 78.33) < 0.05, "Plan B: 30yrs × 2.611% at 65 ≈ 78.33%")

    # -- Plan C = Plan B (same formula per LACERA basic provisions) --
    fc = get_factors("general_C")
    check(len(fc) == 16, f"Plan C has 16 age entries, got {len(fc)}")
    for age_key in fb:
        check(fc.get(age_key) == fb[age_key],
              f"Plan C factor at {age_key} matches Plan B ({fb[age_key]})")

    # -- Plan D = Plan B (same formula) --
    fd = get_factors("general_D")
    check(len(fd) == 16, f"Plan D has 16 age entries, got {len(fd)}")
    for age_key in fb:
        check(fd.get(age_key) == fb[age_key],
              f"Plan D factor at {age_key} matches Plan B ({fb[age_key]})")

    # -- Plan E: 11 ages (55-65), max 2.0 at 65, lower factors --
    fe = get_factors("general_E")
    check(len(fe) == 11, f"Plan E has 11 age entries (55-65), got {len(fe)}")
    check(fe.get("55") == 0.75, f"Plan E factor at 55 = 0.75, got {fe.get('55')}")
    check(fe.get("60") == 1.202, f"Plan E factor at 60 = 1.202, got {fe.get('60')}")
    check(fe.get("65") == 2.0, f"Plan E factor at 65 = 2.0, got {fe.get('65')}")
    # Cross-check: 20yr @ 60 = 24.04% (from official table)
    check(abs(20 * fe.get("60", 0) - 24.04) < 0.01, "Plan E: 20yrs × 1.202% at 60 = 24.04%")
    # Cross-check: 30yr @ 65 = 60.00% (from official table)
    check(abs(30 * fe.get("65", 0) - 60.00) < 0.01, "Plan E: 30yrs × 2.0% at 65 = 60.00%")

    # Plan E service_accrual (half-rate after 35 years)
    sa = plans["general_E"].get("service_accrual", {})
    check("service_accrual" in plans["general_E"], "Plan E has service_accrual")
    check(sa.get("full_rate_years") == 35, f"Plan E full_rate_years = 35, got {sa.get('full_rate_years')}")
    check(sa.get("reduced_rate_multiplier") == 0.5, f"Plan E reduced multiplier = 0.5, got {sa.get('reduced_rate_multiplier')}")
    check(sa.get("max_benefit_pct_of_fac") == 80, f"Plan E service_accrual max = 80%, got {sa.get('max_benefit_pct_of_fac')}")
    # Verify half-rate reproduces official table: 36yr @ 65 = 71.00%
    f65 = fe.get("65", 0)
    calc_36 = 35 * f65 + 1 * (f65 * sa.get("reduced_rate_multiplier", 0))
    check(abs(calc_36 - 71.00) < 0.01, f"Plan E half-rate: 36yr@65 = 71.00%, calc={calc_36:.2f}%")
    # 45yr @ 65 = 80.00% (hits cap)
    calc_45 = min(35 * f65 + 10 * (f65 * sa.get("reduced_rate_multiplier", 0)), 80.0)
    check(abs(calc_45 - 80.00) < 0.01, f"Plan E half-rate+cap: 45yr@65 = 80.00%, calc={calc_45:.2f}%")
    # Verify max_benefit_pct_of_fac at plan level matches service_accrual
    check(plans["general_E"].get("max_benefit_pct_of_fac") == sa.get("max_benefit_pct_of_fac"),
          "Plan E max_benefit_pct consistent between plan and service_accrual")

    # Plan E factors should be lower than Plan B at same ages (noncontributory)
    for age in ["55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65"]:
        check(fe.get(age, 99) < fb.get(age, 0),
              f"Plan E factor at {age} ({fe.get(age)}) < Plan B ({fb.get(age)}) (noncontributory lower)")

    # -- Safety A: 15 ages (41-55), max 2.62 at 55 --
    fsa = get_factors("safety_A")
    check(len(fsa) == 15, f"Safety A has 15 age entries (41-55), got {len(fsa)}")
    check(fsa.get("41") == 1.2515, f"Safety A factor at 41 = 1.2515, got {fsa.get('41')}")
    check(fsa.get("50") == 2.0, f"Safety A factor at 50 = 2.0, got {fsa.get('50')}")
    check(fsa.get("55") == 2.62, f"Safety A factor at 55 = 2.62, got {fsa.get('55')}")
    # Cross-check: 20yr @ 50 = 40.00% (from official table)
    check(abs(20 * fsa.get("50", 0) - 40.00) < 0.01, "Safety A: 20yrs × 2.0% at 50 = 40.00%")
    # Cross-check: 30yr @ 55 = 78.60% (from official table, 78.59 with rounding)
    check(abs(30 * fsa.get("55", 0) - 78.60) < 0.02, "Safety A: 30yrs × 2.62% at 55 ≈ 78.60%")
    # Cross-check early ages: 25yr @ 45 = 39.025 (official 39.03)
    check(abs(25 * fsa.get("45", 0) - 39.03) < 0.02, "Safety A: 25yrs × 1.561% at 45 ≈ 39.03%")
    # Cross-check: 21yr @ 41 = 26.28 (official)
    check(abs(21 * fsa.get("41", 0) - 26.28) < 0.02, "Safety A: 21yrs × 1.2515% at 41 ≈ 26.28%")

    # -- Safety B = Safety A (same benefit formula) --
    fsb = get_factors("safety_B")
    check(len(fsb) == 15, f"Safety B has 15 age entries, got {len(fsb)}")
    for age_key in fsa:
        check(fsb.get(age_key) == fsa[age_key],
              f"Safety B factor at {age_key} matches Safety A ({fsa[age_key]})")

    # -- Safety C (PEPRA): 8 ages (50-57), clean 0.1% increments --
    fsc = get_factors("safety_C")
    check(len(fsc) == 8, f"Safety C has 8 age entries (50-57), got {len(fsc)}")
    check(fsc.get("50") == 2.0, f"Safety C factor at 50 = 2.0, got {fsc.get('50')}")
    check(fsc.get("57") == 2.7, f"Safety C factor at 57 = 2.7, got {fsc.get('57')}")
    # Cross-check: 25yr @ 55 = 62.50% (from official table)
    check(abs(25 * fsc.get("55", 0) - 62.50) < 0.01, "Safety C: 25yrs × 2.5% at 55 = 62.50%")
    # Increment consistency: 0.1 per year like Plan G
    sc_ages = sorted([int(k) for k in fsc.keys()])
    for i in range(1, len(sc_ages)):
        prev = str(sc_ages[i-1])
        curr = str(sc_ages[i])
        diff = round(fsc[curr] - fsc[prev], 4)
        check(abs(diff - 0.1) < 0.001,
              f"Safety C factor increment age {prev}→{curr} = 0.1, got {diff}")

    # -- Monotonicity for all factor tables --
    print("Factor table monotonicity (all plans)...")
    for pid in plans:
        ft = get_factors(pid)
        if not ft:
            continue
        ages_sorted = sorted([int(k) for k in ft.keys()])
        for i in range(1, len(ages_sorted)):
            prev = str(ages_sorted[i-1])
            curr = str(ages_sorted[i])
            check(ft[curr] > ft[prev],
                  f"{pid} factor monotonic: age {curr} ({ft[curr]}) > age {prev} ({ft[prev]})")

    # -- Cross-plan: Plan A 58-62 matches Plan B 55-59 (3yr offset in CERL curve) --
    print("CERL curve cross-plan consistency...")
    cerl_offset_checks = [
        ("general_A", 58, "general_B", 55),
        ("general_A", 59, "general_B", 56),
        ("general_A", 60, "general_B", 57),
        ("general_A", 61, "general_B", 58),
        ("general_A", 62, "general_B", 59),
    ]
    for pa, age_a, pb, age_b in cerl_offset_checks:
        va = get_factors(pa).get(str(age_a))
        vb = get_factors(pb).get(str(age_b))
        # These should differ due to being different formulas, but
        # Session 57b discovered Plan B ages 58-65 = Plan A ages 55-62
        pass  # cross-plan offset verified at research time

    # Plan B@58-65 should equal Plan A@55-62 (confirmed session 57b)
    for offset in range(8):
        age_b = str(58 + offset)
        age_a = str(55 + offset)
        if age_b in fb and age_a in fa:
            check(fb[age_b] == fa[age_a],
                  f"CERL curve: Plan B@{age_b} ({fb[age_b]}) = Plan A@{age_a} ({fa[age_a]})")

    # -- Safety factors > General factors at same ages (safety = higher risk premium) --
    print("Safety vs general factor comparison...")
    for age in ["50", "51", "52", "53", "54", "55"]:
        if age in fsa and age in fb:
            check(fsa[age] > fb[age],
                  f"Safety A factor at {age} ({fsa[age]}) > General B ({fb[age]})")

    # -- Version check updated for factor tables --

    # ── COLA CURRENT CHECKS ───────────────────────────────────────
    print("COLA current year checks...")
    cc = data.get("cola_current", {})
    check(cc.get("year") == 2026, "COLA current year 2026")
    check(cc.get("cpi_change_pct") == 3.0, "CPI change 3.0%")
    check(cc.get("applied_cola_rounded_pct") == 3.0, "Applied COLA 3.0%")
    check("Los Angeles" in cc.get("cpi_area", ""), "CPI area is LA")
    check(cc.get("effective_date") == "2026-04-01", "COLA effective April 1")
    check(cc.get("board_approval_date") == "2026-02-04", "Board approved Feb 4, 2026")

    # Plan awards
    awards = cc.get("plan_awards", {})
    check(len(awards) == 9, f"9 plan awards, got {len(awards)}")
    check(awards.get("general_A") == 3.0, "General A COLA award 3.0%")
    check(awards.get("safety_A") == 3.0, "Safety A COLA award 3.0%")
    for p in ["general_B", "general_C", "general_D", "general_E", "general_G", "safety_B", "safety_C"]:
        check(awards.get(p) == 2.0, f"{p} COLA award 2.0%")

    # COLA accumulation additions
    acc = cc.get("cola_accumulation_addition", {})
    check(acc.get("general_A") == 0.0, "General A no COLA accumulation (3% = max)")
    check(acc.get("safety_A") == 0.0, "Safety A no COLA accumulation (3% = max)")
    for p in ["general_B", "general_C", "general_D", "general_E", "general_G", "safety_B", "safety_C"]:
        check(acc.get(p) == 1.0, f"{p} COLA accumulation 1.0% (3.0 - 2.0)")

    # ── CROSS-PLAN CONSISTENCY CHECKS ─────────────────────────────
    print("Cross-plan consistency checks...")

    # All general plans except E should have max_benefit 100%
    for pname in ["general_A", "general_B", "general_C", "general_D", "general_G"]:
        check(plans[pname]["max_benefit_pct_of_fac"] == 100, f"{pname} max benefit 100%")
    check(plans["general_E"]["max_benefit_pct_of_fac"] == 80, "General E max benefit 80%")

    # All safety plans max benefit 100%
    for pname in ["safety_A", "safety_B", "safety_C"]:
        check(plans[pname]["max_benefit_pct_of_fac"] == 100, f"{pname} max benefit 100%")

    # All safety members not SS covered
    for pname in ["safety_A", "safety_B", "safety_C"]:
        check(plans[pname]["social_security_coverage"] == "not_covered", f"{pname} not SS covered")

    # General members have mixed SS coverage
    for pname in ["general_A", "general_B", "general_C", "general_D", "general_E", "general_G"]:
        check(plans[pname]["social_security_coverage"] == "mixed", f"{pname} SS coverage mixed")

    # Pre-PEPRA general plans (A-D) use 12-month FAC
    for pname in ["general_A", "general_B", "general_C", "general_D"]:
        check(plans[pname]["final_average_compensation"]["months"] == 12, f"{pname} FAC 12 months")

    # PEPRA plans use 36-month FAC
    for pname in ["general_G", "safety_C"]:
        check(plans[pname]["final_average_compensation"]["months"] == 36, f"{pname} FAC 36 months (PEPRA)")

    # Plan E uses 36-month FAC (noncontributory)
    check(plans["general_E"]["final_average_compensation"]["months"] == 36, "General E FAC 36 months")

    # Pre-PEPRA safety plans use 12-month FAC
    for pname in ["safety_A", "safety_B"]:
        check(plans[pname]["final_average_compensation"]["months"] == 12, f"{pname} FAC 12 months")

    # Only Plan E is noncontributory
    check(plans["general_E"]["contributory"] is False, "Only Plan E noncontributory")
    for pname in [p for p in plans if p != "general_E"]:
        check(plans[pname]["contributory"] is True, f"{pname} is contributory")

    # Only Plan E has 10-year vesting
    check(plans["general_E"]["vesting_years"] == 10, "Plan E vesting 10 years")
    for pname in [p for p in plans if p != "general_E"]:
        check(plans[pname]["vesting_years"] == 5, f"{pname} vesting 5 years")

    # Only Plans A (gen/safety) have 3% COLA max
    for pname in ["general_A", "safety_A"]:
        check(plans[pname]["cola"]["max_pct"] == 3.0, f"{pname} COLA 3%")
    for pname in ["general_B", "general_C", "general_D", "general_E", "general_G", "safety_B", "safety_C"]:
        check(plans[pname]["cola"]["max_pct"] == 2.0, f"{pname} COLA 2%")

    # Plans D and E have restricted COLA service dates
    for pname in ["general_D", "general_E"]:
        check(plans[pname]["cola"]["applies_to_all_service"] is False, f"{pname} COLA restricted")
        check(plans[pname]["cola"]["cola_service_start_date"] == "2002-06-04", f"{pname} COLA from 6/4/2002")

    # Max benefit age consistency with formula
    for pname, plan in plans.items():
        check(plan["max_benefit_age"] == plan["benefit_formula"]["max_age_factor_age"],
              f"{pname} max_benefit_age matches formula max_age_factor_age")

    # ── BENEFIT OPTIONS ───────────────────────────────────────────
    print("Benefit options checks...")
    bo = data.get("benefit_options", {})
    check("unmodified" in bo, "unmodified option present")
    check("option_2" in bo, "option_2 present")
    check("option_3" in bo, "option_3 present")
    check(len(bo) >= 5, f"at least 5 benefit options, got {len(bo)}")

    # ── RECIPROCITY ───────────────────────────────────────────────
    print("Reciprocity checks...")
    recip = data.get("reciprocity", {})
    check("CalPERS" in recip.get("reciprocal_systems", []), "CalPERS in reciprocal systems")
    check("CalSTRS" in recip.get("reciprocal_systems", []), "CalSTRS in reciprocal systems")

    # ── HEALTH BENEFITS ───────────────────────────────────────────
    print("Health benefits checks...")
    hb = data.get("health_benefits", {})
    check("tier_1" in hb, "healthcare tier 1 present")
    check("tier_2" in hb, "healthcare tier 2 present")
    check(hb.get("tier_1", {}).get("minimum_service_for_county_subsidy_years") == 10, "Tier 1 min 10 years")
    check(hb.get("tier_2", {}).get("minimum_service_for_county_subsidy_years") == 10, "Tier 2 min 10 years")

    # ── DEATH BENEFITS ────────────────────────────────────────────
    print("Death benefits checks...")
    db = data.get("death_benefits", {})
    check(db.get("burial_benefit") == 5000, "burial benefit $5,000")
    cli = db.get("county_active_life_insurance", {})
    check(cli.get("general_plans_ABCDG") == 2000, "general plans A-G life insurance $2,000")
    check(cli.get("general_plan_E") == 10000, "Plan E life insurance $10,000")

    # ── IRC LIMITS ────────────────────────────────────────────────
    print("IRC limits checks...")
    irc = data.get("irc_limits", {})
    check(irc.get("section_401a17_2026") == 350000, "IRC 401(a)(17) limit $350,000")
    check(irc.get("section_415b_2026") == 280000, "IRC 415(b) limit $280,000")
    check("RB Plan" in irc.get("replacement_benefit_plan", "") or "Replacement" in irc.get("replacement_benefit_plan", ""), "RB plan described")

    # ── PII / CONSUMER-AGNOSTIC COMPLIANCE ────────────────────────
    print("PII and consumer-agnostic compliance...")
    raw = json.dumps(data)
    pii_patterns = [r'\b\d{3}-\d{2}-\d{4}\b', r'\b\d{9}\b']  # SSN patterns
    for pat in pii_patterns:
        check(not re.search(pat, raw), f"No PII pattern: {pat}")

    # No Meridian references
    check("meridian" not in raw.lower(), "No Meridian references")
    check("engine" not in raw.lower() or "fire" in raw.lower(), "No engine references (excluding fire engine context)")

    # ── MANIFEST CHECK ────────────────────────────────────────────
    print("Manifest check...")
    mpath = os.path.join(base, "manifest.json")
    if os.path.exists(mpath):
        manifest = json.load(open(mpath))
        files = manifest.get("files", {})
        check("lacera_plans_los_angeles" in files, "lacera_plans_los_angeles in manifest")
        if "lacera_plans_los_angeles" in files:
            entry = files["lacera_plans_los_angeles"]
            check("los-angeles-county/lacera-plans.json" in entry.get("url", ""),
                  "manifest url correct")
    else:
        check(False, "manifest.json exists")

    # ── COLA HISTORY ─────────────────────────────────────────────
    print("COLA history checks...")
    ch = data.get("cola_history", {})
    check(isinstance(ch, dict), "cola_history is dict")
    check(ch.get("cpi_area") == "Los Angeles-Long Beach-Anaheim", "CPI area correct")
    check(ch.get("cpi_series") == "CPI-U All Urban Consumers", "CPI series correct")
    check(ch.get("rounding_method") == "nearest_half_percent", "rounding method specified")

    ch_years = ch.get("years", [])
    check(len(ch_years) >= 25, f"at least 25 COLA history years, got {len(ch_years)}")

    # Verify years are sorted ascending
    cola_yrs = [y["cola_year"] for y in ch_years]
    check(cola_yrs == sorted(cola_yrs), "COLA history years sorted ascending")
    check(cola_yrs[0] == 2002, f"first COLA year is 2002, got {cola_yrs[0]}")
    check(cola_yrs[-1] == 2026, f"last COLA year is 2026, got {cola_yrs[-1]}")

    # No duplicates
    check(len(cola_yrs) == len(set(cola_yrs)), "no duplicate COLA years")

    # Per-year structural and range checks
    for entry in ch_years:
        yr = entry["cola_year"]
        cpi = entry["cpi_change_pct"]
        rounded = entry["cola_rounded_pct"]
        eff = entry["effective_date"]
        pa = entry["plan_awards"]
        ae = entry["accumulation_excess"]

        # Range checks
        check(-3.0 <= cpi <= 12.0, f"{yr}: CPI {cpi} in plausible range [-3, 12]")
        check(rounded >= 0.0, f"{yr}: rounded COLA {rounded} >= 0")
        check(rounded % 0.5 == 0, f"{yr}: rounded COLA {rounded} is multiple of 0.5")

        # Rounding: nearest 0.5
        expected_rounded = round(cpi * 2) / 2
        check(abs(rounded - expected_rounded) < 0.01,
              f"{yr}: rounded {rounded} matches nearest-0.5 of CPI {cpi} (expected {expected_rounded})")

        # Plan awards capped at plan max
        check(pa["plan_a_3pct_max"] == min(rounded, 3.0),
              f"{yr}: Plan A award = min(rounded, 3.0)")
        check(pa["plan_b_2pct_max"] == min(rounded, 2.0),
              f"{yr}: Plan B award = min(rounded, 2.0)")

        # Accumulation excess = CPI - plan_max
        check(abs(ae["plan_a_3pct_max"] - (cpi - 3.0)) < 0.05,
              f"{yr}: Plan A excess = CPI - 3.0")
        check(abs(ae["plan_b_2pct_max"] - (cpi - 2.0)) < 0.05,
              f"{yr}: Plan B excess = CPI - 2.0")

        # Plan A excess is always 1.0 less than Plan B excess
        check(abs((ae["plan_b_2pct_max"] - ae["plan_a_3pct_max"]) - 1.0) < 0.05,
              f"{yr}: Plan B excess - Plan A excess = 1.0")

        # Effective date format
        check(eff == f"{yr}-04-01", f"{yr}: effective date is April 1")

        # CPI period format
        period = entry["cpi_period"]
        check(period.startswith("Dec "), f"{yr}: CPI period starts with 'Dec '")

        # Source present
        check(len(entry.get("source", "")) > 5, f"{yr}: source field present")

    # ── COLA HISTORY - Known value spot checks ────────────────────
    print("COLA history known-value spot checks...")
    yr_map = {e["cola_year"]: e for e in ch_years}

    # LACERA official values (from inserts/pages)
    known_cpi = {
        2022: 6.6, 2023: 4.9, 2024: 3.5, 2025: 3.4, 2026: 3.0
    }
    for yr, expected_cpi in known_cpi.items():
        actual = yr_map[yr]["cpi_change_pct"]
        check(abs(actual - expected_cpi) < 0.01,
              f"{yr}: CPI {actual} matches LACERA official {expected_cpi}")

    known_rounded = {
        2022: 6.5, 2023: 5.0, 2025: 3.5, 2026: 3.0
    }
    for yr, expected_r in known_rounded.items():
        actual = yr_map[yr]["cola_rounded_pct"]
        check(abs(actual - expected_r) < 0.01,
              f"{yr}: rounded {actual} matches LACERA official {expected_r}")

    # 2009: near-zero CPI year (financial crisis)
    check(yr_map[2009]["cpi_change_pct"] < 0.5,
          f"2009: CPI < 0.5% (financial crisis year)")
    check(yr_map[2009]["cola_rounded_pct"] == 0.0,
          f"2009: rounded COLA = 0.0%")

    # 2022: highest CPI in history (post-COVID inflation)
    max_cpi_year = max(ch_years, key=lambda x: x["cpi_change_pct"])
    check(max_cpi_year["cola_year"] == 2022,
          f"2022 has highest CPI ({max_cpi_year['cpi_change_pct']}%)")

    # ── COLA HISTORY - Accumulation chart cross-validation ────────
    print("COLA history accumulation cross-validation...")
    # Verify Plan B (2% max) accumulation sums match the 2025 LACERA chart
    # Chart value = sum of (CPI - 2.0) for each COLA year in the cohort range
    chart_cohorts = {
        # cohort_label: (first_cola_year, last_cola_year, chart_accumulation_apr2025)
        "4/1/06-3/31/18": (2018, 2025, 13.7),
        "4/1/18-3/31/19": (2019, 2025, 12.1),
        "4/1/19-3/31/20": (2020, 2025, 10.9),
        "4/1/20-3/31/22": (2022, 2025, 10.4),
        "4/1/22-3/31/23": (2023, 2025, 5.8),
        "4/1/23-3/31/24": (2024, 2025, 2.9),
        "4/1/24-3/31/25": (2025, 2025, 1.4),
    }
    for label, (start, end, expected_accum) in chart_cohorts.items():
        computed = sum(yr_map[y]["accumulation_excess"]["plan_b_2pct_max"]
                      for y in range(start, end + 1))
        computed = round(computed, 1)
        diff = abs(computed - expected_accum)
        check(diff <= 0.5,
              f"Cohort {label}: computed B accum {computed:.1f} vs chart {expected_accum} (diff {diff:.1f})")

    # ── COLA HISTORY - Monotonicity and trend checks ──────────────
    print("COLA history trend checks...")
    # Plan B excess should be exactly 1.0 more than Plan A excess for every year
    for entry in ch_years:
        yr = entry["cola_year"]
        a_ex = entry["accumulation_excess"]["plan_a_3pct_max"]
        b_ex = entry["accumulation_excess"]["plan_b_2pct_max"]
        check(abs(b_ex - a_ex - 1.0) < 0.05, f"{yr}: B excess - A excess == 1.0")

    # STAR Program: accumulation stayed below 20% for 2010-2021 (per ACFR)
    # For recent retirees (4/1/06-3/31/18), Plan B accum through 2021 should be < 20%
    accum_thru_2021 = sum(yr_map[y]["accumulation_excess"]["plan_b_2pct_max"]
                         for y in range(2018, 2022))
    check(accum_thru_2021 < 20.0,
          f"Plan B accum 2018-2021 = {accum_thru_2021:.1f} < 20% (STAR threshold)")

    # ── COLA HISTORY - Consistency with cola_current ──────────────
    print("COLA history / cola_current consistency...")
    cc = data.get("cola_current", {})
    latest = yr_map.get(2026, {})
    check(abs(latest.get("cpi_change_pct", 0) - cc.get("cpi_change_pct", -1)) < 0.01,
          "2026 history CPI matches cola_current CPI")
    # Plan awards should match
    cc_awards = cc.get("plan_awards", {})
    if cc_awards:
        check(abs(latest["plan_awards"]["plan_a_3pct_max"] - cc_awards.get("general_A", -1)) < 0.01,
              "2026 Plan A award matches cola_current")
        check(abs(latest["plan_awards"]["plan_b_2pct_max"] - cc_awards.get("general_B", -1)) < 0.01,
              "2026 Plan B award matches cola_current")
    # Accumulation additions should match
    cc_accum = cc.get("cola_accumulation_addition", {})
    if cc_accum:
        check(abs(latest["accumulation_excess"]["plan_a_3pct_max"] - cc_accum.get("general_A", -1)) < 0.01,
              "2026 Plan A accum excess matches cola_current")
        check(abs(latest["accumulation_excess"]["plan_b_2pct_max"] - cc_accum.get("general_B", -1)) < 0.01,
              "2026 Plan B accum excess matches cola_current")

    # ── NOTES ─────────────────────────────────────────────────────
    print("Notes checks...")
    notes = data.get("notes", [])
    check(len(notes) >= 5, f"at least 5 notes, got {len(notes)}")
    notes_text = " ".join(notes).lower()
    check("1937" in notes_text, "notes mention 1937 Act")
    check("pepra" in notes_text, "notes mention PEPRA")
    check("cola" in notes_text, "notes mention COLA")
    check("star" in notes_text, "notes mention STAR COLA")

    # ── SUMMARY ───────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"LACERA VALIDATION: {PASS + FAIL} checks | PASS: {PASS} | FAIL: {FAIL}")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
