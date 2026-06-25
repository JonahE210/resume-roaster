"use client";
// The parser debug view — the portfolio centerpiece.
// TODO(phase6): render the uploaded PDF page as a background and overlay the
// layout_boxes, color-coded by kind/confidence.
import { DebugOverlay } from "@/components/DebugOverlay";

export default function DebugPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Parser Debug</h1>
      <p className="text-neutral-600">
        Shows how the parser interpreted the resume. Blue = section, green = entry,
        yellow = bullet, purple = date, red = low confidence.
      </p>
      <DebugOverlay boxes={[]} />
    </div>
  );
}
