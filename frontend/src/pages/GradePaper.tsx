import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "@/api";
import PaperUploadForm from "@/components/PaperUploadForm";
import type { Question } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

export default function GradePaper() {
  const [searchParams] = useSearchParams();
  const preselected = searchParams.get("question");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionId, setQuestionId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getQuestions()
      .then((qs) => {
        setQuestions(qs);
        if (preselected && qs.some((q) => q.id === Number(preselected))) {
          setQuestionId(preselected);
        } else if (qs.length > 0) {
          setQuestionId(String(qs[0].id));
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [preselected]);

  const selected = questions.find((q) => String(q.id) === questionId);

  if (loading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          OCR + scoring
        </p>
        <h1 className="mt-1 font-display text-4xl font-semibold">Grade written paper</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Upload a PDF or photograph of a handwritten or printed answer. OCR extracts the text;
          you can edit it before scoring.
        </p>
      </header>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {questions.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted-foreground">
            Create a question first, then upload student papers.
          </p>
          <Button asChild className="mt-4">
            <Link to="/questions/new">New question</Link>
          </Button>
        </div>
      ) : (
        <>
          <section className="space-y-4 rounded-lg border border-border bg-card p-5">
            <div className="space-y-2">
              <Label>Select question</Label>
              <Select value={questionId} onValueChange={setQuestionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a question" />
                </SelectTrigger>
                <SelectContent>
                  {questions.map((q) => (
                    <SelectItem key={q.id} value={String(q.id)}>
                      {q.title} ({q.subject}) — {q.max_score} pts
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selected && (
              <>
                <Separator />
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Prompt: </span>
                  {selected.question_text}
                </p>
              </>
            )}
          </section>

          {questionId && (
            <section className="rounded-lg border border-border bg-card p-5">
              <PaperUploadForm questionId={Number(questionId)} />
            </section>
          )}
        </>
      )}
    </div>
  );
}
