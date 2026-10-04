import { createRouter, publicQuery } from "./middleware";
import { analysisRouter } from "./analysis/router";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  analysis: analysisRouter,
});

export type AppRouter = typeof appRouter;
