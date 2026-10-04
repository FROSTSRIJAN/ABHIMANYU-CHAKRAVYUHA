import type { RiskLevel } from "@contracts/analysis";
import { cn } from "@/lib/utils";

const styles: Record<RiskLevel, string> = {
  neutral: "border-sig-neutral/40 bg-sig-neutral/10 text-sig-neutral",
  watch: "border-sig-watch/40 bg-sig-watch/10 text-sig-watch",
  strong: "border-sig-strong/40 bg-sig-strong/10 text-sig-strong",
};

const dotColor: Record<RiskLevel, string> = {
  neutral: "text-sig-neutral bg-sig-neutral",
  watch: "text-sig-watch bg-sig-watch",
  strong: "text-sig-strong bg-sig-strong",
};

const labels: Record<RiskLevel, { en: string; hi: string }> = {
  neutral: { en: "NEUTRAL", hi: "तटस्थ" },
  watch: { en: "WATCH", hi: "निगरानी" },
  strong: { en: "STRONG", hi: "प्रबल" },
};

export function RiskBadge({
  level,
  lang = "en",
  className,
  withDot = true,
}: {
  level: RiskLevel;
  lang?: "en" | "hi";
  className?: string;
  withDot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.16em]",
        styles[level],
        className,
      )}
    >
      {withDot && <span className={cn("led", dotColor[level])} />}
      {labels[level][lang]}
    </span>
  );
}

export function riskTextColor(level: RiskLevel): string {
  return level === "strong"
    ? "text-sig-strong"
    : level === "watch"
      ? "text-sig-watch"
      : "text-sig-neutral";
}

export function riskBarColor(level: RiskLevel): string {
  return level === "strong"
    ? "bg-sig-strong"
    : level === "watch"
      ? "bg-sig-watch"
      : "bg-sig-neutral";
}
