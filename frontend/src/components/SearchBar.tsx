"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SearchBar() {
  const [username, setUsername] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      router.push(`/player/${encodeURIComponent(username.trim())}`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-lg mt-8 relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
      <div className="relative flex items-center w-full h-14 rounded-xl bg-zinc-900/80 backdrop-blur-md border border-white/10 overflow-hidden shadow-2xl">
        <div className="grid place-items-center h-full w-12 text-zinc-400">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          className="peer h-full w-full outline-none text-sm text-zinc-100 bg-transparent pr-2 placeholder-zinc-500"
          type="text"
          id="search"
          placeholder="Search for a player (e.g. zmlzeze)..."
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button
          type="submit"
          className="h-full px-6 bg-white/5 hover:bg-white/10 text-zinc-300 transition-colors font-medium text-sm border-l border-white/10"
        >
          Search
        </button>
      </div>
    </form>
  );
}
