
"""Tests for scripts/run_bbw_simulator.py
Run: python tests/test_run_bbw_simulator.py
"""

import sys
import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_bbw_simulator as rbs
from run_bbw_simulator import _build_parser, run_pipeline


def _make_args(**kwargs):
    """Build a minimal Namespace for run_pipeline tests."""
    defaults = {
        "symbol": None, "tier": None, "timeframe": "5m",
        "top": None, "no_monte_carlo": True, "mc_sims": 1000,
        "no_ollama": True, "ollama_model": "qwen3:8b",
        "output_dir": Path(tempfile.mkdtemp()),
        "verbose": False, "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _parse(args_list):
    """Parse a CLI args list using _build_parser."""
    p = _build_parser()
    args = p.parse_args(args_list)
    args.output_dir = Path(args.output_dir)
    return args


class TestArgparse(unittest.TestCase):

    def test_parse_symbol_flag(self):
        """--symbol RIVERUSDT sets args.symbol = ['RIVERUSDT']."""
        args = _parse(["--symbol", "RIVERUSDT"])
        self.assertEqual(args.symbol, ["RIVERUSDT"],
                         msg="symbol mismatch: " + str(args.symbol))

    def test_parse_no_ollama_flag(self):
        """--no-ollama sets no_ollama=True."""
        args = _parse(["--no-ollama"])
        self.assertTrue(args.no_ollama,
                        msg="no_ollama should be True")

    def test_parse_no_monte_carlo_flag(self):
        """--no-monte-carlo sets no_monte_carlo=True."""
        args = _parse(["--no-monte-carlo"])
        self.assertTrue(args.no_monte_carlo,
                        msg="no_monte_carlo should be True")

    def test_parse_verbose_flag(self):
        """--verbose sets verbose=True."""
        args = _parse(["--verbose"])
        self.assertTrue(args.verbose, msg="verbose should be True")

    def test_parse_dry_run_flag(self):
        """--dry-run sets dry_run=True."""
        args = _parse(["--dry-run"])
        self.assertTrue(args.dry_run, msg="dry_run should be True")

    def test_parse_top_flag(self):
        """--top 5 sets top=5."""
        args = _parse(["--top", "5"])
        self.assertEqual(args.top, 5,
                         msg="top should be 5, got " + str(args.top))

    def test_parse_mc_sims_default(self):
        """Default mc_sims is 1000."""
        args = _parse([])
        self.assertEqual(args.mc_sims, 1000,
                         msg="default mc_sims should be 1000, got " + str(args.mc_sims))

    def test_parse_ollama_model_default(self):
        """Default ollama_model is qwen3:8b."""
        args = _parse([])
        self.assertEqual(args.ollama_model, "qwen3:8b",
                         msg="default model mismatch: " + str(args.ollama_model))


class TestRunPipelineDryRun(unittest.TestCase):

    def test_dry_run_returns_dict(self):
        """dry_run=True returns a dict immediately."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        self.assertIsInstance(result, dict,
                              msg="dry_run should return dict, got " + type(result).__name__)

    def test_dry_run_n_coins_zero(self):
        """dry_run returns n_coins_processed=0."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        self.assertEqual(result["n_coins_processed"], 0,
                         msg="dry_run n_coins_processed should be 0")

    def test_dry_run_has_required_keys(self):
        """dry_run result has n_coins_processed and n_errors."""
        args = _make_args(dry_run=True)
        result = run_pipeline(args)
        for k in ["n_coins_processed", "n_errors"]:
            self.assertIn(k, result, msg="Missing key in result: " + k)


class TestRunPipelineZeroCoins(unittest.TestCase):

    def test_zero_parquets_causes_system_exit(self):
        """Zero processable coins causes sys.exit."""
        args = _make_args(
            symbol=["NONEXISTENT"],
            dry_run=False,
            no_monte_carlo=True,
            no_ollama=True,
        )
        mock_modules = {
            "signals.bbwp":                 MagicMock(),
            "signals.bbw_sequence":         MagicMock(),
            "research.bbw_forward_returns": MagicMock(),
            "research.bbw_simulator":       MagicMock(),
            "research.bbw_report":          MagicMock(),
        }
        import sys as _sys
        with patch.object(rbs, "_load_coin_data", return_value=None),              patch.dict(_sys.modules, mock_modules):
            with self.assertRaises(SystemExit,
                                   msg="zero coins should cause SystemExit"):
                run_pipeline(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
