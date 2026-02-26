
"""Tests for research/bbw_ollama_review.py
Run: python tests/test_bbw_ollama_review.py
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from research.bbw_ollama_review import (
    ollama_chat,
    analyze_state_stats,
    investigate_anomalies,
    generate_executive_summary,
    run_ollama_review,
    OFFLINE_PREFIX,
)


def _mock_resp(text="Test response"):
    """Build a mock requests.Response that returns text."""
    r = MagicMock()
    r.json.return_value = {"response": text}
    r.raise_for_status = MagicMock()
    return r


class TestOllamaChat(unittest.TestCase):

    def test_success_returns_response(self):
        """Successful Ollama call returns the response text."""
        with patch("requests.post", return_value=_mock_resp("Hello World")):
            result = ollama_chat("Test prompt")
        self.assertEqual(result, "Hello World",
                         msg="should return response text, got: " + result[:50])

    def test_connection_error_returns_offline(self):
        """ConnectionError returns string starting with OFFLINE_PREFIX."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("refused")):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="should start with OFFLINE_PREFIX, got: " + result[:60])

    def test_timeout_returns_offline(self):
        """Timeout returns OFFLINE_PREFIX string."""
        with patch("requests.post",
                   side_effect=requests.exceptions.Timeout("timeout")):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="timeout should return OFFLINE, got: " + result[:60])

    def test_json_decode_error_returns_offline(self):
        """JSONDecodeError in response returns OFFLINE_PREFIX string."""
        bad_resp = MagicMock()
        bad_resp.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        bad_resp.raise_for_status = MagicMock()
        with patch("requests.post", return_value=bad_resp):
            result = ollama_chat("Test")
        self.assertTrue(result.startswith(OFFLINE_PREFIX),
                        msg="JSONDecodeError should return OFFLINE, got: " + result[:60])

    def test_always_returns_string(self):
        """ollama_chat always returns str even on unexpected errors."""
        with patch("requests.post", side_effect=Exception("unexpected")):
            result = ollama_chat("Test")
        self.assertIsInstance(result, str,
                              msg="should return str, got " + type(result).__name__)


class TestAnalyzeStateStats(unittest.TestCase):

    def test_missing_csv_returns_string(self):
        """Missing CSV paths return a string without crashing."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("x")):
            result = analyze_state_stats("/nonexistent/path.csv", "/nonexistent.csv")
        self.assertIsInstance(result, str,
                              msg="missing CSV should return string")

    def test_empty_csv_skipped(self):
        """Empty CSV returns a string (not a crash)."""
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("state,expectancy\n")
            tmp = f.name
        try:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = analyze_state_stats(tmp, "/nonexistent.csv")
            self.assertIsInstance(result, str)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_with_mock_ollama_response(self):
        """analyze_state_stats passes CSV data to Ollama and returns response."""
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write("state,expectancy\nBLUE,1.5\nRED,0.8\n")
            tmp = f.name
        try:
            with patch("requests.post", return_value=_mock_resp("Analysis here")):
                result = analyze_state_stats(tmp, "/nonexistent.csv")
            self.assertEqual(result, "Analysis here",
                             msg="should return Ollama response")
        finally:
            Path(tmp).unlink(missing_ok=True)


class TestInvestigateAnomalies(unittest.TestCase):

    def test_missing_all_inputs_returns_string(self):
        """Missing CSV and dir return a string."""
        with patch("requests.post",
                   side_effect=requests.exceptions.ConnectionError("x")):
            result = investigate_anomalies("/nonexistent.csv", "/nonexistent_dir")
        self.assertIsInstance(result, str,
                              msg="missing inputs should return string")

    def test_empty_tier_dir_returns_string(self):
        """Empty per_tier_dir returns no-data string without crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = investigate_anomalies("/nonexistent.csv", tmpdir)
        self.assertIsInstance(result, str)


class TestGenerateExecutiveSummary(unittest.TestCase):

    def test_empty_results_returns_string(self):
        """Empty all_results dict returns a no-data string."""
        result = generate_executive_summary({})
        self.assertIsInstance(result, str,
                              msg="empty dict should return string")

    def test_with_mock_response(self):
        """generate_executive_summary returns Ollama response text."""
        with patch("requests.post", return_value=_mock_resp("Executive summary")):
            result = generate_executive_summary({"test": "data"})
        self.assertEqual(result, "Executive summary",
                         msg="should return Ollama response text")


class TestRunOllamaReview(unittest.TestCase):

    def test_returns_dict(self):
        """run_ollama_review always returns a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertIsInstance(result, dict,
                              msg="should return dict, got " + type(result).__name__)

    def test_correct_keys(self):
        """Return dict has files_written, errors, summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        for k in ["files_written", "errors", "summary"]:
            self.assertIn(k, result, msg="Missing key in result: " + k)

    def test_offline_still_writes_md_files(self):
        """Ollama offline still writes .md files with OFFLINE content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post",
                       side_effect=requests.exceptions.ConnectionError("x")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertGreater(
            len(result["files_written"]), 0,
            msg="should write .md files even when offline, got 0",
        )

    def test_online_writes_md_files(self):
        """When Ollama is online, .md files are written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.post", return_value=_mock_resp("Mock analysis")):
                result = run_ollama_review(
                    reports_dir=tmpdir,
                    output_dir=str(Path(tmpdir) / "ollama"),
                )
        self.assertGreater(len(result["files_written"]), 0,
                           msg="should write at least one .md file when online")

    def test_verbose_does_not_crash(self):
        """verbose=True runs without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with patch("requests.post",
                           side_effect=requests.exceptions.ConnectionError("x")):
                    run_ollama_review(
                        reports_dir=tmpdir,
                        output_dir=str(Path(tmpdir) / "ollama"),
                        verbose=True,
                    )
            except Exception as e:
                self.fail("verbose=True raised exception: " + str(e))


if __name__ == "__main__":
    unittest.main(verbosity=2)
