#!/usr/bin/env python3
"""
Evaluation harness for Gold layer training data.

Loads eval datasets, runs inference, and grades responses based on:
- Semantic accuracy
- Citation presence
- Length appropriateness
- Keyword coverage
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.logger import get_logger

logger = get_logger(__name__)


def load_eval_samples(eval_file: Path) -> list[dict[str, Any]]:
    """Load eval samples from JSONL file."""
    samples = []
    with open(eval_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON line: {e}")
    return samples


def extract_question(messages: list[dict[str, str]]) -> str:
    """Extract user question from messages."""
    for msg in messages:
        if msg["role"] == "user":
            return msg["content"]
    return ""


def check_citation_presence(text: str) -> bool:
    """Check if text contains a citation."""
    citation_patterns = [
        r"\[§\s*[\d-]+\s+[^\]]+\]",
        r"\[NS\s*\d+\]",
        r"\[Lov om [^\]]+\]",
        r"\[Forskrift [^\]]+\]",
    ]
    for pattern in citation_patterns:
        if re.search(pattern, text):
            return True
    return False


def check_keywords(text: str, keywords: list[str]) -> tuple[int, int]:
    """Check presence of required keywords (case-insensitive)."""
    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw.lower() in text_lower)
    return found, len(keywords)


def count_tokens(text: str) -> int:
    """Simple token count using whitespace split."""
    return len(text.split())


def calculate_length_score(token_count: int, max_tokens: int = 300) -> float:
    """Calculate length score based on token count."""
    if 100 <= token_count <= 250:
        return 1.0
    if 50 <= token_count < 100 or 250 < token_count <= max_tokens:
        return 0.8
    if token_count < 50:
        return 0.5
    if token_count > max_tokens:
        return 0.5
    return 0.0


def simple_semantic_similarity(text1: str, text2: str) -> float:
    """
    Simple semantic similarity using word overlap.

    For production, use sentence-transformers:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode([text1, text2])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def grade_response(
    predicted: str,
    expected: str,
    eval_criteria: dict[str, Any],
) -> dict[str, Any]:
    """Grade a predicted response against expected output."""
    scores: dict[str, Any] = {}

    accuracy = simple_semantic_similarity(predicted, expected)
    scores["accuracy"] = accuracy

    citation_required = eval_criteria.get("citation_required", True)
    if citation_required:
        scores["citation"] = 1.0 if check_citation_presence(predicted) else 0.0
    else:
        scores["citation"] = 1.0

    token_count = count_tokens(predicted)
    max_tokens = eval_criteria.get("max_tokens", 300)
    scores["length"] = calculate_length_score(token_count, max_tokens)
    scores["token_count"] = token_count

    must_include = eval_criteria.get("must_include", [])
    if must_include:
        found, total = check_keywords(predicted, must_include)
        scores["keywords"] = found / total if total > 0 else 1.0
        scores["keywords_found"] = found
        scores["keywords_total"] = total
    else:
        scores["keywords"] = 1.0

    overall = (
        scores["accuracy"] * 0.50
        + scores["citation"] * 0.25
        + scores["length"] * 0.15
        + scores["keywords"] * 0.10
    )
    scores["overall"] = overall

    if overall >= 0.90:
        scores["status"] = "pass"
    elif overall >= 0.75:
        scores["status"] = "acceptable"
    else:
        scores["status"] = "fail"

    return scores


def run_inference_mock(question: str, system_prompt: str) -> str:
    """
    Mock inference function - returns expected answer for testing.

    In production, replace with actual model inference:
    - Load LoRA checkpoint
    - Generate response with model
    - Return generated text
    """
    return f"MOCK_RESPONSE: {question}"


def evaluate_samples(
    samples: list[dict[str, Any]],
    model_name: str = "mock",
    use_expected_as_predicted: bool = False,
) -> dict[str, Any]:
    """Evaluate all samples and return results."""
    results = []

    for idx, sample in enumerate(samples):
        question = extract_question(sample["messages"])
        system_prompt = sample["messages"][0]["content"]
        expected = sample.get("expected_output", "")
        eval_criteria = sample.get("eval_criteria", {})

        if use_expected_as_predicted:
            predicted = expected
        else:
            predicted = run_inference_mock(question, system_prompt)

        scores = grade_response(predicted, expected, eval_criteria)

        result = {
            "sample_id": f"{sample['metadata']['task']}_{idx}",
            "domain": sample["metadata"]["domain"],
            "task": sample["metadata"]["task"],
            "question": question,
            "expected": expected,
            "predicted": predicted,
            "scores": scores,
        }
        results.append(result)

        status = str(scores["status"]).upper()
        logger.info(
            f"Sample {idx + 1}: {status} "
            f"(overall={scores['overall']:.2f}, acc={scores['accuracy']:.2f})"
        )

    return aggregate_results(results, model_name)


def aggregate_results(results: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    """Aggregate results and compute metrics."""
    total = len(results)

    if total == 0:
        logger.warning("No results to aggregate")
        return {}

    aggregate_metrics = {
        "overall_score": sum(r["scores"]["overall"] for r in results) / total,
        "accuracy": sum(r["scores"]["accuracy"] for r in results) / total,
        "citation_coverage": sum(r["scores"]["citation"] for r in results) / total,
        "avg_length_tokens": sum(r["scores"]["token_count"] for r in results) / total,
        "pass_rate": sum(1 for r in results if r["scores"]["status"] == "pass") / total,
    }

    by_task = defaultdict(list)
    by_domain = defaultdict(list)

    for result in results:
        by_task[result["task"]].append(result)
        by_domain[result["domain"]].append(result)

    def calc_metrics(subset: list[dict[str, Any]]) -> dict[str, float]:
        count = len(subset)
        return {
            "count": count,
            "overall_score": sum(r["scores"]["overall"] for r in subset) / count,
            "accuracy": sum(r["scores"]["accuracy"] for r in subset) / count,
            "pass_rate": sum(1 for r in subset if r["scores"]["status"] == "pass")
            / count,
        }

    by_task_metrics = {task: calc_metrics(samples) for task, samples in by_task.items()}
    by_domain_metrics = {
        domain: calc_metrics(samples) for domain, samples in by_domain.items()
    }

    failed_samples = [r for r in results if r["scores"]["status"] == "fail"]

    report = {
        "metadata": {
            "model": model_name,
            "total_samples": total,
            "timestamp": datetime.now().isoformat(),
        },
        "aggregate_metrics": aggregate_metrics,
        "by_task": by_task_metrics,
        "by_domain": by_domain_metrics,
        "sample_results": results,
        "failed_samples": failed_samples,
    }

    return report


def print_summary(report: dict[str, Any]) -> None:
    """Print evaluation summary to console."""
    logger.info("=" * 80)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 80)

    metrics = report["aggregate_metrics"]
    logger.info(f"Model: {report['metadata']['model']}")
    logger.info(f"Total Samples: {report['metadata']['total_samples']}")
    logger.info("")
    logger.info(f"Overall Score:        {metrics['overall_score']:.3f}")
    logger.info(f"Accuracy:             {metrics['accuracy']:.3f}")
    logger.info(f"Citation Coverage:    {metrics['citation_coverage']:.3f}")
    logger.info(f"Avg Length (tokens):  {metrics['avg_length_tokens']:.1f}")
    logger.info(f"Pass Rate:            {metrics['pass_rate']:.3f}")
    logger.info("")

    logger.info("By Task:")
    for task, task_metrics in report["by_task"].items():
        logger.info(
            f"  {task:20s}: {task_metrics['count']:3d} samples, "
            f"score={task_metrics['overall_score']:.3f}, "
            f"pass={task_metrics['pass_rate']:.3f}"
        )

    logger.info("")
    logger.info("By Domain:")
    for domain, domain_metrics in report["by_domain"].items():
        logger.info(
            f"  {domain:20s}: {domain_metrics['count']:3d} samples, "
            f"score={domain_metrics['overall_score']:.3f}, "
            f"pass={domain_metrics['pass_rate']:.3f}"
        )

    logger.info("")
    failed_count = len(report["failed_samples"])
    if failed_count > 0:
        logger.warning(f"Failed Samples: {failed_count}")
        for sample in report["failed_samples"][:5]:
            logger.warning(
                f"  - {sample['sample_id']}: {sample['question'][:60]}... "
                f"(score={sample['scores']['overall']:.2f})"
            )

    logger.info("=" * 80)


def main() -> None:
    """Main evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate Gold layer training data quality"
    )
    parser.add_argument(
        "--eval_dir",
        type=Path,
        default=Path("data/gold/eval"),
        help="Directory containing eval JSONL files",
    )
    parser.add_argument(
        "--eval_files",
        type=str,
        nargs="+",
        help="Specific eval files to evaluate (overrides eval_dir)",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="mock",
        help="Model name or checkpoint path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/eval_report.json"),
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--use_expected",
        action="store_true",
        help="Use expected output as predicted (for testing eval harness)",
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("GOLD LAYER EVALUATION HARNESS")
    logger.info("=" * 80)

    if args.eval_files:
        eval_files = [Path(f) for f in args.eval_files]
    else:
        eval_files = list(args.eval_dir.glob("*_eval.jsonl"))

    if not eval_files:
        logger.error(f"No eval files found in {args.eval_dir}")
        return

    logger.info(f"Eval files: {[f.name for f in eval_files]}")
    logger.info(f"Model: {args.model_name}")
    logger.info("")

    all_samples = []
    for eval_file in eval_files:
        if not eval_file.exists():
            logger.warning(f"File not found: {eval_file}")
            continue
        samples = load_eval_samples(eval_file)
        logger.info(f"Loaded {len(samples)} samples from {eval_file.name}")
        all_samples.extend(samples)

    if not all_samples:
        logger.error("No samples loaded")
        return

    logger.info(f"\nTotal samples to evaluate: {len(all_samples)}\n")

    report = evaluate_samples(all_samples, args.model_name, args.use_expected)

    print_summary(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"\nReport saved to: {args.output}")

    pass_rate = report["aggregate_metrics"]["pass_rate"]
    if pass_rate >= 0.90:
        logger.info("✅ PASSED: Eval pass rate >= 90%")
    else:
        logger.warning(f"⚠️ FAILED: Eval pass rate {pass_rate:.1%} < 90%")


if __name__ == "__main__":
    main()
