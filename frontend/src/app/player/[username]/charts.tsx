"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface HistoryPoint {
  date: string;
  battles: number;
  winRate: number;
  avgDamage: number;
}

interface TooltipPayloadItem {
  color?: string;
  name?: string;
  value?: number | string;
}

interface TooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

function ArchivalTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-[#1A1A17] text-white p-3 font-mono text-xs border border-black shadow-lg">
      <p className="text-zinc-400 uppercase tracking-widest text-[10px] mb-1">
        RECORD DATE: {label}
      </p>
      {payload.map((entry, idx) => (
        <p key={idx} className="mt-1">
          <span className="text-zinc-400 mr-2">{entry.name}:</span>
          <span className="font-bold text-[#B3261E]">
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

const axisProps = {
  tick: { fill: "#1A1A17", fontSize: 11, fontFamily: "monospace" },
  tickLine: false,
  axisLine: { stroke: "#1A1A17" },
};

export function WinRateChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#F7F4EC] border-2 border-[#1A1A17] p-6">
      <div className="flex justify-between items-baseline mb-4 border-b border-[#1A1A17] pb-2">
        <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
          01 // WIN RATE TRAJECTORY
        </h3>
        <span className="text-[10px] font-mono text-[#5B6770] uppercase">
          CHRONOLOGICAL LOG
        </span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
          <CartesianGrid stroke="#DAD8CE" vertical={false} />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${v}%`}
            {...axisProps}
          />
          <Tooltip content={<ArchivalTooltip />} />
          <Area
            type="linear"
            dataKey="winRate"
            name="Win Rate"
            stroke="#1A1A17"
            strokeWidth={2}
            fill="#EFEBE0"
            dot={{ r: 4, fill: "#B3261E", stroke: "#1A1A17", strokeWidth: 1.5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AvgDamageChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#F7F4EC] border-2 border-[#1A1A17] p-6">
      <div className="flex justify-between items-baseline mb-4 border-b border-[#1A1A17] pb-2">
        <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
          02 // AVERAGE DAMAGE TREND
        </h3>
        <span className="text-[10px] font-mono text-[#5B6770] uppercase">
          STRUCTURAL DAMAGE
        </span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#DAD8CE" vertical={false} />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
            {...axisProps}
          />
          <Tooltip content={<ArchivalTooltip />} />
          <Area
            type="linear"
            dataKey="avgDamage"
            name="Avg Damage"
            stroke="#1A1A17"
            strokeWidth={2}
            fill="#EFEBE0"
            dot={{ r: 4, fill: "#1A1A17", stroke: "#1A1A17", strokeWidth: 1 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BattlesChart({ data }: { data: HistoryPoint[] }) {
  return (
    <div className="bg-[#F7F4EC] border-2 border-[#1A1A17] p-6">
      <div className="flex justify-between items-baseline mb-4 border-b border-[#1A1A17] pb-2">
        <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
          03 // CUMULATIVE PVP BATTLES
        </h3>
        <span className="text-[10px] font-mono text-[#5B6770] uppercase">
          ENGAGEMENT VOLUME
        </span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#DAD8CE" vertical={false} />
          <XAxis dataKey="date" {...axisProps} />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v: number) => v.toLocaleString()}
            {...axisProps}
          />
          <Tooltip content={<ArchivalTooltip />} />
          <Bar dataKey="battles" name="Battles" fill="#1A1A17" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
