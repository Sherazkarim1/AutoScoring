import { Separator } from "@/components/ui/separator";

const TEAM = [
  { name: "Sheraz Karim", reg: "2262", role: "NLP model & backend API" },
  { name: "Liliyom", reg: "2249", role: "Frontend dashboard & dataset work" },
];

export default function About() {
  return (
    <div className="space-y-12">
      <header className="flex flex-wrap items-start gap-6">
        <img
          src="/kiu_logo.png"
          alt="Karakoram International University"
          className="h-24 w-24 shrink-0 object-contain"
        />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Final year project
          </p>
          <h1 className="mt-1 font-display text-4xl font-semibold leading-tight">About AutoScoring</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            An automatic subjective question scoring system for Karakoram International University,
            Gilgit-Baltistan — Department of Computer Science.
          </p>
        </div>
      </header>

      <section className="max-w-2xl space-y-3">
        <h2 className="font-display text-2xl font-semibold">What it does</h2>
        <Separator />
        <p className="text-sm leading-relaxed text-muted-foreground">
          Manual marking of subjective answers is slow and easy to skew. AutoScoring reads student
          responses — typed or written on paper — and scores them with NLP. BERT embeddings compare
          each answer to the model solution for meaning, keyword coverage, and coherence, then show
          instructors a transparent breakdown they can review.
        </p>
      </section>

      <section className="max-w-2xl space-y-3">
        <h2 className="font-display text-2xl font-semibold">How scoring works</h2>
        <Separator />
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>
            <span className="font-medium text-foreground">Semantic similarity (60%)</span> — transformer
            embeddings compare the student answer to the model answer.
          </li>
          <li>
            <span className="font-medium text-foreground">Keyword coverage (25%)</span> — required terms
            and concepts from the rubric.
          </li>
          <li>
            <span className="font-medium text-foreground">Coherence (15%)</span> — structure and
            readability of the response.
          </li>
          <li>
            <span className="font-medium text-foreground">Paper OCR</span> — PDFs and photos of
            handwritten scripts are transcribed before scoring.
          </li>
        </ul>
      </section>

      <section className="max-w-2xl space-y-3">
        <h2 className="font-display text-2xl font-semibold">Project team</h2>
        <Separator />
        <div className="space-y-5">
          {TEAM.map((m) => (
            <div key={m.reg}>
              <p className="font-medium text-foreground">{m.name}</p>
              <p className="text-sm text-muted-foreground">
                Reg. No. {m.reg} · {m.role}
              </p>
            </div>
          ))}
          <div className="border-t border-border pt-5">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Supervisor</p>
            <p className="mt-1 font-medium">Imran</p>
            <p className="text-sm text-muted-foreground">Co-supervisor · Sajid Hussain</p>
          </div>
        </div>
      </section>

      <section className="max-w-2xl space-y-3">
        <h2 className="font-display text-2xl font-semibold">Stack</h2>
        <Separator />
        <p className="text-sm leading-relaxed text-muted-foreground">
          FastAPI and PostgreSQL on the backend, React for the instructor dashboard, sentence
          transformers for embeddings, EasyOCR for papers, and Docker for local deployment.
        </p>
      </section>

      <footer className="flex items-center gap-3 border-t border-border pt-6 text-xs text-muted-foreground">
        <img src="/kiu_logo.png" alt="" className="h-8 w-8 object-contain opacity-80" aria-hidden />
        <p>Karakoram International University · NLP &amp; Deep Learning FYP</p>
      </footer>
    </div>
  );
}
