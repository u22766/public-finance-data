#!/usr/bin/env python3
"""
Validate county property tax files across all states.
Session 46: Initial build — covers 12 state files (AZ, CO, FL, GA, MD, NC, NV, SC, TN, TX, VA, WA).
"""

import json
import glob
import os
import re
import sys

checks = 0
errors = 0

def check(condition, msg):
    global checks, errors
    checks += 1
    if not condition:
        errors += 1
        print(f"  FAIL: {msg}")
        return False
    return True

# State FIPS prefixes
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
    "DC": "11"
}

# States we expect to find (>= check for forward-compat)
EXPECTED_STATES = {"AZ", "CO", "FL", "GA", "MD", "NC", "NV", "SC", "TN", "TX", "VA", "WA"}

# Minimum county counts per state (>= for forward-compat)
MIN_COUNTY_COUNTS = {
    "AZ": 1, "CO": 1, "FL": 4, "GA": 3, "MD": 1, "NC": 1,
    "NV": 1, "SC": 4, "TN": 3, "TX": 1, "VA": 2, "WA": 1
}

# Consumer-agnostic banned terms
BANNED_TERMS = ["engine_usage", "meridian", "Meridian", "engine_number", "engine_ref"]

# PII patterns
PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'credit card'),
]

def validate_file(filepath, state_code):
    """Validate a single county property tax file."""
    global checks, errors

    print(f"\n--- {state_code}: {os.path.basename(filepath)} ---")

    # Load JSON
    try:
        with open(filepath) as f:
            data = json.load(f)
        check(True, "")
    except Exception as e:
        check(False, f"Invalid JSON: {e}")
        return

    raw = open(filepath).read()

    # Consumer-agnostic check
    for term in BANNED_TERMS:
        check(term not in raw, f"Consumer-specific term found: '{term}'")

    # PII check
    for pattern, label in PII_PATTERNS:
        matches = re.findall(pattern, raw)
        check(len(matches) == 0, f"PII detected ({label}): {len(matches)} matches")

    # Metadata
    meta = data.get("metadata", {})
    for field in ["title", "description", "state_code", "version", "last_updated", "sources", "notes"]:
        check(field in meta, f"Missing metadata.{field}")

    check(meta.get("state_code") == state_code, f"state_code mismatch: expected {state_code}, got {meta.get('state_code')}")
    check(isinstance(meta.get("sources"), list) and len(meta.get("sources", [])) > 0, "sources must be non-empty list")

    # Version format
    version = meta.get("version", "")
    check(bool(re.match(r'^\d+\.\d+$', str(version))), f"Version format invalid: {version}")

    # last_updated format
    lu = meta.get("last_updated", "")
    check(bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(lu))), f"last_updated format invalid: {lu}")

    # Counties array
    counties = data.get("counties", [])
    check(isinstance(counties, list) and len(counties) > 0, "counties must be non-empty list")

    # Minimum county count
    min_count = MIN_COUNTY_COUNTS.get(state_code, 1)
    check(len(counties) >= min_count, f"Expected >= {min_count} counties, got {len(counties)}")

    # Track FIPS for uniqueness
    fips_seen = set()

    for county in counties:
        cname = county.get("county", "UNKNOWN")

        # Required fields
        for field in ["county", "state_code", "fips", "tax_year", "property_tax", "veteran_exemptions"]:
            check(field in county, f"{cname}: missing '{field}'")

        # application block
        check("application" in county, f"{cname}: missing 'application'")
        if "application" in county:
            app = county["application"]
            check("office" in app, f"{cname}: missing application.office")
            check("url" in app, f"{cname}: missing application.url")
            url = app.get("url", "")
            check(url.startswith("https://"), f"{cname}: application URL not HTTPS: {url}")

        # State code consistency
        check(county.get("state_code") == state_code, f"{cname}: state_code mismatch")

        # FIPS validation
        fips = county.get("fips", "")
        check(len(str(fips)) == 5 and str(fips).isdigit(), f"{cname}: FIPS format invalid: {fips}")

        expected_prefix = STATE_FIPS.get(state_code, "??")
        check(str(fips).startswith(expected_prefix), f"{cname}: FIPS {fips} doesn't match state prefix {expected_prefix}")

        # FIPS uniqueness within file
        check(fips not in fips_seen, f"{cname}: duplicate FIPS {fips}")
        fips_seen.add(fips)

        # Tax year
        check(county.get("tax_year") in [2024, 2025, 2026], f"{cname}: tax_year {county.get('tax_year')} outside expected range")

        # Property tax block
        pt = county.get("property_tax", {})
        check(isinstance(pt, dict) and len(pt) > 0, f"{cname}: property_tax must be non-empty dict")

        # At least one rate-like field must exist
        rate_fields = [k for k in pt.keys() if "rate" in k.lower() or "mill" in k.lower() or "levy" in k.lower()]
        check(len(rate_fields) > 0, f"{cname}: no rate/millage/levy field found in property_tax")

        # Rate sanity — any numeric rate field should be positive
        for k, v in pt.items():
            if k.startswith("_"):
                continue
            if isinstance(v, (int, float)) and ("rate" in k.lower() or "mill" in k.lower() or "levy" in k.lower()):
                check(v > 0, f"{cname}: {k} = {v} (expected positive)")
                # Millage should be < 500, rate_per_100 < 10, rate_per_1000 < 50
                if "mill" in k.lower() or "levy" in k.lower():
                    check(v < 500, f"{cname}: {k} = {v} (suspiciously high millage)")
                elif "per_1000" in k.lower():
                    check(v < 50, f"{cname}: {k} = {v} (suspiciously high rate per $1000)")
                elif "per_100" in k.lower():
                    check(v < 10, f"{cname}: {k} = {v} (suspiciously high rate per $100)")

        # Assessment ratio sanity if present
        for k, v in pt.items():
            if "assessment_ratio" in k.lower() and isinstance(v, (int, float)):
                # Keys ending in _pct use percentage (0-100); plain ratio keys use 0-1
                if "_pct" in k.lower():
                    check(0 < v <= 100, f"{cname}: {k} = {v} (expected 0 < pct <= 100)")
                else:
                    check(0 < v <= 1.0, f"{cname}: {k} = {v} (expected 0 < ratio <= 1.0)")

        # Homestead exemption sanity if present
        for k, v in pt.items():
            if "homestead" in k.lower() and isinstance(v, (int, float)):
                check(v >= 0, f"{cname}: {k} = {v} (expected non-negative)")

        # Veteran exemptions
        ve = county.get("veteran_exemptions", {})
        check(isinstance(ve, dict) and len(ve) > 0, f"{cname}: veteran_exemptions must be non-empty dict")

        # At least one exemption entry should exist
        exemption_keys = [k for k in ve.keys() if not k.startswith("_")]
        check(len(exemption_keys) > 0, f"{cname}: no veteran exemption entries found")

        # If disabled_veteran_100_pct exists, validate its subfields
        if "disabled_veteran_100_pct" in ve:
            dv = ve["disabled_veteran_100_pct"]
            check("type" in dv, f"{cname}: vet 100% missing 'type'")
            check(dv.get("type") in ["full_exemption", "partial_exemption"], f"{cname}: vet 100% type = {dv.get('type')}")
            check("eligibility" in dv, f"{cname}: vet 100% missing 'eligibility'")
            check("applies_to" in dv, f"{cname}: vet 100% missing 'applies_to'")

        # All exemption entries should have a type
        for ek, ev in ve.items():
            if ek.startswith("_"):
                continue
            if isinstance(ev, dict):
                check("type" in ev, f"{cname}: {ek} missing 'type'")

    print(f"  {state_code}: {len(counties)} counties validated")


# ── Main ──────────────────────────────────────────────────────────────

print("=" * 60)
print("County Property Tax Validation Suite")
print("=" * 60)

# Discover all county property tax files
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern = os.path.join(base_dir, "states", "*", "county-property-tax.json")
files_found = sorted(glob.glob(pattern))

check(len(files_found) >= len(EXPECTED_STATES), f"Expected >= {len(EXPECTED_STATES)} state files, found {len(files_found)}")

# Extract state codes from file paths
states_found = set()
for f in files_found:
    with open(f) as fh:
        d = json.load(fh)
    sc = d.get("metadata", {}).get("state_code", "??")
    states_found.add(sc)

# Verify expected states present
for expected in EXPECTED_STATES:
    check(expected in states_found, f"Missing expected state: {expected}")

# Validate each file
for filepath in files_found:
    with open(filepath) as fh:
        d = json.load(fh)
    state_code = d.get("metadata", {}).get("state_code", "??")
    validate_file(filepath, state_code)

# Cross-file checks
print(f"\n--- Cross-file checks ---")

# FIPS uniqueness across ALL files
all_fips = {}
for filepath in files_found:
    with open(filepath) as fh:
        d = json.load(fh)
    sc = d["metadata"]["state_code"]
    for c in d["counties"]:
        fips = c.get("fips", "")
        key = f"{sc}/{c.get('county', '?')}"
        check(fips not in all_fips, f"Cross-file FIPS collision: {fips} in {key} and {all_fips.get(fips, '?')}")
        all_fips[fips] = key

# Total county count
total_counties = sum(len(json.load(open(f))["counties"]) for f in files_found)
check(total_counties >= 23, f"Expected >= 23 total counties, got {total_counties}")
print(f"  Total counties across {len(files_found)} files: {total_counties}")

# ── Summary ───────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
if errors == 0:
    print(f"PASS: {checks}/{checks} checks passed across {len(files_found)} state files")
else:
    print(f"FAIL: {checks - errors}/{checks} passed, {errors} failures")
print(f"{'=' * 60}")

sys.exit(1 if errors else 0)
