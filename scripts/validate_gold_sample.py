#!/usr/bin/env python3
"""Quick validation script for Gold JSONL samples."""

import json
from pathlib import Path

from modules.schemas import GoldTrainingSample


def validate_file(filepath: Path):
    """Validate first sample from JSONL file."""
    with open(filepath, "r", encoding="utf-8") as f:
        first_line = f.readline()

    data = json.loads(first_line)

    # Validate with Pydantic
    sample = GoldTrainingSample(**data)

    print(f"✅ {filepath.name} - Valid!")
    print(f"   Question: {sample.messages[1].content}")
    print(f"   Answer: {sample.messages[2].content[:100]}...")
    print(f"   Domain: {sample.metadata.domain}, Task: {sample.metadata.task}")
    print()


if __name__ == "__main__":
    gold_dir = Path("data/gold")

    for jsonl_file in gold_dir.rglob("*.jsonl"):
        validate_file(jsonl_file)
