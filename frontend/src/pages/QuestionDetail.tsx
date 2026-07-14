import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2, Pencil } from "lucide-react";
import { api } from "@/api";
import {
  DetailedReportView,
  Metric,
  PaperPreviews,
  SubmissionResult,
} from "@/components/SubmissionDetails";
import type { Question, Submission } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import PaperUploadForm from "@/components/PaperUploadForm";

export default function QuestionDetail() {
  const { id } = useParams();
  const questionId = Number(id);

  const [question, setQuestion] = useState<Question | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [studentName, setStudentName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [answerText, setAnswerText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<Submission | null>(null);

  const load = () => {
    Promise.all([api.getQuestion(questionId), api.getSubmissions(questionId)])
      .then(([q, subs]) => {
        setQuestion(q);
        setSubmissions(subs);
      })
      .catch((e) => setError(e.message));
  };

  useEffect(load, [questionId]);

  const handleTypedSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setLastResult(null);
    try {
      const result = await api.submitAnswer(questionId, {
        student_name: studentName,
        student_id: studentId || undefined,
        answer_text: answerText,
      });
      setLastResult(result);
      setStudentName("");
      setStudentId("");
      setAnswerText("");
      setShowForm(false);
      load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !question) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  if (!question) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge variant="secondary">{question.subject}</Badge>
          <h1 className="mt-2 font-display text-4xl font-semibold">{question.title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Max {question.max_score} pts · {submissions.length} submissions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link to={`/questions/${id}/edit`}>
              <Pencil className="h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "Score answer"}
          </Button>
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="font-display text-lg font-semibold">Question</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{question.question_text}</p>
        </section>
        <section>
          <h2 className="font-display text-lg font-semibold">Model answer</h2>
          <p className="mt-2 border-l-2 border-primary pl-3 text-sm leading-relaxed text-muted-foreground">
            {question.model_answer}
          </p>
        </section>
      </div>

      {showForm && (
        <section className="rounded-lg border border-border bg-card p-5">
          <Tabs defaultValue="paper">
            <TabsList>
              <TabsTrigger value="paper">Written paper</TabsTrigger>
              <TabsTrigger value="typed">Typed answer</TabsTrigger>
            </TabsList>
            <TabsContent value="paper">
              <PaperUploadForm
                questionId={questionId}
                onSuccess={(result) => {
                  setLastResult(result);
                  setShowForm(false);
                  load();
                }}
              />
            </TabsContent>
            <TabsContent value="typed">
              <form onSubmit={handleTypedSubmit} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Student name</Label>
                    <Input
                      value={studentName}
                      onChange={(e) => setStudentName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Student ID (optional)</Label>
                    <Input value={studentId} onChange={(e) => setStudentId(e.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Answer</Label>
                  <Textarea
                    rows={5}
                    value={answerText}
                    onChange={(e) => setAnswerText(e.target.value)}
                    required
                  />
                </div>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Scoring…
                    </>
                  ) : (
                    "Score answer"
                  )}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </section>
      )}

      {lastResult && (
        <section className="space-y-3 rounded-lg border border-border bg-card p-5">
          <h3 className="font-display text-xl font-semibold">
            Latest score: {lastResult.score} / {lastResult.max_score}
            {lastResult.submission_type === "paper" && (
              <Badge variant="secondary" className="ml-2 align-middle">
                Written paper
              </Badge>
            )}
          </h3>
          <SubmissionResult submission={lastResult} />
        </section>
      )}

      <section>
        <h2 className="font-display text-2xl font-semibold">All submissions</h2>
        {submissions.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No submissions yet.</p>
        ) : (
          <ul className="mt-4 space-y-4">
            {submissions.map((s) => (
              <li key={s.id} className="rounded-lg border border-border bg-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">
                      {s.student_name}
                      {s.student_id && (
                        <span className="text-muted-foreground"> · {s.student_id}</span>
                      )}
                    </p>
                    {s.submission_type === "paper" && (
                      <Badge variant="outline" className="mt-1">
                        Written paper
                      </Badge>
                    )}
                  </div>
                  <Badge
                    variant={
                      s.score / s.max_score >= 0.7
                        ? "success"
                        : s.score / s.max_score >= 0.5
                          ? "warn"
                          : "destructive"
                    }
                  >
                    {s.score} / {s.max_score}
                  </Badge>
                </div>

                {s.ocr_pages && s.ocr_pages.length > 0 && (
                  <div className="mt-3">
                    <PaperPreviews pages={s.ocr_pages} />
                  </div>
                )}

                <p className="mt-3 text-sm text-muted-foreground">{s.answer_text}</p>

                <div className="mt-3 flex flex-wrap gap-4">
                  <Metric label="Semantic" value={s.semantic_similarity} />
                  <Metric label="Keywords" value={s.keyword_coverage} />
                  <Metric label="Coherence" value={s.coherence_score} />
                </div>

                <p className="mt-3 rounded-md border border-border bg-background px-3 py-2 text-sm">
                  {s.feedback}
                </p>
                {s.detailed_report && <DetailedReportView report={s.detailed_report} />}
                <p className="mt-2 text-xs text-muted-foreground">
                  {new Date(s.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
