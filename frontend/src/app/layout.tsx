import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Naval Record Office — World of Warships Statistics",
  description: "Official telemetry, commander dossiers, and historical analytics for World of Warships.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-[#EFEBE0] text-[#1A1A17] font-sans antialiased selection:bg-[#B3261E] selection:text-white">
        {/* Admiralty Masthead Header */}
        <header className="border-b-2 border-[#1A1A17] bg-[#EFEBE0]">
          <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-baseline justify-between gap-4">
            <div className="flex items-baseline gap-4">
              <Link href="/" className="group flex items-baseline gap-3">
                <span className="w-3.5 h-3.5 bg-[#B3261E] inline-block" />
                <span className="text-xl md:text-2xl font-black uppercase tracking-tight text-[#1A1A17] group-hover:text-[#B3261E] transition-colors">
                  Naval Record Office
                </span>
              </Link>
              <span className="text-xs font-mono uppercase text-[#5B6770] tracking-widest hidden md:inline">
                TELEMETRY & DOSSIER ARCHIVE // EN-US
              </span>
            </div>

            <nav className="flex items-center gap-8 text-xs font-mono uppercase tracking-widest font-bold">
              <Link href="/" className="hover:text-[#B3261E] transition-colors">
                01 // DISPATCH
              </Link>
              <Link href="/#leaderboard" className="hover:text-[#B3261E] transition-colors">
                02 // LEADERBOARDS
              </Link>
              <Link href="/encyclopedia" className="hover:text-[#B3261E] transition-colors">
                03 // ENCYCLOPEDIA
              </Link>
              <Link href="/telemetry" className="hover:text-[#B3261E] transition-colors">
                04 // TELEMETRY
              </Link>
              <span className="text-[#B3261E] flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#B3261E] animate-pulse" />
                LIVE
              </span>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative z-0">
          {children}
        </main>

        {/* Archival Footer */}
        <footer className="border-t border-[#1A1A17] bg-[#E5E1D5] py-8 text-xs font-mono text-[#5B6770]">
          <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <span>NAVAL RECORD OFFICE • WORLD OF WARSHIPS STATISTICAL ARCHIVE</span>
            </div>
            <div className="flex gap-6 uppercase">
              <span>OPERATIONAL THEATERS: NA • EU • ASIA</span>
              <span>CLASSIFICATION: PUBLIC</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
