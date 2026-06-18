"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  type TooltipProps,
} from "recharts";

interface HistoryPoint {
  date: string;
  battles: number;
  winRate: number;
  avgDamage: number;
}

// Custom Neon Tactical themed tooltip
function NeonTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#0a0a1a]/95 border border-cyan-500/40 backdrop-blur-md px-4 py-3 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
      <p className="text-cyan-400 text-xs tracking-widest font-bold mb-2 uppercase">
        {label}
      </p>
      {payload.map((entry: any, idx: number) => (
        <p key={idx} className="text-sm" style={{ color: entry.color }}>
          <span className="text-zinc-400 mr-2">{entry.name}:</span>
          <span className="font-bold">
            {typeof entry.value === "number"
              ? entry.name === "Win Rate"
                ? `${entry.value.toFixed(2)}%`
                : entry.value.toLocaleString()
              : entry.value}
          </span>
        </p>
      ))}
    </div>
  );
}

// Shared axis styling
const axisProps = {
  tick: { fill: "#6b7280", fontSize: 11, fontFamily: "monospace" },
  tickLine: false,
  axisLine: { stroke: "#1e293b" },
};

export function WinRateChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
      <h3 className="text-xs tracking-[0.2em] text-cyan-500 font-bold mb-4 uppercase">
        Win Rate Trend
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="winRateGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${v}%`}
            {...axisProps}
          />
          <Tooltip content={<NeonTooltip />} />
          <Area
            type="monotone"
            dataKey="winRate"
            name="Win Rate"
            stroke="#06b6d4"
            strokeWidth={2}
            fill="url(#winRateGrad)"
            dot={{ r: 3, fill: "#06b6d4", strokeWidth: 0 }}
            activeDot={{
              r: 6,
              fill: "#06b6d4",
              stroke: "#0a0a1a",
              strokeWidth: 2,
            }}
            animationDuration={1200}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AvgDamageChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
      <h3 className="text-xs tracking-[0.2em] text-cyan-500 font-bold mb-4 uppercase">
        Average Damage
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="dmgGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#d946ef" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#d946ef" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis
            tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`}
            {...axisProps}
          />
          <Tooltip content={<NeonTooltip />} />
          <Area
            type="monotone"
            dataKey="avgDamage"
            name="Avg Damage"
            stroke="#d946ef"
            strokeWidth={2}
            fill="url(#dmgGrad)"
            dot={{ r: 3, fill: "#d946ef", strokeWidth: 0 }}
            activeDot={{
              r: 6,
              fill: "#d946ef",
              stroke: "#0a0a1a",
              strokeWidth: 2,
            }}
            animationDuration={1200}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BattlesChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#080818]/60 border border-cyan-900/40 rounded-xl p-5 backdrop-blur-sm">
      <h3 className="text-xs tracking-[0.2em] text-cyan-500 font-bold mb-4 uppercase">
        Battles Played
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.9} />
              <stop offset="100%" stopColor="#0e7490" stopOpacity={0.4} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis {...axisProps} />
          <Tooltip content={<NeonTooltip />} />
          <Bar
            dataKey="battles"
            name="Battles"
            fill="url(#barGrad)"
            radius={[4, 4, 0, 0]}
            animationDuration={1200}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
