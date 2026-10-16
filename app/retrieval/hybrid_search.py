from app.retrieval.keyword_search import search_keyword_chunks
from app.retrieval.vector_search import search_similar_chunks


def reciprocal_rank_fusion(
    keyword_results: list[dict],
    vector_results: list[dict],
    rrf_k: int = 60,
) -> list[dict]:
    if rrf_k <= 0:
        raise ValueError("rrf_k must be greater than zero.")

    fused = {}

    for method, results in (
        ("keyword", keyword_results),
        ("vector", vector_results),
    ):
        for rank, result in enumerate(results, start=1):
            key = (
                result["source_filename"],
                result["page_number"],
                result["chunk_id"],
            )

            if key not in fused:
                fused[key] = {
                    **result,
                    "keyword_rank": None,
                    "vector_rank": None,
                    "keyword_score": None,
                    "similarity": None,
                    "rrf_score": 0.0,
                }

            item = fused[key]
            item["rrf_score"] += 1.0 / (rrf_k + rank)
            item[f"{method}_rank"] = rank

            if method == "keyword":
                item["keyword_score"] = result.get("rank")
            else:
                item["similarity"] = result.get("similarity")
                item["chunk_text"] = result["chunk_text"]

    return sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )


def hybrid_search(
    question: str,
    top_k: int = 5,
    candidate_k: int = 10,
) -> list[dict]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    if top_k <= 0 or candidate_k <= 0:
        raise ValueError("top_k and candidate_k must be greater than zero.")

    keyword_results = search_keyword_chunks(question, top_k=candidate_k)
    vector_results = search_similar_chunks(question, top_k=candidate_k)

    return reciprocal_rank_fusion(keyword_results, vector_results)[:top_k]
