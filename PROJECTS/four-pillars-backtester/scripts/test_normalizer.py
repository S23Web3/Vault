"""
Test script for data/normalizer.py and scripts/convert_csv.py.
Validates format detection, normalization, validation, resampling, and parquet output.

Run: python scripts/test_normalizer.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from data.normalizer import OHLCVNormalizer, NormalizerError

PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {name} -- {detail}")


def write_csv(tmpdir, filename, content):
    path = tmpdir / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


# ── Mock CSV data generators ────────────────────────────────────────────────

def mock_bybit_csv(tmpdir, n=100):
    """Bybit format: timestamp,open,high,low,close,volume,turnover"""
    ts_start = 1700000000000
    lines = ["timestamp,open,high,low,close,volume,turnover"]
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i * 0.01
        h = o + 0.5
        l = o - 0.3
        c = o + 0.1
        v = 1000 + i
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{q}")
    return write_csv(tmpdir, "bybit.csv", "\n".join(lines))


def mock_binance_csv(tmpdir, n=100):
    """Binance format: Open time,Open,High,Low,Close,Volume,Close time,Quote asset volume,..."""
    ts_start = 1700000000000
    lines = ["Open time,Open,High,Low,Close,Volume,Close time,Quote asset volume,Number of trades"]
    for i in range(n):
        ts = ts_start + i * 60000
        o = 50000 + i
        h = o + 50
        l = o - 30
        c = o + 10
        v = 5.5 + i * 0.01
        ct = ts + 59999
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{ct},{q},100")
    return write_csv(tmpdir, "binance.csv", "\n".join(lines))


def mock_okx_csv(tmpdir, n=100):
    """OKX format: ts,o,h,l,c,vol,volCcy"""
    ts_start = 1700000000000
    lines = ["ts,o,h,l,c,vol,volCcy"]
    for i in range(n):
        ts = ts_start + i * 60000
        o = 2000 + i * 0.5
        h = o + 2
        l = o - 1
        c = o + 0.5
        v = 500 + i
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{q}")
    return write_csv(tmpdir, "okx.csv", "\n".join(lines))


def mock_weex_csv(tmpdir, n=100):
    """WEEX format: open,high,low,close,base_vol,quote_vol (with timestamp col)"""
    ts_start = 1700000000000
    lines = ["timestamp,open,high,low,close,base_vol,quote_vol"]
    for i in range(n):
        ts = ts_start + i * 60000
        o = 0.005 + i * 0.0001
        h = o + 0.001
        l = o - 0.0005
        c = o + 0.0002
        v = 10000000 + i * 1000
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{q}")
    return write_csv(tmpdir, "weex.csv", "\n".join(lines))


def mock_tradingview_csv(tmpdir, n=100):
    """TradingView format: time,open,high,low,close,Volume"""
    lines = ["time,open,high,low,close,Volume"]
    for i in range(n):
        dt = pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(minutes=i)
        o = 100 + i * 0.1
        h = o + 0.5
        l = o - 0.3
        c = o + 0.2
        v = 5000 + i
        lines.append(f"{dt.isoformat()},{o},{h},{l},{c},{v}")
    return write_csv(tmpdir, "tradingview.csv", "\n".join(lines))


def mock_epoch_seconds_csv(tmpdir, n=100):
    """CryptoCompare-style: time,open,high,low,close,volumefrom,volumeto (epoch seconds)"""
    ts_start = 1700000000
    lines = ["time,open,high,low,close,volumefrom,volumeto"]
    for i in range(n):
        ts = ts_start + i * 60
        o = 30000 + i
        h = o + 20
        l = o - 15
        c = o + 5
        v = 100 + i
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{q}")
    return write_csv(tmpdir, "epoch_s.csv", "\n".join(lines))


def mock_5m_csv(tmpdir, n=100):
    """5m interval data"""
    ts_start = 1700000000000
    lines = ["timestamp,open,high,low,close,volume,turnover"]
    for i in range(n):
        ts = ts_start + i * 300000  # 5 min intervals
        o = 100 + i * 0.05
        h = o + 0.8
        l = o - 0.4
        c = o + 0.2
        v = 5000 + i * 10
        q = v * c
        lines.append(f"{ts},{o},{h},{l},{c},{v},{q}")
    return write_csv(tmpdir, "data_5m.csv", "\n".join(lines))


def mock_tab_csv(tmpdir, n=50):
    """Tab-delimited data"""
    lines = ["timestamp\topen\thigh\tlow\tclose\tvolume"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i
        lines.append(f"{ts}\t{o}\t{o+1}\t{o-0.5}\t{o+0.3}\t{1000+i}")
    return write_csv(tmpdir, "tab.csv", "\n".join(lines))


def mock_semicolon_csv(tmpdir, n=50):
    """Semicolon-delimited data"""
    lines = ["timestamp;open;high;low;close;volume"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i
        lines.append(f"{ts};{o};{o+1};{o-0.5};{o+0.3};{1000+i}")
    return write_csv(tmpdir, "semicolon.csv", "\n".join(lines))


def mock_bom_csv(tmpdir, n=50):
    """CSV with BOM prefix"""
    lines = ["timestamp,open,high,low,close,volume"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i
        lines.append(f"{ts},{o},{o+1},{o-0.5},{o+0.3},{1000+i}")
    content = "\n".join(lines)
    path = tmpdir / "bom.csv"
    path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    return str(path)


def mock_no_vol_csv(tmpdir, n=50):
    """CSV missing volume column"""
    lines = ["timestamp,open,high,low,close"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i
        lines.append(f"{ts},{o},{o+1},{o-0.5},{o+0.3}")
    return write_csv(tmpdir, "novol.csv", "\n".join(lines))


def mock_bad_ohlc_csv(tmpdir, n=50):
    """CSV with OHLC sanity violations (high < low on some rows)"""
    lines = ["timestamp,open,high,low,close,volume"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        o = 100 + i
        if i == 10:
            h, l = o - 1, o + 1  # bad: high < low
        else:
            h, l = o + 1, o - 0.5
        c = o + 0.3
        lines.append(f"{ts},{o},{h},{l},{c},{1000+i}")
    return write_csv(tmpdir, "bad_ohlc.csv", "\n".join(lines))


def mock_dupes_csv(tmpdir, n=50):
    """CSV with duplicate timestamps"""
    lines = ["timestamp,open,high,low,close,volume"]
    ts_start = 1700000000000
    for i in range(n):
        ts = ts_start + i * 60000
        if i == 5:
            ts = ts_start + 4 * 60000  # duplicate of row 4
        o = 100 + i
        lines.append(f"{ts},{o},{o+1},{o-0.5},{o+0.3},{1000+i}")
    return write_csv(tmpdir, "dupes.csv", "\n".join(lines))


# ── Test functions ──────────────────────────────────────────────────────────

def test_delimiter_detection():
    print("\n=== Delimiter Detection ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        n = OHLCVNormalizer(cache_dir=str(tmpdir / "cache"))

        comma_path = mock_bybit_csv(tmpdir)
        check("comma delimiter", n._detect_delimiter(comma_path) == ",")

        tab_path = mock_tab_csv(tmpdir)
        check("tab delimiter", n._detect_delimiter(tab_path) == "\t")

        semi_path = mock_semicolon_csv(tmpdir)
        check("semicolon delimiter", n._detect_delimiter(semi_path) == ";")
    finally:
        shutil.rmtree(tmpdir)


def test_column_mapping():
    print("\n=== Column Mapping ===")

    # Bybit
    m = OHLCVNormalizer._detect_columns(
        ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
    )
    check("bybit columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"})

    # Binance
    m = OHLCVNormalizer._detect_columns(
        ["Open time", "Open", "High", "Low", "Close", "Volume", "Quote asset volume"]
    )
    check("binance columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"})

    # OKX
    m = OHLCVNormalizer._detect_columns(["ts", "o", "h", "l", "c", "vol", "volCcy"])
    check("okx columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol"})

    # WEEX
    m = OHLCVNormalizer._detect_columns(
        ["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"]
    )
    check("weex columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"})

    # TradingView
    m = OHLCVNormalizer._detect_columns(["time", "open", "high", "low", "close", "Volume"])
    check("tradingview columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol"})

    # CryptoCompare (epoch seconds)
    m = OHLCVNormalizer._detect_columns(
        ["time", "open", "high", "low", "close", "volumefrom", "volumeto"]
    )
    check("cryptocompare columns", set(m.keys()) >= {"timestamp", "open", "high", "low", "close", "base_vol"})


def test_timestamp_parsing():
    print("\n=== Timestamp Parsing ===")

    # Epoch ms
    fmt = OHLCVNormalizer._detect_timestamp_format(pd.Series(["1700000000000", "1700000060000"]))
    check("epoch ms detected", fmt == "epoch_ms")

    # Epoch seconds
    fmt = OHLCVNormalizer._detect_timestamp_format(pd.Series(["1700000000", "1700000060"]))
    check("epoch seconds detected", fmt == "epoch_s")

    # ISO string
    fmt = OHLCVNormalizer._detect_timestamp_format(pd.Series(["2024-01-01T00:00:00+00:00", "2024-01-01T00:01:00+00:00"]))
    check("ISO string detected", fmt == "ISO8601")

    # Standard datetime string (pandas ISO8601 may accept space separator on some versions)
    fmt = OHLCVNormalizer._detect_timestamp_format(pd.Series(["2024-01-01 00:00:00", "2024-01-01 00:01:00"]))
    check("datetime string detected", fmt in ("ISO8601", "%Y-%m-%d %H:%M:%S"),
          f"got {fmt!r}")


def test_interval_detection():
    print("\n=== Interval Detection ===")

    # 1m
    ts = pd.Series([1700000000000 + i * 60000 for i in range(100)])
    check("1m interval", OHLCVNormalizer._detect_interval(ts) == "1m")

    # 5m
    ts = pd.Series([1700000000000 + i * 300000 for i in range(100)])
    check("5m interval", OHLCVNormalizer._detect_interval(ts) == "5m")

    # 1h
    ts = pd.Series([1700000000000 + i * 3600000 for i in range(100)])
    check("1h interval", OHLCVNormalizer._detect_interval(ts) == "1h")

    # 1d
    ts = pd.Series([1700000000000 + i * 86400000 for i in range(100)])
    check("1d interval", OHLCVNormalizer._detect_interval(ts) == "1d")


def test_normalize_bybit():
    print("\n=== Normalize Bybit CSV ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_bybit_csv(tmpdir, n=200)
        df = n.normalize(csv_path, "TESTCOIN")

        # Check columns
        expected_cols = ["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol", "datetime"]
        check("columns match", list(df.columns) == expected_cols,
              f"got {list(df.columns)}")

        # Check dtypes
        check("timestamp int64", df["timestamp"].dtype == np.int64)
        check("open float64", df["open"].dtype == np.float64)
        check("datetime tz-aware", hasattr(df["datetime"].dt, "tz") and df["datetime"].dt.tz is not None)

        # Check parquet exists
        pq_path = cache / "TESTCOIN_1m.parquet"
        meta_path = cache / "TESTCOIN_1m.meta"
        check("parquet created", pq_path.exists())
        check("meta created", meta_path.exists())

        # Check meta format
        meta = meta_path.read_text().strip()
        parts = meta.split(",")
        check("meta has 2 parts", len(parts) == 2, f"got: {meta}")

        # Check 5m auto-resample (1m input -> should also save 5m)
        pq_5m = cache / "TESTCOIN_5m.parquet"
        check("5m auto-resample created", pq_5m.exists())

        if pq_5m.exists():
            df_5m = pd.read_parquet(pq_5m)
            check("5m has fewer rows", len(df_5m) < len(df),
                  f"5m: {len(df_5m)}, 1m: {len(df)}")
    finally:
        shutil.rmtree(tmpdir)


def test_normalize_binance():
    print("\n=== Normalize Binance CSV ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_binance_csv(tmpdir, n=100)
        df = n.normalize(csv_path, "BTCTEST")

        check("binance rows", len(df) == 100)
        check("binance has quote_vol", "quote_vol" in df.columns and not df["quote_vol"].isna().all())
    finally:
        shutil.rmtree(tmpdir)


def test_normalize_tradingview():
    print("\n=== Normalize TradingView CSV ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_tradingview_csv(tmpdir, n=100)
        df = n.normalize(csv_path, "TVTEST")

        check("tv rows", len(df) == 100)
        check("tv timestamp is int", df["timestamp"].dtype == np.int64)
    finally:
        shutil.rmtree(tmpdir)


def test_normalize_epoch_seconds():
    print("\n=== Normalize Epoch Seconds CSV ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_epoch_seconds_csv(tmpdir, n=100)
        df = n.normalize(csv_path, "CCTEST")

        check("epoch_s rows", len(df) == 100)
        # Timestamps should be in milliseconds (>1e12)
        check("epoch_s converted to ms", df["timestamp"].iloc[0] > 1e12,
              f"got {df['timestamp'].iloc[0]}")
    finally:
        shutil.rmtree(tmpdir)


def test_5m_detection():
    print("\n=== 5m Interval Detection ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_5m_csv(tmpdir, n=100)
        info = n.detect_format(csv_path)
        check("5m interval detected", info["interval"] == "5m", f"got {info['interval']}")

        # Normalize should save as _5m.parquet (not _1m)
        df = n.normalize(csv_path, "FIVEMIN")
        pq_5m = cache / "FIVEMIN_5m.parquet"
        check("saved as 5m parquet", pq_5m.exists())
        # Should NOT create 1m file (source is 5m)
        pq_1m = cache / "FIVEMIN_1m.parquet"
        check("no 1m file for 5m source", not pq_1m.exists())
    finally:
        shutil.rmtree(tmpdir)


def test_bom_handling():
    print("\n=== BOM Handling ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_bom_csv(tmpdir, n=50)
        df = n.normalize(csv_path, "BOMTEST")
        check("bom parsed", len(df) == 50)
    finally:
        shutil.rmtree(tmpdir)


def test_missing_volume():
    print("\n=== Missing Volume Error ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_no_vol_csv(tmpdir)
        try:
            n.normalize(csv_path, "NOVOL")
            check("missing vol error", False, "should have raised NormalizerError")
        except NormalizerError:
            check("missing vol error", True)
    finally:
        shutil.rmtree(tmpdir)


def test_missing_quote_vol():
    print("\n=== Missing Quote Vol (NaN fill) ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        # TradingView has no quote_vol
        csv_path = mock_tradingview_csv(tmpdir, n=50)
        df = n.normalize(csv_path, "NOQVOL")
        check("quote_vol is NaN", df["quote_vol"].isna().all())
    finally:
        shutil.rmtree(tmpdir)


def test_duplicate_removal():
    print("\n=== Duplicate Timestamp Removal ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_dupes_csv(tmpdir, n=50)
        df = n.normalize(csv_path, "DUPETEST")
        check("dupes removed", len(df) == 49, f"got {len(df)}")
    finally:
        shutil.rmtree(tmpdir)


def test_validation_warnings():
    print("\n=== OHLC Validation Warnings ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))
        csv_path = mock_bad_ohlc_csv(tmpdir)
        info = n.detect_format(csv_path)
        has_warning = any("high" in w.lower() or "low" in w.lower() for w in info["warnings"])
        check("bad OHLC detected", has_warning, f"warnings: {info['warnings']}")
    finally:
        shutil.rmtree(tmpdir)


def test_batch_normalize():
    print("\n=== Batch Normalize ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        csvdir = tmpdir / "csvs"
        csvdir.mkdir()
        n = OHLCVNormalizer(cache_dir=str(cache))

        # Create 3 CSVs with symbol names in filenames
        for sym in ["ATEST_1m", "BTEST_1m", "CTEST_1m"]:
            lines = ["timestamp,open,high,low,close,volume"]
            ts = 1700000000000
            for i in range(20):
                o = 100 + i
                lines.append(f"{ts + i*60000},{o},{o+1},{o-0.5},{o+0.3},{1000+i}")
            (csvdir / f"{sym}.csv").write_text("\n".join(lines))

        results = n.normalize_batch(str(csvdir))
        check("batch 3 files", len(results) == 3, f"got {len(results)}")
        check("batch symbols", set(results.keys()) == {"ATEST", "BTEST", "CTEST"},
              f"got {set(results.keys())}")
    finally:
        shutil.rmtree(tmpdir)


def test_column_override():
    print("\n=== Column Override ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))

        # Create CSV with weird column names
        lines = ["T,P1,P2,P3,P4,V"]
        ts = 1700000000000
        for i in range(20):
            o = 100 + i
            lines.append(f"{ts + i*60000},{o},{o+1},{o-0.5},{o+0.3},{1000+i}")
        csv_path = write_csv(tmpdir, "weird.csv", "\n".join(lines))

        # Manual column map
        col_map = {
            "timestamp": "T", "open": "P1", "high": "P2",
            "low": "P3", "close": "P4", "base_vol": "V",
        }
        df = n.normalize(csv_path, "OVERRIDE", column_map=col_map)
        check("override rows", len(df) == 20)
        check("override columns", list(df.columns) == [
            "timestamp", "open", "high", "low", "close", "base_vol", "quote_vol", "datetime"
        ])
    finally:
        shutil.rmtree(tmpdir)


def test_integration_pipeline():
    """Integration: normalize mock CSV -> load via parquet -> run signal pipeline."""
    print("\n=== Integration Pipeline ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        cache = tmpdir / "cache"
        n = OHLCVNormalizer(cache_dir=str(cache))

        # Create 500 bars of 1m data (enough for ATR=14 warmup)
        lines = ["timestamp,open,high,low,close,volume,turnover"]
        ts = 1700000000000
        price = 100.0
        for i in range(500):
            price += np.random.randn() * 0.5
            o = price
            h = o + abs(np.random.randn()) * 0.3
            l = o - abs(np.random.randn()) * 0.3
            c = o + np.random.randn() * 0.1
            v = 10000 + np.random.randint(0, 5000)
            q = v * c
            lines.append(f"{ts + i*60000},{o:.4f},{h:.4f},{l:.4f},{c:.4f},{v},{q:.2f}")
        csv_path = write_csv(tmpdir, "integration.csv", "\n".join(lines))

        df = n.normalize(csv_path, "INTTEST")

        # Load back from parquet (simulating load_cached)
        pq_path = cache / "INTTEST_1m.parquet"
        df_loaded = pd.read_parquet(pq_path)

        check("loaded matches original", len(df_loaded) == len(df))
        check("loaded has all columns",
              set(df_loaded.columns) == {"timestamp", "open", "high", "low", "close", "base_vol", "quote_vol", "datetime"})

        # Try running signal pipeline (if available)
        try:
            from signals.four_pillars_v383 import compute_signals_v383

            # Rename for signal pipeline compatibility
            df_sig = df_loaded.copy()
            df_sig = compute_signals_v383(df_sig, {})
            check("signal pipeline runs", "atr" in df_sig.columns)
        except ImportError:
            check("signal pipeline (skipped, not in path)", True)

    finally:
        shutil.rmtree(tmpdir)


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  NORMALIZER TEST SUITE")
    print("=" * 60)

    test_delimiter_detection()
    test_column_mapping()
    test_timestamp_parsing()
    test_interval_detection()
    test_normalize_bybit()
    test_normalize_binance()
    test_normalize_tradingview()
    test_normalize_epoch_seconds()
    test_5m_detection()
    test_bom_handling()
    test_missing_volume()
    test_missing_quote_vol()
    test_duplicate_removal()
    test_validation_warnings()
    test_batch_normalize()
    test_column_override()
    test_integration_pipeline()

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {PASS_COUNT} passed, {FAIL_COUNT} failed")
    print(f"{'=' * 60}")
    sys.exit(0 if FAIL_COUNT == 0 else 1)
