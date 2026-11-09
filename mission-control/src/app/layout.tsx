import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEGIS-0 // Mission Control Workbench",
  description: "Zero-Trust Token-Optimal Autonomous Coding & Live-Verification Engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="color-scheme" content="dark" />
      </head>
      <body className="antialiased min-h-screen bg-background text-slate-100">{children}</body>
    </html>
  );
}
