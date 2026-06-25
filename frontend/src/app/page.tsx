"use client";
import { useState } from "react";
import { ResumeUpload } from "@/components/ResumeUpload";
import { JsonViewer } from "@/components/JsonViewer";
import { parseResume, type ParseResult } from "@/lib/api";

export default function UploadPage() {
  const [role, setRole] = useState("Software Engineering Intern");
  const [result, setResult] = useState<ParseResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setError(null);
    try {
      setResult(await parseResume(file));
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Resume Intelligence Engine</h1>
      <p className="text-neutral-600">
        Upload a single-column, one-page SWE resume. The parser reconstructs its
        structure from PDF layout before any AI sees it.
      </p>
      <label className="block text-sm font-medium">
        Target role
        <input
          className="mt-1 block w-full rounded border px-3 py-2"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
      </label>
      <ResumeUpload onFile={handleFile} />
      {error && <p className="text-red-600">{error}</p>}
      {result && (
        <>
          {result.warnings.map((w) => (
            <p key={w} className="text-amber-600">⚠ {w}</p>
          ))}
          <JsonViewer data={result.resume} />
        </>
      )}
    </div>
  );
}
