"""Validation utilities for Chart of Accounts and Business Rules seed data."""

from pathlib import Path

from ..logger import logger
from ..schemas import BusinessRule, ChartOfAccountsEntry
from ..settings import get_silver_dir


def validate_chart_of_accounts(
    accounts: list[ChartOfAccountsEntry],
) -> tuple[bool, list[str]]:
    """Validate chart of accounts for duplicates and class coverage."""
    errors = []

    account_ids = [a.account_id for a in accounts]
    duplicates = [aid for aid in account_ids if account_ids.count(aid) > 1]
    if duplicates:
        errors.append(f"Duplicate account IDs found: {set(duplicates)}")

    classes = {a.account_class for a in accounts}
    expected_classes = {"1", "2", "3", "4", "5", "6", "7", "8"}
    missing_classes = expected_classes - classes
    if missing_classes:
        errors.append(f"Missing account classes: {missing_classes}")

    return len(errors) == 0, errors


def validate_business_rules(rules: list[BusinessRule]) -> tuple[bool, list[str]]:
    """Validate business rules for duplicates, sources, and domain coverage."""
    errors = []

    rule_ids = [r.rule_id for r in rules]
    duplicates = [rid for rid in rule_ids if rule_ids.count(rid) > 1]
    if duplicates:
        errors.append(f"Duplicate rule IDs found: {set(duplicates)}")

    rules_without_sources = [r.rule_id for r in rules if not r.source_ids]
    if rules_without_sources:
        errors.append(f"Rules without source citations: {rules_without_sources[:5]}")

    domains = {r.domain for r in rules}
    expected_domains = {"tax", "accounting", "payroll"}
    missing_domains = expected_domains - domains
    if missing_domains:
        errors.append(f"Missing rule domains: {missing_domains}")

    if len(rules) < 15:
        errors.append(f"Less than 15 rules found (target: 15-30), got {len(rules)}")

    return len(errors) == 0, errors


def validate_cross_references(
    rules: list[BusinessRule], accounts: list[ChartOfAccountsEntry]
) -> tuple[bool, list[str]]:
    """Validate that rule actions reference existing accounts."""
    errors = []

    account_ids = {a.account_id for a in accounts}

    for rule in rules:
        for action in rule.actions:
            if action.type in ["set_account", "set_vat_account"]:
                account_ref = str(action.value)
                if account_ref and account_ref not in account_ids:
                    errors.append(
                        f"Rule {rule.rule_id} references non-existent account: {account_ref}"
                    )

    return len(errors) == 0, errors


def run_all_validations(silver_dir: Path | None = None) -> int:
    """Run comprehensive validation of chart of accounts and business rules."""
    if silver_dir is None:
        silver_dir = get_silver_dir()

    logger.info("=" * 70)
    logger.info("Seed Data Validation Report")
    logger.info("=" * 70)

    all_passed = True

    import json

    coa_path = silver_dir / "chart_of_accounts.json"
    rules_path = silver_dir / "business_rules.json"

    if not coa_path.exists() or not rules_path.exists():
        logger.error(
            "Seed data files not found. Run 'ingest_from_sources.py seed' first."
        )
        return 1

    with coa_path.open("r") as f:
        accounts_data = json.load(f)
    with rules_path.open("r") as f:
        rules_data = json.load(f)

    accounts = [ChartOfAccountsEntry(**a) for a in accounts_data]
    rules = [BusinessRule(**r) for r in rules_data]

    logger.info("\n1. Chart of Accounts Validation")
    logger.info("-" * 70)
    coa_passed, coa_errors = validate_chart_of_accounts(accounts)
    if coa_passed:
        logger.info(f"✓ PASSED: {len(accounts)} accounts validated")
    else:
        logger.error(f"✗ FAILED: {len(coa_errors)} validation errors")
        for error in coa_errors:
            logger.error(f"  - {error}")
        all_passed = False

    logger.info("\n2. Business Rules Validation")
    logger.info("-" * 70)
    rules_passed, rules_errors = validate_business_rules(rules)
    if rules_passed:
        logger.info(f"✓ PASSED: {len(rules)} rules validated")
    else:
        logger.error(f"✗ FAILED: {len(rules_errors)} validation errors")
        for error in rules_errors:
            logger.error(f"  - {error}")
        all_passed = False

    logger.info("\n3. Cross-Reference Validation")
    logger.info("-" * 70)
    xref_passed, xref_errors = validate_cross_references(rules, accounts)
    if xref_passed:
        logger.info("✓ PASSED: All account references are valid")
    else:
        logger.error(f"✗ FAILED: {len(xref_errors)} cross-reference errors")
        for error in xref_errors:
            logger.error(f"  - {error}")
        all_passed = False

    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ ALL VALIDATIONS PASSED")
        logger.info("=" * 70)
        logger.info("\nSeed Data:")
        logger.info(f"  • Chart of Accounts: {len(accounts)} entries")
        logger.info(f"  • Business Rules: {len(rules)} entries")
        return 0
    else:
        logger.error("✗ SOME VALIDATIONS FAILED")
        logger.error("=" * 70)
        return 1
