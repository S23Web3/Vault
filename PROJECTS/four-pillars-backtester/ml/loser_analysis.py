"""
Loser Classification and MFE/MAE Analysis (Sweeney Framework).

Classifies losing trades into 4 categories:
  A: Clean losers     -- MFE < 0.5R, never went your way. Fix entries.
  B: Breakeven fails  -- MFE 0.5-1.0R, partially profitable. Lower BE trigger.
  C: Should-be winners -- MFE > 1.0R, was profitable, reversed. BE raise saves.
  D: Catastrophic      -- MFE > 1.5R, strong winner reversed through. Need TSL.

Also computes the 8 standard Sweeney charts data and BE trigger optimization.

Input: trades DataFrame with mfe, mae, pnl, commission, sl_price, entry_price.
Output: classified trades, chart data, optimal BE trigger.
"""

import numpy as np
import pandas as pd


def classify_losers(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add loser_class column to trades DataFrame.

    Classes based on MFE in R-multiples:
      A: MFE_R < 0.5 (clean loser)
      B: 0.5 <= MFE_R < 1.0 (breakeven failure)
      C: 1.0 <= MFE_R < 1.5 (should-be winner)
      D: MFE_R >= 1.5 (catastrophic reversal)

    Winners get class "W".

    Args:
        trades_df: DataFrame with entry_price, sl_price, mfe, pnl, commission.

    Returns:
        Copy of trades_df with loser_class column added.
    """
    df = trades_df.copy()

    # Compute R (SL distance from entry in dollar terms)
    df["r_value"] = np.abs(df["entry_price"] - df["sl_price"])

    # MFE in R-multiples
    df["mfe_r"] = np.where(df["r_value"] > 0, df["mfe"] / df["r_value"], 0)

    # Net P&L
    df["net_pnl"] = df["pnl"] - df["commission"]

    # Classify
    classes = []
    for _, row in df.iterrows():
        if row["net_pnl"] > 0:
            classes.append("W")
        elif row["mfe_r"] < 0.5:
            classes.append("A")
        elif row["mfe_r"] < 1.0:
            classes.append("B")
        elif row["mfe_r"] < 1.5:
            classes.append("C")
        else:
            classes.append("D")

    df["loser_class"] = classes
    return df


def get_class_summary(classified_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize trade counts and avg P&L per loser class.

    Args:
        classified_df: DataFrame with loser_class column.

    Returns:
        Summary DataFrame with class, count, pct, avg_pnl, avg_mfe_r.
    """
    total = len(classified_df)
    rows = []
    for cls in ["W", "A", "B", "C", "D"]:
        subset = classified_df[classified_df["loser_class"] == cls]
        if len(subset) == 0:
            continue
        rows.append({
            "class": cls,
            "count": len(subset),
            "pct": len(subset) / total * 100,
            "avg_net_pnl": subset["net_pnl"].mean(),
            "avg_mfe_r": subset["mfe_r"].mean(),
            "total_pnl": subset["net_pnl"].sum(),
        })

    return pd.DataFrame(rows)


def optimize_be_trigger(trades_df: pd.DataFrame,
                        atr_range: np.ndarray = None) -> pd.DataFrame:
    """
    Sweep BE trigger levels and compute net impact (Sweeney Ch 4).

    For each candidate trigger T:
      losers_saved = losers where MFE >= T (would have been saved by BE)
      losers_saved_value = sum of |loss| for those trades
      winners_killed = winners that retraced below entry after hitting T
      winners_killed_value = sum of profit for those trades (estimated)
      net_impact = losers_saved_value - winners_killed_value

    Args:
        trades_df: DataFrame with mfe, mae, pnl, commission, entry_price, sl_price.
        atr_range: array of trigger levels to sweep (in $ terms).
                   If None, uses linspace from 0 to max MFE.

    Returns:
        DataFrame with trigger_level, losers_saved, winners_killed, net_impact.
    """
    df = trades_df.copy()
    df["net_pnl"] = df["pnl"] - df["commission"]

    losers = df[df["net_pnl"] <= 0]
    winners = df[df["net_pnl"] > 0]

    if atr_range is None:
        max_mfe = df["mfe"].max() if len(df) > 0 else 10
        atr_range = np.linspace(0.1, max(max_mfe, 1.0), 50)

    rows = []
    for trigger in atr_range:
        # Losers that had MFE >= trigger (would have been saved)
        saved = losers[losers["mfe"] >= trigger]
        saved_value = saved["net_pnl"].abs().sum() if len(saved) > 0 else 0

        # Winners that had MAE worse than -trigger after MFE hit
        # (they would have been stopped out at breakeven, losing the win)
        killed = winners[winners["mfe"] >= trigger]
        # Approximate: these winners still won but might have been exited at BE
        # We lose their actual profit
        killed_value = killed["net_pnl"].sum() if len(killed) > 0 else 0

        net = saved_value - killed_value

        rows.append({
            "trigger": float(trigger),
            "losers_saved": len(saved),
            "saved_value": float(saved_value),
            "winners_killed": len(killed),
            "killed_value": float(killed_value),
            "net_impact": float(net),
        })

    result = pd.DataFrame(rows)
    return result


def compute_etd(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute End Trade Drawdown for each trade.

    ETD = MFE - max(actual_profit, 0)
    High ETD = giving back profit. Low ETD = exiting near peak.

    Args:
        trades_df: DataFrame with mfe, pnl, commission.

    Returns:
        Copy with etd and etd_ratio columns added.
    """
    df = trades_df.copy()
    df["net_pnl"] = df["pnl"] - df["commission"]
    df["etd"] = df["mfe"] - np.maximum(df["net_pnl"], 0)
    df["etd_ratio"] = np.where(df["mfe"] > 0, df["etd"] / df["mfe"], 0)
    return df
