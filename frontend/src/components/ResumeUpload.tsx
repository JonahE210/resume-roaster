"use client";
import { useRef } from "react";

export function ResumeUpload({ onFile }: { onFile: (f: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      className="cursor-pointer rounded-lg border-2 border-dashed p-10 text-center hover:bg-white"
      onClick={() => inputRef.current?.click()}
      onDrop={(e) => {
        e.preventDefault();
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      onDragOver={(e) => e.preventDefault()}
    >
      <p className="text-neutral-600">Drop a PDF here, or click to choose</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
    </div>
  );
}
