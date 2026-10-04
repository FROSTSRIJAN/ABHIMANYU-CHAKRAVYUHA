import { useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { Plus, X, Play, ClipboardPaste, CircleCheck, CircleAlert } from "lucide-react";
import { trpc } from "@/providers/trpc";
import { useI18n } from "@/lib/i18n";
import { MESSAGE_MAX, MESSAGE_MIN, MESSAGE_TEXT_MIN, type MessageInput } from "@contracts/analysis";
import { cn } from "@/lib/utils";

const SAMPLE: MessageInput[] = [
  {
    label: "Original post",
    text: "Our community is researching $NOVA. It is reportedly testing a new lending protocol. Might be worth watching.",
  },
  {
    label: "Group repost",
    text: "$NOVA is testing a new lending protocol. Early members saw 40% gains last quarter, sources say.",
  },
  {
    label: "Influencer thread",
    text: "CONFIRMED: $NOVA lending protocol launches this month. 40% gains — some say 80%. Spots in the presale are limited!",
  },
  {
    label: "Direct message",
    text: "LAST CHANCE: guaranteed 80% returns on the $NOVA presale. Send your deposit NOW — only 3 spots left. Don't miss out!!",
  },
];

interface Card {
  label: string;
  text: string;
}

export default function Analyzer() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [cards, setCards] = useState<Card[]>([
    { label: "", text: "" },
    { label: "", text: "" },
  ]);
  const [error, setError] = useState<string | null>(null);

  const runMutation = trpc.analysis.run.useMutation({
    onSuccess: ({ id }) => navigate("/processing", { state: { id } }),
    onError: () => setError(t("analyzer.error")),
  });

  const checks = useMemo(() => {
    const countOk = cards.length >= MESSAGE_MIN && cards.length <= MESSAGE_MAX;
    const lengthsOk = cards.every((c) => c.text.trim().length >= MESSAGE_TEXT_MIN);
    return { countOk, lengthsOk, valid: countOk && lengthsOk };
  }, [cards]);

  const update = (i: number, patch: Partial<Card>) =>
    setCards((prev) => prev.map((c, idx) => (idx === i ? { ...c, ...patch } : c)));

  const addCard = () => cards.length < MESSAGE_MAX && setCards((p) => [...p, { label: "", text: "" }]);
  const removeCard = (i: number) =>
    cards.length > MESSAGE_MIN && setCards((p) => p.filter((_, idx) => idx !== i));

  const submit = () => {
    if (!checks.valid || runMutation.isPending) return;
    setError(null);
    runMutation.mutate({
      messages: cards.map((c) => ({ text: c.text, label: c.label || undefined })),
    });
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <p className="micro-label flex items-center gap-2">
        <span className="led bg-sig-cyan text-sig-cyan" />
        {t("nav.brandTag")}
      </p>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">
        {t("analyzer.title")}
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
        {t("analyzer.sub")}
      </p>

      <div className="mt-8 space-y-4">
        {cards.map((card, i) => (
          <div key={i} className="panel p-4 sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-[11px] font-bold uppercase tracking-[0.2em] text-sig-cyan">
                {t("common.message")} {i + 1}
              </span>
              {cards.length > MESSAGE_MIN && (
                <button
                  onClick={() => removeCard(i)}
                  className="flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-md border border-hairline px-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground transition-colors hover:border-sig-strong/50 hover:text-sig-strong"
                >
                  <X className="h-3.5 w-3.5" /> {t("analyzer.remove")}
                </button>
              )}
            </div>
            <input
              value={card.label}
              onChange={(e) => update(i, { label: e.target.value })}
              placeholder={t("analyzer.cardPlaceholder")}
              aria-label={`${t("analyzer.cardLabel")} ${i + 1}`}
              className="mt-3 h-11 w-full rounded-md border border-hairline bg-panel-2 px-3 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-sig-cyan/60 focus:outline-none"
            />
            <textarea
              value={card.text}
              onChange={(e) => update(i, { text: e.target.value })}
              placeholder={t("analyzer.textPlaceholder")}
              rows={4}
              aria-label={`${t("common.message")} ${i + 1}`}
              className="mt-3 w-full resize-y rounded-md border border-hairline bg-panel-2 px-3 py-2.5 font-mono text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/60 focus:border-sig-cyan/60 focus:outline-none"
            />
            <div className="mt-1.5 text-right font-mono text-[10px] text-muted-foreground">
              {card.text.trim().length}/2000
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        {cards.length < MESSAGE_MAX && (
          <button
            onClick={addCard}
            className="inline-flex min-h-[44px] items-center gap-2 rounded-md border border-dashed border-hairline px-4 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-colors hover:border-sig-cyan/60 hover:text-sig-cyan"
          >
            <Plus className="h-4 w-4" /> {t("analyzer.add")} ({cards.length}/{MESSAGE_MAX})
          </button>
        )}
        <button
          onClick={() => setCards(SAMPLE.map((s) => ({ label: s.label ?? "", text: s.text })))}
          className="inline-flex min-h-[44px] items-center gap-2 rounded-md border border-hairline bg-panel px-4 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground"
        >
          <ClipboardPaste className="h-4 w-4" /> {t("analyzer.loadSample")}
        </button>
      </div>

      {/* Validation summary + run */}
      <div className="panel-2 mt-8 p-5">
        <p className="micro-label">{t("analyzer.validation")}</p>
        <ul className="mt-3 space-y-1.5">
          {[
            { ok: checks.countOk, label: `${t("analyzer.valMin")} · ${t("analyzer.valMax")}` },
            { ok: checks.lengthsOk, label: t("analyzer.valLen") },
          ].map((c, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              {c.ok ? (
                <CircleCheck className="h-4 w-4 text-sig-neutral" />
              ) : (
                <CircleAlert className="h-4 w-4 text-sig-watch" />
              )}
              <span className={c.ok ? "text-foreground/85" : "text-muted-foreground"}>{c.label}</span>
            </li>
          ))}
        </ul>
        {error && <p className="mt-3 text-sm text-sig-strong">{error}</p>}
        <button
          onClick={submit}
          disabled={!checks.valid || runMutation.isPending}
          className={cn(
            "mt-5 inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-md font-mono text-sm font-bold uppercase tracking-[0.14em] transition-all active:scale-[0.99] sm:w-auto sm:px-10",
            checks.valid && !runMutation.isPending
              ? "glow-cyan bg-sig-cyan text-[#050810]"
              : "cursor-not-allowed bg-panel text-muted-foreground",
          )}
        >
          <Play className="h-4 w-4" />
          {runMutation.isPending ? t("analyzer.running") : t("analyzer.run")}
        </button>
      </div>
    </div>
  );
}
