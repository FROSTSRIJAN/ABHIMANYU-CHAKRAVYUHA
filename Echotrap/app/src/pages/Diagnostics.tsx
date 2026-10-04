import { Activity } from "lucide-react";
import { trpc } from "@/providers/trpc";
import { useI18n } from "@/lib/i18n";
import { RiskBadge, riskBarColor } from "@/components/RiskBadge";
import type { RiskLevel } from "@contracts/analysis";
import { cn } from "@/lib/utils";

function Stat({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-panel p-5">
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className={cn("mt-2 text-2xl font-bold tabular-nums text-foreground", mono && "font-display")}>
        {value}
      </div>
    </div>
  );
}

export default function Diagnostics() {
  const { t, lang } = useI18n();
  const diag = trpc.analysis.diagnostics.useQuery();

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <p className="micro-label flex items-center gap-2">
        <Activity className="h-3.5 w-3.5 text-sig-cyan" /> {t("nav.diagnostics")}
      </p>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">{t("diag.title")}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
        {t("diag.sub")}
      </p>

      {/* model status */}
      <section className="panel mt-10 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-lg font-semibold">{t("diag.modelStatus")}</h2>
          <span className="inline-flex items-center gap-2 rounded border border-sig-neutral/40 bg-sig-neutral/10 px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-sig-neutral">
            <span className="led bg-sig-neutral text-sig-neutral" /> {t("diag.operational")}
          </span>
        </div>
        {diag.data ? (
          <div className="mt-5 grid gap-x-10 gap-y-3 font-mono text-xs sm:grid-cols-2">
            <div className="flex justify-between gap-4 border-b border-hairline/60 pb-2">
              <span className="text-muted-foreground">{t("diag.engine")}</span>
              <span className="text-foreground">{diag.data.engine.model}</span>
            </div>
            <div className="flex justify-between gap-4 border-b border-hairline/60 pb-2">
              <span className="text-muted-foreground">{t("diag.simMethod")}</span>
              <span className="text-right text-foreground">{diag.data.engine.similarityMethod}</span>
            </div>
            <div className="flex justify-between gap-4 border-b border-hairline/60 pb-2">
              <span className="text-muted-foreground">{t("diag.fallbackModel")}</span>
              <span className="text-right text-foreground">{diag.data.engine.fallbackModel}</span>
            </div>
            <div className="flex justify-between gap-4 border-b border-hairline/60 pb-2">
              <span className="text-muted-foreground">{t("diag.lexicons")}</span>
              <span className="text-right text-foreground">
                {diag.data.engine.lexiconSizes.hedge} {t("diag.hedge")} · {diag.data.engine.lexiconSizes.certainty}{" "}
                {t("diag.certainty")} · {diag.data.engine.lexiconSizes.urgency} {t("diag.urgency")}
              </span>
            </div>
          </div>
        ) : (
          <div className="mt-5 h-24 animate-pulse rounded bg-panel-2" />
        )}
      </section>

      {/* usage stats */}
      <section className="mt-8">
        <p className="micro-label">{t("diag.usageTitle")}</p>
        <p className="mt-1.5 text-sm text-muted-foreground">{t("diag.usageSub")}</p>
        {diag.data && diag.data.usage.totalRuns === 0 ? (
          <p className="panel mt-5 border-dashed p-6 text-center text-sm text-muted-foreground">
            {t("diag.noData")}
          </p>
        ) : (
          <div className="mt-5 grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline sm:grid-cols-2 xl:grid-cols-3">
            <Stat label={t("diag.totalRuns")} value={diag.data ? String(diag.data.usage.totalRuns) : "—"} />
            <Stat
              label={t("diag.avgScore")}
              value={diag.data?.usage.avgOverallScore != null ? String(diag.data.usage.avgOverallScore) : "—"}
            />
            <Stat
              label={t("diag.avgSim")}
              value={diag.data?.usage.avgSimilarity != null ? diag.data.usage.avgSimilarity.toFixed(2) : "—"}
            />
            <Stat
              label={t("diag.certShift")}
              value={
                diag.data?.usage.avgCertaintyShift != null
                  ? `${diag.data.usage.avgCertaintyShift > 0 ? "+" : ""}${diag.data.usage.avgCertaintyShift.toFixed(2)}`
                  : "—"
              }
            />
            <Stat
              label={t("diag.urgShift")}
              value={
                diag.data?.usage.avgUrgencyShift != null
                  ? `${diag.data.usage.avgUrgencyShift > 0 ? "+" : ""}${diag.data.usage.avgUrgencyShift.toFixed(2)}`
                  : "—"
              }
            />
            <Stat
              label={t("diag.lastRun")}
              value={
                diag.data?.usage.lastRunAt
                  ? new Date(diag.data.usage.lastRunAt).toLocaleString(lang === "hi" ? "hi-IN" : "en-GB")
                  : "—"
              }
              mono={false}
            />
          </div>
        )}

        {/* outcome distribution */}
        {diag.data && diag.data.usage.totalRuns > 0 && (
          <div className="panel mt-4 p-5">
            <p className="micro-label">{t("diag.levelDist")}</p>
            <div className="mt-4 flex h-3 w-full overflow-hidden rounded">
              {(["neutral", "watch", "strong"] as RiskLevel[]).map((lv) => {
                const count = diag.data.usage.levelDistribution[lv];
                const pct = (count / diag.data.usage.totalRuns) * 100;
                if (pct === 0) return null;
                return (
                  <div key={lv} className={riskBarColor(lv)} style={{ width: `${pct}%` }} title={`${lv}: ${count}`} />
                );
              })}
            </div>
            <div className="mt-3 flex flex-wrap gap-4">
              {(["neutral", "watch", "strong"] as RiskLevel[]).map((lv) => (
                <span key={lv} className="flex items-center gap-2 font-mono text-[11px] text-muted-foreground">
                  <RiskBadge level={lv} lang={lang} withDot={false} />
                  {diag.data.usage.levelDistribution[lv]}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* fallback note */}
      <section className="mt-8 rounded-lg border border-hairline bg-panel p-6">
        <h2 className="font-display text-lg font-semibold">{t("diag.fallbackTitle")}</h2>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t("diag.fallbackBody")}</p>
        <p className="mt-4 border-t border-hairline pt-4 text-xs text-muted-foreground">{t("diag.perRunNote")}</p>
      </section>
    </div>
  );
}
