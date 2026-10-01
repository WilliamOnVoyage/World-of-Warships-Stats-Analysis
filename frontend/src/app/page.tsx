"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface OverviewStats {
  totalPlayers: number;
  totalBattles: number;
  avgWinRate: number;
  status: string;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export default function Home() {
  const [username, setUsername] = useState("");
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetch(`${API_BASE}/api/stats/overview`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => { if (data) setOverview(data); })
      .catch(() => {});
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      router.push(`/player/${encodeURIComponent(username.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#050510] text-cyan-50 font-mono relative overflow-hidden">
      {/* Background Cyber-Grid with Neon Glow */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ff_1px,transparent_1px),linear-gradient(to_bottom,#0ff_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,#000_60%,transparent_100%)] opacity-10 pointer-events-none"></div>
      
      {/* Ambient Neon Blobs */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-cyan-600/20 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-fuchsia-600/10 rounded-full blur-[80px] pointer-events-none"></div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-20">
        <div className="flex items-center justify-between mb-12 border-b-2 border-cyan-500/30 pb-6 relative">
          <div className="absolute bottom-[-2px] left-0 w-1/3 h-[2px] bg-cyan-400 shadow-[0_0_10px_#0ff]"></div>
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 border-2 border-cyan-400 flex items-center justify-center bg-cyan-950/50 shadow-[0_0_15px_rgba(34,211,238,0.4)] rotate-45">
              <div className="w-8 h-8 border border-fuchsia-400/80 -rotate-45 animate-pulse"></div>
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-[0.2em] text-cyan-400 uppercase drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]">
                Neon Tactical Command
              </h1>
              <p className="text-fuchsia-400 text-sm mt-2 tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 bg-fuchsia-400 rounded-full animate-ping"></span>
                NEURAL LINK ESTABLISHED
              </p>
            </div>
          </div>
        </div>

        <div className="border border-cyan-800 bg-black/40 p-8 backdrop-blur-md relative shadow-[0_0_30px_rgba(8,145,178,0.2)]">
          {/* Cyberpunk cut corners simulation using borders */}
          <div className="absolute top-0 left-0 w-8 h-1 bg-cyan-400"></div>
          <div className="absolute top-0 left-0 w-1 h-8 bg-cyan-400"></div>
          <div className="absolute bottom-0 right-0 w-8 h-1 bg-fuchsia-500"></div>
          <div className="absolute bottom-0 right-0 w-1 h-8 bg-fuchsia-500"></div>

          <form onSubmit={handleSearch} className="flex gap-4">
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="ENTER PLAYER HANDLE..." 
              className="flex-1 bg-cyan-950/20 border-b-2 border-cyan-800 p-4 outline-none focus:border-cyan-400 text-cyan-300 placeholder-cyan-800 transition-colors uppercase tracking-widest text-lg"
            />
            <button type="submit" className="bg-cyan-950 hover:bg-cyan-900 border border-cyan-400 px-10 font-bold tracking-widest text-cyan-100 transition-all shadow-[0_0_10px_rgba(34,211,238,0.3)] hover:shadow-[0_0_20px_rgba(34,211,238,0.6)]">
              INITIALIZE
            </button>
          </form>

          {/* Live Overview Stats */}
          <div className="grid grid-cols-3 gap-8 mt-12">
            <div className="border-t border-cyan-800 pt-4 relative group">
              <div className="absolute top-0 left-0 w-1/4 h-[1px] bg-fuchsia-500 group-hover:w-full transition-all duration-500"></div>
              <div className="text-cyan-600 text-xs tracking-widest mb-2 font-bold">TOTAL PLAYERS TRACKED</div>
              <div className="text-5xl text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                {overview ? formatNumber(overview.totalPlayers) : "—"}
              </div>
            </div>
            <div className="border-t border-cyan-800 pt-4 relative group">
              <div className="absolute top-0 left-0 w-1/4 h-[1px] bg-fuchsia-500 group-hover:w-full transition-all duration-500"></div>
              <div className="text-cyan-600 text-xs tracking-widest mb-2 font-bold">BATTLES ANALYZED</div>
              <div className="text-5xl text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                {overview ? formatNumber(overview.totalBattles) : "—"}
              </div>
            </div>
            <div className="border-t border-cyan-800 pt-4 relative group">
              <div className="absolute top-0 left-0 w-1/4 h-[1px] bg-fuchsia-500 group-hover:w-full transition-all duration-500"></div>
              <div className="text-cyan-600 text-xs tracking-widest mb-2 font-bold">SERVER STATUS</div>
              <div className={`text-5xl drop-shadow-[0_0_8px_rgba(255,255,255,0.5)] ${overview?.status === "online" ? "text-green-400" : "text-amber-400"}`}>
                {overview ? overview.status.toUpperCase() : "—"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
