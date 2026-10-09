"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface ClanMember {
  accountId: number;
  nickname: string;
  role: string;
  joinedAt?: number;
}

interface ClanDossier {
  clanId: number;
  tag: string;
  name: string;
  realm?: string;
  membersCount: number;
  description?: string;
  leaderName?: string;
  createdAt?: number;
  members: ClanMember[];
}

interface ClanModalProps {
  clanId: number | null;
  onClose: () => void;
}

export default function ClanModal({ clanId, onClose }: ClanModalProps) {
  const [clan, setClan] = useState<ClanDossier | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clanId) {
      setClan(null);
      return;
    }

    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/clan/${clanId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Clan dossier not found");
        return res.json();
      })
      .then((data) => {
        setClan(data);
      })
      .catch((err) => {
        setError(err.message || "Failed to load clan dossier");
      })
      .finally(() => setLoading(false));
  }, [clanId]);

  if (!clanId) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="border-2 border-[#1A1A17] bg-[#EFEBE0] max-w-4xl w-full p-8 relative shadow-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-start border-b-2 border-[#1A1A17] pb-4 mb-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold">
                02 // OFFICIAL CLAN DOSSIER
              </span>
              <span className="stamp-badge text-[9px]">
                CLASSIFIED ROSTER
              </span>
            </div>
            <div className="flex items-baseline gap-3 mt-1">
              {clan && (
                <span className="text-3xl md:text-4xl font-mono font-black text-[#B3261E]">
                  [{clan.tag}]
                </span>
              )}
              <h2 className="text-3xl md:text-4xl font-black uppercase tracking-tight text-[#1A1A17]">
                {clan ? clan.name : `CLAN NO. ${clanId}`}
              </h2>
            </div>
            {clan && (
              <div className="flex flex-wrap gap-3 text-xs font-mono text-[#5B6770] uppercase mt-2">
                <span className="font-bold text-[#1A1A17]">THEATER: {clan.realm?.toUpperCase() || "NA"} SERVER</span>
                <span>•</span>
                <span>STRENGTH: {clan.membersCount} COMMANDERS</span>
                {clan.leaderName && (
                  <>
                    <span>•</span>
                    <span>COMMANDING ADMIRAL: {clan.leaderName}</span>
                  </>
                )}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-2xl font-bold font-mono text-[#1A1A17] hover:text-[#B3261E] cursor-pointer"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="p-16 text-center font-mono text-sm uppercase text-[#5B6770] tracking-widest">
            Accessing Admiralty Clan Records...
          </div>
        ) : error ? (
          <div className="p-12 text-center font-mono text-sm uppercase text-[#B3261E] tracking-wider">
            {error}
          </div>
        ) : clan ? (
          <>
            {clan.description && (
              <div className="border border-[#1A1A17] bg-[#F7F4EC] p-4 mb-6">
                <div className="text-[10px] font-mono text-[#5B6770] uppercase tracking-wider mb-1 font-bold">
                  FLEET CHARTER & DESIGNATION
                </div>
                <p className="text-xs font-serif italic text-zinc-700 whitespace-pre-line">
                  {clan.description}
                </p>
              </div>
            )}

            {/* Member Roster */}
            <div>
              <div className="flex justify-between items-baseline mb-3 border-b border-[#1A1A17] pb-2">
                <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#1A1A17] font-bold">
                  ACTIVE PERSONNEL ROSTER ({clan.members?.length || 0})
                </div>
                <span className="text-[10px] font-mono text-[#5B6770] uppercase">
                  SORTED BY RANK
                </span>
              </div>

              <div className="border border-[#1A1A17] bg-white overflow-x-auto">
                <table className="w-full text-left font-mono text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#1A1A17] bg-[#E5E1D5] text-[#1A1A17]">
                      <th className="p-3 font-bold uppercase w-12">#</th>
                      <th className="p-3 font-bold uppercase">COMMANDER HANDLE</th>
                      <th className="p-3 font-bold uppercase">FLEET ROLE</th>
                      <th className="p-3 font-bold uppercase text-right">ENLISTMENT DATE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200">
                    {clan.members && clan.members.length > 0 ? (
                      clan.members.map((m, idx) => (
                        <tr key={m.accountId} className="hover:bg-[#F7F4EC] transition-colors">
                          <td className="p-3 text-zinc-400 font-bold">
                            {String(idx + 1).padStart(2, "0")}
                          </td>
                          <td className="p-3 font-sans font-bold text-sm">
                            <Link
                              href={`/player/${encodeURIComponent(m.nickname)}`}
                              onClick={onClose}
                              className="text-[#1A1A17] hover:text-[#B3261E] hover:underline transition-colors"
                            >
                              {m.nickname}
                            </Link>
                          </td>
                          <td className="p-3 uppercase text-[#B3261E] font-bold text-[11px]">
                            {m.role?.replace(/_/g, " ") || "MEMBER"}
                          </td>
                          <td className="p-3 text-right text-[#5B6770]">
                            {m.joinedAt
                              ? new Date(m.joinedAt * 1000).toISOString().split("T")[0]
                              : "—"}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-6 text-center text-zinc-500 uppercase">
                          No roster personnel records available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
