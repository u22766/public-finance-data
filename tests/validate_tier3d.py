#!/usr/bin/env python3
"""
Tier 3D State Expansion Validation — Final 6 states (NE, ND, RI, SD, VT, WY)
Brings total to 50 states + DC (51 jurisdictions).
"""

import json
import sys
import os
import re

PASS = 0
FAIL = 0
WARN = 0

def check(label, condition, msg=""):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  ✗ {label}: {msg}")

def warn(label, msg):
    global WARN
    WARN += 1
    print(f"  ⚠ {label}: {msg}")

# ── Load data ─────────────────────────────────────────────
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sb_path = os.path.join(base, "states", "state-benefits.json")
mf_path = os.path.join(base, "manifest.json")

with open(sb_path) as f:
    sb = json.load(f)
with open(mf_path) as f:
    manifest = json.load(f)

states_by_code = {s["state_code"]: s for s in sb["states"]}
TIER3D = ["NE", "ND", "RI", "SD", "VT", "WY"]
TIER3D_NAMES = {
    "NE": "Nebraska", "ND": "North Dakota", "RI": "Rhode Island",
    "SD": "South Dakota", "VT": "Vermont", "WY": "Wyoming"
}

# ══════════════════════════════════════════════════════════
# SECTION 1 — Structural checks
# ══════════════════════════════════════════════════════════
print("Section 1 — Structural")

version = float(sb["version"])
check("T3D-001-version", version >= 1.9, f"Expected >= 1.9, got {sb['version']}")

state_count = len(sb["states"])
check("T3D-002-state-count", state_count >= 51, f"Expected >= 51, got {state_count}")

for code in TIER3D:
    check(f"T3D-003-present-{code}", code in states_by_code, f"{code} not found in states")
    if code in states_by_code:
        check(f"T3D-004-name-{code}", states_by_code[code]["state_name"] == TIER3D_NAMES[code],
              f"Expected {TIER3D_NAMES[code]}")

# All 50 + DC present
ALL_CODES = ['AK','AL','AR','AZ','CA','CO','CT','DC','DE','FL','GA','HI','IA','ID',
             'IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC',
             'ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD',
             'TN','TX','UT','VA','VT','WA','WI','WV','WY']
missing = [c for c in ALL_CODES if c not in states_by_code]
check("T3D-005-full-national", len(missing) == 0,
      f"Missing states: {', '.join(missing)}")

# ══════════════════════════════════════════════════════════
# SECTION 2 — Income tax checks
# ══════════════════════════════════════════════════════════
print("\nSection 2 — Income tax")

# No-income-tax states: SD, WY
for code in ["SD", "WY"]:
    if code not in states_by_code:
        continue
    it = states_by_code[code]["income_tax"]
    check(f"T3D-010-no-tax-{code}", it.get("has_income_tax") == False,
          "Should have has_income_tax: false")
    check(f"T3D-011-rate-{code}", it.get("top_rate") == 0,
          f"Expected 0 rate, got {it.get('top_rate')}")
    check(f"T3D-012-type-{code}", it.get("rate_type") == "none",
          f"Expected 'none', got {it.get('rate_type')}")
    check(f"T3D-013-mil-exempt-{code}", it["military_retirement"]["exempt"] == True,
          "Should be exempt (no income tax)")

# States with income tax and full military retirement exemption: NE, ND, RI
for code in ["NE", "ND", "RI"]:
    if code not in states_by_code:
        continue
    it = states_by_code[code]["income_tax"]
    check(f"T3D-020-mil-exempt-{code}", it["military_retirement"]["exempt"] == True,
          "Military retirement should be fully exempt")
    check(f"T3D-021-mil-note-{code}", len(it["military_retirement"].get("note", "")) > 10,
          "Military retirement note too short")
    check(f"T3D-022-va-exempt-{code}", it["va_compensation"]["exempt"] == True,
          "VA compensation should be exempt")

# Vermont — partial exemption (income-based)
if "VT" in states_by_code:
    vt_it = states_by_code["VT"]["income_tax"]
    check("T3D-030-VT-mil-partial", vt_it["military_retirement"]["exempt"] == "partial",
          f"VT should be 'partial', got {vt_it['military_retirement']['exempt']}")
    check("T3D-031-VT-act71", "act 71" in vt_it["military_retirement"]["note"].lower() or
          "125,000" in vt_it["military_retirement"]["note"],
          "VT should reference Act 71 or $125,000 threshold")
    check("T3D-032-VT-175k", "175,000" in vt_it["military_retirement"]["note"],
          "VT should reference $175,000 upper threshold")
    check("T3D-033-VT-credit", vt_it.get("low_income_veteran_credit", {}).get("available") == True,
          "VT should have low_income_veteran_credit")
    check("T3D-034-VT-credit-amount", vt_it.get("low_income_veteran_credit", {}).get("amount") == 250,
          "VT low income credit should be $250")
    check("T3D-035-VT-top-rate", vt_it["top_rate"] >= 0.08,
          f"VT top rate should be >= 8%, got {vt_it.get('top_rate')}")

# Nebraska specifics
if "NE" in states_by_code:
    ne_it = states_by_code["NE"]["income_tax"]
    check("T3D-040-NE-ss-exempt", ne_it["ss_income"]["exempt"] == True,
          "NE SS should be fully exempt (2025+)")
    check("T3D-041-NE-sbp-exempt", ne_it["sbp_annuities"]["exempt"] == True,
          "NE SBP should be exempt")
    check("T3D-042-NE-top-rate", 0.04 <= ne_it["top_rate"] <= 0.06,
          f"NE top rate should be ~5.20%, got {ne_it['top_rate']}")
    check("T3D-043-NE-graduated", ne_it["rate_type"] == "graduated",
          "NE should be graduated")
    check("T3D-044-NE-phasedown", "3.99" in ne_it.get("rate_note", "") or "4.55" in ne_it.get("rate_note", ""),
          "NE rate note should mention phasedown rates")
    check("T3D-045-NE-fed-pension", ne_it["taxes_federal_pension"] == False,
          "NE should not tax federal pensions (exempt 2024+)")

# North Dakota specifics
if "ND" in states_by_code:
    nd_it = states_by_code["ND"]["income_tax"]
    check("T3D-050-ND-ss-exempt", nd_it["ss_income"]["exempt"] == True,
          "ND SS should be fully exempt")
    check("T3D-051-ND-sbp-exempt", nd_it["sbp_annuities"]["exempt"] == True,
          "ND SBP should be exempt")
    check("T3D-052-ND-top-rate", nd_it["top_rate"] <= 0.03,
          f"ND top rate should be <= 3%, got {nd_it['top_rate']}")
    check("T3D-053-ND-graduated", nd_it["rate_type"] == "graduated",
          "ND should be graduated")

# Rhode Island specifics
if "RI" in states_by_code:
    ri_it = states_by_code["RI"]["income_tax"]
    check("T3D-060-RI-sbp-taxable", ri_it["sbp_annuities"]["exempt"] == False,
          "RI SBP should be taxable (not fully exempt)")
    check("T3D-061-RI-top-rate", 0.05 <= ri_it["top_rate"] <= 0.07,
          f"RI top rate should be ~5.99%, got {ri_it['top_rate']}")
    check("T3D-062-RI-2023", "2023" in ri_it["military_retirement"].get("note", ""),
          "RI should reference 2023 effective date")

# ══════════════════════════════════════════════════════════
# SECTION 3 — Veteran benefits structure
# ══════════════════════════════════════════════════════════
print("\nSection 3 — Veteran benefits structure")

for code in TIER3D:
    if code not in states_by_code:
        continue
    s = states_by_code[code]
    check(f"T3D-100-vb-exists-{code}", "veteran_benefits" in s,
          f"{code} missing veteran_benefits")
    if "veteran_benefits" not in s:
        continue
    vb = s["veteran_benefits"]
    check(f"T3D-101-schema-note-{code}", "_schema_note" in vb,
          f"{code} missing _schema_note")
    check(f"T3D-102-sources-{code}", len(s.get("sources", [])) >= 2,
          f"{code} should have at least 2 sources")

    # Each benefit should have available, exemption_type, description
    for bkey, bval in vb.items():
        if bkey.startswith("_"):
            continue
        if not isinstance(bval, dict):
            continue
        check(f"T3D-103-available-{code}-{bkey}", "available" in bval,
              f"{code}.{bkey} missing 'available'")
        check(f"T3D-104-type-{code}-{bkey}", "exemption_type" in bval,
              f"{code}.{bkey} missing 'exemption_type'")
        check(f"T3D-105-desc-{code}-{bkey}", len(bval.get("description", "")) > 20,
              f"{code}.{bkey} description too short")

# ══════════════════════════════════════════════════════════
# SECTION 4 — State-specific spot checks
# ══════════════════════════════════════════════════════════
print("\nSection 4 — State-specific spot checks")

# ── Nebraska ──
if "NE" in states_by_code:
    ne_vb = states_by_code["NE"]["veteran_benefits"]
    dv = ne_vb.get("disabled_veteran_homestead_exemption", {})
    check("T3D-200-NE-full", dv.get("exemption_type") == "full",
          "NE should be full exemption for 100% P&T")
    check("T3D-201-NE-iu", dv.get("eligibility", {}).get("iu_eligible") == True,
          "NE should have IU eligible")
    check("T3D-202-NE-4V", "4v" in dv.get("description", "").lower() or "category 4v" in dv.get("description", "").lower(),
          "NE should reference Category 4V")
    check("T3D-203-NE-cat7", "category 7" in dv.get("description", "").lower() or "temporary" in dv.get("description", "").lower(),
          "NE should reference Category 7 / temporary disability")
    check("T3D-204-NE-occupancy", "august 15" in dv.get("eligibility", {}).get("occupancy_requirement", "").lower(),
          "NE should mention August 15 occupancy deadline")
    check("T3D-205-NE-form458", "458" in dv.get("application", {}).get("form", ""),
          "NE should reference Form 458")
    check("T3D-206-NE-survivor", dv.get("survivor_transfer") == True,
          "NE should have survivor transfer")
    check("T3D-207-NE-age57", "57" in str(dv.get("survivor_conditions", {})),
          "NE should mention age 57 remarriage provision")
    check("T3D-208-NE-authority", "77-3506" in dv.get("authority", ""),
          "NE should cite §77-3506")
    check("T3D-209-NE-pending", "pending" in dv.get("pending_legislation_note", "").lower() or
          "lb 272" in dv.get("pending_legislation_note", "").lower(),
          "NE should have pending legislation note")

# ── North Dakota ──
if "ND" in states_by_code:
    nd_vb = states_by_code["ND"]["veteran_benefits"]
    dvc = nd_vb.get("disabled_veteran_property_tax_credit", {})
    check("T3D-220-ND-credit", dvc.get("exemption_type") == "credit",
          "ND should be 'credit' type")
    check("T3D-221-ND-50pct", dvc.get("eligibility", {}).get("rating_required") == 50,
          "ND should require 50% minimum")
    check("T3D-222-ND-9000", "9,000" in dvc.get("description", "") or "9000" in dvc.get("description", ""),
          "ND should reference $9,000 taxable value")
    check("T3D-223-ND-proportional", "proportional" in dvc.get("description", "").lower() or
          "percentage" in dvc.get("description", "").lower(),
          "ND credit should be proportional to disability rating")
    check("T3D-224-ND-iu", dvc.get("eligibility", {}).get("iu_eligible") == True,
          "ND should accept IU")
    check("T3D-225-ND-survivor", dvc.get("survivor_transfer") == True,
          "ND should have survivor transfer")
    check("T3D-226-ND-dic", "dic" in str(dvc.get("survivor_conditions", {})).lower(),
          "ND should mention DIC spouse gets 100% credit")
    check("T3D-227-ND-married", "married" in dvc.get("married_veterans_note", "").lower(),
          "ND should have married veterans cap note")
    check("T3D-228-ND-april1", "april 1" in dvc.get("application", {}).get("filing_deadline", "").lower(),
          "ND deadline should be April 1")
    # Paraplegic
    para = nd_vb.get("paraplegic_veteran_property_tax_exemption", {})
    check("T3D-229-ND-para", para.get("available") == True,
          "ND should have paraplegic exemption")
    check("T3D-230-ND-para-120k", "120,000" in para.get("description", "") or "120000" in para.get("description", ""),
          "ND paraplegic should reference $120,000")

# ── Rhode Island ──
if "RI" in states_by_code:
    ri_vb = states_by_code["RI"]["veteran_benefits"]
    vpe = ri_vb.get("veteran_property_tax_exemption", {})
    check("T3D-240-RI-partial", vpe.get("exemption_type") == "partial",
          "RI should be 'partial' type")
    ri_desc_lower = vpe.get("description", "").lower()
    check("T3D-241-RI-municipal", "municipal" in ri_desc_lower or
          "municipality" in ri_desc_lower or "city and town" in ri_desc_lower or
          "each city" in ri_desc_lower,
          "RI should note municipality/city-town administration")
    check("T3D-242-RI-44-3-4", "44-3-4" in vpe.get("authority", ""),
          "RI should cite RIGL 44-3-4")
    check("T3D-243-RI-wartime", vpe.get("eligibility", {}).get("wartime_service_required") == True,
          "RI should require wartime service")
    check("T3D-244-RI-totally-disabled", "totally disabled" in str(vpe.get("totally_disabled_veteran_enhanced", {})).lower() or
          "100%" in str(vpe.get("totally_disabled_veteran_enhanced", {})),
          "RI should have totally disabled enhanced section")
    check("T3D-245-RI-sah", "specially adapted" in str(vpe.get("totally_disabled_veteran_enhanced", {})).lower() or
          "adapted housing" in str(vpe.get("totally_disabled_veteran_enhanced", {})).lower(),
          "RI should mention specially adapted housing")
    check("T3D-246-RI-motor", "vehicle" in str(vpe).lower() or "motor" in str(vpe).lower(),
          "RI should mention motor vehicle exemption")
    check("T3D-247-RI-survivor", vpe.get("survivor_transfer") == True,
          "RI should have survivor transfer")

# ── South Dakota ──
if "SD" in states_by_code:
    sd_vb = states_by_code["SD"]["veteran_benefits"]
    dve = sd_vb.get("disabled_veteran_property_tax_exemption", {})
    check("T3D-260-SD-partial", dve.get("exemption_type") == "partial",
          "SD disabled vet should be 'partial'")
    check("T3D-261-SD-200k", "200,000" in dve.get("description", "") or "200000" in dve.get("description", ""),
          "SD should reference $200,000 exemption")
    check("T3D-262-SD-pt", dve.get("eligibility", {}).get("pt_required") == True,
          "SD should require P&T")
    check("T3D-263-SD-survivor-150k", "150,000" in str(dve.get("survivor_conditions", {})),
          "SD surviving spouse should reference $150,000")
    check("T3D-264-SD-nov1", "november 1" in dve.get("application", {}).get("filing_deadline", "").lower(),
          "SD deadline should be November 1")
    check("T3D-265-SD-confidential", "confidential" in dve.get("confidentiality_note", "").lower(),
          "SD should note application confidentiality")
    check("T3D-266-SD-10-4-40", "10-4-40" in dve.get("authority", ""),
          "SD should cite SDCL 10-4-40")
    # Paraplegic
    para = sd_vb.get("paraplegic_veteran_property_tax_exemption", {})
    check("T3D-267-SD-para-full", para.get("exemption_type") == "full",
          "SD paraplegic should be full exemption")
    check("T3D-268-SD-wheelchair", "wheelchair" in para.get("eligibility", {}).get("wheelchair_note", "").lower() or
          "wheelchair" in para.get("description", "").lower(),
          "SD should mention wheelchair requirement")
    check("T3D-269-SD-one-year", "one" in str(para.get("eligibility", {})).lower() and
          "year" in str(para.get("eligibility", {})).lower(),
          "SD should mention one-year occupancy")
    check("T3D-270-SD-10-4-24", "10-4-24" in para.get("authority", ""),
          "SD paraplegic should cite SDCL 10-4-24.10")

# ── Vermont ──
if "VT" in states_by_code:
    vt_vb = states_by_code["VT"]["veteran_benefits"]
    dve = vt_vb.get("disabled_veteran_property_tax_exemption", {})
    check("T3D-280-VT-reduction", dve.get("exemption_type") == "reduction",
          "VT should be 'reduction' type")
    check("T3D-281-VT-10k-min", dve.get("exemption_range", {}).get("minimum") == 10000,
          "VT minimum should be $10,000")
    check("T3D-282-VT-40k-max", dve.get("exemption_range", {}).get("maximum") == 40000,
          "VT maximum should be $40,000")
    check("T3D-283-VT-50pct", dve.get("eligibility", {}).get("rating_required") == 50,
          "VT should require 50% minimum")
    check("T3D-284-VT-non-sc", "non-service" in dve.get("eligibility", {}).get("rating_note", "").lower() or
          "pension" in dve.get("eligibility", {}).get("rating_note", "").lower(),
          "VT should mention non-service-connected pension eligibility")
    check("T3D-285-VT-medical-ret", "medical retirement" in dve.get("eligibility", {}).get("rating_note", "").lower(),
          "VT should mention permanent medical retirement eligibility")
    check("T3D-286-VT-3802", "3802" in dve.get("authority", ""),
          "VT should cite 32 VSA §3802")
    check("T3D-287-VT-survivor", dve.get("survivor_transfer") == True,
          "VT should have survivor transfer")
    check("T3D-288-VT-minor", dve.get("survivor_conditions", {}).get("minor_children") == True,
          "VT should allow minor children to continue exemption")

# ── Wyoming ──
if "WY" in states_by_code:
    wy_vb = states_by_code["WY"]["veteran_benefits"]
    vpe = wy_vb.get("veteran_property_tax_exemption", {})
    check("T3D-300-WY-reduction", vpe.get("exemption_type") == "reduction",
          "WY should be 'reduction' type")
    check("T3D-301-WY-6000", vpe.get("exemption_amount_assessed") == 6000,
          f"WY should be $6,000 assessed, got {vpe.get('exemption_amount_assessed')}")
    check("T3D-302-WY-2025-increase", "3,000" in vpe.get("exemption_note", "") or
          "doubled" in vpe.get("exemption_note", "").lower(),
          "WY should note 2025 increase from $3,000")
    check("T3D-303-WY-3year", "3" in str(vpe.get("eligibility", {}).get("residency_requirement", "")) and
          "year" in str(vpe.get("eligibility", {}).get("residency_requirement", "")).lower(),
          "WY should require 3 years residency")
    check("T3D-304-WY-criteria", len(vpe.get("eligibility", {}).get("qualifying_criteria", [])) >= 4,
          "WY should have at least 4 qualifying criteria")
    check("T3D-305-WY-vehicle", vpe.get("vehicle_alternative", {}).get("available") == True,
          "WY should have vehicle registration alternative")
    check("T3D-306-WY-180", "180" in str(vpe.get("vehicle_alternative", {})),
          "WY vehicle alternative should mention ~$180")
    check("T3D-307-WY-may", "may" in vpe.get("application", {}).get("filing_deadline", "").lower(),
          "WY deadline should mention May")
    check("T3D-308-WY-annual", "annual" in vpe.get("application", {}).get("renewal_note", "").lower(),
          "WY should note annual application")
    check("T3D-309-WY-survivor", vpe.get("survivor_transfer") == True,
          "WY should have survivor transfer")
    check("T3D-310-WY-39-13-105", "39-13-105" in vpe.get("authority", ""),
          "WY should cite WS §39-13-105")

# ══════════════════════════════════════════════════════════
# SECTION 5 — Cross-state consistency
# ══════════════════════════════════════════════════════════
print("\nSection 5 — Cross-state consistency")

# Full exemption states among tier3d: only NE (for 100% P&T)
full_exemption_codes = []
for code in TIER3D:
    if code not in states_by_code:
        continue
    vb = states_by_code[code]["veteran_benefits"]
    for bkey, bval in vb.items():
        if bkey.startswith("_"):
            continue
        if isinstance(bval, dict) and bval.get("exemption_type") == "full":
            full_exemption_codes.append(code)
            break

check("T3D-400-NE-in-full", "NE" in full_exemption_codes,
      "NE should have at least one 'full' exemption type")
check("T3D-401-SD-para-full", "SD" in full_exemption_codes,
      "SD should have paraplegic 'full' exemption")

# No-income-tax consistency
no_tax_codes = [c for c in TIER3D if c in states_by_code and
                states_by_code[c]["income_tax"].get("has_income_tax") == False]
check("T3D-410-no-tax-count", set(no_tax_codes) == {"SD", "WY"},
      f"SD and WY should be no-income-tax, got {no_tax_codes}")

# All states should have survivor transfer documented
for code in TIER3D:
    if code not in states_by_code:
        continue
    vb = states_by_code[code]["veteran_benefits"]
    has_survivor = False
    for bkey, bval in vb.items():
        if bkey.startswith("_"):
            continue
        if isinstance(bval, dict) and "survivor_transfer" in bval:
            has_survivor = True
            break
    check(f"T3D-420-survivor-{code}", has_survivor,
          f"{code} should have survivor_transfer documented in at least one benefit")

# All military retirement exempt (either True or 'partial')
for code in TIER3D:
    if code not in states_by_code:
        continue
    mil = states_by_code[code]["income_tax"]["military_retirement"]["exempt"]
    check(f"T3D-430-mil-exempt-{code}", mil in [True, "partial"],
          f"{code} military retirement exempt should be True or 'partial', got {mil}")

# ══════════════════════════════════════════════════════════
# SECTION 6 — Manifest checks
# ══════════════════════════════════════════════════════════
print("\nSection 6 — Manifest")

sb_manifest = manifest["files"].get("state_benefits", {})
m_version = float(sb_manifest.get("version", "0"))
check("T3D-500-manifest-version", m_version >= 1.9,
      f"Manifest version should be >= 1.9, got {sb_manifest.get('version')}")

m_desc = sb_manifest.get("description", "")
check("T3D-501-manifest-51", "51" in m_desc or "56" in m_desc,
      "Manifest description should mention 51 or 56 jurisdictions")

# All 6 codes should appear in manifest description
for code in TIER3D:
    check(f"T3D-502-manifest-{code}", code in m_desc,
          f"{code} not found in manifest description")

# ══════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"Total checks: {PASS + FAIL}")
print(f"Passed: {PASS}")
print(f"Failed: {FAIL}")
print(f"Warnings: {WARN}")

if FAIL == 0:
    print(f"\n✓ ALL TIER 3D CHECKS PASSED")
else:
    print(f"\n✗ VALIDATION FAILED")
    sys.exit(1)
