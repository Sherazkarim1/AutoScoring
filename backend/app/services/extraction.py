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


# Question markers are matched two ways: at the start of a line ("2. Explain ...")
# and inline ("Q2 Explain ..."). OCR flattens a whole page into one line of text, so
# the inline form is what actually fires for uploaded papers. A bare number is only
# trusted at a line start, otherwise "(10 marks)" and "1.5 hours" split mid-question.
# OCR frequently reads the "Q" of "Q2" as "0", so "02"/"03" are accepted too.
QUESTION_SPLIT = re.compile(
    r"(?im)^[ \t]*(?:q(?:uestion)?[ \t]*)?(\d+)[ \t]*[.):\-][ \t]+"
    r"|(?<![A-Za-z0-9])(?:q(?:uestion)?|0)([0-9])(?![0-9])"
)
MARKS_PATTERN = re.compile(r"\((\d+(?:\.\d+)?)\s*marks?\)", re.I)

# Exam papers open with institutional boilerplate: who issued it, which course, which
# session, how long, how many marks. None of it is answerable, so it must never be
# read as a question or as the concepts being tested.
PAPER_BOILERPLATE = {
    "university", "department", "faculty", "institute", "college", "school",
    "kiu", "course", "code", "semester", "term", "session", "subject",
    "examination", "exam", "test", "quiz", "assignment", "mid", "final",
    "fall", "spring", "summer", "year", "hour", "hours", "time", "minutes",
    "marks", "total", "maximum", "minimum", "allowed", "duration", "paper",
    "page", "pages", "roll", "number", "name", "date", "candidate",
    "registration", "reg", "bits", "section", "part", "note", "instructions",
    "computer", "science",
}


def _first_group(match: re.Match) -> str:
    return match.group(1) or match.group(2)


def _strip_paper_header(text: str, first_question_start: int) -> str:
    """Drop the institutional header that precedes the first question marker."""
    return text[first_question_start:].strip()


def extract_question_blocks(ocr_text: str) -> list[tuple[str, str, float | None]]:
    """Return (number, body, marks_or_none) from OCR text."""
    text = (ocr_text or "").strip()
    if not text:
        return []

    matches = list(QUESTION_SPLIT.finditer(text))
    if not matches:
        return [("1", text, _find_marks(text))]

    # Anything before the first question marker is the exam header, not a question.
    text = _strip_paper_header(text, matches[0].start())
    matches = list(QUESTION_SPLIT.finditer(text))
    if not matches:
        return []

    blocks: list[tuple[str, str, float | None]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        body = re.sub(r"\s+", " ", body)
        if len(body) < 8:
            continue
        number = _first_group(match)
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
    # Exam-header words are never testable content, so they are dropped here too.
    blocked = stop | PAPER_BOILERPLATE
    seen: list[str] = []
    seen_lower: set[str] = set()
    for word in words:
        lowered = word.lower()
        if lowered in blocked or lowered in seen_lower:
            continue
        seen.append(word)
        seen_lower.add(lowered)
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
