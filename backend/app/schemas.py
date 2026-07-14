from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InstructorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)


class InstructorLogin(BaseModel):
    email: EmailStr
    password: str


class InstructorOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    question_text: str = Field(min_length=10)
    model_answer: str = Field(min_length=10)
    max_score: float = Field(default=10.0, gt=0, le=100)
    subject: str = Field(default="General", max_length=120)


class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    question_text: Optional[str] = Field(default=None, min_length=10)
    model_answer: Optional[str] = Field(default=None, min_length=10)
    max_score: Optional[float] = Field(default=None, gt=0, le=100)
    subject: Optional[str] = Field(default=None, max_length=120)


class QuestionOut(BaseModel):
    id: int
    instructor_id: int
    title: str
    question_text: str
    model_answer: str
    max_score: float
    subject: str
    created_at: datetime
    submission_count: int = 0

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    student_name: str = Field(min_length=2, max_length=120)
    student_id: Optional[str] = Field(default=None, max_length=64)
    answer_text: str = Field(min_length=5)


class ScoreBreakdown(BaseModel):
    semantic_similarity: float
    keyword_coverage: float
    coherence_score: float
    weighted_score: float


class DetailedReportOut(BaseModel):
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


class OCRLineOut(BaseModel):
    text: str
    confidence: float


class OCRPageOut(BaseModel):
    page_number: int
    text: str
    confidence: float
    lines: list[OCRLineOut]
    preview_url: Optional[str] = None


class OCRPreviewResponse(BaseModel):
    full_text: str
    average_confidence: float
    word_count: int
    page_count: int
    pages: list[OCRPageOut]
    low_confidence_words: list[str]
    file_type: str
    source_filename: str
    source_file_url: Optional[str] = None
    ocr_quality: str


class SubmissionOut(BaseModel):
    id: int
    question_id: int
    student_name: str
    student_id: Optional[str]
    answer_text: str
    submission_type: str = "typed"
    source_filename: Optional[str] = None
    source_file_url: Optional[str] = None
    ocr_raw_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    score: float
    max_score: float
    semantic_similarity: float
    keyword_coverage: float
    coherence_score: float
    feedback: str
    created_at: datetime
    breakdown: Optional[ScoreBreakdown] = None
    detailed_report: Optional[DetailedReportOut] = None
    ocr_pages: Optional[list[OCRPageOut]] = None

    class Config:
        from_attributes = True


class ScorePreviewRequest(BaseModel):
    model_answer: str = Field(min_length=10)
    student_answer: str = Field(min_length=5)
    max_score: float = Field(default=10.0, gt=0, le=100)


class ScorePreviewResponse(BaseModel):
    score: float
    max_score: float
    breakdown: ScoreBreakdown
    feedback: str
    detailed_report: DetailedReportOut


class DashboardStats(BaseModel):
    total_questions: int
    total_submissions: int
    average_score: float
    recent_submissions: list[SubmissionOut]
