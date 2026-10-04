import { Link } from "react-router";
import { useI18n } from "@/lib/i18n";
import { RadarLogo } from "@/components/RadarLogo";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-24 text-center">
      <RadarLogo size={64} />
      <h1 className="mt-8 font-display text-3xl font-bold tracking-tight">{t("notfound.title")}</h1>
      <p className="mt-3 text-sm text-muted-foreground">{t("notfound.body")}</p>
      <Link
        to="/"
        className="mt-8 inline-flex min-h-[48px] items-center rounded-md bg-sig-cyan px-6 font-mono text-xs font-bold uppercase tracking-[0.14em] text-[#050810]"
      >
        {t("notfound.cta")}
      </Link>
    </div>
  );
}
