import { FormEvent, useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/api";
import { DetailedReportView } from "@/components/SubmissionDetails";
import type { ScorePreview } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";

function BreakdownBar({
  label,
  value,
  weight,
}: {
  label: string;
  value: number;
  weight: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span>
          {label} <span className="text-muted-foreground">({weight})</span>
        </span>
        <span className="font-medium tabular-nums">{(value * 100).toFixed(1)}%</span>
      </div>
      <Progress value={value * 100} />
    </div>
  );
}

export default function ScorePreviewPage() {
  const [modelAnswer, setModelAnswer] = useState(
    "Photosynthesis is the process by which green plants convert sunlight, water, and carbon dioxide into glucose and oxygen. It occurs in chloroplasts and is essential for life on Earth."
  );
  const [studentAnswer, setStudentAnswer] = useState(
    "Plants use sunlight to make food from CO2 and water, releasing oxygen. This happens in chloroplasts."
  );
  const [maxScore, setMaxScore] = useState(10);
  const [result, setResult] = useState<ScorePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.previewScore({
        model_answer: modelAnswer,
        student_answer: studentAnswer,
        max_score: maxScore,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <header>
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Sandbox
        </p>
        <h1 className="mt-1 font-display text-4xl font-semibold">Score preview</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Test the NLP scoring engine without saving a submission.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-border bg-card p-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="space-y-2">
          <Label>Model answer</Label>
          <Textarea rows={5} value={modelAnswer} onChange={(e) => setModelAnswer(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label>Student answer</Label>
          <Textarea
            rows={5}
            value={studentAnswer}
            onChange={(e) => setStudentAnswer(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label>Max score</Label>
          <Input
            type="number"
            min={1}
            max={100}
            className="max-w-[120px]"
            value={maxScore}
            onChange={(e) => setMaxScore(Number(e.target.value))}
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing…
            </>
          ) : (
            "Preview score"
          )}
        </Button>
      </form>

      {result && (
        <section className="space-y-5 rounded-lg border border-border bg-card p-6">
          <div className="text-center">
            <p className="font-display text-5xl font-semibold tabular-nums text-primary">
              {result.score}
              <span className="text-2xl text-muted-foreground"> / {result.max_score}</span>
            </p>
          </div>
          <div className="space-y-3">
            <BreakdownBar
              label="Semantic similarity"
              value={result.breakdown.semantic_similarity}
              weight="60%"
            />
            <BreakdownBar
              label="Keyword coverage"
              value={result.breakdown.keyword_coverage}
              weight="25%"
            />
            <BreakdownBar label="Coherence" value={result.breakdown.coherence_score} weight="15%" />
          </div>
          <p className="rounded-md border border-border bg-background px-3 py-2 text-sm">
            {result.feedback}
          </p>
          {result.detailed_report && <DetailedReportView report={result.detailed_report} />}
        </section>
      )}
    </div>
  );
}
