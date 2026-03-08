# Schema Changelog

Documents every structural change to the data files in this repository. Value-only updates (e.g., new year's rates) are NOT recorded here — only changes to keys, file organization, or data types.

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

**Growth pattern:** Adding new keys and files keeps `schema_min_compatible` at 1.0 indefinitely. Older consumers simply ignore keys they don't recognize.

---

*Future schema changes will be documented above in reverse chronological order.*
