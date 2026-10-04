import {
  mysqlTable,
  serial,
  varchar,
  json,
  int,
  timestamp,
} from "drizzle-orm/mysql-core";
import type { AnalysisResult, MessageInput, RiskLevel } from "@contracts/analysis";

export const analysisRuns = mysqlTable("analysis_runs", {
  id: serial("id").primaryKey(),
  messages: json("messages").$type<MessageInput[]>().notNull(),
  result: json("result").$type<AnalysisResult>().notNull(),
  overallLevel: varchar("overall_level", { length: 16 })
    .$type<RiskLevel>()
    .notNull(),
  overallScore: int("overall_score").notNull(),
  messageCount: int("message_count").notNull(),
  runtimeMs: int("runtime_ms").notNull().default(0),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export type AnalysisRunRow = typeof analysisRuns.$inferSelect;
