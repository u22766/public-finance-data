# public-finance-data

Curated public finance reference data sourced from U.S. government publications.

This repository contains **no personal information of any kind**. All data is drawn from publicly available sources — OPM, IRS, SSA, VA, CMS, and state tax authorities. Anyone may fork or use this data freely.

---

## What This Is

A structured, version-controlled library of government-published financial data useful for retirement planning, tax analysis, benefits estimation, and fiscal modeling. The data covers federal retirement systems (FERS, TSP), VA benefits, Medicare (IRMAA), Social Security, federal and state tax brackets, and state/local pension plans.

Designed as a generic data source that any application, tool, or analysis can consume — no authentication, no API keys, no tracking.

---

## How to Use This Repo

1. Fetch `manifest.json` first — it's the version index listing all available files.
2. Compare each file's `version` to your locally cached copy.
3. Fetch only the files that have newer versions.
4. If GitHub is unreachable, fall back to your last cached fetch.

The `schema_version` and `schema_min_compatible` fields in the manifest enable consumers to detect breaking changes. See `schema-changelog.md` for details.

---

## File Structure

```
public-finance-data/
├── manifest.json                              ← Fetch this first (master version index)
├── schema-changelog.md                        ← Documents every schema structure change
├── federal/
│   ├── rates-annual.json                      ← TSP, IRMAA, IRA, SS, FERS, tax brackets, COLA
│   ├── pay-tables.json                        ← GS + DCIPS pay tables, all grades/steps/localities
│   └── veterans-affairs/
│       ├── compensation.json                  ← VA disability comp rates, DIC, VA COLA
│       └── vgli.json                          ← VGLI age-banded premium table
├── states/
│   ├── state-benefits.json                    ← State income tax treatment + property tax + veteran benefits
│   └── virginia/
│       ├── vrs-plans.json                     ← VRS Plan 1, Plan 2, Hybrid (state-level)
│       ├── erfc-plans.json                    ← ERFC Legacy, Tier 1, Tier 2 (Fairfax County)
│       └── plan-combinations.json             ← VRS + ERFC pension stacking patterns
└── reference/
    ├── static-refs.json                       ← SS FRA table, RMD Uniform Lifetime Table, locality codes
    └── other-db-template.json                 ← Generic DB plan template for user-entered pensions
```

### Domain Organization

Files are organized by jurisdiction:

- **`federal/`** — Federal civilian data (OPM, IRS, SSA, CMS) and Department of Veterans Affairs benefits
- **`states/`** — State-level tax treatment and state/county pension plans
- **`reference/`** — Static lookup tables and templates that rarely change

---

## Update Schedule

| File | When | Trigger |
|------|------|---------|
| `federal/rates-annual.json` | January | IRS, OPM, SSA, CMS publish new figures |
| `federal/pay-tables.json` | January (mid-month) | OPM publishes new GS pay schedule |
| `federal/veterans-affairs/compensation.json` | December | VA publishes new COLA rates |
| `federal/veterans-affairs/vgli.json` | As published | VA updates VGLI premium schedule |
| `states/state-benefits.json` | As needed | State tax law changes |
| `states/virginia/vrs-plans.json` | As needed | VRS rule changes |
| `states/virginia/erfc-plans.json` | As needed | ERFC rule changes |
| `reference/static-refs.json` | Rarely | SS FRA table or RMD table changes |

---

## Data Sources

All data in this repository is drawn from official U.S. government sources:

| Data | Source | URL |
|------|--------|-----|
| TSP contribution limits | TSP.gov | https://www.tsp.gov/plan-participation/eligibility/contribution-limits/ |
| GS pay tables | OPM | https://www.opm.gov/policy-data-oversight/pay-leave/salaries-wages/ |
| Locality pay percentages | OPM | https://www.opm.gov/policy-data-oversight/pay-leave/locality-pay/ |
| IRMAA thresholds | CMS / Medicare.gov | https://www.medicare.gov/your-medicare-costs/part-b-costs |
| IRA / tax limits | IRS | https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits |
| Tax brackets | IRS | https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill |
| SS COLA + bend points | SSA | https://www.ssa.gov/oact/COLA/colasummary.html |
| SS Full Retirement Ages | SSA | https://www.ssa.gov/benefits/retirement/planner/agereduction.html |
| VA compensation rates | VA.gov | https://www.va.gov/disability/compensation-rates/veteran-rates/ |
| DIC rates | VA.gov | https://www.va.gov/family-and-caregiver-benefits/survivor-compensation/dependency-indemnity-compensation/survivor-rates/ |
| VGLI premiums | VA.gov | https://www.benefits.va.gov/INSURANCE/vglispring2025discount.asp |
| RMD Uniform Lifetime Table | IRS Pub. 590-B | https://www.irs.gov/publications/p590b |
| VRS plan parameters | VRS | https://www.varetire.org/retirement-plans/ |
| ERFC plan parameters | ERFC | https://www.erfcpension.org/ |

---

## Schema Versioning

The manifest includes two version fields for safe consumption:

- **`schema_version`** — current structure version. Bumped when keys are added, renamed, removed, or paths change.
- **`schema_min_compatible`** — oldest consumer version that can safely read this data.

**Rule of thumb:** If changes only ADD new keys or files, `schema_min_compatible` stays unchanged and older consumers keep working. Path changes or key removals require a `schema_min_compatible` bump. See `schema-changelog.md` for the full change history.

---

## Versioning Convention

Each file uses a `"version"` field:

- **Annual rate files:** `year.patch` format (e.g., `"2026"`, `"2026.1"`). Annual refresh resets to new year. Corrections within the same year increment the patch number.
- **Plan library / state benefits:** Semantic version (e.g., `"2.0.0"`)
- **Static references:** Semantic version (e.g., `"1.0.1"`)

When updating a file, always:
1. Increment the version in the file itself
2. Update `manifest.json` to match (including `last_updated` date)
3. Document any structural changes in `schema-changelog.md`
4. Log value corrections in the Data Corrections section of `schema-changelog.md`

---

## For Maintainers — Annual Update Checklist (January)

### `federal/rates-annual.json`
- [ ] TSP regular limit (`tsp.regular_limit`)
- [ ] TSP catch-up ages 50–59 (`tsp.catchup_age_50_59`)
- [ ] TSP catch-up ages 60–63 (`tsp.catchup_age_60_63`)
- [ ] TSP catch-up income threshold (`tsp.catchup_income_threshold`)
- [ ] Pay cap (`pay.pay_cap`)
- [ ] IRMAA thresholds — all tiers, both single and MFJ (`irmaa`)
- [ ] IRA contribution limit + catch-up (`ira.contribution_limit`, `ira.catchup_age_50_plus`)
- [ ] Roth IRA phase-out range (`ira.roth_phase_out_*`)
- [ ] Traditional IRA deductibility phase-out (`ira.traditional_deductibility_*`)
- [ ] SS COLA for the year (`social_security.cola_YEAR`)
- [ ] SS bend points (`social_security.bend_points`)
- [ ] Standard deductions (`tax.standard_deduction_*`)
- [ ] Tax brackets — all rates, both single and MFJ (`tax.brackets_*`) — verify cutoffs against IRS Rev. Proc. source tables, not computed values
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `rates_annual.version`

### `federal/pay-tables.json`
- [ ] All 15 GS grades, all 10 steps — base pay figures
- [ ] All locality area percentages
- [ ] DCIPS band min/max figures
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `pay_tables.version`

### `federal/veterans-affairs/compensation.json` (December)
- [ ] VA COLA rate (`cola_YEAR_actual`)
- [ ] All compensation base rates by rating
- [ ] All dependent additions by rating
- [ ] DIC base rate and related amounts
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `va_compensation.version`

### `manifest.json`
- [ ] Update `"last_updated"` date
- [ ] Confirm all file versions match their respective files

---

## License

Public domain. All data is reproduced from U.S. government publications, which are not subject to copyright under 17 U.S.C. § 105.

---

*This repository has no affiliation with OPM, IRS, SSA, VA, CMS, or any U.S. government agency.*
