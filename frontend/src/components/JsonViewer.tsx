"use client";
// Minimal structured-JSON viewer. Swap for a collapsible tree later if desired.
export function JsonViewer({ data }: { data: unknown }) {
  return (
    <pre className="overflow-auto rounded-lg border bg-white p-4 text-xs">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
