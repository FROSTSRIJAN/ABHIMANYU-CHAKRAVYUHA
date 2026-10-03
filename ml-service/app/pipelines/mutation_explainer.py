def explain_mutation(mutation: dict) -> str:
    source = mutation["source_claim"]["original_text"]
    target = mutation["target_claim"]["original_text"]
    types = ", ".join(mutation["mutation_types"])
    return (
        f"'{source}' changes to '{target}', indicating {types.lower()}. "
        "This describes observed wording changes and does not establish intent or falsity."
    )
