"""Validation suite for Foreign Service retirement rules file."""
import json
import os
import sys

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {name}" + (f" — {detail}" if detail else ""))

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fpath = os.path.join(repo, "reference", "foreign-service-retirement-rules.json")

# === File existence ===
check("FS-001-file-exists", os.path.exists(fpath), fpath)
if not os.path.exists(fpath):
    print(f"FOREIGN SERVICE VALIDATION: {passed} checks passed, {failed} failed")
    sys.exit(1 if failed else 0)

with open(fpath) as f:
    data = json.load(f)

# === Metadata ===
m = data.get("metadata", {})
check("FS-002-metadata-exists", "metadata" in data)
check("FS-003-version", m.get("version") is not None)
check("FS-004-sources", len(m.get("sources", [])) >= 5)
check("FS-005-covered-agencies", len(m.get("covered_agencies", [])) >= 5)
check("FS-006-admin-authority", "administering_authority" in m)
check("FS-007-admin-has-gtm-ret", "GTM/RET" in str(m.get("administering_authority", {})))

# === Retirement systems array ===
systems = data.get("retirement_systems", [])
check("FS-010-systems-count", len(systems) == 3, f"got {len(systems)}")

system_names = [s.get("system") for s in systems]
check("FS-011-has-fsrds", "FSRDS" in system_names)
check("FS-012-has-fsrds-offset", "FSRDS Offset" in system_names)
check("FS-013-has-fsps", "FSPS" in system_names)

# === FSRDS checks ===
fsrds = next((s for s in systems if s.get("system") == "FSRDS"), {})
check("FS-020-fsrds-multiplier", fsrds.get("multiplier_per_year_pct") == 2.0)
check("FS-021-fsrds-cap", fsrds.get("max_annuity_pct_of_high_3") == 70.0)
check("FS-022-fsrds-contrib", fsrds.get("employee_contribution_rate_pct") == 7.25)
check("FS-023-fsrds-agency-contrib", fsrds.get("agency_contribution_rate_pct") == 7.25)
check("FS-024-fsrds-no-ss", fsrds.get("social_security_coverage") == False)
check("FS-025-fsrds-no-tsp-match", fsrds.get("tsp_matching") == False)
check("FS-026-fsrds-mandatory-65", fsrds.get("mandatory_retirement_age") == 65)
check("FS-027-fsrds-cola-full-cpi", "Full CPI" in fsrds.get("cola_rule", {}).get("method", ""))
check("FS-028-fsrds-survivor-55pct", fsrds.get("survivor_benefits", {}).get("max_survivor_annuity_pct") == 55)
check("FS-029-fsrds-analogous-csrs", "CSRS" in fsrds.get("analogous_to", ""))

# FSRDS eligibility
fsrds_elig = fsrds.get("eligibility", {}).get("voluntary_immediate_unreduced", [])
check("FS-030-fsrds-50-20", any(e.get("rule") == "50/20" for e in fsrds_elig))
check("FS-031-fsrds-any-25", any(e.get("rule") == "any_age/25" for e in fsrds_elig))

# FSRDS example
fsrds_ex = fsrds.get("example", {})
check("FS-032-fsrds-example-years", fsrds_ex.get("years") == 25)
check("FS-033-fsrds-example-rate", fsrds_ex.get("multiplier_total_pct") == 50.0)
check("FS-034-fsrds-example-annuity", fsrds_ex.get("annual_annuity") == 60000)

# FSRDS high-3 includes/excludes
check("FS-035-fsrds-h3-includes", len(fsrds.get("high_3_includes", [])) >= 3)
check("FS-036-fsrds-h3-virtual-locality", any("virtual" in s.lower() for s in fsrds.get("high_3_includes", [])))
check("FS-037-fsrds-h3-excludes", len(fsrds.get("high_3_excludes", [])) >= 3)

# === FSRDS Offset checks ===
offset = next((s for s in systems if s.get("system") == "FSRDS Offset"), {})
check("FS-040-offset-multiplier", offset.get("multiplier_per_year_pct") == 2.0)
check("FS-041-offset-has-ss", offset.get("social_security_coverage") == True)
check("FS-042-offset-has-rule", "offset_rule" in offset)
check("FS-043-offset-cap", offset.get("max_annuity_pct_of_high_3") == 70.0)

# === FSPS checks ===
fsps = next((s for s in systems if s.get("system") == "FSPS"), {})
check("FS-050-fsps-multiplier-20", fsps.get("multiplier_first_20_years_pct") == 1.7)
check("FS-051-fsps-multiplier-beyond", fsps.get("multiplier_beyond_20_years_pct") == 1.0)
check("FS-052-fsps-contrib", fsps.get("employee_contribution_rate_pct") == 1.35)
check("FS-053-fsps-has-ss", fsps.get("social_security_coverage") == True)
check("FS-054-fsps-tsp-match", fsps.get("tsp_matching") == True)
check("FS-055-fsps-mandatory-65", fsps.get("mandatory_retirement_age") == 65)
check("FS-056-fsps-no-cap", fsps.get("max_annuity_cap") is not None)
check("FS-057-fsps-analogous-fers", "FERS" in fsps.get("analogous_to", ""))

# FSPS three-tier system
three_tier = fsps.get("three_tier_system", {})
check("FS-058-fsps-tier1", "annuity" in three_tier.get("tier_1", "").lower())
check("FS-059-fsps-tier2", "social security" in three_tier.get("tier_2", "").lower())
check("FS-060-fsps-tier3", "tsp" in three_tier.get("tier_3", "").lower())

# FSPS COLA — critical difference from FERS
fsps_cola = fsps.get("cola_rule", {})
check("FS-061-fsps-cola-tiered", "Tiered" in fsps_cola.get("method", ""))
check("FS-062-fsps-cola-rules-count", len(fsps_cola.get("rules", [])) == 3)
check("FS-063-fsps-cola-any-age", "any age" in fsps_cola.get("critical_difference_from_fers", "").lower())

# Verify COLA rules match FERS formula
cola_rules = fsps_cola.get("rules", [])
if len(cola_rules) == 3:
    check("FS-064-cola-rule1-lte2", "2.0%" in cola_rules[0].get("condition", ""))
    check("FS-065-cola-rule2-2to3", "2.0% to 3.0%" in cola_rules[1].get("condition", ""))
    check("FS-066-cola-rule3-gt3", "> 3.0%" in cola_rules[2].get("condition", ""))

# FSPS eligibility
fsps_elig = fsps.get("eligibility", {}).get("voluntary_immediate_unreduced", [])
check("FS-070-fsps-50-20", any(e.get("rule") == "50/20" for e in fsps_elig))
check("FS-071-fsps-50-20-multiplier-17", any("1.7" in str(e.get("multiplier", "")) for e in fsps_elig))
check("FS-072-fsps-62-5", any(e.get("rule") == "62/5_fers_equivalent" for e in fsps_elig))
check("FS-073-fsps-25-involuntary", any(e.get("rule") == "any_age/25_involuntary" for e in fsps_elig))

# FSPS reduced retirement
fsps_reduced = fsps.get("eligibility", {}).get("voluntary_reduced", [])
check("FS-074-fsps-mra-10", len(fsps_reduced) >= 1)
if fsps_reduced:
    check("FS-075-fsps-mra-5pct-reduction", "5%" in str(fsps_reduced[0].get("reduction", "")))

# FSPS annuity supplement
supplement = fsps.get("annuity_supplement", {})
check("FS-076-supplement-exists", "annuity_supplement" in fsps)
check("FS-077-supplement-ends-62", "62" in supplement.get("ends", ""))
check("FS-078-supplement-earnings-test", "earnings_test" in supplement)

# FSPS survivor benefits
fsps_surv = fsps.get("survivor_benefits", {})
check("FS-080-fsps-survivor-50pct", fsps_surv.get("max_survivor_annuity_pct") == 50)
check("FS-081-fsps-survivor-cost-10pct", fsps_surv.get("full_survivor_cost_pct") == 10)
check("FS-082-fsps-partial-25pct", fsps_surv.get("partial_survivor_annuity_pct") == 25)
check("FS-083-fsps-partial-cost-5pct", fsps_surv.get("partial_survivor_cost_pct") == 5)
check("FS-084-fsps-combined-max", fsps_surv.get("max_combined_survivor_annuities_pct") == 50)

# FSPS example
fsps_ex = fsps.get("example", {})
check("FS-085-fsps-example-years", fsps_ex.get("years") == 25)
check("FS-086-fsps-example-annuity", fsps_ex.get("total_annual_annuity") == 46800)
check("FS-087-fsps-example-rate", fsps_ex.get("replacement_rate_pct") == 39.0)
# Verify calculation: (120000 × 0.017 × 20) + (120000 × 0.01 × 5) = 40800 + 6000 = 46800
check("FS-088-fsps-example-math", fsps_ex.get("first_20_years_annuity") == 40800)
check("FS-089-fsps-example-math2", fsps_ex.get("beyond_20_years_annuity") == 6000)

# === Transfer provisions ===
transfers = data.get("transfer_provisions", {})
check("FS-090-transfers-exist", "transfer_provisions" in data)
check("FS-091-fsrds-to-fsps", "fsrds_to_fsps" in transfers)
check("FS-092-transfer-irrevocable", transfers.get("fsrds_to_fsps", {}).get("election_irrevocable") == True)

# === Special provisions ===
special = data.get("special_provisions", {})
check("FS-095-special-exists", "special_provisions" in data)
check("FS-096-dss-agents", "diplomatic_security_special_agents" in special)
check("FS-097-virtual-locality", "virtual_locality_pay" in special)
check("FS-098-virtual-locality-date", special.get("virtual_locality_pay", {}).get("effective_date") == "2002-12-29")

# === Comparison to FERS ===
comparison = data.get("comparison_to_fers", {})
check("FS-100-comparison-exists", "comparison_to_fers" in data)
diffs = comparison.get("key_differences", [])
check("FS-101-comparison-count", len(diffs) >= 7, f"got {len(diffs)}")

# 20-year replacement rate comparison
twenty_yr = comparison.get("twenty_year_replacement_rate_comparison", {})
check("FS-102-20yr-fsps", twenty_yr.get("fsps_pct") == 34.0)
check("FS-103-20yr-fers", twenty_yr.get("fers_standard_pct") == 20.0)
check("FS-104-20yr-leo", twenty_yr.get("fers_leo_pct") == 34.0)

# 30-year replacement rate
thirty_yr = comparison.get("thirty_year_replacement_rate_comparison", {})
check("FS-105-30yr-fsps", thirty_yr.get("fsps_pct") == 44.0)
check("FS-106-30yr-fers", thirty_yr.get("fers_standard_pct") == 30.0)

# === Population statistics ===
pop = data.get("population_statistics", {})
check("FS-110-population-exists", "population_statistics" in data)
check("FS-111-fsrds-active", pop.get("fsrds", {}).get("active_employees") == 33)
check("FS-112-fsps-active", pop.get("fsps", {}).get("active_employees") == 15208)
check("FS-113-total", pop.get("total_population") == 31670)

# Cross-check totals
total_active = pop.get("fsrds", {}).get("active_employees", 0) + pop.get("fsps", {}).get("active_employees", 0)
total_annuitants = pop.get("fsrds", {}).get("annuitants", 0) + pop.get("fsps", {}).get("annuitants", 0)
check("FS-114-total-active-sum", pop.get("total_active") == total_active)
check("FS-115-total-annuitants-sum", pop.get("total_annuitants") == total_annuitants)
check("FS-116-total-population-sum", pop.get("total_population") == total_active + total_annuitants)

# === Cross-system consistency checks ===
# FSRDS survivor (55%) should be higher than FSPS survivor (50%) — matches CSRS vs FERS pattern
fsrds_surv_pct = fsrds.get("survivor_benefits", {}).get("max_survivor_annuity_pct", 0)
fsps_surv_pct = fsps.get("survivor_benefits", {}).get("max_survivor_annuity_pct", 0)
check("FS-120-fsrds-survivor-gt-fsps", fsrds_surv_pct > fsps_surv_pct,
      f"FSRDS {fsrds_surv_pct}% should exceed FSPS {fsps_surv_pct}%")

# FSRDS contribution (7.25%) should be much higher than FSPS (1.35%) — matches CSRS vs FERS pattern
check("FS-121-fsrds-contrib-gt-fsps",
      fsrds.get("employee_contribution_rate_pct", 0) > fsps.get("employee_contribution_rate_pct", 0))

# FSRDS multiplier (2.0%) should be higher than FSPS first-20 (1.7%)
check("FS-122-fsrds-mult-gt-fsps",
      fsrds.get("multiplier_per_year_pct", 0) > fsps.get("multiplier_first_20_years_pct", 0))

# Both systems should have mandatory retirement at 65
check("FS-123-both-mandatory-65",
      fsrds.get("mandatory_retirement_age") == 65 and fsps.get("mandatory_retirement_age") == 65)

print(f"\nFOREIGN SERVICE VALIDATION: {passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
