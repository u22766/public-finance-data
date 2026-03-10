#!/usr/bin/env python3
"""
OM-11: Expanded CI Validation for Tier 2 State Coverage
========================================================
public-finance-data / tests / validate_tier2.py

This module extends the existing validation suite (validate.py) with
comprehensive checks for all 15 states in state-benefits.json v1.5.

Run standalone: python validate_tier2.py
Or import into validate.py: from validate_tier2 import run_tier2_checks

Team Gamma — O&M Session 16 — March 2026
"""

import json
import sys
from pathlib import Path
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

# All 15 states expected in v1.5
EXPECTED_STATES = [
    # Tier 1 (original)
    "VA",
    # v1.3 expansion
    "MD", "DC", "FL", "TX",
    # v1.4 expansion
    "GA", "NC", "CO", "WA",
    # v1.5 / Tier 2 expansion
    "PA", "AK", "HI", "AZ", "NV", "OR"
]

# Valid exemption types per schema
VALID_EXEMPTION_TYPES = [
    "full",
    "partial",
    "deduction",
    "reduction",
    "discount",
    "grant",
    "credit"
]

# Valid IU eligibility values
VALID_IU_VALUES = [True, False, "verify", "not_applicable"]

# Valid income tax treatment values
VALID_TAX_TREATMENTS = [
    "exempt",
    "taxed",
    "partial",
    "deductible",
    "subtraction",
    "n/a",
    "N/A"
]

# States with no income tax
NO_INCOME_TAX_STATES = ["FL", "TX", "WA", "AK", "NV"]

# =============================================================================
# VALIDATION CHECKS
# =============================================================================

class ValidationResult:
    """Container for validation results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, check_name: str, details: str = ""):
        self.passed.append(f"✓ {check_name}" + (f": {details}" if details else ""))
    
    def add_fail(self, check_name: str, details: str):
        self.failed.append(f"✗ {check_name}: {details}")
    
    def add_warning(self, check_name: str, details: str):
        self.warnings.append(f"⚠ {check_name}: {details}")
    
    @property
    def total_checks(self) -> int:
        return len(self.passed) + len(self.failed)
    
    @property
    def all_passed(self) -> bool:
        return len(self.failed) == 0


def check_all_states_present(data: dict, results: ValidationResult) -> None:
    """T2-001: Verify all 15 expected states are present."""
    states_in_file = set()
    
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code")
        if code:
            states_in_file.add(code)
    
    missing = set(EXPECTED_STATES) - states_in_file
    extra = states_in_file - set(EXPECTED_STATES)
    
    if missing:
        results.add_fail("T2-001-states-present", f"Missing states: {sorted(missing)}")
    else:
        results.add_pass("T2-001-states-present", f"All {len(EXPECTED_STATES)} states present")
    
    if extra:
        results.add_warning("T2-001-extra-states", f"Unexpected states: {sorted(extra)}")


def check_no_duplicate_states(data: dict, results: ValidationResult) -> None:
    """T2-002: No duplicate state codes."""
    codes = [s.get("state_code") for s in data.get("states", [])]
    duplicates = [c for c in codes if codes.count(c) > 1]
    
    if duplicates:
        results.add_fail("T2-002-no-duplicates", f"Duplicate state codes: {set(duplicates)}")
    else:
        results.add_pass("T2-002-no-duplicates", f"{len(codes)} unique state codes")


def check_veteran_benefits_structure(data: dict, results: ValidationResult) -> None:
    """T2-003: Each state has veteran_benefits section with valid structure."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        vet_benefits = state_entry.get("veteran_benefits")
        
        if not vet_benefits:
            results.add_fail(f"T2-003-vet-benefits-{code}", "Missing veteran_benefits section")
            continue
        
        if not isinstance(vet_benefits, dict):
            results.add_fail(f"T2-003-vet-benefits-{code}", "veteran_benefits must be object")
            continue
        
        if len(vet_benefits) == 0:
            results.add_fail(f"T2-003-vet-benefits-{code}", "veteran_benefits is empty")
            continue
        
        results.add_pass(f"T2-003-vet-benefits-{code}", f"{len(vet_benefits)} benefit type(s)")


def check_benefit_required_fields(data: dict, results: ValidationResult) -> None:
    """T2-004: Each benefit has required fields (exemption_type, description)."""
    required_fields = ["exemption_type", "description"]
    
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        for benefit_key, benefit_data in vet_benefits.items():
            if not isinstance(benefit_data, dict):
                results.add_fail(f"T2-004-fields-{code}-{benefit_key}", "Benefit must be object")
                continue
            
            missing = [f for f in required_fields if f not in benefit_data]
            if missing:
                results.add_fail(f"T2-004-fields-{code}-{benefit_key}", f"Missing: {missing}")
            else:
                results.add_pass(f"T2-004-fields-{code}-{benefit_key}")


def check_exemption_types_valid(data: dict, results: ValidationResult) -> None:
    """T2-005: All exemption_type values are valid."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        for benefit_key, benefit_data in vet_benefits.items():
            if not isinstance(benefit_data, dict):
                continue
            
            ex_type = benefit_data.get("exemption_type", "").lower()
            if ex_type and ex_type not in VALID_EXEMPTION_TYPES:
                results.add_fail(
                    f"T2-005-exemption-type-{code}-{benefit_key}",
                    f"Invalid type '{ex_type}', expected one of {VALID_EXEMPTION_TYPES}"
                )
            elif ex_type:
                results.add_pass(f"T2-005-exemption-type-{code}-{benefit_key}")


def check_source_urls_present(data: dict, results: ValidationResult) -> None:
    """T2-006: Each benefit has non-empty source_url or source field."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        for benefit_key, benefit_data in vet_benefits.items():
            if not isinstance(benefit_data, dict):
                continue
            
            source = benefit_data.get("source_url") or benefit_data.get("source")
            if not source or (isinstance(source, str) and len(source.strip()) == 0):
                results.add_fail(f"T2-006-source-{code}-{benefit_key}", "Missing source_url/source")
            else:
                results.add_pass(f"T2-006-source-{code}-{benefit_key}")


def check_iu_eligibility_flags(data: dict, results: ValidationResult) -> None:
    """T2-007: IU eligibility is documented for each benefit."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        for benefit_key, benefit_data in vet_benefits.items():
            if not isinstance(benefit_data, dict):
                continue
            
            # Check various IU-related keys
            iu_value = benefit_data.get("iu_eligible")
            iu_note = benefit_data.get("iu_eligibility")
            eligibility = benefit_data.get("eligibility", {})
            iu_in_eligibility = eligibility.get("iu_eligible") if isinstance(eligibility, dict) else None
            
            has_iu_info = iu_value is not None or iu_note is not None or iu_in_eligibility is not None
            
            if not has_iu_info:
                results.add_warning(
                    f"T2-007-iu-{code}-{benefit_key}",
                    "No IU eligibility info (iu_eligible or iu_eligibility field)"
                )
            else:
                # Validate the value if present
                if iu_value is not None and iu_value not in VALID_IU_VALUES:
                    results.add_fail(
                        f"T2-007-iu-{code}-{benefit_key}",
                        f"Invalid iu_eligible value: {iu_value}"
                    )
                else:
                    results.add_pass(f"T2-007-iu-{code}-{benefit_key}")


def check_income_tax_structure(data: dict, results: ValidationResult) -> None:
    """T2-008: Each state has income_tax section with required fields."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        income_tax = state_entry.get("income_tax")
        
        if not income_tax:
            results.add_fail(f"T2-008-income-tax-{code}", "Missing income_tax section")
            continue
        
        if not isinstance(income_tax, dict):
            results.add_fail(f"T2-008-income-tax-{code}", "income_tax must be object")
            continue
        
        # Check has_income_tax field
        has_tax = income_tax.get("has_income_tax")
        if has_tax is None:
            results.add_fail(f"T2-008-income-tax-{code}", "Missing has_income_tax field")
            continue
        
        # Validate consistency with known no-tax states
        if code in NO_INCOME_TAX_STATES and has_tax is True:
            results.add_fail(
                f"T2-008-income-tax-{code}",
                f"{code} should have has_income_tax: false"
            )
        elif code not in NO_INCOME_TAX_STATES and has_tax is False:
            results.add_warning(
                f"T2-008-income-tax-{code}",
                f"{code} marked as no income tax but not in expected list"
            )
        else:
            results.add_pass(f"T2-008-income-tax-{code}")


def check_income_tax_retirement_treatment(data: dict, results: ValidationResult) -> None:
    """T2-009: States with income tax have military_retirement field."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        income_tax = state_entry.get("income_tax", {})
        
        if not isinstance(income_tax, dict):
            continue
        
        has_tax = income_tax.get("has_income_tax")
        
        if has_tax:
            mil_ret = income_tax.get("military_retirement")
            if not mil_ret:
                results.add_fail(
                    f"T2-009-mil-retirement-{code}",
                    "Has income tax but missing military_retirement field"
                )
            elif isinstance(mil_ret, str) and mil_ret.lower() not in VALID_TAX_TREATMENTS:
                results.add_warning(
                    f"T2-009-mil-retirement-{code}",
                    f"Unusual military_retirement value: {mil_ret}"
                )
            else:
                results.add_pass(f"T2-009-mil-retirement-{code}")
        else:
            # No income tax - should be N/A or similar
            results.add_pass(f"T2-009-mil-retirement-{code}", "No income tax")


def check_income_tax_ss_treatment(data: dict, results: ValidationResult) -> None:
    """T2-010: States with income tax have social_security field."""
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        income_tax = state_entry.get("income_tax", {})
        
        if not isinstance(income_tax, dict):
            continue
        
        has_tax = income_tax.get("has_income_tax")
        
        if has_tax:
            ss = income_tax.get("social_security")
            if not ss:
                results.add_fail(
                    f"T2-010-ss-{code}",
                    "Has income tax but missing social_security field"
                )
            else:
                results.add_pass(f"T2-010-ss-{code}")
        else:
            results.add_pass(f"T2-010-ss-{code}", "No income tax")


def check_az_iu_exclusion(data: dict, results: ValidationResult) -> None:
    """T2-011: Arizona IU exclusion is properly documented (critical edge case)."""
    for state_entry in data.get("states", []):
        if state_entry.get("state_code") != "AZ":
            continue
        
        vet_benefits = state_entry.get("veteran_benefits", {})
        full_exemption = vet_benefits.get("disabled_veteran_full_exemption", {})
        
        if not full_exemption:
            results.add_warning("T2-011-az-iu", "AZ full exemption benefit not found")
            return
        
        iu_value = full_exemption.get("iu_eligible")
        
        # Per research: AZ IU does NOT qualify for full exemption
        if iu_value is False:
            results.add_pass("T2-011-az-iu", "AZ correctly shows IU does not qualify")
        elif iu_value is True:
            results.add_fail(
                "T2-011-az-iu",
                "AZ full exemption incorrectly shows IU as eligible (should be false)"
            )
        else:
            results.add_warning(
                "T2-011-az-iu",
                f"AZ full exemption iu_eligible is {iu_value}, expected false"
            )


def check_pending_legislation_structure(data: dict, results: ValidationResult) -> None:
    """T2-012: Pending legislation fields are properly structured."""
    states_with_pending = []
    
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code", "UNKNOWN")
        pending = state_entry.get("pending_legislation")
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        # Check state-level pending legislation
        if pending:
            states_with_pending.append(code)
            if isinstance(pending, dict):
                results.add_pass(f"T2-012-pending-{code}")
            elif isinstance(pending, list):
                results.add_pass(f"T2-012-pending-{code}", "List format")
            else:
                results.add_warning(
                    f"T2-012-pending-{code}",
                    "pending_legislation should be object or list"
                )
        
        # Check benefit-level pending legislation
        for benefit_key, benefit_data in vet_benefits.items():
            if isinstance(benefit_data, dict) and benefit_data.get("pending_legislation"):
                states_with_pending.append(f"{code}.{benefit_key}")
    
    if states_with_pending:
        results.add_pass(
            "T2-012-pending-overview",
            f"Pending legislation documented: {len(states_with_pending)} entries"
        )


def check_version_field(data: dict, results: ValidationResult) -> None:
    """T2-013: File has version field and it's 1.5."""
    version = data.get("version")
    
    if not version:
        results.add_fail("T2-013-version", "Missing version field")
    elif version == "1.5":
        results.add_pass("T2-013-version", "v1.5")
    else:
        results.add_warning("T2-013-version", f"Version is {version}, expected 1.5")


# =============================================================================
# TIER 2 SPECIFIC CHECKS
# =============================================================================

def check_tier2_states_complete(data: dict, results: ValidationResult) -> None:
    """T2-100: All Tier 2 states (PA, AK, HI, AZ, NV, OR) have complete entries."""
    tier2_codes = ["PA", "AK", "HI", "AZ", "NV", "OR"]
    
    for state_entry in data.get("states", []):
        code = state_entry.get("state_code")
        if code not in tier2_codes:
            continue
        
        # Check for all required sections
        has_vet = bool(state_entry.get("veteran_benefits"))
        has_tax = bool(state_entry.get("income_tax"))
        has_name = bool(state_entry.get("state_name"))
        
        if has_vet and has_tax and has_name:
            results.add_pass(f"T2-100-complete-{code}", "All required sections present")
        else:
            missing = []
            if not has_vet:
                missing.append("veteran_benefits")
            if not has_tax:
                missing.append("income_tax")
            if not has_name:
                missing.append("state_name")
            results.add_fail(f"T2-100-complete-{code}", f"Missing: {missing}")


def check_pa_financial_need_test(data: dict, results: ValidationResult) -> None:
    """T2-101: PA financial need test is documented (unique requirement)."""
    for state_entry in data.get("states", []):
        if state_entry.get("state_code") != "PA":
            continue
        
        vet_benefits = state_entry.get("veteran_benefits", {})
        
        # Look for financial need test documentation
        found = False
        for benefit_key, benefit_data in vet_benefits.items():
            if not isinstance(benefit_data, dict):
                continue
            
            # Check for financial_need_test field or related
            if benefit_data.get("financial_need_test"):
                found = True
                break
            
            # Check in eligibility sub-object
            eligibility = benefit_data.get("eligibility", {})
            if isinstance(eligibility, dict):
                if eligibility.get("income_limit") or eligibility.get("financial_need"):
                    found = True
                    break
            
            # Check description for mention
            desc = benefit_data.get("description", "")
            if "financial need" in desc.lower() or "income" in desc.lower():
                found = True
                break
        
        if found:
            results.add_pass("T2-101-pa-need-test", "Financial need test documented")
        else:
            results.add_warning(
                "T2-101-pa-need-test",
                "PA financial need test ($114,637 threshold) should be documented"
            )


def check_or_military_retirement_partial(data: dict, results: ValidationResult) -> None:
    """T2-102: OR military retirement shows partial exemption (pre-Oct 1991 only)."""
    for state_entry in data.get("states", []):
        if state_entry.get("state_code") != "OR":
            continue
        
        income_tax = state_entry.get("income_tax", {})
        mil_ret = income_tax.get("military_retirement", "")
        
        # Should indicate partial/conditional, not full exempt
        if isinstance(mil_ret, str):
            mil_ret_lower = mil_ret.lower()
            if "partial" in mil_ret_lower or "pre-" in mil_ret_lower or "1991" in mil_ret:
                results.add_pass("T2-102-or-mil-ret", "Correctly shows partial/conditional")
            elif mil_ret_lower == "exempt":
                results.add_fail(
                    "T2-102-or-mil-ret",
                    "OR should show partial exemption (pre-Oct 1991 only), not full exempt"
                )
            else:
                results.add_pass("T2-102-or-mil-ret", f"Value: {mil_ret}")
        else:
            results.add_warning("T2-102-or-mil-ret", "military_retirement should be string")


# =============================================================================
# RUNNER
# =============================================================================

def run_tier2_checks(data: dict) -> ValidationResult:
    """Run all Tier 2 validation checks."""
    results = ValidationResult()
    
    # Core structure checks
    check_all_states_present(data, results)
    check_no_duplicate_states(data, results)
    check_version_field(data, results)
    
    # Veteran benefits checks
    check_veteran_benefits_structure(data, results)
    check_benefit_required_fields(data, results)
    check_exemption_types_valid(data, results)
    check_source_urls_present(data, results)
    check_iu_eligibility_flags(data, results)
    
    # Income tax checks
    check_income_tax_structure(data, results)
    check_income_tax_retirement_treatment(data, results)
    check_income_tax_ss_treatment(data, results)
    
    # Edge case checks
    check_az_iu_exclusion(data, results)
    check_pending_legislation_structure(data, results)
    
    # Tier 2 specific checks
    check_tier2_states_complete(data, results)
    check_pa_financial_need_test(data, results)
    check_or_military_retirement_partial(data, results)
    
    return results


def main():
    """Standalone runner for Tier 2 validation."""
    # Default path - adjust as needed
    state_benefits_path = Path("states/state-benefits.json")
    
    if len(sys.argv) > 1:
        state_benefits_path = Path(sys.argv[1])
    
    if not state_benefits_path.exists():
        print(f"ERROR: File not found: {state_benefits_path}")
        print("Usage: python validate_tier2.py [path/to/state-benefits.json]")
        sys.exit(1)
    
    print(f"OM-11: Tier 2 Validation Suite")
    print(f"=" * 50)
    print(f"File: {state_benefits_path}")
    print()
    
    with open(state_benefits_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = run_tier2_checks(data)
    
    # Print results
    print(f"PASSED ({len(results.passed)}):")
    for p in results.passed:
        print(f"  {p}")
    
    if results.warnings:
        print(f"\nWARNINGS ({len(results.warnings)}):")
        for w in results.warnings:
            print(f"  {w}")
    
    if results.failed:
        print(f"\nFAILED ({len(results.failed)}):")
        for f in results.failed:
            print(f"  {f}")
    
    print()
    print(f"=" * 50)
    print(f"Total checks: {results.total_checks}")
    print(f"Passed: {len(results.passed)}")
    print(f"Failed: {len(results.failed)}")
    print(f"Warnings: {len(results.warnings)}")
    
    if results.all_passed:
        print("\n✓ ALL TIER 2 CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n✗ VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
