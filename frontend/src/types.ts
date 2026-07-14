export interface Instructor {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface ScoreBreakdown {
  semantic_similarity: number;
  keyword_coverage: number;
  coherence_score: number;
  weighted_score: number;
}

export interface DetailedReport {
  matched_concepts: string[];
  missing_concepts: string[];
  partial_concepts: string[];
  matched_keywords: string[];
  missing_keywords: string[];
  strengths: string[];
  weaknesses: string[];
  word_count: number;
  sentence_count: number;
  ocr_quality_note?: string | null;
}

export interface OCRLine {
  text: string;
  confidence: number;
}

export interface OCRPage {
  page_number: number;
  text: string;
  confidence: number;
  lines: OCRLine[];
  preview_url?: string | null;
}

export interface OCRPreview {
  full_text: string;
  average_confidence: number;
  word_count: number;
  page_count: number;
  pages: OCRPage[];
  low_confidence_words: string[];
  file_type: string;
  source_filename: string;
  source_file_url?: string | null;
  ocr_quality: string;
}

export interface Question {
  id: number;
  instructor_id: number;
  title: string;
  question_text: string;
  model_answer: string;
  max_score: number;
  subject: string;
  created_at: string;
  submission_count: number;
}

export interface Submission {
  id: number;
  question_id: number;
  student_name: string;
  student_id: string | null;
  answer_text: string;
  submission_type: 'typed' | 'paper';
  source_filename?: string | null;
  source_file_url?: string | null;
  ocr_raw_text?: string | null;
  ocr_confidence?: number | null;
  score: number;
  max_score: number;
  semantic_similarity: number;
  keyword_coverage: number;
  coherence_score: number;
  feedback: string;
  created_at: string;
  breakdown?: ScoreBreakdown;
  detailed_report?: DetailedReport;
  ocr_pages?: OCRPage[];
}

export interface DashboardStats {
  total_questions: number;
  total_submissions: number;
  average_score: number;
  recent_submissions: Submission[];
}

export interface ScorePreview {
  score: number;
  max_score: number;
  breakdown: ScoreBreakdown;
  feedback: string;
  detailed_report?: DetailedReport;
}
