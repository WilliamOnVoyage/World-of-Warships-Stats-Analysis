export default function PlayerLoading() {
  return (
    <div className="flex-1 w-full max-w-7xl mx-auto px-6 py-12 animate-pulse">
      {/* Back Link & Stamp */}
      <div className="flex justify-between items-center mb-8 border-b border-[#1A1A17] pb-4">
        <div className="h-4 w-36 bg-zinc-300 rounded" />
        <span className="stamp-badge text-[10px]">
          CLASSIFIED // OFFICIAL COMBAT DOSSIER
        </span>
      </div>

      {/* Commander Header Dossier Skeleton */}
      <section className="border-b-2 border-[#1A1A17] pb-8 mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-4">
            <div className="h-3 w-48 bg-[#B3261E]/30 rounded" />
            <div className="h-16 md:h-24 w-80 md:w-96 bg-zinc-300 rounded" />
            <div className="flex gap-4">
              <div className="h-3 w-32 bg-zinc-300 rounded" />
              <div className="h-3 w-40 bg-zinc-300 rounded" />
              <div className="h-3 w-44 bg-zinc-300 rounded" />
            </div>
          </div>
          <div className="h-10 w-44 bg-zinc-300 rounded border border-[#1A1A17]" />
        </div>
      </section>

      {/* 01 — CORE COMBAT INDICATORS (4-COLUMN GRID) */}
      <section className="border-t-2 border-l-2 border-[#1A1A17] mb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          {[
            "01 // WIN RATE (PVP)",
            "02 // PVP BATTLES",
            "03 // AVERAGE DAMAGE",
            "04 // K/D RATIO"
          ].map((title, i) => (
            <div
              key={i}
              className="border-r-2 border-b-2 border-[#1A1A17] p-8 bg-[#F7F4EC]"
            >
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#5B6770] mb-2 font-bold">
                {title}
              </div>
              <div className="h-12 w-32 bg-zinc-300 rounded my-2" />
              <div className="h-3 w-28 bg-zinc-200 rounded mt-4 border-t border-zinc-300 pt-3" />
            </div>
          ))}
        </div>
      </section>

      {/* 02 — ENGAGEMENT THEATERS BREAKDOWN */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-8 mb-12">
        <div className="flex justify-between items-baseline mb-6 border-b border-[#1A1A17] pb-3">
          <div className="h-4 w-64 bg-zinc-300 rounded" />
          <div className="h-3 w-32 bg-zinc-200 rounded" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="border border-[#1A1A17] p-5 bg-white space-y-3">
              <div className="h-3 w-20 bg-zinc-200 rounded" />
              <div className="h-8 w-24 bg-zinc-300 rounded" />
              <div className="h-3 w-32 bg-zinc-200 rounded" />
            </div>
          ))}
        </div>
      </section>

      {/* 03 — EXTENDED COMBAT METRICS WIREFRAME */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-8 mb-12">
        <div className="flex justify-between items-baseline mb-6 border-b border-[#1A1A17] pb-3">
          <div className="h-4 w-72 bg-zinc-300 rounded" />
          <div className="h-3 w-36 bg-zinc-200 rounded" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {[1, 2, 3, 4, 5, 6].map((idx) => (
            <div key={idx} className="space-y-2">
              <div className="h-3 w-16 bg-zinc-200 rounded" />
              <div className="h-6 w-20 bg-zinc-300 rounded" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
