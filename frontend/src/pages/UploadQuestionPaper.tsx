import { FormEvent, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FileUp, Loader2, Trash2 } from "lucide-react";
import { api } from "@/api";
import { PaperPreviews } from "@/components/SubmissionDetails";
import type { GeneratedQuestionDraft, OCRPreview } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function UploadQuestionPaper() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("General");
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [source, setSource] = useState("");
  const [ocr, setOcr] = useState<OCRPreview | null>(null);
  const [drafts, setDrafts] = useState<GeneratedQuestionDraft[]>([]);

  const handleScan = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Upload a PDF or photo of the question paper.");
      return;
    }
    setScanning(true);
    setError("");
    setWarning("");
    try {
      const result = await api.ingestQuestionPaper(file, subject);
      setOcr(result.ocr);
      setDrafts(result.questions);
      setSource(result.generation_source);
      setWarning(result.warning || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read the question paper");
    } finally {
      setScanning(false);
    }
  };

  const updateDraft = (index: number, patch: Partial<GeneratedQuestionDraft>) => {
    setDrafts((current) =>
      current.map((item, i) => (i === index ? { ...item, ...patch } : item))
    );
  };

  const removeDraft = (index: number) => {
    setDrafts((current) => current.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!drafts.length) return;
    const missing = drafts.findIndex((d) => !d.model_answer.trim());
    if (missing >= 0) {
      setError(
        `Question ${missing + 1} has no model answer. Paste your official answer key before saving.`
      );
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api.bulkCreateQuestions({
        questions: drafts.map((item) => ({ ...item, subject: item.subject || subject })),
        subject,
        source_filename: ocr?.source_filename,
        ocr_raw_text: ocr?.full_text,
        generation_source: source || "paper",
      });
      navigate("/questions");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save questions");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Question paper pipeline
        </p>
        <h1 className="mt-1 font-display text-4xl font-semibold">Upload question paper</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          OCR extracts questions from the paper. You must paste your official model answer
          (answer key) for each question before saving — scoring compares the student to that key.
        </p>
      </header>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {warning && (
        <Alert>
          <AlertDescription>{warning}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleScan} className="space-y-4 rounded-lg border border-border bg-card p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Question paper (PDF or image)</Label>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,image/*"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <Button type="button" variant="outline" onClick={() => fileInputRef.current?.click()}>
              <FileUp className="h-4 w-4" />
              {file ? file.name : "Choose file"}
            </Button>
          </div>
          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input id="subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
        </div>
        <Button type="submit" disabled={scanning}>
          {scanning ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Reading paper…
            </>
          ) : (
            "Extract questions and create drafts"
          )}
        </Button>
        <p className="text-xs text-muted-foreground">
          Printed papers use EasyOCR (faster). Always paste your real answer key into Model answer
          before saving — otherwise a correct student answer can still get a low score.
        </p>
      </form>

      {ocr && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="font-display text-2xl font-semibold">Extracted text</h2>
            <Badge variant="secondary">{ocr.ocr_engine || "easyocr"}</Badge>
          </div>
          <PaperPreviews pages={ocr.pages} />
          <Textarea rows={6} value={ocr.full_text} readOnly />
        </section>
      )}

      {drafts.length > 0 && (
        <section className="space-y-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold">Extracted questions</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Source: extracted draft · edit the model answer before save
              </p>
            </div>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : `Save ${drafts.length} question${drafts.length === 1 ? "" : "s"}`}
            </Button>
          </div>

          {drafts.map((draft, index) => (
            <div key={index} className="space-y-4 rounded-lg border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3">
                <p className="font-medium">Question {index + 1}</p>
                <Button type="button" variant="ghost" size="sm" onClick={() => removeDraft(index)}>
                  <Trash2 className="h-4 w-4" />
                  Remove
                </Button>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2 sm:col-span-2">
                  <Label>Title</Label>
                  <Input
                    value={draft.title}
                    onChange={(e) => updateDraft(index, { title: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max score</Label>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    value={draft.max_score}
                    onChange={(e) => updateDraft(index, { max_score: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Question text</Label>
                <Textarea
                  rows={3}
                  value={draft.question_text}
                  onChange={(e) => updateDraft(index, { question_text: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Model answer</Label>
                <Textarea
                  rows={5}
                  value={draft.model_answer}
                  onChange={(e) => updateDraft(index, { model_answer: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Marking rubric</Label>
                <Textarea
                  rows={3}
                  value={draft.marking_rubric}
                  onChange={(e) => updateDraft(index, { marking_rubric: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Key concepts (comma-separated)</Label>
                <Input
                  value={draft.key_concepts.join(", ")}
                  onChange={(e) =>
                    updateDraft(index, {
                      key_concepts: e.target.value
                        .split(",")
                        .map((part) => part.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
            </div>
          ))}
        </section>
      )}

      <p className="text-sm text-muted-foreground">
        Prefer typing a question yourself?{" "}
        <Link to="/questions/new" className="font-medium text-primary hover:underline">
          Create manually
        </Link>
      </p>
    </div>
  );
}
