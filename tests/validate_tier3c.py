#!/usr/bin/env python3
"""
OM-18 Tier 3C Validation Suite
================================
public-finance-data / tests / validate_tier3c.py

Validates the 10 Tier 3C state entries added in state-benefits v1.8:
LA, MA, WV, NH, ME, UT, NM, ID, MT, DE

Team Gamma — O&M Session 28 — March 2026
"""

import json
import os
import re
import sys


TIER3C_CODES = ["LA", "MA", "WV", "NH", "ME", "UT", "NM", "ID", "MT", "DE"]

TIER3C_NAMES = {
    "LA": "Louisiana", "MA": "Massachusetts", "WV": "West Virginia",
    "NH": "New Hampshire", "ME": "Maine", "UT": "Utah",
    "NM": "New Mexico", "ID": "Idaho", "MT": "Montana", "DE": "Delaware"
}

VALID_EXEMPTION_TYPES = [
    "full", "partial", "deduction", "reduction",
    "discount", "grant", "credit", "refund"
]


class ValidationResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, name, detail=""):
        self.passed.append(f"  ✓ {name}: {detail}" if detail else f"  ✓ {name}")

    def add_fail(self, name, detail):
        self.failed.append(f"  ✗ {name}: {detail}")

    def add_warning(self, name, detail):
        self.warnings.append(f"  ⚠ {name}: {detail}")


def load_data():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "states", "state-benefits.json")
    with open(path) as f:
        return json.load(f)


def get_state(data, code):
    for s in data["states"]:
        if s["state_code"] == code:
            return s
    return None


# =========================================================================
# Section 1: Structural checks
# =========================================================================

def check_structural(data, r):
    """Structural validation for Tier 3C."""
    # Version >= 1.8
    v = data.get("version", "0")
    try:
        vf = float(v)
    except (ValueError, TypeError):
        vf = 0.0
    if vf >= 1.8:
        r.add_pass("STRUCT-01", f"Version {v} >= 1.8")
    else:
        r.add_fail("STRUCT-01", f"Version {v} < 1.8")

    # State count >= 45
    count = len(data.get("states", []))
    if count >= 45:
        r.add_pass("STRUCT-02", f"State count {count} >= 45")
    else:
        r.add_fail("STRUCT-02", f"State count {count} < 45")

    # All 10 states present with correct names
    for code in TIER3C_CODES:
        s = get_state(data, code)
        if s is None:
            r.add_fail(f"STRUCT-{code}", f"State {code} not found")
        else:
            r.add_pass(f"STRUCT-{code}", f"{code} present")
            expected_name = TIER3C_NAMES[code]
            if s.get("state_name") == expected_name:
                r.add_pass(f"STRUCT-{code}-name", f"{code} = {expected_name}")
            else:
                r.add_fail(f"STRUCT-{code}-name",
                           f"Expected {expected_name}, got {s.get('state_name')}")


# =========================================================================
# Section 2: Income tax checks
# =========================================================================

def check_income_tax(data, r):
    """Income tax validation for all 10 states."""
    for code in TIER3C_CODES:
        s = get_state(data, code)
        if s is None:
            continue
        it = s.get("income_tax", {})

        # Required keys
        for key in ["military_retirement", "va_compensation"]:
            if key in it:
                r.add_pass(f"IT-{code}-{key}", f"{code} has {key}")
            else:
                r.add_fail(f"IT-{code}-{key}", f"{code} missing {key}")

        # Military retirement check
        mr = it.get("military_retirement", {})
        if "exempt" in mr:
            r.add_pass(f"IT-{code}-mr-exempt", f"{code} military_retirement.exempt defined")
        else:
            r.add_fail(f"IT-{code}-mr-exempt", f"{code} military_retirement.exempt missing")

        # VA comp should always be exempt
        va = it.get("va_compensation", {})
        if va.get("exempt") is True:
            r.add_pass(f"IT-{code}-va", f"{code} VA comp exempt")
        else:
            r.add_fail(f"IT-{code}-va", f"{code} VA comp should be exempt")

    # Specific checks
    # NH has no income tax
    nh = get_state(data, "NH")
    if nh:
        it = nh.get("income_tax", {})
        if it.get("top_rate") == 0 or it.get("rate_type") == "none":
            r.add_pass("IT-NH-none", "NH correctly has no income tax")
        else:
            r.add_fail("IT-NH-none", f"NH should have no income tax, got rate_type={it.get('rate_type')}")

    # LA flat 3% rate
    la = get_state(data, "LA")
    if la:
        it = la.get("income_tax", {})
        if it.get("top_rate") == 0.03:
            r.add_pass("IT-LA-rate", "LA top rate = 3%")
        else:
            r.add_fail("IT-LA-rate", f"LA top rate should be 0.03, got {it.get('top_rate')}")

    # UT flat 4.5% rate
    ut = get_state(data, "UT")
    if ut:
        it = ut.get("income_tax", {})
        if it.get("top_rate") == 0.045:
            r.add_pass("IT-UT-rate", "UT top rate = 4.5%")
        else:
            r.add_fail("IT-UT-rate", f"UT top rate should be 0.045, got {it.get('top_rate')}")

    # States with full military retirement exemption
    full_exempt_states = ["LA", "MA", "WV", "ME"]
    for code in full_exempt_states:
        s = get_state(data, code)
        if s:
            mr = s.get("income_tax", {}).get("military_retirement", {})
            if mr.get("exempt") is True:
                r.add_pass(f"IT-{code}-full-exempt", f"{code} military retirement fully exempt")
            else:
                r.add_fail(f"IT-{code}-full-exempt", f"{code} military retirement should be fully exempt")

    # States with partial or credit-based exemption
    partial_states = ["NM", "ID", "MT", "DE"]
    for code in partial_states:
        s = get_state(data, code)
        if s:
            mr = s.get("income_tax", {}).get("military_retirement", {})
            if mr.get("exempt") is False and ("note" in mr or "exempt_note" in mr):
                r.add_pass(f"IT-{code}-partial", f"{code} military retirement partial with note")
            elif mr.get("exempt") is True:
                r.add_pass(f"IT-{code}-partial", f"{code} military retirement exempt (credit mechanism)")
            else:
                r.add_fail(f"IT-{code}-partial", f"{code} should have note explaining partial exemption")

    # UT credit mechanism
    if ut:
        mr = ut.get("income_tax", {}).get("military_retirement", {})
        note = mr.get("note", "")
        if "credit" in note.lower() or "4.5%" in note:
            r.add_pass("IT-UT-credit", "UT uses credit mechanism for military retirement")
        else:
            r.add_fail("IT-UT-credit", "UT note should mention credit mechanism")


# =========================================================================
# Section 3: Veteran benefits structure
# =========================================================================

def check_veteran_benefits(data, r):
    """Veteran benefits structural validation."""
    for code in TIER3C_CODES:
        s = get_state(data, code)
        if s is None:
            continue
        vb = s.get("veteran_benefits", {})

        # Must have at least one benefit entry (excluding _schema_note)
        benefit_keys = [k for k in vb if not k.startswith("_")]
        if len(benefit_keys) >= 1:
            r.add_pass(f"VB-{code}-exists", f"{code} has {len(benefit_keys)} benefit(s)")
        else:
            r.add_fail(f"VB-{code}-exists", f"{code} has no veteran benefits")

        # Each benefit must have exemption_type and available
        for bk in benefit_keys:
            b = vb[bk]
            if not isinstance(b, dict):
                continue
            if "exemption_type" in b:
                et = b["exemption_type"]
                if et in VALID_EXEMPTION_TYPES:
                    r.add_pass(f"VB-{code}-{bk}-type", f"{et} is valid")
                else:
                    r.add_fail(f"VB-{code}-{bk}-type", f"Invalid exemption_type: {et}")
            else:
                r.add_fail(f"VB-{code}-{bk}-type", f"{code}.{bk} missing exemption_type")

        # Sources must not be empty
        sources = s.get("sources", [])
        if len(sources) >= 1:
            r.add_pass(f"VB-{code}-sources", f"{code} has {len(sources)} source(s)")
        else:
            r.add_fail(f"VB-{code}-sources", f"{code} has no sources")


# =========================================================================
# Section 4: State-specific spot checks
# =========================================================================

def check_state_specific(data, r):
    """Detailed spot checks for each Tier 3C state."""

    # --- LA ---
    la = get_state(data, "LA")
    if la:
        vb = la.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "full":
            r.add_pass("LA-01", "LA 100% veterans get full exemption")
        else:
            r.add_fail("LA-01", "LA should have full exemption for 100%")

        tiers = dv.get("tiers", [])
        if len(tiers) >= 3:
            r.add_pass("LA-02", f"LA has {len(tiers)} benefit tiers")
        else:
            r.add_fail("LA-02", f"LA should have 3 tiers, got {len(tiers)}")

        elig = dv.get("eligibility", {})
        if elig.get("rating_required") == 50:
            r.add_pass("LA-03", "LA benefits start at 50%")
        else:
            r.add_fail("LA-03", "LA rating_required should be 50")

        if elig.get("iu_eligible") is True:
            r.add_pass("LA-04", "LA IU eligible")
        else:
            r.add_fail("LA-04", "LA IU should be eligible")

        if dv.get("survivor_transfer") is True:
            r.add_pass("LA-05", "LA survivor transfer available")
        else:
            r.add_fail("LA-05", "LA should have survivor transfer")

        it = la.get("income_tax", {})
        if it.get("rate_type") == "flat":
            r.add_pass("LA-06", "LA flat tax")
        else:
            r.add_fail("LA-06", "LA should be flat tax")

    # --- MA ---
    ma = get_state(data, "MA")
    if ma:
        vb = ma.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "partial":
            r.add_pass("MA-01", "MA partial exemption (Clause 22)")
        else:
            r.add_fail("MA-01", "MA should be partial exemption")

        ba = dv.get("base_amounts", {})
        if ba.get("ten_percent_or_purple_heart") == 400:
            r.add_pass("MA-02", "MA base amount $400 for 10%")
        else:
            r.add_fail("MA-02", f"MA 10% amount should be $400")

        if ba.get("paraplegic_or_100pct_blind") == 1500:
            r.add_pass("MA-03", "MA $1,500 for paraplegic/blind")
        else:
            r.add_fail("MA-03", "MA paraplegic amount should be $1,500")

        if "hero_act_note" in dv:
            r.add_pass("MA-04", "MA HERO Act note present")
        else:
            r.add_fail("MA-04", "MA should mention HERO Act")

        pl = dv.get("pending_legislation", {})
        if "2046" in pl.get("bill", "") or "3836" in pl.get("bill", ""):
            r.add_pass("MA-05", "MA pending legislation noted")
        else:
            r.add_fail("MA-05", "MA should note S.2046/H.3836")

    # --- WV ---
    wv = get_state(data, "WV")
    if wv:
        vb = wv.get("veteran_benefits", {})
        # Should have both credit and exemption
        if "disabled_veteran_real_property_tax_credit" in vb:
            r.add_pass("WV-01", "WV has property tax credit")
        else:
            r.add_fail("WV-01", "WV should have property tax credit")

        credit = vb.get("disabled_veteran_real_property_tax_credit", {})
        if credit.get("exemption_type") == "credit":
            r.add_pass("WV-02", "WV credit type correct")
        else:
            r.add_fail("WV-02", "WV credit exemption_type should be 'credit'")

        elig = credit.get("eligibility", {})
        if elig.get("rating_required") == 90:
            r.add_pass("WV-03", "WV credit requires 90%")
        else:
            r.add_fail("WV-03", f"WV credit rating should be 90, got {elig.get('rating_required')}")

        if "disabled_veteran_property_tax_exemption" in vb:
            r.add_pass("WV-04", "WV has P&T exemption under §11-6B")
        else:
            r.add_fail("WV-04", "WV should have §11-6B exemption")

    # --- NH ---
    nh = get_state(data, "NH")
    if nh:
        vb = nh.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "full":
            r.add_pass("NH-01", "NH full exemption for 100% P&T")
        else:
            r.add_fail("NH-01", "NH should be full exemption")

        elig = dv.get("eligibility", {})
        if elig.get("pt_required") is True:
            r.add_pass("NH-02", "NH requires P&T")
        else:
            r.add_fail("NH-02", "NH should require P&T")

        if "wartime_veteran_property_tax_credit" in vb:
            r.add_pass("NH-03", "NH has wartime credit")
        else:
            r.add_fail("NH-03", "NH should have wartime credit")

        it = nh.get("income_tax", {})
        if it.get("rate_type") == "none" or it.get("top_rate") == 0:
            r.add_pass("NH-04", "NH no income tax confirmed")
        else:
            r.add_fail("NH-04", "NH should have no income tax")

    # --- ME ---
    me = get_state(data, "ME")
    if me:
        vb = me.get("veteran_benefits", {})
        dv = vb.get("veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "partial":
            r.add_pass("ME-01", "ME partial exemption")
        else:
            r.add_fail("ME-01", "ME should be partial")

        amounts = dv.get("amounts", {})
        if amounts.get("standard_exemption") == 6000:
            r.add_pass("ME-02", "ME $6,000 standard")
        else:
            r.add_fail("ME-02", "ME standard should be $6,000")

        if amounts.get("paraplegic_adapted_housing") == 50000:
            r.add_pass("ME-03", "ME $50,000 paraplegic")
        else:
            r.add_fail("ME-03", "ME paraplegic should be $50,000")

        it = me.get("income_tax", {})
        mr_note = it.get("military_retirement", {}).get("note", "")
        if "space force" in mr_note.lower() or "Space Force" in mr_note:
            r.add_pass("ME-04", "ME notes Space Force expansion")
        else:
            r.add_fail("ME-04", "ME should note Space Force expansion for 2026")

    # --- UT ---
    ut = get_state(data, "UT")
    if ut:
        vb = ut.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "partial":
            r.add_pass("UT-01", "UT partial exemption")
        else:
            r.add_fail("UT-01", "UT should be partial")

        elig = dv.get("eligibility", {})
        if elig.get("rating_required") == 10:
            r.add_pass("UT-02", "UT starts at 10%")
        else:
            r.add_fail("UT-02", f"UT rating should start at 10, got {elig.get('rating_required')}")

        if elig.get("income_limits_apply") is True:
            r.add_pass("UT-03", "UT has income limits")
        else:
            r.add_fail("UT-03", "UT should note income limits")

    # --- NM ---
    nm = get_state(data, "NM")
    if nm:
        vb = nm.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_exemption", {})
        if dv.get("exemption_type") == "full":
            r.add_pass("NM-01", "NM full exemption for 100% P&T")
        else:
            r.add_fail("NM-01", "NM should be full for 100% P&T")

        if "proportional" in str(dv.get("description", "")).lower():
            r.add_pass("NM-02", "NM mentions proportional exemption")
        else:
            r.add_fail("NM-02", "NM should mention proportional exemption for 2026+")

        if dv.get("effective_date_proportional") == "2026-01-01":
            r.add_pass("NM-03", "NM proportional effective 2026-01-01")
        else:
            r.add_fail("NM-03", "NM proportional should be effective 2026-01-01")

        # $10,000 standard veteran exemption in property_tax
        pt = nm.get("property_tax", {}).get("exemptions", [])
        has_10k = any(e.get("amount") == 10000 for e in pt)
        if has_10k:
            r.add_pass("NM-04", "NM $10,000 standard veteran exemption")
        else:
            r.add_fail("NM-04", "NM should have $10,000 standard veteran exemption")

        # Military retirement partial $40,000
        it = nm.get("income_tax", {})
        mr_note = it.get("military_retirement", {}).get("note", "")
        if "40,000" in mr_note or "40000" in mr_note:
            r.add_pass("NM-05", "NM $40,000 military retirement subtraction")
        else:
            r.add_fail("NM-05", "NM should note $40,000 subtraction")

    # --- ID ---
    id_state = get_state(data, "ID")
    if id_state:
        vb = id_state.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_reduction", {})
        if dv.get("exemption_type") == "reduction":
            r.add_pass("ID-01", "ID reduction type")
        else:
            r.add_fail("ID-01", "ID should be reduction type")

        if dv.get("max_reduction") == 1500:
            r.add_pass("ID-02", "ID max $1,500 reduction")
        else:
            r.add_fail("ID-02", f"ID max reduction should be $1,500")

        elig = dv.get("eligibility", {})
        if elig.get("iu_eligible") is True:
            r.add_pass("ID-03", "ID IU eligible")
        else:
            r.add_fail("ID-03", "ID IU should be eligible")

        if elig.get("homeowners_exemption_required") is True:
            r.add_pass("ID-04", "ID requires homeowner's exemption")
        else:
            r.add_fail("ID-04", "ID should require homeowner's exemption")

        sc = dv.get("survivor_conditions", {})
        if sc.get("not_transferable_to_new_property") is True:
            r.add_pass("ID-05", "ID not transferable to new property")
        else:
            r.add_fail("ID-05", "ID should note non-transferability")

    # --- MT ---
    mt = get_state(data, "MT")
    if mt:
        vb = mt.get("veteran_benefits", {})
        dv = vb.get("disabled_veteran_property_tax_reduction", {})
        if dv.get("exemption_type") == "reduction":
            r.add_pass("MT-01", "MT reduction type")
        else:
            r.add_fail("MT-01", "MT should be reduction type")

        desc = dv.get("description", "")
        if "50%" in desc and "100%" in desc:
            r.add_pass("MT-02", "MT describes reduction tiers")
        else:
            r.add_fail("MT-02", "MT should describe 50-100% reduction tiers")

        elig = dv.get("eligibility", {})
        if elig.get("income_limits_apply") is True:
            r.add_pass("MT-03", "MT has income limits")
        else:
            r.add_fail("MT-03", "MT should have income limits")

        if elig.get("iu_eligible") is True:
            r.add_pass("MT-04", "MT IU eligible")
        else:
            r.add_fail("MT-04", "MT IU should be eligible")

        if dv.get("auto_renewal") is True:
            r.add_pass("MT-05", "MT auto renewal noted")
        else:
            r.add_fail("MT-05", "MT should have auto renewal")

        occ = elig.get("occupancy_requirement", "")
        if "7 months" in occ:
            r.add_pass("MT-06", "MT 7-month occupancy requirement")
        else:
            r.add_fail("MT-06", "MT should note 7-month occupancy requirement")

    # --- DE ---
    de = get_state(data, "DE")
    if de:
        vb = de.get("veteran_benefits", {})

        # School tax credit
        stc = vb.get("disabled_veteran_school_tax_credit", {})
        if stc.get("exemption_type") == "credit":
            r.add_pass("DE-01", "DE school tax credit type")
        else:
            r.add_fail("DE-01", "DE should have school tax credit")

        elig = stc.get("eligibility", {})
        if elig.get("delaware_resident_years") == 3:
            r.add_pass("DE-02", "DE 3-year residency")
        else:
            r.add_fail("DE-02", "DE should require 3-year residency")

        if elig.get("iu_eligible") is True:
            r.add_pass("DE-03", "DE IU eligible for school credit")
        else:
            r.add_fail("DE-03", "DE IU should be eligible")

        # County exemption
        cty = vb.get("county_property_tax_exemption", {})
        if cty.get("county_administered") is True:
            r.add_pass("DE-04", "DE county-administered")
        else:
            r.add_fail("DE-04", "DE should note county administration")

        if cty.get("exemption_type") == "full":
            r.add_pass("DE-05", "DE county exemption full type")
        else:
            r.add_fail("DE-05", "DE county exemption should be full")

        # Income tax partial
        it = de.get("income_tax", {})
        mr = it.get("military_retirement", {})
        mr_note = mr.get("note", "")
        if "12,500" in mr_note or "12500" in mr_note:
            r.add_pass("DE-06", "DE $12,500 pension exclusion noted")
        else:
            r.add_fail("DE-06", "DE should note $12,500 exclusion")


# =========================================================================
# Section 5: Cross-state consistency
# =========================================================================

def check_cross_state(data, r):
    """Cross-state consistency checks."""
    # States with full property tax exemption at 100%
    full_exempt_expected = ["LA", "NH", "NM"]
    for code in full_exempt_expected:
        s = get_state(data, code)
        if s is None:
            continue
        vb = s.get("veteran_benefits", {})
        has_full = False
        for k, v in vb.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict) and v.get("exemption_type") == "full":
                has_full = True
                break
        if has_full:
            r.add_pass(f"CROSS-{code}-full", f"{code} has full exemption")
        else:
            r.add_fail(f"CROSS-{code}-full", f"{code} should have full exemption type")

    # States with partial/reduction/credit
    partial_expected = ["MA", "WV", "ME", "UT", "ID", "MT", "DE"]
    for code in partial_expected:
        s = get_state(data, code)
        if s is None:
            continue
        vb = s.get("veteran_benefits", {})
        types = set()
        for k, v in vb.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict) and "exemption_type" in v:
                types.add(v["exemption_type"])
        non_full = types - {"full"}
        if non_full or "full" not in types:
            r.add_pass(f"CROSS-{code}-nonfull", f"{code} has non-full type(s): {types}")
        else:
            r.add_warning(f"CROSS-{code}-nonfull", f"{code} only has full types")

    # Survivor transfer documented
    for code in TIER3C_CODES:
        s = get_state(data, code)
        if s is None:
            continue
        vb = s.get("veteran_benefits", {})
        has_survivor = False
        for k, v in vb.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict) and "survivor_transfer" in v:
                has_survivor = True
                break
        if has_survivor:
            r.add_pass(f"CROSS-{code}-survivor", f"{code} documents survivor transfer")
        else:
            r.add_warning(f"CROSS-{code}-survivor", f"{code} missing survivor transfer field")


# =========================================================================
# Section 6: Manifest checks
# =========================================================================

def check_manifest(data, r):
    """Manifest checks for Tier 3C."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "manifest.json")
    with open(path) as f:
        m = json.load(f)
    sb = m.get("files", {}).get("state_benefits", {})
    v = sb.get("version", "")
    try:
        vf = float(v)
    except (ValueError, TypeError):
        vf = 0.0
    if vf >= 1.8:
        r.add_pass("MAN-01", f"Manifest version {v} >= 1.8")
    else:
        r.add_fail("MAN-01", f"Manifest version should be >= 1.8, got {v}")

    desc = sb.get("description", "")
    count_match = re.search(r'(\d+)\s+states', desc)
    count = int(count_match.group(1)) if count_match else 0
    if count >= 45:
        r.add_pass("MAN-02", f"Manifest references {count} states (>= 45)")
    else:
        r.add_fail("MAN-02", f"Manifest should reference >= 45 states, found {count}")

    # All 10 codes in description
    for code in TIER3C_CODES:
        if code in desc:
            r.add_pass(f"MAN-{code}", f"Manifest includes {code}")
        else:
            r.add_fail(f"MAN-{code}", f"Manifest should include {code}")


# =========================================================================
# Main
# =========================================================================

def main():
    data = load_data()
    r = ValidationResult()

    print("=" * 60)
    print("TIER 3C VALIDATION — 10-State Expansion (v1.8)")
    print("States: LA, MA, WV, NH, ME, UT, NM, ID, MT, DE")
    print("=" * 60)

    print("\n--- Section 1: Structural ---")
    check_structural(data, r)
    for line in r.passed[-22:]:  # approximate
        print(line)

    print("\n--- Section 2: Income Tax ---")
    prev = len(r.passed)
    check_income_tax(data, r)
    for line in r.passed[prev:]:
        print(line)
    for line in r.failed:
        print(line)

    print("\n--- Section 3: Veteran Benefits Structure ---")
    prev = len(r.passed)
    check_veteran_benefits(data, r)
    for line in r.passed[prev:]:
        print(line)

    print("\n--- Section 4: State-Specific Spot Checks ---")
    prev = len(r.passed)
    check_state_specific(data, r)
    for line in r.passed[prev:]:
        print(line)

    print("\n--- Section 5: Cross-State Consistency ---")
    prev = len(r.passed)
    check_cross_state(data, r)
    for line in r.passed[prev:]:
        print(line)

    print("\n--- Section 6: Manifest ---")
    prev = len(r.passed)
    check_manifest(data, r)
    for line in r.passed[prev:]:
        print(line)

    print("\n" + "=" * 60)
    print(f"Passed: {len(r.passed)}")
    print(f"Failed: {len(r.failed)}")
    print(f"Warnings: {len(r.warnings)}")

    if r.failed:
        print("\nFAILURES:")
        for f in r.failed:
            print(f)

    if r.warnings:
        print("\nWARNINGS:")
        for w in r.warnings:
            print(w)

    if r.failed:
        print(f"\n✗ TIER 3C VALIDATION FAILED")
        sys.exit(1)
    else:
        print(f"\n✓ ALL TIER 3C CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
