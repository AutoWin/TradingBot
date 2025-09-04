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