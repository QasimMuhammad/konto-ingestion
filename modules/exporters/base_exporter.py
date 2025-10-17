"""
Base exporter class with train/val split logic.
"""

import json
import random
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.logger import logger


class BaseExporter(ABC):
    """Abstract base class for Gold layer exporters."""

    def __init__(
        self,
        output_dir: Path,
        split_ratio: float = 0.8,
        seed: int = 42,
    ):
        """
        Initialize base exporter.

        Args:
            output_dir: Directory to write JSONL files
            split_ratio: Train/val split ratio (default: 0.8)
            seed: Random seed for reproducible splits
        """
        self.output_dir = Path(output_dir)
        self.split_ratio = split_ratio
        self.seed = seed
        random.seed(seed)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "total_generated": 0,
            "train_samples": 0,
            "val_samples": 0,
        }

    @abstractmethod
    def extract_family_key(self, item: dict[str, Any]) -> str:
        """
        Extract family key for grouping items before split.

        Examples:
        - Tax glossary: chapter number
        - Accounting: account class
        - Rules: rule family prefix

        Args:
            item: Data item to extract family key from

        Returns:
            Family key string
        """
        pass

    @abstractmethod
    def generate_samples(
        self, source_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Generate training samples from source data.

        Args:
            source_data: List of source data items

        Returns:
            List of generated samples (GoldTrainingSample format)
        """
        pass

    def split_by_family(
        self, samples: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Split samples by family to avoid leakage.

        Groups items by family key, shuffles families, then splits
        at family boundaries.

        Args:
            samples: List of samples to split

        Returns:
            Tuple of (train_samples, val_samples)
        """
        families: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for sample in samples:
            family_key = self.extract_family_key(sample)
            families[family_key].append(sample)

        family_ids = list(families.keys())
        random.shuffle(family_ids)

        split_idx = int(len(family_ids) * self.split_ratio)
        train_families = family_ids[:split_idx]
        val_families = family_ids[split_idx:]

        train_samples = [
            sample for family in train_families for sample in families[family]
        ]
        val_samples = [sample for family in val_families for sample in families[family]]

        logger.info(
            f"Split by family: {len(train_families)} train families, "
            f"{len(val_families)} val families"
        )

        return train_samples, val_samples

    def write_jsonl(
        self, samples: list[dict[str, Any]], filename: str, split: str
    ) -> None:
        """
        Write samples to JSONL file.

        Args:
            samples: List of samples to write
            filename: Output filename
            split: Split type ('train' or 'val')
        """
        output_path = self.output_dir / split / filename

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                sample["metadata"]["split"] = split
                if not sample["metadata"].get("created_at"):
                    sample["metadata"]["created_at"] = (
                        datetime.utcnow().isoformat() + "Z"
                    )
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        logger.info(f"Wrote {len(samples)} samples to {output_path}")

    def export(
        self,
        source_data: list[dict[str, Any]],
        output_filename: str,
    ) -> dict[str, Any]:
        """
        Main export pipeline.

        Args:
            source_data: Source data to export
            output_filename: Base filename for output files

        Returns:
            Export statistics
        """
        logger.info(f"Starting export: {output_filename}")
        logger.info(f"Source data items: {len(source_data)}")

        samples = self.generate_samples(source_data)
        self.stats["total_generated"] = len(samples)
        logger.info(f"Generated {len(samples)} samples")

        train_samples, val_samples = self.split_by_family(samples)
        self.stats["train_samples"] = len(train_samples)
        self.stats["val_samples"] = len(val_samples)

        self.write_jsonl(train_samples, output_filename, "train")
        self.write_jsonl(val_samples, output_filename, "val")

        logger.info(
            f"Export complete: {len(train_samples)} train, {len(val_samples)} val"
        )

        return self.stats
