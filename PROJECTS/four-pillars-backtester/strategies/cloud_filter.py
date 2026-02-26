"""
Cloud 3 directional filter (simplified wrapper).
Blocks signals that violate Cloud 3 direction.
"""

import pandas as pd


def apply_cloud3_filter(df: pd.DataFrame, signals_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Block signals that violate Cloud 3 direction.

    If signal is LONG but cloud3_allows_long=False, remove signal.
    If signal is SHORT but cloud3_allows_short=False, remove signal.

    Args:
        df: DataFrame with cloud3_allows_long, cloud3_allows_short columns.
        signals_df: Optional separate signals DataFrame. If None, filter df in-place.

    Returns:
        Filtered DataFrame with blocked signals removed.
    """
    if signals_df is not None:
        out = signals_df.copy()
        allows_long = df["cloud3_allows_long"].values
        allows_short = df["cloud3_allows_short"].values
    else:
        out = df.copy()
        allows_long = out["cloud3_allows_long"].values
        allows_short = out["cloud3_allows_short"].values

    # Block long signals where Cloud 3 disallows
    long_cols = [c for c in out.columns if c.startswith("long_")]
    for c in long_cols:
        out[c] = out[c] & allows_long

    # Block short signals where Cloud 3 disallows
    short_cols = [c for c in out.columns if c.startswith("short_")]
    for c in short_cols:
        out[c] = out[c] & allows_short

    # Update direction column if present
    if "direction" in out.columns:
        for i in range(len(out)):
            d = out["direction"].iloc[i]
            if d == "LONG" and not allows_long[i]:
                out.iloc[i, out.columns.get_loc("direction")] = ""
                out.iloc[i, out.columns.get_loc("signal_type")] = ""
            elif d == "SHORT" and not allows_short[i]:
                out.iloc[i, out.columns.get_loc("direction")] = ""
                out.iloc[i, out.columns.get_loc("signal_type")] = ""

    return out


if __name__ == "__main__":
    import numpy as np
    n = 10
    df = pd.DataFrame({
        "long_a": [True, False, True, False, False, True, False, False, True, False],
        "short_a": [False, True, False, True, False, False, True, False, False, True],
        "signal_type": ["A", "A", "A", "A", "", "A", "A", "", "A", "A"],
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "", "LONG", "SHORT", "", "LONG", "SHORT"],
        "cloud3_allows_long": [True, True, False, True, True, True, True, True, False, True],
        "cloud3_allows_short": [True, True, True, False, True, True, True, True, True, False],
    })
    result = apply_cloud3_filter(df)
    blocked = (df["direction"] != "") & (result["direction"] == "")
    print(f"PASS -- {blocked.sum()} signals blocked by Cloud 3 filter")
