"""Tests for reporter.py — slug generation and sort order."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reporter import make_slug


class TestMakeSlug(unittest.TestCase):
    """Test query slug generation for report filenames."""

    def test_basic_slug(self):
        """Simple query produces hyphenated lowercase slug."""
        self.assertEqual(
            make_slug("XGBoost feature selection"),
            "xgboost-feature-selection",
            msg="basic slug mismatch",
        )

    def test_special_chars_removed(self):
        """Special characters are stripped from slug."""
        result = make_slug("Hello, World! (test)")
        self.assertNotIn(",", result, msg="comma should be removed")
        self.assertNotIn("!", result, msg="exclamation should be removed")
        self.assertNotIn("(", result, msg="parenthesis should be removed")

    def test_truncated_to_max_len(self):
        """Slug is truncated at max_len characters."""
        result = make_slug("word " * 20, max_len=50)
        self.assertLessEqual(len(result), 50, msg="slug should not exceed max_len")

    def test_all_lowercase(self):
        """Slug is fully lowercased."""
        result = make_slug("UPPER CASE QUERY")
        self.assertEqual(result, result.lower(), msg="slug should be lowercase")

    def test_spaces_become_hyphens(self):
        """Word spaces become hyphens in the slug."""
        result = make_slug("multiple word query")
        self.assertIn("-", result, msg="should contain hyphens")
        self.assertNotIn(" ", result, msg="should not contain spaces")


if __name__ == "__main__":
    unittest.main(verbosity=2)
