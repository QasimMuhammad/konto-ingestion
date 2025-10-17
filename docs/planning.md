# Konto AI — Comprehensive Implementation Plan
_Last updated: 2025-09-20 (Europe/Oslo)_

## Context & Core Idea

**Konto** is built on a simple but powerful principle: *“The future of accounting is a conversation.”*  
Instead of complex menu navigation and cryptic VAT codes, users interact through **chat-first workflows**.  
The system combines:

- **Conversational LLM interface** — natural Q&A for sales, expenses, reimbursements.
- **Deterministic rules engine** — ensures compliance with Norwegian law (MVA, SAF‑T, A‑melding).
- **Explainability** — every posting shows WHY (account, VAT, project) and cites its source.
- **Altinn-ready exports** — MVA first, then A‑melding and SAF‑T as the platform matures.
- **Bilingual support** (Norwegian & English).

### Problem We Solve
SMEs without full finance teams struggle with menu-heavy systems.  
Employees entering expenses or sales often face unfamiliar VAT codes and chart-of-account entries.  
This complexity leads to wasted time, errors, and rework. Non‑experts need **step‑by‑step conversational guidance**.

### Our Approach
- **Phase 1**: MVP with synthetic + public data → glossary fine‑tuning, rules engine, and RAG search over official laws/specs.  
- **Phase 2**: Pilot with SMEs using anonymized data → validate workflows, Altinn sandbox exports.  
- **Phase 3**: Production scaling → payroll, multi‑entity, industry‑specific templates.

This plan operationalizes that approach into concrete engineering steps, week by week.

---


## 1. North-Star Vision
- **Chat-first workflow**: Natural conversation replaces menu navigation.
- **Rules engine**: Deterministic compliance with Norwegian accounting/tax law (MVA, SAF-T, A-melding).
- **LLM assist**: Lightweight fine-tuning + glossary; RAG with citations.
- **Explainability**: Every posting explains WHY (account, VAT, project).
- **EU/Norway hosting**: ADLS Gen2, Postgres, Databricks, Purview, Key Vault.

---

## 2. Phased Development

### Phase 1 — MVP (Synthetic + Public Data)
- Data: public regulations (MVA-loven, Regnskapsloven, Bokføringsloven, SAF-T), standard Chart of Accounts, synthetic dialogues.
- Output: demo system with fine-tuned glossary, rules engine for top scenarios, RAG for citations.
- Duration: 12–20 weeks.

### Phase 2 — Pilot (SMEs with anonymized data)
- Data: expense receipts, reimbursements, invoices, bank feeds, payroll cases (with anonymization + consent).
- Output: realistic compliance validation, Altinn sandbox exports, early partner onboarding.

### Phase 3 — Production & Scaling
- Data: larger anonymized SME datasets, accountant feedback loops, industry-specific templates.
- Output: GA-ready platform, multi-entity support, A-melding, mobile polish.

---

## 3. Repository Layout

- **`konto-ingestion`**: ingestion pipelines for tax regs, accounting regs, synthetic data.
- **`konto-kb`**: curated rules engine + knowledge base.
- **`konto-models`**: LoRA training, eval harness, checkpoints.
- **`konto-app`**: assistant API (FastAPI) + web UI.
- **`konto-infra`**: Terraform/Bicep for Azure deployment.

---

## 4. Data Architecture (Bronze–Silver–Gold)

- **Bronze**: raw HTML/PDF/XML with metadata (url, sha256, timestamp).
- **Silver**: normalized JSON (laws, sections, rates, SAF-T nodes, accounts).
- **Gold**: training-ready JSONL (glossary, synthetic chats), curated rules, quality reports.

Schemas will be defined using Pydantic models and exported as JSON Schema.

### Data Versioning with DVC
- **DVC Integration**: Track large data files (Bronze/Silver/Gold) with Git LFS and DVC
- **Data Pipeline**: DVC stages for ingestion → processing → validation → export
- **Reproducibility**: `dvc repro` to rebuild data artifacts from scratch
- **Storage**: Remote storage (S3/Azure) for data artifacts, Git for code
- **Benefits**: 
  - Track data lineage and changes over time
  - Share datasets across team members
  - Reproducible data processing pipelines
  - Efficient storage of large files

---

## 5. Current Progress Summary

### ✅ **Completed (Week 1-2 + Week 3-4 + Week 5 Phase 1)**
- **Bronze Layer**: HTML/PDF sources with SHA256 tracking
- **Silver Layer**: 8 JSON files with 2,049+ validated records
  - `law_sections.json`: 1,804 legal sections (tax + accounting laws)
  - `saft_v1_3_nodes.json`: 142 SAF-T specification nodes
  - `rate_table.json`: 4 VAT rates with categories
  - `amelding_rules.json`: 50 A-meldingen business rules
  - `chart_of_accounts.json`: 42 NS 4102 accounts
  - `business_rules.json`: 30 seed rules with citations
  - `quality_report.json`: Processing statistics
- **Gold Layer (Phase 1)**: Training data export infrastructure ✨ NEW
  - `tax_glossary.jsonl`: 430 samples (351 train / 79 val)
  - `accounting_glossary.jsonl`: 42 samples (25 train / 17 val)
  - Base exporter with split-by-family logic (no leakage)
  - Pydantic schemas: GoldMessage, GoldMetadata, GoldTrainingSample
  - 100% JSONL validation with citations
- **Parsers**: Lovdata HTML, SAF-T PDF, VAT rates, A-meldingen
- **Validation**: 100% Pydantic schema validation success
- **Rules Seeding**: 30 hand-written baseline rules (Week 6-7 expands to 200-300)
- **Data Quality**: Real technical specifications from official sources

### 🔄 **Next Steps (Week 5-7)**
- Week 5 (Phase 2-4): Rule application + synthetic conversations (target: +2,200 samples)
- Week 5 (Phase 5): Eval harness + LoRA training baseline
- Week 6-7: LLM-assisted rule extraction (30 → 200-300 rules)
- Week 7-8: RAG + Rules API with dual-engine architecture

---

## 6. Step-by-Step Implementation

### Week 1–2: Ingestion Foundations ✅ COMPLETED
- ✅ Finalize `sources.csv` with laws/specs (MVA, Regnskapsloven, Bokføringsloven, SAF-T, A-melding, rates).
- ✅ Implement fetchers (requests), parsers (BeautifulSoup/lxml), and normalizers.
- ✅ Produce Bronze & Silver outputs for tax laws, accounting laws, SAF-T, VAT rates, and A-meldingen.
- ✅ **BONUS**: Implemented comprehensive PDF parsing for SAF-T technical specifications.
- ✅ **BONUS**: Added A-meldingen business rules extraction (50 detailed rules).

### Week 3–4: Knowledge Base & Rules ✅ COMPLETED
- ✅ Normalize section paths and extract citations.
- ✅ Build VAT `rate_table` scraper with valid_from/to.
- ✅ Seed Chart of Accounts (NS 4102) with 42 accounts.
- ✅ Create seed Rules Registry with 30 hand-written rules citing silver data.
- ✅ Integrate seed stage into unified ingestion pipeline.
- **Note**: Seed rules provide MVP baseline; Week 6-7 extends to 200-300 rules via LLM-assisted extraction.

### Week 5–6: Training Data & Fine-Tuning 🔄 IN PROGRESS
- ✅ **Phase 1 Complete**: Export infrastructure + glossary datasets (472 samples)
  - Tax glossary: 430 samples (351 train / 79 val)
  - Accounting glossary: 42 samples (25 train / 17 val)
  - Base exporter with family-based splitting
  - Pydantic validation schemas
- 🔄 **Phase 2-4**: Rule application + synthetic conversations
  - Target: +2,200 samples (500 rule-based + 1,700 synthetic)
  - Total target: ~2,700 samples for Milestone A
- 🔄 **Phase 5**: Eval harness + LoRA training
  - 80-item eval set
  - Train baseline LoRA adapter (Phi-3 mini / Mistral-7B)
  - Gate Milestone B on ≥90% glossary accuracy

### Week 6–7: LLM-Assisted Rule Extraction & Validation (HYBRID APPROACH)
**Goal**: Expand Rules Registry from 30 seed rules to 200-300 validated rules using LLM-assisted extraction from law sections.

**Approach: Hybrid Extraction**
- **Input**: 1,804 law sections from `law_sections.json` (MVA, Regnskapsloven, Bokføringsloven, Skatteloven)
- **Output**: 200-300 validated business rules with confidence scores and human review

**Tasks**:
1. **LLM Extraction Pipeline**
   - Prompt GPT-4/Claude to extract rules from law sections
   - Output structured JSON: conditions, actions, confidence, ambiguities
   - Cross-reference with `rate_table.json` and `chart_of_accounts.json`

2. **Confidence-Based Filtering**
   - **High confidence** (50-100 rules): Clear, unambiguous → Auto-approve
   - **Medium confidence** (150-250 rules): Needs review → Human validation queue
   - **Low confidence** (50-100 rules): Ambiguous → Manual creation or skip
   - **Not rule-worthy** (1,400+ sections): Use for RAG only (definitions, penalties, procedures)

3. **Validation & Review**
   - Cross-reference validation (no conflicts between rules)
   - VAT rate validation (match official `rate_table.json`)
   - Account validation (all referenced accounts exist in `chart_of_accounts.json`)
   - Accountant sign-off on medium-confidence rules

4. **Output**
   - `data/gold/rules/validated_rules.json`: 200-300 production-ready rules
   - `data/gold/rules/review_queue.json`: Rules pending human review
   - `data/gold/rules/extraction_report.json`: Confidence scores, ambiguities, coverage metrics

**Key Deliverables**:
- LLM extraction script: `scripts/extract_rules_from_laws.py`
- Validation script: `scripts/validate_extracted_rules.py`
- Review dashboard: HTML report showing rule coverage by domain/category
- Expanded Rules Registry (10x increase from Week 3-4 seed)

**Acceptance Criteria**:
- ≥200 validated rules with citations to silver layer
- ≥90% of rules have `confidence: high` or manually reviewed
- 100% cross-reference validation (no orphaned accounts/VAT codes)
- Coverage report shows rules for top 50 transaction types
- Zero conflicting rules in production set

**Risk Mitigation**:
- Dual system: LLM-extracted rules + RAG fallback for edge cases
- Human review queue prevents auto-deployment of ambiguous rules
- Confidence scores enable gradual rollout (high-confidence first)
- Accountant validation ensures compliance accuracy

### Week 7–8: RAG & Rules API
**Prerequisites**:
- Week 3-4: Seed rules (30 baseline rules) ✅
- Week 6-7: Expanded rules (200-300 validated rules) ✅
- Week 5-6: Gold training data and LoRA adapters ✅

**Dual-Engine Architecture**:
```
┌─────────────────────────────────────────────────┐
│            User Transaction                      │
│     "Hotel expense 1,200 NOK in Oslo"           │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
        ▼                  ▼
┌──────────────┐   ┌──────────────────────┐
│ Rules Engine │   │   RAG + LLM          │
│ (Deterministic)  │   (Conversational)   │
│              │   │                      │
│ 200-300      │   │ 1,804 law sections   │
│ validated    │   │ Vector search        │
│ rules        │   │ GPT-4/Claude         │
│              │   │                      │
│ Fast (10ms)  │   │ Slower (2-3s)        │
│ 100% accurate│   │ ~90% accurate        │
└──────┬───────┘   └──────────┬───────────┘
       │                      │
       │ account=7140         │ "§ 5-3 says..."
       │ VAT=12%             │ + explanation
       │                      │
       └──────┬───────────────┘
              │
              ▼
    ┌──────────────────┐
    │  User Response   │
    │  + Citation      │
    └──────────────────┘
```

**When to use each:**
- **Rules Engine**: Known scenarios (hotel, salary, office supplies) → instant, deterministic
- **RAG + LLM**: Edge cases, questions, ambiguous transactions → slower, probabilistic
- **Fallback chain**: Rules → RAG → Human review (if confidence < 70%)

**Tasks**:
- Implement RAG service (FastAPI): `/ask` returns answer + citations.
- Implement rules engine endpoint: `/posting_proposal` returns account + VAT code.
- Ensure eval passes: ≥90% on glossary basics.

### Week 9–10: Demo & Observability
- End-to-end demo: upload synthetic invoice → parse → rules engine → LLM explanation → Altinn-ready export.
- Add logging, dashboards (coverage, latency, costs).

### Week 11–12: Azure Readiness
- Infra as code: ADLS Gen2, Postgres(pgvector), Event Hubs, Databricks, Purview, Key Vault.
- Security: Norway residency, RBAC, private endpoints, encryption, deletion workflows.
- Cost governance & DR plan (Norway East/West).

### Week 13–14: DVC Data Versioning (NEW)
- **DVC Setup**: Initialize DVC, configure remote storage (Azure Blob/S3)
- **Data Pipeline**: Convert ingestion scripts to DVC stages
- **Versioning**: Track Bronze/Silver/Gold data artifacts with Git LFS
- **Reproducibility**: `dvc repro` pipeline for end-to-end data processing
- **Benefits**: 
  - Track data lineage and changes over time
  - Share datasets across team members
  - Reproducible data processing pipelines
  - Efficient storage of large files

---

## 7. Risks & Mitigations
- **Legal text drift**: nightly diffs, effective_from/to fields, re-index pipeline.
- **Outdated VAT rates**: never bake numbers into LLM; runtime lookup via rate_table.
- **Parser fragility**: snapshot tests, resilient selectors, CI checks.
- **Hallucinations**: rules engine as ground truth; LLM for language + reasoning only.

---

## 8. Acceptance Criteria (Phase 1 MVP)
- **Bronze+Silver**: ✅ Outputs for all laws, SAF-T, VAT rates, A-melding (2,049 records)
- **Gold datasets**: 150–300 glossary entries, 100+ synthetic chats (Week 5-6)
- **Rules engine**:
  - ✅ Week 3-4: 30 baseline rules with citations to silver data
  - Week 6-7: 200-300 validated rules covering top 50 transaction types
- **LoRA model**: ≥90% accuracy on glossary eval (Week 5-6)
- **Demo**: Runs with `uv sync` + `uv run ingest-all` on a clean machine

**Updated for Week 3-4 completion**: Rules seeding phase complete. Week 6-7 will expand to production-ready rule set.

---

## 9. Next Steps (Post Week 3-4)
1. ✅ ~~Upload `konto-ingestion` to GitHub with plan~~ (Complete)
2. ✅ ~~Implement fetch & parse logic for all sources~~ (Complete)
3. ✅ ~~Run ingestion and verify Bronze/Silver artifacts~~ (Complete - 2,049 records)
4. ✅ ~~Seed Chart of Accounts and baseline rules~~ (Complete - 42 accounts, 30 rules)
5. **Week 5-6**: Export Gold JSONL training datasets (tax/accounting glossary, synthetic chats)
6. **Week 6-7**: LLM-assisted rule extraction (expand 20 → 200-300 validated rules)
7. **Week 7-8**: Build RAG service + Rules API with dual-engine architecture
8. **Week 9-10**: End-to-end demo with Altinn-ready export

---

---

# Appendix A — Weeks 1–4 Low‑Level Implementation Details

# Konto AI — Weeks 1–4 Low‑Level Implementation Plan
_Last updated: 2025‑09‑20 (Europe/Oslo)_

This document breaks down **Weeks 1–2** and **Weeks 3–4** into **developer‑ready, Cursor‑friendly tasks**. Each task includes: scope, files to touch, function signatures, acceptance criteria, and `uv` run commands.

> Repos assumed: `konto-ingestion` (local stubs already provided), `konto-models` (to be created in Week 3–4).

---

## Week 1–2 — Ingestion Foundations & Silver Hardening

### T1 — Implement real HTTP fetcher (requests) with idempotent snapshots
**Why**: Replace `fake_fetch()` and store raw HTML in **Bronze** with SHA256; skip unchanged.

**Files to touch**
- `scripts/ingest_tax_regs.py`
- `scripts/ingest_accounting_regs.py`
- `modules/utils.py` (add HTTP + idempotency helpers)

**Implementation**
```python
# modules/utils.py
import requests
from pathlib import Path
from .utils import log, sha256_bytes  # if in same file, refactor

def http_get(url: str, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "KontoIngestionBot/0.1 (+contact@example.com)"}
    r = requests.get(url, timeout=timeout, headers=headers)
    r.raise_for_status()
    return r.content

def write_bronze_if_changed(path: Path, content: bytes) -> dict:
    h = sha256_bytes(content)
    old = path.read_bytes() if path.exists() else None
    if not old or sha256_bytes(old) != h:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        changed = True
    else:
        changed = False
    return {"sha256": h, "changed": changed}
```

**Integrate fetch into scripts**
```python
# scripts/ingest_tax_regs.py (inside loop)
from modules.utils import http_get, write_bronze_if_changed
raw = http_get(url)
meta = write_bronze_if_changed(BRONZE / f"{sid}.html", raw)
```

**Acceptance Criteria**
- Repeated runs do **not** rewrite Bronze unless remote content changed.
- On network failure, script raises and exits with non‑zero status.

**Run**
```bash
uv run scripts/ingest_tax_regs.py --sources configs/sources.csv
```

---

### T2 — Parse Lovdata HTML into section records
**Why**: Populate **Silver** `*_sections.json` with `section_id`, `path`, `heading`, `text_plain`.

**Files to touch**
- `modules/parsers/lovdata_parser.py`
- `modules/cleaners/normalize_text.py` (extend normalization as needed)
- `tests/test_lovdata_parser.py` (new)

**Implementation sketch**
```python
# modules/parsers/lovdata_parser.py
from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup

@dataclass
class Section:
    law_id: str
    section_id: str      # e.g., "§ 8-1"
    path: str            # e.g., "Kapittel 8 § 8-1"
    heading: str
    text_plain: str

def parse_lovdata_html(html: str, law_id: str) -> List[Section]:
    soup = BeautifulSoup(html, "lxml")
    # Heuristic selectors; adjust once you inspect real HTML:
    # - find chapter headings
    # - find section anchors and bodies
    sections: List[Section] = []
    for sec in soup.select("section, div.paragraf"):  # replace with concrete CSS
        sid = (sec.get("id") or "").strip()           # or parse anchor text
        heading_el = sec.find(["h2","h3","h4"])
        heading = heading_el.get_text(" ", strip=True) if heading_el else ""
        body = sec.get_text(" ", strip=True)
        # Derive human path if available (chapter + section)
        path = heading if "§" in heading else f"{law_id} {sid}"
        if sid or "§" in heading:
            sections.append(Section(
                law_id=law_id,
                section_id=heading.split("§",1)[-1].strip() if "§" in heading else sid,
                path=path,
                heading=heading,
                text_plain=body,
            ))
    return sections
```

**Edge cases**
- Sections without explicit headings → derive from nearest heading.
- Inline footnotes → strip; keep references as plain text.
- Encoding & whitespace normalization (`æøå`, non‑breaking spaces).

**Tests**
```python
# tests/test_lovdata_parser.py
from modules.parsers.lovdata_parser import parse_lovdata_html
def test_minimal_parse():
    html = "<html><div class='paragraf' id='par_8-1'><h3>§ 8-1 Fradrag</h3><p>Tekst...</p></div></html>"
    out = parse_lovdata_html(html, "mva_law_1999")
    assert out and "8-1" in out[0].section_id
```

**Acceptance Criteria**
- For a real Lovdata page, ≥ 20 section entries parsed with non‑empty `text_plain`.
- No exceptions on Unicode or nested markup.

**Run**
```bash
uv run scripts/ingest_tax_regs.py --sources configs/sources.csv
```

---

### T3 — SAF‑T spec node extraction
**Why**: Populate **Silver** `saft_v1_3_nodes.json` with `node_path`, `cardinality`, `description`.

**Files to touch**
- `scripts/ingest_accounting_regs.py`
- `modules/parsers/saft_parser.py`
- `tests/test_saft_parser.py`

**Implementation sketch**
```python
# modules/parsers/saft_parser.py
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List

@dataclass
class SpecNode:
    spec: str
    version: str
    node_path: str
    cardinality: str
    description: str

def parse_saft_page(html: str, version: str) -> List[SpecNode]:
    soup = BeautifulSoup(html, "lxml")
    nodes: List[SpecNode] = []
    for row in soup.select("table tr"):
        cols = [c.get_text(' ', strip=True) for c in row.select("td")]
        if len(cols) >= 3:
            path, card, desc = cols[0], cols[1], cols[2]
            nodes.append(SpecNode("SAF-T", version or "1.3", path, card, desc))
    return nodes
```

**Acceptance Criteria**
- At least 30 nodes extracted on first run.
- No duplicate `node_path` values in output (or deduplicated).

**Run**
```bash
uv run scripts/ingest_accounting_regs.py --sources configs/sources.csv --only saft_v1_3
```

---

### T4 — VAT “satser” scraper → `rate_table` with validity
**Why**: Keep volatile numbers out of the model and in a queryable table.

**Files to touch**
- `scripts/ingest_tax_regs.py` (or new `scripts/ingest_rates.py`)
- `modules/parsers/rates_parser.py` (new)
- `tests/test_rates_parser.py`

**Implementation sketch**
```python
# modules/parsers/rates_parser.py
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict

def parse_mva_rates(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    # Expect a table with columns: type, percent, valid_from, valid_to?
    for row in soup.select("table tr"):
        cols = [c.get_text(' ', strip=True) for c in row.select('td')]
        if len(cols) >= 2 and '%' in cols[1]:
            kind = cols[0].lower()   # e.g., "standard", "lav", "null"
            value = cols[1]
            out.append({
                "kind": kind,
                "value": value,
                "valid_from": None,  # fill if available or default to today
                "valid_to": None
            })
    return out
```

**Acceptance Criteria**
- JSON array with keys: `kind`, `value`, `valid_from`, `valid_to`, `source_url`.
- Script writes `silver/rate_table.json` and is idempotent.

**Run**
```bash
uv run scripts/ingest_tax_regs.py --sources configs/sources.csv --only mva_rates
```

---

### T5 — Pydantic schemas for Silver entities
**Why**: Enforce structure and prepare for JSON Schema export.

**Files to touch**
- `modules/schemas.py` (new)
- `scripts/validate_silver.py` (new)
- `tests/test_schemas.py`

**Implementation sketch**
```python
# modules/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class LawSection(BaseModel):
    law_id: str
    section_id: str
    path: str
    heading: str
    text_plain: str
    source_url: str
    sha256: str

class SpecNode(BaseModel):
    spec: str
    version: str
    node_path: str
    cardinality: str
    description: str
    source_url: str
    sha256: str
```

**Acceptance Criteria**
- Validation passes for generated Silver files; invalid rows fail fast.
- JSON Schema artifacts written to `schemas/` folder.

**Run**
```bash
uv run scripts/ingest_tax_regs.py && uv run scripts/ingest_accounting_regs.py
```

---

### T6 — Testing & CI wiring
**Why**: Prevent regressions as site HTML changes.

**Files to touch**
- `tests/` (pytest)
- `.github/workflows/ci.yml` (optional now)

**Acceptance Criteria**
- `pytest -q` passes locally.
- Basic CI workflow installs with `uv sync` and runs tests.

---

## Week 3–4 — Gold Exporters, Glossary SFT, and Eval

### T7 — Curate Rules Registry (JSON) with citations
**Why**: Deterministic proposals at runtime; LLM provides explanations, not truth source.

**Files to touch**
- `gold/kb/rules.json` (output)
- `modules/rules/registry.py` (optional helper)

**Rule format (example)**
```json
{
  "rule_id": "vat_hotel_no_low_rate",
  "if": [{"domain":"expense","category":"hotel","country":"NO"}],
  "then": [{"account":"7140","vat_code":"LOW_RATE"}],
  "source_ids": ["mva_law_1999_§8-1","mva_rates"],
  "valid_from": "2025-01-01"
}
```

**Acceptance Criteria**
- 15–25 rules with `source_ids` resolvable to `silver` docs.
- JSON schema for rules validates.

---

### T8 — Build Gold exporters for SFT JSONL (tax, accounting, client‑synth)
**Why**: Reproducible training files, short outputs, with metadata.

**Files to touch**
- `modules/exporters/jsonl_exporter.py` (extend)
- `scripts/export_gold_sft.py` (new)
- **Inputs**: `silver/law_sections.json`, curated `gold/kb/rules.json`
- **Outputs**:
  - `gold/train/tax_glossary_train.jsonl`
  - `gold/train/accounting_glossary_train.jsonl`
  - `gold/train/client_synth_chat_train.jsonl`
  - (and `val` variants)

**Implementation sketch**
```python
# scripts/export_gold_sft.py
from pathlib import Path
import json
from modules.exporters.jsonl_exporter import write_jsonl

def build_tax_glossary(sections_path: Path):
    sections = json.loads(Path(sections_path).read_text(encoding='utf-8'))
    rows = []
    for s in sections[:200]:  # sample or filter by regex
        term = s["heading"].split("§")[0].strip() if "§" in s["heading"] else s["heading"]
        if not term or len(s["text_plain"]) < 50: continue
        rows.append({
          "messages":[
            {"role":"system","content":"Du er en norsk regnskapsassistent. Svar kort og presist."},
            {"role":"user","content":f"Definer kort: '{term}'"},
            {"role":"assistant","content":f"{term}: {s['text_plain'][:200]}..."}
          ],
          "metadata":{"domain":"tax","task":"glossary_define","source_scope":"public_rules","source_ids":[s["law_id"]], "locale":"nb-NO"}
        })
    return rows

def main():
    outdir = Path("data/gold/train"); outdir.mkdir(parents=True, exist_ok=True)
    tax_rows = build_tax_glossary(Path("data/silver/mva_law_1999_sections.json"))
    write_jsonl(outdir / "tax_glossary_train.jsonl", tax_rows)

if __name__ == "__main__":
    main()
```

**Acceptance Criteria**
- JSONL validates; random sample shows Norwegian, short answers, proper metadata.
- Train/val split created by **term family**, not random line split.

**Run**
```bash
uv run scripts/export_gold_sft.py
```

---

### T9 — Eval set & harness
**Why**: Quantify glossary mastery and application.

**Files to touch**
- `gold/eval/*.jsonl` (question sets)
- `scripts/eval_sample.py` (sanity check)

**Eval examples**
- “Hvilken MVA‑kode for hotell i Norge?”
- “Forskjell på kreditnota og korrigert faktura?”
- “EU SaaS (Adobe) — omvendt avgiftsplikt?”

**Acceptance Criteria**
- Eval set with ≥80 items (balanced across tax/accounting/application).
- Harness prints accuracy on exact label + presence of `[kilder: …]` tags (if used).

---

### T10 — `konto-models`: Minimal LoRA training & inference
**Why**: Train adapters and test on eval set.

**Files to create (new repo or subfolder)**
- `scripts/train_lora_sft.py` (already provided in earlier bundle — copy here)
- `scripts/infer_lora.py` (new; loads base + adapters, formats chat, prints answer)

**Run**
```bash
# In konto-models
uv sync  # if you manage deps via uv; otherwise pip/conda
export BASE_MODEL=phi-3-mini-4k-instruct  # or mistralai/Mistral-7B-Instruct-v0.3
export TRAIN_FILE=../konto-ingestion/data/gold/train/tax_glossary_train.jsonl
export EVAL_FILE=../konto-ingestion/data/gold/train/accounting_glossary_train.jsonl
python scripts/train_lora_sft.py
python scripts/infer_lora.py --prompt "Definer kort: kreditnota"
```

**Acceptance Criteria**
- Training completes on a small subset with falling loss.
- Inference returns concise Norwegian answers consistent with rules.

---

## Prompts for Cursor Agent (ready to paste)

### Prompt A — Implement HTTP fetch & idempotent Bronze writes
> **Goal**: Replace `fake_fetch()` and add `http_get()` + `write_bronze_if_changed()` utilities.  
> **Files**: `modules/utils.py`, `scripts/ingest_tax_regs.py`, `scripts/ingest_accounting_regs.py`.  
> **Done when**: Re‑running ingestion without site change performs no writes; Bronze files contain real HTML.

### Prompt B — Implement Lovdata HTML → sections
> **Goal**: Parse section headings and bodies into `Section` records.  
> **Files**: `modules/parsers/lovdata_parser.py`, `tests/test_lovdata_parser.py`.  
> **Done when**: At least 20 sections parsed with non‑empty text from a real page.

### Prompt C — SAF‑T spec node extraction
> **Goal**: Parse table rows into `SpecNode` entries.  
> **Files**: `modules/parsers/saft_parser.py`, `tests/test_saft_parser.py`.  
> **Done when**: ≥30 nodes extracted; no duplicates.

### Prompt D — VAT rates scraper
> **Goal**: Create `rate_table.json` with kinds, values, and validity.  
> **Files**: `modules/parsers/rates_parser.py`, `scripts/ingest_tax_regs.py`.  
> **Done when**: JSON exists with `standard|lav|null` entries and dates if available.

### Prompt E — Pydantic schemas & validators
> **Goal**: Validate Silver outputs and export JSON Schema.  
> **Files**: `modules/schemas.py`, `scripts/validate_silver.py`.  
> **Done when**: All Silver JSON files pass validation; schemas exported.

### Prompt F — Export Gold SFT JSONL
> **Goal**: Build tax/accounting/client‑synth SFT files with short answers.  
> **Files**: `scripts/export_gold_sft.py`, `modules/exporters/jsonl_exporter.py`.  
> **Done when**: Files exist under `data/gold/train/` and pass a JSONL sanity check.

### Prompt G — DVC Data Versioning Setup
> **Goal**: Initialize DVC and convert data processing to reproducible pipeline.  
> **Files**: `dvc.yaml`, `.dvc/`, `data/` (tracked), remote storage config.  
> **Done when**: `dvc repro` rebuilds entire data pipeline from scratch; data artifacts versioned.

---

## Command Cheatsheet

```bash
# Install dependencies
uv sync

# === Unified Ingestion Pipeline (Week 3-4 Refactored) ===

# Seed static data (Chart of Accounts + Business Rules)
uv run ingest_from_sources.py seed

# Ingest from external sources (Bronze + Silver)
uv run ingest_from_sources.py ingest

# Full pipeline (Seed + Ingest)
uv run ingest_from_sources.py all

# List available sources
uv run ingest_from_sources.py list

# Domain-specific ingestion
uv run ingest_from_sources.py ingest --domain tax
uv run ingest_from_sources.py ingest --domain accounting
uv run ingest_from_sources.py ingest --domain reporting

# Bronze only (skip Silver processing)
uv run ingest_from_sources.py ingest --bronze-only

# With validation (for seed or all commands)
uv run ingest_from_sources.py seed --with-validation
uv run ingest_from_sources.py all --with-validation

# === Validation & Quality ===

# Validate seed data (Chart of Accounts + Business Rules)
uv run ingest_from_sources.py seed --with-validation

# Validate Silver layer
uv run scripts/validate_silver.py

# === Testing ===

# Run tests
uv run pytest -q

# Run all tests with coverage
uv run tests/run_all_tests.py

# === Future: DVC Commands (Week 13-14) ===

dvc init
dvc remote add -d storage azure://container/path
dvc add data/bronze data/silver data/gold
dvc push  # Upload to remote storage
dvc pull  # Download from remote storage
dvc repro  # Rebuild data pipeline
```

---

## Definition of Done (Weeks 1–4)

- **Bronze**: ✅ Real HTML snapshots with SHA hashes; idempotent writes.
- **Silver**: ✅ Validated `*_sections.json`, `*_nodes.json`, `rate_table.json`, `chart_of_accounts.json`, `business_rules.json`.
- **Gold**: reproducible JSONL for SFT (tax, accounting, client‑synth) + eval set (Week 5-6).
- **Rules**:
  - ✅ **Seed phase (Week 3-4)**: 30 baseline rules with citations, resolvable to Silver
  - 🔄 **Expansion phase (Week 6-7)**: 200-300 LLM-extracted rules with validation
- **Training**: LoRA adapters trained on a small base; inference works on sample prompts (Week 5-6).
- **Docs**: ✅ README updated; this plan kept in repo root.

**Note**: Week 3-4 delivers MVP baseline. Production system requires Week 6-7 rule expansion.

---