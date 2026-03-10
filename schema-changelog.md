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

## state-benefits v1.5 — March 9, 2026

**File:** `states/state-benefits.json`
**Prior version:** v1.4
**Change type:** Non-breaking addition (new state entries; no renamed or removed keys)
**Schema version:** Unchanged — consumers that ignore unknown keys require no changes.

### Summary

Added full `veteran_benefits` and `income_tax` sections for 6 Tier 2 states: PA, AK, HI, AZ, NV, OR. Expands coverage from 9 states to 15 states.

### New State Entries

#### Pennsylvania (PA) — 1 benefit type:
- `veteran_benefits.disabled_veteran_real_estate_tax_exemption` — Full exemption for 100% P&T/IU on primary residence; requires wartime service and financial need test ($114,637 threshold, 2025, CPI-indexed biennially)
- `income_tax`: 3.07% flat; military retirement fully exempt; SS exempt
- `pending_legislation`: SB 831 would remove wartime requirement; HB 1257 adds graduated reductions for 50%+

#### Alaska (AK) — 1 benefit type:
- `veteran_benefits.disabled_veteran_property_tax_exemption` — First $150,000 assessed value for 50%+ disability (mandatory statewide minimum; municipalities may add more)
- `income_tax`: No state income tax

#### Hawaii (HI) — 2 benefit types:
- `veteran_benefits.totally_disabled_veteran_exemption` — Full exemption except minimum tax (~$300) and special assessments; county-administered with varying deadlines
- `veteran_benefits.vehicle_registration_fee_exemption` — $46 registration fee exemption on one vehicle (100% disabled)
- `income_tax`: Up to 11% graduated; military retirement fully exempt; SS exempt
- Note: Kauai County has expanded eligibility to 80%+ disability

#### Arizona (AZ) — 2 benefit types:
- `veteran_benefits.disabled_veteran_full_exemption` — Full exemption on primary residence for 100% service-connected disability (NEW — effective January 1, 2026 via SB 1749, Chapter 247)
- `veteran_benefits.disabled_veteran_partial_exemption` — Up to $4,873 assessed value × disability % (CPI-indexed; any disability rating)
- `income_tax`: 2.5% flat; military retirement fully exempt; SS exempt
- **CRITICAL:** IU does NOT qualify for full exemption — combined service-connected rating is controlling factor, not compensation level
- Income limits apply ($39,865/$47,826); SS, military pensions, VA disability excluded from income calculation

#### Nevada (NV) — 2 benefit types:
- `veteran_benefits.wartime_veteran_exemption` — $3,540 assessed value deduction for wartime veterans (CPI-indexed)
- `veteran_benefits.disabled_veteran_exemption` — Tiered deduction: $17,700 (60-79%), $26,550 (80-99%), $35,400 (100%) assessed value
- `income_tax`: No state income tax
- Note: Cannot stack wartime + disabled veteran exemptions; 5-year marriage requirement for surviving spouse

#### Oregon (OR) — 2 benefit types:
- `veteran_benefits.disabled_veteran_homestead_exemption` — $26,303 basic / $31,565 service-connected assessed value deduction (3% annual increase; 40%+ disability)
- `veteran_benefits.active_duty_military_homestead_exemption` — $108,366 assessed value for Guard/Reserve on federal active duty
- `income_tax`: Up to 9.9% graduated; military retirement only exempt for pre-October 1, 1991 service; SS exempt
- Note: Oregon transitioning from property tax exemptions to credits (2026-27 tax year)

### IU Eligibility — Tier 2 States

| State | IU Treatment |
|-------|-------------|
| PA | Explicitly qualifies ("total disability individual unemployability") |
| AK | Statute says "50% or more" — not explicitly addressed; recommend verification |
| HI | Statute says "totally disabled" — recommend county verification |
| AZ | **Does NOT qualify** for full exemption (combined rating is controlling factor) |
| NV | Statute says "permanent service-connected disability" — recommend verification |
| OR | Requires 40%+ certification — IU with 40%+ combined should qualify; verify |

### Migration Notes for Consumers

- **No breaking changes.** All additions are new state entries within the existing `states` array.
- Consumers that iterate over states dynamically will pick up new states automatically.
- Consumers that hardcode state lists should add: `PA`, `AK`, `HI`, `AZ`, `NV`, `OR`.
- Arizona entries include `effective_date: "2026-01-01"` for the new full exemption — consumers displaying benefits should check effective dates.
- Oregon `transition_to_credits` field flags the upcoming structural change in Oregon tax law.

### Validation

- **179/179 CI checks passing** on the expanded file.
- Additional Tier 2-specific validation run: all 6 states pass structural checks.

### Sources

All values traced to official government sources: state tax authorities, state legislatures, VA resources, myarmybenefits.us.army.mil, county assessor offices. Source URLs documented in each state entry.

---

## state-benefits v1.3 / v1.4 — March 8, 2026

**File:** `states/state-benefits.json`
**Prior version:** v1.2
**Change type:** Non-breaking addition (new state entries; no renamed or removed keys)
**Schema version:** Unchanged — consumers that ignore unknown keys require no changes.

### Summary

Added full `veteran_benefits` and `income_tax` sections for 8 states in two phases: MD, DC, FL, TX (v1.3) and GA, NC, CO, WA (v1.4). Expanded coverage from 1 state (VA) to 9 states.

### New State Entries — v1.3 (MD, DC, FL, TX)

#### Maryland (MD) — 3 benefit types:
- `veteran_benefits.real_property_tax_exemption` — Full exemption for 100% P&T/IU on dwelling + curtilage
- `veteran_benefits.line_of_duty_survivor_property_tax` — Full exemption for surviving spouse of KIA service member
- `veteran_benefits.partial_disability_credit` — County-administered: 50% credit (75%+), 25% credit (50–74%), income limit $100K

#### District of Columbia (DC) — 1 benefit type:
- `veteran_benefits.veterans_homestead_deduction` — $445,000 assessed value deduction for 100% P&T/IU; income limit $163,500 (TY2026)
- `pending_legislation` field added — tracks "Disabled Veterans Complete Property Tax Exemption Amendment Act of 2025"

#### Florida (FL) — 5 benefit types:
- `veteran_benefits.total_permanent_disability_exemption` — Full exemption for 100% P&T on homestead
- `veteran_benefits.partial_disability_exemption` — $5,000 for 10%+ (any property)
- `veteran_benefits.combat_disability_discount` — Age 65+ with combat disability: discount = disability %
- `veteran_benefits.wheelchair_bound_exemption` — Full exemption for paraplegic/hemiplegic/wheelchair-bound/blind
- `veteran_benefits.line_of_duty_survivor_property_tax` — Full exemption; portable (capped at prior amount)

#### Texas (TX) — 4 benefit types:
- `veteran_benefits.total_disability_exemption` — Full exemption for 100%/IU
- `veteran_benefits.partial_disability_exemption` — $5K–$12K based on disability rating
- `veteran_benefits.donated_residence_exemption` — Charitable-donated home: exemption = disability %
- `veteran_benefits.line_of_duty_survivor_property_tax` — Full exemption; portable (capped at prior amount)

### New State Entries — v1.4 (GA, NC, CO, WA)

#### Georgia (GA) — 3 benefit types:
- `veteran_benefits.disabled_veteran_homestead_exemption` — Up to $121,812 (2025, indexed per 38 U.S.C. § 2102)
- `veteran_benefits.vehicle_ad_valorem_exemption` — One vehicle exempt from Ad Valorem tax
- `veteran_benefits.line_of_duty_survivor_property_tax` — $85,645 exemption for KIA surviving spouse
- `pending_legislation` — SB 129 (full exemption, voter approval Nov 2026)

#### North Carolina (NC) — 1 benefit type:
- `veteran_benefits.disabled_veteran_homestead_exclusion` — First $45,000 of appraised value excluded
- `pending_legislation` — S 660 (graduated increase to $500K/100% by 2027)

#### Colorado (CO) — 2 benefit types:
- `veteran_benefits.disabled_veteran_property_tax_exemption` — 50% of first $200,000 actual value
- `veteran_benefits.gold_star_spouse_exemption` — Same 50%/$200K benefit
- `pending_legislation` — Ballot initiative #49 (full exemption)

#### Washington (WA) — 2 benefit types:
- `veteran_benefits.disabled_veteran_property_tax_reduction` — Income-based; freezes value, exempts excess levies
- `veteran_benefits.surviving_spouse_grant_program` — Payment assistance ($40K income limit)
- `pending_legislation` — SB 5398 (full exemption for 100% disabled)

### New Fields (All States)

- `income_tax` section added for all 9 states — covers state income tax rates, military retirement treatment, and Social Security benefit treatment.
- `pending_legislation` field — used where applicable (DC, GA, NC, CO, WA) to flag bills that may expand benefits.

### IU Eligibility — v1.3/v1.4 States

| State | IU Treatment |
|-------|-------------|
| VA | Explicitly qualifies |
| MD | Explicitly qualifies |
| DC | Explicitly qualifies ("paid at 100% level") |
| FL | Statute says "total and permanent" — recommend user verify with county appraiser |
| TX | Explicitly qualifies (IU = 100%) |
| GA | Explicitly qualifies |
| NC | Statute says "permanent and total" — recommend verification |
| CO | Qualifies if rated 70%+ but compensated at 100% |
| WA | Qualifies if receiving compensation at 100% rate |

### Migration Notes for Consumers

- **No breaking changes.** All additions are new keys within the existing `states` array.
- Consumers that iterate over states dynamically will pick up new states automatically.
- Consumers that hardcode state lists should add: `MD`, `DC`, `FL`, `TX`, `GA`, `NC`, `CO`, `WA`.
- The `pending_legislation` field is optional and may be absent for states with no tracked pending bills. Consumers should treat it as nullable.
- The `income_tax` section follows a consistent structure across all states; `taxes_federal_pension: false` states (FL, TX, WA) have simplified entries.

### Validation

- **179/179 CI checks passing** on the expanded file.
- No changes to `tests/validate.py` or `.github/workflows/validate.yml` required.

### Sources

All values traced to official government sources: state tax authority websites, VA resources, myarmybenefits.us.army.mil, state comptroller/assessor sites, and state revenue departments. Source URLs documented in each state entry.

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
