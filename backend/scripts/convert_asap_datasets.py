#!/usr/bin/env python3
"""Convert ASAP dataset files into AutoScoring evaluation CSV format.

Handles:
  1. prompt-3.txt (Handwritten ASAP SAS transcriptions)
     -> Extracts student answers + metadata (ASAP ID, pen color, status)
  2. asap_prompt_3.csv (Typed ASAP AES scoring data)
     -> Rescales 0-3 rubric scores to 0-10 human_scores
     -> Generates two outputs:
        a) asap_prompt3_handwritten.csv - for OCR evaluation (uses prompt-3.txt transcriptions)
        b) asap_prompt3_typed.csv - for typed-essay evaluation (uses rescored rubric data)

Prompt 3 model answer: compares pandas/koalas (specialists) vs pythons (generalists).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "evaluation"
PROJECT_ROOT = BASE.parent
HANDWRITTEN_DIR = PROJECT_ROOT / "Handwritten ASAP SAS"

PROMPT3_TXTFILE = HANDWRITTEN_DIR / "information" / "prompt-3.txt"
ASAP_CSV = DATA_DIR / "asap_prompt_3.csv"
OUT_HANDWRITTEN = DATA_DIR / "asap_prompt3_handwritten.csv"
OUT_TYPED = DATA_DIR / "asap_prompt3_typed.csv"

MODEL_ANSWER_PROMPT3 = (
    "Pandas in China and koalas in Australia are both specialist species, meaning they thrive "
    "in stable environments and rely on very specific food sources. China's panda eats almost "
    "nothing but bamboo, while Australia's koala bear eats eucalyptus leaves almost exclusively. "
    "Because their diets are so specialized, these animals can only survive in their native habitats. "
    "In contrast, pythons are generalist species that can adapt to a wide range of environments and "
    "prey. Generalists like pythons have a much greater variety of food sources and can live in many "
    "different climates and locations, ranging from their native Asia to places like Florida. This "
    "ability to adapt means generalists often become more abundant and can even become invasive species, "
    "while specialists are more vulnerable to environmental change."
)

RESCALE_FACTOR = 10.0 / 3.0

FIELDNAMES = ["title", "model_answer", "student_answer", "human_score", "max_score", "subject"]


def parse_prompt3_txt(path: Path) -> list[dict]:
    """Parse the handwritten prompt-3.txt transcription file.

    Line format (tab-separated, comments start with '#'):
      image_file\tasap_id\ttranscript\tpen_color\tstatus
    """
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            img_file = parts[0].strip()
            asap_id = parts[1].strip()
            transcript = parts[2].strip()
            pen_color = parts[3].strip() if len(parts) > 3 else ""
            status = parts[4].strip() if len(parts) > 4 else ""
            m = re.search(r"SAS_3_(\d+)", img_file)
            if m:
                asap_id = m.group(1)
            entries.append({
                "asap_id": asap_id,
                "image_file": img_file,
                "student_answer": transcript,
                "pen_color": pen_color,
                "status": status,
            })
    return entries


def parse_asap_csv(path: Path) -> list[dict]:
    """Parse typed ASAP CSV: Essay ID, Content, Prompt Adherence, Language, Narrativity.

    All four rubric dimensions are 0-3 integer scores.
    """
    entries = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            essay_id = (row.get("Essay ID") or "").strip()
            try:
                content_score = int((row.get("Content") or "0").strip())
                prompt_score = int((row.get("Prompt Adherence") or "0").strip())
                language_score = int((row.get("Language") or "0").strip())
                narrativity_score = int((row.get("Narrativity") or "0").strip())
            except ValueError:
                continue
            entries.append({
                "essay_id": essay_id,
                "content_score": content_score,
                "prompt_adherence": prompt_score,
                "language_score": language_score,
                "narrativity_score": narrativity_score,
            })
    return entries


def rubric_to_human_score(content: int, prompt_adherence: int,
                          language: int, narrativity: int) -> float:
    """Combine ASAP 0-3 rubric scores and rescale to 0-10.

    Weights emphasize content relevance and prompt adherence (60% combined),
    with language quality and narrativity making up the remainder.
    """
    weighted_raw = (
        0.35 * content
        + 0.25 * prompt_adherence
        + 0.25 * language
        + 0.15 * narrativity
    )
    rescaled = weighted_raw * RESCALE_FACTOR
    return round(max(0.0, min(10.0, rescaled)), 2)


def heuristic_handwritten_score(transcript: str) -> float:
    """Estimate a 0-10 human score for handwritten transcriptions.

    Uses simple heuristics based on the Prompt 3 rubric:
      - Length / keyword coverage (specialist, generalist, bamboo, eucalyptus,
        panda, koala, python, adapt, habitat, diet, exclusively)
      - Sentence structure
    This is an ESTIMATE only; for real evaluation use human-validated scores.
    """
    text = transcript.lower()
    keywords = {
        "panda", "koala", "python", "bamboo", "eucalyptus",
        "specialist", "generalist", "exclusively", "diet", "habitat",
        "adapt", "china", "australia", "species", "food", "climate",
    }
    found = sum(1 for kw in keywords if kw in text)
    kw_score = found / len(keywords)

    words = re.findall(r"[a-z]+", text)
    word_count = len(words)
    length_score = min(1.0, word_count / 60.0)

    sentences = re.split(r"[.!?]+", text)
    sentence_count = sum(1 for s in sentences if len(s.strip()) >= 5)
    struct_score = min(1.0, sentence_count / 3.0)

    combined = 0.45 * kw_score + 0.35 * length_score + 0.20 * struct_score
    return round(max(0.5, min(10.0, combined * 10.0)), 2)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_handwritten_rows(entries: list[dict]) -> list[dict]:
    rows = []
    for e in entries:
        if not e["student_answer"].strip():
            continue
        score = heuristic_handwritten_score(e["student_answer"])
        rows.append({
            "title": f"Prompt3 HW ID {e['asap_id']}",
            "model_answer": MODEL_ANSWER_PROMPT3,
            "student_answer": e["student_answer"],
            "human_score": str(score),
            "max_score": "10",
            "subject": "science",
        })
    return rows


def build_typed_rows(entries: list[dict]) -> list[dict]:
    rows = []
    for e in entries:
        score = rubric_to_human_score(
            e["content_score"],
            e["prompt_adherence"],
            e["language_score"],
            e["narrativity_score"],
        )
        rows.append({
            "title": f"Prompt3 Typed Essay {e['essay_id']}",
            "model_answer": MODEL_ANSWER_PROMPT3,
            "student_answer": f"[Typed essay text for Essay ID {e['essay_id']} - "
                              f"Content={e['content_score']}/3, "
                              f"PromptAdherence={e['prompt_adherence']}/3, "
                              f"Language={e['language_score']}/3, "
                              f"Narrativity={e['narrativity_score']}/3. "
                              f"Full essay text requires training_set_rel3.tsv.]",
            "human_score": str(score),
            "max_score": "10",
            "subject": "reading",
        })
    return rows


def main() -> None:
    print("=== ASAP → AutoScoring CSV conversion ===")

    if PROMPT3_TXTFILE.exists():
        hw_entries = parse_prompt3_txt(PROMPT3_TXTFILE)
        print(f"\nParsed {len(hw_entries)} handwritten transcriptions from prompt-3.txt")
        if hw_entries:
            print(f"  Sample: ASAP ID {hw_entries[0]['asap_id']} -> {len(hw_entries[0]['student_answer'])} chars")
            status_set = sorted(set(e["status"] for e in hw_entries))
            status_counts = ", ".join(
                f"{k}: {sum(1 for e in hw_entries if e['status'] == k)}"
                for k in status_set
            )
            print(f"  Status counts: {{{status_counts}}}")
            hw_rows = build_handwritten_rows(hw_entries)
            write_csv(OUT_HANDWRITTEN, hw_rows)
            print(f"  Wrote {len(hw_rows)} rows -> {OUT_HANDWRITTEN.name}")
            scores = [float(r["human_score"]) for r in hw_rows]
            print(f"  Heuristic score range: {min(scores):.1f} - {max(scores):.1f} (mean {sum(scores)/len(scores):.1f})")
    else:
        print(f"\n[SKIP] prompt-3.txt not found at {PROMPT3_TXTFILE}")
        hw_entries = []

    if ASAP_CSV.exists():
        typed_entries = parse_asap_csv(ASAP_CSV)
        print(f"\nParsed {len(typed_entries)} typed rubric entries from asap_prompt_3.csv")
        if typed_entries:
            cs = [e["content_score"] for e in typed_entries]
            print(f"  Content score distribution: 0={cs.count(0)}, 1={cs.count(1)}, 2={cs.count(2)}, 3={cs.count(3)}")
            typed_rows = build_typed_rows(typed_entries)
            write_csv(OUT_TYPED, typed_rows)
            print(f"  Wrote {len(typed_rows)} rows -> {OUT_TYPED.name}")
            scores = [float(r["human_score"]) for r in typed_rows]
            print(f"  Rescaled score range: {min(scores):.1f} - {max(scores):.1f} (mean {sum(scores)/len(scores):.1f})")
            print("  Note: student_answer is a placeholder. Full essay text requires training_set_rel3.tsv.")
    else:
        print(f"\n[SKIP] asap_prompt_3.csv not found at {ASAP_CSV}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
