import Link from "next/link";
import { WinRateChart, AvgDamageChart, BattlesChart } from "./charts";

const API_BASE = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function getPlayerData(username: string) {
  try {
    const res = await fetch(`${API_BASE}/api/player/${username}`, {
      next: { revalidate: 60 }
    });
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error("Failed to fetch player data");
    }
    return res.json();
  } catch (error) {
    console.error(error);
    return null;
  }
}

export default async function PlayerProfile({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const resolvedParams = await params;
  const username = decodeURIComponent(resolvedParams.username);

  const playerData = await getPlayerData(username);

  if (!playerData) {
    return (
      <div className="flex-1 w-full max-w-6xl mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[50vh]">
        <h1 className="text-3xl font-bold text-white mb-4">Player Not Found</h1>
        <p className="text-zinc-400 mb-8">
          We couldn&apos;t find a World of Warships player with the username &ldquo;{username}&rdquo;.
        </p>
        <Link href="/" className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors font-medium tracking-widest uppercase text-sm border border-cyan-400/30 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
          Back to Search
        </Link>
      </div>
    );
  }

  const { stats, realm, lastUpdated, history } = playerData;
  const updatedAt = new Date(lastUpdated).toLocaleString();

  // Derive per-stat color coding
  const winRateColor =
    stats.winRate >= 55
      ? "text-green-400"
      : stats.winRate >= 50
        ? "text-cyan-400"
        : "text-amber-400";

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto px-4 py-8">
      {/* Back Link */}
      <div className="mb-8">
        <Link href="/" className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1 w-fit mb-6 group">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 group-hover:-translate-x-1 transition-transform">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          <span className="tracking-widest uppercase">Back to Search</span>
        </Link>

        {/* Player Header */}
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 tracking-wider drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
              {playerData.username}
            </h1>
            <div className="flex gap-3 text-sm text-zinc-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]"></span> Active
              </span>
              <span>•</span>
              <span className="uppercase tracking-widest">{realm} Server</span>
              <span>•</span>
              <span>Last updated: {updatedAt}</span>
            </div>
          </div>
          <button className="px-4 py-2 bg-cyan-950/50 hover:bg-cyan-900/50 transition-colors rounded-lg text-sm font-medium border border-cyan-500/30 text-cyan-300 tracking-widest uppercase shadow-[0_0_10px_rgba(6,182,212,0.15)] hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]">
            Refresh Stats
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-cyan-500 to-transparent opacity-60"></div>
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Win Rate</div>
          <div className={`text-4xl font-bold ${winRateColor} drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]`}>
            {stats.winRate.toFixed(1)}%
          </div>
        </div>
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-fuchsia-500 to-transparent opacity-60"></div>
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Average Damage</div>
          <div className="text-4xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
            {stats.avgDamage.toLocaleString()}
          </div>
        </div>
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-cyan-500 via-fuchsia-500 to-transparent opacity-60"></div>
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Total Battles</div>
          <div className="text-4xl font-bold text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
            {stats.battles.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Survived</div>
          <div className="text-2xl font-bold text-zinc-200">{stats.survived.toLocaleString()}</div>
          <div className="text-xs text-zinc-500 mt-1">
            {stats.battles > 0 ? `${((stats.survived / stats.battles) * 100).toFixed(1)}% survival rate` : "N/A"}
          </div>
        </div>
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Total Frags</div>
          <div className="text-2xl font-bold text-zinc-200">{stats.frags.toLocaleString()}</div>
          <div className="text-xs text-zinc-500 mt-1">
            {stats.battles > 0 ? `${(stats.frags / stats.battles).toFixed(2)} per battle` : "N/A"}
          </div>
        </div>
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
          <div className="text-xs font-bold text-cyan-600 mb-1 tracking-[0.2em] uppercase">Total XP</div>
          <div className="text-2xl font-bold text-zinc-200">{stats.xp.toLocaleString()}</div>
          <div className="text-xs text-zinc-500 mt-1">
            {stats.battles > 0 ? `${Math.round(stats.xp / stats.battles).toLocaleString()} avg per battle` : "N/A"}
          </div>
        </div>
      </div>

      {/* Charts Section */}
      {history && history.length > 0 ? (
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-1 h-6 bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.5)]"></div>
            <h2 className="text-lg font-bold text-white tracking-[0.15em] uppercase">Performance History</h2>
            <span className="text-xs text-zinc-500 tracking-widest">({history.length} DATA POINTS)</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <WinRateChart data={history} />
            <AvgDamageChart data={history} />
          </div>
          <BattlesChart data={history} />
        </div>
      ) : (
        <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-8 backdrop-blur-sm min-h-[200px] flex items-center justify-center">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-cyan-500/10 text-cyan-400 mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <p className="text-zinc-400 text-sm tracking-widest uppercase">
              Insufficient data — charts will appear after more snapshots are collected.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
