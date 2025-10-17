"""
Conversation templates for synthetic Gold layer training data.

Templates define multi-turn conversation patterns for different accounting
and tax scenarios.
"""

SYSTEM_PROMPT = (
    "Du er Konto AI, en hjelpsom regnskapsassistent for norske bedrifter. "
    "Du hjelper med kontering, MVA-spørsmål, og regnskapsføring."
)

# Template 1: Expense Entry with Clarification
TEMPLATE_EXPENSE_ENTRY = {
    "template_id": "expense_entry",
    "description": "User describes expense, AI asks for clarification, then provides posting",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": "Jeg har en {category} på {amount} kr. Hvordan konterer jeg den?",
            "assistant": (
                "For å kontere {category_label} riktig, trenger jeg litt mer informasjon:\n"
                "- Er dette for en forretningsreise eller privat bruk?\n"
                "- Er leverandøren norsk eller utenlandsk?"
            ),
        },
        {
            "user": "Det er {context}",
            "assistant": (
                "Takk! Da konteres det slik:\n"
                "- Konto: {account} ({account_label})\n"
                "- MVA-kode: {vat_code}\n"
                "- MVA-sats: {vat_rate}%\n"
                "- Beløp eksl. MVA: {amount_ex_vat} kr\n"
                "- MVA-beløp: {vat_amount} kr\n\n"
                "{explanation}. Er det noe annet jeg kan hjelpe med?"
            ),
        },
    ],
    "placeholders": [
        "category",
        "category_label",
        "amount",
        "context",
        "account",
        "account_label",
        "vat_code",
        "vat_rate",
        "amount_ex_vat",
        "vat_amount",
        "explanation",
    ],
}

# Template 2: VAT Rate Question
TEMPLATE_VAT_QUESTION = {
    "template_id": "vat_question",
    "description": "User asks about VAT rates for a category",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": "Hvilken MVA-sats gjelder for {category}?",
            "assistant": (
                "For {category_label} gjelder {vat_rate}% MVA.\n\n"
                "{explanation} Hvis du har en {category} på {example_amount} kr inkl. MVA, "
                "blir det {example_ex_vat} kr eksl. MVA og {example_vat} kr i MVA."
            ),
        },
    ],
    "placeholders": [
        "category",
        "category_label",
        "vat_rate",
        "explanation",
        "example_amount",
        "example_ex_vat",
        "example_vat",
    ],
}

# Template 3: Account Selection Help
TEMPLATE_ACCOUNT_HELP = {
    "template_id": "account_help",
    "description": "User unsure which account to use",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": "Jeg er usikker på hvilken konto jeg skal bruke for {category}. Hva anbefaler du?",
            "assistant": (
                "For {category_label} anbefaler jeg konto {account} ({account_label}).\n\n"
                "Denne kontoen brukes for {explanation}. "
                "Eksempler: {examples}."
            ),
        },
        {
            "user": "Takk! Og hva med MVA?",
            "assistant": (
                "For {category_label} skal du bruke MVA-kode {vat_code} med sats {vat_rate}%.\n\n"
                "Dette betyr at hvis kjøpet er på {example_amount} kr inkl. MVA, "
                "skal du føre {example_ex_vat} kr på konto {account} og {example_vat} kr på MVA-konto."
            ),
        },
    ],
    "placeholders": [
        "category",
        "category_label",
        "account",
        "account_label",
        "explanation",
        "examples",
        "vat_code",
        "vat_rate",
        "example_amount",
        "example_ex_vat",
        "example_vat",
    ],
}

# Template 4: Quick Posting (Simple)
TEMPLATE_QUICK_POSTING = {
    "template_id": "quick_posting",
    "description": "Direct posting request with all info",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": "{category} {amount} kr, norsk leverandør",
            "assistant": (
                "Kontering:\n"
                "- Konto: {account} ({account_label})\n"
                "- MVA: {vat_code} ({vat_rate}%)\n"
                "- Beløp eksl. MVA: {amount_ex_vat} kr\n"
                "- MVA: {vat_amount} kr"
            ),
        },
    ],
    "placeholders": [
        "category",
        "amount",
        "account",
        "account_label",
        "vat_code",
        "vat_rate",
        "amount_ex_vat",
        "vat_amount",
    ],
}

# Template 5: Correction Flow
TEMPLATE_CORRECTION = {
    "template_id": "correction",
    "description": "User realizes they made a mistake",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": "Jeg konterte {category} på konto {wrong_account}. Er det riktig?",
            "assistant": (
                "Nei, det er ikke helt riktig. For {category_label} skal du bruke "
                "konto {correct_account} ({account_label}), ikke {wrong_account}.\n\n"
                "{explanation}"
            ),
        },
        {
            "user": "Hvordan retter jeg dette?",
            "assistant": (
                "For å rette dette må du:\n"
                "1. Reversere posteringen på konto {wrong_account}\n"
                "2. Føre riktig beløp på konto {correct_account} ({account_label})\n"
                "3. Sjekk at MVA-koden er {vat_code} ({vat_rate}%)\n\n"
                "Beløpet skal være {amount_ex_vat} kr eksl. MVA."
            ),
        },
    ],
    "placeholders": [
        "category",
        "category_label",
        "wrong_account",
        "correct_account",
        "account_label",
        "explanation",
        "vat_code",
        "vat_rate",
        "amount_ex_vat",
    ],
}

# Template 6: Multi-Item Transaction
TEMPLATE_MULTI_ITEM = {
    "template_id": "multi_item",
    "description": "Multiple expense items in one transaction",
    "system": SYSTEM_PROMPT,
    "turns": [
        {
            "user": (
                "Jeg har en kvittering med flere linjer:\n"
                "- {category1} {amount1} kr\n"
                "- {category2} {amount2} kr\n"
                "Hvordan konterer jeg dette?"
            ),
            "assistant": (
                "Du må kontere hver linje separat:\n\n"
                "Linje 1 - {category1_label}:\n"
                "- Konto: {account1} ({account1_label})\n"
                "- MVA: {vat_code1} ({vat_rate1}%)\n"
                "- Beløp eksl. MVA: {amount1_ex_vat} kr\n\n"
                "Linje 2 - {category2_label}:\n"
                "- Konto: {account2} ({account2_label})\n"
                "- MVA: {vat_code2} ({vat_rate2}%)\n"
                "- Beløp eksl. MVA: {amount2_ex_vat} kr"
            ),
        },
    ],
    "placeholders": [
        "category1",
        "category1_label",
        "amount1",
        "account1",
        "account1_label",
        "vat_code1",
        "vat_rate1",
        "amount1_ex_vat",
        "category2",
        "category2_label",
        "amount2",
        "account2",
        "account2_label",
        "vat_code2",
        "vat_rate2",
        "amount2_ex_vat",
    ],
}

# All templates
ALL_TEMPLATES = [
    TEMPLATE_EXPENSE_ENTRY,
    TEMPLATE_VAT_QUESTION,
    TEMPLATE_ACCOUNT_HELP,
    TEMPLATE_QUICK_POSTING,
    TEMPLATE_CORRECTION,
    TEMPLATE_MULTI_ITEM,
]

# Category variations for natural language
CATEGORY_VARIATIONS = {
    "hotel": ["hotellovernatting", "hotell", "overnatting", "hotellrom"],
    "food": ["måltid", "restaurant", "lunsj", "middag", "mat"],
    "office": [
        "kontorrekvisita",
        "kontormateriale",
        "skrivesaker",
        "kontorforsyninger",
    ],
    "transport": ["transport", "drivstoff", "bensin", "taxi", "bompenger"],
    "equipment": ["utstyr", "datautstyr", "verktøy", "maskiner"],
}

# Context variations
CONTEXT_VARIATIONS = [
    "en norsk forretningsreise",
    "forretningsrelatert",
    "en forretningsutgift",
    "en vanlig forretningskjøp",
    "fra en norsk leverandør",
]
