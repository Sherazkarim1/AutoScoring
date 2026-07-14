import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Optional

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.schemas import ScoreBreakdown


@dataclass
class DetailedReport:
    matched_concepts: list[str]
    missing_concepts: list[str]
    partial_concepts: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    strengths: list[str]
    weaknesses: list[str]
    word_count: int
    sentence_count: int
    ocr_quality_note: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "DetailedReport":
        return cls(**json.loads(data))


class ScoringService:
    """BERT-based semantic scoring using sentence-transformers."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _normalize_text(self, text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokenize_words(self, text: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "this",
            "that", "these", "those", "it", "its", "as", "if", "than", "then",
        }
        return {w for w in words if len(w) > 2 and w not in stopwords}

    def _split_concepts(self, text: str) -> list[str]:
        chunks = re.split(r"[.!?;\n]+", text)
        concepts = [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 20]
        if not concepts and text.strip():
            concepts = [text.strip()]
        return concepts

    def _semantic_similarity(self, model_answer: str, student_answer: str) -> float:
        embeddings = self.model.encode(
            [model_answer, student_answer],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        return max(0.0, min(1.0, similarity))

    def _concept_similarity(self, concept: str, student_answer: str) -> float:
        if not concept.strip() or not student_answer.strip():
            return 0.0
        embeddings = self.model.encode(
            [concept, student_answer],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return max(0.0, min(1.0, float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])))

    def _keyword_coverage(self, model_answer: str, student_answer: str) -> float:
        model_tokens = self._tokenize_words(model_answer)
        student_tokens = self._tokenize_words(student_answer)
        if not model_tokens:
            return 0.0
        overlap = model_tokens.intersection(student_tokens)
        return len(overlap) / len(model_tokens)

    def _coherence_score(self, student_answer: str) -> float:
        text = self._normalize_text(student_answer)
        if len(text) < 20:
            return 0.2

        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        sentence_count = max(len(sentences), 1)
        words = text.split()
        word_count = len(words)

        length_score = min(1.0, word_count / 40)
        structure_score = min(1.0, sentence_count / 3)
        unique_ratio = len(set(words)) / max(word_count, 1)
        repetition_penalty = 1.0 if unique_ratio > 0.5 else unique_ratio * 2

        return max(0.0, min(1.0, (0.5 * length_score + 0.3 * structure_score + 0.2 * repetition_penalty)))

    def _generate_feedback(
        self,
        semantic: float,
        keywords: float,
        coherence: float,
        weighted: float,
    ) -> str:
        parts = []

        if semantic >= 0.75:
            parts.append("Strong semantic alignment with the model answer.")
        elif semantic >= 0.5:
            parts.append("Moderate relevance; key concepts are partially covered.")
        else:
            parts.append("Limited semantic overlap with the expected answer.")

        if keywords >= 0.6:
            parts.append("Good coverage of important terminology.")
        elif keywords >= 0.35:
            parts.append("Some key terms are present but coverage is incomplete.")
        else:
            parts.append("Missing several important concepts from the model answer.")

        if coherence >= 0.7:
            parts.append("Answer is well-structured and coherent.")
        elif coherence >= 0.45:
            parts.append("Answer structure is acceptable but could be clearer.")
        else:
            parts.append("Answer lacks coherence or sufficient elaboration.")

        if weighted >= 0.85:
            parts.append("Overall: Excellent response.")
        elif weighted >= 0.65:
            parts.append("Overall: Satisfactory response with room for improvement.")
        else:
            parts.append("Overall: Needs significant improvement.")

        return " ".join(parts)

    def build_detailed_report(
        self,
        model_answer: str,
        student_answer: str,
        ocr_confidence: Optional[float] = None,
    ) -> DetailedReport:
        model_tokens = self._tokenize_words(model_answer)
        student_tokens = self._tokenize_words(student_answer)
        matched_keywords = sorted(model_tokens.intersection(student_tokens))
        missing_keywords = sorted(model_tokens - student_tokens)

        matched_concepts: list[str] = []
        partial_concepts: list[str] = []
        missing_concepts: list[str] = []

        for concept in self._split_concepts(model_answer):
            similarity = self._concept_similarity(concept, student_answer)
            snippet = concept[:120] + ("..." if len(concept) > 120 else "")
            if similarity >= 0.72:
                matched_concepts.append(snippet)
            elif similarity >= 0.45:
                partial_concepts.append(snippet)
            else:
                missing_concepts.append(snippet)

        sentences = [s.strip() for s in re.split(r"[.!?]+", student_answer) if s.strip()]
        word_count = len(student_answer.split())

        strengths: list[str] = []
        weaknesses: list[str] = []

        if matched_concepts:
            strengths.append(f"Covered {len(matched_concepts)} key concept(s) from the model answer.")
        if matched_keywords:
            strengths.append(f"Used {len(matched_keywords)} important term(s): {', '.join(matched_keywords[:8])}.")
        if word_count >= 30:
            strengths.append(f"Provided a substantive written response ({word_count} words).")

        if missing_concepts:
            weaknesses.append(f"Did not adequately address {len(missing_concepts)} expected concept(s).")
        if missing_keywords:
            weaknesses.append(
                f"Missing key terms: {', '.join(missing_keywords[:10])}."
            )
        if partial_concepts:
            weaknesses.append(f"Partially addressed {len(partial_concepts)} concept(s) — needs more detail.")

        ocr_note = None
        if ocr_confidence is not None:
            if ocr_confidence >= 0.8:
                ocr_note = "Handwriting/scan quality is good — OCR extraction is reliable."
            elif ocr_confidence >= 0.6:
                ocr_note = "Moderate scan quality. Some words may need teacher verification."
            else:
                ocr_note = "Low OCR confidence — please verify extracted text against the original paper."

        return DetailedReport(
            matched_concepts=matched_concepts,
            missing_concepts=missing_concepts,
            partial_concepts=partial_concepts,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            strengths=strengths or ["Student attempted the question."],
            weaknesses=weaknesses or ["No major gaps identified."],
            word_count=word_count,
            sentence_count=len(sentences),
            ocr_quality_note=ocr_note,
        )

    def score_answer(
        self,
        model_answer: str,
        student_answer: str,
        max_score: float = 10.0,
        ocr_confidence: Optional[float] = None,
    ) -> tuple[float, ScoreBreakdown, str, DetailedReport]:
        model_norm = self._normalize_text(model_answer)
        student_norm = self._normalize_text(student_answer)

        if not student_norm:
            breakdown = ScoreBreakdown(
                semantic_similarity=0.0,
                keyword_coverage=0.0,
                coherence_score=0.0,
                weighted_score=0.0,
            )
            report = self.build_detailed_report(model_answer, "", ocr_confidence)
            return 0.0, breakdown, "No answer provided.", report

        semantic = self._semantic_similarity(model_norm, student_norm)
        keywords = self._keyword_coverage(model_norm, student_norm)
        coherence = self._coherence_score(student_norm)

        weighted = 0.6 * semantic + 0.25 * keywords + 0.15 * coherence
        weighted = max(0.0, min(1.0, weighted))
        final_score = round(weighted * max_score, 2)

        breakdown = ScoreBreakdown(
            semantic_similarity=round(semantic, 4),
            keyword_coverage=round(keywords, 4),
            coherence_score=round(coherence, 4),
            weighted_score=round(weighted, 4),
        )
        feedback = self._generate_feedback(semantic, keywords, coherence, weighted)
        report = self.build_detailed_report(model_answer, student_answer, ocr_confidence)

        return final_score, breakdown, feedback, report


@lru_cache
def get_scoring_service() -> ScoringService:
    return ScoringService(settings.scoring_model)
