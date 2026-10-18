
import unittest
from unittest.mock import MagicMock, patch

from app.storage.documents import is_document_complete

from app.storage.documents import delete_document, list_documents





class TestDocumentCompleteness(unittest.TestCase):

    def setUp(self):
        self.chunk = {
            "chunk_id": 0,
            "page_number": 1,
            "heading": None,
            "start_offset": 0,
            "end_offset": 12,
            "chunk_text": "Hello world!",
        }

    @patch("app.storage.documents.get_connection")
    def test_returns_true_for_matching_document(
        self, mock_get_connection
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = (1,)
        cursor.fetchall.return_value = [
            (0, 1, None, 0, 12, "Hello world!")
        ]

        result = is_document_complete(
            "hash123", [self.chunk], 1
        )

        self.assertTrue(result)
        self.assertEqual(cursor.execute.call_count, 2)

    @patch("app.storage.documents.get_connection")
    def test_returns_false_for_missing_document(
        self, mock_get_connection
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None

        self.assertFalse(
            is_document_complete("missing", [self.chunk], 1)
        )

    @patch("app.storage.documents.get_connection")
    def test_returns_false_for_incomplete_chunks(
        self, mock_get_connection
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = (1,)
        cursor.fetchall.return_value = []

        self.assertFalse(
            is_document_complete("hash123", [self.chunk], 1)
        )

    def test_returns_false_for_empty_expected_chunks(self):
        self.assertFalse(
            is_document_complete("hash123", [], 1)
        )


    @patch("app.storage.documents.get_connection")
    def test_returns_documents_with_chunk_counts(self, mock_get_connection):
        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.description = [
            ("document_id",),
            ("filename",),
            ("file_hash",),
            ("page_count",),
            ("created_at",),
            ("chunk_count",),
        ]
        cursor.fetchall.return_value = [
            ("hash123", "sample.pdf", "hash123", 3, None, 8),
        ]

        result = list_documents()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "sample.pdf")
        self.assertEqual(result[0]["page_count"], 3)
        self.assertEqual(result[0]["chunk_count"], 8)

    @patch("app.storage.documents.get_connection")
    def test_returns_empty_list_when_library_is_empty(
        self, mock_get_connection
    ):
        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.description = [
            ("document_id",),
            ("filename",),
            ("file_hash",),
            ("page_count",),
            ("created_at",),
            ("chunk_count",),
        ]
        cursor.fetchall.return_value = []

        self.assertEqual(list_documents(), [])


class TestDeleteDocument(unittest.TestCase):

    @patch("app.storage.documents.get_connection")
    def test_deletes_existing_document(self, mock_get_connection):
        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = ("hash123",)

        self.assertTrue(delete_document("hash123"))

        cursor.execute.assert_called_once()
        self.assertIn("DELETE FROM documents", cursor.execute.call_args[0][0])
        self.assertEqual(
            cursor.execute.call_args[0][1],
            ("hash123",),
        )

    @patch("app.storage.documents.get_connection")
    def test_returns_false_when_document_does_not_exist(
        self, mock_get_connection
    ):
        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = None

        self.assertFalse(delete_document("missing-hash"))

    def test_rejects_empty_document_id(self):
        with self.assertRaises(ValueError):
            delete_document("")


if __name__ == "__main__":
    unittest.main()
