"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function HeaderSearch() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/player/${encodeURIComponent(query.trim())}`);
      setQuery("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center">
      <div className="relative flex items-center border border-[#1A1A17] bg-white">
        <span className="pl-2 pr-1 font-mono text-[10px] text-[#5B6770] font-bold select-none">
          CMD:
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="SEARCH COMMANDER..."
          className="bg-transparent px-2 py-1 text-xs font-mono tracking-wider focus:outline-none w-36 md:w-44 text-[#1A1A17] placeholder-[#5B6770]/60 uppercase"
        />
        <button
          type="submit"
          className="bg-[#1A1A17] hover:bg-[#B3261E] text-white px-2.5 py-1 text-[11px] font-mono font-bold uppercase transition-colors cursor-pointer"
          title="Search commander dossier"
        >
          ↵
        </button>
      </div>
    </form>
  );
}
