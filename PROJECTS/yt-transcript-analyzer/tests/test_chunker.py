"""Tests for chunker.py — split logic with mocked Ollama token counter."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunker import split_into_chunks


def _mock_count(text: str) -> int:
    """Mock token counter: approximate 1 token per word."""
    return len(text.split())


class TestSplitIntoChunks(unittest.TestCase):
    """Test chunk splitting with mocked count_tokens."""

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_short_text_single_chunk(self, _):
        """Text smaller than CHUNK_SIZE produces exactly one chunk."""
        text = "word " * 50
        chunks = split_into_chunks(text.strip(), "src")
        self.assertEqual(len(chunks), 1, msg="50 words should fit in one chunk")

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_chunk_id_prefix(self, _):
        """Chunk IDs start with source_id prefix."""
        text = "word " * 50
        chunks = split_into_chunks(text.strip(), "mysrc")
        self.assertTrue(
            chunks[0]["chunk_id"].startswith("mysrc"),
            msg="chunk_id should start with source_id",
        )

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_empty_text_returns_empty(self, _):
        """Empty text input returns empty list."""
        chunks = split_into_chunks("", "src")
        self.assertEqual(chunks, [], msg="empty text should return []")

    @patch("chunker.count_tokens", side_effect=_mock_count)
    def test_chunk_has_required_fields(self, _):
        """Each chunk dict contains all required fields."""
        text = "word " * 30
        chunks = split_into_chunks(text.strip(), "src")
        required = {"chunk_id", "source_id", "chunk_index", "token_count", "text"}
        for chunk in chunks:
            for field in required:
                self.assertIn(field, chunk, msg="missing field: " + field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
