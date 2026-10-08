import Link from "next/link";
import { WinRateChart, AvgDamageChart } from "./charts";
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

interface ShipRecord {
  shipId?: number;
  name?: string;
  tier?: number;
  type?: string;
  nation?: string;
  image?: string;
  battles: number;
  winRate: number;
  avgDamage: number;
  frags: number;
  hitRatio?: number;
  mainBatteryHitRate: number;
  maxDamage: number;
  isPremium?: boolean;
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
          No active combat record was located for commander handle &ldquo;{username}&rdquo;.
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

  const { stats, realm, lastUpdated, history, clan, gameModes, topShips } = playerData;
  const updatedAt = new Date(lastUpdated).toLocaleString("en-US", { timeZone: "UTC" });

  const survivalRate = stats.battles > 0 ? ((stats.survived / stats.battles) * 100).toFixed(2) : "0.00";
  const fragsPerBattle = stats.battles > 0 ? (stats.frags / stats.battles).toFixed(2) : "0.00";
  const planesPerBattle = stats.battles > 0 ? ((stats.planesKilled || 0) / stats.battles).toFixed(2) : "0.00";
  const avgXp = stats.battles > 0 ? Math.round(stats.xp / stats.battles).toLocaleString() : "0";

  const toRoman = (num?: number) => {
    if (!num) return "";
    return ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"][num] || String(num);
  };

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
          CLASSIFIED // OFFICIAL COMBAT DOSSIER
        </span>
      </div>

      {/* Commander Header Dossier */}
      <section className="border-b-2 border-[#1A1A17] pb-8 mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            {clan && clan.tag && (
              <div className="flex items-center gap-2 mb-2 font-mono text-xs">
                <span className="bg-[#B3261E] text-white px-2 py-0.5 font-bold tracking-wider">
                  [{clan.tag}]
                </span>
                <span className="font-bold text-[#1A1A17] uppercase tracking-wide">
                  {clan.name}
                </span>
                <span className="text-[#5B6770] uppercase">
                  • {clan.role || "MEMBER"}
                </span>
              </div>
            )}
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-2">
              DOSSIER NO. {realm.toUpperCase()}-{playerData.accountId}
            </div>
            <h1 className="text-6xl md:text-8xl font-black uppercase tracking-tighter text-[#1A1A17] leading-none font-sans">
              {playerData.username}
            </h1>
            <div className="flex flex-wrap gap-4 text-xs font-mono text-[#5B6770] mt-4 uppercase">
              <span className="font-bold text-[#1A1A17]">THEATER: {realm.toUpperCase()} SERVER</span>
              <span>•</span>
              <span>CLASSIFICATION: VERIFIED COMMANDER</span>
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

      {/* 02 — ENGAGEMENT THEATERS & MODES BREAKDOWN */}
      {gameModes && (
        <section className="border-2 border-[#1A1A17] bg-[#EFEBE0] p-8 mb-12">
          <div className="flex justify-between items-baseline mb-6 border-b border-[#1A1A17] pb-3">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
                02 // ENGAGEMENT THEATERS
              </div>
              <h2 className="text-xl font-black uppercase tracking-tight text-[#1A1A17]">
                COMBAT MODE COMPARATIVE BREAKDOWN
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#5B6770] uppercase">
              SOLO VS SQUADRON TACTICS
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Solo PvP */}
            <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
              <div className="text-xs font-mono uppercase tracking-wider text-[#5B6770] font-bold">
                SOLO PVP
              </div>
              <div className="text-3xl font-black text-[#1A1A17] mt-2">
                {gameModes.solo?.winRate?.toFixed(2) || "0.00"}%
              </div>
              <div className="text-xs font-mono text-[#5B6770] mt-2 flex justify-between border-t border-zinc-300 pt-2">
                <span>BATTLES: {gameModes.solo?.battles?.toLocaleString() || 0}</span>
                <span>WINS: {gameModes.solo?.wins?.toLocaleString() || 0}</span>
              </div>
            </div>

            {/* Division 2 */}
            <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
              <div className="text-xs font-mono uppercase tracking-wider text-[#5B6770] font-bold">
                DIVISION (DUO)
              </div>
              <div className="text-3xl font-black text-[#1A1A17] mt-2">
                {gameModes.div2?.winRate?.toFixed(2) || "0.00"}%
              </div>
              <div className="text-xs font-mono text-[#5B6770] mt-2 flex justify-between border-t border-zinc-300 pt-2">
                <span>BATTLES: {gameModes.div2?.battles?.toLocaleString() || 0}</span>
                <span>WINS: {gameModes.div2?.wins?.toLocaleString() || 0}</span>
              </div>
            </div>

            {/* Division 3 */}
            <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
              <div className="text-xs font-mono uppercase tracking-wider text-[#5B6770] font-bold">
                DIVISION (TRIO)
              </div>
              <div className="text-3xl font-black text-[#1A1A17] mt-2">
                {gameModes.div3?.winRate?.toFixed(2) || "0.00"}%
              </div>
              <div className="text-xs font-mono text-[#5B6770] mt-2 flex justify-between border-t border-zinc-300 pt-2">
                <span>BATTLES: {gameModes.div3?.battles?.toLocaleString() || 0}</span>
                <span>WINS: {gameModes.div3?.wins?.toLocaleString() || 0}</span>
              </div>
            </div>

            {/* Ranked */}
            <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
              <div className="text-xs font-mono uppercase tracking-wider text-[#5B6770] font-bold">
                RANKED COMBAT
              </div>
              <div className="text-3xl font-black text-[#1A1A17] mt-2">
                {gameModes.rank?.winRate?.toFixed(2) || "0.00"}%
              </div>
              <div className="text-xs font-mono text-[#5B6770] mt-2 flex justify-between border-t border-zinc-300 pt-2">
                <span>BATTLES: {gameModes.rank?.battles?.toLocaleString() || 0}</span>
                <span>WINS: {gameModes.rank?.wins?.toLocaleString() || 0}</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 03 — DETAILED COMBAT MATRIX */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-8 mb-12">
        <div className="flex justify-between items-baseline mb-6 border-b border-[#1A1A17] pb-3">
          <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
            03 // EXTENDED COMBAT METRICS & BALLISTICS
          </h2>
          <span className="text-[10px] font-mono text-[#5B6770] uppercase">
            TACTICAL ENGAGEMENT LOG
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

      {/* 04 — TOP COMMISSIONED WARSHIPS LEDGER */}
      {topShips && topShips.length > 0 && (
        <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] mb-12">
          <div className="p-6 border-b-2 border-[#1A1A17] bg-[#EFEBE0] flex justify-between items-baseline">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
                04 // COMMISSIONED WARSHIP LEDGER
              </div>
              <h2 className="text-2xl font-black uppercase tracking-tight text-[#1A1A17]">
                INDIVIDUAL VESSEL PERFORMANCE ARCHIVE
              </h2>
            </div>
            <span className="text-xs font-mono text-[#5B6770] uppercase">
              TOP {topShips.length} VESSELS BY SORTIES
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="border-b-2 border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                  <th className="p-4 font-bold uppercase w-12">#</th>
                  <th className="p-4 font-bold uppercase">WARSHIP</th>
                  <th className="p-4 font-bold uppercase">NATION</th>
                  <th className="p-4 font-bold uppercase text-right">BATTLES</th>
                  <th className="p-4 font-bold uppercase text-right">WIN RATE</th>
                  <th className="p-4 font-bold uppercase text-right">AVG DAMAGE</th>
                  <th className="p-4 font-bold uppercase text-right">FRAGS</th>
                  <th className="p-4 font-bold uppercase text-right">MAIN BATTERY ACC</th>
                  <th className="p-4 font-bold uppercase text-right">MAX DAMAGE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A17] bg-white">
                {topShips.map((ship: ShipRecord, idx: number) => (
                  <tr key={ship.shipId || idx} className="hover:bg-[#F7F4EC] transition-colors">
                    <td className="p-4 font-bold text-sm text-[#5B6770]">
                      {String(idx + 1).padStart(2, "0")}
                    </td>
                    <td className="p-4 font-sans font-bold text-sm">
                      <div className="flex items-center gap-3">
                        {ship.image && (
                          <img
                            src={ship.image}
                            alt={ship.name}
                            className="w-16 h-8 object-contain bg-zinc-900/10 p-0.5 border border-zinc-300"
                          />
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-[#B3261E] font-bold">
                              {toRoman(ship.tier)}
                            </span>
                            <span className="text-[#1A1A17]">{ship.name}</span>
                          </div>
                          <div className="text-[10px] font-mono text-[#5B6770] uppercase">
                            {ship.type} {ship.isPremium ? "• PREMIUM" : ""}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 uppercase text-[#5B6770]">{ship.nation}</td>
                    <td className="p-4 text-right font-bold">{ship.battles.toLocaleString()}</td>
                    <td className="p-4 text-right font-bold text-sm text-[#B3261E]">
                      {ship.winRate.toFixed(2)}%
                    </td>
                    <td className="p-4 text-right">{ship.avgDamage.toLocaleString()}</td>
                    <td className="p-4 text-right">{ship.frags.toLocaleString()}</td>
                    <td className="p-4 text-right">
                      {ship.mainBatteryHitRate > 0 ? `${ship.mainBatteryHitRate}%` : "—"}
                    </td>
                    <td className="p-4 text-right font-bold">
                      {ship.maxDamage > 0 ? ship.maxDamage.toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 05 — HISTORICAL CHARTS */}
      {history && history.length > 0 && (
        <section className="mb-16">
          <div className="flex justify-between items-baseline mb-6 border-b-2 border-[#1A1A17] pb-3">
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
              05 // TEMPORAL PERFORMANCE TRAJECTORY
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
