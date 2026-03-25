# public-finance-data

Curated public finance reference data for retirement planning, tax analysis, and benefits estimation — covering all retirement populations.

This repository contains **no personal information of any kind**. All data is drawn from publicly available sources — IRS, SSA, CMS, OPM, VA, DoD, and state/local government agencies. Anyone may fork or use this data freely.

---

## What This Is

A structured, version-controlled library of publicly available financial data useful for retirement planning, tax analysis, benefits estimation, and fiscal modeling. Covers universal retirement topics (Social Security, tax brackets, RMDs, Roth conversions, Medicare/IRMAA, state tax treatment) as well as sector-specific systems (federal civilian, military, state/local government pensions, veterans benefits). Coverage includes:

- **Tax data** — Federal brackets, standard deductions, capital gains rates, IRA/Roth limits and phase-outs, HSA limits, estate & gift tax, filing status thresholds (10 years × 5 statuses), OBBBA tax provisions
- **Social Security** — Bend points, taxable maximums, COLA history, claiming strategy rules, reduction factors, earnings test thresholds, FRA tables
- **Retirement accounts** — TSP contribution limits, IRA/Roth limits and phase-outs, RMD rules history, Roth conversion rules
- **Healthcare** — Medicare IRMAA thresholds and premiums, FEHB premiums (478 plan entries), FEHB plan benefits, FEHB retirement eligibility, FEDVIP dental/vision, TRICARE (retiree, active duty family, reserve, TFL, pharmacy, dental)
- **State benefits** — Income tax treatment of retirement income, real property tax exemptions, vehicle personal property tax exemptions, and veteran benefits for all 50 states + DC + 5 US territories (56 jurisdictions)
- **County property tax** — Effective rates and exemptions for 44 counties across 13 states
- **Federal retirement systems** — FERS rates, FERS computation rules, FERS SRS rules, CSRS rules, TSP limits, COLA history, LEO premium pay, Foreign Service retirement (FSRDS/FSPS), master index of all federal retirement systems and 6(c) special category positions
- **Federal pay** — GS pay tables (all grades/steps/localities), DCIPS pay bands, military basic pay (27 grades × 22 YOS, 2016–2026), federal pay raise history
- **Life insurance** — FEGLI rates (Basic + Options A/B/C, age-banded), VGLI premiums
- **Veterans Affairs** — VA disability compensation, DIC, VGLI premiums
- **Actuarial tables** — SSA period life table (ages 0–119, both sexes), RMD rules history
- **State/local pensions** — California (CalPERS, CalSTRS, SDCERA, LACERA), Colorado (COPERA), DC (DCRB), Florida (FRS), Maryland (MD-SRPS, Montgomery County MCERP), New York (NYSLRS, NYSTRS), Ohio (OPERS, STRS-Ohio), Texas (ERS, TRS), Virginia (VRS, Fairfax County ERFC/FCERS/PORS/URS, Arlington County ACERS, Richmond RRS, Falls Church FCPP), pension stacking patterns
- **Reference templates** — Generic defined-benefit pension template for manual-entry plans (any sector)

Designed as a generic data source for retirement planning applications, financial tools, or independent analysis — serving federal, military, state/local government, and private-sector retirement populations. No authentication, no API keys, no tracking.

---

## How to Use This Repo

1. Fetch `manifest.json` first — it's the version index listing all 82 available data files.
2. Compare each file's `version` to your locally cached copy.
3. Fetch only the files that have newer versions.
4. If GitHub is unreachable, fall back to your last cached fetch.

The `schema_version` and `schema_min_compatible` fields in the manifest enable consumers to detect breaking changes. See `schema-changelog.md` for details.

---

## File Structure

```
public-finance-data/
├── manifest.json                                ← Fetch this first (master version index, 82 entries)
├── schema-changelog.md                          ← Documents every schema structure change
│
├── federal/
│   ├── rates-annual.json                        ← TSP, IRMAA, IRA, SS, FERS, tax brackets, COLA, earnings test
│   ├── pay-tables.json                          ← GS pay tables — all grades/steps/localities (2016–2026, 11 years)
│   ├── tsp-limits.json                          ← TSP contribution limits (1987–2026)
│   ├── ss-bend-points.json                      ← SS bend points (1979–2026)
│   ├── ss-taxable-max.json                      ← SS taxable maximum (1937–2026)
│   ├── ira-limits.json                          ← IRA/Roth limits + phase-outs (1975–2026)
│   ├── cola-history.json                        ← COLA history — FERS, CSRS, SS, VA (52 years, 4 systems)
│   ├── federal-tax-brackets.json                ← Federal income tax brackets (1913–2026)
│   ├── standard-deduction-history.json          ← Standard deduction history (1970–2026)
│   ├── capital-gains-rates.json                 ← Capital gains tax rates (1913–2026)
│   ├── hsa-limits.json                          ← HSA contribution limits (2004–2026)
│   ├── federal-pay-raises.json                  ← Federal civilian pay raises (1970–2026)
│   ├── estate-gift-tax.json                     ← Estate & gift tax exemptions (1916–2026)
│   ├── fers-contribution-rates.json             ← FERS employee contribution rates by hire cohort
│   ├── fehb-premium-history.json                ← FEHB average premium history (1999–2025)
│   ├── fegli-rates.json                         ← FEGLI life insurance — Basic + Options A/B/C, age-banded
│   ├── fers-computation-rules.json              ← FERS annuity computation — multipliers, MRA+10, deferred, disability
│   ├── fers-eligibility-rules.json              ← FERS retirement eligibility — MRA schedule, pathways, VERA/VSIP
│   ├── fers-service-credit-rules.json           ← Service credit — deposit, redeposit, military buyback, sick leave
│   ├── filing-status-thresholds.json            ← IRS filing status thresholds — 5 statuses × 6 domains (2016–2025)
│   ├── leo-premium-pay.json                     ← LEO premium pay rates — availability, administratively uncontrollable overtime
│   ├── military-pay-tables.json                 ← Military basic pay by grade/YOS (2016–2026, 27 grades)
│   ├── foreign-service-pay-tables.json          ← Foreign Service pay by grade FP-1–FP-9/step 1–14 (2016–2026)
│   ├── dcips/
│   │   └── dcips-pay-tables.json                ← DCIPS pay bands — all occupational categories
│   ├── healthcare/
│   │   ├── fehb-rates.json                      ← FEHB premiums — 478 plan entries (132 plans × enrollment types)
│   │   ├── fehb-plan-benefits.json              ← FEHB plan benefit details (deductibles, copays, coverage)
│   │   ├── fehb-retirement-eligibility.json     ← FEHB retirement eligibility — 5-year rule, TCC, LWOP
│   │   ├── fedvip-rates.json                    ← FEDVIP dental + vision premiums
│   │   ├── tricare-rates.json                   ← TRICARE costs — retiree, ADFM, reserve, TFL, pharmacy, dental
│   │   └── medicare-rates.json                  ← Medicare Part B/D premiums + IRMAA thresholds
│   └── veterans-affairs/
│       ├── compensation.json                    ← VA disability comp rates, DIC, VA COLA
│       └── vgli.json                            ← VGLI age-banded premium table
│
├── states/
│   ├── state-benefits.json                      ← 56 jurisdictions (50 states + DC + 5 territories): income tax, property tax, veteran benefits
│   ├── arizona/
│   │   └── county-property-tax.json             ← Maricopa County
│   ├── california/
│   │   ├── calpers-plans.json                   ← CalPERS pension plans — 5 formulas, Classic + PEPRA (~2M members)
│   │   ├── calstrs-plans.json                   ← CalSTRS pension plans — 2 tiers, DB + SBMA (~990K members)
│   │   ├── county-property-tax.json             ← San Diego, Sacramento, Riverside, Los Angeles (4 counties)
│   │   ├── los-angeles-county/
│   │   │   └── lacera-plans.json                ← LACERA pension plans — 9 plans, general + safety (185K+ members)
│   │   └── san-diego-county/
│   │       └── sdcera-plans.json                ← SDCERA pension plans — 9 benefit tiers (51K+ members)
│   ├── colorado/
│   │   ├── copera-plans.json                    ← COPERA pension plans — state/school/local/judicial/DPS divisions
│   │   └── county-property-tax.json             ← El Paso, Douglas (2 counties)
│   ├── dc/
│   │   └── dc-dcrb-plans.json                   ← DCRB pension plans — police, fire, legacy teachers
│   ├── florida/
│   │   ├── frs-plans.json                       ← FRS pension plans — DB + Investment Plan + hybrid
│   │   └── county-property-tax.json             ← Hillsborough, Orange, Brevard, Okaloosa, Escambia, Duval (6 counties)
│   ├── georgia/
│   │   └── county-property-tax.json             ← Liberty, Houston, Chatham, Muscogee (4 counties)
│   ├── maryland/
│   │   ├── md-srps-plans.json                   ← MD-SRPS pension plans — 7 systems (~400K members)
│   │   ├── county-property-tax.json             ← Prince George's, Anne Arundel, Howard (3 counties)
│   │   └── montgomery-county/
│   │       └── mcerp-plans.json                 ← MCERP pension plans — 8 types ($7.3B system)
│   ├── nevada/
│   │   └── county-property-tax.json             ← Clark County
│   ├── new-york/
│   │   ├── nyslrs-plans.json                    ← NYSLRS pension plans — ERS + PFRS tiers (~1.1M members)
│   │   └── nystrs-plans.json                    ← NYSTRS pension plans — 7 tiers (~430K members)
│   ├── north-carolina/
│   │   └── county-property-tax.json             ← Cumberland, Harnett, Onslow (3 counties)
│   ├── ohio/
│   │   ├── opers-plans.json                     ← OPERS pension plans — DB + DC + Combined (~1M members)
│   │   └── strs-ohio-plans.json                 ← STRS Ohio pension plans — 4 tiers (~500K members)
│   ├── south-carolina/
│   │   └── county-property-tax.json             ← Richland, Berkeley, Beaufort, Horry (4 counties)
│   ├── tennessee/
│   │   └── county-property-tax.json             ← Montgomery, Blount, Knox (3 counties)
│   ├── texas/
│   │   ├── ers-plans.json                       ← Texas ERS pension plans — state employees (~350K members)
│   │   ├── trs-plans.json                       ← Texas TRS pension plans — 8 tiers (~2M members)
│   │   └── county-property-tax.json             ← Bexar, Killeen, Bell, El Paso (4 counties)
│   ├── virginia/
│   │   ├── county-property-tax.json             ← Fairfax, Virginia Beach, Loudoun, Arlington, Prince William, Henrico, Chesterfield (7 counties)
│   │   ├── vrs-plans.json                       ← VRS Plan 1, Plan 2, Hybrid, SPORS, VaLORS, hazardous duty
│   │   ├── arlington-county/
│   │   │   └── acers-plans.json                 ← ACERS pension plans (independent, not VRS)
│   │   ├── fairfax-county/
│   │   │   ├── erfc-plans.json                  ← ERFC Legacy, Tier 1, Tier 2 (county-level pension)
│   │   │   ├── fcers-plans.json                 ← FCERS Plans A-E (county general employees pension)
│   │   │   ├── pors-plans.json                  ← PORS Plans A-C (sworn police officers pension)
│   │   │   ├── urs-plans.json                   ← URS Plans B/D/E/F (fire, sheriff, uniformed pension)
│   │   │   └── plan-combinations.json           ← VRS + ERFC pension stacking patterns
│   │   ├── falls-church/
│   │   │   └── fcpp-plans.json                  ← Falls Church Basic + Police pension plans (independent city)
│   │   └── richmond/
│   │       └── rrs-plans.json                   ← RRS pension plans — 8 types (CLOSED 2024, VRS transition)
│   └── washington/
│       └── county-property-tax.json             ← Pierce, Kitsap (2 counties)
│
├── reference/
│   ├── static-refs.json                         ← SS FRA table, RMD Uniform Lifetime Table, locality codes
│   ├── ssa-life-table.json                      ← SSA period life table (ages 0–119, M/F/combined)
│   ├── other-db-template.json                   ← Generic DB plan template for user-entered pensions
│   ├── social-security-claiming.json            ← SS claiming strategy rules, reduction factors, earnings test
│   ├── military-retirement-rules.json           ← Military retirement (Legacy, Redux, BRS, Ch.61, CRDP/CRSC) — all 8 uniformed services
│   ├── foreign-service-retirement-rules.json    ← Foreign Service retirement (FSRDS, FSRDS Offset, FSPS)
│   ├── federal-retirement-systems-index.json    ← Master catalog of ALL federal retirement systems + 6(c) positions
│   ├── rmd-rules-history.json                   ← RMD age threshold history and SECURE Act changes
│   ├── obbba-tax-provisions.json                ← One Big Beautiful Bill Act tax provisions (2025)
│   ├── tsp-roth-conversion.json                 ← TSP Roth conversion rules and tax treatment
│   ├── fers-srs-rules.json                      ← FERS Special Retirement Supplement rules and earnings test
│   └── csrs-retirement-rules.json               ← CSRS retirement computation and survivor annuity rules
│
└── tests/
    ├── validate.py                              ← Core validation (1,309 checks)
    ├── validate_tier2.py                        ← State benefits validation (530 checks)
    ├── validate_tier3.py                        ← Tier 3A state expansion validation (125 checks)
    ├── validate_tier3b.py                       ← Tier 3B state expansion validation (172 checks)
    ├── validate_tier3c.py                       ← Tier 3C state expansion validation (187 checks)
    ├── validate_tier3d.py                       ← Tier 3D final expansion validation (179 checks)
    ├── validate_medicare.py                     ← Medicare rates validation (7 checks)
    ├── validate_dcips.py                        ← DCIPS pay tables validation (424 checks)
    ├── validate_historical.py                   ← Historical + healthcare + county validation (2,028 checks)
    ├── validate_pharmacy.py                     ← TRICARE pharmacy validation (92 checks)
    ├── validate_dental.py                       ← TRICARE dental validation (116 checks)
    ├── validate_obbba.py                        ← OBBBA tax provisions validation (71 checks)
    ├── validate_military.py                     ← Military retirement rules + pay tables validation (705 checks)
    ├── validate_vehicle_audit.py                ← Vehicle personal property tax audit validation (123 checks)
    ├── validate_territories.py                  ← US territory expansion validation (129 checks)
    ├── validate_federal_retirement.py           ← Federal retirement rules validation (157 checks)
    ├── validate_municipal.py                    ← Municipal pension validation (153 checks)
    ├── validate_sdcera.py                       ← SDCERA pension validation (178 checks)
    ├── validate_lacera.py                       ← LACERA pension validation (1,134 checks)
    ├── validate_filing_status.py                ← Filing status thresholds validation (816 checks)
    ├── validate_county_property_tax.py          ← County property tax — 13 states, 44 counties (1,635 checks)
    ├── validate_leo_fers_comp.py                ← LEO premium pay + FERS computation validation (207 checks)
    ├── validate_foreign_service.py              ← Foreign service retirement rules validation (94 checks)
    ├── validate_systems_index.py                ← Federal retirement systems index validation (114 checks)
    ├── validate_fers_eligibility.py             ← FERS eligibility + service credit validation (206 checks)
    ├── validate_pay_tables.py                   ← GS pay tables (11yr) + VA comp history validation (1,333 checks)
    ├── validate_fs_pay.py                       ← Foreign Service pay tables validation (1,893 checks)
    ├── validate_calpers.py                      ← CalPERS pension validation (208 checks)
    ├── validate_calstrs.py                      ← CalSTRS pension validation (98 checks)
    ├── validate_copera.py                       ← COPERA pension validation (128 checks)
    ├── validate_dcrb.py                         ← DC Retirement Board validation (86 checks)
    ├── validate_md_srps.py                      ← Maryland SRPS pension validation (110 checks)
    ├── validate_ny_pensions.py                  ← New York pension validation — NYSLRS + NYSTRS (92 checks)
    ├── validate_opers.py                        ← Ohio OPERS pension validation (231 checks)
    ├── validate_state_pensions.py               ← Multi-state pension validation — FRS, TRS-TX, STRS-OH (142 checks)
    └── validate_tx_ers.py                       ← Texas ERS + TRS pension validation (240 checks)
```

### Domain Organization

Files are organized by jurisdiction and domain:

- **`federal/`** — Federal-level data: tax brackets and thresholds (IRS), Social Security (SSA), Medicare/IRMAA (CMS), retirement account limits (IRS), federal civilian pay and benefits (OPM), healthcare plans (OPM, DoD, CMS), life insurance (OPM), military pay, and veterans benefits (VA)
- **`states/`** — State-level tax treatment of retirement income, county property tax data, state pension plans (e.g., CalPERS, VRS, FRS, OPERS), and county/municipal pension plans in subdirectories (e.g., `states/virginia/fairfax-county/`, `states/california/san-diego-county/`, `states/california/los-angeles-county/`, `states/maryland/montgomery-county/`)
- **`reference/`** — Static lookup tables, actuarial data, retirement system rules, plan templates, and reference data that rarely changes

---

## Manifest — Current Data Files (82 Entries)

| Key | Version | File |
|-----|---------|------|
| `rates_annual` | 2026.3 | `federal/rates-annual.json` |
| `pay_tables` | 2.0 | `federal/pay-tables.json` |
| `dcips_pay_tables` | 2026.1 | `federal/dcips/dcips-pay-tables.json` |
| `tsp_limits` | 1.0 | `federal/tsp-limits.json` |
| `ss_bend_points` | 1.0 | `federal/ss-bend-points.json` |
| `ss_taxable_max` | 1.0 | `federal/ss-taxable-max.json` |
| `ira_limits` | 2.1 | `federal/ira-limits.json` |
| `cola_history` | 1.1 | `federal/cola-history.json` |
| `federal_tax_brackets` | 1.2 | `federal/federal-tax-brackets.json` |
| `standard_deduction_history` | 1.2 | `federal/standard-deduction-history.json` |
| `capital_gains_rates` | 1.2 | `federal/capital-gains-rates.json` |
| `hsa_limits` | 1.0 | `federal/hsa-limits.json` |
| `federal_pay_raises` | 1.0 | `federal/federal-pay-raises.json` |
| `estate_gift_tax` | 1.0.1 | `federal/estate-gift-tax.json` |
| `fers_contribution_rates` | 1.0 | `federal/fers-contribution-rates.json` |
| `fehb_premium_history` | 1.0 | `federal/fehb-premium-history.json` |
| `fegli_rates` | 1.0 | `federal/fegli-rates.json` |
| `fers_computation_rules` | 2026.1 | `federal/fers-computation-rules.json` |
| `fers_eligibility_rules` | 1.0 | `federal/fers-eligibility-rules.json` |
| `fers_service_credit_rules` | 1.0 | `federal/fers-service-credit-rules.json` |
| `filing_status_thresholds` | 2026.2 | `federal/filing-status-thresholds.json` |
| `leo_premium_pay` | 2026.1 | `federal/leo-premium-pay.json` |
| `military_pay_tables` | 2026.1 | `federal/military-pay-tables.json` |
| `fs_pay_tables` | 2026.1 | `federal/foreign-service-pay-tables.json` |
| `fehb_rates` | 2026.3 | `federal/healthcare/fehb-rates.json` |
| `fehb_plan_benefits` | 2026.1 | `federal/healthcare/fehb-plan-benefits.json` |
| `fehb_retirement_eligibility` | 1.0 | `federal/healthcare/fehb-retirement-eligibility.json` |
| `fedvip_rates` | 2026.2 | `federal/healthcare/fedvip-rates.json` |
| `tricare_rates` | 2026.3 | `federal/healthcare/tricare-rates.json` |
| `medicare_rates` | 2026.2 | `federal/healthcare/medicare-rates.json` |
| `va_compensation` | 2026.2 | `federal/veterans-affairs/compensation.json` |
| `vgli` | 2026 | `federal/veterans-affairs/vgli.json` |
| `state_benefits` | 2.10 | `states/state-benefits.json` |
| `county_property_tax_az` | 1.1 | `states/arizona/county-property-tax.json` |
| `county_property_tax_california` | 1.0 | `states/california/county-property-tax.json` |
| `county_property_tax_co` | 1.2 | `states/colorado/county-property-tax.json` |
| `county_property_tax_fl` | 1.3 | `states/florida/county-property-tax.json` |
| `county_property_tax_ga` | 1.1 | `states/georgia/county-property-tax.json` |
| `county_property_tax_md` | 1.2 | `states/maryland/county-property-tax.json` |
| `county_property_tax_nc` | 1.3 | `states/north-carolina/county-property-tax.json` |
| `county_property_tax_nv` | 1.1 | `states/nevada/county-property-tax.json` |
| `county_property_tax_sc` | 1.0 | `states/south-carolina/county-property-tax.json` |
| `county_property_tax_tn` | 1.0 | `states/tennessee/county-property-tax.json` |
| `county_property_tax_tx` | 1.3 | `states/texas/county-property-tax.json` |
| `county_property_tax_va` | 1.3 | `states/virginia/county-property-tax.json` |
| `county_property_tax_wa` | 1.2 | `states/washington/county-property-tax.json` |
| `calpers_plans_california` | 2026.2 | `states/california/calpers-plans.json` |
| `calstrs_plans_california` | 2026.1 | `states/california/calstrs-plans.json` |
| `sdcera_plans` | 1.0 | `states/california/san-diego-county/sdcera-plans.json` |
| `lacera_plans_los_angeles` | 2026.3 | `states/california/los-angeles-county/lacera-plans.json` |
| `copera_plans_colorado` | 2026.1 | `states/colorado/copera-plans.json` |
| `dcrb_plans_dc` | 2026.1 | `states/dc/dc-dcrb-plans.json` |
| `frs_plans_florida` | 2026.1 | `states/florida/frs-plans.json` |
| `md_srps_plans_maryland` | 2026.1 | `states/maryland/md-srps-plans.json` |
| `mcerp_plans_montgomery` | 2026.3 | `states/maryland/montgomery-county/mcerp-plans.json` |
| `nyslrs_plans_new_york` | 2026.1 | `states/new-york/nyslrs-plans.json` |
| `nystrs_plans_new_york` | 2026.1 | `states/new-york/nystrs-plans.json` |
| `opers_plans_ohio` | 2026.1 | `states/ohio/opers-plans.json` |
| `strs_ohio_plans` | 2026.1 | `states/ohio/strs-ohio-plans.json` |
| `ers_plans_texas` | 2026.1 | `states/texas/ers-plans.json` |
| `trs_plans_texas` | 2026.1 | `states/texas/trs-plans.json` |
| `vrs_plans` | 2026.2 | `states/virginia/vrs-plans.json` |
| `acers_plans_arlington` | 2026.2 | `states/virginia/arlington-county/acers-plans.json` |
| `erfc_plans_fairfax` | 2.0.0 | `states/virginia/fairfax-county/erfc-plans.json` |
| `fcers_plans_fairfax` | 2026.1 | `states/virginia/fairfax-county/fcers-plans.json` |
| `pors_plans_fairfax` | 2026.1 | `states/virginia/fairfax-county/pors-plans.json` |
| `urs_plans_fairfax` | 2026.1 | `states/virginia/fairfax-county/urs-plans.json` |
| `plan_combinations_fairfax` | 2.0.0 | `states/virginia/fairfax-county/plan-combinations.json` |
| `fcpp_plans_falls_church` | 2026.3 | `states/virginia/falls-church/fcpp-plans.json` |
| `rrs_plans_richmond` | 2026.1 | `states/virginia/richmond/rrs-plans.json` |
| `csrs_retirement_rules` | 1.0 | `reference/csrs-retirement-rules.json` |
| `federal_retirement_systems_index` | 1.0 | `reference/federal-retirement-systems-index.json` |
| `fers_srs_rules` | 1.1 | `reference/fers-srs-rules.json` |
| `foreign_service_retirement_rules` | 1.0 | `reference/foreign-service-retirement-rules.json` |
| `military_retirement_rules` | 2.1 | `reference/military-retirement-rules.json` |
| `obbba_tax_provisions` | 1.0 | `reference/obbba-tax-provisions.json` |
| `other_db_template` | 1.0.0 | `reference/other-db-template.json` |
| `rmd_rules_history` | 1.0 | `reference/rmd-rules-history.json` |
| `social_security_claiming` | 1.2 | `reference/social-security-claiming.json` |
| `ssa_life_table` | 1.0 | `reference/ssa-life-table.json` |
| `static_refs` | 1.0.2 | `reference/static-refs.json` |
| `tsp_roth_conversion` | 1.0 | `reference/tsp-roth-conversion.json` |

---

## State and County Coverage

**State benefits** (50 states + DC + 5 US territories — 56 jurisdictions): AK, AL, AR, AS, AZ, CA, CO, CT, DC, DE, FL, GA, GU, HI, IA, ID, IL, IN, KS, KY, LA, MA, MD, ME, MI, MN, MO, MP, MS, MT, NC, ND, NE, NH, NJ, NM, NV, NY, OH, OK, OR, PA, PR, RI, SC, SD, TN, TX, UT, VA, VI, VT, WA, WI, WV, WY

Each state entry includes income tax treatment of retirement income (Social Security, pension, military/federal pay), property tax exemptions (veteran, senior, disability), additional benefit programs, application procedures, survivor transfer conditions, and pending legislation flags.

**County property tax** (44 counties across 13 states, stored as per-state files under `states/{state}/county-property-tax.json`):
- Arizona: Maricopa County (1)
- California: San Diego, Sacramento, Riverside, Los Angeles (4)
- Colorado: El Paso, Douglas (2)
- Florida: Hillsborough, Orange, Brevard, Okaloosa, Escambia, Duval (6)
- Georgia: Liberty, Houston, Chatham, Muscogee (4)
- Maryland: Prince George's, Anne Arundel, Howard (3)
- Nevada: Clark County (1)
- North Carolina: Cumberland, Harnett, Onslow (3)
- South Carolina: Richland, Berkeley, Beaufort, Horry (4)
- Tennessee: Montgomery, Blount, Knox (3)
- Texas: Bexar, Killeen, Bell, El Paso (4)
- Virginia: Fairfax, Virginia Beach, Loudoun, Arlington, Prince William, Henrico, Chesterfield (7)
- Washington: Pierce, Kitsap (2)

**State/local pension systems** (9 states + DC, 24 system files):
- California: CalPERS (~2M members), CalSTRS (~990K), SDCERA (San Diego County — 9 benefit tiers), LACERA (Los Angeles County — 9 plans, largest US county pension)
- Colorado: COPERA (state/school/local/judicial/DPS divisions)
- DC: DCRB (police, fire, legacy teachers)
- Florida: FRS (DB + Investment Plan + hybrid)
- Maryland: MD-SRPS (7 statewide systems), Montgomery County MCERP (8 plan types)
- New York: NYSLRS (ERS + PFRS tiers, ~1.1M members), NYSTRS (7 tiers, ~430K members)
- Ohio: OPERS (DB + DC + Combined, ~1M members), STRS-Ohio (4 tiers, ~500K members)
- Texas: ERS (~350K members), TRS (~2M members)
- Virginia: VRS (state), Fairfax County (ERFC, FCERS, PORS, URS + stacking), Arlington County (ACERS), Falls Church (FCPP), Richmond (RRS)

---

## Validation & CI

All data files are validated on every push and pull request via GitHub Actions. The CI pipeline runs **36 test suites** totaling **~15,450 checks**:

| Suite | File | Checks | Coverage |
|-------|------|--------|----------|
| Core | `validate.py` | 1,309 | Manifest integrity, all federal/state/reference files, pension systems, state benefits audit, legislation watch, partial exemption audit, SS taxation audit, SS 2026 data accuracy + cross-file checks |
| Tier 2 | `validate_tier2.py` | 530 | State benefits — field structure, exemption types, IU eligibility |
| Tier 3A | `validate_tier3.py` | 125 | Tier 3A state expansion — CA, NY, OH, IL, MI, TN, SC, AL, MO, IN |
| Tier 3B | `validate_tier3b.py` | 172 | Tier 3B state expansion — NJ, MN, WI, KY, CT, OK, IA, AR, MS, KS |
| Tier 3C | `validate_tier3c.py` | 187 | Tier 3C state expansion — LA, MA, WV, NH, ME, UT, NM, ID, MT, DE |
| Tier 3D | `validate_tier3d.py` | 179 | Tier 3D final expansion — NE, ND, RI, SD, VT, WY (50 states + DC) |
| Medicare | `validate_medicare.py` | 7 | Medicare IRMAA thresholds and premium values |
| DCIPS | `validate_dcips.py` | 424 | DCIPS pay bands — all occupational categories |
| Historical | `validate_historical.py` | 2,028 | Historical series, county property tax, FEHB, TRICARE, FEDVIP |
| Pharmacy | `validate_pharmacy.py` | 92 | TRICARE pharmacy cost-share validation |
| Dental | `validate_dental.py` | 116 | TRICARE dental premium validation |
| OBBBA | `validate_obbba.py` | 71 | OBBBA tax provision structure and cross-references |
| Military | `validate_military.py` | 705 | Military retirement rules v2.0, pay tables 2016–2026 |
| Vehicle Audit | `validate_vehicle_audit.py` | 123 | Vehicle personal property tax exemptions — MS, SC, CT, AL, AR, NC, NE |
| Territories | `validate_territories.py` | 129 | US territory expansion — AS, GU, MP, PR, VI (56 jurisdictions) |
| Federal Retirement | `validate_federal_retirement.py` | 157 | FERS/CSRS rules, contribution rates, FEGLI, FEHB eligibility |
| Municipal | `validate_municipal.py` | 153 | Municipal pension plans — MCERP, FCPP, RRS, ACERS |
| SDCERA | `validate_sdcera.py` | 178 | SDCERA 9-tier pension system — formulas, eligibility, PEPRA flags |
| LACERA | `validate_lacera.py` | 1,134 | LACERA 9-plan pension system — general/safety plans, COLA, benefit factors, COLA history |
| Filing Status | `validate_filing_status.py` | 816 | Filing status thresholds — 5 statuses × 6 domains (2016–2025) |
| County Property Tax | `validate_county_property_tax.py` | 1,635 | County property tax — 13 states, 44 counties, rates + exemptions |
| LEO/FERS Comp | `validate_leo_fers_comp.py` | 207 | LEO premium pay rates + FERS computation rules |
| Foreign Service | `validate_foreign_service.py` | 94 | Foreign service retirement rules — FSRDS, FSPS, FSRDS Offset |
| Systems Index | `validate_systems_index.py` | 114 | Federal retirement systems index — all known systems + 6(c) positions |
| FERS Eligibility | `validate_fers_eligibility.py` | 206 | FERS eligibility rules + service credit rules + cross-file consistency |
| Pay Tables Bundle | `validate_pay_tables.py` | 1,333 | GS pay tables (11yr, OPM-verified) + VA compensation history (11yr) |
| FS Pay Tables | `validate_fs_pay.py` | 1,893 | Foreign Service pay tables — 9 grades × 14 steps × 11 years |
| CalPERS | `validate_calpers.py` | 208 | CalPERS pension plans — 5 formulas, IRC limits, COLA, PEPRA |
| CalSTRS | `validate_calstrs.py` | 98 | CalSTRS pension plans — 2 tiers, SBMA, contribution rates |
| COPERA | `validate_copera.py` | 128 | COPERA pension plans — all divisions, COLA, benefit formulas |
| DCRB | `validate_dcrb.py` | 86 | DC Retirement Board — police, fire, legacy teacher plans |
| MD-SRPS | `validate_md_srps.py` | 110 | Maryland SRPS — 7 retirement systems, benefit formulas |
| NY Pensions | `validate_ny_pensions.py` | 92 | NYSLRS (ERS + PFRS) and NYSTRS — tier structures, formulas |
| OPERS | `validate_opers.py` | 231 | Ohio OPERS — DB + DC + Combined plans, eligibility, COLA |
| State Pensions | `validate_state_pensions.py` | 142 | Multi-state pension validation — FRS, TRS-TX, STRS-OH |
| TX ERS/TRS | `validate_tx_ers.py` | 240 | Texas ERS + TRS — benefit formulas, eligibility, IRC limits |

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
| `federal/fegli-rates.json` | As published | OPM periodic rate adjustment (last: Oct 2021) |
| `federal/veterans-affairs/compensation.json` | December | VA publishes new COLA rates |
| `federal/veterans-affairs/vgli.json` | As published | VA updates VGLI premium schedule |
| `federal/military-pay-tables.json` | January | NDAA enacts annual pay raise |
| `reference/military-retirement-rules.json` | As enacted | Retirement/disability/concurrent receipt law changes |
| `states/state-benefits.json` | As needed | State tax law changes |
| `states/{state}/county-property-tax.json` | As needed | County rate or exemption changes |
| State pension plans | As needed | Plan parameter changes, new systems added |
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
| FEGLI life insurance | OPM | https://www.opm.gov/healthcare-insurance/life-insurance/ |
| TRICARE costs | TRICARE | https://www.tricare.mil/Costs/Compare |
| IRMAA thresholds | CMS / Medicare.gov | https://www.medicare.gov/your-medicare-costs/part-b-costs |
| IRA / tax limits | IRS | https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits |
| Tax brackets | IRS | https://www.irs.gov/newsroom |
| SS COLA + bend points | SSA | https://www.ssa.gov/oact/COLA/colasummary.html |
| SS earnings test | SSA | https://www.ssa.gov/oact/cola/rtea.html |
| SS Full Retirement Ages | SSA | https://www.ssa.gov/benefits/retirement/planner/agereduction.html |
| SSA life tables | SSA | https://www.ssa.gov/oact/STATS/table4c6.html |
| VA compensation rates | VA.gov | https://www.va.gov/disability/compensation-rates/veteran-rates/ |
| DIC rates | VA.gov | https://www.va.gov/family-and-caregiver-benefits/survivor-compensation/dependency-indemnity-compensation/survivor-rates/ |
| VGLI premiums | VA.gov | https://www.benefits.va.gov/INSURANCE/vgli.asp |
| RMD Uniform Lifetime Table | IRS Pub. 590-B | https://www.irs.gov/publications/p590b |
| VRS plan parameters | VRS | https://www.varetire.org/retirement-plans/ |
| ERFC plan parameters | ERFC | https://www.erfcpension.org/ |
| ACERS plan parameters | Arlington County | https://www.arlingtonva.us/Government/Careers/6-Retiree-Resources/ACERS |
| FCERS plan parameters | Fairfax County Retirement Systems | https://www.fairfaxcounty.gov/retirement/employees-retirement-system |
| PORS plan parameters | Fairfax County Retirement Systems | https://www.fairfaxcounty.gov/retirement/police-officers-retirement-system |
| URS plan parameters | Fairfax County Retirement Systems | https://www.fairfaxcounty.gov/retirement/uniformed-retirement-system |
| RRS plan parameters | City of Richmond Retirement System | https://www.rva.gov/retirement-system/employees |
| FCPP plan parameters | City of Falls Church | https://www.fallschurchva.gov/ |
| MCERP plan parameters | Montgomery County MD | https://www.montgomerycountymd.gov/mcerp/about.html |
| SDCERA plan parameters | SDCERA | https://www.sdcera.org/ |
| LACERA plan parameters | LACERA | https://www.lacera.gov/ |
| CalPERS plan parameters | CalPERS | https://www.calpers.ca.gov/ |
| CalSTRS plan parameters | CalSTRS | https://www.calstrs.com/ |
| COPERA plan parameters | Colorado PERA | https://www.copera.org/ |
| DCRB plan parameters | DC Retirement Board | https://dcrb.dc.gov/ |
| FRS plan parameters | Florida SBA | https://www.myfrs.com/ |
| MD-SRPS plan parameters | Maryland SRPS | https://sra.maryland.gov/ |
| NYSLRS plan parameters | NYS Comptroller | https://www.osc.ny.gov/retirement |
| NYSTRS plan parameters | NYSTRS | https://www.nystrs.org/ |
| OPERS plan parameters | OPERS | https://www.opers.org/ |
| STRS Ohio plan parameters | STRS Ohio | https://www.strsoh.org/ |
| TX ERS plan parameters | Texas ERS | https://www.ers.texas.gov/ |
| TX TRS plan parameters | Texas TRS | https://www.trs.texas.gov/ |
| Military basic pay tables | DFAS / navycs.com | https://militarypay.defense.gov/Pay/Basic-Pay/ |
| Military retirement rules | Defense.gov / USC | https://militarypay.defense.gov/Pay/Retirement/ |

---

## Schema Versioning

The manifest includes two version fields for safe consumption:

- **`schema_version`** — current structure version (currently `2.2`). Bumped when keys are added, renamed, removed, or paths change.
- **`schema_min_compatible`** — oldest consumer version that can safely read this data (currently `2.2`).

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
- [ ] SS earnings test thresholds (`social_security.earnings_test`)
- [ ] SS taxable wage base (`social_security.taxable_wage_base_YEAR`)
- [ ] SS quarter of coverage (`social_security.quarter_of_coverage_YEAR`)
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
- [ ] TRICARE pharmacy copays (January effective)
- [ ] TRICARE dental premiums (March effective)
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

### Cross-file consistency (January)
- [ ] `social-security-claiming.json` earnings test thresholds match `rates-annual.json`
- [ ] `fers-srs-rules.json` exempt amount matches SS under-FRA threshold
- [ ] `ss-bend-points.json` current_year matches `rates-annual.json` bend_points
- [ ] `ss-taxable-max.json` current_year matches `rates-annual.json` taxable_wage_base

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
