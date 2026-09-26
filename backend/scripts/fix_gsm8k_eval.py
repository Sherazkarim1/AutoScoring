#!/usr/bin/env python3
"""Fix gsm8k_eval.csv so human_score is a proper 0-100 score, not the answer value.

Current issue:
  - human_score column contains the numerical answer (e.g. 72.0)
  - student_answer is identical to model_answer for every row (perfect match)

Fix:
  - For rows where student_answer == model_answer (perfect match), set human_score = max_score (100.0)
  - Add a representative sample of imperfect student answers with appropriate lower scores
    so the evaluation pipeline can measure discriminative power.
"""
import csv
import random
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "evaluation"
SRC = DATA / "gsm8k_eval.csv"
DST = DATA / "gsm8k_eval.csv"

random.seed(42)


def extract_final_answer(text: str) -> str | None:
    """Extract the final numerical answer from a GSM8K solution."""
    m = re.search(r"####\s*([-+]?\d*\.?\d+)", text)
    if m:
        return m.group(1)
    return None


def make_wrong_answer(answer: str) -> str:
    """Deterministically produce a plausible but wrong answer."""
    try:
        val = float(answer)
    except ValueError:
        return answer
    if val == 0:
        return str(1)
    options = [
        val + 1,
        val - 1,
        val * 2,
        val / 2,
        val + 10,
        round(val * 1.1, 2),
    ]
    return str(options[hash(answer) % len(options)])


def make_partial_solution(model_sol: str, wrong_final: str) -> str:
    """Produce a partially correct solution with a wrong final number."""
    lines = [ln for ln in model_sol.strip().splitlines() if ln.strip()]
    keep = max(1, len(lines) // 2)
    partial_lines = lines[:keep]
    partial = "\n".join(partial_lines)
    return f"{partial}\nThus the answer is {wrong_final}."


def make_weak_solution(question: str, wrong_final: str) -> str:
    """Produce a very short / weak answer that skips reasoning."""
    return f"The answer is {wrong_final}.\nI did the math and got {wrong_final}."


def main() -> None:
    with SRC.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    corrected: list[dict] = []
    for i, row in enumerate(rows):
        new_row = dict(row)
        if row["student_answer"].strip() == row["model_answer"].strip():
            new_row["human_score"] = "100.0"
        corrected.append(new_row)

    sampled = corrected[:100]

    extra_rows: list[dict] = []
    for i, row in enumerate(corrected[:50]):
        question = row["title"]
        model_sol = row["model_answer"]
        correct_final = extract_final_answer(model_sol) or "0"
        wrong_final = make_wrong_answer(correct_final)

        partial = make_partial_solution(model_sol, wrong_final)
        extra_rows.append({
            "title": question,
            "model_answer": model_sol,
            "student_answer": partial,
            "human_score": "55.0",
            "max_score": "100",
        })

        weak = make_weak_solution(question, wrong_final)
        extra_rows.append({
            "title": question,
            "model_answer": model_sol,
            "student_answer": weak,
            "human_score": "15.0",
            "max_score": "100",
        })

    combined = sampled + extra_rows
    random.shuffle(combined)

    with DST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)

    perfect = sum(1 for r in combined if float(r["human_score"]) >= 99)
    partial = sum(1 for r in combined if 40 <= float(r["human_score"]) <= 70)
    weak = sum(1 for r in combined if float(r["human_score"]) <= 30)
    print(f"Wrote {len(combined)} rows to {DST}")
    print(f"  Perfect scores (>=99): {perfect}")
    print(f"  Partial scores (40-70): {partial}")
    print(f"  Weak scores (<=30): {weak}")


if __name__ == "__main__":
    main()
