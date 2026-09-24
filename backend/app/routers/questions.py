from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_instructor
from app.config import settings
from app.database import get_db
from app.models import Instructor, Question, Submission
from app.schemas import (
    BulkQuestionCreate,
    DetailedReportOut,
    GeneratedQuestionDraft,
    OCRLineOut,
    OCRPageOut,
    OCRPreviewResponse,
    PaperIngestResponse,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    ScorePreviewRequest,
    ScorePreviewResponse,
    SubmissionCreate,
    SubmissionOut,
)
from app.services.extraction import extract_from_ocr
from app.services.ocr import get_ocr_service
from app.services.scoring import get_scoring_service
from app.utils.questions import dump_key_concepts, parse_key_concepts, question_to_out
from app.utils.submissions import submission_to_out, _file_url

router = APIRouter(prefix="/questions", tags=["Questions"])


def _get_owned_question(question_id: int, instructor_id: int, db: Session) -> Question:
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.instructor_id == instructor_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


def _validate_upload(file: UploadFile, content: bytes) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_upload_mb}MB.",
        )


def _ocr_quality_label(confidence: float) -> str:
    if confidence >= 0.8:
        return "Good — handwriting/print is clear"
    if confidence >= 0.6:
        return "Fair — some words may need verification"
    return "Low — please verify extracted text against the paper"


def _ocr_to_preview(ocr_result) -> OCRPreviewResponse:
    pages = [
        OCRPageOut(
            page_number=page.page_number,
            text=page.text,
            confidence=page.confidence,
            lines=[OCRLineOut(text=line.text, confidence=line.confidence) for line in page.lines],
            preview_url=_file_url(page.preview_filename),
        )
        for page in ocr_result.pages
    ]
    return OCRPreviewResponse(
        full_text=ocr_result.full_text,
        average_confidence=ocr_result.average_confidence,
        word_count=ocr_result.word_count,
        page_count=ocr_result.page_count,
        pages=pages,
        low_confidence_words=ocr_result.low_confidence_words,
        file_type=ocr_result.file_type,
        source_filename=ocr_result.source_filename,
        source_file_url=_file_url(ocr_result.stored_path),
        ocr_quality=_ocr_quality_label(ocr_result.average_confidence),
        ocr_engine=getattr(ocr_result, "ocr_engine", "easyocr"),
    )


def _create_question_row(
    instructor_id: int,
    payload: QuestionCreate,
    db: Session,
) -> Question:
    question = Question(
        instructor_id=instructor_id,
        title=payload.title,
        question_text=payload.question_text,
        model_answer=payload.model_answer,
        marking_rubric=payload.marking_rubric,
        key_concepts=dump_key_concepts(payload.key_concepts),
        max_score=payload.max_score,
        subject=payload.subject,
        generation_source=payload.generation_source or "manual",
        source_filename=payload.source_filename,
        source_file_path=payload.source_file_path,
        ocr_raw_text=payload.ocr_raw_text,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("", response_model=list[QuestionOut])
def list_questions(
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(Question)
        .filter(Question.instructor_id == current.id)
        .order_by(Question.created_at.desc())
        .all()
    )
    return [question_to_out(q, db) for q in questions]


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _create_question_row(current.id, payload, db)
    return question_to_out(question, db)


@router.post("/ingest-paper", response_model=PaperIngestResponse)
async def ingest_question_paper(
    file: UploadFile = File(...),
    subject: str = Form(default="General"),
    current: Instructor = Depends(get_current_instructor),
):
    content = await file.read()
    _validate_upload(file, content)
    try:
        ocr_result = get_ocr_service().extract_from_file(
            content,
            file.filename,
            store_file=True,
            engine=settings.question_ocr_engine,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len((ocr_result.full_text or "").strip()) < 12:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from the question paper. Try a clearer scan.",
        )

    try:
        extracted = extract_from_ocr(ocr_result.full_text, subject=subject or "General")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    drafts = [
        GeneratedQuestionDraft(
            title=item.title,
            question_text=item.question_text,
            model_answer=item.model_answer,
            marking_rubric=item.marking_rubric,
            key_concepts=item.key_concepts,
            max_score=item.max_score,
            subject=item.subject or subject or "General",
        )
        for item in extracted.questions
    ]
    return PaperIngestResponse(
        ocr=_ocr_to_preview(ocr_result),
        generation_source=extracted.source,
        warning=extracted.warning,
        questions=drafts,
    )


@router.post("/bulk", response_model=list[QuestionOut], status_code=status.HTTP_201_CREATED)
def bulk_create_questions(
    payload: BulkQuestionCreate,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    if not payload.questions:
        raise HTTPException(status_code=400, detail="No questions to save")
    for index, draft in enumerate(payload.questions, start=1):
        if not (draft.model_answer or "").strip():
            raise HTTPException(
                status_code=400,
                detail=f"Question {index} is missing a model answer. Paste your official answer key before saving.",
            )
    created: list[QuestionOut] = []
    for draft in payload.questions:
        row = _create_question_row(
            current.id,
            QuestionCreate(
                title=draft.title,
                question_text=draft.question_text,
                model_answer=draft.model_answer,
                marking_rubric=draft.marking_rubric,
                key_concepts=draft.key_concepts,
                max_score=draft.max_score,
                subject=draft.subject or payload.subject,
                generation_source=payload.generation_source,
                source_filename=payload.source_filename,
                source_file_path=payload.source_file_path,
                ocr_raw_text=payload.ocr_raw_text,
            ),
            db,
        )
        created.append(question_to_out(row, db))
    return created


@router.post("/preview-score", response_model=ScorePreviewResponse)
def preview_score(
    payload: ScorePreviewRequest,
    _: Instructor = Depends(get_current_instructor),
):
    scorer = get_scoring_service()
    score, breakdown, feedback, report = scorer.score_answer(
        payload.model_answer,
        payload.student_answer,
        payload.max_score,
    )
    return ScorePreviewResponse(
        score=score,
        max_score=payload.max_score,
        breakdown=breakdown,
        feedback=feedback,
        detailed_report=DetailedReportOut(**report.__dict__),
    )


@router.post("/{question_id}/paper/ocr", response_model=OCRPreviewResponse)
async def preview_paper_ocr(
    question_id: int,
    file: UploadFile = File(...),
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
    engine: str = Query(default=None),
):
    _get_owned_question(question_id, current.id, db)
    content = await file.read()
    _validate_upload(file, content)

    try:
        ocr_result = get_ocr_service().extract_from_file(
            content,
            file.filename,
            store_file=True,
            engine=engine or settings.student_ocr_engine,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _ocr_to_preview(ocr_result)


@router.post("/{question_id}/submissions/paper", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def submit_paper_answer(
    question_id: int,
    student_name: str = Form(...),
    student_id: str = Form(default=""),
    file: UploadFile = File(...),
    answer_override: str = Form(default=""),
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _get_owned_question(question_id, current.id, db)
    content = await file.read()
    _validate_upload(file, content)

    try:
        ocr_result = get_ocr_service().extract_from_file(
            content,
            file.filename,
            store_file=True,
            engine=settings.student_ocr_engine,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    answer_text = answer_override.strip() or ocr_result.full_text
    if len(answer_text) < 5:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from the paper. Try a clearer photo or edit the text manually.",
        )

    scorer = get_scoring_service()
    score, breakdown, feedback, report = scorer.score_answer(
        question.model_answer,
        answer_text,
        question.max_score,
        ocr_confidence=ocr_result.average_confidence,
        key_concepts=parse_key_concepts(question.key_concepts),
    )

    submission = Submission(
        question_id=question.id,
        student_name=student_name,
        student_id=student_id or None,
        answer_text=answer_text,
        submission_type="paper",
        source_filename=ocr_result.source_filename,
        source_file_path=ocr_result.stored_path,
        ocr_raw_text=ocr_result.full_text,
        ocr_confidence=ocr_result.average_confidence,
        ocr_details=ocr_result.to_json(),
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
    db.refresh(submission)

    return submission_to_out(submission, breakdown)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _get_owned_question(question_id, current.id, db)
    return question_to_out(question, db)


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    payload: QuestionUpdate,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _get_owned_question(question_id, current.id, db)
    data = payload.model_dump(exclude_unset=True)
    if "key_concepts" in data:
        data["key_concepts"] = dump_key_concepts(data["key_concepts"])
    for field, value in data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question_to_out(question, db)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _get_owned_question(question_id, current.id, db)
    db.delete(question)
    db.commit()


@router.get("/{question_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    question_id: int,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    _get_owned_question(question_id, current.id, db)

    submissions = (
        db.query(Submission)
        .filter(Submission.question_id == question_id)
        .order_by(Submission.created_at.desc())
        .all()
    )
    return [submission_to_out(s) for s in submissions]


@router.post("/{question_id}/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def submit_answer(
    question_id: int,
    payload: SubmissionCreate,
    current: Instructor = Depends(get_current_instructor),
    db: Session = Depends(get_db),
):
    question = _get_owned_question(question_id, current.id, db)

    scorer = get_scoring_service()
    score, breakdown, feedback, report = scorer.score_answer(
        question.model_answer,
        payload.answer_text,
        question.max_score,
        key_concepts=parse_key_concepts(question.key_concepts),
    )

    submission = Submission(
        question_id=question.id,
        student_name=payload.student_name,
        student_id=payload.student_id,
        answer_text=payload.answer_text,
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
    db.refresh(submission)

    return submission_to_out(submission, breakdown)
