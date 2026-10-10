/**
 * Centralized numerical formatting utilities ensuring standard magnitude abbreviations
 * (K, M, B, T) and strict 2-decimal consistency across the Admiralty archive.
 */

export function formatMagnitude(n: number | null | undefined, decimals: number = 2): string {
  if (n === null || n === undefined || isNaN(n)) return (0).toFixed(decimals);
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000_000) return `${(n / 1_000_000_000_000).toFixed(decimals)}T`;
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(decimals)}B`;
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(decimals)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(decimals)}K`;
  return n.toFixed(decimals);
}

export function formatDecimals(n: number | null | undefined, decimals: number = 2): string {
  if (n === null || n === undefined || isNaN(n)) return (0).toFixed(decimals);
  return n.toFixed(decimals);
}

export function formatInteger(n: number | null | undefined): string {
  if (n === null || n === undefined || isNaN(n)) return "0";
  return Math.round(n).toLocaleString();
}

export function formatPercent(n: number | null | undefined, decimals: number = 2): string {
  if (n === null || n === undefined || isNaN(n)) return `${(0).toFixed(decimals)}%`;
  return `${n.toFixed(decimals)}%`;
}
