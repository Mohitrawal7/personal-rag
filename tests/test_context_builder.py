import unittest
from unittest.mock import patch

from app.retrieval.context_builder import build_context


class TestContextBuilder(unittest.TestCase):

    @patch("app.retrieval.context_builder.hybrid_search")
    def test_builds_context_with_source_metadata(self, mock_search):
        mock_search.return_value = [
            {
                "source_filename": "sample.pdf",
                "page_number": 2,
                "chunk_id": 0,
                "chunk_text": "RAG combines retrieval with generation.",
                "rrf_score": 0.03,
            }
        ]

        context, sources = build_context("What is RAG?")

        self.assertIn("sample.pdf", context)
        self.assertIn("page 2", context)
        self.assertIn("RAG combines retrieval with generation.", context)
        self.assertEqual(len(sources), 1)
        mock_search.assert_called_once_with("What is RAG?", top_k=5)

    @patch("app.retrieval.context_builder.hybrid_search")
    def test_handles_no_results(self, mock_search):
        mock_search.return_value = []

        context, sources = build_context("Unknown topic")

        self.assertIn("No relevant information", context)
        self.assertEqual(sources, [])


if __name__ == "__main__":
    unittest.main()
