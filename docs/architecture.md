# Architecture

The MVP is a modular FastAPI service in `ml-service/`. Its pipeline is:

`validation -> normalization/language detection -> claim extraction -> semantic comparison -> mutation analysis -> local evidence retrieval -> verification -> explanation`

Each stage is a small Python component with a testable contract. Model-backed
embedding and NLI adapters are intentionally optional. When they are unavailable,
the service uses transparent lexical heuristics and returns limitations rather
than presenting heuristic scores as calibrated probabilities.

The service is decision support only. It does not provide personalized
investment recommendations, and persuasion indicators are not proof that a claim
is false or fraudulent.
