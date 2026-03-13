"""Validation suite for OBBBA tax provisions reference file."""
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

# Find repo root
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fpath = os.path.join(repo, "reference", "obbba-tax-provisions.json")

check("OB-001-file-exists", os.path.exists(fpath), fpath)
if not os.path.exists(fpath):
    print(f"OBBBA VALIDATION: {passed} checks passed, {failed} failed")
    sys.exit(1 if failed else 0)

with open(fpath) as f:
    data = json.load(f)

# === Metadata ===
m = data.get("metadata", {})
check("OB-002-metadata-exists", "metadata" in data)
check("OB-003-version", m.get("version") == "1.0")
check("OB-004-law-reference", "P.L. 119-21" in m.get("law_reference", ""))
check("OB-005-sources", len(m.get("sources", [])) >= 3)
check("OB-006-irs-guidance", len(m.get("irs_guidance", [])) >= 2)

# === TCJA Permanence ===
tcja = data.get("tcja_permanence", {})
check("OB-010-tcja-section", "tcja_permanence" in data)
check("OB-011-tcja-sunset-null", tcja.get("sunset") is None, "TCJA permanence should have no sunset")
provs = tcja.get("provisions_made_permanent", [])
check("OB-012-tcja-provisions-count", len(provs) >= 5, f"got {len(provs)}")
prov_names = [p.get("provision") for p in provs]
check("OB-013-tcja-rates", "individual_tax_rates" in prov_names)
check("OB-014-tcja-std-ded", "standard_deduction" in prov_names)
check("OB-015-tcja-estate", "estate_tax_exemption" in prov_names)
check("OB-016-tcja-ctc", "child_tax_credit" in prov_names)
check("OB-017-tcja-exemption", "personal_exemption_elimination" in prov_names)

# Estate tax values
estate_prov = [p for p in provs if p.get("provision") == "estate_tax_exemption"]
if estate_prov:
    vals = estate_prov[0].get("values_2026", {})
    check("OB-018-estate-2026-value", vals.get("per_person_exemption") == 14390000)
    check("OB-019-estate-top-rate", vals.get("top_rate_pct") == 40)

# === New Deductions ===
nd = data.get("new_deductions", {})
check("OB-020-new-deductions-section", "new_deductions" in data)

# Senior deduction
sr = nd.get("senior_deduction", {})
check("OB-021-senior-amount", sr.get("amount_per_person") == 6000)
check("OB-022-senior-married", sr.get("married_both_qualifying") == 12000)
check("OB-023-senior-sunset", sr.get("sunset") == "2028-12-31")
check("OB-024-senior-phase-out-single", sr.get("phase_out", {}).get("single_magi_threshold") == 75000)
check("OB-025-senior-phase-out-joint", sr.get("phase_out", {}).get("joint_magi_threshold") == 150000)
check("OB-026-senior-age-req", "65" in sr.get("age_requirement", ""))

# Tip deduction
tip = nd.get("tip_income_deduction", {})
check("OB-027-tip-max", tip.get("maximum_annual") == 25000)
check("OB-028-tip-sunset", tip.get("sunset") == "2028-12-31")

# Overtime deduction
ot = nd.get("overtime_deduction", {})
check("OB-029-overtime-single", ot.get("maximum_annual_single") == 12500)
check("OB-030-overtime-joint", ot.get("maximum_annual_joint") == 25000)
check("OB-031-overtime-sunset", ot.get("sunset") == "2028-12-31")

# Auto loan deduction
auto = nd.get("auto_loan_interest_deduction", {})
check("OB-032-auto-max", auto.get("maximum_annual") == 10000)
check("OB-033-auto-sunset", auto.get("sunset") == "2028-12-31")

# All temporary deductions sunset 2028
for key in ["senior_deduction", "tip_income_deduction", "overtime_deduction", "auto_loan_interest_deduction"]:
    check(f"OB-034-sunset-{key}", nd.get(key, {}).get("sunset") == "2028-12-31",
          f"{key} sunset should be 2028-12-31")

# === SALT Deduction ===
salt = data.get("salt_deduction", {})
check("OB-040-salt-section", "salt_deduction" in data)
check("OB-041-salt-2025-cap", salt.get("cap_schedule", {}).get("2025") == 40000)
check("OB-042-salt-2026-cap", salt.get("cap_schedule", {}).get("2026") == 40400)
check("OB-043-salt-sunset", salt.get("sunset") == "2029-12-31")
check("OB-044-salt-phase-out-joint", salt.get("income_phase_out", {}).get("joint_magi_threshold") == 500000)
check("OB-045-salt-minimum", salt.get("income_phase_out", {}).get("minimum_cap") == 10000)
# Verify SALT schedule is monotonically increasing
sched = salt.get("cap_schedule", {})
years = sorted(sched.keys())
for i in range(1, len(years)):
    check(f"OB-046-salt-ascending-{years[i]}", sched[years[i]] > sched[years[i-1]])

# === Trump Accounts ===
ta = data.get("trump_accounts", {})
check("OB-050-trump-accounts-section", "trump_accounts" in data)
check("OB-051-ta-effective", ta.get("effective_date") == "2026-01-01")
check("OB-052-ta-first-contrib", ta.get("first_contributions_allowed") == "2026-07-04")
cl = ta.get("contribution_limits", {})
check("OB-053-ta-annual-limit", cl.get("annual_aggregate") == 5000)
check("OB-054-ta-employer-limit", cl.get("employer_max_per_employee") == 2500)
check("OB-055-ta-employer-counts", cl.get("employer_contributions_count_toward_aggregate") is True)
check("OB-056-ta-indexed-after", cl.get("indexed_for_inflation_after") == 2027)
pp = ta.get("pilot_program_contribution", {})
check("OB-057-ta-pilot-amount", pp.get("amount") == 1000)
check("OB-058-ta-pilot-not-in-limit", pp.get("counts_toward_annual_limit") is False)
check("OB-059-ta-no-income-req", ta.get("eligibility", {}).get("no_income_requirements") is True)
tt = ta.get("tax_treatment", {})
check("OB-060-ta-growth-deferred", tt.get("growth") == "Tax-deferred")
check("OB-061-ta-contrib-aftertax", "After-tax" in tt.get("contributions", ""))
check("OB-062-ta-employer-excluded", "Excluded" in tt.get("employer_contributions", ""))

# === Energy Credits ===
ec = data.get("energy_credit_changes", {})
check("OB-070-energy-section", "energy_credit_changes" in data)
check("OB-071-energy-provisions", len(ec.get("provisions", [])) >= 3)

# === Other Provisions ===
op = data.get("other_provisions", {})
check("OB-080-other-section", "other_provisions" in data)
check("OB-081-aca-ptc", "aca_premium_tax_credits" in op)
check("OB-082-hsa-expansion", "hsa_eligibility_expansion" in op)
check("OB-083-medicare-fee", "medicare_physician_fee" in op)

# === Cross References ===
cr = data.get("cross_references", {})
check("OB-090-cross-refs", "cross_references" in data)
files_list = cr.get("files_incorporating_obbba", [])
check("OB-091-cross-ref-count", len(files_list) >= 5, f"got {len(files_list)}")
# Verify cross-referenced files exist in repo
for entry in files_list:
    fref = entry.get("file", "")
    check(f"OB-092-xref-exists-{os.path.basename(fref)}", 
          os.path.exists(os.path.join(repo, fref)),
          f"{fref} not found")

print(f"OBBBA VALIDATION: {passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
