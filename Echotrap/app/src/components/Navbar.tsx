import { useState } from "react";
import { Link, NavLink, useLocation } from "react-router";
import { Menu, X } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { RadarLogo } from "@/components/RadarLogo";
import { cn } from "@/lib/utils";

const LINKS = [
  { to: "/", key: "nav.home" },
  { to: "/analyze", key: "nav.analyzer" },
  { to: "/results", key: "nav.results" },
  { to: "/safety", key: "nav.safety" },
  { to: "/diagnostics", key: "nav.diagnostics" },
  { to: "/docs", key: "nav.docs" },
] as const;

function LangToggle({ className }: { className?: string }) {
  const { lang, setLang } = useI18n();
  return (
    <div
      className={cn(
        "flex items-center rounded-md border border-hairline bg-panel-2 p-0.5 font-mono text-[11px] font-semibold",
        className,
      )}
      role="group"
      aria-label="Language"
    >
      {(["en", "hi"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          className={cn(
            "min-h-[32px] min-w-[44px] rounded px-2 tracking-wide transition-colors",
            lang === l ? "bg-sig-cyan text-[#050810]" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {l === "en" ? "EN" : "हिं"}
        </button>
      ))}
    </div>
  );
}

export function Navbar() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-[#050810]/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link to="/" className="flex min-w-0 items-center gap-2.5" onClick={() => setOpen(false)}>
          <RadarLogo />
          <span className="flex min-w-0 flex-col leading-none">
            <span className="font-display text-lg font-bold tracking-tight text-foreground">
              Echo<span className="text-sig-cyan">Trap</span>
            </span>
            <span className="mt-0.5 hidden truncate font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground sm:block">
              {t("nav.brandTag")}
            </span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-panel-2 text-sig-cyan"
                    : "text-muted-foreground hover:bg-panel hover:text-foreground",
                )
              }
            >
              {t(l.key)}
            </NavLink>
          ))}
          <div className="ml-2">
            <LangToggle />
          </div>
        </nav>

        {/* Mobile controls */}
        <div className="flex items-center gap-2 lg:hidden">
          <LangToggle />
          <button
            className="flex h-11 w-11 items-center justify-center rounded-md border border-hairline bg-panel-2 text-foreground"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? t("nav.close") : t("nav.menu")}
            aria-expanded={open}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {open && (
        <nav className="border-t border-hairline bg-[#050810] px-4 pb-4 pt-2 lg:hidden">
          {LINKS.map((l) => {
            const active =
              l.to === "/" ? location.pathname === "/" : location.pathname.startsWith(l.to);
            return (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex min-h-[48px] items-center border-b border-hairline/50 px-1 text-[15px] font-medium last:border-0",
                  active ? "text-sig-cyan" : "text-foreground/80",
                )}
              >
                {t(l.key)}
              </NavLink>
            );
          })}
        </nav>
      )}
    </header>
  );
}
