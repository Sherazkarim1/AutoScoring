import json
from typing import Optional

from app.models import Submission
from app.schemas import DetailedReportOut, OCRPageOut, SubmissionOut
from app.services.scoring import DetailedReport


def _file_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"/api/files/{path}"


def _ocr_pages_from_details(details: Optional[str]) -> Optional[list[OCRPageOut]]:
    if not details:
        return None
    try:
        payload = json.loads(details)
        pages = []
        for page in payload.get("pages", []):
            preview = page.get("preview_filename")
            pages.append(
                OCRPageOut(
                    page_number=page["page_number"],
                    text=page["text"],
                    confidence=page["confidence"],
                    lines=page["lines"],
                    preview_url=_file_url(preview),
                )
            )
        return pages
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def submission_to_out(submission: Submission, breakdown=None) -> SubmissionOut:
    detailed = None
    if submission.detailed_report:
        try:
            report = DetailedReport.from_json(submission.detailed_report)
            detailed = DetailedReportOut(**report.__dict__)
        except (json.JSONDecodeError, TypeError):
            pass

    result = SubmissionOut(
        id=submission.id,
        question_id=submission.question_id,
        student_name=submission.student_name,
        student_id=submission.student_id,
        answer_text=submission.answer_text,
        submission_type=submission.submission_type or "typed",
        source_filename=submission.source_filename,
        source_file_url=_file_url(submission.source_file_path),
        ocr_raw_text=submission.ocr_raw_text,
        ocr_confidence=submission.ocr_confidence,
        score=submission.score,
        max_score=submission.max_score,
        semantic_similarity=submission.semantic_similarity,
        keyword_coverage=submission.keyword_coverage,
        coherence_score=submission.coherence_score,
        feedback=submission.feedback,
        created_at=submission.created_at,
        breakdown=breakdown,
        detailed_report=detailed,
        ocr_pages=_ocr_pages_from_details(submission.ocr_details),
    )
    return result
