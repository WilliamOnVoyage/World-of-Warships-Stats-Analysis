import Link from "next/link";
import { WinRateChart, AvgDamageChart, BattlesChart } from "./charts";
import { RefreshButton } from "./refresh-button";

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
      <div className="flex-1 w-full max-w-5xl mx-auto px-6 py-20 flex flex-col items-center justify-center min-h-[50vh]">
        <span className="stamp-badge text-xs mb-4">RECORD NOT FOUND</span>
        <h1 className="text-4xl font-black uppercase tracking-tight text-[#1A1A17] mb-4">
          COMMANDER NOT IN REGISTER
        </h1>
        <p className="text-sm font-mono text-[#5B6770] mb-8 text-center max-w-md">
          No active telemetry record was located for commander handle &ldquo;{username}&rdquo;.
        </p>
        <Link
          href="/"
          className="px-6 py-3 bg-[#1A1A17] hover:bg-[#B3261E] text-white transition-colors font-mono font-bold text-xs uppercase tracking-widest"
        >
          ← RETURN TO DISPATCH
        </Link>
      </div>
    );
  }

  const { stats, realm, lastUpdated, history } = playerData;
  const updatedAt = new Date(lastUpdated).toLocaleString("en-US", { timeZone: "UTC" });

  const survivalRate = stats.battles > 0 ? ((stats.survived / stats.battles) * 100).toFixed(2) : "0.00";
  const fragsPerBattle = stats.battles > 0 ? (stats.frags / stats.battles).toFixed(2) : "0.00";
  const planesPerBattle = stats.battles > 0 ? ((stats.planesKilled || 0) / stats.battles).toFixed(2) : "0.00";
  const avgXp = stats.battles > 0 ? Math.round(stats.xp / stats.battles).toLocaleString() : "0";

  return (
    <div className="flex-1 w-full max-w-7xl mx-auto px-6 py-12">
      {/* Navigation & Stamp */}
      <div className="mb-8 flex items-center justify-between border-b border-[#1A1A17] pb-4">
        <Link
          href="/"
          className="text-xs font-mono uppercase tracking-widest text-[#5B6770] hover:text-[#B3261E] flex items-center gap-2 group transition-colors"
        >
          <span className="group-hover:-translate-x-1 transition-transform">←</span>
          <span>RETURN TO DISPATCH</span>
        </Link>
        <span className="stamp-badge text-[10px]">
          CLASSIFIED // VERIFIED TELEMETRY
        </span>
      </div>

      {/* Commander Header Dossier */}
      <section className="border-b-2 border-[#1A1A17] pb-8 mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-2">
              DOSSIER NO. {realm.toUpperCase()}-{playerData.accountId}
            </div>
            <h1 className="text-6xl md:text-8xl font-black uppercase tracking-tighter text-[#1A1A17] leading-none font-sans">
              {playerData.username}
            </h1>
            <div className="flex flex-wrap gap-4 text-xs font-mono text-[#5B6770] mt-4 uppercase">
              <span className="font-bold text-[#1A1A17]">THEATER: {realm.toUpperCase()} SERVER</span>
              <span>•</span>
              <span>MODE: RANDOM BATTLES (PVP)</span>
              <span>•</span>
              <span>SYNCHRONIZED: {updatedAt} UTC</span>
            </div>
          </div>
          <RefreshButton username={playerData.username} />
        </div>
      </section>

      {/* 01 — CORE COMBAT INDICATORS (4-COLUMN GRID) */}
      <section className="border-t-2 border-l-2 border-[#1A1A17] mb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          {/* Win Rate */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              01 // WIN RATE (PVP)
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#B3261E]">
              {stats.winRate.toFixed(2)}%
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              VICTORIES IN RANDOM BATTLES
            </div>
          </div>

          {/* Battles */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              02 // PVP BATTLES
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {stats.battles.toLocaleString()}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              DENOMINATOR: RANDOM ONLY
            </div>
          </div>

          {/* Average Damage */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              03 // AVERAGE DAMAGE
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {stats.avgDamage.toLocaleString()}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              MEAN STRUCTURAL DAMAGE
            </div>
          </div>

          {/* K/D Ratio */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              04 // K/D RATIO
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {(stats.kdRatio || (stats.frags / Math.max(stats.battles - stats.survived, 1))).toFixed(2)}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              DESTRUCTION RATIO
            </div>
          </div>
        </div>
      </section>

      {/* 02 — DETAILED COMBAT MATRIX */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-8 mb-12">
        <div className="flex justify-between items-baseline mb-6 border-b border-[#1A1A17] pb-3">
          <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
            02 // EXTENDED COMBAT TELEMETRY
          </h2>
          <span className="text-[10px] font-mono text-[#5B6770] uppercase">
            ACTIVE SENSOR LOG
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">WARSHIPS SUNK</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{stats.frags.toLocaleString()}</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">{fragsPerBattle} / battle</div>
          </div>

          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">SURVIVAL RATE</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{survivalRate}%</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">{stats.survived.toLocaleString()} survived</div>
          </div>

          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">PLANES DESTROYED</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{(stats.planesKilled || 0).toLocaleString()}</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">{planesPerBattle} / battle</div>
          </div>

          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">MAX DAMAGE RECORD</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{(stats.maxDamage || 0).toLocaleString()}</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">single battle max</div>
          </div>

          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">SCOUTING DAMAGE</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{((stats.damageScouting || 0) / 1_000_000).toFixed(1)}M</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">spotting total</div>
          </div>

          <div className="border-t border-[#1A1A17] pt-3">
            <div className="text-[10px] font-mono text-[#5B6770] uppercase">AVERAGE XP</div>
            <div className="text-2xl font-black text-[#1A1A17] mt-1">{avgXp}</div>
            <div className="text-[10px] font-mono text-[#5B6770] mt-0.5">per battle mean</div>
          </div>
        </div>
      </section>

      {/* 03 — HISTORICAL CHARTS */}
      {history && history.length > 0 && (
        <section className="mb-16">
          <div className="flex justify-between items-baseline mb-6 border-b-2 border-[#1A1A17] pb-3">
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
              03 // TEMPORAL PERFORMANCE TRAJECTORY
            </h2>
            <span className="text-xs font-mono text-[#5B6770]">
              {history.length} CHRONOLOGICAL LOG POINTS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <WinRateChart data={history} />
            <AvgDamageChart data={history} />
          </div>
        </section>
      )}
    </div>
  );
}
