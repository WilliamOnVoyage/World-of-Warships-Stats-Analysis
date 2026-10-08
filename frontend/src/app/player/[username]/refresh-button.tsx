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
      className="px-5 py-3 bg-[#1A1A17] hover:bg-[#B3261E] disabled:opacity-50 transition-colors text-white text-xs font-mono font-bold tracking-widest uppercase flex items-center gap-2 cursor-pointer shadow-sm"
    >
      {loading ? (
        <>
          <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
          SYNCING COMBAT DOSSIER...
        </>
      ) : (
        "SYNC COMBAT DOSSIER →"
      )}
    </button>
  );
}
