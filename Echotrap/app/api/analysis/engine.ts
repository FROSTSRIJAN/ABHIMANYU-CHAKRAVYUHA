/**
 * EchoTrap claim-mutation engine (server-side).
 *
 * Rule-based lexical pipeline ("lex-heur v1"). For each ordered pair of
 * consecutive messages it measures:
 *   - semantic similarity (Jaccard / containment blend over content tokens)
 *   - certainty shift (hedge lexicon vs absolute-claim lexicon)
 *   - urgency shift (pressure lexicon + punctuation/casing signals)
 *   - numeric drift (extracted numbers/percentages)
 *   - entity drift (capitalized tokens / $TICKERS / @handles)
 * and classifies the dominant mutation per transition.
 *
 * Deliberately conservative: output is framed as *language-risk* signals,
 * never as proof of fraud.
 */
import type {
  AnalysisResult,
  EngineDiagnostics,
  MessageInput,
  Mutation,
  MutationType,
  RiskLevel,
  SignalCard,
  TimelinePoint,
} from "@contracts/analysis";

export const ENGINE_MODEL = "echotrap-lexheur";
export const ENGINE_VERSION = "1.0.0";
export const SIMILARITY_METHOD = "token jaccard/containment blend (0.6/0.4)";
export const FALLBACK_MODEL = "char-3gram cosine fallback";

/* ------------------------------------------------------------------ */
/* Lexicons                                                            */
/* ------------------------------------------------------------------ */

const HEDGE_TERMS = [
  "might", "may", "could", "perhaps", "possibly", "probably", "allegedly",
  "reportedly", "rumor", "rumoured", "rumored", "suggests", "suggesting",
  "appears", "seems", "unlikely", "unclear", "unconfirmed", "speculation",
  "speculative", "i think", "not sure", "believe", "potentially", "maybe",
  "expected", "estimate", "roughly", "around", "about", "some", "few",
];

const CERTAINTY_TERMS = [
  "will", "guaranteed", "guarantee", "confirmed", "definitely", "certainly",
  "certain", "assured", "promise", "promises", "promised", "locked",
  "locked in", "sure thing", "no risk", "risk-free", "risk free", "always",
  "never fails", "cannot lose", "can't lose", "must", "fact", "proven",
  "insider", "official", "announced", "done deal", "100%", "surely",
  "undoubtedly", "without doubt",
];

const URGENCY_TERMS = [
  "now", "immediately", "urgent", "urgently", "hurry", "quick", "quickly",
  "fast", "act fast", "today", "tonight", "deadline", "expires", "expiring",
  "limited", "limited time", "last chance", "final call", "don't miss",
  "do not miss", "miss out", "fomo", "before it's too late", "before it is too late",
  "once in a lifetime", "asap", "right away", "instantly", "spot", "spots left",
  "closing", "countdown", "hours left", "minutes left", "ending soon",
  "buy now", "deposit now", "send now", "wire", "dm me", "inbox me",
];

const STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "at",
  "by", "for", "with", "about", "against", "between", "into", "through",
  "during", "before", "after", "above", "below", "to", "from", "up", "down",
  "in", "out", "on", "off", "over", "under", "again", "further", "once",
  "here", "there", "all", "any", "both", "each", "more", "most", "other",
  "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
  "too", "very", "can", "just", "is", "are", "was", "were", "be", "been",
  "being", "have", "has", "had", "having", "do", "does", "did", "doing",
  "of", "it", "its", "this", "that", "these", "those", "i", "you", "he",
  "she", "we", "they", "them", "his", "her", "their", "our", "your", "my",
  "as", "us", "me", "him", "what", "which", "who", "whom", "how", "why",
]);

/* ------------------------------------------------------------------ */
/* Token / signal extraction                                           */
/* ------------------------------------------------------------------ */

interface MessageSignals {
  tokens: Set<string>;
  certainty: number;
  urgency: number;
  hedgeHits: string[];
  certaintyHits: string[];
  urgencyHits: string[];
  numbers: string[];
  entities: string[];
  capsWords: number;
  exclamations: number;
  fallbackSimilarity: boolean;
  charGrams: Map<string, number>;
}

function tokenize(text: string): Set<string> {
  const words = text
    .toLowerCase()
    .replace(/[$@#]/g, " ")
    .replace(/[^a-z0-9%.\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w) && !/^\d/.test(w));
  return new Set(words);
}

function charGrams(text: string, n = 3): Map<string, number> {
  const clean = text.toLowerCase().replace(/\s+/g, " ");
  const map = new Map<string, number>();
  for (let i = 0; i + n <= clean.length; i++) {
    const g = clean.slice(i, i + n);
    map.set(g, (map.get(g) ?? 0) + 1);
  }
  return map;
}

function countLexiconHits(lower: string, terms: string[]): string[] {
  const hits: string[] = [];
  for (const term of terms) {
    const re = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (re.test(lower)) hits.push(term);
  }
  return hits;
}

function extractNumbers(text: string): string[] {
  const matches = text.match(/\$?\d[\d,]*(?:\.\d+)?\s?%?/g) ?? [];
  return matches.map((m) => m.replace(/,/g, "").trim());
}

function extractEntities(text: string): string[] {
  const out = new Set<string>();
  for (const m of text.matchAll(/\$[A-Z]{1,6}\b/g)) out.add(m[0].toUpperCase());
  for (const m of text.matchAll(/@[A-Za-z0-9_]{2,}/g)) out.add(m[0].toLowerCase());
  for (const m of text.matchAll(/\b[A-Z][A-Z]{1,6}\b/g)) {
    if (!["I", "A", "AM", "PM", "DM", "OK"].includes(m[0])) out.add(m[0].toUpperCase());
  }
  // Capitalized words not at sentence start (rough proper-noun pass)
  for (const m of text.matchAll(/(?<=[a-z]\s)[A-Z][a-z]{2,}/g)) out.add(m[0]);
  return [...out];
}

function scoreAxis(hedgeHits: number, certaintyHits: number): number {
  // certainty axis: 0 = fully hedged, 0.5 = no signal, 1 = fully absolute
  if (hedgeHits === 0 && certaintyHits === 0) return 0.5;
  const raw = certaintyHits / (certaintyHits + hedgeHits);
  return Math.round(raw * 100) / 100;
}

function analyzeMessage(text: string): MessageSignals {
  const lower = text.toLowerCase();
  const hedgeHits = countLexiconHits(lower, HEDGE_TERMS);
  const certaintyHits = countLexiconHits(lower, CERTAINTY_TERMS);
  const urgencyHits = countLexiconHits(lower, URGENCY_TERMS);
  const capsWords = (text.match(/\b[A-Z]{3,}\b/g) ?? []).length;
  const exclamations = (text.match(/!/g) ?? []).length;
  const tokens = tokenize(text);

  const lexicalUrgency = Math.min(1, urgencyHits.length / 3);
  const punctUrgency = Math.min(1, (exclamations * 0.18 + capsWords * 0.12));
  const urgency = Math.round(Math.min(1, lexicalUrgency * 0.75 + punctUrgency * 0.35) * 100) / 100;

  return {
    tokens,
    certainty: scoreAxis(hedgeHits.length, certaintyHits.length),
    urgency,
    hedgeHits,
    certaintyHits,
    urgencyHits,
    numbers: extractNumbers(text),
    entities: extractEntities(text),
    capsWords,
    exclamations,
    fallbackSimilarity: tokens.size < 4,
    charGrams: charGrams(text),
  };
}

/* ------------------------------------------------------------------ */
/* Similarity                                                          */
/* ------------------------------------------------------------------ */

function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 1;
  let inter = 0;
  for (const t of a) if (b.has(t)) inter++;
  return inter / (a.size + b.size - inter || 1);
}

function containment(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let inter = 0;
  for (const t of a) if (b.has(t)) inter++;
  return inter / Math.min(a.size, b.size);
}

function gramCosine(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (const [, v] of a) na += v * v;
  for (const [k, v] of b) {
    nb += v * v;
    const av = a.get(k);
    if (av) dot += av * v;
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

function similarity(a: MessageSignals, b: MessageSignals): { value: number; fallback: boolean } {
  const fallback = a.fallbackSimilarity || b.fallbackSimilarity;
  if (fallback) {
    return { value: Math.round(gramCosine(a.charGrams, b.charGrams) * 100) / 100, fallback: true };
  }
  const blend = 0.6 * jaccard(a.tokens, b.tokens) + 0.4 * containment(a.tokens, b.tokens);
  return { value: Math.round(blend * 100) / 100, fallback: false };
}

/* ------------------------------------------------------------------ */
/* Mutation classification                                             */
/* ------------------------------------------------------------------ */

function clamp01(v: number): number {
  return Math.min(1, Math.max(0, v));
}

function levelFromScore(score: number): RiskLevel {
  if (score >= 0.62) return "strong";
  if (score >= 0.3) return "watch";
  return "neutral";
}

interface TransitionReport {
  similarity: number;
  fallback: boolean;
  deltaCertainty: number;
  deltaUrgency: number;
  mutations: Mutation[];
}

function analyzeTransition(
  i: number,
  prev: MessageSignals,
  next: MessageSignals,
): TransitionReport {
  const sim = similarity(prev, next);
  const dCert = Math.round((next.certainty - prev.certainty) * 100) / 100;
  const dUrg = Math.round((next.urgency - prev.urgency) * 100) / 100;

  const prevNums = new Set(prev.numbers);
  const nextNums = new Set(next.numbers);
  const numsChanged =
    prev.numbers.length + next.numbers.length > 0 &&
    (prev.numbers.some((n) => !nextNums.has(n)) || next.numbers.some((n) => !prevNums.has(n)));

  const droppedEntities = prev.entities.filter((e) => !next.entities.includes(e));
  const addedEntities = next.entities.filter((e) => !prev.entities.includes(e));

  const mutations: Mutation[] = [];
  const push = (
    type: MutationType,
    score: number,
    summary: string,
    detail: string,
  ) => {
    mutations.push({
      transitionIndex: i,
      fromIndex: i,
      toIndex: i + 1,
      type,
      severity: levelFromScore(score),
      score: Math.round(clamp01(score) * 100) / 100,
      summary,
      detail,
    });
  };

  if (Math.abs(dCert) >= 0.2) {
    const dir = dCert > 0 ? "rises" : "drops";
    push(
      "certainty_shift",
      Math.abs(dCert),
      `Certainty ${dir} (${dCert > 0 ? "+" : ""}${dCert.toFixed(2)})`,
      dCert > 0
        ? `Hedges give way to absolute claims. New certainty markers: [${next.certaintyHits.slice(0, 4).join(", ") || "—"}]; hedges lost: [${prev.hedgeHits.filter((h) => !next.hedgeHits.includes(h)).slice(0, 4).join(", ") || "—"}].`
        : `Absolute claims soften into hedged language. New hedges: [${next.hedgeHits.slice(0, 4).join(", ") || "—"}].`,
    );
  }

  if (dUrg >= 0.18) {
    push(
      "urgency_shift",
      dUrg * 1.15,
      `Urgency rises (+${dUrg.toFixed(2)})`,
      `Pressure markers appear: [${next.urgencyHits.slice(0, 5).join(", ") || "—"}]${next.exclamations > prev.exclamations ? `; exclamation marks ${prev.exclamations} → ${next.exclamations}` : ""}${next.capsWords > prev.capsWords ? `; ALL-CAPS words ${prev.capsWords} → ${next.capsWords}` : ""}.`,
    );
  }

  if (numsChanged) {
    const removed = prev.numbers.filter((n) => !nextNums.has(n));
    const added = next.numbers.filter((n) => !prevNums.has(n));
    push(
      "numeric_shift",
      0.35 + 0.15 * Math.min(3, removed.length + added.length),
      "Figures change between versions",
      `Dropped figures: [${removed.join(", ") || "—"}]; introduced figures: [${added.join(", ") || "—"}]. Changing numbers across retellings is a classic mutation signature.`,
    );
  }

  if (addedEntities.length > 0 || droppedEntities.length > 0) {
    push(
      "entity_shift",
      0.3 + 0.12 * Math.min(3, addedEntities.length + droppedEntities.length),
      "Named entities change",
      `New names/tickers: [${addedEntities.join(", ") || "—"}]; dropped: [${droppedEntities.join(", ") || "—"}].`,
    );
  }

  const cont = containment(prev.tokens, next.tokens);
  if (cont >= 0.75 && next.tokens.size > prev.tokens.size + 3 && sim.value < 0.85) {
    push(
      "addition",
      0.3 + (1 - sim.value) * 0.5,
      "New claims added on top of the original",
      "The later message keeps the original content but layers additional claims on top — the story grows as it travels.",
    );
  } else if (cont < 0.45 && sim.value < 0.5) {
    push(
      "omission",
      0.45 + (0.5 - sim.value) * 0.6,
      "Original claims dropped or rewritten",
      "Much of the earlier content disappears in the later version — key context may have been quietly removed.",
    );
  } else if (sim.value < 0.55) {
    push(
      "scope_shift",
      0.35 + (0.55 - sim.value) * 0.6,
      "Topic scope drifts",
      `Token overlap with the previous message is only ${(sim.value * 100).toFixed(0)}% — the claim is drifting away from its original form.`,
    );
  }

  return { similarity: sim.value, fallback: sim.fallback, deltaCertainty: dCert, deltaUrgency: dUrg, mutations };
}

/* ------------------------------------------------------------------ */
/* Public entry point                                                  */
/* ------------------------------------------------------------------ */

export function runAnalysis(id: number, createdAt: Date, messages: MessageInput[]): AnalysisResult {
  const started = Date.now();
  const signals = messages.map((m) => analyzeMessage(m.text));

  const timeline: TimelinePoint[] = [];
  const allMutations: Mutation[] = [];
  const perTransitionSimilarity: number[] = [];
  let anyFallback = false;

  for (let i = 0; i < messages.length; i++) {
    let simPrev: number | null = null;
    if (i > 0) {
      const tr = analyzeTransition(i - 1, signals[i - 1], signals[i]);
      simPrev = tr.similarity;
      perTransitionSimilarity.push(tr.similarity);
      anyFallback = anyFallback || tr.fallback;
      allMutations.push(...tr.mutations);
    }
    timeline.push({
      index: i,
      label: messages[i].label?.trim() || `Message ${i + 1}`,
      similarityToPrevious: simPrev,
      certainty: signals[i].certainty,
      urgency: signals[i].urgency,
      excerpt: messages[i].text.slice(0, 90) + (messages[i].text.length > 90 ? "…" : ""),
    });
  }

  const avgSimilarity =
    perTransitionSimilarity.length > 0
      ? Math.round((perTransitionSimilarity.reduce((a, b) => a + b, 0) / perTransitionSimilarity.length) * 100) / 100
      : 1;

  const certaintyShift = Math.round((signals[signals.length - 1].certainty - signals[0].certainty) * 100) / 100;
  const urgencyShift = Math.round((signals[signals.length - 1].urgency - signals[0].urgency) * 100) / 100;

  const strongCount = allMutations.filter((m) => m.severity === "strong").length;
  const watchCount = allMutations.filter((m) => m.severity === "watch").length;
  const mutationDensity = allMutations.length / Math.max(1, messages.length - 1);

  const rawScore =
    (1 - avgSimilarity) * 34 +
    Math.max(0, certaintyShift) * 22 +
    Math.max(0, urgencyShift) * 20 +
    Math.min(1, mutationDensity / 2.5) * 14 +
    strongCount * 5 +
    watchCount * 2;
  const overallScore = Math.min(100, Math.round(rawScore));
  const overallLevel: RiskLevel = overallScore >= 55 ? "strong" : overallScore >= 25 ? "watch" : "neutral";

  const signalCards: SignalCard[] = [
    {
      key: "certainty",
      level: levelFromScore(Math.abs(certaintyShift) * 1.1),
      value: `${certaintyShift > 0 ? "+" : ""}${certaintyShift.toFixed(2)}`,
      note:
        certaintyShift > 0.2
          ? "Language hardens from hedged to absolute across the sequence."
          : certaintyShift < -0.2
            ? "Claims soften over the sequence — earlier confidence is walked back."
            : "Certainty stays broadly stable across the sequence.",
    },
    {
      key: "urgency",
      level: levelFromScore(Math.max(0, urgencyShift) * 1.4),
      value: `${urgencyShift > 0 ? "+" : ""}${urgencyShift.toFixed(2)}`,
      note:
        urgencyShift > 0.18
          ? "Pressure and deadline language escalates — a hallmark of manipulation patterns."
          : "No meaningful build-up of pressure language detected.",
    },
    {
      key: "similarity",
      level: levelFromScore((1 - avgSimilarity) * 1.15),
      value: avgSimilarity.toFixed(2),
      note:
        avgSimilarity < 0.4
          ? "Later versions share little wording with the original claim."
          : avgSimilarity < 0.7
            ? "Wording drifts noticeably between versions."
            : "Versions stay close to the original wording.",
    },
    {
      key: "mutation_density",
      level: levelFromScore(mutationDensity / 2.2),
      value: `${allMutations.length}`,
      note: `${allMutations.length} distinct mutation${allMutations.length === 1 ? "" : "s"} detected across ${messages.length - 1} transition${messages.length - 1 === 1 ? "" : "s"}.`,
    },
  ];

  const topMutations = [...allMutations].sort((a, b) => b.score - a.score).slice(0, 2);
  const plainExplanation = buildPlainExplanation(overallLevel, topMutations, certaintyShift, urgencyShift, avgSimilarity);

  const headline =
    overallLevel === "strong"
      ? "Strong language-risk signals detected in this sequence"
      : overallLevel === "watch"
        ? "Some wording shifts are worth a closer look"
        : "No significant claim mutation detected";

  const diagnostics: EngineDiagnostics = {
    model: `${ENGINE_MODEL}@${ENGINE_VERSION}`,
    similarityMethod: SIMILARITY_METHOD,
    fallbackUsed: anyFallback,
    fallbackNote: anyFallback
      ? `${FALLBACK_MODEL} engaged for ${signals.filter((s) => s.fallbackSimilarity).length} short/sparse message(s); treat similarity scores there as approximate.`
      : "Primary token pipeline covered all messages; fallback not engaged.",
    certaintyShift,
    urgencyShift,
    avgSimilarity,
    perTransitionSimilarity,
    runtimeMs: Date.now() - started,
  };

  return {
    id,
    createdAt,
    messageCount: messages.length,
    overallLevel,
    overallScore,
    headline,
    mutations: [...allMutations].sort((a, b) => a.transitionIndex - b.transitionIndex || b.score - a.score),
    timeline,
    signals: signalCards,
    plainExplanation,
    safetyNextSteps: SAFETY_STEPS,
    diagnostics,
  };
}

function buildPlainExplanation(
  level: RiskLevel,
  top: Mutation[],
  dCert: number,
  dUrg: number,
  avgSim: number,
): string {
  const parts: string[] = [];
  if (level === "neutral") {
    parts.push(
      `The messages in this sequence stay fairly consistent (average wording overlap ${(avgSim * 100).toFixed(0)}%). EchoTrap did not find strong signs that the claim is mutating as it spreads.`,
    );
  } else {
    parts.push(
      `Across this sequence, the way the claim is expressed changes in ways that deserve attention (average wording overlap ${(avgSim * 100).toFixed(0)}%).`,
    );
  }
  if (dCert > 0.2) parts.push("The wording becomes more certain over time — early caution turns into confident promises.");
  if (dCert < -0.2) parts.push("The wording becomes less certain over time — confident early claims are later hedged.");
  if (dUrg > 0.18) parts.push("Pressure to act quickly increases from message to message.");
  for (const m of top) parts.push(`Strongest signal: ${m.summary.toLowerCase()} between message ${m.fromIndex + 1} and ${m.toIndex + 1}.`);
  parts.push(
    "Remember: this is a language-pattern analysis, not a verdict. Mutated wording is a reason to verify, not proof of fraud.",
  );
  return parts.join(" ");
}

const SAFETY_STEPS = [
  "Find the original source — search for the earliest version of the claim before acting on any later version.",
  "Verify numbers independently: prices, returns, deadlines and guarantees should match an official announcement or filing.",
  "Check who benefits: identify who posted each version and whether they profit from you acting quickly.",
  "Treat urgency as a red flag, not a reason to hurry. Legitimate opportunities rarely expire in hours.",
  "Never send money, credentials, or wallet keys based on a forwarded message alone.",
  "If the claim involves investments, cross-check the entity against your regulator's registration database.",
];

export const LEXICON_SIZES = {
  hedge: HEDGE_TERMS.length,
  certainty: CERTAINTY_TERMS.length,
  urgency: URGENCY_TERMS.length,
};
