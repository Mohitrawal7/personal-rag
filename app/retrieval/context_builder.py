from app.retrieval.hybrid_search import hybrid_search


def build_context(
    question: str,
    top_k: int = 5,
) -> tuple[str, list[dict]]:
    results = hybrid_search(question, top_k=top_k)

    if not results:
        return "No relevant information was found in the documents.", []

    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"[Source {index}: {result['source_filename']}, "
            f"page {result['page_number']}]\n"
            f"{result['chunk_text']}"
        )

    context = "\n\n".join(context_parts)
    return context, results
