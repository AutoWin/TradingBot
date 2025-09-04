from __future__ import annotations

import argparse
import os
import sys
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime

try:
    # Allow configuration via .env file
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Optional dependency; proceed if not installed
    pass

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
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--csv", help="Path to CSV with columns time,open,high,low,close")
    src.add_argument("--mt5", action="store_true", help="Use MetaTrader5 terminal as data source")
    p.add_argument("--use-env", action="store_true", help="Fill missing args (or override defaults) from environment variables")
    p.add_argument("--symbol", help="Symbol for MT5 source, e.g., EURUSD")
    p.add_argument("--timeframe", default="M15", help="MT5 timeframe, e.g., M15,H1,D1")
    p.add_argument("--bars", type=int, default=2000, help="Max bars to scan")
    p.add_argument("--start-date", dest="start_date", help="Start datetime (YYYY-MM-DD[ HH:MM[:SS]])")
    p.add_argument("--end-date", dest="end_date", help="End datetime (YYYY-MM-DD[ HH:MM[:SS]])")
    p.add_argument("--periods", default="610,377,233,144,89,55,34,8", help="Comma-separated depths for 8 levels")
    p.add_argument("--dev", type=int, default=1, help="Deviation in points (like Dev)")
    p.add_argument("--backstep", type=int, default=1, help="Backstep (like Stp)")
    p.add_argument("--big", type=int, default=7, help="Big level index (1..8)")
    p.add_argument("--small", type=int, default=8, help="Small level index (1..8)")
    p.add_argument("--maxdist", type=int, default=10000, help="Max distance between point2 and point1 (points)")
    p.add_argument("--plot", action="store_true", help="Render a plot of detected triangles")
    p.add_argument("--out", help="Path to save plot (PNG)")
    args = p.parse_args(argv)

    def _env_bool(name: str) -> Optional[bool]:
        v = os.getenv(name)
        if v is None:
            return None
        return v.strip().lower() in {"1", "true", "yes", "on"}

    def _env_int(name: str) -> Optional[int]:
        v = os.getenv(name)
        if v is None:
            return None
        try:
            return int(v)
        except ValueError:
            raise ValueError(f"Environment variable {name} must be an integer")

    def _parse_date(s: Optional[str]) -> Optional[datetime]:
        if not s or str(s).strip() == "":
            return None
        # Accept common formats; rely on pandas for robustness
        ts = pd.to_datetime(s, errors="raise")
        # Convert pandas Timestamp to naive datetime (no tz) for MT5
        if hasattr(ts, "to_pydatetime"):
            dt = ts.to_pydatetime()
        else:
            dt = datetime.fromtimestamp(ts.value // 10**9)
        # Drop timezone info if any
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return dt

    # If neither --csv nor --mt5 provided, try DATA_SOURCE from env
    if not args.mt5 and not args.csv:
        source = os.getenv("DATA_SOURCE", "").strip().lower()
        if source == "mt5":
            args.mt5 = True
        elif source == "csv":
            args.csv = os.getenv("CSV_PATH")

    # Optionally override/fill from env when --use-env is provided
    if args.use_env:
        if not args.csv and not args.mt5:
            source = os.getenv("DATA_SOURCE", "").strip().lower()
            if source == "mt5":
                args.mt5 = True
            elif source == "csv":
                args.csv = os.getenv("CSV_PATH")
        # Fill fields if present in env
        args.symbol = args.symbol or os.getenv("SYMBOL")
        args.timeframe = os.getenv("TIMEFRAME", args.timeframe)
        args.bars = _env_int("BARS") or args.bars
        env_periods = os.getenv("PERIODS")
        if env_periods:
            args.periods = env_periods
        args.dev = _env_int("DEV") or args.dev
        args.backstep = _env_int("BACKSTEP") or args.backstep
        args.big = _env_int("BIG_LEVEL") or args.big
        args.small = _env_int("SMALL_LEVEL") or args.small
        args.maxdist = _env_int("MAXDIST") or args.maxdist
        env_plot = _env_bool("PLOT")
        if env_plot is not None:
            args.plot = env_plot
        args.out = args.out or os.getenv("OUT_PATH")
        args.start_date = args.start_date or os.getenv("START_DATE")
        args.end_date = args.end_date or os.getenv("END_DATE")

    if args.mt5:
        if not args.symbol:
            p.error("--symbol (or SYMBOL in env) is required when using --mt5 or DATA_SOURCE=mt5")
        start_dt = _parse_date(args.start_date)
        end_dt = _parse_date(args.end_date)
        df = fetch_ohlc(args.symbol, timeframe=args.timeframe, bars=args.bars, start_date=start_dt, end_date=end_dt)
    else:
        if not args.csv:
            p.error("--csv is required for CSV source (or set DATA_SOURCE=csv and CSV_PATH in env)")
        df = load_csv(args.csv)
        # Optional date filtering for CSV data
        if args.start_date or args.end_date:
            start_dt = _parse_date(args.start_date)
            end_dt = _parse_date(args.end_date)
            t = pd.to_datetime(df["time"], errors="coerce")
            mask = pd.Series(True, index=df.index)
            if start_dt is not None:
                mask &= t >= start_dt
            if end_dt is not None:
                mask &= t <= end_dt
            df = df.loc[mask].reset_index(drop=True)
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

    # Optionally render/save visualization
    if args.plot or args.out:
        title = f"{(args.symbol or 'CSV')} {args.timeframe} 1-2-3 Triangles"
        plot_ohlc_with_triangles(
            df=df,
            triangles=tris,
            title=title,
            show=bool(args.plot),
            out_path=args.out,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


