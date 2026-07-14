#!/usr/bin/env python3
"""
Evaluate AutoScoring accuracy against human teacher scores.

CSV format (header required):
  model_answer,student_answer,human_score[,max_score][,title]

Example:
  cd backend
  python evaluate.py data/evaluation/sample_eval.csv
  python evaluate.py data/evaluation/my_dataset.csv --output reports/eval_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from app.services.evaluation import EvaluationMetrics, compute_metrics
from app.services.scoring import get_scoring_service


REQUIRED_COLUMNS = {"model_answer", "student_answer", "human_score"}


def load_dataset(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing a header row")

        missing = REQUIRED_COLUMNS - {h.strip() for h in reader.fieldnames}
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

        rows = []
        for index, row in enumerate(reader, start=2):
            model_answer = (row.get("model_answer") or "").strip()
            student_answer = (row.get("student_answer") or "").strip()
            human_raw = (row.get("human_score") or "").strip()

            if not model_answer or not student_answer or not human_raw:
                print(f"Warning: skipping row {index} (missing required values)", file=sys.stderr)
                continue

            try:
                human_score = float(human_raw)
                max_score = float((row.get("max_score") or "10").strip())
            except ValueError as exc:
                raise ValueError(f"Invalid numeric value on row {index}") from exc

            rows.append(
                {
                    "title": (row.get("title") or f"Row {index}").strip(),
                    "model_answer": model_answer,
                    "student_answer": student_answer,
                    "human_score": human_score,
                    "max_score": max_score,
                }
            )

    if len(rows) < 2:
        raise ValueError("Need at least 2 valid rows to compute evaluation metrics")

    return rows


def run_evaluation(rows: list[dict]) -> tuple[EvaluationMetrics, list[dict]]:
    scorer = get_scoring_service()
    human_scores: list[float] = []
    system_scores: list[float] = []
    details: list[dict] = []

    for row in rows:
        score, breakdown, _, _ = scorer.score_answer(
            row["model_answer"],
            row["student_answer"],
            row["max_score"],
        )
        human_scores.append(row["human_score"])
        system_scores.append(score)
        details.append(
            {
                "title": row["title"],
                "human_score": row["human_score"],
                "system_score": score,
                "max_score": row["max_score"],
                "error": round(abs(row["human_score"] - score), 2),
                "semantic_similarity": breakdown.semantic_similarity,
                "keyword_coverage": breakdown.keyword_coverage,
                "coherence_score": breakdown.coherence_score,
            }
        )

    metrics = compute_metrics(human_scores, system_scores)
    return metrics, details


def print_report(metrics: EvaluationMetrics, details: list[dict]) -> None:
    print("\n" + "=" * 52)
    print("  AutoScoring Evaluation Report")
    print("=" * 52)
    for line in metrics.summary_lines():
        print(f"  {line}")
    print("-" * 52)
    print("  Per-sample comparison")
    print("-" * 52)
    print(f"  {'Title':<28} {'Human':>6} {'System':>6} {'Err':>6}")
    for item in details:
        title = item["title"][:28]
        print(
            f"  {title:<28} {item['human_score']:>6.1f} "
            f"{item['system_score']:>6.1f} {item['error']:>6.2f}"
        )
    print("=" * 52 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AutoScoring vs human scores")
    parser.add_argument("csv_path", type=Path, help="Path to evaluation CSV file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save JSON report",
    )
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"Error: file not found: {args.csv_path}", file=sys.stderr)
        return 1

    try:
        rows = load_dataset(args.csv_path)
        metrics, details = run_evaluation(rows)
        print_report(metrics, details)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "metrics": metrics.to_dict(),
                "samples": details,
                "source_csv": str(args.csv_path),
            }
            args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Saved report to {args.output}")

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
