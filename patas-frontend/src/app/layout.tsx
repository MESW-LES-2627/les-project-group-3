import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";

import { SiteHeader } from "@/components/site-header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Patas",
  description: "Plataforma Colaborativa de Proteção Animal",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-background text-ink">
        <Suspense
          fallback={
            <div
              className="min-h-[4.5rem] border-b border-line bg-surface"
              aria-hidden="true"
            />
          }
        >
          <SiteHeader />
        </Suspense>
        {children}
      </body>
    </html>
  );
}
