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
const appSchemaVersion = "1.0"; // hardcoded in consumer app
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

### Files and Structure

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
| Update values only | No | No |
| Correct values | No | No |

**Growth pattern:** Adding new keys and files keeps `schema_min_compatible` at 1.0 indefinitely. Older consumers simply ignore keys they don't recognize.

---

*Future schema changes will be documented above the v1.0 section in reverse chronological order. Data corrections are logged in the Data Corrections Log section.*
