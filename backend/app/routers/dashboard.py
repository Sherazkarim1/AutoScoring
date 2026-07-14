from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_instructor
from app.database import get_db
from app.models import Instructor, Question, Submission
from app.schemas import DashboardStats
from app.utils.submissions import submission_to_out

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question_ids = [
        q.id
        for q in db.query(Question.id).filter(Question.instructor_id == current.id).all()
    ]

    total_questions = len(question_ids)
    total_submissions = 0
    average_score = 0.0
    recent_submissions: list[Submission] = []

    if question_ids:
        total_submissions = (
            db.query(Submission).filter(Submission.question_id.in_(question_ids)).count()
        )
        avg = (
            db.query(func.avg(Submission.score / Submission.max_score * 100))
            .filter(Submission.question_id.in_(question_ids))
            .scalar()
        )
        average_score = round(float(avg or 0), 2)

        recent_submissions = (
            db.query(Submission)
            .filter(Submission.question_id.in_(question_ids))
            .order_by(Submission.created_at.desc())
            .limit(10)
            .all()
        )

    return DashboardStats(
        total_questions=total_questions,
        total_submissions=total_submissions,
        average_score=average_score,
        recent_submissions=[submission_to_out(s) for s in recent_submissions],
    )
