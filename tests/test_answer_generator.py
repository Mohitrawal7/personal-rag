import json
import unittest
from unittest.mock import Mock, patch

from app.generation.answer_generator import generate_answer


class TestAnswerGenerator(unittest.TestCase):

    @patch("app.generation.answer_generator.hybrid_search")
    def test_returns_message_when_no_chunks_found(self, mock_search):
        mock_search.return_value = []

        result = generate_answer("What is RAG?")

        self.assertIn("could not find", result["answer"])
        self.assertEqual(result["sources"], [])

    @patch("app.generation.answer_generator.urlopen")
    @patch("app.generation.answer_generator.hybrid_search")
    def test_generates_answer_with_sources(self, mock_search, mock_urlopen):
        mock_search.return_value = [
            {
                "source_filename": "sample.pdf",
                "page_number": 2,
                "chunk_id": 0,
                "chunk_text": "RAG combines retrieval with generation.",
                "rrf_score": 0.03,
            }
        ]

        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "response": "RAG combines retrieval with generation. "
                        "[Source: sample.pdf, page 2]"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = generate_answer("What is RAG?")

        self.assertIn("RAG combines retrieval with generation", result["answer"])
        self.assertEqual(
            result["sources"],
            [{"filename": "sample.pdf", "page_number": 2}],
        )
        mock_urlopen.assert_called_once()

    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            generate_answer("   ")


if __name__ == "__main__":
    unittest.main()
