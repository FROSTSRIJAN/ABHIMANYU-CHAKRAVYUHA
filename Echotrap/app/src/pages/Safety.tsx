import { Check, X, ShieldCheck, ListChecks, SearchCheck } from "lucide-react";
import { useI18n } from "@/lib/i18n";

export default function Safety() {
  const { t } = useI18n();

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <p className="micro-label flex items-center gap-2">
        <ShieldCheck className="h-3.5 w-3.5 text-sig-neutral" /> {t("nav.safety")}
      </p>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">{t("safety.title")}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
        {t("safety.sub")}
      </p>

      {/* does / does not */}
      <div className="mt-10 grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline md:grid-cols-2">
        <div className="bg-panel p-6">
          <h2 className="font-display text-lg font-semibold text-sig-neutral">{t("safety.doesTitle")}</h2>
          <ul className="mt-4 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <li key={i} className="flex gap-2.5 text-sm leading-relaxed text-foreground/85">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-sig-neutral" />
                {t(`safety.does${i}`)}
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-panel p-6">
          <h2 className="font-display text-lg font-semibold text-sig-strong">{t("safety.doesNotTitle")}</h2>
          <ul className="mt-4 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <li key={i} className="flex gap-2.5 text-sm leading-relaxed text-foreground/85">
                <X className="mt-0.5 h-4 w-4 shrink-0 text-sig-strong" />
                {t(`safety.doesNot${i}`)}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* checklist */}
      <section className="panel-2 mt-8 p-6 sm:p-8">
        <h2 className="flex items-center gap-2.5 font-display text-lg font-semibold">
          <ListChecks className="h-5 w-5 text-sig-cyan" /> {t("safety.checklistTitle")}
        </h2>
        <ol className="mt-5 grid gap-3 sm:grid-cols-2">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <li key={i} className="flex gap-3 rounded-md border border-hairline bg-panel p-3.5 text-[13px] leading-relaxed text-foreground/85">
              <span className="shrink-0 font-mono text-[11px] font-bold text-sig-cyan">
                {String(i).padStart(2, "0")}
              </span>
              {t(`safety.check${i}`)}
            </li>
          ))}
        </ol>
      </section>

      {/* verification guidance */}
      <section className="mt-8 rounded-lg border border-sig-watch/30 bg-sig-watch/5 p-6 sm:p-8">
        <h2 className="flex items-center gap-2.5 font-display text-lg font-semibold text-sig-watch">
          <SearchCheck className="h-5 w-5" /> {t("safety.verifyTitle")}
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-foreground/85">{t("safety.verifyBody")}</p>
        <p className="mt-3 text-sm leading-relaxed text-foreground/85">{t("safety.verifyBody2")}</p>
      </section>
    </div>
  );
}
