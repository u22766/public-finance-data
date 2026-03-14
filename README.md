# public-finance-data

Curated public finance reference data sourced from U.S. government publications.

This repository contains **no personal information of any kind**. All data is drawn from publicly available sources — OPM, IRS, SSA, VA, CMS, DoD, and state tax authorities. Anyone may fork or use this data freely.

---

## What This Is

A structured, version-controlled library of government-published financial data useful for retirement planning, tax analysis, benefits estimation, and fiscal modeling. Coverage includes:

- **Federal retirement systems** — FERS rates, TSP contribution limits, COLA history, Social Security bend points and taxable maximums
- **Federal pay** — GS pay tables (all grades/steps/localities), DCIPS pay bands, and military basic pay (27 grades × 22 YOS, 2016–2026)
- **Healthcare** — FEHB premiums (478 plan entries), FEHB plan benefits, FEDVIP dental/vision, TRICARE (retiree, active duty family, reserve, TFL), Medicare IRMAA
- **Veterans Affairs** — VA disability compensation, DIC, VGLI premiums
- **Tax data** — Federal brackets, standard deductions, IRA/Roth limits and phase-outs
- **State benefits** — Income tax treatment, real property tax exemptions, vehicle personal property tax exemptions, and veteran benefits for all 50 states + DC + 5 US territories (56 jurisdictions)
- **County property tax** — Effective rates and veteran exemptions for 10 counties
- **Actuarial tables** — SSA period life table (ages 0–119, both sexes)
- **State/local pensions** — Virginia VRS plans, Fairfax County ERFC plans, pension stacking patterns

Designed as a generic data source that any application, tool, or analysis can consume — no authentication, no API keys, no tracking.

---

## How to Use This Repo

1. Fetch `manifest.json` first — it's the version index listing all 44 available data files.
2. Compare each file's `version` to your locally cached copy.
3. Fetch only the files that have newer versions.
4. If GitHub is unreachable, fall back to your last cached fetch.

The `schema_version` and `schema_min_compatible` fields in the manifest enable consumers to detect breaking changes. See `schema-changelog.md` for details.

---

## File Structure

```
public-finance-data/
├── manifest.json                                ← Fetch this first (master version index, 44 entries)
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
│   ├── federal-tax-brackets.json                ← Federal income tax brackets (1913–2026)
│   ├── standard-deduction-history.json          ← Standard deduction history (1970–2026)
│   ├── capital-gains-rates.json                 ← Capital gains tax rates (1913–2026)
│   ├── hsa-limits.json                          ← HSA contribution limits (2004–2026)
│   ├── federal-pay-raises.json                  ← Federal civilian pay raises (1970–2026)
│   ├── estate-gift-tax.json                     ← Estate & gift tax exemptions (1916–2026)
│   ├── fers-contribution-rates.json             ← FERS employee contribution rates by hire cohort
│   ├── fehb-premium-history.json                ← FEHB average premium history (1999–2025)
│   ├── military-pay-tables.json                 ← Military basic pay by grade/YOS (2016–2026, 27 grades)
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
│   ├── state-benefits.json                      ← 56 jurisdictions (50 states + DC + 5 territories): income tax, property tax, veteran benefits
│   ├── arizona/
│   │   └── county-property-tax.json             ← Maricopa County
│   ├── colorado/
│   │   └── county-property-tax.json             ← El Paso County
│   ├── florida/
│   │   └── county-property-tax.json             ← Hillsborough County
│   ├── maryland/
│   │   └── county-property-tax.json             ← Prince George's County
│   ├── nevada/
│   │   └── county-property-tax.json             ← Clark County
│   ├── north-carolina/
│   │   └── county-property-tax.json             ← Cumberland County
│   ├── texas/
│   │   └── county-property-tax.json             ← Bexar County
│   ├── virginia/
│   │   ├── county-property-tax.json             ← Fairfax County, Virginia Beach
│   │   ├── vrs-plans.json                       ← VRS Plan 1, Plan 2, Hybrid
│   │   ├── erfc-plans.json                      ← ERFC Legacy, Tier 1, Tier 2 (Fairfax County)
│   │   └── plan-combinations.json               ← VRS + ERFC pension stacking patterns
│   └── washington/
│       └── county-property-tax.json             ← Pierce County
│
├── reference/
│   ├── static-refs.json                         ← SS FRA table, RMD Uniform Lifetime Table, locality codes
│   ├── ssa-life-table.json                      ← SSA period life table (ages 0–119, M/F/combined)
│   ├── other-db-template.json                   ← Generic DB plan template for user-entered pensions
│   ├── social-security-claiming.json            ← SS claiming strategy rules and reduction factors
│   ├── military-retirement-rules.json           ← Military retirement rules (Legacy, Redux, BRS, Ch.61 disability, CRDP/CRSC)
│   ├── rmd-rules-history.json                   ← RMD age threshold history and SECURE Act changes
│   └── obbba-tax-provisions.json                ← One Big Beautiful Bill Act tax provisions (2025)
│
└── tests/
    ├── validate.py                              ← Core validation (311 checks)
    ├── validate_tier2.py                        ← State benefits validation (255 checks)
    └── validate_tier3.py                        ← Tier 3A state expansion validation (123 checks)
    └── validate_tier3b.py                       ← Tier 3B state expansion validation (170 checks)
    └── validate_tier3c.py                       ← Tier 3C state expansion validation (187 checks)
    ├── validate_medicare.py                     ← Medicare rates validation (7 checks)
    ├── validate_dcips.py                        ← DCIPS pay tables validation (424 checks)
    ├── validate_historical.py                   ← Historical + healthcare + county validation (1,963 checks)
    ├── validate_pharmacy.py                     ← TRICARE pharmacy validation (92 checks)
    ├── validate_dental.py                       ← TRICARE dental validation (116 checks)
    └── validate_obbba.py                        ← OBBBA tax provisions validation (71 checks)
    └── validate_military.py                     ← Military retirement rules + pay tables validation (705 checks)
    └── validate_vehicle_audit.py                ← Vehicle personal property tax audit validation (111 checks)
    └── validate_territories.py                 ← US territory expansion validation (129 checks)
```

### Domain Organization

Files are organized by jurisdiction and domain:

- **`federal/`** — Federal civilian data (OPM, IRS, SSA, CMS), healthcare plans (OPM, DoD, CMS), and Department of Veterans Affairs benefits
- **`states/`** — State-level tax treatment, county property tax data, and state/county pension plans
- **`reference/`** — Static lookup tables, actuarial data, and templates that rarely change

---

## Manifest — Current Data Files (44 Entries)

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
| `federal_tax_brackets` | 1.1 | `federal/federal-tax-brackets.json` |
| `standard_deduction_history` | 1.0.1 | `federal/standard-deduction-history.json` |
| `capital_gains_rates` | 1.0.1 | `federal/capital-gains-rates.json` |
| `hsa_limits` | 1.0 | `federal/hsa-limits.json` |
| `federal_pay_raises` | 1.0 | `federal/federal-pay-raises.json` |
| `estate_gift_tax` | 1.0.1 | `federal/estate-gift-tax.json` |
| `fers_contribution_rates` | 1.0 | `federal/fers-contribution-rates.json` |
| `fehb_premium_history` | 1.0 | `federal/fehb-premium-history.json` |
| `fehb_rates` | 2026.3 | `federal/healthcare/fehb-rates.json` |
| `fehb_plan_benefits` | 2026.1 | `federal/healthcare/fehb-plan-benefits.json` |
| `fedvip_rates` | 2026.1 | `federal/healthcare/fedvip-rates.json` |
| `tricare_rates` | 2026.3 | `federal/healthcare/tricare-rates.json` |
| `medicare_rates` | 2026.2 | `federal/healthcare/medicare-rates.json` |
| `va_compensation` | 2026.1 | `federal/veterans-affairs/compensation.json` |
| `vgli` | 2026 | `federal/veterans-affairs/vgli.json` |
| `state_benefits` | 2.1 | `states/state-benefits.json` |
| `county_property_tax_az` | 1.1 | `states/arizona/county-property-tax.json` |
| `county_property_tax_co` | 1.1 | `states/colorado/county-property-tax.json` |
| `county_property_tax_fl` | 1.1 | `states/florida/county-property-tax.json` |
| `county_property_tax_md` | 1.1 | `states/maryland/county-property-tax.json` |
| `county_property_tax_nc` | 1.1 | `states/north-carolina/county-property-tax.json` |
| `county_property_tax_nv` | 1.1 | `states/nevada/county-property-tax.json` |
| `county_property_tax_tx` | 1.1 | `states/texas/county-property-tax.json` |
| `county_property_tax_va` | 1.1 | `states/virginia/county-property-tax.json` |
| `county_property_tax_wa` | 1.1 | `states/washington/county-property-tax.json` |
| `vrs_plans` | 2.0.0 | `states/virginia/vrs-plans.json` |
| `erfc_plans` | 2.0.0 | `states/virginia/erfc-plans.json` |
| `plan_combinations` | 2.0.0 | `states/virginia/plan-combinations.json` |
| `static_refs` | 1.0.1 | `reference/static-refs.json` |
| `ssa_life_table` | 1.0 | `reference/ssa-life-table.json` |
| `other_db_template` | 1.0.0 | `reference/other-db-template.json` |
| `social_security_claiming` | 1.1 | `reference/social-security-claiming.json` |
| `military_retirement_rules` | 2.0 | `reference/military-retirement-rules.json` |
| `military_pay_tables` | 2026.1 | `federal/military-pay-tables.json` |
| `rmd_rules_history` | 1.0 | `reference/rmd-rules-history.json` |
| `obbba_tax_provisions` | 1.0 | `reference/obbba-tax-provisions.json` |

---

## State and County Coverage

**State benefits** (50 states + DC + 5 US territories — 56 jurisdictions): AK, AL, AR, AS, AZ, CA, CO, CT, DC, DE, FL, GA, GU, HI, IA, ID, IL, IN, KS, KY, LA, MA, MD, ME, MI, MN, MO, MP, MS, MT, NC, ND, NE, NH, NJ, NM, NV, NY, OH, OK, OR, PA, PR, RI, SC, SD, TN, TX, UT, VA, VI, VT, WA, WI, WV, WY

Each state entry includes income tax treatment of military/federal retirement pay, property tax exemptions for disabled veterans, additional veteran benefit programs, application procedures, survivor transfer conditions, and pending legislation flags.

**County property tax** (10 counties across 9 states, stored as per-state files under `states/{state}/county-property-tax.json`): Fairfax County VA, Virginia Beach VA, Prince George's County MD, Cumberland County NC, Bexar County TX, Hillsborough County FL, El Paso County CO, Pierce County WA, Maricopa County AZ, Clark County NV

---

## Validation & CI

All data files are validated on every push and pull request via GitHub Actions. The CI pipeline runs fifteen test suites totaling **5,113 checks**:

| Suite | File | Checks | Coverage |
|-------|------|--------|----------|
| Core | `validate.py` | 315 | Manifest integrity, all federal/state/reference files |
| Tier 2 | `validate_tier2.py` | 490 | State benefits — field structure, exemption types, IU eligibility |
| Medicare | `validate_medicare.py` | 7 | Medicare IRMAA thresholds and premium values |
| DCIPS | `validate_dcips.py` | 424 | DCIPS pay bands — all occupational categories |
| Historical | `validate_historical.py` | 1,963 | Historical series, county property tax, FEHB, TRICARE, FEDVIP |
| Pharmacy | `validate_pharmacy.py` | 92 | TRICARE pharmacy cost-share validation |
| Dental | `validate_dental.py` | 116 | TRICARE dental premium validation |
| OBBBA | `validate_obbba.py` | 71 | OBBBA tax provision structure and cross-references |
| Tier 3A | `validate_tier3.py` | 123 | Tier 3A state expansion — CA, NY, OH, IL, MI, TN, SC, AL, MO, IN |
| Tier 3B | `validate_tier3b.py` | 170 | Tier 3B state expansion — NJ, MN, WI, KY, CT, OK, IA, AR, MS, KS |
| Tier 3C | `validate_tier3c.py` | 187 | Tier 3C state expansion — LA, MA, WV, NH, ME, UT, NM, ID, MT, DE |
| Tier 3D | `validate_tier3d.py` | 176 | Tier 3D final expansion — NE, ND, RI, SD, VT, WY (50 states + DC) |
| Vehicle Audit | `validate_vehicle_audit.py` | 111 | Vehicle personal property tax exemptions — MS, SC, CT, AL, AR, NC |
| Territories | `validate_territories.py` | 129 | US territory expansion — AS, GU, MP, PR, VI (56 jurisdictions) |
| Military | `validate_military.py` | 705 | Military retirement rules v2.0, pay tables 2016–2026 |

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
| `federal/military-pay-tables.json` | January | NDAA enacts annual pay raise |
| `reference/military-retirement-rules.json` | As enacted | Retirement/disability/concurrent receipt law changes |
| `states/state-benefits.json` | As needed | State tax law changes |
| `states/{state}/county-property-tax.json` | As needed | County rate or exemption changes |
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
| Military basic pay tables | DFAS / navycs.com | https://militarypay.defense.gov/Pay/Basic-Pay/ |
| Military retirement rules | Defense.gov / USC | https://militarypay.defense.gov/Pay/Retirement/ |

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

### `federal/military-pay-tables.json` (January, after NDAA)
- [ ] Add new year's pay table (all 27 grades × 22 YOS columns)
- [ ] Update `pay_raise_history` with new year's raise percentage and NDAA authority
- [ ] Verify values against DFAS published tables
- [ ] Update `"version"` to new year
- [ ] Update `manifest.json` `military_pay_tables.version`

---

## License

Public domain. All data is reproduced from U.S. government publications, which are not subject to copyright under 17 U.S.C. § 105.

---

*This repository has no affiliation with OPM, IRS, SSA, VA, CMS, DoD, or any U.S. government agency.*
