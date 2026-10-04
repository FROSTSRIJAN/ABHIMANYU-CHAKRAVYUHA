import { TriangleAlert } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { RadarLogo } from "@/components/RadarLogo";

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="border-t border-hairline bg-panel">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-2.5">
            <RadarLogo size={22} />
            <div>
              <div className="font-display text-sm font-bold">
                Echo<span className="text-sig-cyan">Trap</span>
              </div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {t("footer.note")}
              </div>
            </div>
          </div>
          <div className="flex max-w-xl items-start gap-2.5 rounded-md border border-sig-watch/25 bg-sig-watch/5 p-3">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-sig-watch" />
            <p className="text-xs leading-relaxed text-muted-foreground">{t("common.disclaimer")}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
