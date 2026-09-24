"""Split OCR text from a question paper into questions. Teacher supplies the answer key."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import lru_cache


@dataclass
class ExtractedQuestion:
    title: str
    question_text: str
    model_answer: str
    marking_rubric: str
    key_concepts: list[str]
    max_score: float = 10.0
    subject: str = "General"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractionResult:
    questions: list[ExtractedQuestion]
    source: str
    warning: str | None = None


QUESTION_SPLIT = re.compile(
    r"(?im)^\s*(?:q(?:uestion)?\s*)?(\d+)\s*[\.\)\:\-]\s+",
)
MARKS_PATTERN = re.compile(r"\((\d+(?:\.\d+)?)\s*marks?\)", re.I)


def extract_question_blocks(ocr_text: str) -> list[tuple[str, str, float | None]]:
    """Return (number, body, marks_or_none) from OCR text."""
    text = (ocr_text or "").strip()
    if not text:
        return []

    matches = list(QUESTION_SPLIT.finditer(text))
    if not matches:
        return [("1", text, _find_marks(text))]

    blocks: list[tuple[str, str, float | None]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        body = re.sub(r"\s+", " ", body)
        if len(body) < 8:
            continue
        number = match.group(1)
        blocks.append((number, body, _find_marks(body)))
    return blocks or [("1", text, _find_marks(text))]


def _find_marks(text: str) -> float | None:
    match = MARKS_PATTERN.search(text)
    if not match:
        return None
    try:
        value = float(match.group(1))
        return value if 0 < value <= 100 else None
    except ValueError:
        return None


def _key_phrases(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text)
    stop = {
        "this", "that", "these", "those", "with", "from", "your", "what", "when",
        "where", "which", "while", "explain", "describe", "discuss", "define",
        "briefly", "following", "question", "answer", "marks", "using", "into",
    }
    seen: list[str] = []
    for word in words:
        lowered = word.lower()
        if lowered in stop or lowered in {s.lower() for s in seen}:
            continue
        seen.append(word)
        if len(seen) >= limit:
            break
    return seen


def extract_from_ocr(ocr_text: str, subject: str = "General") -> ExtractionResult:
    text = (ocr_text or "").strip()
    if len(text) < 12:
        raise ValueError("Not enough text extracted from the question paper.")

    blocks = extract_question_blocks(text)
    questions: list[ExtractedQuestion] = []
    for number, body, marks in blocks:
        concepts = _key_phrases(body)
        concept_line = ", ".join(concepts) if concepts else "the main ideas in the prompt"
        questions.append(
            ExtractedQuestion(
                title=f"Question {number}",
                question_text=body,
                model_answer="",
                marking_rubric=(
                    f"Award full marks if the student covers: {concept_line}. "
                    "Deduct marks for missing definitions or incomplete explanation."
                ),
                key_concepts=concepts,
                max_score=marks or 10.0,
                subject=subject,
            )
        )
    return ExtractionResult(
        questions=questions,
        source="paper",
        warning=(
            "Questions were extracted from the paper. Paste your official model answer "
            "(answer key) into each question before saving — otherwise scoring will be wrong."
        ),
    )


@lru_cache
def get_extraction_service():
    return extract_from_ocr
