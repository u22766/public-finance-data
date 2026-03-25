#!/usr/bin/env python3
"""
Validation suite for ERS (Employees Retirement System of Texas) plans data.
File: states/texas/ers-plans.json
"""

import json
import sys
import os

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_FILE = os.path.join(REPO_ROOT, "states", "texas", "ers-plans.json")

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


def test_top_level(d):
    required = [
        "systemName", "systemAbbreviation", "version", "last_updated",
        "jurisdiction", "established", "totalMembers", "coverage",
        "socialSecurity", "vesting", "contributions", "retirementGroups",
        "cola", "lecos", "retirementInsurance", "supplementalSavings",
        "funding", "sources"
    ]
    for f in required:
        check(f in d, f"Missing top-level field: {f}")
    check(d.get("systemName") == "Employees Retirement System of Texas",
          "systemName mismatch")
    check(d.get("systemAbbreviation") == "ERS", "systemAbbreviation must be ERS")
    check(d.get("established") == 1947, "established must be 1947")
    check(d.get("version") == "2026.1", "version must be 2026.1")
    check(d.get("last_updated") == "2026-03-24", "last_updated must be 2026-03-24")


def test_jurisdiction(d):
    j = d.get("jurisdiction", {})
    check(j.get("state") == "TX", "jurisdiction.state must be TX")
    check(j.get("level") == "state", "jurisdiction.level must be state")
    check(j.get("name") == "Texas", "jurisdiction.name must be Texas")
    check(j.get("type") == "statewide_public_employee_pension",
          "jurisdiction.type mismatch")


def test_social_security(d):
    ss = d.get("socialSecurity", {})
    check(ss.get("covered") is True, "socialSecurity.covered must be True (TX ERS SS-covered)")
    check("note" in ss, "socialSecurity must have note")
    check("source" in ss, "socialSecurity must have source")


def test_vesting(d):
    v = d.get("vesting", {})
    check(v.get("regularAccount_years") == 5, "vesting.regularAccount_years must be 5")
    check(v.get("lecoSupplementalAccount_years") == 20,
          "vesting.lecoSupplementalAccount_years must be 20")
    check("note" in v, "vesting must have note")
    check("source" in v, "vesting must have source")


def test_contributions(d):
    c = d.get("contributions", {})
    check("groups1to3" in c, "contributions must have groups1to3")
    check("group4" in c, "contributions must have group4")
    check("lecos" in c, "contributions must have lecos")
    check("source" in c, "contributions must have source")

    g123 = c.get("groups1to3", {})
    check(g123.get("memberRate") == 0.095,
          "groups1to3 memberRate must be 0.095 (9.5%)")
    check(g123.get("stateAndAgencyRate") == 0.10,
          "groups1to3 stateAndAgencyRate must be 0.10")

    g4 = c.get("group4", {})
    check(g4.get("memberRate") == 0.06,
          "group4 memberRate must be 0.06 (6%)")
    check(g4.get("stateAndAgencyRate") == 0.10,
          "group4 stateAndAgencyRate must be 0.10")
    check(g4.get("stateMatchAtRetirement") == 1.50,
          "group4 stateMatchAtRetirement must be 1.50 (150%)")

    le = c.get("lecos", {})
    check(le.get("additionalStateRate_groups1to3") == 0.0175,
          "lecos additionalStateRate_groups1to3 must be 0.0175")
    check(le.get("additionalMemberRate_group4") == 0.02,
          "lecos additionalMemberRate_group4 must be 0.02")
    check(le.get("additionalStateMatchAtRetirement_group4") == 3.00,
          "lecos group4 state match must be 3.00 (300%)")


def test_retirement_groups_structure(d):
    rg = d.get("retirementGroups", {})
    check("overview" in rg, "retirementGroups must have overview")
    for g in ["group1", "group2", "group3", "group4"]:
        check(g in rg, f"retirementGroups must have {g}")


def test_hire_ranges(d):
    rg = d.get("retirementGroups", {})
    check("Before September 1, 2009" in rg.get("group1", {}).get("hireRange", ""),
          "group1 hireRange must reference Before September 1, 2009")
    check("September 1, 2009" in rg.get("group2", {}).get("hireRange", ""),
          "group2 hireRange must reference September 1, 2009")
    check("September 1, 2013" in rg.get("group3", {}).get("hireRange", ""),
          "group3 hireRange must reference September 1, 2013")
    check("September 1, 2022" in rg.get("group4", {}).get("hireRange", ""),
          "group4 hireRange must reference September 1, 2022")


def test_groups_1_2_3_structure(d):
    rg = d.get("retirementGroups", {})
    for gname in ["group1", "group2", "group3"]:
        g = rg.get(gname, {})
        check(g.get("planType") == "defined_benefit",
              f"{gname} planType must be defined_benefit")
        check("finalAverageSalary" in g, f"{gname} must have finalAverageSalary")
        check("formula" in g, f"{gname} must have formula")
        check("retirementEligibility" in g, f"{gname} must have retirementEligibility")
        check("source" in g, f"{gname} must have source")

        fas = g.get("finalAverageSalary", {})
        check("months" in fas, f"{gname} finalAverageSalary must have months")
        check("method" in fas, f"{gname} finalAverageSalary must have method")
        check("components" in fas, f"{gname} finalAverageSalary must have components")
        check(isinstance(fas.get("components"), list),
              f"{gname} finalAverageSalary.components must be a list")
        check(len(fas.get("components", [])) >= 3,
              f"{gname} finalAverageSalary.components must have at least 3 entries")

        formula = g.get("formula", {})
        check(formula.get("multiplierStandard") == 0.023,
              f"{gname} formula.multiplierStandard must be 0.023")
        check(formula.get("multiplierLECO") == 0.028,
              f"{gname} formula.multiplierLECO must be 0.028")
        check(formula.get("lecoThreshold_years") == 20,
              f"{gname} formula.lecoThreshold_years must be 20")
        check("maxAnnuity" in formula, f"{gname} formula must have maxAnnuity")

        elig = g.get("retirementEligibility", {})
        check("ruleOf80" in elig, f"{gname} retirementEligibility must have ruleOf80")
        ro80 = elig.get("ruleOf80", {})
        check(ro80.get("rule") == "age_plus_service_equals_80",
              f"{gname} ruleOf80.rule must be age_plus_service_equals_80")
        check("minimumService_years" in ro80,
              f"{gname} ruleOf80 must have minimumService_years")


def test_fas_months(d):
    """Verify FAS periods become more punitive from Group 1 to Group 3."""
    rg = d.get("retirementGroups", {})
    fas1 = rg["group1"]["finalAverageSalary"]["months"]
    fas2 = rg["group2"]["finalAverageSalary"]["months"]
    fas3 = rg["group3"]["finalAverageSalary"]["months"]

    check(fas1 == 36, "Group 1 FAS must be 36 months")
    check(fas2 == 48, "Group 2 FAS must be 48 months")
    check(fas3 == 60, "Group 3 FAS must be 60 months")
    check(fas1 < fas2 < fas3,
          "FAS period must increase from Group 1 to Group 3 (less favorable for newer members)")


def test_early_retirement_reductions(d):
    rg = d.get("retirementGroups", {})

    # Group 1 — no reduction
    g1_elig = rg["group1"]["retirementEligibility"]
    check(g1_elig.get("earlyRetirementReduction") is None,
          "Group 1 earlyRetirementReduction must be null")

    # Group 2 — 5%/yr under 60, capped at 25%
    g2_red = rg["group2"]["retirementEligibility"].get("earlyRetirementReduction", {})
    check(g2_red.get("applies") is True,
          "Group 2 earlyRetirementReduction.applies must be True")
    check(g2_red.get("threshold_age") == 60,
          "Group 2 earlyRetirementReduction.threshold_age must be 60")
    check(g2_red.get("reductionPerYearUnder") == 0.05,
          "Group 2 reductionPerYearUnder must be 0.05")
    check(g2_red.get("cap") == 0.25,
          "Group 2 early retirement reduction cap must be 0.25 (25%)")

    # Group 3 — 5%/yr under 62, NO cap
    g3_red = rg["group3"]["retirementEligibility"].get("earlyRetirementReduction", {})
    check(g3_red.get("applies") is True,
          "Group 3 earlyRetirementReduction.applies must be True")
    check(g3_red.get("threshold_age") == 62,
          "Group 3 earlyRetirementReduction.threshold_age must be 62")
    check(g3_red.get("reductionPerYearUnder") == 0.05,
          "Group 3 reductionPerYearUnder must be 0.05")
    check(g3_red.get("cap") is None,
          "Group 3 early retirement reduction cap must be null (no cap)")


def test_group4(d):
    g4 = d.get("retirementGroups", {}).get("group4", {})
    check(g4.get("planType") == "cash_balance",
          "group4 planType must be cash_balance")
    check("accountMechanics" in g4, "group4 must have accountMechanics")
    check("retirementEligibility" in g4, "group4 must have retirementEligibility")
    check("gainSharingRetireesNote" in g4, "group4 must have gainSharingRetireesNote")
    check("lecos_group4" in g4, "group4 must have lecos_group4")
    check("source" in g4, "group4 must have source")

    acct = g4.get("accountMechanics", {})
    check(acct.get("memberContributionRate") == 0.06,
          "group4 accountMechanics.memberContributionRate must be 0.06")
    check(acct.get("guaranteedAnnualInterest") == 0.04,
          "group4 guaranteedAnnualInterest must be 0.04 (4%)")
    check("gainSharing" in acct, "group4 accountMechanics must have gainSharing")

    gs = acct.get("gainSharing", {})
    check(gs.get("available") is True, "group4 gainSharing.available must be True")
    check(gs.get("maxAdditionalInterest") == 0.03,
          "group4 gainSharing.maxAdditionalInterest must be 0.03 (3%)")
    check("fy2025GainShare" in gs, "group4 gainSharing must have fy2025GainShare")
    check(gs.get("fy2025GainShare") == 0.0296,
          "group4 gainSharing.fy2025GainShare must be 0.0296")

    match = acct.get("stateMatchAtRetirement", {})
    check(match.get("regularAccount") == 1.50,
          "group4 stateMatchAtRetirement.regularAccount must be 1.50 (150%)")

    elig = g4.get("retirementEligibility", {})
    check("ruleOf80" in elig, "group4 retirementEligibility must have ruleOf80")
    ro80 = elig.get("ruleOf80", {})
    check(ro80.get("minimumService_years") == 5,
          "group4 ruleOf80 minimumService_years must be 5")

    lecos4 = g4.get("lecos_group4", {})
    check(lecos4.get("additionalMemberContributionRate") == 0.02,
          "lecos_group4 additionalMemberContributionRate must be 0.02")
    check(lecos4.get("stateMatchAtRetirement_lecoAccount") == 3.00,
          "lecos_group4 stateMatchAtRetirement_lecoAccount must be 3.00 (300%)")
    check(lecos4.get("vestingLecoAccount_years") == 20,
          "lecos_group4 vestingLecoAccount_years must be 20")


def test_cola(d):
    cola = d.get("cola", {})
    check("groups1to3" in cola, "cola must have groups1to3")
    check("group4" in cola, "cola must have group4")
    check("source" in cola, "cola must have source")

    c123 = cola.get("groups1to3", {})
    check(c123.get("guaranteed") is False,
          "cola.groups1to3.guaranteed must be False")
    check(c123.get("type") == "legislative_discretionary",
          "cola.groups1to3.type must be legislative_discretionary")

    c4 = cola.get("group4", {})
    check(c4.get("type") == "gain_sharing",
          "cola.group4.type must be gain_sharing")
    check(c4.get("guaranteed") is False,
          "cola.group4.guaranteed must be False")
    check(c4.get("maxAnnualIncrease") == 0.03,
          "cola.group4.maxAnnualIncrease must be 0.03")
    check(c4.get("permanent") is True,
          "cola.group4.permanent must be True")
    check(c4.get("fy2025GainShare") == 0.0296,
          "cola.group4.fy2025GainShare must be 0.0296")


def test_lecos(d):
    le = d.get("lecos", {})
    check("overview" in le, "lecos must have overview")
    check("eligibility" in le, "lecos must have eligibility")
    check("groups1to3Formula" in le, "lecos must have groups1to3Formula")
    check("additionalStateContribution_groups1to3" in le,
          "lecos must have additionalStateContribution_groups1to3")
    check(le.get("additionalStateContribution_groups1to3") == 0.0175,
          "lecos additionalStateContribution_groups1to3 must be 0.0175")
    check("fundedStatus_aug2024" in le, "lecos must have fundedStatus_aug2024")

    fs = le.get("fundedStatus_aug2024", {})
    check(fs.get("fundedRatio") == 1.015,
          "lecos fundedStatus fundedRatio must be 1.015 (101.5%)")
    check("source" in fs, "lecos fundedStatus_aug2024 must have source")


def test_retirement_insurance(d):
    ri = d.get("retirementInsurance", {})
    check("eligibilityRequirement" in ri,
          "retirementInsurance must have eligibilityRequirement")
    check("tieredStatePremiumContribution" in ri,
          "retirementInsurance must have tieredStatePremiumContribution")
    check("allGroupsSameInsuranceRules" in ri,
          "retirementInsurance must have allGroupsSameInsuranceRules")
    check(ri.get("allGroupsSameInsuranceRules") is True,
          "retirementInsurance.allGroupsSameInsuranceRules must be True")

    tier = ri.get("tieredStatePremiumContribution", {})
    check(tier.get("years10to14") == 0.50,
          "tieredStatePremiumContribution.years10to14 must be 0.50")
    check(tier.get("years15to19") == 0.75,
          "tieredStatePremiumContribution.years15to19 must be 0.75")
    check(tier.get("years20plus") == 1.00,
          "tieredStatePremiumContribution.years20plus must be 1.00")
    check("source" in tier, "tieredStatePremiumContribution must have source")


def test_supplemental_savings(d):
    ss = d.get("supplementalSavings", {})
    check("name" in ss, "supplementalSavings must have name")
    check("Texa$aver" in ss.get("name", ""),
          "supplementalSavings name must reference Texa$aver")
    check("types" in ss, "supplementalSavings must have types")
    check("401(k)" in ss.get("types", []),
          "supplementalSavings types must include 401(k)")
    check("457(b)" in ss.get("types", []),
          "supplementalSavings types must include 457(b)")
    check("autoEnrollment" in ss, "supplementalSavings must have autoEnrollment")
    ae = ss.get("autoEnrollment", {})
    check(ae.get("applies") is True, "autoEnrollment.applies must be True")
    check(ae.get("defaultRate") == 0.01, "autoEnrollment.defaultRate must be 0.01")


def test_funding(d):
    fund = d.get("funding", {})
    check("trustFund" in fund, "funding must have trustFund")
    tf = fund.get("trustFund", {})
    check("fy2024Return" in tf, "trustFund must have fy2024Return")
    check("assumedRateOfReturn" in tf, "trustFund must have assumedRateOfReturn")
    check(tf.get("assumedRateOfReturn") == 0.07,
          "trustFund assumedRateOfReturn must be 0.07 (7%)")
    check(tf.get("fy2024Return") == 0.1251,
          "trustFund fy2024Return must be 0.1251 (12.51%)")
    check("targetFullyFunded" in tf, "trustFund must have targetFullyFunded")
    check("2054" in str(tf.get("targetFullyFunded", "")),
          "trustFund targetFullyFunded must reference 2054")
    check("source" in tf, "trustFund must have source")


def test_total_members(d):
    tm = d.get("totalMembers", {})
    check("activeEmployees" in tm, "totalMembers must have activeEmployees")
    check("retireesBeneficiaries" in tm, "totalMembers must have retireesBeneficiaries")
    check(tm.get("activeEmployees") > 100000,
          "activeEmployees must be > 100,000")
    check("source" in tm, "totalMembers must have source")


def test_sources(d):
    sources = d.get("sources", [])
    check(isinstance(sources, list), "sources must be a list")
    check(len(sources) >= 8, "sources must have at least 8 entries")
    for i, s in enumerate(sources):
        check("title" in s, f"sources[{i}] must have title")
        check("url" in s, f"sources[{i}] must have url")
        check("accessed" in s, f"sources[{i}] must have accessed")
        check(s.get("url", "").startswith("http"),
              f"sources[{i}] url must start with http")


def test_no_consumer_references(d):
    text = json.dumps(d)
    forbidden = ["meridian", "engine_", "engine usage", "consumer_id"]
    for term in forbidden:
        check(term.lower() not in text.lower(),
              f"Consumer reference found: '{term}'")


def test_group4_differs_from_group1(d):
    """Group 4 should have lower contribution rate than Groups 1-3."""
    c = d.get("contributions", {})
    check(c["group4"]["memberRate"] < c["groups1to3"]["memberRate"],
          "Group 4 member contribution rate must be less than Groups 1-3")

    rg = d.get("retirementGroups", {})
    check(rg["group4"]["planType"] != rg["group1"]["planType"],
          "Group 4 planType must differ from Group 1 (cash_balance vs defined_benefit)")


def test_coverage(d):
    pops = d.get("coverage", {}).get("populations", [])
    check(len(pops) >= 3, "coverage.populations must have at least 3 entries")
    excl = d.get("coverage", {}).get("exclusions", [])
    check(len(excl) >= 2, "coverage.exclusions must have at least 2 entries")
    excl_text = " ".join(excl)
    check("TRS" in excl_text or "higher education" in excl_text,
          "coverage.exclusions must mention TRS/higher education")
    check(d.get("coverage", {}).get("mandatory") is True,
          "coverage.mandatory must be True")


def main():
    print(f"Loading: {DATA_FILE}")
    try:
        d = load_data()
    except Exception as e:
        print(f"FATAL: Could not load data file: {e}")
        sys.exit(1)

    test_top_level(d)
    test_jurisdiction(d)
    test_social_security(d)
    test_vesting(d)
    test_contributions(d)
    test_retirement_groups_structure(d)
    test_hire_ranges(d)
    test_groups_1_2_3_structure(d)
    test_fas_months(d)
    test_early_retirement_reductions(d)
    test_group4(d)
    test_cola(d)
    test_lecos(d)
    test_retirement_insurance(d)
    test_supplemental_savings(d)
    test_funding(d)
    test_total_members(d)
    test_sources(d)
    test_no_consumer_references(d)
    test_group4_differs_from_group1(d)
    test_coverage(d)

    print(f"\n{'='*55}")
    if errors:
        print(f"FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n{checks - len(errors)}/{checks} checks passed")
        sys.exit(1)
    else:
        print(f"PASSED — {checks}/{checks} checks passed ✅")
        print(f"{'='*55}")


if __name__ == "__main__":
    main()
