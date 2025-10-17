# Gold Layer Evaluation Dataset

## Overview

This directory contains manually curated evaluation samples for assessing the quality of LLM-generated responses in the Norwegian accounting and tax domain.

**Total Samples**: 50 (current), 80 (target for Milestone A)

## Dataset Breakdown

| Dataset | Samples | Status | Description |
|---------|---------|--------|-------------|
| `tax_glossary_eval.jsonl` | 30 | ✅ Complete | Tax and VAT terminology questions |
| `accounting_glossary_eval.jsonl` | 20 | ✅ Complete | Chart of Accounts and SAF-T questions |
| `rule_application_eval.jsonl` | 20 | 🔄 Phase 3 | Rule-based posting proposals |
| `conversation_eval.jsonl` | 10 | 🔄 Phase 4 | Multi-turn conversations |

## File Format

Each JSONL file contains one JSON object per line with the following structure:

```json
{
  "messages": [
    {"role": "system", "content": "System prompt"},
    {"role": "user", "content": "User question"},
    {"role": "assistant", "content": "EXPECTED_ANSWER"}
  ],
  "metadata": {
    "domain": "tax|accounting|reporting|payroll",
    "task": "glossary_define|posting_proposal|conversation|vat_question",
    "source_ids": ["source_id_1", "source_id_2"],
    "locale": "nb-NO",
    "split": "eval"
  },
  "expected_output": "The expected answer text with citation",
  "eval_criteria": {
    "must_include": ["keyword1", "keyword2"],
    "citation_required": true|false,
    "max_tokens": 300
  }
}
```

## Evaluation Criteria

### 1. Glossary Accuracy (Tax & Accounting)

**Objective**: Term definition matches expected semantic meaning

**Grading**:
- **Exact Match (1.0)**: Response is semantically identical to expected output
- **Semantic Similarity (0.7-0.99)**: Response captures main points but differs in wording
  - Use sentence-transformers cosine similarity (threshold: 0.75)
  - Check presence of `must_include` keywords (all must be present)
- **Partial Match (0.4-0.69)**: Response is related but missing key information
- **No Match (0.0)**: Response is incorrect or irrelevant

**Quality Checks**:
- ✅ All `must_include` keywords present (case-insensitive)
- ✅ Response length: 50-300 tokens (configurable via `max_tokens`)
- ✅ Norwegian language quality (manual spot check)
- ✅ No hallucinations (no invented laws or sections)

### 2. Citation Quality

**Objective**: Source references are present and resolvable

**Grading**:
- **Citation Present (1.0)**: Response includes citation in format `[§ X-Y Law Title]` or `[NS 4102]`
- **No Citation (0.0)**: No citation present when `citation_required: true`
- **N/A**: When `citation_required: false`

**Citation Patterns** (regex):
```
\[§\s*[\d-]+\s+[^\]]+\]  # Law citations: [§ 1-1 Lov om ...]
\[NS\s*\d+\]              # Standard references: [NS 4102]
```

**Validation**:
- Source IDs in `metadata.source_ids` must be resolvable to Silver layer
- Citation text should match law/standard title from source

### 3. Answer Length

**Objective**: Responses are concise and appropriate for the question type

**Grading**:
- **Optimal (1.0)**: 100-250 tokens
- **Acceptable (0.8)**: 50-100 or 250-300 tokens
- **Too Short (0.5)**: <50 tokens
- **Too Verbose (0.5)**: >300 tokens (default max_tokens)

**Token Counting**: Use simple whitespace split or tiktoken for GPT models

### 4. Norwegian Language Quality

**Objective**: Responses use natural, correct Norwegian (Bokmål)

**Manual Spot Check** (20% of samples):
- ✅ Correct grammar and spelling
- ✅ Natural phrasing (not robotic translation)
- ✅ Appropriate formality level (professional but accessible)
- ✅ Correct use of domain terminology
- ❌ No English words (except proper nouns: SAF-T, MVA)
- ❌ No Swedish/Danish phrasing

**Automated Checks**:
- Norwegian character usage (æ, ø, å)
- Domain-specific keywords present

## Scoring Rubric

### Overall Score Calculation

```python
overall_score = (
    accuracy_score * 0.50 +      # Semantic accuracy (50%)
    citation_score * 0.25 +       # Citation quality (25%)
    length_score * 0.15 +         # Length appropriateness (15%)
    keyword_score * 0.10          # Must-include keywords (10%)
)
```

### Pass Criteria

**Glossary Tasks**:
- ✅ Overall score ≥ 0.90 → **Pass**
- ⚠️ Overall score 0.75-0.89 → **Acceptable**
- ❌ Overall score < 0.75 → **Fail**

**Milestone A Target**: ≥90% Pass rate on glossary eval set (50 samples)

## Usage

### Run Evaluation

```bash
# Evaluate all glossary samples
uv run scripts/eval_glossary.py \
  --eval_dir data/gold/eval \
  --model_name <model_or_checkpoint_path> \
  --output results/eval_report.json

# Evaluate specific dataset
uv run scripts/eval_glossary.py \
  --eval_files data/gold/eval/tax_glossary_eval.jsonl \
  --model_name gpt-4 \
  --output results/tax_eval.json
```

### Eval Output Format

```json
{
  "metadata": {
    "model": "checkpoints/milestone_a_v1",
    "eval_files": ["tax_glossary_eval.jsonl", "accounting_glossary_eval.jsonl"],
    "total_samples": 50,
    "timestamp": "2025-10-17T12:00:00Z"
  },
  "aggregate_metrics": {
    "overall_score": 0.92,
    "accuracy": 0.94,
    "citation_coverage": 0.96,
    "avg_length_tokens": 142,
    "pass_rate": 0.94
  },
  "by_task": {
    "glossary_define": {
      "count": 50,
      "overall_score": 0.92,
      "accuracy": 0.94,
      "pass_rate": 0.94
    }
  },
  "by_domain": {
    "tax": {
      "count": 30,
      "overall_score": 0.91,
      "pass_rate": 0.93
    },
    "accounting": {
      "count": 20,
      "overall_score": 0.94,
      "pass_rate": 0.95
    }
  },
  "sample_results": [
    {
      "sample_id": "tax_glossary_0",
      "question": "Hva er merverdiavgift?",
      "expected": "Merverdiavgift er en avgift til staten...",
      "predicted": "Merverdiavgift er en...",
      "scores": {
        "overall": 0.95,
        "accuracy": 0.98,
        "citation": 1.0,
        "length": 0.9,
        "keywords": 1.0
      },
      "status": "pass"
    }
  ],
  "failed_samples": [...],
  "warnings": [...]
}
```

## Quality Assurance

### Manual Review Process

1. **Spot Check**: Review 20% of samples (10/50) manually
2. **Failed Samples**: Review all samples with `overall_score < 0.75`
3. **Citation Verification**: Validate 10 random citations against Silver layer
4. **Norwegian Quality**: Review 10 samples for language quality

### Baseline Benchmarks

Run eval on baseline models for comparison:

```bash
# GPT-4 zero-shot (expected: ~70-80% pass rate)
uv run scripts/eval_glossary.py --model_name gpt-4 --baseline

# Phi-3 base (expected: ~40-50% pass rate)
uv run scripts/eval_glossary.py --model_name microsoft/Phi-3-mini-4k-instruct --baseline
```

## Coverage Analysis

### Tax Glossary Coverage (30 samples)

**Topics**:
- Basic definitions (merverdiavgift, omsetning, etc.) - 6 samples
- Registration and thresholds - 3 samples
- VAT rates and calculation - 4 samples
- Deductions (fradragsrett) - 5 samples
- Reverse charge (omvendt avgiftsplikt) - 2 samples
- Import/export - 2 samples
- Exemptions and procedures - 4 samples
- Documentation and reporting - 4 samples

**Laws Covered**:
- Merverdiavgiftsloven (MVA law 2009) - 28 samples
- MVA rates and regulations - 2 samples

### Accounting Glossary Coverage (20 samples)

**Topics**:
- Asset accounts (klasse 1) - 3 samples
- Equity and liabilities (klasse 2) - 3 samples
- Revenue accounts (klasse 3) - 2 samples
- Cost of goods sold (klasse 4) - 1 sample
- Payroll costs (klasse 5) - 2 samples
- Operating expenses (klasse 6) - 4 samples
- Financial items (klasse 7-8) - 3 samples
- Account classes - 2 samples

**Sources**:
- Chart of Accounts (NS 4102) - 18 samples
- SAF-T structure - 0 samples (to be added in Phase 2 iteration)

## Future Enhancements

### Phase 3-4 Additions

1. **Rule Application Eval** (20 samples):
   - Transaction descriptions → posting proposals
   - VAT code validation
   - Account selection accuracy
   - Multi-line transaction handling

2. **Conversation Eval** (10 samples):
   - Multi-turn coherence
   - Clarifying question quality
   - Context retention across turns
   - Error correction handling

### Evaluation Improvements

1. **LLM-as-Judge**: Use GPT-4 for semantic similarity scoring
2. **Human Feedback**: Collect user ratings on real-world queries
3. **A/B Testing**: Compare model versions on same eval set
4. **Temporal Consistency**: Track model performance over time

---

_Last Updated: 2025-10-17_  
_Status: Phase 2 Complete (50/80 samples)_

