"use client";
// Analysis dashboard: scores + AI feedback.
// TODO(phase6): wire to a shared store (or query param) so it reads the parsed
// resume from the upload step, calls analyzeResume(), and renders FeedbackCards.
import { FeedbackCards } from "@/components/FeedbackCards";

export default function AnalysisPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analysis</h1>
      <p className="text-neutral-600">
        Deterministic scores first, then AI critique + bullet rewrites. Stub UI.
      </p>
      <FeedbackCards analysis={null} />
    </div>
  );
}
