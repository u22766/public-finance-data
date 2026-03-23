"""Validation suite for Federal Retirement Systems Index file."""
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
fpath = os.path.join(repo, "reference", "federal-retirement-systems-index.json")

# === File existence ===
check("IX-001-file-exists", os.path.exists(fpath), fpath)
if not os.path.exists(fpath):
    print(f"SYSTEMS INDEX VALIDATION: {passed} checks passed, {failed} failed")
    sys.exit(1 if failed else 0)

with open(fpath) as f:
    data = json.load(f)

# === Metadata ===
m = data.get("metadata", {})
check("IX-002-metadata-exists", "metadata" in data)
check("IX-003-version", m.get("version") is not None)
check("IX-004-sources", len(m.get("sources", [])) >= 5)

# === Top-level sections ===
check("IX-010-civilian-systems", "civilian_retirement_systems" in data)
check("IX-011-uniformed-services", "uniformed_services_retirement" in data)
check("IX-012-special-category", "special_category_positions_6c" in data)
check("IX-013-dc-plans", "defined_contribution_plans" in data)

# === Civilian systems completeness ===
civ = data.get("civilian_retirement_systems", {})
required_civilian = ["fers", "csrs", "csrs_offset", "fsrds", "fsrds_offset", "fsps", "tvars",
                      "federal_reserve_system", "judicial_retirement_systems"]
for sys_key in required_civilian:
    check(f"IX-020-civ-{sys_key}", sys_key in civ, f"Missing civilian system: {sys_key}")

# === FERS entry ===
fers = civ.get("fers", {})
check("IX-030-fers-name", "Federal Employees Retirement System" in fers.get("full_name", ""))
check("IX-031-fers-established", fers.get("established") == 1987)
check("IX-032-fers-active-pop", fers.get("active_employees_approx", 0) > 2000000)
check("IX-033-fers-annuitants", fers.get("annuitants_approx", 0) > 900000)
check("IX-034-fers-standard-mult", fers.get("standard_multiplier_pct") == 1.0)
check("IX-035-fers-enhanced-mult", fers.get("enhanced_multiplier_pct") == 1.1)
check("IX-036-fers-special-mult", fers.get("special_category_multiplier_pct") == 1.7)
check("IX-037-fers-coverage", fers.get("repo_coverage") == "fully_modeled")
check("IX-038-fers-contrib-pre2013", fers.get("employee_contribution_rates_pct", {}).get("fers_pre_2013") == 0.8)
check("IX-039-fers-contrib-rae", fers.get("employee_contribution_rates_pct", {}).get("fers_rae_2013") == 3.1)
check("IX-039b-fers-contrib-frae", fers.get("employee_contribution_rates_pct", {}).get("fers_frae_2014_plus") == 4.4)

# === CSRS entry ===
csrs = civ.get("csrs", {})
check("IX-040-csrs-established", csrs.get("established") == 1920)
check("IX-041-csrs-contrib", csrs.get("employee_contribution_rate_pct") == 7.0)
check("IX-042-csrs-max-80pct", csrs.get("max_annuity_pct") == 80)
check("IX-043-csrs-coverage", csrs.get("repo_coverage") == "fully_modeled")

# === FSRDS entry ===
fsrds = civ.get("fsrds", {})
check("IX-050-fsrds-mult", fsrds.get("multiplier_pct") == 2.0)
check("IX-051-fsrds-cap", fsrds.get("max_annuity_pct_of_high_3") == 70)
check("IX-052-fsrds-contrib", fsrds.get("employee_contribution_rate_pct") == 7.25)
check("IX-053-fsrds-mandatory", fsrds.get("mandatory_retirement_age") == 65)
check("IX-054-fsrds-coverage", fsrds.get("repo_coverage") == "fully_modeled")
check("IX-055-fsrds-agencies", len(fsrds.get("covered_agencies", [])) >= 5)

# === FSPS entry ===
fsps = civ.get("fsps", {})
check("IX-060-fsps-contrib", fsps.get("employee_contribution_rate_pct") == 1.35)
check("IX-061-fsps-mandatory", fsps.get("mandatory_retirement_age") == 65)
check("IX-062-fsps-coverage", fsps.get("repo_coverage") == "fully_modeled")
check("IX-063-fsps-supplement", fsps.get("annuity_supplement") == True)

# === TVARS entry ===
tvars = civ.get("tvars", {})
check("IX-075-tvars-established", tvars.get("established") == 1939)
check("IX-076-tvars-features", len(tvars.get("key_features", [])) >= 4)
check("IX-077-tvars-rule-of-80", any("rule of 80" in f.lower() for f in tvars.get("key_features", [])))
check("IX-078-tvars-not-tsp", any("not" in f.lower() and ("tsp" in f.lower() or "thrift savings" in f.lower()) for f in tvars.get("key_features", [])))

# === Federal Reserve entry ===
fed = civ.get("federal_reserve_system", {})
check("IX-080-fed-no-employee-contrib", any("no employee contribution" in f.lower() for f in fed.get("key_features", [])))
check("IX-081-fed-separate-thrift", any("thrift plan" in f.lower() for f in fed.get("key_features", [])))

# === Judicial systems ===
jud = civ.get("judicial_retirement_systems", {})
check("IX-085-judicial-systems", len(jud.get("systems", [])) >= 5)
check("IX-086-judicial-catalog-only", jud.get("repo_coverage") == "catalog_only")

# === Uniformed services ===
uni = data.get("uniformed_services_retirement", {})
services = uni.get("eight_uniformed_services", [])
check("IX-090-eight-services", len(services) == 8, f"got {len(services)}")

service_names = [s.get("service", "") for s in services]
for expected in ["Army", "Marine Corps", "Navy", "Air Force", "Space Force", "Coast Guard", "USPHS", "NOAA"]:
    check(f"IX-091-service-{expected.split()[0].lower()}", any(expected in sn for sn in service_names),
          f"Missing service containing: {expected}")

# USPHS/NOAA shutdown vulnerability
usphs = next((s for s in services if "USPHS" in s.get("service", "")), {})
noaa = next((s for s in services if "NOAA" in s.get("service", "")), {})
check("IX-095-usphs-not-protected", usphs.get("protected_during_shutdown") == False)
check("IX-096-noaa-not-protected", noaa.get("protected_during_shutdown") == False)
check("IX-097-usphs-not-mrf", "NOT" in usphs.get("retirement_fund", ""))
check("IX-098-noaa-not-mrf", "NOT" in noaa.get("retirement_fund", ""))

# DoD services ARE protected
army = next((s for s in services if "Army" in s.get("service", "")), {})
check("IX-099-army-protected", army.get("protected_during_shutdown") == True)

# Coast Guard protected since FY2021
cg = next((s for s in services if "Coast Guard" in s.get("service", "")), {})
check("IX-100-cg-protected", cg.get("protected_during_shutdown") == True)
check("IX-101-cg-mrf-note", "FY2021" in cg.get("note", "") or "2021" in cg.get("note", ""))

# Shared retirement systems
shared = uni.get("shared_retirement_systems", [])
check("IX-105-shared-count", len(shared) == 4, f"got {len(shared)}")
shared_names = [s.get("system", "") for s in shared]
for expected in ["Final Pay", "High-3", "REDUX", "Blended Retirement"]:
    check(f"IX-106-shared-{expected.split()[0].lower()}", any(expected in sn for sn in shared_names))

check("IX-107-uniformed-coverage", uni.get("repo_coverage") == "fully_modeled")

# === Special category (6c) positions ===
sc = data.get("special_category_positions_6c", {})
check("IX-110-6c-formula", "1.7%" in sc.get("enhanced_formula", ""))
check("IX-111-6c-additional-contrib", sc.get("additional_contribution_pct") == 0.5)
check("IX-112-6c-categories", len(sc.get("eligible_position_categories", [])) >= 7)

# Mandatory retirement ages
mra = sc.get("mandatory_retirement_ages", {})
check("IX-113-leo-mra-57", mra.get("law_enforcement_officers") == 57)
check("IX-114-ff-mra-57", mra.get("firefighters") == 57)
check("IX-115-atc-mra-56", mra.get("air_traffic_controllers") == 56)

# DHS positions should be represented
categories = sc.get("eligible_position_categories", [])
leo_cat = next((c for c in categories if c.get("category") == "Law Enforcement Officers (LEO)"), {})
dhs_examples = leo_cat.get("examples_by_agency", {}).get("DHS", [])
check("IX-116-dhs-leo-examples", len(dhs_examples) >= 5, f"got {len(dhs_examples)}")
check("IX-117-dhs-has-border-patrol", any("border patrol" in e.lower() for e in dhs_examples))
check("IX-118-dhs-has-ice", any("ice" in e.lower() for e in dhs_examples))
check("IX-119-dhs-has-secret-service", any("secret service" in e.lower() for e in dhs_examples))
check("IX-120-dhs-has-air-marshal", any("air marshal" in e.lower() for e in dhs_examples))
check("IX-121-dhs-has-dla-police", any("dla police" in e.lower() for e in dhs_examples))

# CBPO special provision
cbpo = next((c for c in categories if "CBPO" in c.get("category", "") or "CBP Officer" in c.get("category", "")), {})
check("IX-122-cbpo-exists", cbpo != {}, "CBPO category not found")
check("IX-123-cbpo-authority", "110-161" in cbpo.get("authority", ""))

# FF category
ff_cat = next((c for c in categories if c.get("category") == "Firefighters"), {})
check("IX-124-ff-exists", ff_cat != {})
check("IX-125-ff-dod", "DoD" in ff_cat.get("examples_by_agency", {}))

# ATC category
atc_cat = next((c for c in categories if "Air Traffic" in c.get("category", "")), {})
check("IX-126-atc-exists", atc_cat != {})

# === Defined contribution plans ===
dc = data.get("defined_contribution_plans", {})
check("IX-130-tsp-exists", "tsp" in dc)
check("IX-131-fed-thrift", "federal_reserve_thrift_plan" in dc)
check("IX-132-tva-401k", "tva_401k" in dc)

tsp = dc.get("tsp", {})
check("IX-133-tsp-coverage", tsp.get("repo_coverage") == "fully_modeled")
check("IX-134-tsp-fers-match", "5%" in tsp.get("fers_matching", "") or "4%" in tsp.get("fers_matching", ""))

# === Repo coverage consistency ===
# Every system with repo_coverage should have a valid value
all_systems = []
for section in [civ, dc]:
    for key, val in section.items():
        if isinstance(val, dict) and "repo_coverage" in val:
            all_systems.append((key, val))

valid_coverages = {"fully_modeled", "referenced", "catalog_only"}
for key, val in all_systems:
    check(f"IX-140-coverage-valid-{key}", val.get("repo_coverage") in valid_coverages,
          f"{key}: {val.get('repo_coverage')}")

# Fully modeled entries should have repo_files
for key, val in all_systems:
    if val.get("repo_coverage") == "fully_modeled":
        check(f"IX-141-has-files-{key}", "repo_files" in val or "repo_file" in val,
              f"fully_modeled {key} missing repo_files")

print(f"\nSYSTEMS INDEX VALIDATION: {passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
