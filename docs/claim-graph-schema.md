# Claim graph schema

`POST /analyze/graph` returns a deterministic JSON graph:

- `nodes`: normalized claims with message IDs, extracted metadata,
  verification status, evidence references, retrieval methods, contradiction
  indicators, and verification limitations.
- `edges`: directed sequential transformations with source/target IDs,
  relationship, mutation types, semantic similarity, detection method, and
  explanation.
- `mutation_summary`: counts for certainty, urgency, qualifier, numerical, and
  entity changes.
- `verification_limitations`: corpus/model limitations.
- `human_review_recommended`: true when mutations or uncertain/conflicting
  verification warrant review.

The directed sequence is an ordering representation only. It does not assert
that one message caused another.
