import type {
  AnalysisResult,
  EngineDiagnostics,
  MessageInput,
  Mutation,
  RiskLevel,
  SignalCard,
  TimelinePoint,
} from "@contracts/analysis";
import { env } from "../lib/env";

const DEFAULT_URL = "http://127.0.0.1:8000";

type SequencePair = {
  message_index: number;
  semantic_similarity: number;
  certainty_change: string;
  urgency_change: string;
  added_claims: string[];
  removed_qualifiers: string[];
  persuasion_indicators: string[];
  explanation: string[];
};

type SequenceResponse = {
  status: string;
  pairs: SequencePair[];
  limitations?: string[];
};

type FullAnalysisResponse = {
  status: string;
  language: string;
  claims: string[];
  semantic_similarity: number | null;
  mutation_analysis: {
    certainty_escalation: boolean;
    urgency_escalation: boolean;
    investment_persuasion: boolean;
    added_claims: string[];
    removed_qualifiers: string[];
    explanation: string[];
    certainty_change: string;
    urgency_change: string;
    persuasion_indicators: string[];
    limitations: string[];
    confidence_type: string;
    comparison_status: string;
  };
  verification: {
    label: string;
    limitations: string[];
  };
  uncertainty: {
    level: string;
    reason: string;
  };
  explanation?: {
    summary?: string;
    limitations?: string[];
  };
};

function serviceUrl(): string {
  return env.mlServiceUrl || DEFAULT_URL;
}

async function post<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await fetch(`${serviceUrl()}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail || `ML service returned HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

function level(score: number): RiskLevel {
  return score >= 0.62 ? "strong" : score >= 0.3 ? "watch" : "neutral";
}

function number(value: number | null | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function explainPair(pair: SequencePair): string {
  return Array.isArray(pair.explanation) ? pair.explanation.join(" ") : String(pair.explanation || "No explanation provided.");
}

export async function runPythonAnalysis(
  id: number,
  createdAt: Date,
  messages: MessageInput[],
): Promise<AnalysisResult> {
  const payload = { messages: messages.map(({ text }) => text) };
  const [sequence, full] = await Promise.all([
    post<SequenceResponse>("/analyze/sequence", payload),
    post<FullAnalysisResponse>("/analyze", payload),
  ]);

  const pairs = sequence.pairs ?? [];
  const similarities = pairs.map((pair) => number(pair.semantic_similarity));
  const avgSimilarity = similarities.length
    ? Math.round((similarities.reduce((sum, value) => sum + value, 0) / similarities.length) * 100) / 100
    : 1;
  const certaintyShift = pairs.some((pair) => pair.certainty_change === "INCREASED") ? 0.4 : 0;
  const urgencyShift = pairs.some((pair) => pair.urgency_change === "INCREASED") ? 0.4 : 0;

  const mutations: Mutation[] = pairs.flatMap((pair) => {
    const transitionIndex = pair.message_index - 1;
    const items: Mutation[] = [];
    const add = (type: Mutation["type"], score: number, summary: string, detail: string) => {
      items.push({
        transitionIndex,
        fromIndex: transitionIndex,
        toIndex: pair.message_index,
        type,
        severity: level(score),
        score: Math.round(Math.min(1, score) * 100) / 100,
        summary,
        detail,
      });
    };

    if (pair.certainty_change === "INCREASED") {
      add("certainty_shift", 0.75, "Certainty increases", explainPair(pair));
    }
    if (pair.urgency_change === "INCREASED") {
      add("urgency_shift", 0.8, "Urgency increases", explainPair(pair));
    }
    if (pair.added_claims.length > 0) {
      add("addition", 0.55, "New claims are added", `Added claims: ${pair.added_claims.join("; ")}`);
    }
    if (pair.removed_qualifiers.length > 0) {
      add("omission", 0.5, "Qualifying language is removed", `Removed qualifiers: ${pair.removed_qualifiers.join(", ")}`);
    }
    if (items.length === 0 && pair.explanation.length > 0) {
      add("scope_shift", 0.25, "The message wording shifts", explainPair(pair));
    }
    return items;
  });

  const score = Math.min(
    100,
    Math.round(
      (1 - avgSimilarity) * 35 +
        (certaintyShift > 0 ? 25 : 0) +
        (urgencyShift > 0 ? 25 : 0) +
        Math.min(1, mutations.length / Math.max(1, messages.length - 1)) * 15,
    ),
  );
  const overallLevel = score >= 55 ? "strong" : score >= 25 ? "watch" : "neutral";
  const headline =
    overallLevel === "strong"
      ? "Strong language-risk signals detected in this sequence"
      : overallLevel === "watch"
        ? "Some wording shifts are worth a closer look"
        : "No significant claim mutation detected";

  const timeline: TimelinePoint[] = messages.map((message, index) => {
    const pair = pairs[index - 1];
    return {
      index,
      label: message.label || `Message ${index + 1}`,
      similarityToPrevious: index === 0 ? null : number(pair?.semantic_similarity),
      certainty: index === messages.length - 1 && certaintyShift > 0 ? 0.9 : index > 0 ? 0.65 : 0.35,
      urgency: index === messages.length - 1 && urgencyShift > 0 ? 0.9 : 0.1,
      excerpt: message.text.slice(0, 90) + (message.text.length > 90 ? "…" : ""),
    };
  });

  const signals: SignalCard[] = [
    {
      key: "certainty",
      level: level(certaintyShift),
      value: certaintyShift ? "+0.40" : "0.00",
      note: full.mutation_analysis.explanation[0] || "No certainty escalation detected.",
    },
    {
      key: "urgency",
      level: level(urgencyShift),
      value: urgencyShift ? "+0.40" : "0.00",
      note: full.mutation_analysis.urgency_escalation ? "Urgency language appears later in the sequence." : "No urgency escalation detected.",
    },
    {
      key: "similarity",
      level: level((1 - avgSimilarity) * 1.15),
      value: avgSimilarity.toFixed(2),
      note: "Pairwise similarity returned by the Python analysis service.",
    },
    {
      key: "mutation_density",
      level: level(mutations.length / Math.max(1, pairs.length)),
      value: String(mutations.length),
      note: `${mutations.length} language mutation signal${mutations.length === 1 ? "" : "s"} detected.`,
    },
  ];

  const diagnostics: EngineDiagnostics = {
    model: "python-ml-service",
    similarityMethod: "FastAPI /analyze/sequence",
    fallbackUsed: full.mutation_analysis.confidence_type === "heuristic",
    fallbackNote: [...(sequence.limitations || []), ...(full.mutation_analysis.limitations || []), ...(full.verification.limitations || [])].join(" "),
    certaintyShift,
    urgencyShift,
    avgSimilarity,
    perTransitionSimilarity: similarities,
    runtimeMs: 0,
  };

  return {
    id,
    createdAt,
    messageCount: messages.length,
    overallLevel,
    overallScore: score,
    headline,
    mutations,
    timeline,
    signals,
    plainExplanation:
      full.explanation?.summary ||
      `${full.mutation_analysis.explanation.join(" ")} Verification status: ${full.verification.label}. ${full.uncertainty.reason}`,
    safetyNextSteps: [
      "Find the earliest source of the claim before acting on later versions.",
      "Verify numbers, returns, deadlines, and guarantees independently.",
      "Treat urgency as a reason to pause, not a reason to hurry.",
    ],
    diagnostics,
  };
}
