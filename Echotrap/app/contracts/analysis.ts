/**
 * EchoTrap — normalized analysis contract.
 * Single source of truth shared by the backend engine and the frontend.
 * Everything the Results / Diagnostics pages render comes from this shape.
 */

export type RiskLevel = "neutral" | "watch" | "strong";

export type MutationType =
  | "certainty_shift"
  | "urgency_shift"
  | "numeric_shift"
  | "scope_shift"
  | "entity_shift"
  | "omission"
  | "addition";

export interface MessageInput {
  /** Raw message text, 8–2000 chars */
  text: string;
  /** Optional label, e.g. "Initial post", "Follow-up DM" */
  label?: string;
}

export interface Mutation {
  /** 0-based transition index (between message[i] and message[i+1]) */
  transitionIndex: number;
  fromIndex: number;
  toIndex: number;
  type: MutationType;
  severity: RiskLevel;
  /** 0..1 magnitude of this mutation */
  score: number;
  /** Short human-readable summary, e.g. "Certainty rises sharply" */
  summary: string;
  /** Longer explanation with the concrete evidence */
  detail: string;
}

export interface TimelinePoint {
  index: number;
  label: string;
  /** Jaccard-containment blend vs previous message; null for the first message */
  similarityToPrevious: number | null;
  /** 0..1 hedged(0) → absolute(1) */
  certainty: number;
  /** 0..1 calm(0) → urgent(1) */
  urgency: number;
  /** First ~90 chars of the message */
  excerpt: string;
}

export interface SignalCard {
  key: "certainty" | "urgency" | "similarity" | "mutation_density";
  level: RiskLevel;
  /** Display value, e.g. "+0.42" or "0.31" */
  value: string;
  /** One-line interpretation */
  note: string;
}

export interface EngineDiagnostics {
  model: string;
  similarityMethod: string;
  fallbackUsed: boolean;
  fallbackNote: string;
  /** certainty(last) - certainty(first) */
  certaintyShift: number;
  /** urgency(last) - urgency(first) */
  urgencyShift: number;
  avgSimilarity: number;
  perTransitionSimilarity: number[];
  runtimeMs: number;
}

export interface AnalysisResult {
  id: number;
  createdAt: Date;
  messageCount: number;
  overallLevel: RiskLevel;
  /** 0..100 composite language-risk score */
  overallScore: number;
  headline: string;
  mutations: Mutation[];
  timeline: TimelinePoint[];
  signals: SignalCard[];
  plainExplanation: string;
  safetyNextSteps: string[];
  diagnostics: EngineDiagnostics;
}

export interface DiagnosticsSummary {
  engine: {
    model: string;
    version: string;
    similarityMethod: string;
    fallbackModel: string;
    lexiconSizes: {
      hedge: number;
      certainty: number;
      urgency: number;
    };
  };
  usage: {
    totalRuns: number;
    lastRunAt: Date | null;
    avgOverallScore: number | null;
    levelDistribution: { neutral: number; watch: number; strong: number };
    avgSimilarity: number | null;
    avgCertaintyShift: number | null;
    avgUrgencyShift: number | null;
  };
}

export const MESSAGE_MIN = 2;
export const MESSAGE_MAX = 5;
export const MESSAGE_TEXT_MIN = 8;
export const MESSAGE_TEXT_MAX = 2000;

export const RISK_LEVELS: RiskLevel[] = ["neutral", "watch", "strong"];
