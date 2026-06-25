// Typed client for the backend. Keep response types in sync with backend schemas.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface BBox { x0: number; y0: number; x1: number; y1: number; }
export interface LayoutBox { kind: string; text: string; page: number; bbox: BBox; }

export interface Entry {
  title?: string; organization?: string; location?: string;
  start_date?: string; end_date?: string;
  bullets: string[]; technologies: string[]; confidence: number;
}
export interface Section {
  type: string; raw_heading: string;
  entries: Entry[]; skills: Record<string, string[]>; confidence: number;
}
export interface Resume {
  contact: Record<string, string | null>;
  sections: Section[];
  layout_boxes: LayoutBox[];
}
export interface ParseResult { resume: Resume; page_count: number; warnings: string[]; }

export async function parseResume(file: File): Promise<ParseResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/parse`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`parse failed: ${res.status}`);
  return res.json();
}

export async function analyzeResume(
  resume: Resume,
  targetRole: string,
  opts: { roast?: boolean; useAi?: boolean } = {},
): Promise<unknown> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume,
      target_role: targetRole,
      roast: opts.roast ?? false,
      use_ai: opts.useAi ?? true,
    }),
  });
  if (!res.ok) throw new Error(`analyze failed: ${res.status}`);
  return res.json();
}
