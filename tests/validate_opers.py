#!/usr/bin/env python3
"""
Validation suite for OPERS (Ohio Public Employees Retirement System) plans data.
File: states/ohio/opers-plans.json
"""

import json
import sys
import os

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_FILE = os.path.join(REPO_ROOT, "states", "ohio", "opers-plans.json")

errors = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)


def test_top_level_structure(d):
    """Top-level required fields."""
    required = [
        "systemName", "systemAbbreviation", "version", "last_updated",
        "jurisdiction", "established", "totalMembers", "coverage",
        "socialSecurity", "vesting", "contributions", "cola", "plans",
        "healthCare", "funding", "sources"
    ]
    for field in required:
        check(field in d, f"Missing top-level field: {field}")

    check(d.get("systemName") == "Ohio Public Employees Retirement System",
          "systemName mismatch")
    check(d.get("systemAbbreviation") == "OPERS", "systemAbbreviation must be OPERS")
    check(d.get("established") == 1935, "established year must be 1935")


def test_jurisdiction(d):
    j = d.get("jurisdiction", {})
    check(j.get("state") == "OH", "jurisdiction.state must be OH")
    check(j.get("level") == "state", "jurisdiction.level must be state")
    check(j.get("name") == "Ohio", "jurisdiction.name must be Ohio")
    check(j.get("type") == "statewide_public_employee_pension",
          "jurisdiction.type must be statewide_public_employee_pension")


def test_version(d):
    check(d.get("version") == "2026.1", "version must be 2026.1")
    check(d.get("last_updated") == "2026-03-24", "last_updated must be 2026-03-24")


def test_social_security(d):
    ss = d.get("socialSecurity", {})
    check(ss.get("covered") is False, "socialSecurity.covered must be False")
    check(ss.get("medicareOnly") is True, "socialSecurity.medicareOnly must be True")
    check("note" in ss, "socialSecurity must have note")
    check("source" in ss, "socialSecurity must have source")


def test_vesting(d):
    v = d.get("vesting", {})
    check(v.get("years") == 5, "vesting.years must be 5")
    check("note" in v, "vesting must have note")


def test_contributions(d):
    c = d.get("contributions", {})
    check("generalMembers" in c, "contributions must have generalMembers")
    check("lawEnforcement" in c, "contributions must have lawEnforcement")
    check("publicSafety" in c, "contributions must have publicSafety")
    check("source" in c, "contributions must have source")

    gm = c.get("generalMembers", {})
    check(gm.get("memberRate") == 0.10, "generalMembers memberRate must be 0.10")
    check(gm.get("employerRate") == 0.14, "generalMembers employerRate must be 0.14")

    le = c.get("lawEnforcement", {})
    check(le.get("memberRate") == 0.13, "lawEnforcement memberRate must be 0.13")
    check(le.get("employerRate") == 0.181, "lawEnforcement employerRate must be 0.181")

    ps = c.get("publicSafety", {})
    check(ps.get("memberRate") == 0.12, "publicSafety memberRate must be 0.12")
    check(ps.get("employerRate") == 0.181, "publicSafety employerRate must be 0.181")


def test_compensation_limits(d):
    cl = d.get("compensationLimits", {})
    check("hiredFrom1994" in cl, "compensationLimits must have hiredFrom1994")
    check("hiredBefore1994" in cl, "compensationLimits must have hiredBefore1994")

    h94 = cl.get("hiredFrom1994", {})
    check(h94.get("annualLimit") == 360000,
          "hiredFrom1994 annualLimit must be 360000")

    hpre94 = cl.get("hiredBefore1994", {})
    check(hpre94.get("annualLimit") == 535000,
          "hiredBefore1994 annualLimit must be 535000")


def test_cola(d):
    cola = d.get("cola", {})
    check(cola.get("type") == "cpi_based", "cola.type must be cpi_based")
    check(cola.get("index") == "CPI-W", "cola.index must be CPI-W")
    check(cola.get("cap") == 0.03, "cola.cap must be 0.03")
    check(cola.get("floor") == 0.00, "cola.floor must be 0.00")
    check("timing" in cola, "cola must have timing")
    check("source" in cola, "cola must have source")


def test_plans_structure(d):
    plans = d.get("plans", {})
    check("overview" in plans, "plans must have overview")
    check("traditionalPensionPlan" in plans, "plans must have traditionalPensionPlan")
    check("memberDirectedPlan" in plans, "plans must have memberDirectedPlan")
    check("combinedPlan" in plans, "plans must have combinedPlan")


def test_traditional_plan(d):
    tp = d.get("plans", {}).get("traditionalPensionPlan", {})
    check(tp.get("planType") == "defined_benefit", "Traditional plan type must be defined_benefit")
    check(tp.get("status", "").startswith("OPEN"), "Traditional plan must be OPEN")
    check("memberGroups" in tp, "traditionalPensionPlan must have memberGroups")
    check("paymentOptions" in tp, "traditionalPensionPlan must have paymentOptions")
    check("disabilityBenefits" in tp, "traditionalPensionPlan must have disabilityBenefits")
    check("survivorBenefits" in tp, "traditionalPensionPlan must have survivorBenefits")
    check("lawEnforcementPublicSafety" in tp,
          "traditionalPensionPlan must have lawEnforcementPublicSafety note")


def test_member_groups(d):
    mg = d.get("plans", {}).get("traditionalPensionPlan", {}).get("memberGroups", {})
    for grp in ["groupA", "groupB", "groupC"]:
        g = mg.get(grp, {})
        check(grp in mg, f"memberGroups must have {grp}")
        check("finalAverageSalary" in g, f"{grp} must have finalAverageSalary")
        check("formula" in g, f"{grp} must have formula")
        check("retirementEligibility" in g, f"{grp} must have retirementEligibility")

        fas = g.get("finalAverageSalary", {})
        check("years" in fas, f"{grp} finalAverageSalary must have years")
        check("method" in fas, f"{grp} finalAverageSalary must have method")

        formula = g.get("formula", {})
        check("multiplierBase" in formula, f"{grp} formula must have multiplierBase")
        check("multiplierEnhanced" in formula, f"{grp} formula must have multiplierEnhanced")
        check("enhancedThreshold_years" in formula,
              f"{grp} formula must have enhancedThreshold_years")

        elig = g.get("retirementEligibility", {})
        check("unreduced" in elig, f"{grp} retirementEligibility must have unreduced")
        check("reduced" in elig, f"{grp} retirementEligibility must have reduced")

        # Each unreduced/reduced entry must have rule, age/service
        for rule in elig.get("unreduced", []):
            check("rule" in rule, f"{grp} unreduced entry must have rule")
            check("service" in rule, f"{grp} unreduced entry must have service")

        for rule in elig.get("reduced", []):
            check("rule" in rule, f"{grp} reduced entry must have rule")
            check("service" in rule, f"{grp} reduced entry must have service")


def test_group_a_specifics(d):
    ga = d["plans"]["traditionalPensionPlan"]["memberGroups"]["groupA"]

    # FAS: 3 years
    check(ga["finalAverageSalary"]["years"] == 3, "Group A FAS must be 3 years")
    check(ga["finalAverageSalary"]["method"] == "highest_3_years",
          "Group A FAS method must be highest_3_years")

    # Formula: 2.2% base, 2.5% enhanced, threshold 30
    f = ga["formula"]
    check(f["multiplierBase"] == 0.022, "Group A multiplierBase must be 0.022")
    check(f["multiplierEnhanced"] == 0.025, "Group A multiplierEnhanced must be 0.025")
    check(f["enhancedThreshold_years"] == 30,
          "Group A enhancedThreshold_years must be 30")

    # Eligibility: unreduced any/30 or 65/5
    elig = ga["retirementEligibility"]
    unreduced_rules = {r["rule"] for r in elig["unreduced"]}
    check("any_age_30_years" in unreduced_rules,
          "Group A must have unreduced any_age_30_years rule")
    check("age_65_5_years" in unreduced_rules,
          "Group A must have unreduced age_65_5_years rule")

    # Verify service/age values
    any30 = next((r for r in elig["unreduced"] if r["rule"] == "any_age_30_years"), None)
    check(any30 is not None and any30.get("service") == 30,
          "Group A any_age_30_years service must be 30")
    check(any30 is not None and any30.get("age") is None,
          "Group A any_age_30_years age must be null")

    age65 = next((r for r in elig["unreduced"] if r["rule"] == "age_65_5_years"), None)
    check(age65 is not None and age65.get("age") == 65,
          "Group A age_65_5_years age must be 65")
    check(age65 is not None and age65.get("service") == 5,
          "Group A age_65_5_years service must be 5")

    # Reduced: 55/25 and 60/5
    reduced_rules = {r["rule"] for r in elig["reduced"]}
    check("age_55_25_years" in reduced_rules,
          "Group A must have reduced age_55_25_years rule")
    check("age_60_5_years" in reduced_rules,
          "Group A must have reduced age_60_5_years rule")


def test_group_b_specifics(d):
    gb = d["plans"]["traditionalPensionPlan"]["memberGroups"]["groupB"]

    # FAS: 3 years
    check(gb["finalAverageSalary"]["years"] == 3, "Group B FAS must be 3 years")

    # Formula: same thresholds as A
    f = gb["formula"]
    check(f["multiplierBase"] == 0.022, "Group B multiplierBase must be 0.022")
    check(f["multiplierEnhanced"] == 0.025, "Group B multiplierEnhanced must be 0.025")
    check(f["enhancedThreshold_years"] == 30,
          "Group B enhancedThreshold_years must be 30")

    # Eligibility: unreduced any/32, 52/31, 66/5
    elig = gb["retirementEligibility"]
    unreduced_rules = {r["rule"] for r in elig["unreduced"]}
    check("any_age_32_years" in unreduced_rules,
          "Group B must have unreduced any_age_32_years rule")
    check("age_52_31_years" in unreduced_rules,
          "Group B must have unreduced age_52_31_years rule")
    check("age_66_5_years" in unreduced_rules,
          "Group B must have unreduced age_66_5_years rule")

    # Verify values
    any32 = next((r for r in elig["unreduced"] if r["rule"] == "any_age_32_years"), None)
    check(any32 is not None and any32.get("service") == 32,
          "Group B any_age_32_years service must be 32")

    age52 = next((r for r in elig["unreduced"] if r["rule"] == "age_52_31_years"), None)
    check(age52 is not None and age52.get("age") == 52,
          "Group B age_52_31_years age must be 52")
    check(age52 is not None and age52.get("service") == 31,
          "Group B age_52_31_years service must be 31")

    # Reduced same as A
    reduced_rules = {r["rule"] for r in elig["reduced"]}
    check("age_55_25_years" in reduced_rules,
          "Group B must have reduced age_55_25_years")
    check("age_60_5_years" in reduced_rules,
          "Group B must have reduced age_60_5_years")


def test_group_c_specifics(d):
    gc = d["plans"]["traditionalPensionPlan"]["memberGroups"]["groupC"]

    # FAS: 5 years
    check(gc["finalAverageSalary"]["years"] == 5, "Group C FAS must be 5 years")
    check(gc["finalAverageSalary"]["method"] == "highest_5_years",
          "Group C FAS method must be highest_5_years")

    # Formula: 2.2% base, 2.5% enhanced, threshold 35
    f = gc["formula"]
    check(f["multiplierBase"] == 0.022, "Group C multiplierBase must be 0.022")
    check(f["multiplierEnhanced"] == 0.025, "Group C multiplierEnhanced must be 0.025")
    check(f["enhancedThreshold_years"] == 35,
          "Group C enhancedThreshold_years must be 35")

    # Eligibility: unreduced 55/32 or 67/5
    elig = gc["retirementEligibility"]
    unreduced_rules = {r["rule"] for r in elig["unreduced"]}
    check("age_55_32_years" in unreduced_rules,
          "Group C must have unreduced age_55_32_years")
    check("age_67_5_years" in unreduced_rules,
          "Group C must have unreduced age_67_5_years")

    age55 = next((r for r in elig["unreduced"] if r["rule"] == "age_55_32_years"), None)
    check(age55 is not None and age55.get("age") == 55,
          "Group C age_55_32_years age must be 55")
    check(age55 is not None and age55.get("service") == 32,
          "Group C age_55_32_years service must be 32")

    age67 = next((r for r in elig["unreduced"] if r["rule"] == "age_67_5_years"), None)
    check(age67 is not None and age67.get("age") == 67,
          "Group C age_67_5_years age must be 67")
    check(age67 is not None and age67.get("service") == 5,
          "Group C age_67_5_years service must be 5")

    # Reduced: 57/25 and 62/5
    reduced_rules = {r["rule"] for r in elig["reduced"]}
    check("age_57_25_years" in reduced_rules,
          "Group C must have reduced age_57_25_years")
    check("age_62_5_years" in reduced_rules,
          "Group C must have reduced age_62_5_years")

    age57 = next((r for r in elig["reduced"] if r["rule"] == "age_57_25_years"), None)
    check(age57 is not None and age57.get("age") == 57,
          "Group C age_57_25_years age must be 57")
    check(age57 is not None and age57.get("service") == 25,
          "Group C age_57_25_years service must be 25")


def test_group_c_differs_from_a(d):
    """Group C must be less generous than Group A in measurable ways."""
    mg = d["plans"]["traditionalPensionPlan"]["memberGroups"]
    ga = mg["groupA"]
    gc = mg["groupC"]

    check(gc["finalAverageSalary"]["years"] > ga["finalAverageSalary"]["years"],
          "Group C FAS years must be greater than Group A (less favorable)")
    check(gc["formula"]["enhancedThreshold_years"] > ga["formula"]["enhancedThreshold_years"],
          "Group C enhanced threshold must be greater than Group A")


def test_plop(d):
    plop = d.get("plans", {}).get("traditionalPensionPlan", {}) \
             .get("paymentOptions", {}).get("plop", {})
    check("name" in plop, "PLOP must have name")
    check("abbreviation" in plop, "PLOP must have abbreviation")
    check(plop.get("abbreviation") == "PLOP", "PLOP abbreviation must be PLOP")
    check("range" in plop, "PLOP must have range")
    check("effect" in plop, "PLOP must have effect")


def test_member_directed_plan(d):
    mdp = d.get("plans", {}).get("memberDirectedPlan", {})
    check(mdp.get("planType") == "defined_contribution",
          "memberDirectedPlan planType must be defined_contribution")
    check(mdp.get("status") == "OPEN", "memberDirectedPlan status must be OPEN")
    check("retirementEligibility" in mdp, "memberDirectedPlan must have retirementEligibility")


def test_combined_plan(d):
    cp = d.get("plans", {}).get("combinedPlan", {})
    check(cp.get("planType") == "hybrid", "combinedPlan planType must be hybrid")
    check("CLOSED" in cp.get("status", ""),
          "combinedPlan status must indicate CLOSED")
    check("2022" in cp.get("status", ""),
          "combinedPlan status must reference 2022 closure date")


def test_health_care(d):
    hc = d.get("healthCare", {})
    check("overview" in hc, "healthCare must have overview")
    check("eligibility" in hc, "healthCare must have eligibility")
    check("preMedicareMembers" in hc, "healthCare must have preMedicareMembers")
    check("medicareEligibleMembers" in hc, "healthCare must have medicareEligibleMembers")
    check("qualifyingServiceTypes" in hc, "healthCare must have qualifyingServiceTypes")
    check("source" in hc, "healthCare must have source")

    prem = hc.get("preMedicareMembers", {})
    check(prem.get("model") == "Health Reimbursement Arrangement (HRA)",
          "preMedicareMembers model must be HRA")
    check(prem.get("effectiveDate") == "2022-01-01",
          "preMedicareMembers effectiveDate must be 2022-01-01")

    elig = hc.get("eligibility", {})
    check("byGroup" in elig, "healthCare.eligibility must have byGroup")
    check("agingIn" in elig, "healthCare.eligibility must have agingIn")


def test_funding(d):
    funding = d.get("funding", {})
    check("fy2025" in funding, "funding must have fy2025")

    fy = funding.get("fy2025", {})
    check("investmentReturn" in fy, "fy2025 must have investmentReturn")
    check("estimatedFundedRatio" in fy, "fy2025 must have estimatedFundedRatio")
    check("assumedRateOfReturn" in fy, "fy2025 must have assumedRateOfReturn")
    check("healthCareSolvency_years" in fy, "fy2025 must have healthCareSolvency_years")
    check("source" in funding, "funding must have source")

    check(fy.get("investmentReturn") == 0.144,
          "fy2025 investmentReturn must be 0.144 (14.4%)")
    check(fy.get("assumedRateOfReturn") == 0.069,
          "fy2025 assumedRateOfReturn must be 0.069 (6.9%)")
    check(fy.get("estimatedFundedRatio") >= 0.75,
          "fy2025 estimatedFundedRatio must be at least 0.75")


def test_sources(d):
    sources = d.get("sources", [])
    check(isinstance(sources, list), "sources must be a list")
    check(len(sources) >= 5, "sources must have at least 5 entries")
    for i, s in enumerate(sources):
        check("title" in s, f"sources[{i}] must have title")
        check("url" in s, f"sources[{i}] must have url")
        check("accessed" in s, f"sources[{i}] must have accessed")
        check(s.get("url", "").startswith("http"),
              f"sources[{i}] url must start with http")


def test_no_consumer_references(d):
    """Ensure no consumer-specific references are present."""
    text = json.dumps(d)
    forbidden = ["meridian", "engine_", "engine usage", "consumer_id"]
    for term in forbidden:
        check(term.lower() not in text.lower(),
              f"Consumer reference found: '{term}'")


def test_coverage_populations(d):
    pops = d.get("coverage", {}).get("populations", [])
    check(len(pops) >= 5, "coverage.populations must have at least 5 entries")
    check(isinstance(pops, list), "coverage.populations must be a list")

    excl = d.get("coverage", {}).get("exclusions", [])
    check(len(excl) >= 2, "coverage.exclusions must have at least 2 entries")
    # STRS Ohio should be excluded
    excl_text = " ".join(excl)
    check("STRS" in excl_text, "coverage.exclusions must mention STRS Ohio")


def main():
    print(f"Loading: {DATA_FILE}")
    try:
        d = load_data()
    except Exception as e:
        print(f"FATAL: Could not load data file: {e}")
        sys.exit(1)

    test_top_level_structure(d)
    test_jurisdiction(d)
    test_version(d)
    test_social_security(d)
    test_vesting(d)
    test_contributions(d)
    test_compensation_limits(d)
    test_cola(d)
    test_plans_structure(d)
    test_traditional_plan(d)
    test_member_groups(d)
    test_group_a_specifics(d)
    test_group_b_specifics(d)
    test_group_c_specifics(d)
    test_group_c_differs_from_a(d)
    test_plop(d)
    test_member_directed_plan(d)
    test_combined_plan(d)
    test_health_care(d)
    test_funding(d)
    test_sources(d)
    test_no_consumer_references(d)
    test_coverage_populations(d)

    print(f"\n{'='*55}")
    if errors:
        print(f"FAILED — {len(errors)} error(s) found:")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n{checks - len(errors)}/{checks} checks passed")
        sys.exit(1)
    else:
        print(f"PASSED — {checks}/{checks} checks passed ✅")
        print(f"{'='*55}")


if __name__ == "__main__":
    main()
