"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ClanModal from "@/components/ClanModal";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface OverviewStats {
  totalPlayers: number;
  totalBattles: number;
  avgWinRate: number;
  status: string;
}

interface LeaderboardEntry {
  rank: number;
  nickname: string;
  accountId: number;
  realm: string;
  battles: number;
  wins: number;
  winRate: number;
  avgDamage: number;
  frags: number;
  survived: number;
  kd: number;
}

interface ClanEntry {
  rank: number;
  clanId: number;
  tag: string;
  name: string;
  realm: string;
  membersCount: number;
  leaderName: string;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export default function Home() {
  const [username, setUsername] = useState("");
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [activeTab, setActiveTab] = useState<"commanders" | "clans">("commanders");
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [clans, setClans] = useState<ClanEntry[]>([]);
  const [category, setCategory] = useState("win_rate");
  const [mode, setMode] = useState("pvp");
  const [realm, setRealm] = useState("all");
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);
  const [selectedClanId, setSelectedClanId] = useState<number | null>(null);
  const router = useRouter();

  // Load global overview stats
  useEffect(() => {
    fetch(`${API_BASE}/api/stats/overview`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => { if (data) setOverview(data); })
      .catch(() => {});
  }, []);

  // Load leaderboards on category, realm, mode, or tab change
  useEffect(() => {
    setLoadingLeaderboard(true);
    if (activeTab === "commanders") {
      const minBattles = (mode === "solo" || mode === "div" || mode === "rank") ? 20 : 500;
      fetch(`${API_BASE}/api/leaderboard?category=${category}&realm=${realm}&mode=${mode}&min_battles=${minBattles}&limit=15`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && data.leaderboard) {
            setLeaderboard(data.leaderboard);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingLeaderboard(false));
    } else {
      fetch(`${API_BASE}/api/leaderboard/clans?realm=${realm}&limit=20`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && (data.leaderboard || data.clans)) {
            setClans(data.leaderboard || data.clans);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingLeaderboard(false));
    }
  }, [activeTab, category, realm, mode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      router.push(`/player/${encodeURIComponent(username.trim())}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 w-full">
      {/* 01 — COMMANDER LOOKUP */}
      <section className="border-b-2 border-[#1A1A17] pb-12 mb-12">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-mono uppercase tracking-[0.25em] text-[#5B6770] font-bold">
            01 // COMMANDER DOSSIER LOOKUP
          </span>
          <span className="stamp-badge text-[10px]">
            ARCHIVAL ACCESS
          </span>
        </div>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row border-2 border-[#1A1A17] bg-[#F7F4EC]">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="ENTER COMMANDER HANDLE (E.G. ZMLZEZE)..."
            className="flex-1 px-6 py-5 text-xl font-mono uppercase tracking-wider outline-none bg-transparent text-[#1A1A17] placeholder:text-zinc-400"
          />
          <button
            type="submit"
            className="bg-[#1A1A17] hover:bg-[#B3261E] text-white px-10 py-5 font-mono text-xs uppercase tracking-[0.25em] font-bold transition-colors cursor-pointer"
          >
            DISPATCH QUERY →
          </button>
        </form>
      </section>

      {/* 02 — GLOBAL TELEMETRY LEDGER (4 METRIC CARDS) */}
      <section className="border-t-2 border-l-2 border-[#1A1A17] mb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          {/* Card 1 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              COMMANDERS TRACKED
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {overview ? formatNumber(overview.totalPlayers) : <span className="opacity-30 font-mono">---</span>}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              NA • EU • ASIA REGISTER
            </div>
          </div>

          {/* Card 2 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              BATTLES ANALYZED
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {overview ? formatNumber(overview.totalBattles) : <span className="opacity-30 font-mono">---</span>}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              RANDOM & COMBAT THEATERS
            </div>
          </div>

          {/* Card 3 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              FLEET MEAN WIN RATE
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#B3261E]">
              {overview ? `${overview.avgWinRate.toFixed(2)}%` : <span className="opacity-30 font-mono">---</span>}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              VERIFIED ACTIVE COMMANDERS
            </div>
          </div>

          {/* Card 4 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              OPERATIONAL STATUS
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              ONLINE
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              10 REQ/S PIPELINE SYNC
            </div>
          </div>
        </div>
      </section>

      {/* 03 — FLEET LEADERBOARD & CLAN ARCHIVES */}
      <section id="leaderboard" className="border-2 border-[#1A1A17] bg-[#F7F4EC] mb-16">
        <div className="p-6 border-b-2 border-[#1A1A17] flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#EFEBE0]">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
              02 // ADMIRALTY LEADERBOARDS
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setActiveTab("commanders")}
                className={`text-2xl font-black uppercase tracking-tight transition-colors cursor-pointer ${
                  activeTab === "commanders" ? "text-[#1A1A17] underline decoration-[#B3261E] decoration-4 underline-offset-8" : "text-[#5B6770] hover:text-[#1A1A17]"
                }`}
              >
                COMMANDERS
              </button>
              <span className="text-2xl font-black text-[#5B6770]">/</span>
              <button
                onClick={() => setActiveTab("clans")}
                className={`text-2xl font-black uppercase tracking-tight transition-colors cursor-pointer ${
                  activeTab === "clans" ? "text-[#1A1A17] underline decoration-[#B3261E] decoration-4 underline-offset-8" : "text-[#5B6770] hover:text-[#1A1A17]"
                }`}
              >
                CLANS REGISTER
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
            {activeTab === "commanders" && (
              <>
                {/* Battle Mode Selector */}
                <div className="flex border border-[#1A1A17] bg-white">
                  {[
                    { id: "pvp", label: "RANDOM" },
                    { id: "solo", label: "SOLO" },
                    { id: "div", label: "DIVISION" },
                    { id: "rank", label: "RANKED" },
                    { id: "pve", label: "CO-OP" },
                  ].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setMode(m.id)}
                      className={`px-3 py-2 uppercase font-bold transition-colors cursor-pointer ${
                        mode === m.id
                          ? "bg-[#1A1A17] text-white"
                          : "text-[#5B6770] hover:text-[#1A1A17]"
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>

                {/* Category Toggle */}
                <div className="flex border border-[#1A1A17] bg-white">
                  {[
                    { id: "win_rate", label: "WIN RATE" },
                    { id: "damage", label: "AVG DAMAGE" },
                    { id: "battles", label: "BATTLES" },
                    { id: "frags", label: "K/D" }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setCategory(tab.id)}
                      className={`px-3 py-2 uppercase font-bold transition-colors cursor-pointer ${
                        category === tab.id
                          ? "bg-[#5B6770] text-white"
                          : "text-[#5B6770] hover:text-[#1A1A17]"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* Realm Filter */}
            <div className="flex border border-[#1A1A17] bg-white">
              {["all", "na", "eu", "asia"].map((r) => (
                <button
                  key={r}
                  onClick={() => setRealm(r)}
                  className={`px-3 py-2 uppercase font-bold transition-colors cursor-pointer ${
                    realm === r
                      ? "bg-[#B3261E] text-white"
                      : "text-[#5B6770] hover:text-[#1A1A17]"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Table */}
        <div className="overflow-x-auto">
          {activeTab === "commanders" ? (
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="border-b-2 border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                  <th className="p-4 font-bold uppercase w-16">RANK</th>
                  <th className="p-4 font-bold uppercase">COMMANDER</th>
                  <th className="p-4 font-bold uppercase">THEATER</th>
                  <th className="p-4 font-bold uppercase text-right">BATTLES</th>
                  <th className="p-4 font-bold uppercase text-right">WIN RATE</th>
                  <th className="p-4 font-bold uppercase text-right">AVG DAMAGE</th>
                  <th className="p-4 font-bold uppercase text-right">K/D</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A17] bg-white">
                {loadingLeaderboard ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                      Retrieving Admiralty Records...
                    </td>
                  </tr>
                ) : leaderboard.length > 0 ? (
                  leaderboard.map((entry) => (
                    <tr key={entry.accountId} className="hover:bg-[#F7F4EC] transition-colors">
                      <td className="p-4 font-bold text-sm">
                        {entry.rank === 1 ? (
                          <span className="text-[#B3261E] font-black">01</span>
                        ) : (
                          String(entry.rank).padStart(2, "0")
                        )}
                      </td>
                      <td className="p-4 font-sans font-bold text-sm">
                        <Link
                          href={`/player/${encodeURIComponent(entry.nickname)}`}
                          className="hover:text-[#B3261E] transition-colors hover:underline"
                        >
                          {entry.nickname}
                        </Link>
                      </td>
                      <td className="p-4 text-[#5B6770] uppercase">{entry.realm}</td>
                      <td className="p-4 text-right">{entry.battles.toLocaleString()}</td>
                      <td className="p-4 text-right font-bold text-[#B3261E] text-sm">
                        {entry.winRate.toFixed(2)}%
                      </td>
                      <td className="p-4 text-right">{entry.avgDamage.toLocaleString()}</td>
                      <td className="p-4 text-right font-bold">{entry.kd.toFixed(2)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                      No records found for current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="border-b-2 border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                  <th className="p-4 font-bold uppercase w-16">RANK</th>
                  <th className="p-4 font-bold uppercase">CLAN DESIGNATION</th>
                  <th className="p-4 font-bold uppercase">THEATER</th>
                  <th className="p-4 font-bold uppercase text-right">PERSONNEL</th>
                  <th className="p-4 font-bold uppercase">COMMANDING ADMIRAL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A17] bg-white">
                {loadingLeaderboard ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                      Querying Clan Registry...
                    </td>
                  </tr>
                ) : clans.length > 0 ? (
                  clans.map((c) => (
                    <tr
                      key={c.clanId}
                      onClick={() => setSelectedClanId(c.clanId)}
                      className="hover:bg-[#F7F4EC] transition-colors cursor-pointer group"
                      title="Click to view clan roster & intelligence dossier"
                    >
                      <td className="p-4 font-bold text-sm">
                        {c.rank === 1 ? (
                          <span className="text-[#B3261E] font-black">01</span>
                        ) : (
                          String(c.rank).padStart(2, "0")
                        )}
                      </td>
                      <td className="p-4 font-sans font-bold text-sm">
                        <span className="font-mono text-[#B3261E] mr-2">[{c.tag}]</span>
                        <span className="text-[#1A1A17] group-hover:text-[#B3261E] transition-colors">{c.name}</span>
                      </td>
                      <td className="p-4 text-[#5B6770] uppercase">{c.realm}</td>
                      <td className="p-4 text-right font-bold">{c.membersCount} COMMANDERS</td>
                      <td className="p-4 text-[#5B6770]">{c.leaderName}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                      No clans registered in this operational theater.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* 04 — ENCYCLOPEDIA ARCHIVE CALLOUT */}
      <section className="border-2 border-[#1A1A17] bg-[#EFEBE0] p-8 mb-12 flex flex-col md:flex-row items-baseline justify-between gap-6">
        <div>
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
            03 // STATIC INTELLIGENCE REGISTER
          </div>
          <h3 className="text-2xl font-black uppercase tracking-tight text-[#1A1A17]">
            WARSHIP ENCYCLOPEDIA & ARCHIVE
          </h3>
          <p className="text-xs font-mono text-[#5B6770] mt-2 max-w-xl">
            Explore complete technical specifications, combat parameters, tier ratings, and silhouettes for over 1,000 commissioned naval vessels across all operational nations.
          </p>
        </div>
        <Link
          href="/encyclopedia"
          className="bg-[#1A1A17] hover:bg-[#B3261E] text-white px-8 py-4 font-mono text-xs uppercase tracking-[0.2em] font-bold transition-colors cursor-pointer self-end md:self-auto"
        >
          OPEN ENCYCLOPEDIA →
        </Link>
      </section>

      {selectedClanId && (
        <ClanModal clanId={selectedClanId} onClose={() => setSelectedClanId(null)} />
      )}
    </div>
  );
}
