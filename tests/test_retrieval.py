import os
import unittest
from unittest.mock import patch

with patch.dict(os.environ, {"BAILIAN_API_KEY": "test-key"}):
    from src.index import tokenize, retrieve


class TestRetrieval(unittest.TestCase):

    def setUp(self):
        self.index = {
            "docs": [
                {
                    "title": "Library Study Rooms",
                    "text": "Book study rooms in the library.",
                    "tf": {"book": 1, "study": 1, "rooms": 1, "library": 1},
                    "len": 4,
                    "source_id": "library",
                    "url": "https://example.com/library",
                },
                {
                    "title": "Student Accommodation",
                    "text": "Apply for student accommodation.",
                    "tf": {
                        "apply": 1,
                        "student": 1,
                        "accommodation": 1,
                    },
                    "len": 3,
                    "source_id": "accommodation",
                    "url": "https://example.com/accommodation",
                },
            ],
            "idf": {
                "book": 1.0,
                "study": 1.0,
                "rooms": 1.0,
                "library": 1.0,
                "apply": 1.0,
                "student": 1.0,
                "accommodation": 1.0,
            },
            "avgdl": 3.5,
            "N": 2,
        }

    def test_tokenize_lowercases_text(self):
        self.assertEqual(
            tokenize("HKU LIBRARY"),
            ["hku", "library"],
        )

    def test_tokenize_removes_punctuation(self):
        self.assertEqual(
            tokenize("Hello, World!"),
            ["hello", "world"],
        )

    def test_tokenize_empty_text(self):
        self.assertEqual(tokenize(""), [])

    def test_retrieve_returns_relevant_document(self):
        results = retrieve("library study rooms", self.index)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["title"],
            "Library Study Rooms",
        )

    def test_retrieve_returns_no_results_for_empty_query(self):
        results = retrieve("", self.index)

        self.assertEqual(results, [])

    def test_retrieve_returns_no_results_for_unrelated_query(self):
        results = retrieve("gaming laptop", self.index)

        self.assertEqual(results, [])

    def test_retrieve_respects_top_k(self):
        results = retrieve("student", self.index, top_k=1)

        self.assertEqual(len(results), 1)

    def test_retrieve_ranks_more_relevant_document_first(self):
        results = retrieve("library study rooms", self.index)

        self.assertEqual(
            results[0]["title"],
            "Library Study Rooms",
        )


if __name__ == "__main__":
    unittest.main()
