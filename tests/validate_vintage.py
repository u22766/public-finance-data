"""Validation suite for data_vintage.json — ensures manifest and vintage stay in sync."""
import json
import os
import re
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
vintage_path = os.path.join(repo, "data_vintage.json")
manifest_path = os.path.join(repo, "manifest.json")

# === File existence ===
check("DV-001-vintage-file-exists", os.path.exists(vintage_path), vintage_path)
check("DV-002-manifest-file-exists", os.path.exists(manifest_path), manifest_path)

if not os.path.exists(vintage_path) or not os.path.exists(manifest_path):
    print(f"DATA VINTAGE VALIDATION: {passed} checks passed, {failed} failed")
    sys.exit(1 if failed else 0)

with open(vintage_path) as f:
    vintage = json.load(f)
with open(manifest_path) as f:
    manifest = json.load(f)

# === Top-level structure ===
check("DV-010-has-bundle-version", "bundle_version" in vintage)
check("DV-011-bundle-version-is-int", isinstance(vintage.get("bundle_version"), int),
      f"got {type(vintage.get('bundle_version')).__name__}")
check("DV-012-bundle-version-positive", vintage.get("bundle_version", 0) >= 1,
      f"got {vintage.get('bundle_version')}")

check("DV-015-has-vintage-schema-version", "vintage_schema_version" in vintage)
check("DV-016-vintage-schema-version-is-string", isinstance(vintage.get("vintage_schema_version"), str))

check("DV-020-has-data-vintage-block", "data_vintage" in vintage)
check("DV-021-data-vintage-is-dict", isinstance(vintage.get("data_vintage"), dict))

if not isinstance(vintage.get("data_vintage"), dict):
    print(f"DATA VINTAGE VALIDATION: {passed} checks passed, {failed} failed")
    sys.exit(1 if failed else 0)

dv = vintage["data_vintage"]

# === Separate vintage entries from comment keys ===
vintage_entries = {k: v for k, v in dv.items() if not k.startswith("_comment")}
comment_keys = {k: v for k, v in dv.items() if k.startswith("_comment")}

# === Cross-reference with manifest ===
manifest_keys = set(manifest.get("files", {}).keys())
vintage_keys = set(vintage_entries.keys())

missing_from_vintage = manifest_keys - vintage_keys
extra_in_vintage = vintage_keys - manifest_keys

check("DV-030-no-manifest-keys-missing-from-vintage",
      len(missing_from_vintage) == 0,
      f"manifest keys without vintage entry: {sorted(missing_from_vintage)}")

check("DV-031-no-extra-keys-in-vintage",
      len(extra_in_vintage) == 0,
      f"vintage keys not in manifest: {sorted(extra_in_vintage)}")

check("DV-032-counts-match",
      len(manifest_keys) == len(vintage_keys),
      f"manifest={len(manifest_keys)}, vintage={len(vintage_keys)}")

# === Entry-level validation ===
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REFLECTS_PATTERN = re.compile(r"^(TY|FY|PY|CY)?\d{4}(-\d{4})?$")

for key, entry in vintage_entries.items():
    prefix = f"DV-100-{key}"

    # Must be a dict
    check(f"{prefix}-is-dict", isinstance(entry, dict), f"got {type(entry).__name__}")
    if not isinstance(entry, dict):
        continue

    # Must have 'reflects'
    check(f"{prefix}-has-reflects", "reflects" in entry)

    # 'reflects' format: optional prefix (TY/FY/PY/CY) + 4-digit year, optionally -year for ranges
    reflects = entry.get("reflects", "")
    check(f"{prefix}-reflects-format", REFLECTS_PATTERN.match(reflects),
          f"got '{reflects}'")

    # Must have at least one of rates_effective or last_entry_year
    has_rates_eff = "rates_effective" in entry
    has_last_entry = "last_entry_year" in entry
    check(f"{prefix}-has-date-field", has_rates_eff or has_last_entry,
          "needs rates_effective or last_entry_year")

    # If rates_effective present, validate format
    if has_rates_eff:
        re_val = entry["rates_effective"]
        check(f"{prefix}-rates-effective-format", DATE_PATTERN.match(str(re_val)),
              f"got '{re_val}'")

    # If last_entry_year present, validate it's an integer
    if has_last_entry:
        ley = entry["last_entry_year"]
        check(f"{prefix}-last-entry-year-is-int", isinstance(ley, int),
              f"got {type(ley).__name__}: {ley}")
        if isinstance(ley, int):
            check(f"{prefix}-last-entry-year-reasonable", 2000 <= ley <= 2100,
                  f"got {ley}")

    # No unexpected keys
    allowed_keys = {"reflects", "rates_effective", "last_entry_year"}
    unexpected = set(entry.keys()) - allowed_keys
    check(f"{prefix}-no-unexpected-keys", len(unexpected) == 0,
          f"unexpected: {unexpected}")

# === No consumer-specific references ===
vintage_str = json.dumps(vintage).lower()
for term in ["meridian", "engine", "wizard", "e4 ", "e5 ", "e18 ", "e35 ", "e36 ", "e40 "]:
    check(f"DV-200-no-consumer-ref-{term.strip()}",
          term not in vintage_str,
          f"found '{term.strip()}' in file")

# === Summary ===
print(f"DATA VINTAGE VALIDATION: {passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
