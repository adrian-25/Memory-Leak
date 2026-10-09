import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MemoryLeak — Organizational Knowledge Risk Intelligence",
  description:
    "AI-powered platform for detecting knowledge concentration risks, bus-factor dependencies, and documentation gaps.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
