Python 1-2-3 Triangles (port of MT4 indicator)

Setup
-----
1) Create a virtualenv (optional) and install requirements:
```
pip install -r requirements.txt
```

CLI
---
```
# CSV source
python -m python123.cli --csv data.csv --periods 610,377,233,144,89,55,34,8 --dev 1 --backstep 1 --big 7 --small 8 --bars 2000 --maxdist 10000

# MT5 source (requires running terminal or login configured)
python -m python123.cli --mt5 --symbol EURUSD --timeframe M15 --periods 610,377,233,144,89,55,34,8 --dev 1 --backstep 1 --big 7 --small 8 --bars 2000 --maxdist 10000

# Visualization
python -m python123.cli --mt5 --symbol EURUSD --timeframe M15 --plot --out triangles.png
```

Date range options:
- `--start-date` and `--end-date` accept formats like `YYYY-MM-DD`, `YYYY-MM-DD HH:MM`, or `YYYY-MM-DD HH:MM:SS`.
- For MT5 source:
  - Provide both `--start-date` and `--end-date` to fetch a closed interval via MT5 `copy_rates_range`.
  - Provide only `--start-date` to fetch `--bars` bars starting from that datetime (inclusive) via `copy_rates_from`.
  - Providing only `--end-date` is not supported and will error; specify `--start-date` as well.
- For CSV source: rows are filtered to the inclusive range if provided.

CSV columns required: time, open, high, low, close. Rows should be oldest first; the CLI reverses to match MT4 buffer orientation (newest at index 0).

API
---
```python
import numpy as np
from python123 import compute_semafor_levels, detect_123_triangles

highs = np.array([...], dtype=float)
lows = np.array([...], dtype=float)
periods = [610,377,233,144,89,55,34,8]
sema = compute_semafor_levels(highs, lows, periods, deviation_points=1, backstep=1)
tris = detect_123_triangles(sema, big_level=7, small_level=8, max_distance_points=10000, max_bars_scan=2000)
```

Notes
-----
- Indices follow MT4 semantics: index 0 is the latest bar.
- Deviation and backstep are integer points like the MT4 inputs.

### Commands to create, activate, and run inside the virtualenv (Linux bash)

- **Create venv (if you haven’t yet):**
```bash
python3 -m venv /home/anohana/Documents/MQBOT/.venv
```

- **Activate it:**
```bash
source /home/anohana/Documents/MQBOT/.venv/bin/activate
```

- **Install requirements:**
```bash
pip install -r /home/anohana/Documents/MQBOT/requirements.txt
```

- **Run the CLI (examples):**
```bash
python -m python123.cli --csv /path/to/data.csv
# or (MT5 example)
python -m python123.cli --mt5 --symbol EURUSD --timeframe M15
```

- **Deactivate when done:**
```bash
deactivate
```

- If you prefer without activating, you can call the venv’s Python directly:
```bash
/home/anohana/Documents/MQBOT/.venv/bin/python -m python123.cli --csv /path/to/data.csv
```

Test

Environment configuration
-------------------------
- You can configure runs via a `.env` file (auto-loaded if `python-dotenv` is installed). Example keys:

```
# Data source: "mt5" or "csv"
DATA_SOURCE=mt5

# CSV mode
CSV_PATH=/absolute/or/relative/path/to/data.csv

# MT5 mode
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
# Optional path to terminal
MT5_PATH=C:\\Program Files\\MetaTrader 5\\terminal64.exe

# Common params
SYMBOL=EURUSD
TIMEFRAME=M15
BARS=2000
PERIODS=610,377,233,144,89,55,34,8
DEV=1
BACKSTEP=1
BIG_LEVEL=7
SMALL_LEVEL=8
MAXDIST=10000
PLOT=false
OUT_PATH=triangles.png
# Optional date range
START_DATE=2024-01-01 00:00:00
END_DATE=2024-03-01 23:59:59
```

Usage with env:
- Either rely on auto-detection when neither `--csv` nor `--mt5` is passed (use `DATA_SOURCE`), or pass `--use-env` to fill/override values from the environment.

Examples:
```
# Use DATA_SOURCE=mt5 and other keys from .env
python -m python123.cli --use-env

# Force CSV but fill other options from .env
python -m python123.cli --csv ./data.csv --use-env
```

Windows notes
-------------
- MetaTrader 5 initialization will accept credentials only when all three are provided together: `MT5_LOGIN`, `MT5_PASSWORD`, and `MT5_SERVER`. If you already have a running and authorized MT5 terminal, you can omit all three and the library will attach to the terminal.
- If you see `Terminal: Invalid params` during initialize, verify that either:
  - all three credentials are set (e.g. in `.env`) and correct; or
  - none are set and a terminal is running and logged in; and
  - optional `MT5_PATH` points to a valid `terminal64.exe` if needed.
- PowerShell may block script activation of virtualenvs by default. To allow local scripts, run an elevated PowerShell once and set policy for current user:
  - `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
  You can revert later with `Set-ExecutionPolicy -Scope CurrentUser Restricted`.