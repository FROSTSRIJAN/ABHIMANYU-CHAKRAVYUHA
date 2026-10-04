import { Link } from "react-router";
import { ArrowRight, ScanSearch, ShieldCheck, FileSearch, MoveRight } from "lucide-react";
import { useI18n } from "@/lib/i18n";

function Ticker() {
  const { t } = useI18n();
  const items = [1, 2, 3, 4, 5, 6].map((i) => t(`home.ticker.${i}`));
  const row = [...items, ...items];
  return (
    <div className="overflow-hidden border-y border-hairline bg-panel py-2" aria-hidden>
      <div className="flex w-max animate-marquee gap-10">
        {row.map((item, i) => (
          <span
            key={i}
            className="flex items-center gap-2 whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            <span className="led bg-sig-cyan text-sig-cyan" />
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function HeroVisual() {
  // Code-drawn "mutation radar": concentric scan rings with a claim drifting off-center
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[380px]">
      <svg viewBox="0 0 400 400" className="h-full w-full">
        <defs>
          <radialGradient id="fade" cx="50%" cy="50%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="200" cy="200" r="190" fill="url(#fade)" />
        {[190, 150, 110, 70, 32].map((r) => (
          <circle key={r} cx="200" cy="200" r={r} stroke="#1a2540" fill="none" />
        ))}
        <line x1="200" y1="10" x2="200" y2="390" stroke="#1a2540" />
        <line x1="10" y1="200" x2="390" y2="200" stroke="#1a2540" />
        {/* sweep */}
        <g className="origin-[200px_200px] animate-radar-sweep">
          <path d="M200 200 L200 12 A188 188 0 0 1 333 67 Z" fill="#22d3ee" fillOpacity="0.13" />
          <line x1="200" y1="200" x2="200" y2="14" stroke="#22d3ee" strokeWidth="1.5" />
        </g>
        {/* the claim, drifting outward across 4 versions */}
        <circle cx="200" cy="200" r="5" fill="#34d399" />
        <text x="212" y="196" fill="#34d399" fontSize="10" fontFamily="JetBrains Mono, monospace">v1</text>
        <circle cx="244" cy="176" r="5.5" fill="#34d399" fillOpacity="0.85" />
        <text x="256" y="172" fill="#34d399" fontSize="10" fontFamily="JetBrains Mono, monospace" opacity="0.8">v2</text>
        <circle cx="296" cy="146" r="6" fill="#fbbf24" />
        <text x="308" y="142" fill="#fbbf24" fontSize="10" fontFamily="JetBrains Mono, monospace">v3</text>
        <circle cx="352" cy="104" r="7" fill="#f87171" className="animate-led-pulse" />
        <text x="330" y="90" fill="#f87171" fontSize="10" fontFamily="JetBrains Mono, monospace">v4 !</text>
        {/* drift path */}
        <path d="M200 200 L244 176 L296 146 L352 104" stroke="#f87171" strokeOpacity="0.4" strokeDasharray="4 4" fill="none" />
      </svg>
      <div className="absolute bottom-2 left-1/2 w-max -translate-x-1/2 rounded border border-hairline bg-panel px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        mutation trajectory · 4 versions
      </div>
    </div>
  );
}

const FLOW_STEPS = [1, 2, 3, 4] as const;
const FLOW_COLORS = ["border-sig-neutral/50", "border-sig-neutral/30", "border-sig-watch/50", "border-sig-strong/60"];
const FLOW_TEXT = ["text-sig-neutral", "text-sig-neutral/80", "text-sig-watch", "text-sig-strong"];

export default function Home() {
  const { t } = useI18n();

  return (
    <div>
      {/* Hero */}
      <section className="mx-auto grid max-w-7xl items-center gap-10 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:pt-20">
        <div>
          <p className="micro-label flex items-center gap-2">
            <span className="led bg-sig-cyan text-sig-cyan" />
            {t("home.kicker")}
          </p>
          <h1 className="text-balance mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            {t("home.titleA")}{" "}
            <span className="text-sig-cyan">{t("home.titleB")}</span>
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            {t("home.subtitle")}
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/analyze"
              className="glow-cyan inline-flex min-h-[48px] items-center justify-center gap-2 rounded-md bg-sig-cyan px-6 font-mono text-sm font-bold uppercase tracking-[0.12em] text-[#050810] transition-transform active:scale-[0.98]"
            >
              {t("home.ctaAnalyze")} <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/safety"
              className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-md border border-hairline bg-panel px-6 font-mono text-sm font-semibold uppercase tracking-[0.12em] text-foreground transition-colors hover:bg-panel-2 active:scale-[0.98]"
            >
              <ShieldCheck className="h-4 w-4 text-sig-neutral" />
              {t("home.ctaSafety")}
            </Link>
          </div>
        </div>
        <HeroVisual />
      </section>

      <Ticker />

      {/* Why EchoTrap */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <p className="micro-label">01 — {t("home.whyTitle")}</p>
        <h2 className="mt-3 max-w-2xl font-display text-2xl font-bold tracking-tight sm:text-3xl">
          {t("home.whySub")}
        </h2>
        <div className="mt-10 grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline md:grid-cols-3">
          {[
            { icon: ScanSearch, title: t("home.why1Title"), body: t("home.why1Body") },
            { icon: ShieldCheck, title: t("home.why2Title"), body: t("home.why2Body") },
            { icon: FileSearch, title: t("home.why3Title"), body: t("home.why3Body") },
          ].map((f, i) => (
            <div key={i} className="bg-panel p-6">
              <f.icon className="h-5 w-5 text-sig-cyan" />
              <h3 className="mt-4 font-display text-lg font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Example mutation flow */}
      <section className="border-y border-hairline bg-panel/50">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <p className="micro-label">02 — {t("home.flowTitle")}</p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {t("home.flowSub")}
          </h2>
          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {FLOW_STEPS.map((step, i) => (
              <div key={step} className="relative">
                <div className={`panel flex h-full flex-col border-l-[3px] p-5 ${FLOW_COLORS[i]}`}>
                  <div className="flex items-center justify-between">
                    <span className={`font-mono text-[10px] font-bold uppercase tracking-[0.2em] ${FLOW_TEXT[i]}`}>
                      {t("home.flowStep")} {step}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {t(`home.flow${step}Label`)}
                    </span>
                  </div>
                  <p className="mt-4 flex-1 text-[13px] leading-relaxed text-foreground/90">
                    “{t(`home.flow${step}Text`)}”
                  </p>
                  <p className={`mt-4 border-t border-hairline pt-3 font-mono text-[10px] uppercase tracking-[0.14em] ${FLOW_TEXT[i]}`}>
                    {t(`home.flow${step}Note`)}
                  </p>
                </div>
                {i < 3 && (
                  <MoveRight className="absolute -right-3.5 top-1/2 z-10 hidden h-5 w-5 -translate-y-1/2 text-sig-cyan xl:block" />
                )}
              </div>
            ))}
          </div>
          <p className="mt-8 max-w-3xl font-display text-lg font-medium text-foreground/90">
            {t("home.flowVerdict")}
          </p>
        </div>
      </section>

      {/* CTA + compliance */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="panel-2 flex flex-col items-start justify-between gap-6 p-8 lg:flex-row lg:items-center">
          <div className="max-w-xl">
            <p className="micro-label">03 — {t("home.complianceTitle")}</p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t("home.complianceBody")}</p>
          </div>
          <Link
            to="/analyze"
            className="inline-flex min-h-[48px] shrink-0 items-center gap-2 rounded-md bg-sig-cyan px-6 font-mono text-sm font-bold uppercase tracking-[0.12em] text-[#050810] transition-transform active:scale-[0.98]"
          >
            {t("home.ctaAnalyze")} <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
