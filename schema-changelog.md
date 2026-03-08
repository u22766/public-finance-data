# Schema Changelog

Documents structural changes and versioning conventions for this repository.

---

## Data Versioning Convention

File versions use a `year.patch` format:

- **Annual refresh:** Version resets to the new year (e.g., `"2027"`)
- **Correction within same year:** Patch number increments (e.g., `"2026.1"`, `"2026.2"`)
- **No patch number = `.0` implied:** `"2026"` and `"2026.0"` are equivalent (the original annual release)

Consumers should compare file versions to determine whether to re-fetch. A version change — whether year or patch — means the file contents have changed.

### Consumer-Side Schema Check

Consumers should check `schema_min_compatible` before reading data:

```javascript
const appSchemaVersion = "2.0"; // hardcoded in consumer app — update after migration
const repoMinCompatible = manifest.schema_min_compatible || "1.0";

if (compareVersions(appSchemaVersion, repoMinCompatible) < 0) {
  // App is too old to read this data safely — fall back to embedded data
  showWarning("Data format has changed. Update your app to use the latest rates.");
  return;
}

// Safe to proceed — compare file versions and fetch updated files

function compareVersions(a, b) {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    if ((pa[i] || 0) < (pb[i] || 0)) return -1;
    if ((pa[i] || 0) > (pb[i] || 0)) return 1;
  }
  return 0;
}
```

---

## Data Corrections Log

### rates-annual.json v2026.1

**Date:** 2026-03-08
**Change type:** Value correction (no schema impact)

Corrected federal income tax bracket middle cutoffs for both single and married-filing-jointly. Original values had been computed from OBBBA adjustment percentages rather than taken directly from IRS tables.

**Source:** IRS Rev. Proc. 2025-32, Section 4.01, Tables 1 (single) and 3 (MFJ)

**Single filer corrections:**

| Bracket | Before | After |
|---|---|---|
| 12% max | 50,650 | 50,400 |
| 22% max | 106,525 | 105,700 |
| 32% max | 256,450 | 256,225 |

**MFJ corrections:**

| Bracket | Before | After |
|---|---|---|
| 12% max | 101,300 | 100,800 |
| 22% max | 213,050 | 211,400 |
| 24% max | 403,500 | 403,550 |
| 32% max | 512,850 | 512,450 |

All corresponding `min` values on adjacent brackets adjusted accordingly. 10% and 37% endpoints were already correct and unchanged.

---

## Schema Version 2.0 — Domain-Based Restructure

**Date:** 2026-03-08
**schema_version:** 2.0
**schema_min_compatible:** 2.0 (BREAKING — all file paths changed)

Reorganized repository from feature-based folders (`rates/`, `plans/`, `reference/`) to domain-based folders (`federal/`, `states/`, `reference/`). Split `plan-library.json` into jurisdiction-specific files. Extracted VA and VGLI data from `rates-annual.json` into dedicated files under `federal/veterans-affairs/`.

### Why This Is a Breaking Change

All file URL paths in the manifest changed. Consumer applications using `manifest.files.*.url` to fetch files must update to the new paths. The `schema_min_compatible` bump to 2.0 ensures apps on schema 1.x will trigger their fallback behavior rather than silently failing.

### Path Migration Map

| Old Path (schema 1.x) | New Path (schema 2.0) | Notes |
|---|---|---|
| `rates/rates-annual.json` | `federal/rates-annual.json` | VA and VGLI sections removed |
| `rates/pay-tables.json` | `federal/pay-tables.json` | Unchanged content |
| — | `federal/veterans-affairs/compensation.json` | NEW — extracted from rates-annual.json |
| — | `federal/veterans-affairs/vgli.json` | NEW — extracted from rates-annual.json |
| `plans/state-benefits.json` | `states/state-benefits.json` | Unchanged content |
| `plans/plan-library.json` | `states/virginia/vrs-plans.json` | VRS plans + hire date mapping |
| `plans/plan-library.json` | `states/virginia/erfc-plans.json` | ERFC plans + hire date mapping + county metadata |
| `plans/plan-library.json` | `states/virginia/plan-combinations.json` | VRS + ERFC stacking patterns |
| `plans/plan-library.json` | `reference/other-db-template.json` | Generic DB plan fallback |
| `reference/static-refs.json` | `reference/static-refs.json` | Unchanged path and content |

### Manifest Key Changes

| Old Key (schema 1.x) | New Key(s) (schema 2.0) |
|---|---|
| `plan_library` | `vrs_plans`, `erfc_plans`, `plan_combinations`, `other_db_template` |
| `rates_annual` | `rates_annual` (slimmed), `va_compensation`, `vgli` |

### New File: `federal/veterans-affairs/compensation.json`

Contains VA disability compensation rates by rating, dependent additions, DIC rates, and VA COLA data. All data was previously in the `va` section of `rates-annual.json`. Extracted because VA compensation has a different update cycle (December COLA) than federal civilian rates (January).

### New File: `federal/veterans-affairs/vgli.json`

Contains VGLI age-banded premium table. Previously the `vgli` section of `rates-annual.json`. Extracted because VGLI premiums update on their own schedule (VA-determined).

### New File: `states/virginia/vrs-plans.json`

Virginia Retirement System plans (Plan 1, Plan 2, Hybrid) with state-level hire date auto-derive mapping. Split from `plan-library.json` because VRS is a state-level system distinct from county-level supplemental plans.

### New File: `states/virginia/erfc-plans.json`

ERFC supplemental pension plans (Legacy, 2001 Tier 1, 2001 Tier 2) with county-level jurisdiction metadata. Split from `plan-library.json` because ERFC is a Fairfax County system specific to FCPS, not a state-level plan. Added `jurisdiction` object documenting county, school system, and scope.

### New File: `states/virginia/plan-combinations.json`

VRS + ERFC pension stacking patterns. Split from `plan-library.json` because combinations bridge state and county jurisdictions.

### New File: `reference/other-db-template.json`

Generic defined benefit plan template for user-entered parameters. Split from `plan-library.json` because it is not tied to any jurisdiction.

### Consumer App Migration Steps

1. Update `appSchemaVersion` to `"2.0"` in your schema check code
2. Update all file fetch paths to use new `manifest.files.*.url` values
3. Replace single `plan_library` fetch with separate `vrs_plans`, `erfc_plans`, `plan_combinations` fetches
4. Add fetches for `va_compensation` and `vgli` (previously embedded in `rates_annual`)
5. Update any code referencing `rates.va` or `rates.vgli` to read from the new standalone files

---

## Schema Version 1.1 — Veteran Benefits (state-benefits.json v1.2)

**Date:** 2026-03-08
**schema_version:** 1.1
**schema_min_compatible:** 1.0 (unchanged — new keys only, backward compatible)

Added veteran-specific property and housing benefit data to `state-benefits.json`.

### New Root Section: `federal_veteran_benefits`

Contains federal veteran benefits that apply identically in all states. Added to avoid repeating in every state entry.

| Benefit | Key Details |
|---------|------------|
| `va_funding_fee_exemption` | Waiver of 0.5%–3.3% one-time fee. Any comp rating qualifies. Survivor transfer via DIC. Age 57+ remarriage exception for housing loan benefits. Age 55+ remarriage exception for DIC/CHAMPVA only. Terminated remarriage restores eligibility. Purple Heart exemption. Tax-deductible starting 2026. |

### New State-Level Section: `veteran_benefits` (Virginia model)

Added to Virginia entry as the reference template for all future state entries.

| Benefit | Key Details |
|---------|------------|
| `real_property_tax_exemption` | Full exemption, 100% P&T or IU+P&T. Survivor transfer (no remarriage, portable since 2019). VA Code § 58.1-3219.5. |
| `vehicle_tax_exemption` | Full exemption, 1 car/truck, 100% P&T or IU+P&T. No survivor transfer (prohibited by statute). VA Code § 58.1-3668. |
| `line_of_duty_survivor_property_tax` | NEW benefit from Nov 2024 constitutional amendment. Surviving spouse of service member who died in line of duty (expanded from prior "killed in action" standard). Effective Jan 1, 2025. VA Constitution Art. X, § 6-A(b). |

### Sources Verified (March 8, 2026)

All data validated against primary statutory sources:
- VA Code § 58.1-3219.5 (real property), § 58.1-3668 (vehicle)
- VA Constitution Article X, Section 6-A (both subdivisions)
- 38 U.S.C. § 103(d) (remarriage rules), 38 U.S.C. § 3729 (funding fee)
- 38 CFR § 3.55 (remarriage reinstatement)
- VA.gov funding fee page, VA DVS tax exemptions page
- VA news release (Feb 2026) confirming funding fee tax deductibility

---

## Schema Version 1.0 — Initial Release

**Date:** 2026-03-08
**schema_min_compatible:** 1.0

Baseline schema established for all data files.

### Files and Structure (schema 1.x — superseded by 2.0)

| File | Key Sections |
|------|-------------|
| `rates/rates-annual.json` | `tsp`, `pay`, `fers`, `irmaa`, `ira`, `social_security`, `va`, `vgli`, `planning_assumption_defaults`, `tax` |
| `rates/pay-tables.json` | `gs_base_pay`, `locality_areas`, `dcips` |
| `plans/plan-library.json` | `hireDateMapping`, `plans`, `planCombinations` |
| `plans/state-benefits.json` | `states[]` array with per-state tax treatment |
| `reference/static-refs.json` | `social_security_fra`, `rmd_uniform_lifetime_table`, `opm_locality_codes` |

### Schema Version Rules

| Change Type | Bump schema_version? | Bump schema_min_compatible? |
|---|---|---|
| Add new key | Yes (minor) | No |
| Add new file | Yes (minor) | No |
| Rename key | Yes (major) | **Yes** |
| Remove key | Yes (major) | **Yes** |
| Change value type | Yes (major) | **Yes** |
| Move/rename file path | Yes (major) | **Yes** |
| Update values only | No | No |
| Correct values | No | No |

**Growth pattern:** Adding new keys and files keeps `schema_min_compatible` unchanged. Older consumers simply ignore keys they don't recognize. Path changes or key removals require a `schema_min_compatible` bump.

---

*Future schema changes will be documented above the v1.0 section in reverse chronological order. Data corrections are logged in the Data Corrections Log section.*
