import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
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
  title: "WoWS Stats Tracker",
  description: "AI-native World of Warships player statistics and analytics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#050510] text-cyan-50 font-mono selection:bg-cyan-500/30">
        <header className="sticky top-0 z-50 w-full border-b-2 border-cyan-500/30 bg-[#050510]/80 backdrop-blur-xl shadow-[0_0_15px_rgba(34,211,238,0.1)]">
          <div className="absolute bottom-[-2px] left-0 w-1/4 h-[2px] bg-cyan-400 shadow-[0_0_10px_#0ff]"></div>
          <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 border border-cyan-400 flex items-center justify-center bg-cyan-950/50 shadow-[0_0_10px_rgba(34,211,238,0.4)]">
                <div className="w-4 h-4 border border-fuchsia-400/80 animate-pulse"></div>
              </div>
              <span className="text-xl font-bold tracking-[0.2em] text-cyan-400 uppercase drop-shadow-[0_0_5px_rgba(34,211,238,0.8)]">
                WoWS Stats
              </span>
            </div>
            <nav className="flex gap-8 text-sm font-bold tracking-widest text-cyan-600">
              <Link href="/" className="hover:text-cyan-300 transition-colors hover:drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">HOME</Link>
              <a href="#" className="hover:text-cyan-300 transition-colors hover:drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">LEADERBOARD</a>
              <a href="#" className="text-fuchsia-500 hover:text-fuchsia-300 transition-colors hover:drop-shadow-[0_0_5px_rgba(217,70,239,0.5)]">LOGIN</a>
            </nav>
          </div>
        </header>
        <main className="flex-1 flex flex-col relative z-0">
          {children}
        </main>
      </body>
    </html>
  );
}
