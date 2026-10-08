"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface Ship {
  shipId: number;
  name: string;
  tier: number;
  type: string;
  nation: string;
  isPremium: boolean;
  imageSmall: string | null;
  imageLarge: string | null;
  description?: string;
}

interface ShipSpecs {
  health: number;
  armourRange: { min: number; max: number };
  floodDamageReduction: number;
  artillery: {
    distance: number;
    shotDelay: number;
    rotationTime: number;
    maxDispersion: number;
    gunRate: number;
    shells: Record<
      string,
      {
        name?: string;
        damage?: number;
        burnProbability?: number;
        bulletSpeed?: number;
        bulletMass?: number;
      }
    >;
  } | null;
  torpedoes: {
    name?: string;
    distance: number;
    speed: number;
    maxDamage: number;
    reloadTime: number;
    visibilityDist: number;
  } | null;
  secondaries: {
    distance: number;
  } | null;
  mobility: {
    maxSpeed: number;
    turningRadius: number;
    rudderTime: number;
  };
  concealment: {
    detectShip: number;
    detectPlane: number;
  };
  antiAircraft: {
    defense: number;
  } | null;
}

const NATIONS = [
  { id: "all", label: "ALL NATIONS" },
  { id: "usa", label: "USA" },
  { id: "japan", label: "JAPAN" },
  { id: "germany", label: "GERMANY" },
  { id: "ussr", label: "USSR" },
  { id: "uk", label: "U.K." },
  { id: "france", label: "FRANCE" },
  { id: "italy", label: "ITALY" },
  { id: "pan_asia", label: "PAN-ASIA" },
  { id: "europe", label: "EUROPE" },
];

const SHIP_TYPES = [
  { id: "all", label: "ALL CLASSES" },
  { id: "Destroyer", label: "DESTROYER" },
  { id: "Cruiser", label: "CRUISER" },
  { id: "Battleship", label: "BATTLESHIP" },
  { id: "AirCarrier", label: "CARRIER" },
  { id: "Submarine", label: "SUBMARINE" },
];

const TIERS = [
  { id: 0, label: "ALL TIERS" },
  { id: 11, label: "XI (SUPER)" },
  { id: 10, label: "X" },
  { id: 9, label: "IX" },
  { id: 8, label: "VIII" },
  { id: 7, label: "VII" },
  { id: 6, label: "VI" },
  { id: 5, label: "V" },
  { id: 4, label: "IV" },
  { id: 3, label: "III" },
  { id: 2, label: "II" },
  { id: 1, label: "I" },
];

const toRoman = (num: number) => {
  return ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"][num] || String(num);
};

export default function EncyclopediaPage() {
  const [ships, setShips] = useState<Ship[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [selectedNation, setSelectedNation] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedTier, setSelectedTier] = useState<number>(0);
  const [premiumFilter, setPremiumFilter] = useState<string>("all"); // "all", "tech", "premium"
  const [selectedShip, setSelectedShip] = useState<Ship | null>(null);
  const [selectedShipSpecs, setSelectedShipSpecs] = useState<ShipSpecs | null>(null);
  const [loadingSpecs, setLoadingSpecs] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (selectedNation !== "all") params.append("nation", selectedNation);
    if (selectedType !== "all") params.append("type", selectedType);
    if (selectedTier > 0) params.append("tier", String(selectedTier));
    if (premiumFilter === "premium") params.append("is_premium", "true");
    if (premiumFilter === "tech") params.append("is_premium", "false");
    if (search.trim()) params.append("search", search.trim());
    params.append("limit", "100");

    fetch(`${API_BASE}/api/encyclopedia/ships?${params.toString()}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.ships) {
          setShips(data.ships);
          setTotalCount(data.total || data.ships.length);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedNation, selectedType, selectedTier, premiumFilter, search]);

  const handleOpenDossier = (s: Ship) => {
    setSelectedShip(s);
    setSelectedShipSpecs(null);
    setLoadingSpecs(true);
    fetch(`${API_BASE}/api/encyclopedia/ship/${s.shipId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.specs) {
          setSelectedShipSpecs(data.specs);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingSpecs(false));
  };

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
        <span className="stamp-badge text-[10px]">
          OFFICIAL REGISTER // CLASSIFICATION: PUBLIC
        </span>
      </div>

      {/* Header Banner */}
      <section className="border-b-2 border-[#1A1A17] pb-8 mb-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold mb-2">
              03 // STATIC INTELLIGENCE ARCHIVE
            </div>
            <h1 className="text-5xl md:text-7xl font-black uppercase tracking-tight text-[#1A1A17]">
              WARSHIP ENCYCLOPEDIA
            </h1>
            <p className="text-xs font-mono text-[#5B6770] mt-3 uppercase tracking-wider max-w-2xl">
              COMPREHENSIVE ADMIRALTY CATALOGUE OF 1,007 COMMISSIONED COMBAT VESSELS, ARCHIVAL SPECIFICATIONS, SILHOUETTES, AND DESIGNATION RATINGS.
            </p>
          </div>
          <div className="border-2 border-[#1A1A17] bg-[#F7F4EC] px-6 py-4 font-mono text-right">
            <div className="text-[10px] text-[#5B6770] uppercase">MATCHING VESSELS</div>
            <div className="text-3xl font-black text-[#1A1A17]">
              {loading ? "..." : `${totalCount} HULLS`}
            </div>
          </div>
        </div>
      </section>

      {/* Filters Control Center */}
      <section className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-6 mb-12">
        <div className="flex flex-col gap-5">
          {/* Search Box */}
          <div className="flex flex-col sm:flex-row border border-[#1A1A17] bg-white">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="SEARCH BY SHIP DESIGNATION (E.G. YAMATO, IOWA, BISMARCK)..."
              className="flex-1 px-4 py-3 text-sm font-mono uppercase tracking-wider outline-none bg-transparent text-[#1A1A17] placeholder:text-zinc-400"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="px-4 py-3 text-xs font-mono uppercase text-[#B3261E] font-bold hover:underline"
              >
                CLEAR
              </button>
            )}
          </div>

          {/* Filter Row 1: Nations */}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#5B6770] font-bold mb-2">
              OPERATIONAL THEATER / NATION:
            </div>
            <div className="flex flex-wrap gap-1.5 font-mono text-xs">
              {NATIONS.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setSelectedNation(n.id)}
                  className={`px-3 py-1.5 uppercase font-bold border border-[#1A1A17] transition-colors cursor-pointer ${
                    selectedNation === n.id
                      ? "bg-[#1A1A17] text-white"
                      : "bg-white text-[#5B6770] hover:text-[#1A1A17] hover:bg-[#EFEBE0]"
                  }`}
                >
                  {n.label}
                </button>
              ))}
            </div>
          </div>

          {/* Filter Row 2: Ship Class & Tier */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-zinc-300">
            {/* Classes */}
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-[#5B6770] font-bold mb-2">
                HULL CLASSIFICATION:
              </div>
              <div className="flex flex-wrap gap-1.5 font-mono text-xs">
                {SHIP_TYPES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedType(t.id)}
                    className={`px-3 py-1.5 uppercase font-bold border border-[#1A1A17] transition-colors cursor-pointer ${
                      selectedType === t.id
                        ? "bg-[#5B6770] text-white"
                        : "bg-white text-[#5B6770] hover:text-[#1A1A17]"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Premium vs Standard */}
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-[#5B6770] font-bold mb-2">
                COMMISSION STATUS:
              </div>
              <div className="flex flex-wrap gap-1.5 font-mono text-xs">
                {[
                  { id: "all", label: "ALL HULLS" },
                  { id: "tech", label: "STANDARD TECH TREE" },
                  { id: "premium", label: "PREMIUM / SPECIAL" },
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPremiumFilter(p.id)}
                    className={`px-3 py-1.5 uppercase font-bold border border-[#1A1A17] transition-colors cursor-pointer ${
                      premiumFilter === p.id
                        ? "bg-[#B3261E] text-white"
                        : "bg-white text-[#5B6770] hover:text-[#1A1A17]"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Filter Row 3: Tier Bar */}
          <div className="pt-2 border-t border-zinc-300">
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#5B6770] font-bold mb-2">
              TIER RATING:
            </div>
            <div className="flex flex-wrap gap-1 font-mono text-xs">
              {TIERS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTier(t.id)}
                  className={`px-2.5 py-1 uppercase font-bold border border-[#1A1A17] transition-colors cursor-pointer ${
                    selectedTier === t.id
                      ? "bg-[#1A1A17] text-white"
                      : "bg-white text-[#5B6770] hover:text-[#1A1A17]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Grid of Warships */}
      <section className="mb-16">
        {loading ? (
          <div className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-16 text-center font-mono text-sm uppercase text-[#5B6770] tracking-widest">
            Accessing Admiralty Warship Registry...
          </div>
        ) : ships.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {ships.map((s) => (
              <div
                key={s.shipId}
                onClick={() => handleOpenDossier(s)}
                className="border-2 border-[#1A1A17] bg-[#F7F4EC] hover:bg-white hover:border-[#B3261E] transition-all cursor-pointer flex flex-col justify-between group shadow-sm"
              >
                {/* Card Header */}
                <div className="p-4 border-b border-[#1A1A17] flex items-center justify-between bg-[#EFEBE0]">
                  <div className="flex items-center gap-2 font-mono text-xs font-bold">
                    <span className="text-[#B3261E]">{toRoman(s.tier)}</span>
                    <span className="text-[#5B6770] uppercase">• {s.nation}</span>
                  </div>
                  {s.isPremium && (
                    <span className="bg-[#B3261E] text-white font-mono text-[9px] font-bold px-1.5 py-0.5 tracking-wider uppercase">
                      PREMIUM
                    </span>
                  )}
                </div>

                {/* Card Silhouette Image */}
                <div className="h-32 flex items-center justify-center p-4 bg-zinc-900/5 group-hover:bg-zinc-900/10 transition-colors">
                  {s.imageSmall ? (
                    <img
                      src={s.imageSmall}
                      alt={s.name}
                      className="max-h-24 max-w-full object-contain filter drop-shadow-md group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="font-mono text-xs text-zinc-400 uppercase">NO SILHOUETTE</div>
                  )}
                </div>

                {/* Card Body */}
                <div className="p-5 flex-1 flex flex-col justify-between border-t border-[#1A1A17]">
                  <div>
                    <h3 className="text-xl font-black uppercase tracking-tight text-[#1A1A17] group-hover:text-[#B3261E] transition-colors">
                      {s.name}
                    </h3>
                    <div className="text-[11px] font-mono text-[#5B6770] uppercase mt-1">
                      {s.type}
                    </div>
                  </div>

                  {s.description && (
                    <p className="text-xs text-zinc-600 line-clamp-3 mt-3 font-serif italic border-t border-zinc-200 pt-2">
                      {s.description}
                    </p>
                  )}

                  <div className="mt-4 pt-3 border-t border-[#1A1A17] flex justify-between items-center text-[10px] font-mono text-[#5B6770]">
                    <span>HULL ID: {s.shipId}</span>
                    <span className="font-bold text-[#1A1A17] group-hover:text-[#B3261E]">
                      INSPECT DOSSIER →
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-16 text-center font-mono text-sm uppercase text-[#5B6770] tracking-widest">
            No commissioned warships matched current filter parameters.
          </div>
        )}
      </section>

      {/* Modal / Ship Dossier Viewer */}
      {selectedShip && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
          onClick={() => setSelectedShip(null)}
        >
          <div
            className="border-2 border-[#1A1A17] bg-[#EFEBE0] max-w-4xl w-full p-8 relative shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b-2 border-[#1A1A17] pb-4 mb-6">
              <div>
                <div className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold">
                  TACTICAL DOSSIER & ARCHIVE // ID: {selectedShip.shipId}
                </div>
                <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tight text-[#1A1A17] mt-1">
                  {selectedShip.name}
                </h2>
                <div className="flex flex-wrap gap-3 text-xs font-mono text-[#5B6770] uppercase mt-2">
                  <span className="font-bold text-[#B3261E]">TIER {toRoman(selectedShip.tier)}</span>
                  <span>•</span>
                  <span>THEATER: {selectedShip.nation}</span>
                  <span>•</span>
                  <span>CLASS: {selectedShip.type}</span>
                  {selectedShip.isPremium && (
                    <>
                      <span>•</span>
                      <span className="text-[#B3261E] font-bold">PREMIUM COMMISSION</span>
                    </>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSelectedShip(null)}
                className="text-2xl font-bold font-mono text-[#1A1A17] hover:text-[#B3261E] cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Artwork Banner */}
            {selectedShip.imageLarge || selectedShip.imageSmall ? (
              <div className="p-6 bg-[#F7F4EC] border border-[#1A1A17] mb-6 flex items-center justify-center">
                <img
                  src={selectedShip.imageLarge || selectedShip.imageSmall || ""}
                  alt={selectedShip.name}
                  className="max-h-56 max-w-full object-contain filter drop-shadow-lg"
                />
              </div>
            ) : null}

            {/* In-Game Technical Specifications Blueprint */}
            <div className="border-2 border-[#1A1A17] bg-[#F7F4EC] p-6 mb-6">
              <div className="flex justify-between items-baseline border-b border-[#1A1A17] pb-2 mb-4">
                <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#B3261E] font-bold">
                  VESSEL SPECIFICATIONS BLUEPRINT
                </span>
                <span className="text-[10px] font-mono text-[#5B6770] uppercase">
                  IN-GAME ACTIVE PROFILE
                </span>
              </div>

              {loadingSpecs ? (
                <div className="p-8 text-center font-mono text-xs uppercase text-[#5B6770] tracking-widest">
                  Retrieving Naval Parameters from Admiralty Archives...
                </div>
              ) : selectedShipSpecs ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 font-mono text-xs">
                  {/* Panel 1: Survivability & Armour */}
                  <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                    <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                      01 // SURVIVABILITY & ARMOUR
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">HIT POINTS:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.health.toLocaleString()} HP</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">ARMOUR PLATING:</span>
                        <span className="font-bold text-[#1A1A17]">
                          {selectedShipSpecs.armourRange.max > 0
                            ? `${selectedShipSpecs.armourRange.min} — ${selectedShipSpecs.armourRange.max} MM`
                            : "—"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">TORPEDO DEFENSE:</span>
                        <span className="font-bold text-[#B3261E]">
                          {selectedShipSpecs.floodDamageReduction > 0
                            ? `${selectedShipSpecs.floodDamageReduction}% REDUCTION`
                            : "—"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Panel 2: Artillery (if equipped) */}
                  {selectedShipSpecs.artillery ? (
                    <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                      <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                        02 // MAIN BATTERY ARTILLERY
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">FIRING RANGE:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.artillery.distance} KM</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">RELOAD CYCLE:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.artillery.shotDelay} S ({selectedShipSpecs.artillery.gunRate} RPM)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">180° TRAVERSE:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.artillery.rotationTime} S</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">MAX DISPERSION:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.artillery.maxDispersion} M</span>
                        </div>
                        {selectedShipSpecs.artillery.shells?.HE && (
                          <div className="flex justify-between text-[11px] pt-1 border-t border-zinc-300">
                            <span className="text-[#5B6770]">HE ALPHA / FIRE:</span>
                            <span className="font-bold text-[#1A1A17]">
                              {selectedShipSpecs.artillery.shells.HE.damage?.toLocaleString() || "—"} / {selectedShipSpecs.artillery.shells.HE.burnProbability}%
                            </span>
                          </div>
                        )}
                        {selectedShipSpecs.artillery.shells?.AP && (
                          <div className="flex justify-between text-[11px]">
                            <span className="text-[#5B6770]">AP ALPHA / SPEED:</span>
                            <span className="font-bold text-[#1A1A17]">
                              {selectedShipSpecs.artillery.shells.AP.damage?.toLocaleString() || "—"} / {selectedShipSpecs.artillery.shells.AP.bulletSpeed} M/S
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4 flex flex-col justify-center items-center text-[#5B6770]">
                      <div className="text-[10px] uppercase font-bold mb-1">02 // MAIN BATTERY</div>
                      <div>NO SURFACE ARTILLERY</div>
                    </div>
                  )}

                  {/* Panel 3: Torpedoes (if equipped) */}
                  {selectedShipSpecs.torpedoes ? (
                    <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                      <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                        03 // TORPEDO BATTERY
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">RANGE:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.torpedoes.distance} KM</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">SPEED:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.torpedoes.speed} KTS</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">MAX DAMAGE:</span>
                          <span className="font-bold text-[#B3261E]">{selectedShipSpecs.torpedoes.maxDamage.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">RELOAD:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.torpedoes.reloadTime} S</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5B6770]">DETECTION:</span>
                          <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.torpedoes.visibilityDist} KM</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4 flex flex-col justify-center items-center text-[#5B6770]">
                      <div className="text-[10px] uppercase font-bold mb-1">03 // TORPEDO BATTERY</div>
                      <div>NO TORPEDO TUBES</div>
                    </div>
                  )}

                  {/* Panel 4: Mobility & Propulsion */}
                  <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                    <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                      04 // PROPULSION & MANEUVERABILITY
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">MAX SPEED:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.mobility.maxSpeed} KTS</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">TURNING RADIUS:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.mobility.turningRadius} M</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">RUDDER SHIFT:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.mobility.rudderTime} S</span>
                      </div>
                    </div>
                  </div>

                  {/* Panel 5: Concealment */}
                  <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                    <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                      05 // CONCEALMENT & STEALTH
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">SURFACE DETECTION:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.concealment.detectShip} KM</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">AIR DETECTION:</span>
                        <span className="font-bold text-[#1A1A17]">{selectedShipSpecs.concealment.detectPlane} KM</span>
                      </div>
                    </div>
                  </div>

                  {/* Panel 6: Anti-Aircraft & Secondaries */}
                  <div className="border border-[#1A1A17] bg-[#EFEBE0] p-4">
                    <div className="text-[10px] uppercase font-bold text-[#5B6770] mb-2 border-b border-zinc-300 pb-1">
                      06 // DEFENSE & SECONDARIES
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">AA DEFENSE INDEX:</span>
                        <span className="font-bold text-[#1A1A17]">
                          {selectedShipSpecs.antiAircraft?.defense || "—"} / 100
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#5B6770]">SECONDARY RANGE:</span>
                        <span className="font-bold text-[#1A1A17]">
                          {selectedShipSpecs.secondaries?.distance ? `${selectedShipSpecs.secondaries.distance} KM` : "—"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 text-center text-[#5B6770]">
                  Technical parameters unavailable for this hull configuration.
                </div>
              )}
            </div>

            {/* Historical Description */}
            {selectedShip.description && (
              <div className="mb-6 font-serif text-sm text-zinc-800 leading-relaxed bg-[#F7F4EC] p-4 border border-[#1A1A17]">
                <div className="font-mono text-[10px] uppercase text-[#5B6770] font-bold mb-1">
                  HISTORICAL NAVAL ARCHIVE RECORD:
                </div>
                <p>{selectedShip.description}</p>
              </div>
            )}

            {/* Footer */}
            <div className="flex justify-between items-center pt-4 border-t border-[#1A1A17]">
              <span className="text-[10px] font-mono text-[#5B6770] uppercase">
                ADMIRALTY ARCHIVE RECORD • OFFICIAL WARGAMING VESSEL REGISTRY
              </span>
              <button
                onClick={() => setSelectedShip(null)}
                className="bg-[#1A1A17] hover:bg-[#B3261E] text-white px-6 py-2.5 font-mono text-xs uppercase tracking-widest font-bold transition-colors cursor-pointer"
              >
                CLOSE DOSSIER
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
