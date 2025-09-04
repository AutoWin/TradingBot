from __future__ import annotations

from typing import Optional
from datetime import datetime
import os
import pandas as pd
import MetaTrader5 as mt5

try:
    # Load environment variables from a .env file if present
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # dotenv is optional; proceed if not installed
    pass

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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Fetch OHLC from MetaTrader5 terminal.
    Requires a running terminal (or provide login/password/server for initialize).
    Returns DataFrame with columns: time, open, high, low, close (oldest first).
    """
    # Prefer explicit args; fall back to environment variables if missing
    env_login = os.getenv("MT5_LOGIN")
    env_password = os.getenv("MT5_PASSWORD")
    env_server = os.getenv("MT5_SERVER")
    env_path = os.getenv("MT5_PATH")

    if login is None and env_login:
        try:
            login = int(env_login)
        except ValueError:
            raise ValueError("MT5_LOGIN must be an integer")
    if password is None:
        password = env_password
    if server is None:
        server = env_server

    # Build initialize kwargs. Pass credentials only if all three are present.
    has_login = login is not None
    has_password = password is not None and str(password) != ""
    has_server = server is not None and str(server) != ""
    has_full_credentials = has_login and has_password and has_server
    has_any_credentials = has_login or has_password or has_server

    init_kwargs: dict = {}
    if env_path:
        init_kwargs["path"] = env_path
    if has_full_credentials:
        init_kwargs["login"] = login  # type: ignore[arg-type]
        init_kwargs["password"] = password
        init_kwargs["server"] = server

    # Initialize terminal (without credentials if not fully provided)
    initialized = mt5.initialize(**init_kwargs)

    if not initialized:
        err = mt5.last_error()
        hint = ""
        if has_any_credentials and not has_full_credentials:
            hint = " (hint: provide MT5_LOGIN, MT5_PASSWORD and MT5_SERVER together, or none if a terminal is already authorized)"
        # Only include keys to avoid leaking secrets
        init_keys = list(init_kwargs.keys())
        raise RuntimeError(f"MT5 initialize failed: {err}{hint}. init keys: {init_keys}")

    tf = TIMEFRAME_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    # Ensure symbol is available/selected
    info = mt5.symbol_info(symbol)
    if info is None:
        # Try to select the symbol from Market Watch
        if not mt5.symbol_select(symbol, True):
            err = mt5.last_error()
            mt5.shutdown()
            raise RuntimeError(f"MT5 symbol_select failed for {symbol}: {err}")

    # Decide fetch method based on provided dates
    if start_date is not None and end_date is not None:
        rates = mt5.copy_rates_range(symbol, tf, start_date, end_date)
    elif start_date is not None and end_date is None:
        # Fetch 'bars' count starting from start_date
        rates = mt5.copy_rates_from(symbol, tf, start_date, bars)
    elif start_date is None and end_date is not None:
        mt5.shutdown()
        raise ValueError("end_date provided without start_date. Provide both, or only start_date, or neither.")
    else:
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
    if rates is None:
        err = mt5.last_error()
        mt5.shutdown()
        raise RuntimeError(f"MT5 copy_rates_from_pos failed: {err}")

    df = pd.DataFrame(rates)
    df.rename(columns={"time": "time", "open": "open", "high": "high", "low": "low", "close": "close"}, inplace=True)
    # MT5 returns oldest at index 0 already, keep it.
    out = df[["time", "open", "high", "low", "close"]]
    # Close the MT5 connection to avoid leaking a handle when running CLI
    mt5.shutdown()
    return out


