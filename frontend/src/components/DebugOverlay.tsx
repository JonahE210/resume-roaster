"use client";
import type { LayoutBox } from "@/lib/api";

const KIND_COLOR: Record<string, string> = {
  section: "border-blue-500",
  entry: "border-green-500",
  bullet: "border-yellow-500",
  date: "border-purple-500",
  line: "border-neutral-300",
  uncertain: "border-red-500",
};

// TODO(phase6): position boxes absolutely over a rendered PDF page using bbox
// coords scaled to the rendered page size. For now, list them.
export function DebugOverlay({ boxes }: { boxes: LayoutBox[] }) {
  if (boxes.length === 0) {
    return <p className="text-neutral-500">No parse loaded yet.</p>;
  }
  return (
    <div className="space-y-1">
      {boxes.map((b, i) => (
        <div key={i} className={`border-l-4 pl-2 text-sm ${KIND_COLOR[b.kind] ?? ""}`}>
          <span className="text-neutral-400">[{b.kind}]</span> {b.text}
        </div>
      ))}
    </div>
  );
}
