"""Seed demo instructor, questions, and sample submissions."""

from app.auth import get_password_hash
from app.database import SessionLocal, engine
from app.models import Base, Instructor, Question, Submission

DEMO_EMAIL = "instructor@kiu.edu.pk"
DEMO_PASSWORD = "password123"


def seed():
    from app.services.scoring import get_scoring_service

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    scorer = get_scoring_service()

    try:
        instructor = db.query(Instructor).filter(Instructor.email == DEMO_EMAIL).first()
        if not instructor:
            instructor = Instructor(
                name="Dr. Imran",
                email=DEMO_EMAIL,
                hashed_password=get_password_hash(DEMO_PASSWORD),
            )
            db.add(instructor)
            db.commit()
            db.refresh(instructor)
            print(f"Created demo instructor: {DEMO_EMAIL} / {DEMO_PASSWORD}")

        if db.query(Question).filter(Question.instructor_id == instructor.id).count() == 0:
            questions_data = [
                {
                    "title": "What is Machine Learning?",
                    "question_text": "Define machine learning and explain its main types with brief examples.",
                    "model_answer": (
                        "Machine learning is a branch of artificial intelligence that enables "
                        "systems to learn patterns from data without being explicitly programmed. "
                        "The main types are supervised learning (labeled data, e.g. classification), "
                        "unsupervised learning (finding patterns in unlabeled data, e.g. clustering), "
                        "and reinforcement learning (learning through rewards and penalties)."
                    ),
                    "max_score": 10.0,
                    "subject": "Computer Science",
                },
                {
                    "title": "Explain the Water Cycle",
                    "question_text": "Describe the stages of the water cycle and their importance.",
                    "model_answer": (
                        "The water cycle includes evaporation (water turns to vapor from oceans and lakes), "
                        "condensation (vapor forms clouds), precipitation (rain or snow falls), "
                        "and collection (water returns to bodies of water). "
                        "It is important because it distributes fresh water, supports ecosystems, "
                        "and regulates Earth's climate."
                    ),
                    "max_score": 10.0,
                    "subject": "Environmental Science",
                },
            ]

            sample_answers = [
                [
                    ("Ali Khan", "Machine learning lets computers learn from data. Types include supervised, unsupervised, and reinforcement learning."),
                    ("Sara Ahmed", "ML is AI that learns automatically. Supervised uses labels, unsupervised finds hidden patterns."),
                ],
                [
                    ("Bilal Hussain", "Water evaporates, forms clouds, rains, and collects in rivers. It keeps the environment balanced."),
                ],
            ]

            for idx, qdata in enumerate(questions_data):
                question = Question(instructor_id=instructor.id, **qdata)
                db.add(question)
                db.commit()
                db.refresh(question)

                for student_name, answer in sample_answers[idx]:
                    score, breakdown, feedback, report = scorer.score_answer(
                        question.model_answer, answer, question.max_score
                    )
                    submission = Submission(
                        question_id=question.id,
                        student_name=student_name,
                        answer_text=answer,
                        submission_type="typed",
                        detailed_report=report.to_json(),
                        score=score,
                        max_score=question.max_score,
                        semantic_similarity=breakdown.semantic_similarity,
                        keyword_coverage=breakdown.keyword_coverage,
                        coherence_score=breakdown.coherence_score,
                        feedback=feedback,
                    )
                    db.add(submission)

                db.commit()
                print(f"Seeded question: {qdata['title']}")

        print("Database seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
