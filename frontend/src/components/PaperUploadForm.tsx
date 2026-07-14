import { FormEvent, useRef, useState } from "react";
import { Camera, FileUp, Loader2 } from "lucide-react";
import { api } from "@/api";
import { PaperPreviews, SubmissionResult } from "@/components/SubmissionDetails";
import type { OCRPreview, Submission } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface PaperUploadFormProps {
  questionId: number;
  onSuccess?: (result: Submission) => void;
}

export default function PaperUploadForm({ questionId, onSuccess }: PaperUploadFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const [studentName, setStudentName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ocrPreview, setOcrPreview] = useState<OCRPreview | null>(null);
  const [extractedText, setExtractedText] = useState("");
  const [scanning, setScanning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Submission | null>(null);

  const handleFileSelect = async (file: File | null) => {
    if (!file) return;
    setSelectedFile(file);
    setOcrPreview(null);
    setExtractedText("");
    setResult(null);
    setScanning(true);
    setError("");
    try {
      const preview = await api.previewPaperOcr(questionId, file);
      setOcrPreview(preview);
      setExtractedText(preview.full_text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OCR scan failed");
    } finally {
      setScanning(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please upload a PDF or photo of the student paper.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const submission = await api.submitPaper(questionId, {
        student_name: studentName,
        student_id: studentId || undefined,
        file: selectedFile,
        answer_override: extractedText,
      });
      setResult(submission);
      onSuccess?.(submission);
      setStudentName("");
      setStudentId("");
      setSelectedFile(null);
      setOcrPreview(null);
      setExtractedText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Paper scoring failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="sname">Student name</Label>
          <Input
            id="sname"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="sid">Student ID (optional)</Label>
          <Input id="sid" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border bg-background/60 p-6">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp,.bmp,application/pdf,image/*"
          className="hidden"
          onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
        />

        {!selectedFile ? (
          <div className="text-center">
            <p className="font-display text-lg font-semibold">Upload student paper</p>
            <p className="mt-1 text-sm text-muted-foreground">
              PDF, JPG, or PNG — or take a photo of handwriting
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Button type="button" onClick={() => fileInputRef.current?.click()}>
                <FileUp className="h-4 w-4" />
                Upload PDF / image
              </Button>
              <Button type="button" variant="outline" onClick={() => cameraInputRef.current?.click()}>
                <Camera className="h-4 w-4" />
                Take photo
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <p className="font-medium">{selectedFile.name}</p>
            <span className="text-xs text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(0)} KB
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedFile(null);
                setOcrPreview(null);
                setExtractedText("");
              }}
            >
              Change file
            </Button>
          </div>
        )}
      </div>

      {scanning && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Reading paper with OCR…
        </p>
      )}

      {ocrPreview && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant={
                ocrPreview.average_confidence >= 0.7
                  ? "success"
                  : ocrPreview.average_confidence >= 0.5
                    ? "warn"
                    : "destructive"
              }
            >
              OCR {(ocrPreview.average_confidence * 100).toFixed(0)}% · {ocrPreview.ocr_quality}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {ocrPreview.page_count} page(s) · {ocrPreview.word_count} words
            </span>
          </div>

          <PaperPreviews pages={ocrPreview.pages} />

          {ocrPreview.low_confidence_words.length > 0 && (
            <Alert>
              <AlertDescription>
                Unclear words — verify manually: {ocrPreview.low_confidence_words.join(", ")}
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="extracted">Extracted text</Label>
            <Textarea
              id="extracted"
              rows={8}
              value={extractedText}
              onChange={(e) => setExtractedText(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              Edit if OCR misread the handwriting before scoring.
            </p>
          </div>
        </div>
      )}

      <Button
        type="submit"
        disabled={submitting || scanning || !selectedFile || extractedText.length < 5}
      >
        {submitting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Scoring…
          </>
        ) : (
          "Score written paper"
        )}
      </Button>

      {result && (
        <div className="space-y-3 rounded-lg border border-border bg-background p-4">
          <h3 className="font-display text-xl font-semibold">
            Score: {result.score} / {result.max_score}
          </h3>
          <SubmissionResult submission={result} />
        </div>
      )}
    </form>
  );
}
