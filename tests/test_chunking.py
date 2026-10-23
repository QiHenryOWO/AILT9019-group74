
import unittest

from src.chunking import chunk_text


class TestChunking(unittest.TestCase):

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(chunk_text(""), [])

    def test_whitespace_only_text_returns_empty_list(self):
        self.assertEqual(chunk_text("   "), [])

    def test_short_text_returns_one_chunk(self):
        text = "Hello world"

        chunks = chunk_text(text, size=100)

        self.assertEqual(chunks, ["Hello world"])

    def test_long_text_is_split_into_chunks(self):
        text = "a" * 1000

        chunks = chunk_text(text, size=500, overlap=0)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0]), 500)
        self.assertEqual(len(chunks[1]), 500)

    def test_chunks_have_expected_overlap(self):
        text = "a" * 1000

        chunks = chunk_text(text, size=500, overlap=100)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0][-100:], chunks[1][:100])

    def test_text_is_stripped_of_outer_whitespace(self):
        chunks = chunk_text("   hello world   ")

        self.assertEqual(chunks, ["hello world"])


if __name__ == "__main__":
    unittest.main()
