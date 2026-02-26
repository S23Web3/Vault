"""
Data fetcher for historical candle data.
Primary: Bybit v5 API (full historical pagination).
Fallback: WEEX API (latest 1000 candles only).
Saves to Parquet files in data/cache/.
Restartable — skips coins that already have complete data.
"""

import time
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional


class BybitFetcher:
    """Fetches historical OHLCV candles from Bybit v5 public API."""

    BASE_URL = "https://api.bybit.com"
    ENDPOINT = "/v5/market/kline"
    MAX_CANDLES = 1000  # API limit per request
    COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]

    def __init__(self, cache_dir: str = "data/cache", rate_limit: float = 0.1):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit  # seconds between requests
        self.session = requests.Session()

    def _cache_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}_1m.parquet"

    def _meta_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}_1m.meta"

    def _fetch_page(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """Fetch one page of 1m candles between start_ms and end_ms."""
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": "1",
            "start": str(start_ms),
            "end": str(end_ms),
            "limit": str(self.MAX_CANDLES),
        }
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data.get("retCode") != 0:
                print(f"  API error for {symbol}: {data.get('retMsg')}")
                return []

            candles = data.get("result", {}).get("list", [])
            return candles if candles else []

        except requests.exceptions.RequestException as e:
            print(f"  Request error for {symbol}: {e}")
            return []

    def fetch_symbol(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        force: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch all 1m candles for a symbol between start_time and end_time.
        Paginates forward from start_time. Saves to Parquet.
        Returns DataFrame or None on failure.
        """
        cache_file = self._cache_path(symbol)
        meta_file = self._meta_path(symbol)

        # Check if already cached with matching time range
        if not force and cache_file.exists() and meta_file.exists():
            meta = meta_file.read_text().strip().split(",")
            if len(meta) == 2:
                cached_start, cached_end = int(meta[0]), int(meta[1])
                req_start = int(start_time.timestamp() * 1000)
                req_end = int(end_time.timestamp() * 1000)
                if cached_start <= req_start and cached_end >= req_end:
                    print(f"  {symbol}: cached, skipping")
                    return pd.read_parquet(cache_file)

        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        cursor = end_ms  # Paginate backwards from end
        all_candles = []
        page = 0

        while cursor > start_ms:
            page += 1
            candles = self._fetch_page(symbol, start_ms, cursor)

            if not candles:
                break

            all_candles.extend(candles)

            # Bybit returns newest first — oldest is the last element
            oldest_ts = min(int(c[0]) for c in candles)

            # Move cursor to just before the oldest candle
            next_cursor = oldest_ts - 1
            if next_cursor >= cursor:
                break  # No progress, avoid infinite loop
            cursor = next_cursor

            # If we got fewer than max, no more pages
            if len(candles) < self.MAX_CANDLES:
                break

            time.sleep(self.rate_limit)

            if page % 50 == 0:
                pct = min(100, (end_ms - cursor) / max(1, end_ms - start_ms) * 100)
                print(f"  {symbol}: {len(all_candles)} candles fetched ({pct:.0f}%)...")

        if not all_candles:
            print(f"  {symbol}: no data returned")
            return None

        # Build DataFrame — Bybit columns: [startTime, open, high, low, close, volume, turnover]
        df = pd.DataFrame(all_candles, columns=self.COLUMNS)
        df["timestamp"] = pd.to_numeric(df["timestamp"])
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Rename for consistency with backtester
        df = df.rename(columns={"volume": "base_vol", "turnover": "quote_vol"})

        # Filter to requested range and deduplicate
        df = df[(df["timestamp"] >= start_ms) & (df["timestamp"] <= end_ms)]
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

        # Convert timestamp to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        # Save to Parquet
        df.to_parquet(cache_file, engine="pyarrow", index=False)
        meta_file.write_text(f"{start_ms},{end_ms}")

        print(f"  {symbol}: {len(df)} candles saved")
        return df

    def fetch_multiple(
        self,
        symbols: list[str],
        start_time: datetime,
        end_time: datetime,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        """Fetch candles for multiple symbols serially. Returns dict of DataFrames."""
        results = {}
        total = len(symbols)

        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{total}] Fetching {symbol}...")
            df = self.fetch_symbol(symbol, start_time, end_time, force=force)
            if df is not None:
                results[symbol] = df

        print(f"\nDone: {len(results)}/{total} symbols fetched")
        return results

    def load_cached(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load a cached Parquet file. Returns None if not found."""
        cache_file = self._cache_path(symbol)
        if cache_file.exists():
            return pd.read_parquet(cache_file)
        return None

    def list_cached(self) -> list[str]:
        """List all cached symbols."""
        return [f.stem.replace("_1m", "") for f in self.cache_dir.glob("*_1m.parquet")]


class WEEXFetcher:
    """
    Fetches latest OHLCV candles from WEEX contract API.
    NOTE: WEEX API only returns the latest ~1000 candles with no historical pagination.
    Use BybitFetcher for historical data. This class kept for live price checks.
    """

    BASE_URL = "https://api-contract.weex.com"
    ENDPOINT = "/capi/v2/market/candles"
    MAX_CANDLES = 1000

    def __init__(self, rate_limit: float = 0.25):
        self.session = requests.Session()
        self.rate_limit = rate_limit

    @staticmethod
    def to_api_symbol(symbol: str) -> str:
        """Convert user symbol (BTCUSDT) to WEEX API format (cmt_btcusdt)."""
        s = symbol.lower().replace("_", "")
        if not s.startswith("cmt_"):
            s = f"cmt_{s}"
        return s

    def fetch_latest(self, symbol: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """Fetch latest N candles from WEEX (max 1000)."""
        api_sym = self.to_api_symbol(symbol)
        params = {"symbol": api_sym, "granularity": "1m", "limit": str(min(limit, self.MAX_CANDLES))}
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        try:
            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if not isinstance(data, list) or len(data) == 0:
                return None

            cols = ["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"]
            df = pd.DataFrame(data, columns=cols)
            df["timestamp"] = pd.to_numeric(df["timestamp"])
            for col in ["open", "high", "low", "close", "base_vol", "quote_vol"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df = df.sort_values("timestamp").reset_index(drop=True)
            return df

        except Exception:
            return None
