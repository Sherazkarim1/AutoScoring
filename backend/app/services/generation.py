"""Extract exam questions and generate model answers, rubrics, and key concepts."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from functools import lru_cache

from app.config import settings


@dataclass
class GeneratedQuestion:
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
class GenerationResult:
    questions: list[GeneratedQuestion]
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


def heuristic_generate(ocr_text: str, subject: str = "General") -> GenerationResult:
    blocks = extract_question_blocks(ocr_text)
    questions: list[GeneratedQuestion] = []
    for number, body, marks in blocks:
        concepts = _key_phrases(body)
        concept_line = ", ".join(concepts) if concepts else "the main ideas in the prompt"
        model_answer = (
            f"A complete answer to this question should explain {concept_line}. "
            f"It should define the required terms, cover each part of the prompt, "
            f"and give a short example or justification where relevant. "
            f"Prompt: {body[:400]}"
        )
        rubric = (
            f"Award full marks if the student covers: {concept_line}. "
            "Deduct marks for missing definitions, incomplete explanation, "
            "or answers that do not address the asked question. "
            "Partial marks for a relevant but incomplete response."
        )
        questions.append(
            GeneratedQuestion(
                title=f"Question {number}",
                question_text=body,
                model_answer=model_answer,
                marking_rubric=rubric,
                key_concepts=concepts,
                max_score=marks or 10.0,
                subject=subject,
            )
        )
    return GenerationResult(
        questions=questions,
        source="heuristic",
        warning=(
            "No LLM API key is configured, so model answers are drafts from the extracted "
            "questions. Review and edit them before scoring. Set LLM_API_KEY for full generation."
        ),
    )


def _llm_chat(prompt: str) -> str:
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key}",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are an exam-paper assistant for university instructors. "
                "Return only valid JSON."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    def _post(payload: dict) -> str:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:300]}") from exc
        return data["choices"][0]["message"]["content"]

    base = {"model": settings.llm_model, "temperature": 0.2, "messages": messages}
    try:
        return _post({**base, "response_format": {"type": "json_object"}})
    except RuntimeError:
        return _post(base)


def _parse_llm_questions(raw: str, subject: str) -> list[GeneratedQuestion]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()
    payload = json.loads(cleaned)
    items = payload.get("questions", payload if isinstance(payload, list) else [])
    questions: list[GeneratedQuestion] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        question_text = str(item.get("question_text") or item.get("question") or "").strip()
        model_answer = str(item.get("model_answer") or "").strip()
        if len(question_text) < 8 or len(model_answer) < 10:
            continue
        concepts = item.get("key_concepts") or []
        if isinstance(concepts, str):
            concepts = [p.strip() for p in concepts.split(",") if p.strip()]
        try:
            max_score = float(item.get("max_score") or 10)
        except (TypeError, ValueError):
            max_score = 10.0
        questions.append(
            GeneratedQuestion(
                title=str(item.get("title") or f"Question {index}").strip(),
                question_text=question_text,
                model_answer=model_answer,
                marking_rubric=str(item.get("marking_rubric") or "").strip(),
                key_concepts=[str(c).strip() for c in concepts if str(c).strip()],
                max_score=max(1.0, min(max_score, 100.0)),
                subject=str(item.get("subject") or subject),
            )
        )
    return questions


def llm_generate(ocr_text: str, subject: str = "General") -> GenerationResult:
    prompt = f"""Extract exam questions from this OCR text of a question paper.
For each question generate:
- title
- question_text
- max_score (number; use marks on the paper if present, else 10)
- model_answer (a complete ideal student answer)
- marking_rubric (how marks should be awarded)
- key_concepts (array of short terms)

Ignore headers, instructions, and university logos.
If the paper has only one prompt, return one question.

Return JSON: {{ "questions": [ ... ] }}

OCR TEXT:
{ocr_text[:12000]}
"""
    raw = _llm_chat(prompt)
    questions = _parse_llm_questions(raw, subject)
    if not questions:
        raise RuntimeError("LLM returned no usable questions")
    return GenerationResult(questions=questions, source="llm")


def generate_from_ocr(ocr_text: str, subject: str = "General") -> GenerationResult:
    text = (ocr_text or "").strip()
    if len(text) < 12:
        raise ValueError("Not enough text extracted from the question paper.")

    if settings.llm_api_key:
        try:
            return llm_generate(text, subject)
        except Exception as exc:
            fallback = heuristic_generate(text, subject)
            fallback.warning = (
                f"LLM generation failed ({exc}). Drafts were created from extracted questions — please edit them."
            )
            return fallback
    return heuristic_generate(text, subject)


@lru_cache
def get_generation_service():
    return generate_from_ocr
