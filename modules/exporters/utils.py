"""
Shared utilities for Gold layer exporters.
"""

import json
from pathlib import Path


def calculate_vat(amount_incl_vat: float, vat_rate: float) -> tuple[float, float]:
    """
    Calculate VAT breakdown from amount including VAT.

    Args:
        amount_incl_vat: Total amount including VAT
        vat_rate: VAT rate as percentage (e.g., 25.0 for 25%)

    Returns:
        Tuple of (amount_ex_vat, vat_amount)
    """
    amount_ex_vat = amount_incl_vat / (1 + vat_rate / 100)
    vat_amount = amount_incl_vat - amount_ex_vat
    return round(amount_ex_vat, 2), round(vat_amount, 2)


def load_json(file_path: Path) -> list[dict] | dict:  # type: ignore[return]
    """
    Load JSON data from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded JSON data (list or dict)
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


SYSTEM_PROMPTS = {
    "tax_glossary": (
        "Du er en norsk regnskapsassistent med ekspertise innen skatt og merverdiavgift. "
        "Svar kort og presist med kildehenvisninger."
    ),
    "accounting_glossary": (
        "Du er en norsk regnskapsassistent med ekspertise innen regnskap og bokføring. "
        "Svar kort og presist med kildehenvisninger."
    ),
    "posting_proposal": (
        "Du er Konto AI, en regnskapsassistent for norske bedrifter. "
        "Du hjelper med å kontere transaksjoner korrekt med riktig konto, "
        "MVA-kode og beregning av merverdiavgift."
    ),
    "conversation": (
        "Du er Konto AI, en hjelpsom regnskapsassistent for norske bedrifter. "
        "Du hjelper med kontering, MVA-spørsmål, og regnskapsføring."
    ),
}
