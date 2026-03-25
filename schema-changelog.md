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
const appSchemaVersion = "2.2"; // hardcoded in consumer app — update after migration
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


### Session 68 — Data Vintage File & Validator

**Date:** 2026-03-25

Added `data_vintage.json` — a standalone reference file that labels what fiscal/tax/plan/calendar year each dataset reflects. Covers all 82 manifest entries with `reflects` (e.g., "TY2026", "FY2026", "PY2026") and `rates_effective` or `last_entry_year` per entry. Top-level `bundle_version` (integer, for snapshot migration logic) and `vintage_schema_version` (string, for evolving the vintage block structure).

**New file:** `data_vintage.json` at repo root, peer to `manifest.json`.

**New validator:** `tests/validate_vintage.py` (530 checks) — ensures every manifest key has a corresponding vintage entry and vice versa, validates entry structure (`reflects` format, date formats, required fields), and guards against consumer-specific references.

**CI workflow:** Added `validate_vintage.py` step. Suite count 36→37. Total: ~15,980 checks.

**No schema changes. Non-breaking addition.**

### Session 68 — FRS Florida Depth Update (v2026.1 → v2026.2)

**Date:** 2026-03-25

FRS employer contribution rates, EOC multiplier correction, early retirement detail, and compensation caps. Resolves 3 of 5 original `researchGaps` items (employer rates, EOC multiplier detail, early retirement reduction tables).

**Changed file:** `states/florida/frs-plans.json` (v2026.1 → v2026.2)

**New data:**
- FY2025-26 employer contribution rates for all 10 membership classes, with rate component breakdown (HIS, admin assessment, UAL by class). Source: `frs.fl.gov/forms/2025-26_contributions_total.pdf`.
- FY2024-25 employer rates (prior year baseline). Source: `frs.fl.gov/forms/2024-25_contributions_total.pdf`.
- Compensation caps: $524,520 (pre-July 1996 enrollees) / $350,000 (post-July 1996). Source: IR 25-239.
- Investment Plan member account allocation rates by class for FY2025-26.
- Membership counts by class from 2024 actuarial data (Regular 560K, Special Risk 78K, SR Admin 102).
- DROP employer contribution rate (22.02% FY2025-26).

**Corrections:**
- EOC multiplier: was "3.0% to 3.4%". Now correctly structured as subclasses — judges 3⅓% (0.03333), all other EOC 3.0%. Per §121.091(1)(a)4, Florida Statutes.

**Enhanced:**
- Early retirement: was generic "5% per year". Now includes class-specific benchmark ages: Regular/SMSC/EOC from age 65, Special Risk from age 60 (or 57 with 30+ years SR service). Per §121.091(3)(a).

**Validator:** `validate_state_pensions.py` FRS checks expanded 142 → 171 (29 new checks covering employer rates, UAL components, comp caps, EOC subclasses, benchmark ages).

**Manifest:** `data_vintage.json` added to manifest (82 → 83 entries). FRS entry updated to v2026.2.

**No schema changes. Non-breaking addition.**

### Session 67 — Documentation & CI Catch-up

**Date:** 2026-03-24

Documentation and CI infrastructure catch-up to close gaps accumulated during the Sessions 60–66 state pension expansion sprint.

**CI workflow:** Added 10 missing validation suites to `.github/workflows/validate.yml`. These suites existed on disk and ran locally but were never added to the CI pipeline: `validate_calpers.py` (208), `validate_calstrs.py` (98), `validate_copera.py` (128), `validate_dcrb.py` (86), `validate_md_srps.py` (110), `validate_ny_pensions.py` (92), `validate_opers.py` (231), `validate_pay_tables.py` (1,333), `validate_state_pensions.py` (142), `validate_tx_ers.py` (240). CI now runs 36 suites (was 26). Total: ~15,450 checks.

**README.md:** Full rewrite of 7 stale sections: file count (70→82), file tree (added 12 state pension files + 3 new state directories), manifest table (66→82 entries, 12 rows added), state/local pension coverage section (4 states → 9 states + DC, 24 system files), validation table (27→36 suites, check counts updated), "What This Is" bullet, Data Sources table (12 new pension system sources added). Update Schedule table updated with state pension row.

**schema-changelog.md:** Backfilled entries for Sessions 60–66 documenting all 12 new state pension files, 9 new validators, CalPERS IRC correction, and depth audit work.

**No data changes. No schema changes.**

### calpers-plans.json v2026.2

**Date:** 2026-03-24

**Session 66 — Depth & Currency Audit: CalPERS IRC 401(a)(17) correction**

Fixed `classic_irc_401a17` limit: was `$350,000` (stale 2025 value), corrected to `$360,000` per IRS Notice 2025-67 for 2026. Added 5-year IRC limit history (2021–2025).

Also in Session 66: Added 2026 COLA row to `cola-history.json` (v1.0→v1.1), extended FEDVIP and FEHB historical series, added FERS-SRS exempt amounts for 2021–2023, added 2021/2025 RMD rules history entries. See session 66 handoff for full list.

**CI:** 36/36 suites passed. `validate_historical.py` check count increased 2025→2028 (new COLA row).

**No schema changes. Non-breaking correction.**

### State Pension Expansion — Sessions 60–65

**Dates:** 2026-03-24 (pushed across Sessions 60–65)

12 new state pension system files added in a rapid expansion sprint, covering 9 states + DC. Each file includes benefit formulas, eligibility rules, COLA provisions, contribution rates, and IRC limits where applicable. Listed by session:

**Session 60 — CalSTRS, FRS, TRS-TX, STRS-Ohio (4 files, 3 validators)**

- `states/california/calstrs-plans.json` (v2026.1) — California State Teachers' Retirement System. 2 tiers (2%@60 Classic, 2%@62 PEPRA), 2% simple COLA, SBMA purchasing power protection, contribution rates. ~990K members. **Validator:** `validate_calstrs.py` (98 checks).
- `states/florida/frs-plans.json` (v2026.1) — Florida Retirement System Pension Plan. DB plan, Investment Plan, and hybrid options. ~1M active members. **Validator:** `validate_state_pensions.py` covers FRS.
- `states/texas/trs-plans.json` (v2026.1) — Teacher Retirement System of Texas. 8 tiers, non-SS-covered population. ~2M members. **Validator:** `validate_state_pensions.py` covers TRS-TX.
- `states/ohio/strs-ohio-plans.json` (v2026.1) — State Teachers Retirement System of Ohio. 4 tiers, DB + DC + Combined. ~500K members. **Validator:** `validate_state_pensions.py` covers STRS-OH.

**Session 61 — NYSLRS, NYSTRS (2 files, 1 validator)**

- `states/new-york/nyslrs-plans.json` (v2026.1) — New York State and Local Retirement System. ERS + PFRS tiers. ~1.1M members. **Validator:** `validate_ny_pensions.py` (92 checks).
- `states/new-york/nystrs-plans.json` (v2026.1) — New York State Teachers' Retirement System. 7 tiers. ~430K members. **Validator:** `validate_ny_pensions.py` covers NYSTRS.

**Session 62 — CalPERS (1 file, 1 validator)**

- `states/california/calpers-plans.json` (v2026.1) — California Public Employees' Retirement System. 5 representative formulas (Classic Misc 2%@55/60, PEPRA Misc 2%@62, Classic/PEPRA Safety), COLA/PPPA, comp caps, funding status, health benefits overview. ~2M members. Largest US public pension system. **Validator:** `validate_calpers.py` (208 checks).

**Session 63 — COPERA (1 file, 1 validator)**

- `states/colorado/copera-plans.json` (v2026.1) — Colorado Public Employees' Retirement Association. State, school, local government, judicial, and DPS divisions. COLA provisions, benefit formulas, contribution rates. **Validator:** `validate_copera.py` (128 checks).

**Session 64 — MD-SRPS (1 file, 1 validator)**

- `states/maryland/md-srps-plans.json` (v2026.1) — Maryland State Retirement and Pension System. 7 subsystems (EPS, TPS, CORS, LEOPS, MSPRS, JRS, LPP). ~400K members. **Validator:** `validate_md_srps.py` (110 checks).

**Session 64/65 — DCRB, OPERS, TX ERS (3 files, 3 validators)**

- `states/dc/dc-dcrb-plans.json` (v2026.1) — District of Columbia Retirement Board. Police & Firefighters' plan, legacy teacher plan. **Validator:** `validate_dcrb.py` (86 checks).
- `states/ohio/opers-plans.json` (v2026.1) — Ohio Public Employees Retirement System. DB, DC, and Combined plans. ~1M members. **Validator:** `validate_opers.py` (231 checks).
- `states/texas/ers-plans.json` (v2026.1) — Employees Retirement System of Texas. State employee pension. ~350K members. **Validator:** `validate_tx_ers.py` (240 checks).

**Totals:** 12 new data files, 9 new validators (1,335 new checks), manifest expanded from 70 to 82 entries.

**No schema changes. All non-breaking additions.**

### lacera-plans.json v2026.3

**Date:** 2026-03-24

**Session 59 — LACERA COLA History: 25-year December-over-December CPI record (2002–2026)**

Added `cola_history` section with year-by-year COLA data for all 25 years from 2002 through 2026. Each entry contains:

- `cpi_change_pct`: Raw December-over-December CPI-U change for the LA-Long Beach-Anaheim metro area
- `cola_rounded_pct`: CPI rounded to nearest 0.5% per CERL statute
- `plan_awards`: Applied COLA awards capped at plan maximums (3% for Plan A, 2% for Plan B)
- `accumulation_excess`: Raw CPI minus plan max — positive values add to COLA Accumulation, negative values are drawn from accumulation to fund the max COLA award
- `effective_date`, `cpi_period`, `source` for each year

Data sources by period: 2002–2019 derived from BLS CPI-U LA-LB-Anaheim December index values (1967=100 base); 2020–2021 derived from LACERA COLA Accumulation chart cross-referenced with California DIR CPI data; 2022–2026 from LACERA official COLA inserts and plan-specific pages.

Cross-validated against LACERA's published 2026 COLA Accumulation chart for 11 retirement date cohorts. Recent cohorts (2018+) match exactly; older cohorts within 0.4% tolerance (expected from 1-decimal rounding over 20+ year spans).

**CI:** Expanded `validate_lacera.py` from 775 to 1134 checks (+359). Total: ~14,100 checks across 27 suites.

**No schema changes. Non-breaking addition.**

### lacera-plans.json v2026.2

**Date:** 2026-03-24

**Session 58 — LACERA Benefit Factor Tables: Complete coverage for all 9 plans**

Added `benefit_factor_table` to all 9 LACERA plans. Each table contains per-year-of-service factors by age at retirement, derived from 10-year rows of official LACERA Plan Book percentage tables and cross-verified against multiple service-year rows.

- **General A:** 13 ages (50–62), factors 1.475–2.611%
- **General B/C/D:** 16 ages (50–65), factors 1.242–2.611% (C and D share B's formula per LACERA basic provisions)
- **General E:** 11 ages (55–65), factors 0.75–2.0% (noncontributory, lower factors; max benefit 80% FAC)
- **General G:** Already present from v2026.1 — 16 ages (52–67), clean 0.1% increments (PEPRA)
- **Safety A/B:** 15 ages (41–55), factors 1.2515–2.62% (A and B share same benefit formula; differ only in COLA cap)
- **Safety C:** 8 ages (50–57), factors 2.0–2.7%, clean 0.1% increments (PEPRA)

Cross-plan CERL curve consistency verified: Plan B ages 58–65 exactly match Plan A ages 55–62 (3-year offset). Safety factors confirmed higher than general factors at all overlapping ages.

Added `service_accrual` structured object to Plan E documenting the half-rate accrual after 35 years of service (reduced_rate_multiplier: 0.5) and 80% FAC cap. Verified against official table: 36yr@65 = 71.00%, 45yr@65 = 80.00% (cap).

**CI:** Expanded `validate_lacera.py` from 532 to 775 checks (+243). Total: ~13,700 checks across 27 suites.

**No schema changes. Non-breaking addition.**

### lacera-plans.json v2026.1

**Date:** 2026-03-23

**Session 57 — LACERA (Los Angeles County) Pension Plans: 9-plan build**

New file. Complete LACERA retirement plan data covering all 9 plans: General A, B, C, D, E, G and Safety A, B, C. LACERA is the largest county retirement system in the United States (~185K members, $79.2B in assets). Covers both legacy plans (pre-1979), mid-era plans (1979–2012 including the Plan D/E contributory choice), and PEPRA plans (2013+). Includes benefit formulas with age factor tables, final average compensation rules, retirement eligibility, COLA provisions (with accumulation banking and STAR COLA), 2026 COLA awards (board-approved February 4, 2026), reciprocity agreements, healthcare tiers, IRC limits, and Plan G verified benefit factor table (16 age entries, cross-checked against official LACERA percentage tables).

**CI:** Added `validate_lacera.py` (532 checks). Total: ~13,460 checks across 27 suites.

**No schema changes. Non-breaking addition.**

### foreign-service-pay-tables.json v2026.1

**Date:** 2026-03-24

**Session 56 — Foreign Service Pay Tables: 11-year historical build (2016–2026)**

New file. Complete Foreign Service base pay schedule covering all 9 grades (FP-1 through FP-9), all 14 steps, for 11 years (2016–2026). Includes Senior Foreign Service pay ranges, Executive Schedule caps, GS-15/Step-10 base pay cap history, GS equivalency mapping, and annual base raise history. Computed from official 2017 State Department PDF (anchor year) and verified against 2024 Plumbook values (exact match within $2 rounding). 2026 values verified against Path to Foreign Service 2026 salary guide (FP-5/Step-7 = $65,058 ± $1). Companion to `reference/foreign-service-retirement-rules.json` — provides the salary input data needed for High-3 average computation in FSRDS/FSPS retirement formulas.

**CI:** Added `validate_fs_pay.py` (1,893 checks). Total: ~12,924 checks across 26 suites.

**No schema changes. Non-breaking addition.**

### state-benefits.json v2.10

**Date:** 2026-03-23

**Session 56 Legislation Watch Refresh — all 8 tracked bills checked:**

Routine monitoring update. No bills advanced since Session 40. All `last_checked` dates refreshed to 2026-03-23.

**Updates:**
- MD HB 761 (Keep Our Heroes Home Act): **NEW bill added** to watch list. Would increase military retirement subtraction to $25K for 2026, $40K for 2027+, for all ages. Companion to recurring legislation (HB 554/2023, HB 952/2024). In House Ways and Means, no committee vote.
- MD HB 857: Session context added — sine die April 13, state facing $1.4B structural deficit (primary obstacle to revenue-reducing bills). Hearing held 2/19 with MACo opposition; no committee vote.
- MD HB 857 description corrected: bill applies to under-55 only (was incorrectly noted as "all ages" in inline reference).
- MN HF194: No change. Still in House Taxes with 12 authors. No hearing scheduled.
- MA S.2046: No change. Still in Senate Ways and Means since 12/22/2025.
- NC S660/H39/H728: No movement. All in initial committees.
- NE LB272/LB425: No movement. Session runs through April 17; neither designated priority.

**No schema changes. Non-breaking patch.**

### pay-tables.json v2.0

**Date:** 2026-03-23

**Session 55 — Pay Tables Bundle: GS Historical Walkback + VA Compensation History**

**Non-breaking structural change:** `pay-tables.json` restructured from single-year to multi-year format (matching `military-pay-tables.json` pattern). All 11 years (2016–2026) of GS base pay tables sourced from official OPM Salary Table PDFs. 15 grades × 10 steps × 11 years = 1,650 data points.

**Critical data fix:** The previous 2026 GS base pay values were incorrect (e.g., GS-1/Step 1 showed $22,026 instead of the official $22,584). All values now match OPM's published Salary Table 2026-GS exactly.

**VA compensation history:** `compensation.json` v2026.2 adds `rate_history` section with 11 years (2016–2026) of base rates for all 10 disability ratings. Values derived from 2026 official rates using published VA COLA percentages, verified against VA.gov past rates.

**New validation:** `validate_pay_tables.py` — 1,333 checks covering GS structure, OPM spot-check values, cross-year consistency, raise percentage verification, locality area integrity, cross-file consistency with `federal-pay-raises.json`, VA rate history structure, year-over-year increases, and VA.gov spot-check verification.

**Files changed:**
- `federal/pay-tables.json` — v2026 → v2.0 (restructured + corrected + 10 years added)
- `federal/veterans-affairs/compensation.json` — v2026.1 → v2026.2 (rate_history added)
- `tests/validate_pay_tables.py` — NEW (1,333 checks)

### state-benefits.json v2.9

**Date:** 2026-03-15

**Session 40 Legislation Watch Refresh — all 8 tracked bills checked:**

Routine monitoring update. No bills advanced since Session 39. All `last_checked` dates refreshed to 2026-03-15.

**Updates:**
- MN HF194: Author Rasmusson added 2/26/2026 (now 12 authors). Bipartisan support continues to grow but no hearing scheduled.
- MD HB 857: MACo (Maryland Association of Counties) submitted opposing testimony at 2/19 hearing, citing local revenue impact. No committee vote reported.
- MA S.2046: Still in Senate Ways and Means. No change since 12/22/2025 committee referral.
- NC S660/H39/H728: No movement. All in Rules committees.
- NE LB272/LB425: Carryover bills. 60-day session (Jan 7 – Apr 17, 2026) focused on $471M budget deficit. Neither designated priority.

**Also completed:** March 2026 source link audit — inventoried 297 unique URLs across 49 JSON files. SSA, IRS, CMS URLs confirmed live. Full programmatic audit of government domains blocked by sandbox egress restrictions; recommend spot-checking remaining URLs in September audit window.

**No schema changes. Non-breaking patch.**

### state-benefits.json v2.8

**Date:** 2026-03-14

**Session 39 Social Security Taxation Audit — 3 critical fixes, 2 string-to-boolean fixes, 4 enrichments:**

Cross-referenced all 56 jurisdictions against the confirmed 2026 list of 8 states that tax Social Security (CO, CT, MN, MT, NM, RI, UT, VT). Found 3 states with wrong exemption status.

**Critical Fixes:**
- KS: `exempt` changed from `false` to `true`. Kansas fully exempted Social Security starting 2024 tax year. **Impact:** A KS retiree receiving $25K/year SS would have incorrectly calculated ~$1,000+ in phantom state tax.
- MT: `exempt` changed from `true` to `false`. Montana still taxes Social Security. Added `partial_exemption: true` with $5,500 subtraction for 65+. **Impact:** A MT retiree could have assumed $0 state tax on SS when they may owe.
- NM: `exempt` changed from `true` to `false`. New Mexico taxes SS for higher-income filers (above $100K single / $150K joint). Added AGI thresholds. **Impact:** Higher-income NM retirees could have assumed $0 SS tax.

**String-to-Boolean Fixes:**
- RI: `exempt` changed from string `"partial"` to boolean `false` + `partial_exemption: true`
- VT: `exempt` changed from string `"partial"` to boolean `false` + `partial_exemption: true` with AGI thresholds ($55K single / $70K joint for full exemption)

**Enrichments:**
- CO: Added `partial_exemption: true` + age-based tiers ($15K/$20K/$24K)
- CT: Added `partial_exemption: true` + AGI thresholds ($75K single / $100K joint, max 25% taxed)
- UT: Added credit mechanism + AGI thresholds ($45K single / $75K joint)
- MN: Added `partial_exemption: true` with subtraction details

**CI:** Added `test_ss_taxation_audit` (99 new checks: 8 taxing-state validations, 32 must-exempt guard rails, 59 boolean-type checks). Total: 5,979 checks across 15 suites.

### state-benefits.json v2.7

**Date:** 2026-03-14

**Session 39 Partial Exemption Audit — 6 states corrected, 1 expansion added:**

Schema consistency fix: Several states had notes describing partial military retirement exemptions but were missing the `partial_exemption: true` flag. A consumer querying `partial_exemption` would have missed these states entirely.

- CO: Added `partial_exemption: true` + `age_based_tiers` ($15K under-55 / $20K 55-64 / $24K 65+)
- DE: Added `partial_exemption: true` + `max_exclusion: 12500`
- ID: Added `partial_exemption: true` + `conditional_exemption` (disabled OR age 62+ OR earned income sufficient for federal filing; capped at max SS benefit)
- MT: Added `partial_exemption: true` (50% deduction for 5 years for working residents; $5,500 subtraction for 65+)
- NM: Added `partial_exemption: true` + `max_exclusion: 40000` (increased from $30K in 2024)
- VT: **Fixed** `exempt` from string `"partial"` to boolean `false`; added `partial_exemption: true` + `agi_threshold` ($125K full / $125-175K phased / $175K+ none)

Data enrichment:
- IN: Added `includes_usphs_noaa: true` and `sunset_date: 2028-07-01` (April 2025 expansion to Space Force, USPHS, NOAA Corps retirees and survivors)

**CI:** Added `test_partial_exemption_audit` (33 new checks). Fixed 2 tier3d checks that expected VT's old `exempt: "partial"` string. Total: 5,880 checks across 15 suites.

### state-benefits.json v2.6

**Date:** 2026-03-14

**Session 39 Legislation Watch — All pending bills checked and updated:**
- MN HF194: Still in House Taxes Committee. Now has 11 authors (Gottfried added 3/12/2026). Bipartisan support but no floor vote.
- MA S.2046: **ADVANCED** — Reported favorably by Revenue Committee, referred to Senate Ways and Means (12/22/2025). Most active bill in our watch list.
- MD HB 857: **NEW** — Introduced 2/4/2026 with 25 co-sponsors. Would increase under-55 military retirement subtraction from $12,500 to $20,000. Hearing held 2/19/2026.
- NC S660/H39/H728: All in initial committee referrals. No movement since 2025.
- NE LB272/LB425: Carryover bills. 2026 short session (60 days) dominated by $471M budget deficit. Speaker prioritizing 2026 bills; neither designated as priority.

**CI:** Added 12 legislation watch checks + 3 tier2 consistency checks. Total validate.py: 987 → 1,019.

### medicare-rates.json v2026.2

**Date:** 2026-03-14

**Version field fix:** File version field was `2026.1` but content matched `2026.2` (26-year premium history merged in Session 21). Corrected version field to `2026.2` to match manifest entry. No data change.

### state-benefits.json v2.5

**Date:** 2026-03-14

**Phase 2 Audit — 10 stale tax rates updated to 2026:**
- GA: 5.49% → 5.09% (phase-down continues)
- IN: 3.05% → 2.95% (HB1001)
- KY: 4.0% → 3.5% (revenue-trigger phasedown)
- MS: 5.0% → 4.0% (path to 3.0% by 2030)
- MT: 5.9% → 5.65% (HB337)
- NE: 5.2% → 4.55% (path to 3.99% by 2027)
- OH: 3.57% → 2.75% flat (HB96, bracket consolidation)
- OK: 4.75% → 4.5% (HB2764, 6→3 brackets)
- SC: 6.4% → 6.0% (FY2026 budget)
- IA: 3.8% → 3.9% (completed flat transition)

**Exemption classification corrections:**
- GA: Changed `exempt: true` to `exempt: false, partial_exemption: true` — $65K cap means partial, not full
- UT: Changed to credit mechanism model — nonrefundable 4.5% credit (equals tax rate), effectively full but technically a credit

**CI:** Added 10 rate spot-checks and UT credit mechanism validation.

### state-benefits.json v2.4

**Date:** 2026-03-14

**Critical Correction — Virginia military retirement:**
- **Fixed:** `income_tax.military_retirement.exempt` changed from `true` to `false`. Virginia offers a **$40,000 subtraction** (partial exemption), NOT a full exemption. Phase-in: $10K (2022), $20K (2023), $30K (2024), $40K (2025+). No age requirement (removed 2023). TSP distributions do NOT qualify. SBP payments eligible. Surviving spouses NOT eligible. HB 2700 (full exemption for 2026+) did not pass; continued to 2027.
- **Impact:** A military retiree in VA with $60K/year retirement would have incorrectly shown $0 state tax instead of ~$1,150 (5.75% × $20K over the subtraction cap).

**Critical Correction — Maryland military retirement:**
- **Fixed:** `income_tax.military_retirement.exempt` changed from `true` to `false`. Maryland offers a **partial exemption**: $12,500 under age 55, $20,000 at age 55+. The original data was incorrect.
- Added pending legislation: HB 761 ($25K for 2026, $40K thereafter) and HB 857 ($20K all ages).

**Oregon note added:**
- Filled in empty note: military retirement taxable for service after Oct 1, 1991; pre-1991 service may qualify for deduction.

**CI:** Added 10 new guard rail checks for VA and MD partial exemption values.

### state-benefits.json v2.3

**Date:** 2026-03-14

**Critical Correction — North Carolina military retirement:**
- **Fixed:** `income_tax.military_retirement.exempt` changed from `false` to `true`. Military retirement pay has been fully exempt in NC since January 1, 2021 (Session Law 2021-180). The original data entry was incorrect.
- **Fixed:** `income_tax.top_rate` updated from `0.0475` to `0.0399` (Session Law 2023-134, effective 2026 tax year). Rate schedule: 4.75% (2023), 4.50% (2024), 4.25% (2025), 3.99% (2026+).
- Added SBP exemption status, TSP non-exemption, deduction line reference, and Bailey Decision note.
- Updated pending legislation status for S 660 / H 39 / H 728.

**Data Update — Georgia military retirement:**
- Updated exemption structure from age-based tiers to flat $65,000 for all ages (HB 266, signed May 13, 2025, effective 2026 tax year).
- Preserved prior tiers in `prior_tiers` for historical reference and prior-year filing.
- Added SBP coverage clarification (not covered by military-specific exemption).

**CI:** Added 23 new checks including NC/GA value assertions and multi-state military exemption guard rails.

## Data Addition: FERS Eligibility Rules and Service Credit Rules (v1.0)

**Date:** 2026-03-23
**Schema version:** 2.2 (unchanged — non-breaking addition)
**Manifest entries:** +2 new (66 → 68 total)

Added two new federal retirement data files closing key computational gaps:

1. **`federal/fers-eligibility-rules.json`** (v1.0) — Complete FERS retirement eligibility: MRA schedule by birth year (13 bands, ages 55-57, per 5 U.S.C. § 8412(h)), all four immediate retirement pathways (MRA+30, age 60+20, age 62+5, MRA+10 with reduction formula), special category retirement (LEO/FF/ATC mandatory retirement at 57), VERA/VSIP early retirement provisions (including $25K VSIP cap and repayment rules), deferred and disability retirement eligibility, and FEHB 5-year continuation rule. 206-check validation suite (shared with service credit file).

2. **`federal/fers-service-credit-rules.json`** (v1.0) — Comprehensive service credit rules: civilian deposit (FERS 1.3% rate, CSRS 7% rate, pre/post-October 1982 distinction), redeposit (FERS/CSRS, actuarial reduction provisions), military service credit buyback (3% FERS / 7% CSRS, military retirement pay waiver interaction, combat-disabled exception), sick leave conversion (OPM 2087-hour formula, 18-point reference table with OPM-verified examples, FERS phase-in from 50% to 100%), and 42 years of Treasury variable interest rate history (1985-2026, sourced from BAL letters).

---

## Data Addition: Foreign Service Retirement Rules (v1.0)

**Date:** 2026-03-23
**Schema version:** 2.2 (unchanged — non-breaking addition)
**Manifest entries:** +2 new, 1 version bump (64 → 66 total)

Added two new reference files and updated one existing file:

1. **`reference/foreign-service-retirement-rules.json`** (v1.0) — Complete coverage of all three Foreign Service retirement systems (FSRDS, FSRDS Offset, FSPS) with benefit formulas, eligibility requirements, COLA rules (including the critical FSPS COLAs-at-any-age difference from FERS), survivor benefits, annuity supplement provisions, transfer rules, DSS special agent provisions, virtual locality pay rules, and a detailed FERS comparison section. Population: ~31,670 (active + annuitants). 94-check validation suite.

2. **`reference/federal-retirement-systems-index.json`** (v1.0) — Master catalog of ALL known federal and uniformed services retirement systems. Covers FERS, CSRS, CSRS Offset, FSRDS/FSPS, TVARS, Federal Reserve System, 6 judicial retirement plans, all 8 uniformed services (with shutdown funding vulnerability notes for USPHS/NOAA), complete 6(c) special category position classification by agency (including DHS/DLA), and defined contribution plans (TSP, Fed Thrift Plan, TVA 401(k)). 116-check validation suite.

3. **`reference/military-retirement-rules.json`** (v2.0 → v2.1) — Added explicit USPHS and NOAA Commissioned Corps coverage notes, funding source distinction (Military Retirement Fund vs. agency appropriations), BRS applicability to all uniformed services, and additional statutory authorities.

---

## Data Addition: FCPP Plans (City of Falls Church Pension Plans)

**Date:** 2026-03-14
**File:** `states/virginia/falls-church/fcpp-plans.json`
**Manifest key:** `fcpp_plans_falls_church`
**Version:** 2026.1

- 2 defined benefit plans: Basic (general employees) and Police (sworn officers)
- Basic: 1.8% multiplier, 5-year AFC, 5% EE contribution, Rule of 90 early retirement with $200/mo supplement
- Police: 2.8%/3.0% split multiplier (first 20 years / excess), 7% EE contribution, 2 tiers by hire date (Dec 8, 1986)
- Constitutional officers use VRS, not city pension
- CI: 31 new FCPP-specific checks added

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

## Data Update: ACERS Post-2025 Tier Verified (v2026.2)

- **Date:** March 14, 2026 (Session 37)
- **File:** `states/virginia/arlington-county/acers-plans.json` (UPDATED)
- **Manifest ID:** `acers_plans_arlington`
- **Version:** 2026.2 (was 2026.1)
- **Schema version unchanged** (2.2)

Verified Ord. No. 24-13 (October 19, 2024) post-2025 tier for General Members. Key findings: 1.0% DB multiplier (down from 1.5%) for non-bargaining-unit general members hired on/after Jan 12, 2025, offset by 7.5% county 401(a) DC contribution (up from 4.2%). Collective bargaining unit members retain the pre-2025 1.5% formula options. DROP extended to 4 years per Ord. No. 23-10 (July 2023). MAP opt-in provision documented.

## Data Update: VRS Plans Consolidated (Virginia Retirement System v2026.2)

- **Date:** March 14, 2026 (Session 37)
- **File:** `states/virginia/vrs-plans.json` (UPDATED)
- **Manifest ID:** `vrs_plans`
- **Version:** 2026.2 (was 2.0.0)
- **Schema version unchanged** (2.2)

Major consolidation of VRS reference data. Previous file had skeleton data with incomplete Plan 2/Hybrid parameters. Now includes: comprehensive COLA formulas (Plan 1 max 5%, Plan 2/Hybrid max 3% with CPI-U calculation details), full eligibility rules for all 3 plans, Hybrid DC contribution structure (mandatory 1% + voluntary 4% with employer match up to 2.5%, DC vesting schedule), PLOP details, hazardous duty section covering SPORS (1.85%), VaLORS (2.0%/1.7%), and political subdivision enhanced benefits (1.7%/1.85%), hazardous duty supplement ($17,856/yr as of Jul 2025), health insurance credit ($4.25/yr state, $1.50/yr political subdivision), portability agreements, and group life insurance.

## Data Addition: MCERP Plans (Montgomery County MD Employee Retirement Plans)

- **Date:** March 14, 2026 (Session 37)
- **File:** `states/maryland/montgomery-county/mcerp-plans.json` (NEW)
- **Manifest ID:** `mcerp_plans_montgomery`
- **Version:** 2026.1
- **Schema version unchanged** (2.2) — file addition is non-breaking

Adds Montgomery County MD Employee Retirement Plans data — the first Maryland pension system modeled. $7.3B system with 9,500 active employees and 6,500 retirees. 8 plan types: ERS Optional Non-Integrated (2% × AFE × years, 12-mo AFE), ERS Optional Integrated (SS-integrated with 1.25%/2% split after SS age), ERS Mandatory Integrated (36-mo AFE), ERS Public Safety (Groups E/F/G, OPEN), GRIP cash balance (FY2009), RSP 401(a) DC, Elected Officials Plan, and 457 DCP. ERS closed to non-public-safety hired after Oct 1, 1994. Key features: Rule of 85 unreduced retirement, complex COLA with pre/post July 2011 split (100% CPI vs 2.5% cap), SS-integrated benefit reduction after SS age.

## Data Addition: RRS Plans (Richmond Retirement System)

- **Date:** March 14, 2026 (Session 37)
- **File:** `states/virginia/richmond/rrs-plans.json` (NEW)
- **Manifest ID:** `rrs_plans_richmond`
- **Version:** 2026.1
- **Schema version unchanged** (2.2) — file addition is non-breaking

Adds Richmond Retirement System pension data with 8 plan types: General DB Basic (1.75%), General DB Enhanced (2.0%), Sworn P&F Basic (1.65% + 0.75% pre-65 supplement), Sworn P&F Enhanced (same formula, 20-year unreduced), General DC 401(a) with tiered employer contributions (5-10%), Executive DB Basic, Executive DB Enhanced, and Executive 2:1 Service Credit. RRS is CLOSED to new members effective January 1, 2024 (city transitioned to VRS). System continues serving 10,000+ legacy members and retirees. Key features: ad hoc COLA only (no automatic formula), 6-year DROP for sworn, portability with VRS and 6 other VA localities.

## Data Addition: PORS Plans (Fairfax County Police Officers Retirement System)

- **Date:** March 14, 2026
- **File:** `states/virginia/fairfax-county/pors-plans.json` (NEW)
- **Manifest ID:** `pors_plans_fairfax`
- **Version:** 2026.1
- **Schema version unchanged** (2.2) — file addition is non-breaking

Adds Fairfax County Police Officers Retirement System data with 3 plan tiers (A, B, C) based on sworn-in date. PORS is independent from VRS, established 1944 (oldest Fairfax County retirement system). Covers only sworn full-time FCPD officers. Key parameters: 2.8% multiplier, 8.65% employee contribution, NO Social Security participation, 3-year DROP, automatic CPI-based COLA (max 4%).

## Data Addition: URS Plans (Fairfax County Uniformed Retirement System)

- **Date:** March 14, 2026
- **File:** `states/virginia/fairfax-county/urs-plans.json` (NEW)
- **Manifest ID:** `urs_plans_fairfax`
- **Version:** 2026.1
- **Schema version unchanged** (2.2) — file addition is non-breaking

Adds Fairfax County Uniformed Retirement System data with 4 modeled plan tiers (B, D, E, F). URS is independent from VRS, established 1974. Covers Fire/Rescue, Sheriff, Animal Control, Police Helicopter, and Public Safety Communications. Unique features: Pre-62 Supplemental Benefit (Plans B/D only), Pre-Social Security Benefit, severe service-connected disability at 90%. URS members DO participate in Social Security (unlike PORS).

## Data Addition: FCERS Plans (Fairfax County Employees' Retirement System)

**Date:** March 14, 2026 (Session 35)
**Type:** Non-breaking addition (no schema version bump)

Added `states/virginia/fairfax-county/fcers-plans.json` with full plan parameters for the Fairfax County Employees' Retirement System (FCERS/ERS). FCERS is a fully independent defined benefit pension system (NOT VRS) established 1955. Covers general county employees and certain FCPS non-teaching positions.

**New file:** `states/virginia/fairfax-county/fcers-plans.json`
**New manifest key:** `fcers_plans_fairfax`
**Plans modeled:** 5 plan tiers (A, B, C, D, E) with different hire date ranges, contribution structures, and multipliers
**CI impact:** +95 validation checks in `validate.py` Layer 5 (total: 5,261 across 15 suites)

---

## Data Addition: ACERS Plans (Arlington County)

**Date:** March 14, 2026 (Session 34)
**Change type:** New file + manifest key (non-breaking)
**`schema_version`:** 2.2 (unchanged — adding new file does not require bump)

Added `states/virginia/arlington-county/acers-plans.json` with full plan parameters for the Arlington County Employees' Retirement System (ACERS). ACERS is a fully independent defined benefit pension system (NOT VRS) with $3.28B in assets and 111% funded ratio (FY2024).

**New file:** `states/virginia/arlington-county/acers-plans.json`
**New manifest key:** `acers_plans_arlington`

**Coverage:**
- 6 plan tiers across 3 code chapters (Ch.21, Ch.35, Ch.46)
- General members: 1.5% × AFC × years (max 30), FAC = highest 36 consecutive months
- School Board (Ch.35): 0.625% × AFC × years
- Public safety: separate provisions (age 52 normal retirement, 7.5% employee contribution)
- Post-2025 tier (Ord. No. 24-13): parameters flagged for verification
- COLA, SS Leveling, DROP, lump sum, survivor options documented

**Validation:** 26 new checks added to `validate.py` Layer 5 (referential integrity).

---

## Schema Version 2.2 — County-Level Pension Jurisdictional Restructure

**Date:** March 14, 2026 (Session 33)
**Change type:** Breaking — file path and manifest key change
**`schema_version`:** 2.1 → 2.2
**`schema_min_compatible`:** 2.1 → 2.2

### Summary

Moved county-level pension data (ERFC plans and VRS+ERFC plan combinations) from the state-level `states/virginia/` directory into a county-specific subdirectory `states/virginia/fairfax-county/`. This corrects a jurisdictional hierarchy issue: ERFC is a Fairfax County retirement system, not a Virginia state system. VRS plans remain at state level.

### Breaking Change

**Removed manifest keys:**
- `erfc_plans` (url: `states/virginia/erfc-plans.json`)
- `plan_combinations` (url: `states/virginia/plan-combinations.json`)

**Added manifest keys:**
- `erfc_plans_fairfax` (url: `states/virginia/fairfax-county/erfc-plans.json`)
- `plan_combinations_fairfax` (url: `states/virginia/fairfax-county/plan-combinations.json`)

**Deleted files (old locations):**
- `states/virginia/erfc-plans.json`
- `states/virginia/plan-combinations.json`

**Unchanged:**
- `states/virginia/vrs-plans.json` — VRS is a state-level pension, correct location
- `states/virginia/county-property-tax.json` — multi-county collection, correct at state level
- `reference/other-db-template.json` — generic DB template, unchanged

### Rationale

ERFC (Employees' Retirement Fund of the City of Fairfax County) is administered by Fairfax County for county government and FCPS employees. Placing it alongside VRS (a Virginia state pension system) implied they were peer-level systems. The restructure makes the jurisdictional hierarchy explicit: state-level pension data at the state directory, county-level pension data in a county subdirectory.

This pattern supports future expansion if other county/municipal pension systems are added (e.g., NYC pension funds under `states/new-york/new-york-city/`, Chicago pension funds under `states/illinois/chicago/`).

### Consumer Migration

```javascript
// Before (Schema 2.1):
const erfc = await fetch(manifest.files.erfc_plans.url);
const combos = await fetch(manifest.files.plan_combinations.url);

// After (Schema 2.2):
const erfc = await fetch(manifest.files.erfc_plans_fairfax.url);
const combos = await fetch(manifest.files.plan_combinations_fairfax.url);
```

### Research Context: County-Level Pension Landscape

Research conducted during this session found that over 5,000 locally-administered pension plans exist in the United States. Notable examples include New York City (5 separate pension funds covering 300,000+ members), Chicago (Municipal Employees' Annuity and Benefit Fund plus police/fire/teachers funds), 20 California counties operating independent retirement systems under the 1937 County Employees Retirement Act (including LA County, San Diego, Orange County, San Francisco), and Pennsylvania with 928+ local municipal pension plans. Illinois has 365+ local plans.

For this repo's scope (federal retirement planning with state/local benefits as supplementary data), the `other-db-template.json` file handles user-entered pension parameters for any plan not explicitly modeled. The explicit ERFC modeling exists because Virginia/Fairfax County is the repo's most deeply covered jurisdiction. The directory structure now supports adding other county/municipal pension systems as needed.

---

## Schema Version 2.1 — County Data Per-State Restructure

**Date:** March 13, 2026 (Session 24)
**Change type:** Breaking — file path change
**`schema_version`:** 2.0 → 2.1
**`schema_min_compatible`:** 2.0 → 2.1

### Summary

Restructured county property tax data from a single flat file into per-state files under state-specific directories. No data values changed — structural reorganization only.

### Breaking Change

**Removed:** `states/counties/county-property-tax.json` (single file, 10 counties)
**Removed:** `states/counties/` directory

**Added:** 9 per-state county files:

| Manifest Key | Path | Counties |
|---|---|---|
| `county_property_tax_az` | `states/arizona/county-property-tax.json` | Maricopa County |
| `county_property_tax_co` | `states/colorado/county-property-tax.json` | El Paso County |
| `county_property_tax_fl` | `states/florida/county-property-tax.json` | Hillsborough County |
| `county_property_tax_md` | `states/maryland/county-property-tax.json` | Prince George's County |
| `county_property_tax_nc` | `states/north-carolina/county-property-tax.json` | Cumberland County |
| `county_property_tax_nv` | `states/nevada/county-property-tax.json` | Clark County |
| `county_property_tax_tx` | `states/texas/county-property-tax.json` | Bexar County |
| `county_property_tax_va` | `states/virginia/county-property-tax.json` | Fairfax County, Virginia Beach |
| `county_property_tax_wa` | `states/washington/county-property-tax.json` | Pierce County |

### Schema Changes

Each per-state file now includes `metadata.state_code` field identifying the state. Version bumped from `1.0` to `1.1`.

### Consumer Migration

Consumers referencing `county_property_tax` must update to state-specific keys (`county_property_tax_va`, etc.). The `counties` array schema within each file is unchanged — only the file location and manifest key changed.

```javascript
// Before (Schema 2.0):
const countyData = await fetch(manifest.files.county_property_tax.url);

// After (Schema 2.1):
// Option A: Fetch specific state
const vaCounties = await fetch(manifest.files.county_property_tax_va.url);

// Option B: Fetch all county files
const countyKeys = Object.keys(manifest.files).filter(k => k.startsWith('county_property_tax_'));
const allCounties = await Promise.all(
  countyKeys.map(k => fetch(manifest.files[k].url).then(r => r.json()))
);
```

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
