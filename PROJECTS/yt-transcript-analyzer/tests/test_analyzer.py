"""Tests for analyzer.py — response parser, strip_thinking, keyword filter."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import (
    extract_query_keywords,
    keyword_prefilter,
    parse_response,
    strip_thinking,
)


class TestStripThinking(unittest.TestCase):
    """Test <think>...</think> block removal."""

    def test_removes_single_line_think_block(self):
        """Single-line think block is stripped, leaving the rest."""
        text = "<think>reasoning</think>\nFOUND: yes\nQUOTE: relevant text"
        result = strip_thinking(text)
        self.assertNotIn("<think>", result, msg="<think> tag should be gone")
        self.assertIn("FOUND: yes", result, msg="FOUND line should remain")

    def test_removes_multiline_think_block(self):
        """Multiline think block is stripped completely."""
        text = "<think>\nline1\nline2\n</think>\nFOUND: no"
        result = strip_thinking(text)
        self.assertNotIn("line1", result, msg="think content should be gone")
        self.assertIn("FOUND: no", result, msg="FOUND line should remain")

    def test_no_think_block_unchanged(self):
        """Text without think block is returned unchanged."""
        text = "FOUND: yes\nQUOTE: something"
        self.assertEqual(strip_thinking(text), text, msg="unchanged when no think block")


class TestParseResponse(unittest.TestCase):
    """Test FOUND/QUOTE field parsing with fallbacks."""

    def test_found_yes(self):
        """FOUND: yes → found=True with correct quote."""
        result = parse_response("FOUND: yes\nQUOTE: relevant text")
        self.assertTrue(result["found"], msg="found should be True")
        self.assertEqual(result["quote"], "relevant text", msg="quote mismatch")

    def test_found_no(self):
        """FOUND: no → found=False."""
        result = parse_response("FOUND: no\nQUOTE: none")
        self.assertFalse(result["found"], msg="found should be False")

    def test_missing_found_defaults_no(self):
        """Missing FOUND field defaults to found=False."""
        result = parse_response("some random text without fields")
        self.assertFalse(result["found"], msg="missing FOUND should default to False")

    def test_missing_quote_defaults_none(self):
        """Missing QUOTE field defaults to quote=none."""
        result = parse_response("FOUND: yes")
        self.assertEqual(result["quote"], "none", msg="missing QUOTE should default to none")


class TestKeywordFilter(unittest.TestCase):
    """Test query keyword extraction and pre-filter."""

    def test_removes_stop_words(self):
        """Stop words are excluded from extracted keywords."""
        keywords = extract_query_keywords("the best way to learn Python")
        self.assertIn("best", keywords, msg="content word should be included")
        self.assertIn("python", keywords, msg="content word should be included")
        self.assertNotIn("the", keywords, msg="stop word should be excluded")
        self.assertNotIn("to", keywords, msg="stop word should be excluded")

    def test_keyword_present_returns_true(self):
        """Text containing a keyword passes the filter."""
        self.assertTrue(
            keyword_prefilter("Python is great for ML", ["python"]),
            msg="keyword present should return True",
        )

    def test_keyword_absent_returns_false(self):
        """Text without any keyword fails the filter."""
        self.assertFalse(
            keyword_prefilter("Today is a sunny day", ["python"]),
            msg="keyword absent should return False",
        )

    def test_empty_keywords_always_passes(self):
        """Empty keyword list passes all text."""
        self.assertTrue(
            keyword_prefilter("anything at all", []),
            msg="empty keywords should always return True",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
