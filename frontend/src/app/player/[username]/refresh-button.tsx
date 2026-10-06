"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function RefreshButton({ username }: { username: string }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await fetch(`/api/player/${encodeURIComponent(username)}?refresh=true`);
      router.refresh();
    } catch (e) {
      console.error("Refresh failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleRefresh}
      disabled={loading}
      className="px-4 py-2 bg-cyan-950/50 hover:bg-cyan-900/50 disabled:opacity-50 transition-colors rounded-lg text-sm font-medium border border-cyan-500/30 text-cyan-300 tracking-widest uppercase shadow-[0_0_10px_rgba(6,182,212,0.15)] hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] flex items-center gap-2"
    >
      {loading ? (
        <>
          <span className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
          SYNCING...
        </>
      ) : (
        "Refresh Stats"
      )}
    </button>
  );
}
