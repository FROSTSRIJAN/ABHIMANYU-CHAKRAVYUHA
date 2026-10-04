import { BookOpen } from "lucide-react";
import { useI18n } from "@/lib/i18n";

export default function Docs() {
  const { t } = useI18n();

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <p className="micro-label flex items-center gap-2">
        <BookOpen className="h-3.5 w-3.5 text-sig-cyan" /> {t("nav.docs")}
      </p>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">{t("docs.title")}</h1>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-base">{t("docs.sub")}</p>

      <div className="mt-10 space-y-10">
        <section>
          <h2 className="font-display text-xl font-semibold">{t("docs.whatTitle")}</h2>
          <p className="mt-3 text-sm leading-relaxed text-foreground/85">{t("docs.whatBody")}</p>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold">{t("docs.pipelineTitle")}</h2>
          <ol className="mt-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <li key={i} className="panel flex gap-3.5 p-4 text-sm leading-relaxed text-foreground/85">
                <span className="shrink-0 font-mono text-[11px] font-bold text-sig-cyan">
                  {String(i).padStart(2, "0")}
                </span>
                {t(`docs.pipe${i}`)}
              </li>
            ))}
          </ol>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold">{t("docs.contractTitle")}</h2>
          <p className="mt-3 text-sm leading-relaxed text-foreground/85">{t("docs.contractBody")}</p>
          <pre className="panel mt-4 overflow-x-auto p-4 font-mono text-[11px] leading-relaxed text-sig-cyan/90">
{`AnalysisResult {
  id, createdAt, messageCount
  overallLevel: "neutral" | "watch" | "strong"
  overallScore: 0..100
  headline: string
  timeline:  [{ label, similarityToPrevious, certainty, urgency, excerpt }]
  mutations: [{ type, severity, score, summary, detail }]
  signals:   [{ key, level, value, note }]
  plainExplanation: string
  safetyNextSteps: string[]
  diagnostics: { model, similarityMethod, fallbackUsed,
                 certaintyShift, urgencyShift, avgSimilarity,
                 perTransitionSimilarity[], runtimeMs }
}`}
          </pre>
        </section>

        <section>
          <h2 className="font-display text-xl font-semibold">{t("docs.limitsTitle")}</h2>
          <p className="mt-3 text-sm leading-relaxed text-foreground/85">{t("docs.limitsBody")}</p>
        </section>

        <section className="rounded-lg border border-sig-watch/30 bg-sig-watch/5 p-6">
          <h2 className="font-display text-xl font-semibold text-sig-watch">{t("docs.ethicsTitle")}</h2>
          <p className="mt-3 text-sm leading-relaxed text-foreground/85">{t("docs.ethicsBody")}</p>
        </section>
      </div>
    </div>
  );
}
