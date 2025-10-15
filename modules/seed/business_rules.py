"""
Business Rules seed data generator.
Generates deterministic accounting rules with citations to silver layer.
"""

import json
from datetime import datetime
from pathlib import Path

from ..logger import logger
from ..schemas import (
    BusinessRule,
)
from ..settings import get_silver_dir


def get_business_rules() -> list[BusinessRule]:
    """Business rules for common accounting scenarios with citations to silver layer."""
    timestamp = datetime.now().isoformat()

    rules_data = [
        {
            "rule_id": "expense_hotel_no_001",
            "rule_name": "Hotellovernatting Norge",
            "description": "Reisekostnad for hotellovernatting i Norge med redusert MVA-sats 12 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "hotel"},
                {"field": "country", "operator": "equals", "value": "NO"},
            ],
            "actions": [
                {"type": "set_account", "value": "7140"},
                {"type": "set_vat_code", "value": "LOW"},
                {"type": "set_vat_rate", "value": 12.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "rate_table_low_12",
            ],
            "citations": [
                "Merverdiavgiftsloven § 5-3: Redusert sats for overnatting",
                "Skatteetaten satser: 12 % MVA for hotellrom",
            ],
            "examples": [
                {
                    "description": "Hotellovernatting på forretningsreise",
                    "input": {
                        "amount": 1200,
                        "category": "hotel",
                        "country": "NO",
                    },
                    "output": {"account": "7140", "vat_code": "LOW", "vat_rate": 12.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_food_travel_001",
            "rule_name": "Måltid på reise",
            "description": "Kostnad for mat under tjenestereise med MVA-sats 15 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "food"},
                {"field": "context", "operator": "equals", "value": "travel"},
            ],
            "actions": [
                {"type": "set_account", "value": "7160"},
                {"type": "set_vat_code", "value": "MEDIUM"},
                {"type": "set_vat_rate", "value": 15.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "rate_table_medium_15",
            ],
            "citations": [
                "Merverdiavgiftsloven § 5-2: Redusert sats for næringsmidler",
                "Skatteetaten satser: 15 % MVA for mat og drikkevarer",
            ],
            "examples": [
                {
                    "description": "Restaurant under forretningsreise",
                    "input": {
                        "amount": 250,
                        "category": "food",
                        "context": "travel",
                    },
                    "output": {
                        "account": "7160",
                        "vat_code": "MEDIUM",
                        "vat_rate": 15.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_rent_office_001",
            "rule_name": "Kontorhusleie",
            "description": "Husleie for kontorlokaler med full MVA-sats 25 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "rent"},
                {"field": "subcategory", "operator": "equals", "value": "office"},
            ],
            "actions": [
                {"type": "set_account", "value": "6000"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "bokforingsloven_2004",
            ],
            "citations": [
                "Merverdiavgiftsloven § 4-1: Utleie av fast eiendom",
                "Standard sats 25 % for utleie av næringslokaler",
            ],
            "examples": [
                {
                    "description": "Månedlig kontorhusleie",
                    "input": {
                        "amount": 15000,
                        "category": "rent",
                        "subcategory": "office",
                    },
                    "output": {"account": "6000", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "income_product_sales_001",
            "rule_name": "Varesalg",
            "description": "Inntekt fra salg av varer med full MVA-sats 25 %",
            "category": "income",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "income"},
                {"field": "category", "operator": "equals", "value": "product_sales"},
            ],
            "actions": [
                {"type": "set_account", "value": "3000"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
                {"type": "set_vat_account", "value": "2700"},
            ],
            "source_ids": [
                "mva_law_2009",
                "regnskapsloven_1998",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-1: Omsetning av varer",
                "Standard MVA-sats 25 % på varesalg",
            ],
            "examples": [
                {
                    "description": "Salg av produkter til kunde",
                    "input": {
                        "amount": 10000,
                        "category": "product_sales",
                    },
                    "output": {
                        "account": "3000",
                        "vat_code": "HIGH",
                        "vat_rate": 25.0,
                        "vat_account": "2700",
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "income_service_sales_001",
            "rule_name": "Tjenestesalg",
            "description": "Inntekt fra salg av tjenester med full MVA-sats 25 %",
            "category": "income",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "income"},
                {"field": "category", "operator": "equals", "value": "service_sales"},
                {"field": "country", "operator": "equals", "value": "NO"},
            ],
            "actions": [
                {"type": "set_account", "value": "3100"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
                {"type": "set_vat_account", "value": "2700"},
            ],
            "source_ids": [
                "mva_law_2009",
                "regnskapsloven_1998",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-1: Omsetning av tjenester",
                "Standard MVA-sats 25 % på tjenestesalg",
            ],
            "examples": [
                {
                    "description": "Konsulenttjenester",
                    "input": {
                        "amount": 20000,
                        "category": "service_sales",
                        "country": "NO",
                    },
                    "output": {
                        "account": "3100",
                        "vat_code": "HIGH",
                        "vat_rate": 25.0,
                        "vat_account": "2700",
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_salary_001",
            "rule_name": "Lønnskostnad",
            "description": "Lønn til ansatte uten MVA",
            "category": "expense",
            "domain": "payroll",
            "priority": 5,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "salary"},
            ],
            "actions": [
                {"type": "set_account", "value": "5000"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "bokforingsloven_2004",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-6: Lønnskostnader er ikke avgiftspliktige",
                "Bokføringsloven § 5-1: Lønn som driftskostnad",
            ],
            "examples": [
                {
                    "description": "Månedlig lønn",
                    "input": {
                        "amount": 45000,
                        "category": "salary",
                    },
                    "output": {
                        "account": "5000",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_employer_tax_001",
            "rule_name": "Arbeidsgiveravgift",
            "description": "Arbeidsgiveravgift til NAV uten MVA",
            "category": "expense",
            "domain": "payroll",
            "priority": 5,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "employer_tax"},
            ],
            "actions": [
                {"type": "set_account", "value": "5400"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "skatteloven_1999",
            ],
            "citations": [
                "Folketrygdloven § 23-2: Arbeidsgiveravgift",
                "Arbeidsgiveravgift er ikke MVA-pliktig",
            ],
            "examples": [
                {
                    "description": "AGA på lønnskostnader",
                    "input": {
                        "amount": 6345,
                        "category": "employer_tax",
                    },
                    "output": {
                        "account": "5400",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_office_supplies_001",
            "rule_name": "Kontorrekvisita",
            "description": "Kontormateriell og rekvisita med full MVA-sats 25 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "office_supplies"},
            ],
            "actions": [
                {"type": "set_account", "value": "6800"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for kontorrekvisita",
            ],
            "examples": [
                {
                    "description": "Papir, penner, mapper",
                    "input": {
                        "amount": 350,
                        "category": "office_supplies",
                    },
                    "output": {"account": "6800", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_telecom_001",
            "rule_name": "Telefon og internett",
            "description": "Telefonabonnement og internett med full MVA-sats 25 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "category",
                    "operator": "in",
                    "value": ["telephone", "internet", "telecom"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6900"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for telekommunikasjon",
            ],
            "examples": [
                {
                    "description": "Mobilabonnement og bredbånd",
                    "input": {
                        "amount": 799,
                        "category": "telecom",
                    },
                    "output": {"account": "6900", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_fuel_001",
            "rule_name": "Drivstoff",
            "description": "Drivstoff til firmabil med full MVA-sats 25 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "fuel"},
            ],
            "actions": [
                {"type": "set_account", "value": "7320"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for drivstoff",
            ],
            "examples": [
                {
                    "description": "Bensin/diesel til firmabil",
                    "input": {
                        "amount": 950,
                        "category": "fuel",
                    },
                    "output": {"account": "7320", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_consulting_001",
            "rule_name": "Konsulenttjenester",
            "description": "Kjøp av konsulenttjenester, typisk med full MVA-sats",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "consulting"},
            ],
            "actions": [
                {"type": "set_account", "value": "6340"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for konsulenttjenester",
            ],
            "examples": [
                {
                    "description": "IT-konsulent, rådgivning",
                    "input": {
                        "amount": 12000,
                        "category": "consulting",
                    },
                    "output": {"account": "6340", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_maintenance_001",
            "rule_name": "Reparasjon og vedlikehold",
            "description": "Reparasjon og vedlikehold av bygg/utstyr med full MVA-sats",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "category",
                    "operator": "in",
                    "value": ["repair", "maintenance"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6300"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for reparasjoner",
            ],
            "examples": [
                {
                    "description": "Reparasjon av maskiner",
                    "input": {
                        "amount": 4500,
                        "category": "repair",
                    },
                    "output": {"account": "6300", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            # TODO: Verify current rate policy - standard electricity is often 25%, not 15%
            #       15% applies only to certain cases (e.g., water/sewage services)
            "rule_id": "expense_electricity_001",
            "rule_name": "Strøm",
            "description": "Strømkostnader med redusert MVA-sats 15 % (ved visse vilkår)",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "electricity"},
            ],
            "actions": [
                {"type": "set_account", "value": "6100"},
                {"type": "set_vat_code", "value": "MEDIUM"},
                {"type": "set_vat_rate", "value": 15.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "rate_table_medium_15",
            ],
            "citations": [
                "Merverdiavgiftsloven: Strøm kan ha redusert sats",
                "15 % MVA for vann og avløpstjenester",
            ],
            "examples": [
                {
                    "description": "Månedlig strømregning",
                    "input": {
                        "amount": 2500,
                        "category": "electricity",
                    },
                    "output": {
                        "account": "6100",
                        "vat_code": "MEDIUM",
                        "vat_rate": 15.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "income_interest_001",
            "rule_name": "Renteinntekt",
            "description": "Renteinntekter fra bank uten MVA",
            "category": "income",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "income"},
                {"field": "category", "operator": "equals", "value": "interest"},
            ],
            "actions": [
                {"type": "set_account", "value": "8050"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-6: Finansielle tjenester er unntatt MVA",
            ],
            "examples": [
                {
                    "description": "Renteinntekt fra bankinnskudd",
                    "input": {
                        "amount": 150,
                        "category": "interest",
                    },
                    "output": {
                        "account": "8050",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_interest_001",
            "rule_name": "Rentekostnad",
            "description": "Rentekostnader på lån uten MVA",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "interest"},
            ],
            "actions": [
                {"type": "set_account", "value": "8150"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-6: Finansielle tjenester er unntatt MVA",
            ],
            "examples": [
                {
                    "description": "Rentekostnad på banklån",
                    "input": {
                        "amount": 2500,
                        "category": "interest",
                    },
                    "output": {
                        "account": "8150",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_transport_public_001",
            "rule_name": "Offentlig transport",
            "description": "Reise med tog, buss, fly med redusert MVA-sats 12 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "category",
                    "operator": "in",
                    "value": ["train", "bus", "flight", "public_transport"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "7000"},
                {"type": "set_vat_code", "value": "LOW"},
                {"type": "set_vat_rate", "value": 12.0},
            ],
            "source_ids": [
                "mva_law_2009",
                "rate_table_low_12",
            ],
            "citations": [
                "Merverdiavgiftsloven § 5-3: Redusert sats for persontransport",
                "12 % MVA for tog, buss, fly",
            ],
            "examples": [
                {
                    "description": "Togbillett Oslo-Bergen",
                    "input": {
                        "amount": 899,
                        "category": "train",
                    },
                    "output": {"account": "7000", "vat_code": "LOW", "vat_rate": 12.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_goods_purchase_001",
            "rule_name": "Varekjøp",
            "description": "Kjøp av varer til videresalg med full MVA-sats 25 %",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "goods_purchase"},
            ],
            "actions": [
                {"type": "set_account", "value": "4000"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Standard MVA-sats 25 % for varekjøp",
            ],
            "examples": [
                {
                    "description": "Innkjøp av handelsvarer",
                    "input": {
                        "amount": 50000,
                        "category": "goods_purchase",
                    },
                    "output": {"account": "4000", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_eu_service_reverse_001",
            "rule_name": "EU-tjeneste omvendt avgiftsplikt",
            "description": "Kjøp av tjenester fra EU med omvendt avgiftsplikt",
            "category": "vat_calculation",
            "domain": "tax",
            "priority": 5,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "category", "operator": "equals", "value": "service"},
                {"field": "country", "operator": "in", "value": ["EU"]},
                {
                    "field": "supplier_vat_registered",
                    "operator": "equals",
                    "value": True,
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6340"},
                {"type": "set_vat_code", "value": "REVERSE_CHARGE"},
                {"type": "set_vat_rate", "value": 25.0},
                {"type": "set_posting_type", "value": "reverse_charge_eu"},
            ],
            "source_ids": [
                "mva_law_2009",
            ],
            "citations": [
                "Merverdiavgiftsloven § 3-30: Omvendt avgiftsplikt",
                "§ 11-1: Fradragsrett for inngående avgift",
            ],
            "examples": [
                {
                    "description": "SaaS-abonnement fra EU (Adobe, Microsoft)",
                    "input": {
                        "amount": 5000,
                        "category": "service",
                        "country": "EU",
                        "supplier_vat_registered": True,
                    },
                    "output": {
                        "account": "6340",
                        "vat_code": "REVERSE_CHARGE",
                        "vat_rate": 25.0,
                        "posting_type": "reverse_charge_eu",
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "asset_machinery_001",
            "rule_name": "Maskiner og utstyr",
            "description": "Kjøp av maskiner og utstyr som anleggsmiddel",
            "category": "expense",
            "domain": "accounting",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "category",
                    "operator": "in",
                    "value": ["machinery", "equipment"],
                },
                {"field": "amount", "operator": "greater_than", "value": 15000},
            ],
            "actions": [
                {"type": "set_account", "value": "1220"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
                {"type": "set_asset_category", "value": "machinery"},
            ],
            "source_ids": [
                "regnskapsloven_1998",
                "mva_law_2009",
            ],
            "citations": [
                "Regnskapsloven § 5-1: Aktivering av anleggsmidler",
                "Bokføringsloven § 6-1: Maskiner som varig driftsmiddel",
            ],
            "examples": [
                {
                    "description": "Kjøp av produksjonsmaskin",
                    "input": {
                        "amount": 85000,
                        "category": "machinery",
                    },
                    "output": {
                        "account": "1220",
                        "vat_code": "HIGH",
                        "vat_rate": 25.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "asset_it_equipment_001",
            "rule_name": "IT-utstyr",
            "description": "Kjøp av datautstyr og IT-utstyr som inventar",
            "category": "expense",
            "domain": "accounting",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "category",
                    "operator": "in",
                    "value": ["computer", "it_equipment"],
                },
                {"field": "amount", "operator": "greater_than", "value": 15000},
            ],
            "actions": [
                {"type": "set_account", "value": "1240"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
                {"type": "set_asset_category", "value": "it_equipment"},
            ],
            "source_ids": [
                "regnskapsloven_1998",
                "mva_law_2009",
            ],
            "citations": [
                "Regnskapsloven § 5-1: Aktivering av anleggsmidler",
                "IT-utstyr over 15 000 kr aktiveres som inventar",
            ],
            "examples": [
                {
                    "description": "Servere og nettverksutstyr",
                    "input": {
                        "amount": 45000,
                        "category": "it_equipment",
                    },
                    "output": {
                        "account": "1240",
                        "vat_code": "HIGH",
                        "vat_rate": 25.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_rent_001",
            "rule_name": "Husleie kontor",
            "description": "Husleie for kontorlokaler",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {"field": "description", "operator": "contains", "value": "husleie"},
            ],
            "actions": [
                {"type": "set_account", "value": "5405"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for husleie"],
            "examples": [
                {
                    "description": "Månedlig husleie",
                    "input": {"amount": 15000, "description": "husleie kontor"},
                    "output": {"account": "5405", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_phone_internet_001",
            "rule_name": "Telefon og internett",
            "description": "Kostnader til telefon og internett",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": ["telefon", "internett"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6550"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for telekommunikasjon"],
            "examples": [
                {
                    "description": "Mobilabonnement",
                    "input": {"amount": 799, "description": "telefon abonnement"},
                    "output": {"account": "6550", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_software_001",
            "rule_name": "Programvarelisenser",
            "description": "SaaS og programvarelisenser",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": ["Microsoft", "Google Workspace", "Adobe"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6551"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for programvarelisenser"],
            "examples": [
                {
                    "description": "Microsoft 365 abonnement",
                    "input": {"amount": 2000, "description": "Microsoft 365"},
                    "output": {"account": "6551", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_supplies_001",
            "rule_name": "Forbruksmateriell",
            "description": "Kontorrekvisita og forbruksmateriell",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": ["kontorrekvisita", "papir", "blekk"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "6010"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for kontorrekvisita"],
            "examples": [
                {
                    "description": "Papir og kontormateriell",
                    "input": {"amount": 350, "description": "kontorrekvisita papir"},
                    "output": {"account": "6010", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_rent_machine_001",
            "rule_name": "Leie av maskiner",
            "description": "Leiekostnader for maskiner og utstyr",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": "leie av maskin",
                },
            ],
            "actions": [
                {"type": "set_account", "value": "5401"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for maskinleie"],
            "examples": [
                {
                    "description": "Leie av gravemaskin",
                    "input": {
                        "amount": 5000,
                        "description": "leie av maskin gravemaskin",
                    },
                    "output": {"account": "5401", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_cleaning_001",
            "rule_name": "Renhold og vakthold",
            "description": "Kostnader til renhold og vakthold",
            "category": "expense",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": ["renhold", "vakt"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "5410"},
                {"type": "set_vat_code", "value": "HIGH"},
                {"type": "set_vat_rate", "value": 25.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": ["Standard MVA-sats 25 % for renhold og vakthold"],
            "examples": [
                {
                    "description": "Rengjøringstjenester",
                    "input": {"amount": 3500, "description": "renhold kontor"},
                    "output": {"account": "5410", "vat_code": "HIGH", "vat_rate": 25.0},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "income_interest_bank_001",
            "rule_name": "Renteinntekt bank",
            "description": "Renteinntekter fra bankinnskudd",
            "category": "income",
            "domain": "tax",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "income"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": "renteinntekt",
                },
            ],
            "actions": [
                {"type": "set_account", "value": "8300"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": ["mva_law_2009"],
            "citations": [
                "Merverdiavgiftsloven § 3-6: Finansielle tjenester er unntatt MVA"
            ],
            "examples": [
                {
                    "description": "Renteinntekt fra bank",
                    "input": {"amount": 150, "description": "renteinntekt bankkonto"},
                    "output": {
                        "account": "8300",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "expense_wages_001",
            "rule_name": "Lønnsutbetaling",
            "description": "Utbetaling av lønn til ansatte",
            "category": "expense",
            "domain": "payroll",
            "priority": 5,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": ["lønn", "salary"],
                },
            ],
            "actions": [
                {"type": "set_account", "value": "5900"},
                {"type": "set_vat_code", "value": "EXEMPT"},
                {"type": "set_vat_rate", "value": 0.0},
            ],
            "source_ids": ["mva_law_2009", "bokforingsloven_2004"],
            "citations": [
                "Merverdiavgiftsloven § 3-6: Lønnskostnader er ikke avgiftspliktige"
            ],
            "examples": [
                {
                    "description": "Månedlig lønn",
                    "input": {"amount": 45000, "description": "lønn ansatt"},
                    "output": {
                        "account": "5900",
                        "vat_code": "EXEMPT",
                        "vat_rate": 0.0,
                    },
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "liability_supplier_001",
            "rule_name": "Leverandørgjeld",
            "description": "Betaling til leverandør",
            "category": "expense",
            "domain": "accounting",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {"field": "transaction_type", "operator": "equals", "value": "expense"},
                {
                    "field": "description",
                    "operator": "contains",
                    "value": "faktura leverandør",
                },
            ],
            "actions": [
                {"type": "set_account", "value": "2400"},
            ],
            "source_ids": ["bokforingsloven_2004"],
            "citations": ["Bokføringsloven: Leverandørgjeld"],
            "examples": [
                {
                    "description": "Betaling av leverandørfaktura",
                    "input": {"amount": 10000, "description": "faktura leverandør"},
                    "output": {"account": "2400"},
                }
            ],
            "valid_from": "2024-01-01",
        },
        {
            "rule_id": "asset_bank_main_001",
            "rule_name": "Overføring driftskonto",
            "description": "Overføring til hovedkonto for daglig drift",
            "category": "transfer",
            "domain": "accounting",
            "priority": 10,
            "is_active": True,
            "conditions": [
                {
                    "field": "transaction_type",
                    "operator": "equals",
                    "value": "transfer",
                },
                {
                    "field": "description",
                    "operator": "contains",
                    "value": "overføring driftskonto",
                },
            ],
            "actions": [
                {"type": "set_account", "value": "1920"},
            ],
            "source_ids": ["bokforingsloven_2004"],
            "citations": ["Bokføringsloven: Banktransaksjoner"],
            "examples": [
                {
                    "description": "Overføring til driftskonto",
                    "input": {"amount": 50000, "description": "overføring driftskonto"},
                    "output": {"account": "1920"},
                }
            ],
            "valid_from": "2024-01-01",
        },
    ]

    for rule_data in rules_data:
        rule_data["created_at"] = timestamp
        rule_data["last_updated"] = timestamp
        rule_data["jurisdiction"] = "NO"

    validated_rules: list[BusinessRule] = []
    for rule_dict in rules_data:
        try:
            validated_rule = BusinessRule(**rule_dict)
            validated_rules.append(validated_rule)
        except Exception as e:
            rule_id = rule_dict.get("rule_id", "unknown")
            logger.error(f"Validation failed for rule {rule_id}: {e}")
            raise

    return validated_rules


def seed_business_rules(silver_dir: Path | None = None) -> int:
    """Generate business rules registry to silver layer."""
    logger.info("Seeding Business Rules Registry")

    if silver_dir is None:
        silver_dir = get_silver_dir()

    silver_dir.mkdir(parents=True, exist_ok=True)

    output_path = silver_dir / "business_rules.json"

    # Get validated typed rules
    rules = get_business_rules()

    # Convert to dicts for JSON serialization
    validated_rules = [rule.model_dump() for rule in rules]

    # Write to JSON
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(validated_rules, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Business Rules: {len(validated_rules)} rules → {output_path.name}")

    # Print summary by category and domain
    category_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    for rule_data in validated_rules:
        cat = rule_data["category"]
        dom = rule_data["domain"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        domain_counts[dom] = domain_counts.get(dom, 0) + 1

    for cat, count in sorted(category_counts.items()):
        logger.info(f"  {cat}: {count} rules")

    return 0
