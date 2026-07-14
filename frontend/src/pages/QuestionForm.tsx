import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api } from "@/api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function QuestionForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [questionText, setQuestionText] = useState("");
  const [modelAnswer, setModelAnswer] = useState("");
  const [maxScore, setMaxScore] = useState(10);
  const [subject, setSubject] = useState("General");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .getQuestion(Number(id))
      .then((q) => {
        setTitle(q.title);
        setQuestionText(q.question_text);
        setModelAnswer(q.model_answer);
        setMaxScore(q.max_score);
        setSubject(q.subject);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const payload = {
      title,
      question_text: questionText,
      model_answer: modelAnswer,
      max_score: maxScore,
      subject,
    };
    try {
      if (isEdit) {
        await api.updateQuestion(Number(id), payload);
        navigate(`/questions/${id}`);
      } else {
        const q = await api.createQuestion(payload);
        navigate(`/questions/${q.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Question
          </p>
          <h1 className="mt-1 font-display text-4xl font-semibold">
            {isEdit ? "Edit question" : "New question"}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Define the prompt and the model answer used for comparison.
          </p>
        </div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/questions">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </Button>
      </header>

      <form onSubmit={handleSubmit} className="space-y-5 rounded-lg border border-border bg-card p-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="max">Max score</Label>
          <Input
            id="max"
            type="number"
            min={1}
            max={100}
            step={0.5}
            className="max-w-[140px]"
            value={maxScore}
            onChange={(e) => setMaxScore(Number(e.target.value))}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="qtext">Question text</Label>
          <Textarea
            id="qtext"
            rows={4}
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="model">Model answer</Label>
          <Textarea
            id="model"
            rows={6}
            value={modelAnswer}
            onChange={(e) => setModelAnswer(e.target.value)}
            required
          />
          <p className="text-xs text-muted-foreground">
            Reference answer used for semantic similarity scoring.
          </p>
        </div>

        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : isEdit ? "Update question" : "Create question"}
        </Button>
      </form>
    </div>
  );
}
