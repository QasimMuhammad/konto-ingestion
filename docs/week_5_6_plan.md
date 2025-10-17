# Week 5-6: Gold Layer Training Data Export

_Last updated: 2025-10-17_  
_Status: Phase 1-4 Complete, Phase 5.1 Complete (Orchestrator)_

**✅ Completed**:
- Phase 1: Base infrastructure + glossary exporters (472 samples: 430 tax, 42 accounting)
- Phase 2: Evaluation harness + 50 curated eval samples (30 tax, 20 accounting)
- Phase 3: Rule application exporter (399 samples: 324 train, 75 val)
- Phase 4: Synthetic conversation exporter (837 samples: 459 train, 378 val)
- Phase 5.1: Export orchestrator (runs all exporters + aggregates statistics)

**📊 Final Milestone A Dataset**:
- Training: 1,159 samples
- Validation: 549 samples
- Eval/Test: 50 samples
- **Grand Total: 1,758 samples**

**⏸️ Deferred (Requires GPU)**:
- Phase 5.2: LoRA training baseline (for future implementation)

## 🎯 Overview

**Goal**: Generate high-quality JSONL training datasets from Silver layer data for LoRA fine-tuning of Norwegian accounting/tax LLM.

**Scope**: Tax glossaries, accounting glossaries, rule-based posting proposals, and synthetic conversations.

**Success Metric**: ≥90% accuracy on eval set with 3,500 initial samples (Milestone A).

---

## 📊 Milestone-Based Approach

### Milestone A: Pipeline Validation (Week 5, Days 1-6)
**Target**: 3,500 total samples (2,840 train + 660 val)

**Objectives**:
- Validate export → train → eval pipeline end-to-end
- Test JSONL format hygiene and Pydantic validation
- Train baseline LoRA adapter
- Establish eval harness with 80-item test set
- Gate Milestone B on ≥90% glossary accuracy

**Dataset Breakdown**:
| Dataset | Train | Val | Total | Source |
|---------|-------|-----|-------|--------|
| Tax glossary | 800 | 200 | 1,000 | 1,804 law sections (filtered) |
| Accounting glossary | 240 | 60 | 300 | 142 SAF-T + 42 CoA entries |
| Rule application | 400 | 100 | 500 | 30 rules × 15 variations |
| Synthetic chat | 1,400 | 300 | 1,700 | Generated from templates |
| **TOTAL** | **2,840** | **660** | **3,500** | |

### Milestone B: Scaling (Week 6+)
**Target**: 10-15k samples  
**Trigger**: Milestone A eval shows ≥90% glossary accuracy  
**Focus**: Expand synthetic conversations, add edge cases, more rule variations

### Milestone C: Pilot Quality (Week 7-8+)
**Target**: 20-50k samples  
**Trigger**: Milestone B eval shows ≥93% glossary, ≥85% rule accuracy  
**Focus**: Production-ready dataset with LLM-extracted rules (200-300 total)

---

## 🔧 JSONL Schema Specification

### Pydantic Models (add to `modules/schemas.py`)

```python
class GoldMessage(BaseModel):
    """Single message in OpenAI chat format."""
    role: Literal["system", "user", "assistant"]
    content: str

class GoldMetadata(BaseModel):
    """Metadata for Gold training samples."""
    domain: Literal["tax", "accounting", "reporting", "payroll"]
    task: Literal["glossary_define", "posting_proposal", "conversation", "vat_question"]
    source_ids: list[str] = Field(..., min_length=1)
    locale: Literal["nb-NO", "en-US"] = "nb-NO"
    split: Literal["train", "val"] = "train"
    rule_ids: list[str] | None = None
    conversation_type: str | None = None
    turns: int | None = None
    created_at: str | None = None

class GoldTrainingSample(BaseModel):
    """Complete Gold layer training sample."""
    messages: list[GoldMessage] = Field(..., min_length=2)
    metadata: GoldMetadata
    
    @field_validator("messages")
    @classmethod
    def validate_message_flow(cls, v: list[GoldMessage]) -> list[GoldMessage]:
        """Ensure system -> user -> assistant pattern."""
        if len(v) < 2:
            raise ValueError("Must have at least 2 messages")
        if v[0].role != "system":
            raise ValueError("First message must be system")
        return v
```

### Example Output Format

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Du er en norsk regnskapsassistent. Svar kort og presist med kildehenvisninger."
    },
    {
      "role": "user",
      "content": "Hva betyr 'omvendt avgiftsplikt'?"
    },
    {
      "role": "assistant",
      "content": "Omvendt avgiftsplikt betyr at kjøperen (ikke selgeren) må beregne og innbetale merverdiavgiften. Dette gjelder typisk for kjøp av tjenester fra utlandet. [§ 11-1 merverdiavgiftsloven]"
    }
  ],
  "metadata": {
    "domain": "tax",
    "task": "glossary_define",
    "source_ids": ["mva_law_2009_PARAGRAF_11-1"],
    "locale": "nb-NO",
    "split": "train",
    "created_at": "2025-10-16T10:30:00Z"
  }
}
```

---

## 📁 File Structure

```
data/gold/
├── train/
│   ├── tax_glossary_train.jsonl           (800 samples)
│   ├── accounting_glossary_train.jsonl    (240 samples)
│   ├── rule_application_train.jsonl       (400 samples)
│   └── synthetic_chat_train.jsonl         (1,400 samples)
├── val/
│   ├── tax_glossary_val.jsonl             (200 samples)
│   ├── accounting_glossary_val.jsonl      (60 samples)
│   ├── rule_application_val.jsonl         (100 samples)
│   └── synthetic_chat_val.jsonl           (300 samples)
├── eval/
│   ├── tax_glossary_eval.jsonl            (30 items)
│   ├── accounting_glossary_eval.jsonl     (20 items)
│   ├── rule_application_eval.jsonl        (20 items)
│   ├── conversation_eval.jsonl            (10 items)
│   └── README.md                          (evaluation criteria)
└── metadata/
    ├── export_stats.json                  (generation statistics)
    └── quality_report.json                (quality assessment)

scripts/
├── export_gold_glossary.py                (Tax + Accounting glossaries)
├── export_gold_rules.py                   (Rule-based posting proposals)
├── export_gold_synthetic.py               (Synthetic conversations)
├── export_gold_all.py                     (Orchestrator)
└── eval_glossary.py                       (Evaluation harness)

modules/
├── exporters/
│   ├── __init__.py
│   ├── base_exporter.py                   (Base class with split logic)
│   ├── glossary_exporter.py               (Glossary-specific logic)
│   ├── rule_exporter.py                   (Rule variation generator)
│   └── synthetic_exporter.py              (Template-based generator)
└── gold_templates.py                      (Conversation templates)
```

---

## 🔨 Implementation Plan (Milestone A)

### Phase 1: Foundation (Days 1-2)

#### Task 1.1: Create Base Infrastructure
**Files**: `modules/exporters/base_exporter.py`

**Features**:
- Abstract base class for all exporters
- Train/val split logic with family isolation
- Quality checks (deduplication, length validation)
- Metadata generation

**Split Strategy**:
```python
def split_by_family(items, split_ratio=0.8):
    """
    Split samples by semantic families to avoid leakage.
    
    Examples:
    - Tax glossary: Split by law chapters (Kapittel 1, 2, 3...)
    - Accounting: Split by account classes (1xxx, 2xxx, 7xxx...)
    - Rules: Split by rule families (expense_hotel_*, income_sales_*)
    - Synthetic: Split by conversation templates
    """
    # Group by family key
    families = group_by(items, key=extract_family_key)
    
    # Shuffle families (not items within families)
    family_ids = list(families.keys())
    random.seed(42)  # Reproducible splits
    random.shuffle(family_ids)
    
    # Split at family boundary
    split_idx = int(len(family_ids) * split_ratio)
    train_families = family_ids[:split_idx]
    val_families = family_ids[split_idx:]
    
    # Aggregate items
    train = [item for fam in train_families for item in families[fam]]
    val = [item for fam in val_families for item in families[fam]]
    
    return train, val
```

#### Task 1.2: Add Gold Schemas to Pydantic
**Files**: `modules/schemas.py`

Add `GoldMessage`, `GoldMetadata`, `GoldTrainingSample` classes (see schema section above).

#### Task 1.3: Implement Tax Glossary Exporter
**Files**: `scripts/export_gold_glossary.py`

**Logic**:
1. Load `law_sections.json` (1,804 sections)
2. Filter sections suitable for glossary:
   - Has clear heading with terminology
   - Text length between 100-800 characters
   - Exclude procedural sections (contains keywords: "søknad", "klage", "vedtak")
   - Prioritize definitions (heading contains: "definisjon", "virkeområde", "gjelder")
3. Generate Q&A pairs:
   - Extract term from heading (before/after §)
   - Format question: "Hva betyr '{term}'?" or "Forklar '{term}'"
   - Use text_plain as answer (trim to 150-250 tokens)
   - Add citation: "[§ X-Y {law_title}]"
4. Split by law chapters
5. Output train/val JSONL

**Target**: 800 train + 200 val = 1,000 samples

#### Task 1.4: Implement Accounting Glossary Exporter
**Files**: `scripts/export_gold_glossary.py` (extend)

**Logic**:
1. Load `saft_v1_3_nodes.json` (142 nodes) + `chart_of_accounts.json` (42 entries)
2. Generate two types:
   - **SAF-T nodes**: "Hva er '{node_label}' i SAF-T?" → description
   - **Chart of Accounts**: "Hva er konto {account_id}?" → label + description + examples
3. Split by account class / node level
4. Output train/val JSONL

**Target**: 240 train + 60 val = 300 samples

### Phase 2: Evaluation Harness (Day 3)

#### Task 2.1: Create Eval Dataset
**Files**: `data/gold/eval/*.jsonl`

**Manual curation** (80 items total):
- 30 tax glossary questions (diverse coverage: MVA, definitions, rates, procedures)
- 20 accounting glossary (SAF-T + Chart of Accounts)
- 20 rule application scenarios (hotel, food, office supplies, EU transactions)
- 10 conversation flows (multi-turn dialogues)

**Format**: Same as training JSONL, but with `expected_output` field for grading.

#### Task 2.2: Implement Eval Harness
**Files**: `scripts/eval_glossary.py`

**Features**:
- Load eval set
- Run inference (LoRA adapter or base model)
- Grade responses:
  - Exact match (strict)
  - Semantic similarity (sentence-transformers)
  - Citation presence (regex check)
  - Length appropriateness (100-300 tokens)
- Generate report: accuracy, avg_length, citation_coverage

**Baseline**: Run eval on GPT-4 zero-shot → expect ~70-80% accuracy

#### Task 2.3: Document Eval Criteria
**Files**: `data/gold/eval/README.md`

Define rubrics for:
- Glossary accuracy (term definition matches expected)
- Citation quality (source_ids resolvable to Silver)
- Answer length (not too verbose or terse)
- Norwegian language quality (manual spot check)

### Phase 3: Rule Application (Day 4)

#### Task 3.1: Implement Rule Exporter
**Files**: `scripts/export_gold_rules.py`

**Logic**:
1. Load `business_rules.json` (30 rules with examples)
2. For each rule, generate 15 variations:
   - Vary amounts (500, 1000, 1500, 2000, 2500, etc.)
   - Vary descriptions (formal, casual, detailed, minimal)
   - Vary context (business trip, office purchase, client meeting)
3. Format as transaction description → posting proposal with citations
4. Split by rule families (expense_hotel_*, expense_food_*, etc.)
5. Output train/val JSONL

**Sample Variations**:
```python
# Base rule: expense_hotel_no_001
variations = [
    {
        "amount": 1200,
        "desc": "Hotellovernatting forretningsreise Oslo",
        "detail_level": "minimal"
    },
    {
        "amount": 1850,
        "desc": "Overnatting på Radisson Blu Oslo - 2 netter inkl. frokost",
        "detail_level": "detailed"
    },
    {
        "amount": 950,
        "desc": "hotell",
        "detail_level": "terse"  # Test robustness
    },
    # ... 12 more variations
]
```

**Target**: 400 train + 100 val = 500 samples

### Phase 4: Synthetic Conversations (Day 5)

#### Task 4.1: Create Conversation Templates
**Files**: `modules/gold_templates.py`

**Template Types** (5-7 templates):
1. **Expense entry**: User describes expense → AI asks clarifying questions → posting proposal
2. **VAT question**: User asks about VAT rates → AI explains with citations
3. **Account selection**: User uncertain about account → AI guides with examples
4. **Correction flow**: User made mistake → AI helps correct
5. **Multi-item transaction**: Multiple line items → AI processes each

**Example Template**:
```python
TEMPLATE_EXPENSE_ENTRY = {
    "system": "Du er Konto AI, en hjelpsom regnskapsassistent for norske bedrifter.",
    "turns": [
        {
            "user": "Jeg har en {category} på {amount} kr fra {location}. Hvordan kontererer jeg den?",
            "assistant": "For å kontere {category}regningen riktig, trenger jeg litt mer informasjon:\n- Er dette for en forretningsreise eller privat?\n- Er leverandøren norsk eller utenlandsk?"
        },
        {
            "user": "Det er en norsk {context}",
            "assistant": "Takk! Da konteres det slik:\n- Konto: {account} ({account_label})\n- MVA: {vat_rate}% ({vat_code})\n- Beløp eksl. MVA: {amount_ex_vat} kr\n- MVA-beløp: {vat_amount} kr\n\n{explanation} [{citation}]. Er det noe annet jeg kan hjelpe med?"
        }
    ],
    "placeholders": ["category", "amount", "location", "context", "account", "account_label", "vat_rate", "vat_code", "amount_ex_vat", "vat_amount", "explanation", "citation"]
}
```

#### Task 4.2: Implement Synthetic Exporter
**Files**: `scripts/export_gold_synthetic.py`

**Logic**:
1. Load templates from `gold_templates.py`
2. Load business rules for placeholder values
3. Generate 200-300 conversations per template:
   - Inject rule-based values (accounts, VAT, amounts)
   - Randomize phrasing (formal/informal)
   - Vary complexity (2-turn, 3-turn, 4-turn)
4. Split by template type
5. Output train/val JSONL

**Target**: 1,400 train + 300 val = 1,700 samples

### Phase 5: Training Loop (Day 6)

#### Task 5.1: Orchestrate Full Export
**Files**: `scripts/export_gold_all.py`

**Features**:
- Run all exporters in sequence
- Aggregate statistics
- Validate all JSONL with Pydantic
- Generate `metadata/export_stats.json`

**Run**:
```bash
uv run scripts/export_gold_all.py --milestone A
```

#### Task 5.2: Train Baseline LoRA
**Files**: `scripts/train_lora_baseline.py`

**Config**:
- Base model: `microsoft/Phi-3-mini-4k-instruct` or `mistralai/Mistral-7B-Instruct-v0.3`
- LoRA rank: 16
- Training samples: 2,840 (all train splits combined)
- Epochs: 3
- Batch size: 4 (adjust for GPU)
- Learning rate: 2e-4

**Run**:
```bash
uv run scripts/train_lora_baseline.py \
  --train_files data/gold/train/*.jsonl \
  --output_dir checkpoints/milestone_a_v1 \
  --epochs 3
```

#### Task 5.3: Run Eval Harness
**Files**: `scripts/eval_glossary.py`

**Run**:
```bash
uv run scripts/eval_glossary.py \
  --model checkpoints/milestone_a_v1 \
  --eval_dir data/gold/eval \
  --output results/milestone_a_eval.json
```

**Expected Results**:
- Glossary accuracy: ≥90% (gate for Milestone B)
- Citation presence: ≥95%
- Avg answer length: 100-300 tokens
- No hallucinations: 100% (manual review of 20 samples)

#### Task 5.4: Document Results
**Files**: `docs/training_log.md`

Log:
- Training hyperparameters
- Eval results (accuracy, citations, length)
- Sample outputs (10 good, 5 bad)
- Decision: Proceed to Milestone B or iterate?

---

## ✅ Acceptance Criteria (Milestone A)

### Deliverables
- [ ] 3,500 total samples (2,840 train + 660 val) in valid JSONL format
- [ ] 80-item eval set with documented expected answers
- [ ] LoRA checkpoint trained on Milestone A data
- [ ] Eval harness implementation with automated scoring
- [ ] Training log with results and analysis

### Quality Gates
- [ ] **JSONL format**: 100% valid (Pydantic validation passes)
- [ ] **No duplicates**: ≥98% unique message content
- [ ] **Citation coverage**: ≥95% have valid source_ids
- [ ] **Norwegian quality**: Manual review of 50 samples → ≥90% natural
- [ ] **Train/val leakage**: 0% overlap (verify split strategy)
- [ ] **Glossary accuracy**: ≥90% on eval set
- [ ] **Answer length**: 80% within 100-300 token range

### Decision Point
- ✅ **If glossary accuracy ≥90%**: Proceed to Milestone B (scale to 10-15k)
- ⚠️ **If accuracy <90%**: Debug and iterate:
  - Check data quality (manual review)
  - Adjust model config (learning rate, epochs)
  - Refine prompts/templates
  - Add more diverse examples

---

## 📏 API Performance SLOs (Week 7-8 Preview)

Document these now for downstream design:

```yaml
/posting_proposal (Rules Engine):
  - p50: ≤5 ms
  - p95: ≤10 ms  
  - p99: ≤20 ms
  - accuracy: 100% (deterministic)
  - response: {account, vat_code, vat_rate, source_ids[], confidence: 1.0}

/ask (RAG + LLM):
  - p50: ≤1.5s
  - p95: ≤3s
  - p99: ≤5s
  - accuracy: ≥90% (with eval set)
  - response: {answer, citations[], source_ids[], confidence: 0.0-1.0}

/hybrid (Router):
  - Try rules first (10ms), fallback to RAG if confidence < 0.95
  - p95: ≤50ms (rules hit) or ≤3s (RAG fallback)
```

---

## 🚧 Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Glossary samples too verbose | Filter by text_length, truncate at 250 tokens |
| Train/val leakage from similar sections | Split by chapter/family, verify with dedup check |
| Synthetic conversations sound robotic | Manual review of 30 samples, iterate templates |
| Eval set too easy/hard | Baseline with GPT-4 zero-shot (expect 70-80%) |
| LoRA training diverges | Start with conservative LR (2e-4), monitor loss |
| Norwegian quality issues | Add language quality validator with regex checks |

---

## 📅 Timeline (Milestone A)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1 | Base infrastructure + Tax glossary | 1,000 samples |
| 2 | Accounting glossary | +300 samples (1,300 total) |
| 3 | Eval harness + manual curation | 80-item eval set |
| 4 | Rule application exporter | +500 samples (1,800 total) |
| 5 | Synthetic conversations | +1,700 samples (3,500 total) |
| 6 | Training + eval + decision | Milestone A complete |

---

## 🔗 Dependencies

**Prerequisites** (already complete):
- ✅ Silver layer with 2,049 validated records
- ✅ Pydantic schemas for Silver entities
- ✅ Business rules seed data (30 rules)
- ✅ Chart of Accounts (42 entries)

**New dependencies** (install before starting):
```bash
# Add to pyproject.toml [project.dependencies]
uv add transformers
uv add peft  # For LoRA training
uv add torch
uv add sentence-transformers  # For eval semantic similarity
uv add datasets  # For JSONL handling
```

**Hardware requirements**:
- GPU with ≥16GB VRAM (for Phi-3 mini training)
- Or use cloud GPU (RunPod, Lambda Labs)
- CPU fallback possible but slow (10x training time)

---

## 📖 References

- OpenAI Chat format: https://platform.openai.com/docs/guides/chat
- LoRA paper: https://arxiv.org/abs/2106.09685
- Phi-3 docs: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
- Norwegian language quality: NS-ISO 8859-1, nb-NO locale

---

## 🔄 Next Steps After Milestone A

1. **If successful (≥90%)**: Scale to Milestone B (10-15k samples)
   - Add 3x more synthetic conversations
   - Expand rule variations to 50 per rule
   - Add edge cases to eval set

2. **Week 6-7**: LLM-assisted rule extraction
   - Extract 200-300 rules from 1,804 law sections
   - Confidence-based filtering
   - Human review queue

3. **Week 7-8**: RAG + Rules API
   - Build dual-engine architecture
   - Implement `/posting_proposal` and `/ask` endpoints
   - Deploy with SLO monitoring

---

_End of Week 5-6 Plan_

