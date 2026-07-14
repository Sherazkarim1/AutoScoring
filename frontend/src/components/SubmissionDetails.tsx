import { useEffect, useState } from "react";
import { API_ORIGIN } from "@/api";
import type { DetailedReport, OCRPage, Submission } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

function Metric({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="min-w-[100px] space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium tabular-nums">{pct}%</span>
      </div>
      <Progress value={pct} className="h-1.5" />
    </div>
  );
}

export function DetailedReportView({ report }: { report: DetailedReport }) {
  return (
    <div className="mt-4 space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <h4 className="text-sm font-semibold">Matched concepts</h4>
          {report.matched_concepts.length ? (
            <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
              {report.matched_concepts.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">None fully matched</p>
          )}
        </div>
        <div className="space-y-2">
          <h4 className="text-sm font-semibold">Partially covered</h4>
          {report.partial_concepts.length ? (
            <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
              {report.partial_concepts.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">None</p>
          )}
        </div>
        <div className="space-y-2">
          <h4 className="text-sm font-semibold">Missing concepts</h4>
          {report.missing_concepts.length ? (
            <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
              {report.missing_concepts.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">None</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h4 className="mb-2 text-sm font-semibold">Key terms found</h4>
          <div className="flex flex-wrap gap-1.5">
            {report.matched_keywords.map((k) => (
              <Badge key={k} variant="success">
                {k}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <h4 className="mb-2 text-sm font-semibold">Key terms missing</h4>
          <div className="flex flex-wrap gap-1.5">
            {report.missing_keywords.length ? (
              report.missing_keywords.map((k) => (
                <Badge key={k} variant="destructive">
                  {k}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">None</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h4 className="mb-2 text-sm font-semibold">Strengths</h4>
          <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
            {report.strengths.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-2 text-sm font-semibold">Areas to improve</h4>
          <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
            {report.weaknesses.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {report.word_count} words · {report.sentence_count} sentences
        {report.ocr_quality_note ? ` · ${report.ocr_quality_note}` : ""}
      </p>
    </div>
  );
}

export function SubmissionResult({ submission }: { submission: Submission }) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-4">
        <Metric label="Semantic" value={submission.semantic_similarity} />
        <Metric label="Keywords" value={submission.keyword_coverage} />
        <Metric label="Coherence" value={submission.coherence_score} />
        {submission.ocr_confidence != null && (
          <Metric label="OCR quality" value={submission.ocr_confidence} />
        )}
      </div>
      <p className="rounded-md border border-border bg-background px-3 py-2 text-sm leading-relaxed">
        {submission.feedback}
      </p>
      {submission.detailed_report && <DetailedReportView report={submission.detailed_report} />}
    </div>
  );
}

function AuthenticatedImage({
  path,
  alt,
}: {
  path: string | null | undefined;
  alt: string;
}) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!path) {
      setSrc(null);
      return;
    }
    const url = path.startsWith("http") ? path : `${API_ORIGIN}${path}`;
    const token = localStorage.getItem("token");
    let objectUrl: string | null = null;

    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load image");
        return res.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => setSrc(null));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  if (!src) {
    return (
      <div className="flex min-h-[120px] items-center justify-center bg-muted text-xs text-muted-foreground">
        {alt}
      </div>
    );
  }
  return <img src={src} alt={alt} className="block w-full" />;
}

export function PaperPreviews({ pages }: { pages: OCRPage[] }) {
  if (!pages.length) return null;
  return (
    <div className="flex flex-wrap gap-3">
      {pages.map((page) => (
        <figure
          key={page.page_number}
          className="max-w-[240px] overflow-hidden rounded-md border border-border bg-card"
        >
          <AuthenticatedImage path={page.preview_url} alt={`Page ${page.page_number}`} />
          <figcaption className="border-t border-border px-2 py-1.5 text-xs text-muted-foreground">
            Page {page.page_number} · {(page.confidence * 100).toFixed(0)}% OCR
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export { Metric };
