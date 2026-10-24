import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DocIQ - Technical Document Intelligence & Q&A Platform",
  description:
    "Upload technical documents, search them, and ask natural-language questions with grounded, citation-backed answers powered by Supabase pgvector.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-[#090d16] text-slate-100 selection:bg-teal-500/30 selection:text-teal-200 font-sans`}
      >
        {children}
      </body>
    </html>
  );
}
