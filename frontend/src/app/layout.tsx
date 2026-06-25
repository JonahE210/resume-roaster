import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resume Intelligence Engine",
  description: "Layout-aware resume parser + analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900">
        <nav className="border-b bg-white px-6 py-3 text-sm font-medium">
          <a href="/" className="mr-4">Upload</a>
          <a href="/analysis" className="mr-4">Analysis</a>
          <a href="/debug">Parser Debug</a>
        </nav>
        <main className="mx-auto max-w-5xl p-6">{children}</main>
      </body>
    </html>
  );
}
