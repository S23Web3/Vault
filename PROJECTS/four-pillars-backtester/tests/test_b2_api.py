"""
B2 smoke tests — Vince API Layer + Dataclasses.

Tests:
  1. Syntax  — all vince/ files parse without error
  2. Types   — dataclass instantiation, field types, defaults
  3. API     — all api.py stubs raise NotImplementedError (not AttributeError or ImportError)
  4. Audit   — run_audit() executes and returns findings; CRITICAL count is sane
  5. Import  — vince package imports cleanly

No pytest dependency. Run directly:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester"
    python tests/test_b2_api.py
"""

import sys
import py_compile
import traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASSES: list[str] = []
FAILURES: list[str] = []


def ok(label: str) -> None:
    """Record a passing test."""
    PASSES.append(label)
    print("[PASS] " + label)


def fail(label: str, reason: str) -> None:
    """Record a failing test."""
    FAILURES.append(label + ": " + reason)
    print("[FAIL] " + label + ": " + reason)


# ── Test 1: Syntax ────────────────────────────────────────────────────────────

def test_syntax():
    """AST-compile all vince/ source files via py_compile."""
    vince_files = [
        ROOT / "vince" / "__init__.py",
        ROOT / "vince" / "types.py",
        ROOT / "vince" / "api.py",
        ROOT / "vince" / "audit.py",
    ]
    for path in vince_files:
        label = "syntax:" + path.name
        if not path.exists():
            fail(label, "file not found: " + str(path))
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            ok(label)
        except py_compile.PyCompileError as e:
            fail(label, str(e))


# ── Test 2: Types — dataclass instantiation ───────────────────────────────────

def test_types():
    """Instantiate all dataclasses; check field types and defaults."""
    import pandas as pd
    from vince.types import (
        IndicatorSnapshot,
        OHLCRow,
        EnrichedTradeSet,
        MetricRow,
        ConstellationFilter,
        ConstellationResult,
        SessionRecord,
        BacktestResult,
    )

    # IndicatorSnapshot
    try:
        snap = IndicatorSnapshot(k1=25.0, k2=30.0, k3=45.0, k4=60.0,
                                  cloud_bull=True, bbw=None, bar_idx=100)
        assert snap.bbw is None, "bbw should default to None"
        assert snap.bar_idx == 100
        ok("types:IndicatorSnapshot")
    except Exception as e:
        fail("types:IndicatorSnapshot", str(e))

    # OHLCRow
    try:
        ohlc = OHLCRow(open=1.0, high=1.05, low=0.98, close=1.02)
        assert ohlc.high > ohlc.low
        ok("types:OHLCRow")
    except Exception as e:
        fail("types:OHLCRow", str(e))

    # EnrichedTradeSet with empty DataFrame
    try:
        df = pd.DataFrame({"entry_bar": [1, 2], "pnl": [10.0, -5.0],
                           "direction": ["LONG", "SHORT"], "symbol": ["BTCUSDT", "ETHUSDT"]})
        ets = EnrichedTradeSet(
            trades=df,
            session_id="abc123",
            plugin_name="FourPillarsPlugin",
            symbols=["BTCUSDT", "ETHUSDT"],
            date_range=("2026-01-01", "2026-02-01"),
            enriched_at="2026-03-02T10:00:00Z",
        )
        assert isinstance(ets.trades, pd.DataFrame)
        assert len(ets.trades) == 2
        ok("types:EnrichedTradeSet")
    except Exception as e:
        fail("types:EnrichedTradeSet", str(e))

    # MetricRow
    try:
        m = MetricRow(label="Win Rate", matched=0.62, complement=0.45, delta=0.17)
        assert abs(m.delta - 0.17) < 1e-9
        ok("types:MetricRow")
    except Exception as e:
        fail("types:MetricRow", str(e))

    # ConstellationFilter — no-args (all fields optional)
    try:
        f = ConstellationFilter()
        assert f.direction is None
        assert f.outcome is None
        assert f.column_filters == {}
        ok("types:ConstellationFilter (no-args)")
    except Exception as e:
        fail("types:ConstellationFilter (no-args)", str(e))

    # ConstellationFilter — with plugin-specific filters
    try:
        f2 = ConstellationFilter(
            direction="LONG",
            outcome="win",
            min_mfe_atr=1.0,
            saw_green=True,
            column_filters={"grade": "A", "k1_9_at_entry": {"lte": 30}},
        )
        assert f2.direction == "LONG"
        assert f2.column_filters["grade"] == "A"
        ok("types:ConstellationFilter (with filters)")
    except Exception as e:
        fail("types:ConstellationFilter (with filters)", str(e))

    # ConstellationResult
    try:
        cr = ConstellationResult(
            matched_count=120,
            complement_count=880,
            metrics=[MetricRow("Win Rate", 0.62, 0.48, 0.14)],
            permutation_p_value=0.03,
        )
        assert cr.matched_count + cr.complement_count == 1000
        ok("types:ConstellationResult")
    except Exception as e:
        fail("types:ConstellationResult", str(e))

    # SessionRecord
    try:
        sr = SessionRecord(
            session_id="deadbeef",
            name="March investigation",
            created_at="2026-03-02T10:00:00Z",
            updated_at="2026-03-02T10:00:00Z",
            plugin_name="FourPillarsPlugin",
            symbols=["BTCUSDT"],
            date_range=("2026-01-01", "2026-03-01"),
            notes="Testing Grade A LONG only",
            last_filter=None,
        )
        assert sr.last_filter is None
        ok("types:SessionRecord")
    except Exception as e:
        fail("types:SessionRecord", str(e))

    # BacktestResult
    try:
        br = BacktestResult(
            params={"sl_mult": 1.5, "tp_mult": 2.5},
            trade_csv=Path("results/trades.csv"),
            start="2026-01-01",
            end="2026-02-01",
            symbols=["BTCUSDT"],
            trade_count=450,
            gross_pnl=1200.0,
            net_pnl=980.0,
            max_drawdown=120.0,
            profit_factor=1.45,
            win_rate=0.58,
            calmar=8.17,
        )
        assert br.calmar > 0
        ok("types:BacktestResult")
    except Exception as e:
        fail("types:BacktestResult", str(e))


# ── Test 3: API stubs raise NotImplementedError ───────────────────────────────

def test_api_stubs():
    """All api.py functions must raise NotImplementedError, not crash on import."""
    import pandas as pd
    from vince import api
    from vince.types import ConstellationFilter, EnrichedTradeSet

    stub_calls = [
        ("run_enricher", lambda: api.run_enricher(
            Path("trades.csv"), ["BTCUSDT"], "2026-01-01", "2026-02-01", None)),
        ("query_constellation", lambda: api.query_constellation(
            None, ConstellationFilter())),
        ("compute_mfe_histogram", lambda: api.compute_mfe_histogram(None)),
        ("compute_tp_sweep", lambda: api.compute_tp_sweep(None)),
        ("run_backtest", lambda: api.run_backtest(
            None, {}, "2026-01-01", "2026-02-01", ["BTCUSDT"])),
        ("get_session_record", lambda: api.get_session_record("abc")),
        ("save_session_record", lambda: api.save_session_record(None)),
        ("run_discovery", lambda: api.run_discovery(None, 0.05, 30)),
    ]

    for name, call in stub_calls:
        try:
            call()
            fail("api:" + name, "should have raised NotImplementedError but did not")
        except NotImplementedError:
            ok("api:" + name + " raises NotImplementedError")
        except Exception as e:
            fail("api:" + name, "unexpected exception: " + type(e).__name__ + ": " + str(e))


# ── Test 4: Audit runs and returns findings ───────────────────────────────────

def test_audit():
    """run_audit() must complete without crashing and return a non-empty list."""
    try:
        from vince.audit import run_audit, AuditFinding
        findings = run_audit(print_results=False)

        if not isinstance(findings, list):
            fail("audit:return_type", "expected list, got " + type(findings).__name__)
            return
        ok("audit:returns list")

        if not findings:
            fail("audit:non_empty", "expected findings, got empty list")
            return
        ok("audit:non_empty (" + str(len(findings)) + " findings)")

        # All items should be AuditFinding instances
        if all(isinstance(f, AuditFinding) for f in findings):
            ok("audit:all AuditFinding instances")
        else:
            fail("audit:AuditFinding types", "not all items are AuditFinding")

        # Severity values must be valid
        valid_severities = {"CRITICAL", "WARNING", "INFO"}
        bad_sev = [f.severity for f in findings if f.severity not in valid_severities]
        if bad_sev:
            fail("audit:severity_values", "invalid severities: " + str(set(bad_sev)))
        else:
            ok("audit:severity_values all valid")

        # CRITICAL findings expected (bot import, BBW, exit manager, etc.)
        n_crit = sum(1 for f in findings if f.severity == "CRITICAL")
        if n_crit > 0:
            ok("audit:CRITICAL findings found (" + str(n_crit) + ") — expected given known issues")
        else:
            fail("audit:CRITICAL count", "0 CRITICAL findings — audit may not be running checks")

    except Exception as e:
        fail("audit:run_audit", traceback.format_exc())


# ── Test 5: Package import ────────────────────────────────────────────────────

def test_import():
    """vince package and all submodules must import without error."""
    modules = ["vince", "vince.types", "vince.api", "vince.audit"]
    for mod in modules:
        try:
            import importlib
            importlib.import_module(mod)
            ok("import:" + mod)
        except Exception as e:
            fail("import:" + mod, str(e))


# ── Runner ────────────────────────────────────────────────────────────────────

def main():
    """Run all B2 smoke tests."""
    print("=" * 60)
    print("B2 SMOKE TESTS — " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 60)

    test_syntax()
    test_import()
    test_types()
    test_api_stubs()
    test_audit()

    print("\n" + "=" * 60)
    print("RESULTS: " + str(len(PASSES)) + " PASS  |  " + str(len(FAILURES)) + " FAIL")
    if FAILURES:
        print("\nFAILURES:")
        for f in FAILURES:
            print("  - " + f)
        print("=" * 60)
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
