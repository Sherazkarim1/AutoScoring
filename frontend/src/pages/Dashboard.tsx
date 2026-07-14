import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FilePlus2, ScanLine } from "lucide-react";
import { api } from "@/api";
import type { DashboardStats } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

function ScoreBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="min-w-[110px] space-y-1">
      <Progress value={pct} className="h-2" />
      <p className="text-xs text-muted-foreground">
        {value.toFixed(1)} / {max}
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getStats()
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!stats) {
    return <p className="text-sm text-muted-foreground">Loading dashboard…</p>;
  }

  return (
    <div className="space-y-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Overview
          </p>
          <h1 className="mt-1 font-display text-4xl font-semibold">Dashboard</h1>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">
            Your questions, submissions, and scoring activity in one place.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild>
            <Link to="/grade-paper">
              <ScanLine className="h-4 w-4" />
              Grade paper
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/questions/new">
              <FilePlus2 className="h-4 w-4" />
              New question
            </Link>
          </Button>
        </div>
      </header>

      <section className="grid gap-8 border-y border-border py-8 sm:grid-cols-3">
        {[
          { label: "Questions", value: stats.total_questions },
          { label: "Submissions", value: stats.total_submissions },
          { label: "Average score", value: `${stats.average_score}%` },
        ].map((item) => (
          <div key={item.label}>
            <p className="text-sm text-muted-foreground">{item.label}</p>
            <p className="mt-1 font-display text-4xl font-semibold tabular-nums">{item.value}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="font-display text-2xl font-semibold">Recent submissions</h2>
        <Separator className="my-4" />
        {stats.recent_submissions.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No submissions yet. Create a question and grade an answer.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="pb-3 font-medium">Student</th>
                  <th className="pb-3 font-medium">Score</th>
                  <th className="pb-3 font-medium">Semantic</th>
                  <th className="pb-3 font-medium">Keywords</th>
                  <th className="pb-3 font-medium">Coherence</th>
                  <th className="pb-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_submissions.map((s) => (
                  <tr key={s.id} className="border-b border-border/70 align-top">
                    <td className="py-4">
                      <p className="font-medium">{s.student_name}</p>
                      <Link
                        to={`/questions/${s.question_id}`}
                        className="text-xs text-muted-foreground hover:text-primary"
                      >
                        View question
                      </Link>
                    </td>
                    <td className="py-4">
                      <ScoreBar value={s.score} max={s.max_score} />
                    </td>
                    <td className="py-4 tabular-nums">{(s.semantic_similarity * 100).toFixed(0)}%</td>
                    <td className="py-4 tabular-nums">{(s.keyword_coverage * 100).toFixed(0)}%</td>
                    <td className="py-4 tabular-nums">{(s.coherence_score * 100).toFixed(0)}%</td>
                    <td className="py-4 text-muted-foreground">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="font-display text-lg font-semibold">How scoring works</h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Typed answers and written papers are supported. Papers are read with OCR, then scored with
          BERT embeddings. Reports show matched and missing concepts, keywords, and feedback.
        </p>
      </section>
    </div>
  );
}
