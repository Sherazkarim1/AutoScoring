from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="instructor", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    title = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=False)
    model_answer = Column(Text, nullable=False)
    max_score = Column(Float, default=10.0)
    subject = Column(String(120), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship("Instructor", back_populates="questions")
    submissions = relationship("Submission", back_populates="question", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    student_name = Column(String(120), nullable=False)
    student_id = Column(String(64), nullable=True)
    answer_text = Column(Text, nullable=False)
    submission_type = Column(String(20), default="typed", nullable=False)
    source_filename = Column(String(255), nullable=True)
    source_file_path = Column(String(512), nullable=True)
    ocr_raw_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_details = Column(Text, nullable=True)
    detailed_report = Column(Text, nullable=True)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    semantic_similarity = Column(Float, nullable=False)
    keyword_coverage = Column(Float, nullable=False)
    coherence_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="submissions")
