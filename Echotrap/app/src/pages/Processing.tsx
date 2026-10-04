import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { Check, Loader2 } from "lucide-react";
import { trpc } from "@/providers/trpc";
import { useI18n } from "@/lib/i18n";
import { RadarLogo } from "@/components/RadarLogo";
import { cn } from "@/lib/utils";

const STEP_COUNT = 5;
const STEP_MS = 950;
const MIN_TOTAL_MS = STEP_COUNT * STEP_MS + 600;

export default function Processing() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const id = (location.state as { id?: number } | null)?.id;

  const [step, setStep] = useState(0);
  const startedAt = useMemo(() => Date.now(), []);

  // Redirect away if landed here without a run id
  useEffect(() => {
    if (!id) navigate("/analyze", { replace: true });
  }, [id, navigate]);

  // Fetch the finished report
  const resultQuery = trpc.analysis.get.useQuery(
    { id: id ?? 0 },
    { enabled: !!id, retry: 2 },
  );

  // Staged step progression
  useEffect(() => {
    const iv = setInterval(() => {
      setStep((s) => Math.min(s + 1, STEP_COUNT));
    }, STEP_MS);
    return () => clearInterval(iv);
  }, []);

  // Leave only when both the animation finished AND the data arrived
  useEffect(() => {
    if (!id || !resultQuery.data) return;
    const elapsed = Date.now() - startedAt;
    const wait = Math.max(0, MIN_TOTAL_MS - elapsed);
    const to = setTimeout(() => navigate(`/results/${id}`, { replace: true }), wait);
    return () => clearTimeout(to);
  }, [id, resultQuery.data, navigate, startedAt]);

  if (!id) return null;

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-20 sm:px-6">
      <div className="glow-cyan rounded-full border border-hairline bg-panel p-6">
        <RadarLogo size={88} />
      </div>

      <h1 className="mt-8 text-center font-display text-2xl font-bold tracking-tight sm:text-3xl">
        {t("processing.title")}
      </h1>
      <p className="mt-2 text-center text-sm text-muted-foreground">{t("processing.sub")}</p>

      <div className="panel mt-10 w-full p-5 sm:p-6">
        <ol className="space-y-4">
          {Array.from({ length: STEP_COUNT }).map((_, i) => {
            const done = step > i;
            const active = step === i;
            return (
              <li key={i} className="flex items-center gap-3">
                <span
                  className={cn(
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border font-mono text-[10px]",
                    done
                      ? "border-sig-neutral/60 bg-sig-neutral/15 text-sig-neutral"
                      : active
                        ? "border-sig-cyan/60 bg-sig-cyan/10 text-sig-cyan"
                        : "border-hairline text-muted-foreground",
                  )}
                >
                  {done ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : active ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </span>
                <span
                  className={cn(
                    "font-mono text-xs uppercase tracking-[0.14em]",
                    done ? "text-sig-neutral" : active ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  {t(`processing.step${i + 1}`)}
                </span>
                {active && (
                  <span className="ml-auto h-1.5 flex-1 max-w-[120px] overflow-hidden rounded bg-panel-2">
                    <span className="block h-full w-1/2 animate-shimmer bg-gradient-to-r from-transparent via-sig-cyan/70 to-transparent bg-[length:200%_100%]" />
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </div>

      <p className="mt-6 max-w-md text-center font-mono text-[10px] uppercase leading-relaxed tracking-[0.14em] text-muted-foreground">
        {t("processing.note")}
      </p>
    </div>
  );
}
