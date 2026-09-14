import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Question, Submission
from app.schemas import QuestionOut


def parse_key_concepts(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in raw.split(",") if part.strip()]


def dump_key_concepts(concepts: list[str] | None) -> Optional[str]:
    cleaned = [str(item).strip() for item in (concepts or []) if str(item).strip()]
    return json.dumps(cleaned) if cleaned else None


def question_to_out(question: Question, db: Session) -> QuestionOut:
    count = db.query(Submission).filter(Submission.question_id == question.id).count()
    return QuestionOut(
        id=question.id,
        instructor_id=question.instructor_id,
        title=question.title,
        question_text=question.question_text,
        model_answer=question.model_answer,
        marking_rubric=question.marking_rubric,
        key_concepts=parse_key_concepts(question.key_concepts),
        source_filename=question.source_filename,
        generation_source=question.generation_source or "manual",
        max_score=question.max_score,
        subject=question.subject,
        created_at=question.created_at,
        submission_count=count,
    )
