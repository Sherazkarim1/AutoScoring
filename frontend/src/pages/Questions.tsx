import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FilePlus2, ScanLine, Trash2 } from "lucide-react";
import { api } from "@/api";
import type { Question } from "@/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function Questions() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .getQuestions()
      .then(setQuestions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Delete "${title}" and all its submissions?`)) return;
    try {
      await api.deleteQuestion(id);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Exam bank
          </p>
          <h1 className="mt-1 font-display text-4xl font-semibold">Questions</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Manage prompts and model answers for NLP scoring.
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

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading questions…</p>
      ) : questions.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-6 py-12 text-center">
          <p className="text-sm text-muted-foreground">No questions yet.</p>
          <Button asChild className="mt-4">
            <Link to="/questions/new">Create your first question</Link>
          </Button>
        </div>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {questions.map((q) => (
            <li key={q.id} className="flex flex-col gap-4 py-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">{q.subject}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {q.submission_count} submissions · max {q.max_score} pts
                  </span>
                </div>
                <h2 className="font-display text-xl font-semibold">{q.title}</h2>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{q.question_text}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" asChild>
                  <Link to={`/grade-paper?question=${q.id}`}>Upload paper</Link>
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <Link to={`/questions/${q.id}`}>Open</Link>
                </Button>
                <Button size="sm" variant="ghost" asChild>
                  <Link to={`/questions/${q.id}/edit`}>Edit</Link>
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-destructive hover:text-destructive"
                  onClick={() => handleDelete(q.id, q.title)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
