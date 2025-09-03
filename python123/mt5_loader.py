from __future__ import annotations

from typing import Optional
import pandas as pd
import MetaTrader5 as mt5


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def fetch_ohlc(
    symbol: str,
    timeframe: str = "M15",
    bars: int = 2000,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLC from MetaTrader5 terminal.
    Requires a running terminal (or provide login/password/server for initialize).
    Returns DataFrame with columns: time, open, high, low, close (oldest first).
    """
    if not mt5.initialize(login=login, password=password, server=server):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    tf = TIMEFRAME_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
    if rates is None:
        raise RuntimeError(f"MT5 copy_rates_from_pos failed: {mt5.last_error()}")

    df = pd.DataFrame(rates)
    df.rename(columns={"time": "time", "open": "open", "high": "high", "low": "low", "close": "close"}, inplace=True)
    # MT5 returns oldest at index 0 already, keep it.
    return df[["time", "open", "high", "low", "close"]]


