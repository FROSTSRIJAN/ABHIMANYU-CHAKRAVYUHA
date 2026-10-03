# API contract

All endpoints return JSON and reject empty strings. Inputs larger than
`ABHIMANYU_MAX_INPUT_CHARS` return HTTP 413.

- `GET /health`: service liveness.
- `GET /models`: loaded and optional model adapters.
- `POST /compare`: `{ "first": "...", "second": "..." }`; returns relatedness,
  not truth probability.
- `POST /verify`: `{ "claim": "...", "evidence": [...] }`; returns a cautious
  evidence label.
- `POST /analyze`: `{ "messages": ["...", "..."], "evidence": [...] }`; returns
  language, extracted claims, semantic relatedness, mutation indicators,
  evidence, limitations, and uncertainty.
- `POST /analyze/sequence`: accepts two to twenty ordered messages and returns
  pairwise mutation observations. Similarity remains semantic relatedness, not
  factual confidence.
- `POST /analyze/graph`: accepts an ordered message list and optional evidence,
  returning normalized claim nodes, sequential mutation edges, verification
  annotations, and review flags.

Evidence records require `document_id`, `passage`, and `source_name`; URL and
publication date are optional and are never invented by the service.
