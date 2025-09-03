from __future__ import annotations

import argparse
import sys
import pandas as pd
import numpy as np

from .semafor import compute_semafor_levels
from .triangles import detect_123_triangles
from .mt5_loader import fetch_ohlc
from .plot import plot_ohlc_with_triangles


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expect columns: time, open, high, low, close
    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(df.columns.str.lower()):
        raise ValueError("CSV must contain columns: time, open, high, low, close")
    # normalize column names
    df.columns = [c.lower() for c in df.columns]
    # Ensure newest at index 0 (like MT4 buffers)
    df = df.iloc[::-1].reset_index(drop=True)
    return df


def main(argv=None):
    p = argparse.ArgumentParser(description="Detect 1-2-3 triangles from OHLC data (CSV or MT5)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="Path to CSV with columns time,open,high,low,close")
    src.add_argument("--mt5", action="store_true", help="Use MetaTrader5 terminal as data source")
    p.add_argument("--symbol", help="Symbol for MT5 source, e.g., EURUSD")
    p.add_argument("--timeframe", default="M15", help="MT5 timeframe, e.g., M15,H1,D1")
    p.add_argument("--bars", type=int, default=2000, help="Max bars to scan")
    p.add_argument("--periods", default="610,377,233,144,89,55,34,8", help="Comma-separated depths for 8 levels")
    p.add_argument("--dev", type=int, default=1, help="Deviation in points (like Dev)")
    p.add_argument("--backstep", type=int, default=1, help="Backstep (like Stp)")
    p.add_argument("--big", type=int, default=7, help="Big level index (1..8)")
    p.add_argument("--small", type=int, default=8, help="Small level index (1..8)")
    p.add_argument("--maxdist", type=int, default=10000, help="Max distance between point2 and point1 (points)")
    p.add_argument("--plot", action="store_true", help="Render a plot of detected triangles")
    p.add_argument("--out", help="Path to save plot (PNG)")
    args = p.parse_args(argv)

    if args.mt5:
        if not args.symbol:
            p.error("--symbol is required when using --mt5")
        df = fetch_ohlc(args.symbol, timeframe=args.timeframe, bars=args.bars)
    else:
        df = load_csv(args.csv)
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)

    periods = [int(x) for x in str(args.periods).split(",")]
    if len(periods) < max(args.big, args.small):
        print("Error: not enough periods for selected levels", file=sys.stderr)
        return 2

    sema = compute_semafor_levels(highs=highs, lows=lows, periods=periods, deviation_points=args.dev, backstep=args.backstep)
    tris = detect_123_triangles(semafor_levels=sema, big_level=args.big, small_level=args.small, max_distance_points=args.maxdist, max_bars_scan=args.bars)

    for t in tris:
        print(f"{t.dir.upper()} 1({t.bar1},{t.price1}) 2({t.bar2},{t.price2}) 3({t.bar3},{t.price3})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


