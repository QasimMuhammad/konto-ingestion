"""
Rule-based posting proposal exporter for Gold layer training data.

Generates variations of business rules with different amounts, descriptions,
and contexts to train the model on deterministic rule application.
"""

import random
from pathlib import Path

from typing import Any

from modules.exporters.base_exporter import BaseExporter
from modules.logger import get_logger

logger = get_logger(__name__)


class RuleExporter(BaseExporter):
    """Exporter for rule-based posting proposal training samples."""

    def __init__(self, output_dir: Path, split_ratio: float = 0.8):
        super().__init__(output_dir, split_ratio)
        self.domain = "accounting"
        self.task = "posting_proposal"
        self.variations_per_rule = 15

    def extract_family_key(self, item: dict[str, Any]) -> str:
        """Extract family key from rule_ids for train/val splitting."""
        rule_ids = item.get("metadata", {}).get("rule_ids", [])
        if rule_ids:
            rule_id = rule_ids[0]
            parts = rule_id.split("_")
            if len(parts) >= 2:
                return f"{parts[0]}_{parts[1]}"
        return "unknown"

    def calculate_vat(
        self, amount_incl_vat: float, vat_rate: float
    ) -> tuple[float, float]:
        """
        Calculate VAT breakdown from amount including VAT.

        Returns: (amount_ex_vat, vat_amount)
        """
        amount_ex_vat = amount_incl_vat / (1 + vat_rate / 100)
        vat_amount = amount_incl_vat - amount_ex_vat
        return round(amount_ex_vat, 2), round(vat_amount, 2)

    def generate_description_variations(
        self, base_description: str, category: str, amount: float
    ) -> list[str]:
        """Generate description variations for a transaction."""
        category_templates = {
            "hotel": [
                f"Hotellovernatting {amount} kr",
                "Hotel - forretningsreise",
                "Overnatting",
                "hotell",
                "Radisson Blu Oslo - 2 netter",
                "Hotell med frokost inkludert",
            ],
            "food": [
                f"Måltid {amount} kr",
                "Lunsj med kunde",
                "Mat og drikke",
                "restaurant",
                "Middag forretningsreise",
                "Lunch på forretningsreise",
            ],
            "office": [
                f"Kontorrekvisita {amount} kr",
                "Kontormateriale",
                "Skrivesaker",
                "kontorrekvisita",
                "Printer papir og blekkpatron",
                "Diverse kontorrekvisita",
            ],
            "transport": [
                f"Transport {amount} kr",
                "Drivstoff",
                "Bensin",
                "Parkering Oslo",
                "Bompenger",
                "Transport til kunde",
            ],
            "equipment": [
                f"Utstyr {amount} kr",
                "PC-utstyr",
                "Datamaskin",
                "utstyr",
                "Mus og tastatur",
                "Kontorpult",
            ],
        }

        return category_templates.get(
            category,
            [
                f"{base_description} {amount} kr",
                base_description,
                category,
                f"{category} {amount}",
            ],
        )

    def format_posting_proposal(
        self,
        account: str,
        account_label: str,
        vat_code: str,
        vat_rate: float,
        amount_incl_vat: float,
        rule_id: str,
        citation: str | None = None,
    ) -> str:
        """Format a posting proposal with VAT calculation."""
        amount_ex_vat, vat_amount = self.calculate_vat(amount_incl_vat, vat_rate)

        citation_text = f"\n\n[{citation}]" if citation else f"\n\n[Regel: {rule_id}]"

        return f"""Kontering:
- Konto: {account} ({account_label})
- MVA-kode: {vat_code}
- MVA-sats: {vat_rate}%
- Beløp eksl. MVA: {amount_ex_vat:.2f} kr
- MVA-beløp: {vat_amount:.2f} kr
- Totalt: {amount_incl_vat:.2f} kr{citation_text}"""

    def generate_variations_for_rule(
        self,
        rule: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate variations of a business rule."""
        variations = []

        rule_id = rule["rule_id"]
        rule_name = rule["rule_name"]

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
            logger.warning(f"Rule {rule_id} missing required actions")
            return []

        account = account_action["value"]
        vat_rate = vat_rate_action["value"]
        vat_code = vat_code_action["value"]

        amounts = [
            500,
            750,
            1000,
            1200,
            1500,
            1800,
            2000,
            2500,
            3000,
            3500,
            4000,
            5000,
            7500,
            10000,
            15000,
        ]
        random.seed(hash(rule_id))
        selected_amounts = random.sample(
            amounts, min(self.variations_per_rule, len(amounts))
        )

        citation = (
            rule["citations"][0] if rule.get("citations") else f"Regel: {rule_name}"
        )

        example_category = "office"
        if "hotel" in rule_id.lower():
            example_category = "hotel"
        elif "food" in rule_id.lower() or "meal" in rule_id.lower():
            example_category = "food"
        elif "transport" in rule_id.lower() or "fuel" in rule_id.lower():
            example_category = "transport"
        elif "equipment" in rule_id.lower() or "computer" in rule_id.lower():
            example_category = "equipment"

        for amount in selected_amounts:
            descriptions = self.generate_description_variations(
                rule_name, example_category, amount
            )

            for desc in descriptions[
                : max(1, self.variations_per_rule // len(selected_amounts) + 1)
            ]:
                variations.append(
                    {
                        "rule_id": rule_id,
                        "description": desc,
                        "amount": amount,
                        "account": account,
                        "account_label": rule_name,
                        "vat_code": vat_code,
                        "vat_rate": vat_rate,
                        "citation": citation,
                    }
                )

                if len(variations) >= self.variations_per_rule:
                    break

            if len(variations) >= self.variations_per_rule:
                break

        return variations[: self.variations_per_rule]

    def generate_samples(
        self, source_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate training samples from business rules."""
        samples: list[dict[str, Any]] = []

        system_prompt = (
            "Du er Konto AI, en regnskapsassistent for norske bedrifter. "
            "Du hjelper med å kontere transaksjoner korrekt med riktig konto, "
            "MVA-kode og beregning av merverdiavgift."
        )

        for rule in source_data:
            if not rule.get("is_active", True):
                continue

            variations = self.generate_variations_for_rule(rule)

            for var in variations:
                user_message = var["description"]

                assistant_message = self.format_posting_proposal(
                    account=var["account"],
                    account_label=var["account_label"],
                    vat_code=var["vat_code"],
                    vat_rate=var["vat_rate"],
                    amount_incl_vat=var["amount"],
                    rule_id=var["rule_id"],
                    citation=var.get("citation"),
                )

                sample = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": assistant_message},
                    ],
                    "metadata": {
                        "domain": "accounting",
                        "task": "posting_proposal",
                        "source_ids": rule.get("source_ids", []),
                        "locale": "nb-NO",
                        "rule_ids": [var["rule_id"]],
                        "family_key": self.extract_family_key(
                            {"metadata": {"rule_ids": [var["rule_id"]]}}
                        ),
                    },
                }

                samples.append(sample)

        logger.info(f"Generated {len(samples)} samples from {len(source_data)} rules")
        return samples
