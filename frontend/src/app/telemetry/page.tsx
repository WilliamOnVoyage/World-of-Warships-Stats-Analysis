"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface PipelineJob {
  jobName: string;
  cursor: number;
  status: string;
  heartbeat: string | null;
  heartbeatAgeMinutes: number | null;
  details: string | null;
}

interface DailyRollup {
  statDate: string;
  realm: string;
  activePlayers: number;
  battlesFought: number;
  totalTrackedPlayers: number;
  meanWinRate: number;
  damageDealt: number;
}

interface TelemetryData {
  timestamp: string;
  totalPlayers: number;
  totalSnapshots: number;
  pipelineJobs: PipelineJob[];
  dailyRollups: DailyRollup[];
  systemHealth: {
    ec2Status: string;
    rdsStatus: string;
    snsTopic: string;
    antiSpamPolicy: string;
    cloudWatchAlarms: string[];
  };
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export default function TelemetryDashboard() {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTelemetry = () => {
    setLoading(true);
    fetch(`${API_BASE}/api/telemetry/overview`)
      .then((res) => (res.ok ? res.json() : null))
      .then((res) => {
        if (res) setData(res);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const latestRollup = data?.dailyRollups?.[0];

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 w-full">
      {/* Navigation & Stamp */}
      <div className="mb-8 flex items-center justify-between border-b border-[#1A1A17] pb-4">
        <Link
          href="/"
          className="text-xs font-mono uppercase tracking-widest text-[#5B6770] hover:text-[#B3261E] flex items-center gap-2 group transition-colors"
        >
          <span className="group-hover:-translate-x-1 transition-transform">←</span>
          <span>RETURN TO DISPATCH</span>
        </Link>
        <div className="flex items-center gap-4">
          <button
            onClick={fetchTelemetry}
            className="text-xs font-mono uppercase tracking-widest text-[#5B6770] hover:text-[#B3261E] underline cursor-pointer"
          >
            [REFRESH DATA]
          </button>
          <span className="stamp-badge text-[10px]">
            TIER 3 // OPERATIONS & TELEMETRY
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <section className="border-b-2 border-[#1A1A17] pb-8 mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-2">
              04 // ADMIRALTY TELEMETRY & OPERATIONS REGISTER
            </div>
            <h1 className="text-5xl md:text-7xl font-black uppercase tracking-tight text-[#1A1A17]">
              OPERATIONS DASHBOARD
            </h1>
            <p className="text-xs font-mono text-[#5B6770] mt-3 uppercase tracking-wider max-w-2xl">
              REAL-TIME DATA PIPELINE TELEMETRY, INGESTION HARVESTER HEARTBEATS, DAILY FLEET ROLLUPS, AND SYSTEM HEALTH MONITORS.
            </p>
          </div>
          <div className="border-2 border-[#1A1A17] bg-[#F7F4EC] px-6 py-4 font-mono text-right">
            <div className="text-[10px] text-[#5B6770] uppercase">HEARTBEAT SYNC</div>
            <div className="text-xl font-black text-[#1A1A17]">
              {data ? new Date(data.timestamp).toLocaleTimeString("en-US", { timeZone: "UTC" }) : "..."} UTC
            </div>
          </div>
        </div>
      </section>

      {/* 4 Telemetry Metrics Cards */}
      <section className="border-t-2 border-l-2 border-[#1A1A17] mb-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          {/* Card 1 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              TOTAL REGISTERED FLEET
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {data ? formatNumber(data.totalPlayers) : "---"}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              NA • EU • ASIA REGISTERED HULLS
            </div>
          </div>

          {/* Card 2 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              COMBAT SNAPSHOTS
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              {data ? formatNumber(data.totalSnapshots) : "---"}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              DIFF-ONLY PARTITIONED RECORDS
            </div>
          </div>

          {/* Card 3 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              DAILY ACTIVE SORTIES
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#B3261E]">
              {latestRollup ? formatNumber(latestRollup.activePlayers) : "---"}
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              ACTIVE COMMANDERS (24H WINDOW)
            </div>
          </div>

          {/* Card 4 */}
          <div className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC] hover:bg-white transition-colors">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
              PIPELINE HARVEST RATE
            </div>
            <div className="text-5xl md:text-6xl font-black tracking-tight text-[#1A1A17]">
              10/S
            </div>
            <div className="text-xs font-mono text-[#5B6770] mt-4 border-t border-zinc-300 pt-3">
              WARGAMING API TOKEN BUDGET
            </div>
          </div>
        </div>
      </section>

      {/* 01 — ACTIVE INGESTION PIPELINES & HARVESTERS */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] mb-14">
        <div className="p-6 border-b-2 border-[#1A1A17] bg-[#EFEBE0] flex justify-between items-baseline">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
              01 // ACTIVE INGESTION PIPELINES & HARVESTERS
            </div>
            <h2 className="text-2xl font-black uppercase tracking-tight text-[#1A1A17]">
              PIPELINE WORKERS & DISCOVERY ENGINES
            </h2>
          </div>
          <span className="text-xs font-mono text-[#5B6770] uppercase">
            AUTONOMOUS BACKGROUND WORKERS
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b-2 border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                <th className="p-4 font-bold uppercase w-16">#</th>
                <th className="p-4 font-bold uppercase">JOB DESIGNATION</th>
                <th className="p-4 font-bold uppercase">STATUS</th>
                <th className="p-4 font-bold uppercase text-right">CURSOR ID</th>
                <th className="p-4 font-bold uppercase text-right">HEARTBEAT</th>
                <th className="p-4 font-bold uppercase">ACTIVITY REPORT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A1A17] bg-white">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                    Polling Pipeline Status...
                  </td>
                </tr>
              ) : data && data.pipelineJobs.length > 0 ? (
                data.pipelineJobs.map((job, idx) => (
                  <tr key={job.jobName} className="hover:bg-[#F7F4EC] transition-colors">
                    <td className="p-4 font-bold text-[#5B6770]">
                      {String(idx + 1).padStart(2, "0")}
                    </td>
                    <td className="p-4 font-sans font-bold text-sm">
                      <span className="font-mono text-xs bg-zinc-100 border border-zinc-300 px-2 py-0.5 mr-2">
                        {job.jobName.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                        {job.status}
                      </span>
                    </td>
                    <td className="p-4 text-right font-bold text-[#1A1A17]">
                      {job.cursor ? job.cursor.toLocaleString() : "0"}
                    </td>
                    <td className="p-4 text-right">
                      {job.heartbeatAgeMinutes !== null ? (
                        <span className={job.heartbeatAgeMinutes < 15 ? "text-emerald-700 font-bold" : "text-amber-700"}>
                          {job.heartbeatAgeMinutes === 0 ? "JUST NOW" : `${job.heartbeatAgeMinutes}M AGO`}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="p-4 text-[#5B6770]">
                      {job.details || "Active and processing records."}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                    No active pipeline jobs recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 02 — DAILY HISTORICAL SERVER ROLLUPS */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] mb-14">
        <div className="p-6 border-b-2 border-[#1A1A17] bg-[#EFEBE0] flex justify-between items-baseline">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
              02 // DAILY HISTORICAL SERVER ROLLUPS
            </div>
            <h2 className="text-2xl font-black uppercase tracking-tight text-[#1A1A17]">
              CHRONOLOGICAL SERVER TELEMETRY ARCHIVE
            </h2>
          </div>
          <span className="text-xs font-mono text-[#5B6770] uppercase">
            IMMUTABLE PARTITION SNAPSHOTS
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b-2 border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                <th className="p-4 font-bold uppercase">DATE (UTC)</th>
                <th className="p-4 font-bold uppercase">THEATER</th>
                <th className="p-4 font-bold uppercase text-right">TRACKED FLEET</th>
                <th className="p-4 font-bold uppercase text-right">ACTIVE SORTIES</th>
                <th className="p-4 font-bold uppercase text-right">BATTLES ANALYZED</th>
                <th className="p-4 font-bold uppercase text-right">MEAN WIN RATE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A1A17] bg-white">
              {data && data.dailyRollups.length > 0 ? (
                data.dailyRollups.map((r) => (
                  <tr key={`${r.statDate}-${r.realm}`} className="hover:bg-[#F7F4EC] transition-colors">
                    <td className="p-4 font-bold font-sans text-sm text-[#1A1A17]">
                      {r.statDate}
                    </td>
                    <td className="p-4 uppercase text-[#5B6770]">
                      {r.realm.toUpperCase()}
                    </td>
                    <td className="p-4 text-right font-bold text-[#1A1A17]">
                      {r.totalTrackedPlayers.toLocaleString()}
                    </td>
                    <td className="p-4 text-right text-[#B3261E] font-bold">
                      {r.activePlayers.toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      {r.battlesFought.toLocaleString()}
                    </td>
                    <td className="p-4 text-right font-bold">
                      {r.meanWinRate.toFixed(2)}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-zinc-500 uppercase tracking-widest">
                    No historical rollups compiled yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 03 — INFRASTRUCTURE HEALTH & MONITORING SPECIFICATION */}
      <section className="border-2 border-[#1A1A17] bg-[#EFEBE0] p-8 mb-12">
        <div className="border-b border-[#1A1A17] pb-4 mb-6">
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-1">
            03 // INFRASTRUCTURE & ALERTING SPECIFICATION
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tight text-[#1A1A17]">
            AWS INFRASTRUCTURE & ANTI-FATIGUE POLICY
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
          <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
            <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
              COMPUTE HOST (EC2)
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between">
                <span className="text-[#5B6770]">INSTANCE ID:</span>
                <span className="font-bold text-[#1A1A17]">i-06bef9ba2c963cd36</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">PUBLIC IP:</span>
                <span className="font-bold text-[#1A1A17]">44.253.134.12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">CLOUDWATCH ALARM:</span>
                <span className="font-bold text-emerald-700">STATUS CHECK (OK)</span>
              </div>
            </div>
          </div>

          <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
            <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
              RELATIONAL STORAGE (RDS)
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between">
                <span className="text-[#5B6770]">CLUSTER ID:</span>
                <span className="font-bold text-[#1A1A17]">wows-stats-db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">ALLOCATED DISK:</span>
                <span className="font-bold text-[#1A1A17]">20 GB POSTGRESQL</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">STORAGE BUFFER:</span>
                <span className="font-bold text-emerald-700">~17.4 GB FREE (OK)</span>
              </div>
            </div>
          </div>

          <div className="border border-[#1A1A17] bg-[#F7F4EC] p-5">
            <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
              ALERTING POLICY
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between">
                <span className="text-[#5B6770]">DISPATCH TOPIC:</span>
                <span className="font-bold text-[#1A1A17]">WoWS-Stats-Critical</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">ANTI-SPAM:</span>
                <span className="font-bold text-[#B3261E]">12H COOLDOWN LOCK</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5B6770]">TIER 3 NOISE:</span>
                <span className="font-bold text-[#1A1A17]">0 EMAILS (DASHBOARD ONLY)</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
