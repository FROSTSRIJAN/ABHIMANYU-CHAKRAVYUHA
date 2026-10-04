import { z } from "zod";
import { desc, eq, sql } from "drizzle-orm";
import { createRouter, publicQuery } from "../middleware";
import { getDb } from "../queries/connection";
import { env } from "../lib/env";
import { analysisRuns } from "@db/schema";
import {
  MESSAGE_MAX,
  MESSAGE_MIN,
  MESSAGE_TEXT_MAX,
  MESSAGE_TEXT_MIN,
  type AnalysisResult,
  type DiagnosticsSummary,
  type MessageInput,
  type RiskLevel,
} from "@contracts/analysis";
import {
  ENGINE_MODEL,
  ENGINE_VERSION,
  FALLBACK_MODEL,
  LEXICON_SIZES,
  runAnalysis,
  SIMILARITY_METHOD,
} from "./engine";
import { runPythonAnalysis } from "./pythonClient";

const messageSchema = z.object({
  text: z.string().min(MESSAGE_TEXT_MIN).max(MESSAGE_TEXT_MAX),
  label: z.string().max(60).optional(),
});

type MemoryRun = {
  id: number;
  messages: MessageInput[];
  result: AnalysisResult;
  overallLevel: RiskLevel;
  overallScore: number;
  messageCount: number;
  runtimeMs: number;
  createdAt: Date;
};

const memoryRuns = new Map<number, MemoryRun>();
let nextMemoryId = 1;

function useMemoryStore(): boolean {
  return !env.databaseUrl && !env.isProduction;
}

function memoryDiagnostics(): DiagnosticsSummary {
  const runs = [...memoryRuns.values()];
  const dist = { neutral: 0, watch: 0, strong: 0 };
  for (const run of runs) dist[run.overallLevel] += 1;
  const recent = runs.slice(-25);
  const average = (values: number[]) =>
    values.length ? Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 100) / 100 : null;

  return {
    engine: {
      model: `${ENGINE_MODEL}@${ENGINE_VERSION}`,
      version: ENGINE_VERSION,
      similarityMethod: SIMILARITY_METHOD,
      fallbackModel: FALLBACK_MODEL,
      lexiconSizes: LEXICON_SIZES,
    },
    usage: {
      totalRuns: runs.length,
      lastRunAt: runs.at(-1)?.createdAt ?? null,
      avgOverallScore: average(runs.map((run) => run.overallScore)),
      levelDistribution: dist,
      avgSimilarity: average(recent.map((run) => run.result.diagnostics.avgSimilarity)),
      avgCertaintyShift: average(recent.map((run) => run.result.diagnostics.certaintyShift)),
      avgUrgencyShift: average(recent.map((run) => run.result.diagnostics.urgencyShift)),
    },
  };
}

export const analysisRouter = createRouter({
  run: publicQuery
    .input(
      z.object({
        messages: z.array(messageSchema).min(MESSAGE_MIN).max(MESSAGE_MAX),
      }),
    )
    .mutation(async ({ input }) => {
      const messages: MessageInput[] = input.messages.map((m) => ({
        text: m.text.trim(),
        label: m.label?.trim() || undefined,
      }));

      const createdAt = new Date();
      let draft;
      try {
        draft = await runPythonAnalysis(0, createdAt, messages);
      } catch (error) {
        console.warn("Python ML service unavailable; using local TypeScript fallback.", error);
        draft = runAnalysis(0, createdAt, messages);
      }
      if (useMemoryStore()) {
        const id = nextMemoryId++;
        const result = { ...draft, id, createdAt };
        memoryRuns.set(id, {
          id,
          messages,
          result,
          overallLevel: result.overallLevel,
          overallScore: result.overallScore,
          messageCount: messages.length,
          runtimeMs: result.diagnostics.runtimeMs,
          createdAt,
        });
        return { id };
      }

      const db = getDb();
      const inserted = await db.insert(analysisRuns).values({
        messages,
        result: draft,
        overallLevel: draft.overallLevel,
        overallScore: draft.overallScore,
        messageCount: messages.length,
        runtimeMs: draft.diagnostics.runtimeMs,
      });
      const id = Number(inserted[0].insertId);

      const result = { ...draft, id, createdAt };
      await db
        .update(analysisRuns)
        .set({ result })
        .where(eq(analysisRuns.id, id));

      return { id };
    }),

  get: publicQuery
    .input(z.object({ id: z.number().int().positive() }))
    .query(async ({ input }) => {
      if (useMemoryStore()) return memoryRuns.get(input.id)?.result ?? null;

      const db = getDb();
      const rows = await db
        .select()
        .from(analysisRuns)
        .where(eq(analysisRuns.id, input.id))
        .limit(1);
      const row = rows[0];
      if (!row) return null;
      return row.result;
    }),

  recent: publicQuery.query(async () => {
    if (useMemoryStore()) {
      return [...memoryRuns.values()]
        .sort((a, b) => b.id - a.id)
        .slice(0, 8)
        .map(({ id, overallLevel, overallScore, messageCount, createdAt }) => ({
          id,
          overallLevel,
          overallScore,
          messageCount,
          createdAt,
        }));
    }

    const db = getDb();
    const rows = await db
      .select({
        id: analysisRuns.id,
        overallLevel: analysisRuns.overallLevel,
        overallScore: analysisRuns.overallScore,
        messageCount: analysisRuns.messageCount,
        createdAt: analysisRuns.createdAt,
      })
      .from(analysisRuns)
      .orderBy(desc(analysisRuns.id))
      .limit(8);
    return rows;
  }),

  diagnostics: publicQuery.query(async (): Promise<DiagnosticsSummary> => {
    if (useMemoryStore()) return memoryDiagnostics();

    const db = getDb();
    const agg = await db
      .select({
        totalRuns: sql<number>`count(*)`,
        lastRunAt: sql<Date | null>`max(${analysisRuns.createdAt})`,
        avgOverallScore: sql<number | null>`avg(${analysisRuns.overallScore})`,
      })
      .from(analysisRuns);

    const levels = await db
      .select({
        level: analysisRuns.overallLevel,
        count: sql<number>`count(*)`,
      })
      .from(analysisRuns)
      .groupBy(analysisRuns.overallLevel);

    const dist = { neutral: 0, watch: 0, strong: 0 };
    for (const l of levels) dist[l.level] = Number(l.count);

    // Averages of engine metrics across recent runs (from stored results).
    const recentRows = await db
      .select({ result: analysisRuns.result })
      .from(analysisRuns)
      .orderBy(desc(analysisRuns.id))
      .limit(25);

    let avgSimilarity: number | null = null;
    let avgCertaintyShift: number | null = null;
    let avgUrgencyShift: number | null = null;
    if (recentRows.length > 0) {
      const n = recentRows.length;
      avgSimilarity =
        Math.round((recentRows.reduce((a, r) => a + r.result.diagnostics.avgSimilarity, 0) / n) * 100) / 100;
      avgCertaintyShift =
        Math.round((recentRows.reduce((a, r) => a + r.result.diagnostics.certaintyShift, 0) / n) * 100) / 100;
      avgUrgencyShift =
        Math.round((recentRows.reduce((a, r) => a + r.result.diagnostics.urgencyShift, 0) / n) * 100) / 100;
    }

    const a = agg[0];
    return {
      engine: {
        model: `${ENGINE_MODEL}@${ENGINE_VERSION}`,
        version: ENGINE_VERSION,
        similarityMethod: SIMILARITY_METHOD,
        fallbackModel: FALLBACK_MODEL,
        lexiconSizes: LEXICON_SIZES,
      },
      usage: {
        totalRuns: Number(a?.totalRuns ?? 0),
        lastRunAt: a?.lastRunAt ?? null,
        avgOverallScore: a?.avgOverallScore != null ? Math.round(Number(a.avgOverallScore)) : null,
        levelDistribution: dist,
        avgSimilarity,
        avgCertaintyShift,
        avgUrgencyShift,
      },
    };
  }),
});
