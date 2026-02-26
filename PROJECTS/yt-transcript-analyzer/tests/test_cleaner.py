"""Tests for cleaner.py — VTT parsing and deduplication logic."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cleaner import deduplicate, group_into_blocks, parse_vtt, vtt_timestamp_to_seconds


class TestVttTimestampToSeconds(unittest.TestCase):
    """Test VTT timestamp string parsing."""

    def test_hms_format(self):
        """HH:MM:SS.mmm format parses to float seconds."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("00:01:30.000"), 90.0)

    def test_ms_format(self):
        """MM:SS.mmm format parses to float seconds."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("01:30.000"), 90.0)

    def test_zero(self):
        """Zero timestamp returns 0.0."""
        self.assertAlmostEqual(vtt_timestamp_to_seconds("00:00:00.000"), 0.0)


class TestDeduplicate(unittest.TestCase):
    """Test consecutive duplicate line removal."""

    def test_removes_consecutive(self):
        """Two identical consecutive entries collapse to one."""
        entries = [(0.0, "Hello world"), (1.0, "Hello world"), (2.0, "Next line")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 2, msg="dedup: expected 2 entries, got " + str(len(result)))
        self.assertEqual(result[1][1], "Next line")

    def test_case_insensitive(self):
        """Case differences are ignored during dedup."""
        entries = [(0.0, "Hello World"), (1.0, "hello world")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 1, msg="case-insensitive dedup failed")

    def test_non_consecutive_kept(self):
        """Non-consecutive identical lines are both kept."""
        entries = [(0.0, "Line A"), (1.0, "Line B"), (2.0, "Line A")]
        result = deduplicate(entries)
        self.assertEqual(len(result), 3, msg="non-consecutive dedup should keep both")


class TestGroupIntoBlocks(unittest.TestCase):
    """Test 30-second block grouping."""

    def test_single_block(self):
        """Entries within one interval form one block."""
        entries = [(0.0, "A"), (10.0, "B"), (20.0, "C")]
        result = group_into_blocks(entries, interval=30)
        self.assertEqual(len(result), 1, msg="single block expected")

    def test_two_blocks(self):
        """Entries spanning two intervals form two blocks."""
        entries = [(0.0, "A"), (31.0, "B")]
        result = group_into_blocks(entries, interval=30)
        self.assertEqual(len(result), 2, msg="two blocks expected")

    def test_empty_input(self):
        """Empty input returns empty list."""
        self.assertEqual(group_into_blocks([]), [], msg="empty input should return []")


class TestParseVtt(unittest.TestCase):
    """Test VTT file parsing with a temp file."""

    def test_basic_vtt(self):
        """Parsing a minimal VTT file returns correct entries."""
        vtt_content = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:02.000\n"
            "Hello world\n\n"
            "00:00:02.000 --> 00:00:04.000\n"
            "Second line\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtt", delete=False, encoding="utf-8"
        ) as f:
            f.write(vtt_content)
            tmp = Path(f.name)
        try:
            entries = parse_vtt(tmp)
            self.assertGreater(len(entries), 0, msg="should have at least one entry")
            self.assertEqual(entries[0][1], "Hello world", msg="first entry text mismatch")
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
