# Stage 4 benchmark dataset

The dataset is a manually authored, curated synthetic collection of original
and modified claims. It contains positive and negative examples for the Stage
3 mutation taxonomy, including currency, dates, negation, paraphrases,
multiple mutations, and a Spanish example.

It is not representative of production traffic and must not be presented as a
real-world accuracy study. Labels are manually authored ground truth for the
synthetic pairs, not generated predictions. The `language`, `split`, and
`category` fields support reproducible slicing.

The JSON schema is:

- `example_id`: unique stable identifier
- `original_claim`, `modified_claim`: input claim pair
- `expected_mutation_labels`: zero or more taxonomy labels
- `expected_mutation_present`: whether any mutation is expected
- `explanation`: short rationale
- `language`, `split`, `category`: dataset metadata

Run the benchmark from the repository root with:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m benchmarks.runner --output-dir "C:\ABHIMANYU CHAKRAVYUHA"
```
