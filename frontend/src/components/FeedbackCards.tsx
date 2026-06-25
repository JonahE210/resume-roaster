"use client";
// Renders AI critique + bullet rewrites. Shape matches ai/critique.py output.
interface Critique {
  overall_feedback?: string;
  top_strengths?: string[];
  main_issues?: string[];
  rewritten_bullets?: { original: string; improved: string }[];
  roast?: string | null;
}

export function FeedbackCards({ analysis }: { analysis: { ai?: Critique } | null }) {
  if (!analysis?.ai) {
    return <p className="text-neutral-500">Run an analysis to see feedback.</p>;
  }
  const ai = analysis.ai;
  return (
    <div className="space-y-4">
      {ai.overall_feedback && (
        <div className="rounded-lg border bg-white p-4">{ai.overall_feedback}</div>
      )}
      {ai.rewritten_bullets?.map((r, i) => (
        <div key={i} className="rounded-lg border bg-white p-4 text-sm">
          <p className="text-red-600 line-through">{r.original}</p>
          <p className="text-green-700">{r.improved}</p>
        </div>
      ))}
      {ai.roast && <div className="rounded-lg border bg-amber-50 p-4 italic">{ai.roast}</div>}
    </div>
  );
}
