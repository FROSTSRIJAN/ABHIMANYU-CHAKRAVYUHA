import { Link, useParams } from "react-router";
import { ArrowRight, TriangleAlert, Info } from "lucide-react";
import { trpc } from "@/providers/trpc";
import { useI18n } from "@/lib/i18n";
import { RiskBadge, riskTextColor, riskBarColor } from "@/components/RiskBadge";
import type { AnalysisResult, RiskLevel } from "@contracts/analysis";
import { cn } from "@/lib/utils";

/* ---------- summary banner ---------- */

const bannerStyles: Record<RiskLevel, string> = {
  neutral: "border-sig-neutral/40 bg-sig-neutral/5",
  watch: "border-sig-watch/40 bg-sig-watch/5",
  strong: "border-sig-strong/40 bg-sig-strong/5",
};

function SummaryBanner({ result }: { result: AnalysisResult }) {
  const { t, lang } = useI18n();
  return (
    <div className={cn("rounded-lg border p-6 sm:p-8", bannerStyles[result.overallLevel])}>
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <RiskBadge level={result.overallLevel} lang={lang} />
          <p className="micro-label mt-3">{t(`results.banner.${result.overallLevel}`)}</p>
          <h1 className="text-balance mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {result.headline}
          </h1>
          <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            {result.messageCount} {t("results.messages")} · {result.mutations.length} {t("results.mutationsFound")} ·{" "}
            {new Date(result.createdAt).toLocaleString(lang === "hi" ? "hi-IN" : "en-GB")}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <div className={cn("font-display text-6xl font-bold tabular-nums leading-none", riskTextColor(result.overallLevel))}>
            {result.overallScore}
          </div>
          <div className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            {t("results.score")}
          </div>
          <div className="mx-auto mt-3 h-1.5 w-28 overflow-hidden rounded bg-panel-2">
            <div className={cn("h-full", riskBarColor(result.overallLevel))} style={{ width: `${result.overallScore}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- timeline ---------- */

function AxisBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 shrink-0 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
        {label}
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded bg-panel-2">
        <div className={cn("h-full", color)} style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="w-9 text-right font-mono text-[10px] tabular-nums text-foreground/80">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function Timeline({ result }: { result: AnalysisResult }) {
  const { t } = useI18n();
  return (
    <section>
      <p className="micro-label">{t("results.timelineTitle")}</p>
      <p className="mt-1.5 text-sm text-muted-foreground">{t("results.timelineSub")}</p>
      <div className="mt-5 space-y-3">
        {result.timeline.map((pt) => (
          <div key={pt.index} className="panel relative p-4 pl-5 sm:p-5 sm:pl-6">
            <span
              className={cn(
                "absolute left-0 top-0 h-full w-[3px] rounded-l-lg",
                pt.index === result.timeline.length - 1
                  ? riskBarColor(result.overallLevel)
                  : "bg-hairline",
              )}
            />
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-mono text-xs font-bold uppercase tracking-[0.16em] text-sig-cyan">
                {pt.label}
              </span>
              {pt.similarityToPrevious !== null && (
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {t("results.simToPrev")}:{" "}
                  <span
                    className={cn(
                      "font-bold",
                      pt.similarityToPrevious < 0.4
                        ? "text-sig-strong"
                        : pt.similarityToPrevious < 0.7
                          ? "text-sig-watch"
                          : "text-sig-neutral",
                    )}
                  >
                    {(pt.similarityToPrevious * 100).toFixed(0)}%
                  </span>
                </span>
              )}
            </div>
            <p className="mt-2 truncate text-[13px] text-foreground/75">“{pt.excerpt}”</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <AxisBar label={t("results.certainty")} value={pt.certainty} color="bg-sig-cyan" />
              <AxisBar label={t("results.urgency")} value={pt.urgency} color="bg-sig-watch" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------- mutation list ---------- */

function MutationList({ result }: { result: AnalysisResult }) {
  const { t, lang } = useI18n();
  return (
    <section>
      <p className="micro-label">{t("results.mutationsTitle")}</p>
      <p className="mt-1.5 text-sm text-muted-foreground">{t("results.mutationsSub")}</p>
      {result.mutations.length === 0 ? (
        <p className="panel mt-5 border-dashed p-6 text-center text-sm text-muted-foreground">
          {t("results.noMutations")}
        </p>
      ) : (
        <div className="mt-5 space-y-3">
          {result.mutations.map((m, i) => (
            <div key={i} className="panel p-4 sm:p-5">
              <div className="flex flex-wrap items-center gap-2.5">
                <RiskBadge level={m.severity} lang={lang} withDot={false} />
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {t("results.transition")} {m.fromIndex + 1} → {m.toIndex + 1} · {m.type.replaceAll("_", " ")}
                </span>
                <span className={cn("ml-auto font-mono text-xs font-bold tabular-nums", riskTextColor(m.severity))}>
                  {m.score.toFixed(2)}
                </span>
              </div>
              <h3 className="mt-2.5 font-display text-base font-semibold">{m.summary}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{m.detail}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ---------- signal cards ---------- */

function SignalCards({ result }: { result: AnalysisResult }) {
  const { t, lang } = useI18n();
  return (
    <section>
      <p className="micro-label">{t("results.signalsTitle")}</p>
      <div className="mt-5 grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline sm:grid-cols-2 xl:grid-cols-4">
        {result.signals.map((s) => (
          <div key={s.key} className="bg-panel p-5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                {t(`results.signal.${s.key}`)}
              </span>
              <RiskBadge level={s.level} lang={lang} withDot={false} />
            </div>
            <div className={cn("mt-3 font-display text-3xl font-bold tabular-nums", riskTextColor(s.level))}>
              {s.value}
            </div>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{s.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------- page ---------- */

function Report({ result }: { result: AnalysisResult }) {
  const { t } = useI18n();
  return (
    <div className="space-y-12">
      <SummaryBanner result={result} />
      <Timeline result={result} />
      <MutationList result={result} />
      <SignalCards result={result} />

      <section className="panel-2 p-6">
        <p className="micro-label flex items-center gap-2">
          <Info className="h-3.5 w-3.5 text-sig-cyan" /> {t("results.explainTitle")}
        </p>
        <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-foreground/90">
          {result.plainExplanation}
        </p>
      </section>

      <section className="rounded-lg border border-sig-watch/30 bg-sig-watch/5 p-6">
        <p className="micro-label flex items-center gap-2 !text-sig-watch">
          <TriangleAlert className="h-3.5 w-3.5" /> {t("results.safetyTitle")}
        </p>
        <ol className="mt-4 space-y-2.5">
          {result.safetyNextSteps.map((s, i) => (
            <li key={i} className="flex gap-3 text-sm leading-relaxed text-foreground/85">
              <span className="mt-0.5 shrink-0 font-mono text-[11px] font-bold text-sig-watch">
                {String(i + 1).padStart(2, "0")}
              </span>
              {s}
            </li>
          ))}
        </ol>
        <p className="mt-5 border-t border-sig-watch/20 pt-4 text-xs leading-relaxed text-muted-foreground">
          <strong className="text-sig-watch">{t("results.disclaimerTitle")}:</strong> {t("common.disclaimer")}
        </p>
      </section>

      {/* per-run diagnostics footer */}
      <section className="panel p-5">
        <p className="micro-label">{t("diag.modelStatus")}</p>
        <div className="mt-3 grid gap-x-8 gap-y-2 font-mono text-[11px] text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
          <span>{t("diag.engine")}: <b className="text-foreground">{result.diagnostics.model}</b></span>
          <span>{t("diag.simMethod")}: <b className="text-foreground">{result.diagnostics.similarityMethod}</b></span>
          <span>runtime: <b className="text-foreground">{result.diagnostics.runtimeMs}ms</b></span>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{result.diagnostics.fallbackNote}</p>
      </section>
    </div>
  );
}

function RecentList() {
  const { t, lang } = useI18n();
  const recent = trpc.analysis.recent.useQuery();
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="font-display text-3xl font-bold tracking-tight">{t("results.recentTitle")}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{t("results.recentSub")}</p>
      {recent.data && recent.data.length === 0 && (
        <div className="panel mt-8 border-dashed p-10 text-center">
          <p className="text-sm text-muted-foreground">{t("results.empty")}</p>
          <Link
            to="/analyze"
            className="mt-5 inline-flex min-h-[48px] items-center gap-2 rounded-md bg-sig-cyan px-6 font-mono text-xs font-bold uppercase tracking-[0.14em] text-[#050810]"
          >
            {t("results.openAnalyzer")} <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}
      <div className="mt-8 space-y-3">
        {recent.data?.map((r) => (
          <Link
            key={r.id}
            to={`/results/${r.id}`}
            className="panel flex items-center gap-4 p-4 transition-colors hover:bg-panel-2"
          >
            <span className="font-mono text-xs text-muted-foreground">#{r.id}</span>
            <RiskBadge level={r.overallLevel} lang={lang} withDot={false} />
            <span className={cn("font-display text-xl font-bold tabular-nums", riskTextColor(r.overallLevel))}>
              {r.overallScore}
            </span>
            <span className="ml-auto font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {new Date(r.createdAt).toLocaleString(lang === "hi" ? "hi-IN" : "en-GB")}
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function Results() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const numId = id ? Number(id) : null;

  const query = trpc.analysis.get.useQuery(
    { id: numId ?? 0 },
    { enabled: !!numId && Number.isFinite(numId) },
  );

  if (!numId) return <RecentList />;

  if (query.isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-12 sm:px-6">
        {[0, 1, 2].map((i) => (
          <div key={i} className="panel h-32 animate-pulse bg-panel" />
        ))}
      </div>
    );
  }

  if (!query.data) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6">
        <p className="font-display text-xl font-bold">{t("common.notFound")}</p>
        <Link
          to="/analyze"
          className="mt-6 inline-flex min-h-[48px] items-center gap-2 rounded-md bg-sig-cyan px-6 font-mono text-xs font-bold uppercase tracking-[0.14em] text-[#050810]"
        >
          {t("results.openAnalyzer")} <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <Report result={query.data} />
    </div>
  );
}
