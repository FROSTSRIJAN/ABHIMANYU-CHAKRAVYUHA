export function RadarLogo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
      <circle cx="16" cy="16" r="14" stroke="#22d3ee" strokeOpacity="0.35" />
      <circle cx="16" cy="16" r="9.5" stroke="#22d3ee" strokeOpacity="0.5" />
      <circle cx="16" cy="16" r="5" stroke="#22d3ee" strokeOpacity="0.7" />
      <line x1="16" y1="2" x2="16" y2="6" stroke="#22d3ee" strokeOpacity="0.5" />
      <line x1="16" y1="26" x2="16" y2="30" stroke="#22d3ee" strokeOpacity="0.5" />
      <line x1="2" y1="16" x2="6" y2="16" stroke="#22d3ee" strokeOpacity="0.5" />
      <line x1="26" y1="16" x2="30" y2="16" stroke="#22d3ee" strokeOpacity="0.5" />
      <g className="origin-center animate-radar-sweep">
        <path d="M16 16 L16 2 A14 14 0 0 1 25.9 6.1 Z" fill="#22d3ee" fillOpacity="0.22" />
        <line x1="16" y1="16" x2="16" y2="2.5" stroke="#22d3ee" strokeWidth="1.4" />
      </g>
      <circle cx="21.5" cy="11.5" r="1.6" fill="#f87171" />
      <circle cx="16" cy="16" r="1.8" fill="#22d3ee" />
    </svg>
  );
}
