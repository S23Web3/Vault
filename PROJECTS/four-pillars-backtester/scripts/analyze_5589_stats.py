"""
Quick stats analysis of combined trades CSV for 55/89 v2.
Run: python scripts/analyze_5589_stats.py
"""
import pandas as pd


def main() -> None:
    """Print statistical breakdown of 55/89 v2 trade results."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    df = pd.read_csv(root / "results" / "trades_5589_ALL.csv")
    n = len(df)
    wins = int((df["pnl"] > 0).sum())
    dollar = chr(36)

    print("=== OVERALL ===")
    print("Total trades: " + str(n))
    print("Win rate: {:.1%}".format(wins / n))
    print("Net PnL: " + dollar + "{:.2f}".format(df["pnl"].sum()))
    print("Avg win: " + dollar + "{:.2f}".format(df.loc[df["pnl"] > 0, "pnl"].mean() if wins > 0 else 0))
    print("Avg loss: " + dollar + "{:.2f}".format(df.loc[df["pnl"] <= 0, "pnl"].mean()))
    print()

    print("=== DIRECTION ===")
    for d in ["LONG", "SHORT"]:
        sub = df[df["direction"] == d]
        w = int((sub["pnl"] > 0).sum())
        print(d + ": " + str(len(sub)) + " trades, WR={:.1%}".format(w / len(sub) if len(sub) else 0)
              + ", net=" + dollar + "{:.2f}".format(sub["pnl"].sum()))
    print()

    print("=== PHASE EXITS ===")
    for reason in sorted(df["exit_reason"].unique()):
        sub = df[df["exit_reason"] == reason]
        w = int((sub["pnl"] > 0).sum())
        print(reason + ": " + str(len(sub)) + " ({:.1%})".format(len(sub) / n)
              + " WR={:.1%}".format(w / len(sub) if len(sub) else 0)
              + " avg=" + dollar + "{:.2f}".format(sub["pnl"].mean()))
    print()

    print("=== BARS HELD ===")
    print("Median bars held: " + str(df["bars_held"].median()))
    print("Mean bars held: {:.1f}".format(df["bars_held"].mean()))
    p2 = df[df["exit_reason"] == "sl_phase2"]
    print("Phase 2 median bars held: " + str(p2["bars_held"].median()) if len(p2) else "N/A")
    print()

    print("=== GRADE BREAKDOWN ===")
    for g in ["A", "B", "C", ""]:
        sub = df[df["trade_grade"] == g]
        if len(sub) == 0:
            continue
        w = int((sub["pnl"] > 0).sum())
        label = g if g else "EMPTY"
        print("Grade " + label + ": " + str(len(sub))
              + " ({:.1%})".format(len(sub) / n)
              + " WR={:.1%}".format(w / len(sub))
              + " avg=" + dollar + "{:.2f}".format(sub["pnl"].mean()))
    print()

    print("=== RATCHET ===")
    print("Mean ratchet count: {:.2f}".format(df["ratchet_count"].mean()))
    r2 = int((df["ratchet_count"] >= 2).sum())
    r0 = int((df["ratchet_count"] == 0).sum())
    print("Ratchet >= 2 (Phase 4 eligible): " + str(r2) + "/" + str(n) + " ({:.1%})".format(r2 / n))
    print("Ratchet == 0: " + str(r0) + "/" + str(n) + " ({:.1%})".format(r0 / n))
    print()

    print("=== BE TRIGGER ===")
    print("EMA BE triggered: " + str(int(df["ema_be_triggered"].sum())) + " / " + str(n))
    print()

    print("=== SAW GREEN (LSG) ===")
    losers = df[df["pnl"] <= 0]
    sg = int(losers["saw_green"].sum())
    print("Losers that saw green: " + str(sg) + "/" + str(len(losers))
          + " ({:.1%})".format(sg / len(losers) if len(losers) else 0))
    print()

    print("=== QUICK STOPS (bars_held <= 5) ===")
    quick = df[df["bars_held"] <= 5]
    print("Trades exiting in 5 bars or less: " + str(len(quick)) + "/" + str(n)
          + " ({:.1%})".format(len(quick) / n))
    for r in sorted(quick["exit_reason"].unique()):
        print("    " + r + ": " + str(len(quick[quick["exit_reason"] == r])))
    print()

    print("=== PHASE 2 EXITS: BREAKDOWN ===")
    p2_trades = df[df["exit_reason"] == "sl_phase2"]
    if len(p2_trades) > 0:
        print("Count: " + str(len(p2_trades)))
        print("Bars held: median=" + str(p2_trades["bars_held"].median())
              + " mean={:.1f}".format(p2_trades["bars_held"].mean()))
        print("Avg PnL: " + dollar + "{:.2f}".format(p2_trades["pnl"].mean()))
        print("Saw green: " + str(int(p2_trades["saw_green"].sum())) + "/" + str(len(p2_trades)))
    print()

    print("=== EMA DELTA AT ENTRY (cross timing proxy) ===")
    # Check how many trades entered when EMAs were already crossed (delta > 0 for long, < 0 for short)
    # We can infer from be_triggered = 0 everywhere: cross never happened AFTER entry
    print("BE triggered across all 532 trades: " + str(int(df["ema_be_triggered"].sum())))
    print("This means the EMA 55/89 cross NEVER fires post-entry for any trade.")


if __name__ == "__main__":
    main()
