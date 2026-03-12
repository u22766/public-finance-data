# public-finance-data

Curated public finance reference data sourced from U.S. government publications.

This repository contains **no personal information of any kind**. All data is drawn from publicly available sources — OPM, IRS, SSA, VA, CMS, DoD, and state tax authorities. Anyone may fork or use this data freely.

---

## What This Is

A structured, version-controlled library of government-published financial data useful for retirement planning, tax analysis, benefits estimation, and fiscal modeling. Coverage includes:

- **Federal retirement systems** — FERS rates, TSP contribution limits, COLA history, Social Security bend points and taxable maximums
- **Federal pay** — GS pay tables (all grades/steps/localities) and DCIPS pay bands
- **Healthcare** — FEHB premiums (478 plan entries), FEHB plan benefits, FEDVIP dental/vision, TRICARE (retiree, active duty family, reserve, TFL), Medicare IRMAA
- **Veterans Affairs** — VA disability compensation, DIC, VGLI premiums
- **Tax data** — Federal brackets, standard deductions, IRA/Roth limits and phase-outs
- **State benefits** — Income tax treatment, property tax exemptions, and veteran benefits for 15 states
- **County property tax** — Effective rates and veteran exemptions for 10 counties
- **Actuarial tables** — SSA period life table (ages 0–119, both sexes)
- **State/local pensions** — Virginia VRS plans, Fairfax County ERFC plans, pension stacking patterns

Designed as a generic data source that any application, tool, or analysis can consume — no authentication, no API keys, no tracking.

---

## How to Use This Repo

1. Fetch `manifest.json` first — it's the version index listing all 23 available data files.
2. Compare each file's `version` to your locally cached copy.
3. Fetch only the files that have newer versions.
4. If GitHub is unreachable, fall back to your last cached fetch.

The `schema_version` and `schema_min_compatible` fields in the manifest enable consumers to detect breaking changes. See `schema-changelog.md` for details.

---

## File Structure

```
public-finance-data/
├── manifest.json                                ← Fetch this first (master version index, 23 entries)
├── schema-changelog.md                          ← Documents every schema structure change
│
├── federal/
│   ├── rates-annual.json                        ← TSP, IRMAA, IRA, SS, FERS, tax brackets, COLA
│   ├── pay-tables.json                          ← GS pay tables — all grades/steps/localities
│   ├── tsp-limits.json                          ← TSP contribution limits (1987–2026)
│   ├── ss-bend-points.json                      ← SS bend points (1979–2026)
│   ├── ss-taxable-max.json                      ← SS taxable maximum (1937–2026)
│   ├── ira-limits.json                          ← IRA/Roth limits + phase-outs (1975–2026)
│   ├── cola-history.json                        ← COLA history — FERS, CSRS, SS, VA (51 years, 4 systems)
│   ├── dcips/
│   │   └── dcips-pay-tables.json                ← DCIPS pay bands — all occupational categories
│   ├── healthcare/
│   │   ├── fehb-rates.json                      ← FEHB premiums — 478 plan entries (132 plans × enrollment types)
│   │   ├── fehb-plan-benefits.json              ← FEHB plan benefit details (deductibles, copays, coverage)
│   │   ├── fedvip-rates.json                    ← FEDVIP dental + vision premiums
│   │   ├── tricare-rates.json                   ← TRICARE costs — retiree, ADFM, reserve, TFL
│   │   └── medicare-rates.json                  ← Medicare Part B/D premiums + IRMAA thresholds
│   └── veterans-affairs/
│       ├── compensation.json                    ← VA disability comp rates, DIC, VA COLA
│       └── vgli.json                            ← VGLI age-banded premium table
│
├── states/
│   ├── state-benefits.json                      ← 15 states: income tax, property tax, veteran benefits
│   ├── counties/
│   │   └── county-property-tax.json             ← 10 counties: effective rates + veteran exemptions
│   └── virginia/
│       ├── vrs-plans.json                       ← VRS Plan 1, Plan 2, Hybrid
│       ├── erfc-plans.json                      ← ERFC Legacy, Tier 1, Tier 2 (Fairfax County)
│       └── plan-combinations.json               ← VRS + ERFC pension stacking patterns
│
├── reference/
│   ├── static-refs.json                         ← SS FRA table, RMD Uniform Lifetime Table, locality codes
│   ├── ssa-life-table.json                      ← SSA period life table (ages 0–119, M/F/combined)
│   └── other-db-template.json                   ← Generic DB plan template for user-entered pensions
│
└── tests/
    ├── validate.py                              ← Core validation (231 checks)
    ├── validate_tier2.py                        ← State benefits validation (169 checks)
    ├── validate_medicare.py                     ← Medicare rates validation (7 checks)
    ├── validate_dcips.py                        ← DCIPS pay tables validation (424 checks)
    └── validate_historical.py                   ← Historical + healthcare validation (11,928 checks)
```

### Domain Organization

Files are organized by jurisdiction and domain:

- **`federal/`** — Federal civilian data (OPM, IRS, SSA, CMS), healthcare plans (OPM, DoD, CMS), and Department of Veterans Affairs benefits
- **`states/`** — State-level tax treatment, county property tax data, and state/county pension plans
- **`reference/`** — Static lookup tables, actuarial data, and templates that rarely change

---

## Manifest — Current Data Files (23 Entries)

| Key | Version | File |
|-----|---------|------|
| `rates_annual` | 2026.2 | `federal/rates-annual.json` |
| `pay_tables` | 2026 | `federal/pay-tables.json` |
| `dcips_pay_tables` | 2026.1 | `federal/dcips/dcips-pay-tables.json` |
| `tsp_limits` | 1.0 | `federal/tsp-limits.json` |
| `ss_bend_points` | 1.0 | `federal/ss-bend-points.json` |
| `ss_taxable_max` | 1.0 | `federal/ss-taxable-max.json` |
| `ira_limits` | 2.0 | `federal/ira-limits.json` |
| `cola_history` | 1.0 | `federal/cola-history.json` |
| `fehb_rates` | 2026.3 | `federal/healthcare/fehb-rates.json` |
| `fehb_plan_benefits` | 2026.1 | `federal/healthcare/fehb-plan-benefits.json` |
| `fedvip_rates` | 2026.1 | `federal/healthcare/fedvip-rates.json` |
| `tricare_rates` | 2026.1 | `federal/healthcare/tricare-rates.json` |
| `medicare_rates` | 2026.1 | `federal/healthcare/medicare-rates.json` |
| `va_compensation` | 2026.1 | `federal/veterans-affairs/compensation.json` |
| `vgli` | 2026 | `federal/veterans-affairs/vgli.json` |
| `state_benefits` | 1.5 | `states/state-benefits.json` |
| `county_property_tax` | 1.0 | `states/counties/county-property-tax.json` |
| `vrs_plans` | 2.0.0 | `states/virginia/vrs-plans.json` |
| `erfc_plans` | 2.0.0 | `states/virginia/erfc-plans.json` |
| `plan_combinations` | 2.0.0 | `states/virginia/plan-combinations.json` |
| `static_refs` | 1.0.1 | `reference/static-refs.json` |
| `ssa_life_table` | 1.0 | `reference/ssa-life-table.json` |
| `other_db_template` | 1.0.0 | `reference/other-db-template.json` |

---

## State and County Coverage

**State benefits** (15 states): VA, MD, DC, FL, TX, GA, NC, CO, WA, PA, AK, HI, AZ, NV, OR

Each state entry includes income tax treatment of military/federal retirement pay, property tax exemptions for disabled veterans, additional veteran benefit programs, application procedures, survivor transfer conditions, and pending legislation flags.

**County property tax** (10 counties): Fairfax County VA, Virginia Beach VA, Prince George's County MD, Cumberland County NC, Bexar County TX, Hillsborough County FL, El Paso County CO, Pierce County WA, Maricopa County AZ, Clark County NV

---

## Validation & CI

All data files are validated on every push and pull request via GitHub Actions. The CI pipeline runs five test suites totaling **12,759+ checks**:

| Suite | File | Checks | Coverage |
|-------|------|--------|----------|
| Core | `validate.py` | 231 | Manifest integrity, all federal/state/reference files |
| Tier 2 | `validate_tier2.py` | 169 | State benefits — field structure, exemption types, IU eligibility |
| Medicare | `validate_medicare.py` | 7 | Medicare IRMAA thresholds and premium values |
| DCIPS | `validate_dcips.py` | 424 | DCIPS pay bands — all occupational categories |
| Historical | `validate_historical.py` | 11,928 | Historical series, FEHB (9,109), TRICARE, FEDVIP, plan benefits |

---

## Update Schedule

| File | When | Trigger |
|------|------|---------|
| `federal/rates-annual.json` | January | IRS, OPM, SSA, CMS publish new figures |
| `federal/pay-tables.json` | January | OPM publishes new GS pay schedule |
| `federal/dcips/dcips-pay-tables.json` | January | DCIPS pay band updates |
| `federal/healthcare/fehb-rates.json` | November–January | OPM publishes new FEHB premiums |
| `federal/healthcare/fehb-plan-benefits.json` | November–January | OPM publishes plan benefit details |
| `federal/healthcare/fedvip-rates.json` | November–January | OPM publishes FEDVIP rates |
| `federal/healthcare/tricare-rates.json` | October–January | DoD publishes TRICARE cost updates |
| `federal/healthcare/medicare-rates.json` | November | CMS publishes new IRMAA thresholds |
| `federal/veterans-affairs/compensation.json` | December | VA publishes new COLA rates |
| `federal/veterans-affairs/vgli.json` | As published | VA updates VGLI premium schedule |
| `states/state-benefits.json` | As needed | State tax law changes |
| `states/counties/county-property-tax.json` | As needed | County rate or exemption changes |
| Historical series (tsp, ss, ira, cola) | January | Annual new-year data point added |
| `reference/static-refs.json` | Rarely | SS FRA table or RMD table changes |

---

## Data Sources

All data in this repository is drawn from official U.S. government sources:

| Data | Source | URL |
|------|--------|-----|
| TSP contribution limits | TSP.gov | https://www.tsp.gov/plan-participation/eligibility/contribution-limits/ |
| GS pay tables | OPM | https://www.opm.gov/policy-data-oversight/pay-leave/salaries-wages/ |
| Locality pay percentages | OPM | https://www.opm.gov/policy-data-oversight/pay-leave/locality-pay/ |
| DCIPS pay bands | DCIPS | https://dcips.defense.gov/ |
| FEHB premiums | OPM | https://www.opm.gov/healthcare-insurance/healthcare/plan-information/premiums/ |
| FEHB plan benefits | OPM | https://www.opm.gov/healthcare-insurance/healthcare/plan-information/ |
| FEDVIP dental/vision | OPM BENEFEDS | https://www.benefeds.com/ |
| TRICARE costs | TRICARE | https://www.tricare.mil/Costs/Compare |
| IRMAA thresholds | CMS / Medicare.gov | https://www.medicare.gov/your-medicare-costs/part-b-costs |
| IRA / tax limits | IRS | https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits |
| Tax brackets | IRS | https://www.irs.gov/newsroom |
| SS COLA + bend points | SSA | https://www.ssa.gov/oact/COLA/colasummary.html |
| SS Full Retirement Ages | SSA | https://www.ssa.gov/benefits/retirement/planner/agereduction.html |
| SSA life tables | SSA | https://www.ssa.gov/oact/STATS/table4c6.html |
| VA compensation rates | VA.gov | https://www.va.gov/disability/compensation-rates/veteran-rates/ |
| DIC rates | VA.gov | https://www.va.gov/family-and-caregiver-benefits/survivor-compensation/dependency-indemnity-compensation/survivor-rates/ |
| VGLI premiums | VA.gov | https://www.benefits.va.gov/INSURANCE/vgli.asp |
| RMD Uniform Lifetime Table | IRS Pub. 590-B | https://www.irs.gov/publications/p590b |
| VRS plan parameters | VRS | https://www.varetire.org/retirement-plans/ |
| ERFC plan parameters | ERFC | https://www.erfcpension.org/ |

---

## Schema Versioning

The manifest includes two version fields for safe consumption:

- **`schema_version`** — current structure version (currently `2.0`). Bumped when keys are added, renamed, removed, or paths change.
- **`schema_min_compatible`** — oldest consumer version that can safely read this data (currently `2.0`).

**Rule of thumb:** If changes only ADD new keys or files, `schema_min_compatible` stays unchanged and older consumers keep working. Path changes or key removals require a `schema_min_compatible` bump. See `schema-changelog.md` for the full change history.

---

## Versioning Convention

Each file uses a `"version"` field:

- **Annual rate files:** `year.patch` format (e.g., `"2026"`, `"2026.1"`). Annual refresh resets to new year. Corrections within the same year increment the patch number.
- **Historical series:** Semantic version (e.g., `"1.0"`, `"2.0"`). Bumped when new year's data is appended or structure changes.
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
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `pay_tables.version`

### `federal/dcips/dcips-pay-tables.json`
- [ ] DCIPS band min/max figures for all occupational categories
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `dcips_pay_tables.version`

### `federal/healthcare/` (November–January)
- [ ] FEHB premiums — all plans, all enrollment types
- [ ] FEHB plan benefits — deductibles, copays, coverage details
- [ ] FEDVIP dental and vision premiums
- [ ] TRICARE enrollment fees, deductibles, catastrophic caps
- [ ] Medicare Part B/D premiums and IRMAA thresholds
- [ ] Update all healthcare file versions
- [ ] Update `manifest.json` for all healthcare entries

### `federal/veterans-affairs/compensation.json` (December)
- [ ] VA COLA rate (`cola_YEAR_actual`)
- [ ] All compensation base rates by rating
- [ ] All dependent additions by rating
- [ ] DIC base rate and related amounts
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `va_compensation.version`

### Historical series (January)
- [ ] Append new year's data point to `tsp-limits.json`
- [ ] Append new year's data point to `ss-bend-points.json`
- [ ] Append new year's data point to `ss-taxable-max.json`
- [ ] Append new year's data point to `ira-limits.json`
- [ ] Append new year's COLA values to `cola-history.json`

### `manifest.json`
- [ ] Update `"last_updated"` date
- [ ] Confirm all file versions match their respective files

---

## License

Public domain. All data is reproduced from U.S. government publications, which are not subject to copyright under 17 U.S.C. § 105.

---

*This repository has no affiliation with OPM, IRS, SSA, VA, CMS, DoD, or any U.S. government agency.*
