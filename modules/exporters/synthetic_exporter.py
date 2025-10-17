"""
Synthetic conversation exporter for Gold layer training data.

Generates multi-turn conversations using templates and business rules.
"""

import random
from pathlib import Path
from typing import Any

from modules.exporters.base_exporter import BaseExporter
from modules.gold_templates import (
    ALL_TEMPLATES,
    CATEGORY_VARIATIONS,
    CONTEXT_VARIATIONS,
)
from modules.logger import get_logger

logger = get_logger(__name__)


class SyntheticExporter(BaseExporter):
    """Exporter for synthetic conversation training samples."""

    def __init__(
        self,
        output_dir: Path,
        split_ratio: float = 0.8,
        conversations_per_template: int = 250,
    ):
        super().__init__(output_dir, split_ratio)
        self.domain = "accounting"
        self.conversations_per_template = conversations_per_template

    def extract_family_key(self, item: dict[str, Any]) -> str:
        """Extract family key from conversation_type for train/val splitting."""
        return item.get("metadata", {}).get("conversation_type", "unknown")

    def calculate_vat(
        self, amount_incl_vat: float, vat_rate: float
    ) -> tuple[float, float]:
        """Calculate VAT breakdown from amount including VAT."""
        amount_ex_vat = amount_incl_vat / (1 + vat_rate / 100)
        vat_amount = amount_incl_vat - amount_ex_vat
        return round(amount_ex_vat, 2), round(vat_amount, 2)

    def get_rule_data(self, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract random rule data for placeholder values."""
        if not rules:
            return {}

        rule = random.choice(rules)

        account_action = next(
            (a for a in rule["actions"] if a["type"] == "set_account"), None
        )
        vat_rate_action = next(
            (a for a in rule["actions"] if a["type"] == "set_vat_rate"), None
        )
        vat_code_action = next(
            (a for a in rule["actions"] if a["type"] == "set_vat_code"), None
        )

        if not (account_action and vat_rate_action and vat_code_action):
            return {}

        return {
            "rule_id": rule["rule_id"],
            "rule_name": rule["rule_name"],
            "account": account_action["value"],
            "vat_rate": vat_rate_action["value"],
            "vat_code": vat_code_action["value"],
            "explanation": rule.get("description", ""),
            "citations": rule.get("citations", []),
        }

    def get_category_info(self, rule_id: str) -> tuple[str, str]:
        """Get category and label from rule ID."""
        if "hotel" in rule_id.lower():
            cat = random.choice(CATEGORY_VARIATIONS["hotel"])
            return cat, "hotellovernatting"
        elif "food" in rule_id.lower() or "meal" in rule_id.lower():
            cat = random.choice(CATEGORY_VARIATIONS["food"])
            return cat, "måltid"
        elif "office" in rule_id.lower():
            cat = random.choice(CATEGORY_VARIATIONS["office"])
            return cat, "kontorrekvisita"
        elif "transport" in rule_id.lower():
            cat = random.choice(CATEGORY_VARIATIONS["transport"])
            return cat, "transport"
        elif "equipment" in rule_id.lower():
            cat = random.choice(CATEGORY_VARIATIONS["equipment"])
            return cat, "utstyr"
        else:
            return "kostnad", "diverse kostnad"

    def fill_template(
        self, template: dict[str, Any], rules: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Fill a template with actual values from business rules."""
        template_id = template["template_id"]

        # Get rule data (either 1 or 2 rules for multi-item)
        if template_id == "multi_item":
            if len(rules) < 2:
                return None
            rule1_data = self.get_rule_data(rules[: len(rules) // 2])
            rule2_data = self.get_rule_data(rules[len(rules) // 2 :])
            if not rule1_data or not rule2_data:
                return None
        else:
            rule1_data = self.get_rule_data(rules)
            if not rule1_data:
                return None

        # Generate amounts
        amounts = [500, 750, 1000, 1200, 1500, 1800, 2000, 2500, 3000]
        amount = random.choice(amounts)

        # Calculate VAT
        amount_ex_vat, vat_amount = self.calculate_vat(amount, rule1_data["vat_rate"])

        # Get category variations
        category, category_label = self.get_category_info(rule1_data["rule_id"])

        # Build placeholder values
        values = {
            "category": category,
            "category_label": category_label,
            "amount": amount,
            "amount_ex_vat": amount_ex_vat,
            "vat_amount": vat_amount,
            "account": rule1_data["account"],
            "account_label": rule1_data["rule_name"],
            "vat_code": rule1_data["vat_code"],
            "vat_rate": rule1_data["vat_rate"],
            "explanation": rule1_data["explanation"],
            "context": random.choice(CONTEXT_VARIATIONS),
            "example_amount": 1000,
            "example_ex_vat": round(1000 / (1 + rule1_data["vat_rate"] / 100), 2),
            "example_vat": round(1000 - 1000 / (1 + rule1_data["vat_rate"] / 100), 2),
            "examples": "diverse forretningskostnader",
            "wrong_account": "6300",
            "correct_account": rule1_data["account"],
        }

        # For multi-item templates
        if template_id == "multi_item":
            amount2 = random.choice(amounts)
            amount2_ex_vat, vat_amount2 = self.calculate_vat(
                amount2, rule2_data["vat_rate"]
            )
            category2, category2_label = self.get_category_info(rule2_data["rule_id"])

            values.update(
                {
                    "category1": category,
                    "category1_label": category_label,
                    "amount1": amount,
                    "amount1_ex_vat": amount_ex_vat,
                    "account1": rule1_data["account"],
                    "account1_label": rule1_data["rule_name"],
                    "vat_code1": rule1_data["vat_code"],
                    "vat_rate1": rule1_data["vat_rate"],
                    "category2": category2,
                    "category2_label": category2_label,
                    "amount2": amount2,
                    "amount2_ex_vat": amount2_ex_vat,
                    "account2": rule2_data["account"],
                    "account2_label": rule2_data["rule_name"],
                    "vat_code2": rule2_data["vat_code"],
                    "vat_rate2": rule2_data["vat_rate"],
                }
            )

        # Fill template turns
        messages = [{"role": "system", "content": template["system"]}]

        for turn in template["turns"]:
            user_content = turn["user"].format(**values)
            assistant_content = turn["assistant"].format(**values)

            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": assistant_content})

        return {
            "messages": messages,
            "metadata": {
                "domain": "accounting",
                "task": "conversation",
                "source_ids": [rule1_data["rule_id"]],
                "locale": "nb-NO",
                "conversation_type": template_id,
                "turns": len(template["turns"]),
                "family_key": template_id,
            },
        }

    def generate_samples(
        self, source_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate synthetic conversation samples from templates."""
        samples: list[dict[str, Any]] = []

        rules = [r for r in source_data if r.get("is_active", True)]

        if not rules:
            logger.warning("No active rules found for synthetic generation")
            return samples

        for template in ALL_TEMPLATES:
            template_id = template["template_id"]
            logger.info(
                f"Generating {self.conversations_per_template} conversations "
                f"for template: {template_id}"
            )

            for _ in range(self.conversations_per_template):
                try:
                    sample = self.fill_template(template, rules)
                    if sample:
                        samples.append(sample)
                except Exception as e:
                    logger.debug(f"Failed to generate sample for {template_id}: {e}")
                    continue

        logger.info(
            f"Generated {len(samples)} conversation samples from {len(ALL_TEMPLATES)} templates"
        )
        return samples
