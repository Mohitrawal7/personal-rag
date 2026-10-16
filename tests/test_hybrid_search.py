import unittest

from app.retrieval.hybrid_search import (
    hybrid_search,
    reciprocal_rank_fusion,
)


class TestReciprocalRankFusion(unittest.TestCase):

    def setUp(self):
        self.keyword_results = [
            {
                "source_filename": "sample.pdf",
                "page_number": 1,
                "chunk_id": 0,
                "chunk_text": "Information about Python.",
                "rank": 0.8,
            }
        ]

        self.vector_results = [
            {
                "source_filename": "sample.pdf",
                "page_number": 1,
                "chunk_id": 0,
                "chunk_text": "Information about Python.",
                "similarity": 0.9,
            }
        ]

    def test_combines_matching_results(self):
        results = reciprocal_rank_fusion(
            self.keyword_results,
            self.vector_results,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["keyword_rank"], 1)
        self.assertEqual(results[0]["vector_rank"], 1)
        self.assertIsNotNone(results[0]["keyword_score"])
        self.assertIsNotNone(results[0]["similarity"])

    def test_combined_result_has_rrf_score(self):
        results = reciprocal_rank_fusion(
            self.keyword_results,
            self.vector_results,
        )

        expected_score = (1 / 61) + (1 / 61)
        self.assertAlmostEqual(
            results[0]["rrf_score"],
            expected_score,
        )

    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            hybrid_search("   ")

    def test_rejects_invalid_top_k(self):
        with self.assertRaises(ValueError):
            hybrid_search("test question", top_k=0)


if __name__ == "__main__":
    unittest.main()
