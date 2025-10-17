"""
Glossary exporter for tax and accounting terminology.
"""

import re
from pathlib import Path
from typing import Any

from modules.exporters.base_exporter import BaseExporter
from modules.logger import logger


class GlossaryExporter(BaseExporter):
    """Exporter for tax and accounting glossary training data."""

    def __init__(
        self,
        output_dir: Path,
        domain: str = "tax",
        split_ratio: float = 0.8,
        seed: int = 42,
    ):
        """
        Initialize glossary exporter.

        Args:
            output_dir: Directory to write JSONL files
            domain: Domain type ('tax' or 'accounting')
            split_ratio: Train/val split ratio
            seed: Random seed
        """
        super().__init__(output_dir, split_ratio, seed)
        self.domain = domain

        self.system_prompts = {
            "tax": "Du er en norsk regnskapsassistent med ekspertise innen skatt og merverdiavgift. Svar kort og presist med kildehenvisninger.",
            "accounting": "Du er en norsk regnskapsassistent med ekspertise innen regnskap og bokføring. Svar kort og presist med kildehenvisninger.",
        }

        self.procedural_keywords = {
            "søknad",
            "klage",
            "vedtak",
            "frist",
            "innlevering",
            "kontrollopplysninger",
            "straff",
            "overtredelse",
        }

        self.definition_keywords = {
            "definisjon",
            "virkeområde",
            "gjelder",
            "omfatter",
            "betyr",
            "menes",
        }

    def extract_family_key(self, item: dict[str, Any]) -> str:
        """
        Extract family key from generated sample.

        Family key is stored in metadata['family_key'] during generation.
        """
        return item.get("metadata", {}).get("family_key", "unknown")

    def is_procedural_section(self, text: str) -> bool:
        """Check if section is procedural (should be excluded from glossary)."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.procedural_keywords)

    def has_definition_content(self, heading: str, text: str) -> bool:
        """Check if section contains definition-worthy content."""
        heading_lower = heading.lower()
        text_lower = text.lower()

        has_def_keyword = any(
            keyword in heading_lower or keyword in text_lower[:200]
            for keyword in self.definition_keywords
        )

        return has_def_keyword

    def extract_term_from_heading(self, heading: str) -> str | None:
        """
        Extract terminology from heading.

        Examples:
        - "§ 1-1. Saklig virkeområde" -> "Saklig virkeområde"
        - "Kapittel 3 Fradrag" -> "Fradrag"
        """
        heading = heading.strip()

        match = re.search(r"§\s*[\d-]+\.?\s*(.+)", heading)
        if match:
            return match.group(1).strip()

        match = re.search(r"Kapittel\s+\d+\s+(.+)", heading)
        if match:
            return match.group(1).strip()

        if len(heading) > 10 and not heading.startswith("§"):
            return heading

        return None

    def truncate_text(self, text: str, max_tokens: int = 250) -> str:
        """
        Truncate text to approximate token limit.

        Rough approximation: 1 token ≈ 4 characters for Norwegian.
        """
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars].rsplit(".", 1)[0]
        if truncated:
            return truncated + "."
        return text[:max_chars] + "..."

    def add_citation(self, item: dict[str, Any], text: str) -> str:
        """Add citation to answer text."""
        if self.domain == "tax":
            section_label = (
                item.get("section_label") or item.get("heading", "").split(".")[0]
            )
            law_title = item.get("law_title", "")
            citation = f"[{section_label} {law_title}]"
        elif self.domain == "accounting":
            if "account_id" in item:
                citation = f"[NS 4102 konto {item['account_id']}]"
            elif "node_path" in item:
                citation = f"[SAF-T {item.get('version', '1.3')} {item['node_path']}]"
            else:
                citation = "[SAF-T spesifikasjon]"
        else:
            citation = ""

        if citation and not text.endswith(citation):
            return f"{text} {citation}"
        return text

    def generate_tax_glossary_sample(
        self, section: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Generate glossary sample from law section."""
        heading = section.get("heading", "")
        text_plain = section.get("text_plain", "")

        if len(text_plain) < 100 or len(text_plain) > 3000:
            return None

        if self.is_procedural_section(text_plain):
            return None

        term = self.extract_term_from_heading(heading)
        if not term:
            return None

        answer = self.truncate_text(text_plain, max_tokens=250)
        answer = self.add_citation(section, answer)

        questions = [
            f"Hva betyr '{term}'?",
            f"Forklar '{term}'",
            f"Hva er '{term}'?",
        ]

        import random

        question = random.choice(questions)

        chapter = section.get("chapter_no", "unknown")
        law_id = section.get("law_id", "unknown")
        family_key = f"{law_id}_chapter_{chapter}"

        return {
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompts["tax"],
                },
                {
                    "role": "user",
                    "content": question,
                },
                {
                    "role": "assistant",
                    "content": answer,
                },
            ],
            "metadata": {
                "domain": "tax",
                "task": "glossary_define",
                "source_ids": [
                    f"{section.get('law_id', 'unknown')}_{section.get('section_id', 'unknown')}"
                ],
                "locale": "nb-NO",
                "family_key": family_key,
            },
        }

    def generate_account_glossary_sample(
        self, account: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Generate glossary sample from chart of accounts entry."""
        account_id = account.get("account_id", "")
        account_label = account.get("account_label", "")
        description = account.get("description", "")
        examples = account.get("examples", [])

        if not account_id or not account_label:
            return None

        answer_parts = [description]
        if examples:
            examples_str = ", ".join(examples[:3])
            answer_parts.append(f"Eksempler: {examples_str}")

        answer = " ".join(answer_parts)
        answer = self.add_citation(account, answer)

        question = f"Hva er konto {account_id}?"

        account_class = account.get("account_class", "unknown")
        family_key = f"account_class_{account_class}"

        return {
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompts["accounting"],
                },
                {
                    "role": "user",
                    "content": question,
                },
                {
                    "role": "assistant",
                    "content": answer,
                },
            ],
            "metadata": {
                "domain": "accounting",
                "task": "glossary_define",
                "source_ids": [f"chart_of_accounts_{account_id}"],
                "locale": "nb-NO",
                "family_key": family_key,
            },
        }

    def generate_saft_glossary_sample(
        self, node: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Generate glossary sample from SAF-T node."""
        node_label = node.get("node_label", "")
        description = node.get("description", "")

        if not node_label or not description or len(description) < 20:
            return None

        answer = self.truncate_text(description, max_tokens=200)
        answer = self.add_citation(node, answer)

        question = f"Hva er '{node_label}' i SAF-T?"

        node_level = node.get("node_level", 0)
        family_key = f"saft_level_{node_level}"

        return {
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompts["accounting"],
                },
                {
                    "role": "user",
                    "content": question,
                },
                {
                    "role": "assistant",
                    "content": answer,
                },
            ],
            "metadata": {
                "domain": "accounting",
                "task": "glossary_define",
                "source_ids": [f"saft_{node.get('node_id', 'unknown')}"],
                "locale": "nb-NO",
                "family_key": family_key,
            },
        }

    def generate_samples(
        self, source_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate glossary samples from source data."""
        samples: list[dict[str, Any]] = []

        for item in source_data:
            sample = None

            if self.domain == "tax":
                sample = self.generate_tax_glossary_sample(item)
            elif self.domain == "accounting":
                if "account_id" in item:
                    sample = self.generate_account_glossary_sample(item)
                elif "node_id" in item:
                    sample = self.generate_saft_glossary_sample(item)

            if sample:
                samples.append(sample)

        logger.info(f"Generated {len(samples)} {self.domain} glossary samples")
        return samples
