"""
Validation suite for federal retirement benefits gap files:
  - reference/tsp-roth-conversion.json
  - reference/fers-srs-rules.json
  - reference/csrs-retirement-rules.json
  - federal/fegli-rates.json
  - federal/healthcare/fehb-retirement-eligibility.json

Session 43 — Team Gamma O&M
"""

import json
import os
import sys

PASS = 0
FAIL = 0
ERRORS = []

def check(description, condition):
    global PASS, FAIL, ERRORS
    if condition:
        PASS += 1
    else:
        FAIL += 1
        ERRORS.append(description)
        print(f"  FAIL: {description}")

def load_json(path):
    with open(path) as f:
        return json.load(f)

# ─── Locate repo root ───
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ════════════════════════════════════════════════════════════════
# 1. TSP ROTH IN-PLAN CONVERSION RULES
# ════════════════════════════════════════════════════════════════
print("=== TSP Roth In-Plan Conversion Rules ===")
tsp_path = os.path.join(REPO, "reference", "tsp-roth-conversion.json")
check("tsp-roth-conversion.json exists", os.path.exists(tsp_path))
tsp = load_json(tsp_path)

# Metadata
check("TSP Roth: has metadata", "metadata" in tsp)
check("TSP Roth: has version", "version" in tsp.get("metadata", {}))
check("TSP Roth: has last_updated", "last_updated" in tsp.get("metadata", {}))
check("TSP Roth: has sources", len(tsp.get("metadata", {}).get("sources", [])) >= 3)

# Effective date
check("TSP Roth: effective_date is 2026-01-28", tsp.get("effective_date") == "2026-01-28")

# Eligibility
elig = tsp.get("eligibility", {})
cats = [e["category"] for e in elig.get("eligible_participants", [])]
check("TSP Roth: active_employees eligible", "active_employees" in cats)
check("TSP Roth: separated_participants eligible", "separated_participants" in cats)
check("TSP Roth: spousal_beneficiaries eligible", "spousal_beneficiaries" in cats)

# Conversion mechanics
mech = tsp.get("conversion_mechanics", {})
check("TSP Roth: minimum amount $500", mech.get("minimum_amount") == 500)
check("TSP Roth: max 26 per year", mech.get("maximum_per_year") == 26)
check("TSP Roth: irrevocable is true", mech.get("irrevocable") is True)

# Tax treatment
tax = tsp.get("tax_treatment", {})
check("TSP Roth: TSP does NOT withhold taxes", tax.get("withholding", {}).get("tsp_withholds") is False)
check("TSP Roth: has estimated tax schedule", len(tax.get("estimated_tax_payments", {}).get("schedule", [])) == 4)

# Five-year rules
five = tsp.get("five_year_rules", {})
check("TSP Roth: has participation_rule", "participation_rule" in five)
check("TSP Roth: has conversion_rule", "conversion_rule" in five)
check("TSP Roth: has qualified_distribution", "qualified_distribution" in five)

# RMD exemption
rmd = tsp.get("rmd_exemption", {})
check("TSP Roth: RMD exemption effective 2024-01-01", rmd.get("effective_date") == "2024-01-01")

# Mandatory Roth catchup
catchup = tsp.get("mandatory_roth_catchup", {})
check("TSP Roth: catchup threshold 2026 = $150,000", catchup.get("threshold_2026") == 150000)
check("TSP Roth: catchup age 50-59 = $8,000", catchup.get("catchup_limits", {}).get("age_50_59") == 8000)
check("TSP Roth: catchup age 60-63 = $11,250", catchup.get("catchup_limits", {}).get("age_60_63") == 11250)

# Planning interactions
plan = tsp.get("planning_interactions", {})
check("TSP Roth: has irmaa_impact", "irmaa_impact" in plan)
check("TSP Roth: has fers_srs_interaction", "fers_srs_interaction" in plan)
check("TSP Roth: has ladder_strategy", "ladder_strategy" in plan)

# Withdrawal ordering
wo = tsp.get("withdrawal_ordering", {})
check("TSP Roth: has 3 withdrawal order sources", len(wo.get("order", [])) == 3)

# ════════════════════════════════════════════════════════════════
# 2. FERS SPECIAL RETIREMENT SUPPLEMENT (SRS) RULES
# ════════════════════════════════════════════════════════════════
print("\n=== FERS SRS Rules ===")
srs_path = os.path.join(REPO, "reference", "fers-srs-rules.json")
check("fers-srs-rules.json exists", os.path.exists(srs_path))
srs = load_json(srs_path)

# Metadata
check("SRS: has metadata with version", "version" in srs.get("metadata", {}))
check("SRS: has sources >= 3", len(srs.get("metadata", {}).get("sources", [])) >= 3)

# Eligibility
elig = srs.get("eligibility", {})
eligible_cats = [e["category"] for e in elig.get("eligible_categories", [])]
check("SRS: MRA + 30 eligible", "MRA + 30" in eligible_cats)
check("SRS: Age 60 + 20 eligible", "Age 60 + 20" in eligible_cats)
check("SRS: Special provision eligible", any("Special Provision" in c for c in eligible_cats))
check("SRS: VERA/VSIP eligible", "VERA/VSIP" in eligible_cats)

not_eligible = [e["category"] for e in elig.get("not_eligible", [])]
check("SRS: MRA + 10 NOT eligible", "MRA + 10" in not_eligible)
check("SRS: Deferred NOT eligible", "Deferred retirement" in not_eligible)
check("SRS: Disability NOT eligible", "Disability retirement" in not_eligible)
check("SRS: Age 62+ NOT eligible", "Age 62+ at retirement" in not_eligible)

# Formula
formula = srs.get("formula", {})
check("SRS: formula denominator is 40", formula.get("components", {}).get("denominator", {}).get("value") == 40)
check("SRS: formula has example", "example" in formula)

# Earnings test
et = srs.get("earnings_test", {})
check("SRS: has reduction formula", "reduction_formula" in et)
check("SRS: $1 for every $2 rule", "$1 for every $2" in et.get("reduction_formula", {}).get("description", ""))
check("SRS: exempt amount 2024 = $22,320", et.get("exempt_amounts", {}).get("2024") == 22320)
check("SRS: exempt amount 2025 = $23,400", et.get("exempt_amounts", {}).get("2025") == 23400)
check("SRS: does not apply to TSP withdrawals", "TSP withdrawals" in str(et.get("does_not_apply_to", [])))
check("SRS: does not apply to investment income", "Investment income" in str(et.get("does_not_apply_to", [])))

# COLA
check("SRS: does NOT receive COLA", srs.get("cola", {}).get("receives_cola") is False)

# Tax
check("SRS: federally taxable", srs.get("tax_treatment", {}).get("federal", {}).get("taxable") is True)
check("SRS: not subject to FICA", "FICA" in str(srs.get("tax_treatment", {}).get("federal", {}).get("not_fica", "")))

# Start/end
se = srs.get("start_and_end", {})
check("SRS: ends before age 62", "62" in se.get("ends", ""))

# Planning interactions
check("SRS: has tsp roth interaction", "with_tsp_roth_conversions" in srs.get("planning_interactions", {}))
check("SRS: has social security interaction", "with_social_security" in srs.get("planning_interactions", {}))

# ════════════════════════════════════════════════════════════════
# 3. CSRS RETIREMENT RULES
# ════════════════════════════════════════════════════════════════
print("\n=== CSRS Retirement Rules ===")
csrs_path = os.path.join(REPO, "reference", "csrs-retirement-rules.json")
check("csrs-retirement-rules.json exists", os.path.exists(csrs_path))
csrs = load_json(csrs_path)

# Metadata
check("CSRS: has metadata with version", "version" in csrs.get("metadata", {}))
check("CSRS: has sources >= 3", len(csrs.get("metadata", {}).get("sources", [])) >= 3)

# System status
check("CSRS: system status CLOSED", csrs.get("system_status") == "CLOSED")
check("CSRS: closed date 1987-01-01", csrs.get("closed_date") == "1987-01-01")
check("CSRS: no Social Security", csrs.get("social_security_participation") is False)
check("CSRS: employee contribution 7.0%", csrs.get("employee_contribution_rate_pct") == 7.0)

# Annuity formula tiers
formula = csrs.get("annuity_formula", {})
tiers = formula.get("tiers", [])
check("CSRS: has 3 formula tiers", len(tiers) == 3)
check("CSRS: tier 1 = 1.5% (first 5 years)", tiers[0].get("multiplier_pct") == 1.5 if len(tiers) >= 1 else False)
check("CSRS: tier 2 = 1.75% (years 6-10)", tiers[1].get("multiplier_pct") == 1.75 if len(tiers) >= 2 else False)
check("CSRS: tier 3 = 2.0% (beyond 10)", tiers[2].get("multiplier_pct") == 2.0 if len(tiers) >= 3 else False)
check("CSRS: max annuity 80%", formula.get("maximum_annuity_pct") == 80.0)

# Example math verification
ex = formula.get("example", {})
if ex:
    expected_total = 7500 + 8750 + 40000  # 56,250
    check("CSRS: example total = $56,250", ex.get("total_annual") == expected_total)
    check("CSRS: example effective rate = 56.25%", ex.get("effective_rate_pct") == 56.25)

# Eligibility
elig = csrs.get("eligibility", {})
opt_ret = elig.get("optional_retirement", [])
check("CSRS: has 3 optional retirement categories", len(opt_ret) == 3)
categories = [e["category"] for e in opt_ret]
check("CSRS: 55/30 category exists", "55/30" in categories)
check("CSRS: 60/20 category exists", "60/20" in categories)
check("CSRS: 62/5 category exists", "62/5" in categories)

# Early retirement reduction
early = elig.get("early_retirement", {})
check("CSRS: early retirement 2% per year under 55", "2%" in early.get("reduction", ""))

# Sick leave credit
sl = csrs.get("sick_leave_credit", {})
check("CSRS: sick leave hours per month = 174", sl.get("hours_per_month") == 174)
check("CSRS: 2087 hours = 1 year", "2,087" in sl.get("conversion", ""))

# Survivor annuity
surv = csrs.get("survivor_annuity", {})
check("CSRS: full survivor = 55%", surv.get("full_survivor", {}).get("benefit_pct") == 55)
check("CSRS: full survivor cost ~10%", surv.get("full_survivor", {}).get("cost_pct_of_annuity") == 10)

# COLA
cola = csrs.get("cola_rules", {})
check("CSRS: full CPI COLA", cola.get("full_cpi") is True)

# CSRS Offset
offset = csrs.get("csrs_offset", {})
check("CSRS Offset: SS component 6.2%", offset.get("contribution_rate_pct", {}).get("social_security") == 6.2)
check("CSRS Offset: CSRS component 0.2%", offset.get("contribution_rate_pct", {}).get("csrs_component") == 0.2)

# Voluntary contributions
vc = csrs.get("voluntary_contributions", {})
check("CSRS: voluntary contributions max 10% of pay", vc.get("maximum_pct_of_pay") == 10)

# TSP access
tsp_access = csrs.get("tsp_access", {})
check("CSRS: no agency auto contribution", tsp_access.get("agency_auto_pct") == 0)
check("CSRS: no agency match", tsp_access.get("agency_match") is False)

# No SRS
check("CSRS: no SRS", "no_srs" in csrs)

# Special category
sc = csrs.get("special_category_employees", {})
check("CSRS: special category first 20 = 2.5%", sc.get("formula", {}).get("first_20_years_multiplier_pct") == 2.5)
check("CSRS: special category beyond 20 = 2.0%", sc.get("formula", {}).get("beyond_20_years_multiplier_pct") == 2.0)

# WEP/GPO
wg = csrs.get("wep_gpo_impact", {})
check("CSRS: mentions WEP/GPO repeal", "repeal" in wg.get("repeal_status", "").lower())

# ════════════════════════════════════════════════════════════════
# 4. FEGLI RATES AND RULES
# ════════════════════════════════════════════════════════════════
print("\n=== FEGLI Rates and Rules ===")
fegli_path = os.path.join(REPO, "federal", "fegli-rates.json")
check("fegli-rates.json exists", os.path.exists(fegli_path))
fegli = load_json(fegli_path)

# Metadata
check("FEGLI: has metadata with version", "version" in fegli.get("metadata", {}))
check("FEGLI: has sources >= 3", len(fegli.get("metadata", {}).get("sources", [])) >= 3)

# Coverage types
ct = fegli.get("coverage_types", {})
check("FEGLI: has basic coverage", "basic" in ct)
check("FEGLI: has option_a_standard", "option_a_standard" in ct)
check("FEGLI: has option_b_additional", "option_b_additional" in ct)
check("FEGLI: has option_c_family", "option_c_family" in ct)

# Basic coverage formula
basic = ct.get("basic", {})
check("FEGLI: basic formula includes $2,000 add", "2,000" in basic.get("formula", ""))
check("FEGLI: government pays one-third", "Two-thirds" in str(basic.get("cost_sharing", {}).get("employee_share", "")))

# Option A
opt_a = ct.get("option_a_standard", {})
check("FEGLI: Option A = $10,000", opt_a.get("face_value") == 10000)

# Option B multiples
opt_b = ct.get("option_b_additional", {})
check("FEGLI: Option B multiples 1-5", opt_b.get("multiples_available") == [1, 2, 3, 4, 5])

# Option C
opt_c = ct.get("option_c_family", {})
check("FEGLI: Option C spouse = $5,000 per multiple", opt_c.get("per_multiple", {}).get("spouse") == 5000)
check("FEGLI: Option C child = $2,500 per multiple", opt_c.get("per_multiple", {}).get("each_eligible_child") == 2500)

# Extra benefit schedule
extra = fegli.get("extra_benefit_under_45", {})
schedule = extra.get("schedule", [])
check("FEGLI: extra benefit has 11 entries", len(schedule) == 11)
# Age 35 or under: 100% extra (200% total)
first = schedule[0] if schedule else {}
check("FEGLI: age 35 or under = 200% total", first.get("total_basic_pct") == 200)
# Age 45+: 0% extra (100% total)
last = schedule[-1] if schedule else {}
check("FEGLI: age 45+ = 100% total", last.get("total_basic_pct") == 100)

# Employee premium rates - Basic
rates = fegli.get("employee_premium_rates", {})
basic_r = rates.get("basic", {})
check("FEGLI: Basic biweekly $0.16/1000", basic_r.get("biweekly_per_1000") == 0.16)
check("FEGLI: Basic not age-rated", basic_r.get("age_rated") is False)

# Option A rates - pinned values
opt_a_rates = rates.get("option_a", {}).get("age_bands", [])
check("FEGLI: Option A has 7 age bands", len(opt_a_rates) == 7)
# Under 35: $0.20 biweekly
if opt_a_rates:
    check("FEGLI: Option A under 35 = $0.20 bw", opt_a_rates[0].get("biweekly") == 0.20)
    # 60+: $6.00 biweekly
    check("FEGLI: Option A 60+ = $6.00 bw", opt_a_rates[-1].get("biweekly") == 6.00)

# Option B rates - pinned values
opt_b_rates = rates.get("option_b", {}).get("age_bands", [])
check("FEGLI: Option B has 11 age bands", len(opt_b_rates) == 11)
if opt_b_rates:
    check("FEGLI: Option B under 35 = $0.02/1000 bw", opt_b_rates[0].get("biweekly_per_1000") == 0.02)
    check("FEGLI: Option B 60-64 = $0.40/1000 bw", opt_b_rates[6].get("biweekly_per_1000") == 0.40)
    check("FEGLI: Option B 80+ = $2.88/1000 bw", opt_b_rates[-1].get("biweekly_per_1000") == 2.88)

# Option C rates - pinned values
opt_c_rates = rates.get("option_c", {}).get("age_bands", [])
check("FEGLI: Option C has 11 age bands", len(opt_c_rates) == 11)
if opt_c_rates:
    check("FEGLI: Option C under 35 = $0.20/mult bw", opt_c_rates[0].get("biweekly_per_multiple") == 0.20)
    check("FEGLI: Option C 80+ = $7.80/mult bw", opt_c_rates[-1].get("biweekly_per_multiple") == 7.80)

# Retirement reduction elections
ret = fegli.get("retirement_reduction_elections", {})
basic_opts = ret.get("basic_options", [])
check("FEGLI: 3 Basic retirement options", len(basic_opts) == 3)
elections = [o["election"] for o in basic_opts]
check("FEGLI: 75% Reduction option exists", any("75%" in e for e in elections))
check("FEGLI: 50% Reduction option exists", any("50%" in e for e in elections))
check("FEGLI: No Reduction option exists", any("No Reduction" in e for e in elections))

# 75% reduction is free after 65
for opt in basic_opts:
    if "75%" in opt.get("election", ""):
        check("FEGLI: 75% reduction is free post-65", "Free" in str(opt.get("post_65_premium", "")))
        check("FEGLI: 75% reduction final = 25%", opt.get("final_coverage_pct") == 25)

# Option B No Reduction post-retirement rates
opt_b_no_red = ret.get("option_b_retirement", {}).get("with_no_reduction", {})
post_rates = opt_b_no_red.get("post_retirement_rates_monthly_per_1000", [])
check("FEGLI: Option B No Reduction has 4 post-retirement age bands", len(post_rates) == 4)
if post_rates:
    check("FEGLI: Option B 80+ monthly = $6.240/1000", post_rates[-1].get("rate") == 6.240)

# 5-year eligibility rule for retirement
ret_elig = fegli.get("eligibility_to_continue_in_retirement", {})
check("FEGLI: has 5-year retirement eligibility requirement", "5 years" in ret_elig.get("requirement", ""))

# ════════════════════════════════════════════════════════════════
# 5. FEHB RETIREMENT ELIGIBILITY RULES
# ════════════════════════════════════════════════════════════════
print("\n=== FEHB Retirement Eligibility Rules ===")
fehb_path = os.path.join(REPO, "federal", "healthcare", "fehb-retirement-eligibility.json")
check("fehb-retirement-eligibility.json exists", os.path.exists(fehb_path))
fehb = load_json(fehb_path)

# Metadata
check("FEHB Ret: has metadata with version", "version" in fehb.get("metadata", {}))
check("FEHB Ret: has sources >= 3", len(fehb.get("metadata", {}).get("sources", [])) >= 3)

# Five-year rule
fyr = fehb.get("five_year_rule", {})
check("FEHB Ret: has 5-year rule", "5 years" in fyr.get("description", ""))
check("FEHB Ret: has statutory reference", "8905" in fyr.get("statutory_reference", ""))
check("FEHB Ret: has alternatives", len(fyr.get("alternatives", [])) >= 2)

# Who can continue
wcc = fehb.get("who_can_continue", {})
check("FEHB Ret: immediate retirees eligible", wcc.get("immediate_retirees", {}).get("eligible") is True)
check("FEHB Ret: disability retirees eligible", wcc.get("disability_retirees", {}).get("eligible") is True)
check("FEHB Ret: survivor annuitants eligible", wcc.get("survivor_annuitants", {}).get("eligible") is True)

# Premium mechanics
pm = fehb.get("premium_mechanics_in_retirement", {})
check("FEHB Ret: government continues share", "government" in pm.get("government_share", {}).get("description", "").lower())
check("FEHB Ret: not age-rated", "NOT age-rated" in pm.get("no_age_increase", ""))
check("FEHB Ret: retiree premiums after-tax", pm.get("annuitant_share", {}).get("pre_tax") is False)

# Medicare coordination
mc = fehb.get("medicare_coordination", {})
check("FEHB Ret: has Medicare Part A guidance", "recommended" in str(mc.get("enrollment_at_65", {}).get("medicare_part_a", {})))
check("FEHB Ret: has Medicare Part B guidance", "optional" in str(mc.get("enrollment_at_65", {}).get("medicare_part_b", {})))
check("FEHB Ret: has FEHB as secondary explanation", "fehb_as_secondary" in mc)

# TCC
tcc = fehb.get("temporary_continuation_of_coverage", {})
check("FEHB Ret: TCC duration 18 months", tcc.get("duration_months") == 18)
check("FEHB Ret: TCC cost 102%", "102%" in tcc.get("cost", ""))

# ════════════════════════════════════════════════════════════════
# CROSS-FILE CHECKS
# ════════════════════════════════════════════════════════════════
print("\n=== Cross-File Consistency Checks ===")

# TSP Roth references SRS correctly
srs_ref = tsp.get("planning_interactions", {}).get("fers_srs_interaction", {})
check("Cross: TSP Roth references fers-srs-rules.json", "fers-srs-rules.json" in srs_ref.get("reference", ""))

# SRS references TSP Roth correctly
tsp_ref = srs.get("planning_interactions", {}).get("with_tsp_roth_conversions", {})
check("Cross: SRS references tsp-roth-conversion.json", "tsp-roth-conversion.json" in tsp_ref.get("reference", ""))

# CSRS correctly states no SRS
check("Cross: CSRS states no SRS", "no_srs" in csrs)

# CSRS survivor = 55% vs FERS 50% (cross-check rates-annual.json)
rates_path = os.path.join(REPO, "federal", "rates-annual.json")
if os.path.exists(rates_path):
    rates = load_json(rates_path)
    fers_surv = rates.get("fers", {}).get("survivor_full_pct")
    check("Cross: FERS survivor 50% (rates-annual)", fers_surv == 0.5)
    check("Cross: CSRS survivor 55% (different from FERS)", csrs.get("survivor_annuity", {}).get("full_survivor", {}).get("benefit_pct") == 55)

# FEGLI and FEHB both mention 5-year rule
check("Cross: FEGLI has 5-year retirement eligibility", "5 years" in fegli.get("eligibility_to_continue_in_retirement", {}).get("requirement", ""))
check("Cross: FEHB has 5-year rule", "5 years" in fehb.get("five_year_rule", {}).get("description", ""))

# Verify all files have valid version strings
for name, data in [("tsp-roth", tsp), ("fers-srs", srs), ("csrs", csrs), ("fegli", fegli), ("fehb-ret", fehb)]:
    v = data.get("metadata", {}).get("version", "")
    check(f"Cross: {name} has non-empty version", len(str(v)) > 0)
    lu = data.get("metadata", {}).get("last_updated", "")
    check(f"Cross: {name} has last_updated", len(str(lu)) >= 10)

# ════════════════════════════════════════════════════════════════
# RANGE AND REASONABLENESS CHECKS
# ════════════════════════════════════════════════════════════════
print("\n=== Range and Reasonableness Checks ===")

# CSRS tiers should be increasing
csrs_tiers = csrs.get("annuity_formula", {}).get("tiers", [])
if len(csrs_tiers) == 3:
    check("CSRS: tiers are increasing (1.5 < 1.75 < 2.0)",
          csrs_tiers[0]["multiplier_pct"] < csrs_tiers[1]["multiplier_pct"] < csrs_tiers[2]["multiplier_pct"])

# FEGLI Option B rates should be monotonically increasing by age
for option_name, bands_key, rate_key in [
    ("Option B", "option_b", "biweekly_per_1000"),
    ("Option C", "option_c", "biweekly_per_multiple")
]:
    bands = rates.get(option_name.lower().replace(" ", "_"), {}).get("age_bands", [])
    if len(bands) >= 2:
        all_increasing = True
        for i in range(1, len(bands)):
            if bands[i].get(rate_key, 0) < bands[i-1].get(rate_key, 0):
                all_increasing = False
                break
        check(f"FEGLI: {option_name} rates monotonically increasing by age", all_increasing)

# SRS earnings test exempt amounts should be increasing
et_amts = srs.get("earnings_test", {}).get("exempt_amounts", {})
check("SRS: exempt amounts increasing (2024 < 2025)", et_amts.get("2024", 0) < et_amts.get("2025", 0))

# TSP catchup limits: 60-63 super catchup > regular catchup
cl = tsp.get("mandatory_roth_catchup", {}).get("catchup_limits", {})
check("TSP Roth: super catchup > regular catchup", cl.get("age_60_63", 0) > cl.get("age_50_59", 0))

# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"TOTAL: {PASS + FAIL} checks | PASS: {PASS} | FAIL: {FAIL}")
print(f"{'='*60}")

if ERRORS:
    print("\nFailed checks:")
    for e in ERRORS:
        print(f"  ✗ {e}")

sys.exit(0 if FAIL == 0 else 1)
